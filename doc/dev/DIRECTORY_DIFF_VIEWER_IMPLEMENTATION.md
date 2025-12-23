# Directory Diff Viewer Implementation

## Overview

This document describes the implementation details of the Directory Diff Viewer feature in TFM. The viewer provides recursive directory comparison with a tree-structured, side-by-side display, following the established UILayer architecture pattern.

## Architecture

### Component Hierarchy

```
DirectoryDiffViewer (UILayer)
├── DirectoryScanner (Worker Thread) - Background scanning
│   ├── Single-level directory traversal
│   ├── File metadata collection
│   └── Progress reporting
├── FileComparator (Worker Thread) - Background file comparison
│   ├── Content comparison
│   └── Result updates
├── PriorityHandler (Worker Thread) - Priority queue management
│   ├── Visible node detection
│   └── Priority-based scheduling
├── DiffEngine
│   ├── Tree structure building
│   ├── Difference detection
│   └── Classification logic
└── TreeRenderer (integrated in DirectoryDiffViewer)
    ├── Tree node rendering
    ├── Expand/collapse state management
    ├── Pending status indicators
    └── Visual highlighting
```

### Progressive Scanning Architecture

The viewer uses a **progressive, breadth-first scanning** approach to minimize time-to-first-display:

1. **Initial Display (< 100ms)**: Scan only top-level items, display immediately
2. **Background Scanning**: Worker threads scan subdirectories progressively
3. **Priority System**: Visible items are scanned before off-screen items
4. **On-Demand Scanning**: User expansion triggers immediate scanning
5. **Lazy Scanning**: One-sided directories scanned only when expanded

### Design Principles

1. **UILayer Integration**: Implements the UILayer interface for seamless stack management
2. **Progressive Scanning**: Provides instant feedback with background processing
3. **Thread Safety**: Uses locks and queues for safe concurrent access
4. **Priority-Based**: Scans visible items first for optimal user experience
5. **Lazy Rendering**: Only renders visible nodes for performance with large trees
6. **Path Abstraction**: Uses `tfm_path.Path` for local and remote file system support
7. **Consistent Styling**: Uses `tfm_colors` for visual consistency with other TFM components

## Progressive Scanning System

### Overview

The progressive scanning system provides instant feedback by displaying top-level items immediately while scanning deeper levels in the background. This architecture ensures the UI remains responsive even with very large directory trees.

### Data Flow Diagram

```
User Opens Viewer
       ↓
[Initial Scan] ← Scan top-level only (< 100ms)
       ↓
[Display Tree] ← Show immediate results
       ↓
[Start Workers] ← Launch background threads
       ↓
┌──────────────────────────────────────┐
│  Background Processing (Parallel)    │
├──────────────────────────────────────┤
│ [Directory Scanner] → scan_queue     │
│       ↓                              │
│ [File Comparator] → comparison_queue │
│       ↓                              │
│ [Priority Handler] → priority_queue  │
└──────────────────────────────────────┘
       ↓
[Update Tree] ← Progressive updates
       ↓
[Mark Dirty] ← Trigger redraw
       ↓
[User Sees Updates] ← Incremental display
```

### Thread Architecture

#### Main Thread
- Handles UI rendering
- Processes user input
- Performs on-demand scanning (when user expands)
- Updates tree structure from worker results

#### Directory Scanner Thread
- Processes scan_queue (breadth-first)
- Scans single directory level at a time
- Updates file dictionaries with thread-safe locking
- Adds child directories to queue
- Marks tree as dirty for UI update

#### File Comparator Thread
- Processes comparison_queue
- Compares file content byte-by-byte
- Updates tree node difference types
- Marks tree as dirty for UI update

#### Priority Handler Thread
- Monitors viewport changes
- Identifies visible nodes
- Moves high-priority items to front of scan_queue
- Ensures visible items are scanned first

### Work Queue System

#### Scan Queue (FIFO)
```python
scan_queue: queue.Queue[ScanTask]

@dataclass
class ScanTask:
    left_path: Optional[Path]
    right_path: Optional[Path]
    relative_path: str
    priority: int
    is_visible: bool
```

#### Priority Queue (Priority-based)
```python
priority_queue: queue.PriorityQueue[Tuple[int, ScanTask]]

# Priority levels:
IMMEDIATE = 1000   # User just expanded
VISIBLE = 100      # Currently visible
EXPANDED = 50      # Expanded but scrolled off
NORMAL = 10        # Not visible, not expanded
LOW = 1            # One-sided directories
```

#### Comparison Queue (FIFO)
```python
comparison_queue: queue.Queue[ComparisonTask]

@dataclass
class ComparisonTask:
    left_path: Path
    right_path: Path
    relative_path: str
    priority: int
    is_visible: bool
```

### Thread Synchronization Strategy

#### Lock Hierarchy

To prevent deadlocks, locks must be acquired in this order:

1. **queue_lock**: Protects work queues
2. **data_lock**: Protects file dictionaries
3. **tree_lock**: Protects tree structure

**Critical Rule**: Never hold multiple locks when calling external functions.

#### Lock Usage Patterns

**Directory Scanner Worker**:
```python
# Get task from queue
with self.queue_lock:
    task = self.scan_queue.get()

# Scan directory (no locks held)
files = self._scan_single_level(task.left_path, task.right_path)

# Update data structures
with self.data_lock:
    self.left_files.update(files[0])
    self.right_files.update(files[1])

with self.tree_lock:
    self._update_tree_node(task.relative_path, files)

# Add child tasks
with self.queue_lock:
    for child in children:
        self.scan_queue.put(child_task)
```

**File Comparator Worker**:
```python
# Get task from queue
with self.queue_lock:
    task = self.comparison_queue.get()

# Compare files (no locks held)
are_identical = self.compare_file_content(task.left_path, task.right_path)

# Update tree
with self.tree_lock:
    node = self._find_node(task.relative_path)
    node.difference_type = IDENTICAL if are_identical else CONTENT_DIFFERENT
    node.content_compared = True
```

### Scanning Phases

#### Phase 1: Initial Display (< 100ms)

```python
def start_scan(self):
    # Scan only top-level
    left_top = self._scan_single_level(self.left_path, None)
    right_top = self._scan_single_level(None, self.right_path)
    
    # Build initial tree with PENDING status
    self.build_tree()
    
    # Display immediately
    self.mark_dirty()
    
    # Start background workers
    self._start_directory_scanner_worker()
    self._start_file_comparator_worker()
    self._start_priority_handler_worker()
```

#### Phase 2: Background Scanning

```python
def _directory_scanner_worker(self):
    while not self.cancelled:
        # Check priority queue first
        if not self.priority_queue.empty():
            _, task = self.priority_queue.get()
        else:
            task = self.scan_queue.get()
        
        # Scan single level
        files = self._scan_single_level(task.left_path, task.right_path)
        
        # Update data structures (thread-safe)
        self._update_with_lock(files)
        
        # Add children to queue (breadth-first)
        for child_dir in child_directories:
            self.scan_queue.put(child_task)
        
        # Trigger UI update
        self.mark_dirty()
```

#### Phase 3: On-Demand Scanning

```python
def expand_node(self, node_index: int):
    node = self.visible_nodes[node_index]
    
    if not node.children_scanned:
        # Scan immediately in main thread
        node.scan_in_progress = True
        self.mark_dirty()  # Show "scanning..." indicator
        
        files = self._scan_single_level(node.left_path, node.right_path)
        self._update_tree_node(node, files)
        
        node.children_scanned = True
        node.scan_in_progress = False
    
    node.is_expanded = True
    self.update_visible_nodes()
    self.mark_dirty()
```

### Priority System

#### Priority Calculation

```python
def _calculate_priority(self, node: TreeNode) -> int:
    if node.scan_in_progress:
        return IMMEDIATE  # User just expanded
    
    if self._is_visible(node):
        return VISIBLE  # Currently in viewport
    
    if node.is_expanded:
        return EXPANDED  # Expanded but scrolled off
    
    if node.left_path is None or node.right_path is None:
        return LOW  # One-sided directory (lazy scan)
    
    return NORMAL  # Default priority
```

#### Viewport Detection

```python
def _get_visible_nodes_range(self) -> List[TreeNode]:
    """Get nodes currently visible in viewport."""
    start = self.scroll_offset
    end = start + self.content_height
    return self.visible_nodes[start:end]

def _update_priorities(self):
    """Called on scroll, expand, collapse."""
    visible = self._get_visible_nodes_range()
    
    for node in visible:
        if not node.children_scanned and node.is_directory:
            task = ScanTask(
                left_path=node.left_path,
                right_path=node.right_path,
                relative_path=node.relative_path,
                priority=VISIBLE,
                is_visible=True
            )
            self.priority_queue.put((VISIBLE, task))
```

### Pending Status Management

#### Status Indicators

```python
@dataclass
class TreeNode:
    children_scanned: bool = False    # Directory contents listed
    content_compared: bool = False    # File content compared
    scan_in_progress: bool = False    # Currently being scanned
```

#### Display Logic

```python
def _get_node_display_text(self, node: TreeNode) -> str:
    if node.scan_in_progress:
        return f"{node.name} [scanning...]"
    
    if node.is_directory and not node.children_scanned:
        return f"{node.name} ..."
    
    if not node.is_directory and not node.content_compared:
        return f"{node.name} [pending]"
    
    return node.name
```

### Performance Characteristics

#### Time to First Display
- **Target**: < 100ms
- **Typical**: 50-80ms for most directories
- **Factors**: Number of top-level items, file system speed

#### Background Scanning Rate
- **Typical**: 100-500 directories/second
- **Factors**: File system speed, directory depth, file count

#### Memory Usage
- **Per Node**: ~250 bytes (with progressive fields)
- **10,000 nodes**: ~2.5 MB
- **Optimization**: Only scanned nodes consume memory

#### Thread Overhead
- **3 worker threads**: ~1-2 MB total
- **Queue overhead**: Minimal (< 100 KB typical)
- **Lock contention**: Minimal (short critical sections)

## Core Components

### DirectoryDiffViewer Class

**Location**: `src/tfm_directory_diff_viewer.py`

Main class implementing the UILayer interface:

```python
class DirectoryDiffViewer(UILayer):
    """
    A UILayer that displays recursive directory comparison results.
    
    Attributes:
        renderer: TTK renderer instance
        left_path: Path to left directory
        right_path: Path to right directory
        root_node: Root of the tree structure
        visible_nodes: Flattened list of visible nodes
        cursor_position: Current cursor index
        scroll_offset: First visible line
        show_identical: Whether to show identical files
    """
```

#### Key Methods

**Initialization**:
```python
def __init__(self, renderer, left_path: Path, right_path: Path)
```
- Initializes state variables
- Starts directory scanning in worker thread
- Sets up progress callback

**Scanning**:
```python
def start_scan(self) -> None
```
- Creates DirectoryScanner instance
- Launches worker thread
- Registers progress callback

**Tree Management**:
```python
def build_tree(self) -> None
def flatten_tree(self, node: TreeNode, result: List[TreeNode]) -> None
def update_visible_nodes(self) -> None
```
- Builds unified tree structure from scan results
- Flattens tree into visible node list
- Updates visibility based on expand/collapse state

**Navigation**:
```python
def expand_node(self, node_index: int) -> None
def collapse_node(self, node_index: int) -> None
def move_cursor(self, delta: int) -> None
```
- Handles expand/collapse operations
- Manages cursor movement with bounds checking
- Updates visible nodes list

**Rendering**:
```python
def render(self, renderer) -> None
def render_header(self, renderer) -> None
def render_content(self, renderer) -> None
def render_status_bar(self, renderer) -> None
```
- Coordinates rendering of all viewer sections
- Handles progress display during scanning
- Applies color highlighting based on difference type

### Data Structures

#### TreeNode

**Location**: `src/tfm_directory_diff_viewer.py`

```python
@dataclass
class TreeNode:
    name: str                           # File or directory name
    left_path: Optional[Path]           # Path in left directory
    right_path: Optional[Path]          # Path in right directory
    is_directory: bool                  # True for directories
    difference_type: DifferenceType     # Classification
    depth: int                          # Nesting level (0 = root)
    is_expanded: bool                   # Expansion state
    children: List[TreeNode]            # Child nodes
    parent: Optional[TreeNode]          # Parent reference
    left_info: Optional[FileInfo]       # Left file metadata
    right_info: Optional[FileInfo]      # Right file metadata
    
    # Progressive scanning fields
    children_scanned: bool = False      # Directory contents listed
    content_compared: bool = False      # File content compared
    scan_in_progress: bool = False      # Currently being scanned
```

**Design Notes**:
- Stores both left and right paths for side-by-side display
- Maintains parent reference for upward traversal
- Stores file metadata for error handling and display
- Progressive scanning fields track scanning state
- `children_scanned`: True when directory has been listed
- `content_compared`: True when file content has been compared
- `scan_in_progress`: True during active scanning (shows indicator)

#### DifferenceType

```python
class DifferenceType(Enum):
    IDENTICAL = "identical"
    ONLY_LEFT = "only_left"
    ONLY_RIGHT = "only_right"
    CONTENT_DIFFERENT = "content_different"
    CONTAINS_DIFFERENCE = "contains_difference"
    PENDING = "pending"  # Not yet scanned or compared
```

**Classification Logic**:
1. **PENDING**: Not yet scanned or compared (initial state)
2. **ONLY_LEFT**: `left_path` exists, `right_path` is None
3. **ONLY_RIGHT**: `right_path` exists, `left_path` is None
4. **CONTENT_DIFFERENT**: Both paths exist, file content differs
5. **CONTAINS_DIFFERENCE**: Directory with any non-identical descendants
6. **IDENTICAL**: Both paths exist, content matches, no descendant differences

#### FileInfo

```python
@dataclass
class FileInfo:
    path: Path                          # Full path
    relative_path: str                  # Relative from root
    is_directory: bool                  # Directory flag
    size: int                           # File size in bytes
    mtime: float                        # Modification time
    is_accessible: bool                 # Permission check
    error_message: Optional[str]        # Error details
```

### DirectoryScanner Class

**Location**: `src/tfm_directory_diff_viewer.py`

Handles single-level directory scanning in worker threads:

```python
class DirectoryScanner:
    """
    Scans directories one level at a time (non-recursive).
    Used by worker thread for progressive scanning.
    
    Attributes:
        left_path: Root path for left directory
        right_path: Root path for right directory
        progress_callback: Function to report progress
        cancelled: Cancellation flag
    """
```

#### Scanning Algorithm

1. **Single-Level Scan**: Scan only immediate children (non-recursive)
2. **Metadata Collection**: Gather file info for each item
3. **Queue Management**: Add subdirectories to scan queue
4. **Progress Reporting**: Call callback with current status
5. **Cancellation Check**: Periodically check cancellation flag
6. **Result Return**: Return dictionaries of FileInfo objects

**Key Implementation Details**:
- Uses `tfm_path.Path.iterdir()` for directory listing
- Scans only one level at a time (breadth-first)
- Catches permission errors and marks files as inaccessible
- Reports progress based on queue sizes
- Checks cancellation flag frequently for responsiveness
- Worker thread processes scan_queue continuously

### DiffEngine Class

**Location**: `src/tfm_directory_diff_viewer.py`

Builds tree structure and detects differences:

```python
class DiffEngine:
    """
    Builds unified tree structure and classifies differences.
    
    Attributes:
        left_files: Dictionary of left directory files
        right_files: Dictionary of right directory files
    """
```

#### Tree Building Algorithm

1. **Collect Unique Paths**: Merge keys from both file dictionaries
2. **Create Nodes**: Build TreeNode for each unique path
3. **Establish Hierarchy**: Link parent-child relationships
4. **Classify Nodes**: Determine difference type for each node
5. **Propagate Differences**: Mark parent directories with CONTAINS_DIFFERENCE

**Classification Logic**:
```python
def classify_node(self, node: TreeNode) -> DifferenceType:
    # Check existence
    if node.left_path is None:
        return DifferenceType.ONLY_RIGHT
    if node.right_path is None:
        return DifferenceType.ONLY_LEFT
    
    # Check content for files
    if not node.is_directory:
        if self.compare_file_content(node.left_path, node.right_path):
            return DifferenceType.IDENTICAL
        else:
            return DifferenceType.CONTENT_DIFFERENT
    
    # Check children for directories
    if any(child.difference_type != DifferenceType.IDENTICAL 
           for child in node.children):
        return DifferenceType.CONTAINS_DIFFERENCE
    
    return DifferenceType.IDENTICAL
```

**File Comparison**:
```python
def compare_file_content(self, left_path: Path, right_path: Path) -> bool:
    # Compare file sizes first (fast check)
    if left_path.stat().st_size != right_path.stat().st_size:
        return False
    
    # Compare content byte-by-byte
    with left_path.open('rb') as f1, right_path.open('rb') as f2:
        while True:
            chunk1 = f1.read(8192)
            chunk2 = f2.read(8192)
            if chunk1 != chunk2:
                return False
            if not chunk1:
                break
    
    return True
```

## Rendering System

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│ Header: Left Path | Right Path                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Tree Content (scrollable):                                 │
│   [+] directory/          [+] directory/                   │
│       file1.txt               file1.txt                    │
│       file2.txt               [blank]                      │
│       [blank]                 file3.txt                    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Status: Line 5/100 | 50 files, 10 differences | Filter: ON │
└─────────────────────────────────────────────────────────────┘
```

### Rendering Pipeline

1. **Header Rendering**: Draw directory paths and controls
2. **Content Rendering**: Draw visible tree nodes with highlighting
3. **Status Bar Rendering**: Draw statistics and current state

### Color Scheme

Uses `tfm_colors` constants:

- `COLOR_DIFF_ONLY_ONE_SIDE`: Orange/yellow for only-left/only-right
- `COLOR_DIFF_CHANGE`: Red for content-different
- `COLOR_DIFF_FOCUSED`: Blue for contains-difference
- `COLOR_DIFF_BLANK`: Gray for blank alignment spaces
- `COLOR_CURSOR`: Highlight for current cursor position

### Side-by-Side Alignment

**Algorithm**:
1. Calculate half-width of terminal
2. Render left side in columns 0 to half-width
3. Render separator at half-width
4. Render right side in columns half-width+1 to width
5. Use blank spaces with gray background for missing items

**Implementation**:
```python
def render_node_row(self, renderer, y: int, node: TreeNode):
    half_width = renderer.width // 2
    
    # Render left side
    if node.left_path:
        self.render_node_side(renderer, y, 0, node, is_left=True)
    else:
        self.render_blank_side(renderer, y, 0, half_width)
    
    # Render separator
    renderer.draw_text(y, half_width, "|", COLOR_NORMAL)
    
    # Render right side
    if node.right_path:
        self.render_node_side(renderer, y, half_width + 1, node, is_left=False)
    else:
        self.render_blank_side(renderer, y, half_width + 1, half_width)
```

## Event Handling

### Key Event Processing

**Location**: `handle_key_event()` method

```python
def handle_key_event(self, event) -> bool:
    if self.scan_in_progress:
        # Handle cancellation during scan
        if event.key == KEY_ESCAPE:
            self.cancel_scan()
            return True
        return True
    
    # Navigation
    if event.key == KEY_UP:
        self.move_cursor(-1)
    elif event.key == KEY_DOWN:
        self.move_cursor(1)
    elif event.key == KEY_PGUP:
        self.move_cursor(-self.page_size)
    elif event.key == KEY_PGDN:
        self.move_cursor(self.page_size)
    
    # Expand/collapse
    elif event.key == KEY_RIGHT or event.key == KEY_ENTER:
        self.expand_current_node()
    elif event.key == KEY_LEFT:
        self.collapse_current_node()
    
    # File diff viewer
    elif event.key == ord('d') or event.key == ord('D'):
        self.open_file_diff()
    
    # Filter toggle
    elif event.key == ord('i') or event.key == ord('I'):
        self.toggle_identical_filter()
    
    # Close viewer
    elif event.key == KEY_ESCAPE or event.key == ord('q'):
        self._should_close = True
    
    return True
```

### System Event Processing

Handles window resize events:

```python
def handle_system_event(self, event) -> bool:
    if event.type == "window_resize":
        self.mark_dirty()
        return True
    return False
```

## Integration Points

### FileManager Integration

**Location**: `src/tfm_main.py`

Key binding registration:
```python
# In FileManager.__init__()
self.key_bindings.register(KEY_CTRL_D, self.open_directory_diff)

def open_directory_diff(self):
    left_path = self.left_pane.get_current_directory()
    right_path = self.right_pane.get_current_directory()
    
    if not left_path.is_dir() or not right_path.is_dir():
        self.show_error("Both panes must contain directories")
        return
    
    viewer = DirectoryDiffViewer(self.renderer, left_path, right_path)
    self.ui_layer_stack.push(viewer)
```

### DiffViewer Integration

**Location**: `DirectoryDiffViewer.open_file_diff()` method

```python
def open_file_diff(self):
    node = self.visible_nodes[self.cursor_position]
    
    if not node.is_directory and \
       node.difference_type == DifferenceType.CONTENT_DIFFERENT:
        from tfm_diff_viewer import DiffViewer
        
        diff_viewer = DiffViewer(
            self.renderer,
            node.left_path,
            node.right_path
        )
        self.ui_layer_stack.push(diff_viewer)
```

### UILayer Stack Integration

The viewer participates in the UILayer stack system:

1. **Push**: FileManager pushes DirectoryDiffViewer onto stack
2. **Active**: DirectoryDiffViewer receives events and renders
3. **Push Child**: DirectoryDiffViewer can push DiffViewer onto stack
4. **Pop**: User closes viewer, returns to previous layer

## Performance Considerations

### Progressive Scanning Performance

**Time to First Display**:
- **Target**: < 100ms
- **Typical**: 50-80ms for most directories
- **Measurement**: From viewer open to first tree display
- **Factors**: Number of top-level items, file system speed

**Background Scanning Rate**:
- **Typical**: 100-500 directories/second
- **Factors**: File system speed, directory depth, file count per directory
- **Optimization**: Breadth-first ensures visible items scanned first

**Priority System Overhead**:
- **Viewport detection**: O(1) - simple slice operation
- **Priority updates**: O(visible_nodes) - typically < 50 nodes
- **Queue operations**: O(log n) for priority queue

### Scanning Performance

**Optimization Strategies**:
1. **Progressive Scanning**: Display immediately, scan in background
2. **Worker Threads**: Three threads prevent UI blocking
3. **Breadth-First**: Scan top levels before deep levels
4. **Priority-Based**: Visible items scanned before hidden
5. **Lazy Scanning**: One-sided directories scanned on-demand
6. **On-Demand**: User expansion triggers immediate scanning
7. **Progress Reporting**: Updates UI periodically, not per file
8. **Cancellation**: Allows user to abort long scans
9. **Error Handling**: Continues on permission errors

**Typical Performance**:
- **Initial display**: < 100ms (top-level only)
- **1,000 files**: 1-2 seconds (background)
- **10,000 files**: 10-20 seconds (background)
- **100,000 files**: 2-5 minutes (background)
- **UI remains responsive**: Always, regardless of scan size

### Rendering Performance

**Optimization Strategies**:
1. **Lazy Rendering**: Only renders visible nodes
2. **Dirty Flag**: Skips rendering when no changes
3. **Flat List**: Uses flattened visible_nodes for O(1) access
4. **Minimal Redraws**: Only redraws changed regions

**Typical Performance**:
- 1,000 visible nodes: 60 FPS
- 10,000 visible nodes: 60 FPS (only ~50 visible at once)

### Memory Usage

**Memory Footprint**:
- TreeNode: ~250 bytes per node (with progressive fields)
- FileInfo: ~150 bytes per file
- Work queues: ~100 KB typical, ~1 MB maximum
- Thread overhead: ~1-2 MB for 3 worker threads
- **10,000 files**: ~4 MB total

**Optimization Strategies**:
1. **Progressive Loading**: Only scanned nodes consume memory
2. **Shared Strings**: Python interns common strings
3. **Optional Fields**: Uses None for missing data
4. **No Caching**: Doesn't cache rendered output
5. **Lazy Scanning**: One-sided directories not loaded until expanded

**Memory Growth**:
- **Linear with scanned nodes**: O(n) where n = scanned files
- **Not linear with total files**: Unscanned directories don't consume memory
- **Bounded by visible tree**: Only expanded portions fully loaded

## Thread Safety

### Synchronization Primitives

**Locks**:
```python
self.data_lock = threading.RLock()    # Protects file dictionaries
self.tree_lock = threading.RLock()    # Protects tree structure
self.queue_lock = threading.Lock()    # Protects work queues
```

**Work Queues**:
```python
self.scan_queue = queue.Queue()              # Thread-safe FIFO
self.priority_queue = queue.PriorityQueue()  # Thread-safe priority
self.comparison_queue = queue.Queue()        # Thread-safe FIFO
```

**Cancellation**:
```python
self.cancelled = False  # Atomic boolean for shutdown
```

### Lock Ordering Rules

**Critical Rule**: Always acquire locks in this order to prevent deadlocks:

1. **queue_lock** (highest priority)
2. **data_lock** (medium priority)
3. **tree_lock** (lowest priority)

**Never**:
- Acquire locks in reverse order
- Hold multiple locks when calling external functions
- Hold locks during I/O operations

### Thread-Safe Patterns

**Pattern 1: Queue Access**
```python
# Get task from queue
with self.queue_lock:
    if not self.scan_queue.empty():
        task = self.scan_queue.get()
    else:
        return

# Process task (no locks held)
result = self._scan_single_level(task.left_path, task.right_path)

# Update data
with self.data_lock:
    self.left_files.update(result[0])
    self.right_files.update(result[1])
```

**Pattern 2: Tree Updates**
```python
# Find node (read-only, short critical section)
with self.tree_lock:
    node = self._find_node(relative_path)
    if node is None:
        return

# Update node (write, short critical section)
with self.tree_lock:
    node.children_scanned = True
    node.children.extend(new_children)
    self.mark_dirty()
```

**Pattern 3: Priority Updates**
```python
# Get visible nodes (read-only)
with self.tree_lock:
    visible = self._get_visible_nodes_range()

# Process visible nodes (no locks held)
tasks = []
for node in visible:
    if not node.children_scanned:
        tasks.append(self._create_scan_task(node))

# Add to priority queue
with self.queue_lock:
    for task in tasks:
        self.priority_queue.put((VISIBLE, task))
```

### Race Condition Prevention

**Scenario 1: Concurrent Tree Updates**
- **Problem**: Multiple threads updating same node
- **Solution**: tree_lock protects all tree modifications
- **Pattern**: Short critical sections, update then release

**Scenario 2: Queue Starvation**
- **Problem**: Priority queue starves regular queue
- **Solution**: Check priority queue first, fall back to regular
- **Pattern**: Balanced queue processing

**Scenario 3: Dirty Flag Races**
- **Problem**: Multiple threads marking dirty simultaneously
- **Solution**: mark_dirty() is atomic (simple boolean set)
- **Pattern**: No lock needed for dirty flag

### Deadlock Prevention

**Strategy 1: Lock Ordering**
- Always acquire locks in defined order
- Never acquire in reverse order
- Document lock hierarchy in code

**Strategy 2: Short Critical Sections**
- Hold locks for minimal time
- Release before I/O operations
- Release before calling external functions

**Strategy 3: No Nested Locks**
- Avoid holding multiple locks simultaneously
- If needed, follow strict ordering
- Use RLock for reentrant scenarios

### Thread Lifecycle

**Startup**:
```python
def start_scan(self):
    # Initial scan (main thread)
    self._scan_top_level()
    
    # Start workers
    self._start_directory_scanner_worker()
    self._start_file_comparator_worker()
    self._start_priority_handler_worker()
```

**Shutdown**:
```python
def _stop_worker_threads(self):
    # Set cancellation flag
    self.cancelled = True
    
    # Wake up threads (put sentinel values)
    self.scan_queue.put(None)
    self.comparison_queue.put(None)
    self.priority_queue.put((0, None))
    
    # Join with timeout
    for thread in [self.scanner_thread, self.comparator_thread, 
                   self.priority_thread]:
        if thread and thread.is_alive():
            thread.join(timeout=1.0)
```

**Exception Handling**:
```python
def _directory_scanner_worker(self):
    try:
        while not self.cancelled:
            # Process tasks
            pass
    except Exception as e:
        # Log error
        self.log_error(f"Scanner thread error: {e}")
        # Set error flag
        self.scan_error = True
    finally:
        # Cleanup
        pass
```

## Error Handling

### Permission Errors

**Handling Strategy**:
1. Catch `PermissionError` during directory traversal
2. Mark FileInfo with `is_accessible = False`
3. Store error message in `error_message` field
4. Continue scanning accessible portions
5. Display error indicator in tree view
6. Show error count in status bar

**Implementation**:
```python
try:
    for item in path.iterdir():
        # Process item
except PermissionError as e:
    file_info = FileInfo(
        path=path,
        relative_path=rel_path,
        is_directory=True,
        size=0,
        mtime=0,
        is_accessible=False,
        error_message=str(e)
    )
```

### I/O Errors

**Handling Strategy**:
1. Catch `IOError`, `OSError` during file comparison
2. Mark node with error indicator
3. Log error for debugging
4. Continue with other files

### Cancellation

**Handling Strategy**:
1. Set `cancelled` flag in DirectoryScanner
2. Check flag periodically during scan
3. Clean up worker thread
4. Close viewer gracefully

## Testing

### Unit Tests

**Location**: `test/test_directory_diff_viewer.py`

Tests for core functionality:
- Tree building with various directory structures
- Difference classification logic
- Node navigation and bounds checking
- Expand/collapse state management
- Error handling with inaccessible files

### Integration Tests

**Location**: `test/test_directory_diff_filemanager_integration.py`

Tests for integration with other components:
- Invocation from FileManager
- UILayer stack push/pop
- DiffViewer integration
- Renderer integration

### Demo Scripts

**Location**: `demo/demo_directory_diff_viewer.py`

Demonstrates all features:
- Basic directory comparison
- Various difference types
- Navigation and interaction
- Error handling scenarios

## Future Enhancements

### Implemented Features

The following features have been implemented as part of the progressive scanning enhancement:

1. ✅ **Progressive Scanning**: Instant display with background processing
2. ✅ **Priority System**: Visible items scanned first
3. ✅ **On-Demand Scanning**: User expansion triggers immediate scanning
4. ✅ **Lazy Scanning**: One-sided directories scanned only when needed
5. ✅ **Thread Safety**: Robust synchronization with multiple worker threads
6. ✅ **Performance**: Handles 10,000+ files efficiently

### Potential Future Improvements

1. **Filtering Options**: Filter by file type, size, date
2. **Sorting Options**: Sort by name, size, date, difference type
3. **Copy/Move Operations**: Copy files from one side to other
4. **Synchronization**: Sync directories based on comparison
5. **Export Results**: Save comparison results to file
6. **Binary Diff**: Semantic diff for binary files
7. **Symbolic Link Handling**: Better handling of symlinks
8. **Parallel File Comparison**: Multiple comparator threads for faster content comparison

### Architecture Considerations

Any enhancements should:
- Maintain UILayer interface compatibility
- Follow TFM coding standards
- Use existing TFM components where possible
- Preserve performance characteristics
- Include comprehensive tests

## References

### Related Components

- **UILayer**: `src/tfm_ui_layer.py` - Base interface
- **DiffViewer**: `src/tfm_diff_viewer.py` - File diff viewer
- **FileManager**: `src/tfm_main.py` - Main application
- **Path**: `src/tfm_path.py` - File system abstraction
- **Colors**: `src/tfm_colors.py` - Color scheme

### Related Documentation

- **User Guide**: `doc/DIRECTORY_DIFF_VIEWER_FEATURE.md`
- **TFM User Guide**: `doc/TFM_USER_GUIDE.md`
- **UILayer System**: `doc/dev/UI_LAYER_STACK_SYSTEM.md`

## Maintenance Notes

### Code Organization

The entire feature is contained in a single file:
- `src/tfm_directory_diff_viewer.py` (~1500 lines with progressive scanning)

This follows the TFM pattern of self-contained UILayer implementations.

### Progressive Scanning Implementation

The progressive scanning feature adds:
- **~500 lines**: Worker thread implementations
- **~200 lines**: Priority system and queue management
- **~100 lines**: Thread synchronization and safety
- **Total**: ~800 additional lines for progressive scanning

### Dependencies

**Internal**:
- `tfm_ui_layer`: UILayer interface
- `tfm_path`: Path abstraction
- `tfm_colors`: Color constants
- `tfm_wide_char_utils`: Wide character support
- `tfm_scrollbar`: Scrollbar rendering
- `tfm_progress_animator`: Progress animation

**External**:
- `threading`: Worker threads for scanning
- `queue`: Thread-safe work queues
- `dataclasses`: Data structure definitions
- `enum`: Enumeration types

### Coding Standards

Follows TFM Python coding standards:
- Type hints for all public methods
- Docstrings for classes and complex methods
- Specific exception handling with logging
- No executable permissions on Python files
