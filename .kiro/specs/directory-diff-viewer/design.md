# Design Document

## Overview

The Directory Diff Viewer is a new UILayer component that provides recursive directory comparison with a tree-structured, side-by-side display. It follows the established TFM architecture pattern used by TextViewer and DiffViewer, implementing the UILayer interface for seamless integration with the UI layer stack system.

The viewer compares two directory trees recursively, detects differences at both file and directory levels, and presents results in an expandable/collapsible tree structure with visual highlighting for different types of changes.

## Architecture

### Component Structure

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
├── TreeRenderer
│   ├── Tree node rendering
│   ├── Expand/collapse state management
│   └── Visual highlighting
└── UILayer Interface Implementation
    ├── Event handling (keyboard navigation)
    ├── Rendering coordination
    └── Lifecycle management
```

### Integration with TFM

The Directory Diff Viewer integrates with TFM's existing architecture:

1. **UILayer Stack**: Implements the UILayer interface to participate in the layer stack system
2. **File Manager Integration**: Invoked from FileManager with left and right pane paths
3. **Path Abstraction**: Uses tfm_path.Path for local and remote file system support
4. **Color System**: Uses tfm_colors for consistent visual styling
5. **Renderer**: Uses TTK renderer for cross-platform rendering

## Components and Interfaces

### DirectoryDiffViewer Class

Main class implementing the UILayer interface:

```python
class DirectoryDiffViewer(UILayer):
    def __init__(self, renderer, left_path: Path, right_path: Path):
        """
        Initialize the directory diff viewer.
        
        Args:
            renderer: TTK renderer instance
            left_path: Path to left directory
            right_path: Path to right directory
        """
        
    # UILayer interface methods
    def handle_key_event(self, event) -> bool
    def handle_char_event(self, event) -> bool
    def handle_system_event(self, event) -> bool
    def render(self, renderer) -> None
    def is_full_screen(self) -> bool
    def needs_redraw(self) -> bool
    def mark_dirty(self) -> None
    def clear_dirty(self) -> None
    def should_close(self) -> bool
    def on_activate(self) -> None
    def on_deactivate(self) -> None
    
    # Core functionality methods
    def start_scan(self) -> None
    def build_tree(self) -> None
    def expand_node(self, node_index: int) -> None
    def collapse_node(self, node_index: int) -> None
    def open_file_diff(self, node_index: int) -> None
```

### TreeNode Data Structure

Represents a single node in the directory tree:

```python
@dataclass
class TreeNode:
    name: str                    # File or directory name
    left_path: Optional[Path]    # Path in left directory (None if only in right)
    right_path: Optional[Path]   # Path in right directory (None if only in left)
    is_directory: bool           # True for directories, False for files
    difference_type: DifferenceType  # Classification of difference
    depth: int                   # Nesting level (0 = root)
    is_expanded: bool            # Expansion state (directories only)
    children: List[TreeNode]     # Child nodes (directories only)
    parent: Optional[TreeNode]   # Parent node reference
```

### DifferenceType Enumeration

```python
class DifferenceType(Enum):
    IDENTICAL = "identical"              # Same in both locations
    ONLY_LEFT = "only_left"              # Exists only in left directory
    ONLY_RIGHT = "only_right"            # Exists only in right directory
    CONTENT_DIFFERENT = "content_different"  # File content differs
    CONTAINS_DIFFERENCE = "contains_difference"  # Directory contains differences
```

### DirectoryScanner Class

Handles recursive directory traversal in a worker thread:

```python
class DirectoryScanner:
    def __init__(self, left_path: Path, right_path: Path, progress_callback):
        """
        Initialize the directory scanner.
        
        Args:
            left_path: Root path for left directory
            right_path: Root path for right directory
            progress_callback: Callback function for progress updates
        """
        
    def scan(self) -> Tuple[Dict[str, FileInfo], Dict[str, FileInfo]]:
        """
        Scan both directories recursively.
        
        Returns:
            Tuple of (left_files, right_files) dictionaries
            Keys are relative paths, values are FileInfo objects
        """
        
    def cancel(self) -> None:
        """Cancel the scanning operation."""
```

### FileInfo Data Structure

Stores metadata for a single file or directory:

```python
@dataclass
class FileInfo:
    path: Path                   # Full path to file/directory
    relative_path: str           # Relative path from root
    is_directory: bool           # True for directories
    size: int                    # File size in bytes (0 for directories)
    mtime: float                 # Modification time
    is_accessible: bool          # False if permission denied
    error_message: Optional[str] # Error message if not accessible
```

### DiffEngine Class

Builds the tree structure and detects differences:

```python
class DiffEngine:
    def __init__(self, left_files: Dict[str, FileInfo], right_files: Dict[str, FileInfo]):
        """
        Initialize the diff engine.
        
        Args:
            left_files: Dictionary of files from left directory
            right_files: Dictionary of files from right directory
        """
        
    def build_tree(self) -> TreeNode:
        """
        Build a unified tree structure from both file sets.
        
        Returns:
            Root TreeNode containing the entire tree
        """
        
    def classify_node(self, node: TreeNode) -> DifferenceType:
        """
        Classify a node's difference type.
        
        Args:
            node: TreeNode to classify
            
        Returns:
            DifferenceType classification
        """
        
    def compare_file_content(self, left_path: Path, right_path: Path) -> bool:
        """
        Compare file content for equality.
        
        Args:
            left_path: Path to left file
            right_path: Path to right file
            
        Returns:
            True if files are identical, False otherwise
        """
```

## Data Models

### Tree Structure

The tree is stored as a flat list of visible nodes for efficient rendering:

```python
visible_nodes: List[TreeNode]  # Flattened list of visible nodes
node_index_map: Dict[TreeNode, int]  # Map nodes to their index in visible_nodes
```

When a directory is collapsed, its children are removed from `visible_nodes`. When expanded, children are inserted at the appropriate position.

### Rendering State

```python
scroll_offset: int              # First visible line index
cursor_position: int            # Current cursor position (index in visible_nodes)
horizontal_offset: int          # Horizontal scroll offset
show_identical: bool            # Whether to show identical files
_dirty: bool                    # Needs redraw flag
_should_close: bool             # Close request flag
```

### Progress State

```python
scan_in_progress: bool          # True while scanning
scan_progress: float            # Progress percentage (0.0 to 1.0)
scan_status: str                # Current status message
scan_thread: Optional[Thread]   # Worker thread reference
scan_cancelled: bool            # Cancellation flag
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Tree Structure Completeness

*For any* pair of directories, the built tree structure should contain all unique paths from both directories, with no paths duplicated or omitted.

**Validates: Requirements 2.4**

### Property 2: Difference Classification Consistency

*For any* tree node, its difference classification should accurately reflect the comparison result: identical files should be marked identical, files existing only on one side should be marked only-left or only-right, and files with different content should be marked content-different.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 3: Directory Difference Propagation

*For any* directory node, if any descendant has a non-identical classification, the directory should be classified as contains-difference.

**Validates: Requirements 4.4**

### Property 4: Tree Navigation Consistency

*For any* visible tree node, navigating up then down should return to the same node, and the cursor should never move to an invalid position.

**Validates: Requirements 7.1**

### Property 5: Expand/Collapse State Preservation

*For any* directory node, expanding then collapsing should restore the original visible node list, and the cursor should remain on a valid node.

**Validates: Requirements 7.2, 7.3**

### Property 6: Side-by-Side Alignment

*For any* tree node, if the node exists in both directories, both paths should be displayed in the same row; if it exists only on one side, the other side should display a blank space.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4**

### Property 7: File Content Comparison Accuracy

*For any* two files with the same name, the content comparison should return true if and only if the files have identical byte content.

**Validates: Requirements 4.3**

### Property 8: Progress Reporting Monotonicity

*For any* scanning operation, progress values should be monotonically increasing from 0.0 to 1.0, and the final progress should always be 1.0 when complete.

**Validates: Requirements 10.2**

### Property 9: Cancellation Responsiveness

*For any* scanning operation, when cancellation is requested, the scan should stop within a reasonable time and the viewer should close gracefully.

**Validates: Requirements 10.4, 10.5**

### Property 10: Error Handling Graceful Degradation

*For any* inaccessible directory or file, the system should mark it with an error indicator and continue processing accessible portions, never crashing or hanging.

**Validates: Requirements 11.1, 11.2**

## Error Handling

### Permission Errors

When a directory or file cannot be accessed due to permissions:
- Mark the node with an error indicator (special color/icon)
- Store error message in node metadata
- Continue scanning accessible portions
- Display error count in status bar

### I/O Errors

When file operations fail:
- Catch OSError, IOError exceptions
- Mark affected nodes with error indicators
- Log errors for debugging
- Allow user to continue viewing accessible data

### Cancellation

When user cancels scanning:
- Set cancellation flag
- Worker thread checks flag periodically
- Clean up partial results
- Close viewer gracefully

### Empty or Identical Directories

When both directories are empty or identical:
- Display appropriate message in content area
- Show statistics in status bar
- Allow user to close viewer normally

## Testing Strategy

### Unit Tests

Unit tests verify specific examples and edge cases:

1. **Tree Building**: Test tree construction with various directory structures
2. **Difference Detection**: Test classification logic with known file pairs
3. **Node Navigation**: Test cursor movement and boundary conditions
4. **Expand/Collapse**: Test state transitions and visible node updates
5. **Error Handling**: Test permission errors, I/O errors, and cancellation
6. **Edge Cases**: Empty directories, single-file directories, deeply nested structures

### Property-Based Tests

Property tests verify universal properties across all inputs (minimum 100 iterations each):

1. **Property 1 Test**: Generate random directory structures, verify all paths appear in tree
   - **Feature: directory-diff-viewer, Property 1: Tree Structure Completeness**

2. **Property 2 Test**: Generate random file pairs, verify classification matches actual comparison
   - **Feature: directory-diff-viewer, Property 2: Difference Classification Consistency**

3. **Property 3 Test**: Generate random directory trees, verify parent directories reflect child differences
   - **Feature: directory-diff-viewer, Property 3: Directory Difference Propagation**

4. **Property 4 Test**: Generate random trees, perform random navigation sequences, verify consistency
   - **Feature: directory-diff-viewer, Property 4: Tree Navigation Consistency**

5. **Property 5 Test**: Generate random trees, perform random expand/collapse sequences, verify state preservation
   - **Feature: directory-diff-viewer, Property 5: Expand/Collapse State Preservation**

6. **Property 6 Test**: Generate random trees, verify all nodes have correct alignment
   - **Feature: directory-diff-viewer, Property 6: Side-by-Side Alignment**

7. **Property 7 Test**: Generate random file pairs, verify content comparison accuracy
   - **Feature: directory-diff-viewer, Property 7: File Content Comparison Accuracy**

8. **Property 8 Test**: Generate random directory structures, verify progress monotonicity
   - **Feature: directory-diff-viewer, Property 8: Progress Reporting Monotonicity**

9. **Property 9 Test**: Generate random directory structures, test cancellation at random points
   - **Feature: directory-diff-viewer, Property 9: Cancellation Responsiveness**

10. **Property 10 Test**: Generate directory structures with simulated permission errors, verify graceful degradation
    - **Feature: directory-diff-viewer, Property 10: Error Handling Graceful Degradation**

### Integration Tests

Integration tests verify the viewer works correctly with the rest of TFM:

1. **UILayer Stack Integration**: Test push/pop operations with the layer stack
2. **FileManager Integration**: Test invocation from FileManager with various directory pairs
3. **DiffViewer Integration**: Test opening file diff viewer from directory diff viewer
4. **Renderer Integration**: Test rendering with different terminal sizes
5. **Path Abstraction**: Test with both local and remote paths (if supported)

### Testing Framework

- **Unit Tests**: Python's unittest framework
- **Property Tests**: Hypothesis library for property-based testing
- **Test Data Generation**: Hypothesis strategies for generating directory structures
- **Mocking**: unittest.mock for isolating components during testing
