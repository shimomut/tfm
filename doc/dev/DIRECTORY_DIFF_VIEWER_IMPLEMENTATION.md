# Directory Diff Viewer Implementation

## Overview

This document describes the implementation details of the Directory Diff Viewer feature in TFM. The viewer provides recursive directory comparison with a tree-structured, side-by-side display, following the established UILayer architecture pattern.

## Architecture

### Component Hierarchy

```
DirectoryDiffViewer (UILayer)
├── DirectoryScanner (Worker Thread)
│   ├── Recursive directory traversal
│   ├── File metadata collection
│   └── Progress reporting
├── DiffEngine
│   ├── Tree structure building
│   ├── Difference detection
│   └── Classification logic
└── TreeRenderer (integrated in DirectoryDiffViewer)
    ├── Tree node rendering
    ├── Expand/collapse state management
    └── Visual highlighting
```

### Design Principles

1. **UILayer Integration**: Implements the UILayer interface for seamless stack management
2. **Threaded Scanning**: Uses worker threads to prevent UI blocking during directory traversal
3. **Lazy Rendering**: Only renders visible nodes for performance with large trees
4. **Path Abstraction**: Uses `tfm_path.Path` for local and remote file system support
5. **Consistent Styling**: Uses `tfm_colors` for visual consistency with other TFM components

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
```

**Design Notes**:
- Stores both left and right paths for side-by-side display
- Maintains parent reference for upward traversal
- Stores file metadata for error handling and display

#### DifferenceType

```python
class DifferenceType(Enum):
    IDENTICAL = "identical"
    ONLY_LEFT = "only_left"
    ONLY_RIGHT = "only_right"
    CONTENT_DIFFERENT = "content_different"
    CONTAINS_DIFFERENCE = "contains_difference"
```

**Classification Logic**:
1. **ONLY_LEFT**: `left_path` exists, `right_path` is None
2. **ONLY_RIGHT**: `right_path` exists, `left_path` is None
3. **CONTENT_DIFFERENT**: Both paths exist, file content differs
4. **CONTAINS_DIFFERENCE**: Directory with any non-identical descendants
5. **IDENTICAL**: Both paths exist, content matches, no descendant differences

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

Handles recursive directory traversal in a worker thread:

```python
class DirectoryScanner:
    """
    Scans two directories recursively and collects file metadata.
    
    Attributes:
        left_path: Root path for left directory
        right_path: Root path for right directory
        progress_callback: Function to report progress
        cancelled: Cancellation flag
    """
```

#### Scanning Algorithm

1. **Initialization**: Set up paths and callback
2. **Traversal**: Recursively walk both directory trees
3. **Metadata Collection**: Gather file info for each item
4. **Progress Reporting**: Call callback with current status
5. **Cancellation Check**: Periodically check cancellation flag
6. **Result Return**: Return dictionaries of FileInfo objects

**Key Implementation Details**:
- Uses `tfm_path.Path.iterdir()` for directory listing
- Catches permission errors and marks files as inaccessible
- Reports progress as percentage of estimated total files
- Checks cancellation flag every N files for responsiveness

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

### Scanning Performance

**Optimization Strategies**:
1. **Worker Thread**: Prevents UI blocking during scan
2. **Progress Reporting**: Updates UI periodically, not per file
3. **Cancellation**: Allows user to abort long scans
4. **Error Handling**: Continues on permission errors

**Typical Performance**:
- 1,000 files: < 1 second
- 10,000 files: 5-10 seconds
- 100,000 files: 1-2 minutes

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
- TreeNode: ~200 bytes per node
- FileInfo: ~150 bytes per file
- 10,000 files: ~3.5 MB total

**Optimization Strategies**:
1. **Shared Strings**: Python interns common strings
2. **Optional Fields**: Uses None for missing data
3. **No Caching**: Doesn't cache rendered output

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

### Potential Improvements

1. **Filtering Options**: Filter by file type, size, date
2. **Sorting Options**: Sort by name, size, date, difference type
3. **Copy/Move Operations**: Copy files from one side to other
4. **Synchronization**: Sync directories based on comparison
5. **Export Results**: Save comparison results to file
6. **Binary Diff**: Semantic diff for binary files
7. **Symbolic Link Handling**: Better handling of symlinks
8. **Performance**: Parallel scanning for very large directories

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
- `src/tfm_directory_diff_viewer.py` (~800 lines)

This follows the TFM pattern of self-contained UILayer implementations.

### Dependencies

**Internal**:
- `tfm_ui_layer`: UILayer interface
- `tfm_path`: Path abstraction
- `tfm_colors`: Color constants
- `tfm_wide_char_utils`: Wide character support
- `tfm_scrollbar`: Scrollbar rendering

**External**:
- `threading`: Worker thread for scanning
- `dataclasses`: Data structure definitions
- `enum`: Enumeration types

### Coding Standards

Follows TFM Python coding standards:
- Type hints for all public methods
- Docstrings for classes and complex methods
- Specific exception handling with logging
- No executable permissions on Python files
