# Design Document: Qt GUI Port for TFM

## Overview

This design document outlines the architecture for porting TFM (TUI File Manager) to support both Terminal User Interface (TUI) and Graphical User Interface (GUI) modes using Qt for Python. The design focuses on creating a clean abstraction layer that separates UI-specific code from business logic, enabling both interfaces to share the same core functionality while providing native experiences in each mode.

The key architectural principle is to extract all business logic from the current curses-based implementation into UI-agnostic modules, then implement both curses and Qt backends that conform to a common interface. This approach ensures code reusability, maintainability, and feature parity between both modes.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Entry Points                             │
│  ┌──────────────┐              ┌──────────────┐            │
│  │   tfm.py     │              │  tfm_qt.py   │            │
│  │  (TUI Mode)  │              │  (GUI Mode)  │            │
│  └──────┬───────┘              └──────┬───────┘            │
└─────────┼──────────────────────────────┼──────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  UI Abstraction Layer                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           IUIBackend Interface                        │  │
│  │  - render_panes()                                     │  │
│  │  - show_dialog()                                      │  │
│  │  - show_progress()                                    │  │
│  │  - get_input()                                        │  │
│  │  - handle_events()                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │                              │
    ┌─────┴─────┐                  ┌─────┴─────┐
    ▼           ▼                  ▼           ▼
┌─────────┐ ┌─────────┐      ┌─────────┐ ┌─────────┐
│ Curses  │ │  Qt     │      │ Curses  │ │  Qt     │
│ Pane    │ │ Pane    │      │ Dialog  │ │ Dialog  │
│ Renderer│ │ Renderer│      │ System  │ │ System  │
└─────────┘ └─────────┘      └─────────┘ └─────────┘
          │                              │
          └──────────────┬───────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ PaneManager  │  │FileOperations│  │ StateManager │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ LogManager   │  │ProgressMgr   │  │ CacheManager │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ArchiveOps    │  │ExternalPgms  │  │ S3 Support   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Storage Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Local Files  │  │  S3 Storage  │  │ SCP/FTP      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**Entry Points Layer:**
- `tfm.py`: Initializes curses environment and creates TUI backend
- `tfm_qt.py`: Initializes Qt application and creates GUI backend
- Both delegate to the same application controller

**UI Abstraction Layer:**
- Defines `IUIBackend` interface that both TUI and GUI must implement
- Provides UI-agnostic methods for rendering, input, and dialogs
- Ensures business logic never directly calls curses or Qt APIs

**Business Logic Layer:**
- Contains all existing managers (PaneManager, FileOperations, etc.)
- Refactored to remove direct curses dependencies
- Communicates with UI through abstraction layer only

**Storage Layer:**
- Existing Path abstraction already provides storage-agnostic interface
- No changes needed to support GUI mode

## Components and Interfaces

### 1. IUIBackend Interface

The core abstraction that both TUI and GUI backends must implement:

```python
class IUIBackend(ABC):
    """Abstract interface for UI backends"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the UI backend. Returns True on success."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up UI resources."""
        pass
    
    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        """Get current screen/window dimensions (height, width)."""
        pass
    
    @abstractmethod
    def render_panes(self, left_pane: Dict, right_pane: Dict, 
                    active_pane: str, layout: Dict):
        """Render the dual-pane file browser."""
        pass
    
    @abstractmethod
    def render_header(self, left_path: str, right_path: str, active_pane: str):
        """Render the header with directory paths."""
        pass
    
    @abstractmethod
    def render_footer(self, left_info: str, right_info: str, active_pane: str):
        """Render the footer with file counts and sort info."""
        pass
    
    @abstractmethod
    def render_status_bar(self, message: str, controls: List[Dict]):
        """Render the status bar with message and controls."""
        pass
    
    @abstractmethod
    def render_log_pane(self, messages: List[str], scroll_offset: int, 
                       height_ratio: float):
        """Render the log message pane."""
        pass
    
    @abstractmethod
    def show_dialog(self, dialog_type: str, **kwargs) -> Any:
        """Show a dialog and return user response."""
        pass
    
    @abstractmethod
    def show_progress(self, operation: str, current: int, total: int, 
                     message: str):
        """Show progress indicator for long operations."""
        pass
    
    @abstractmethod
    def get_input_event(self, timeout: int = -1) -> Optional[InputEvent]:
        """Get next input event (key press, mouse click, etc.)."""
        pass
    
    @abstractmethod
    def refresh(self):
        """Refresh the display."""
        pass
    
    @abstractmethod
    def set_color_scheme(self, scheme: str):
        """Set the color scheme (dark/light)."""
        pass
```

### 2. InputEvent Class

Unified input event representation:

```python
@dataclass
class InputEvent:
    """Represents a user input event"""
    type: str  # 'key', 'mouse', 'resize'
    key: Optional[int] = None  # Key code for keyboard events
    key_name: Optional[str] = None  # Human-readable key name
    mouse_x: Optional[int] = None  # Mouse coordinates
    mouse_y: Optional[int] = None
    mouse_button: Optional[int] = None  # Mouse button number
    modifiers: Set[str] = field(default_factory=set)  # 'ctrl', 'shift', 'alt'
```

### 3. CursesBackend Implementation

Wraps existing curses code:

```python
class CursesBackend(IUIBackend):
    """Curses-based TUI backend"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.color_manager = CursesColorManager()
        
    def initialize(self) -> bool:
        curses.curs_set(0)
        self.stdscr.keypad(True)
        self.color_manager.init_colors()
        return True
    
    def render_panes(self, left_pane, right_pane, active_pane, layout):
        # Existing draw_pane logic from FileManager
        pass
    
    def show_dialog(self, dialog_type, **kwargs):
        # Delegate to existing dialog classes
        if dialog_type == 'confirmation':
            return self._show_confirmation_dialog(**kwargs)
        elif dialog_type == 'input':
            return self._show_input_dialog(**kwargs)
        # ... other dialog types
    
    def get_input_event(self, timeout=-1) -> Optional[InputEvent]:
        if timeout >= 0:
            self.stdscr.timeout(timeout)
        key = self.stdscr.getch()
        if key == -1:
            return None
        return self._convert_curses_key(key)
```

### 4. QtBackend Implementation

Qt-based GUI implementation:

```python
class QtBackend(IUIBackend):
    """Qt-based GUI backend"""
    
    def __init__(self, app: QApplication):
        self.app = app
        self.main_window = TFMMainWindow()
        self.event_queue = queue.Queue()
        
    def initialize(self) -> bool:
        self.main_window.show()
        self.main_window.input_event.connect(self._on_input_event)
        return True
    
    def render_panes(self, left_pane, right_pane, active_pane, layout):
        self.main_window.left_pane_widget.update_files(left_pane['files'])
        self.main_window.right_pane_widget.update_files(right_pane['files'])
        self.main_window.set_active_pane(active_pane)
    
    def show_dialog(self, dialog_type, **kwargs):
        if dialog_type == 'confirmation':
            return QMessageBox.question(
                self.main_window, 
                kwargs.get('title', 'Confirm'),
                kwargs.get('message', ''),
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.Yes
        # ... other dialog types
    
    def get_input_event(self, timeout=-1) -> Optional[InputEvent]:
        try:
            return self.event_queue.get(timeout=timeout/1000.0 if timeout > 0 else None)
        except queue.Empty:
            return None
```

### 5. Application Controller

Refactored FileManager that works with any backend:

```python
class TFMApplication:
    """Main application controller - UI agnostic"""
    
    def __init__(self, ui_backend: IUIBackend, config: Config):
        self.ui = ui_backend
        self.config = config
        
        # Initialize business logic components (no UI dependencies)
        self.pane_manager = PaneManager(config)
        self.file_operations = FileOperations(config)
        self.log_manager = LogManager(config)
        self.progress_manager = ProgressManager()
        # ... other managers
        
    def run(self):
        """Main application loop"""
        if not self.ui.initialize():
            return False
            
        try:
            while not self.should_quit:
                self.render()
                event = self.ui.get_input_event(timeout=100)
                if event:
                    self.handle_input(event)
        finally:
            self.ui.cleanup()
    
    def render(self):
        """Render all UI components"""
        height, width = self.ui.get_screen_size()
        
        # Render header
        self.ui.render_header(
            str(self.pane_manager.left_pane['path']),
            str(self.pane_manager.right_pane['path']),
            self.pane_manager.active_pane
        )
        
        # Render panes
        layout = self._calculate_layout(height, width)
        self.ui.render_panes(
            self.pane_manager.left_pane,
            self.pane_manager.right_pane,
            self.pane_manager.active_pane,
            layout
        )
        
        # Render footer, status bar, log pane
        # ...
        
        self.ui.refresh()
    
    def handle_input(self, event: InputEvent):
        """Handle input events"""
        if event.type == 'key':
            self._handle_key_event(event)
        elif event.type == 'mouse':
            self._handle_mouse_event(event)
        elif event.type == 'resize':
            self.needs_full_redraw = True
```

## Data Models

### Pane Data Structure

Already well-defined in existing code, no changes needed:

```python
pane_data = {
    'path': Path,  # Current directory path
    'selected_index': int,  # Cursor position
    'scroll_offset': int,  # Scroll position
    'files': List[Path],  # File list
    'selected_files': Set[str],  # Multi-selection
    'sort_mode': str,  # 'name', 'size', 'date', 'ext'
    'sort_reverse': bool,  # Sort direction
    'filter_pattern': str,  # Active filter
}
```

### Layout Data Structure

Defines UI layout dimensions:

```python
@dataclass
class LayoutInfo:
    """UI layout dimensions"""
    screen_height: int
    screen_width: int
    left_pane_width: int
    right_pane_width: int
    pane_height: int
    log_height: int
    header_y: int
    panes_y: int
    footer_y: int
    status_y: int
    log_y: int
```

### Dialog Configuration

Unified dialog configuration:

```python
@dataclass
class DialogConfig:
    """Configuration for dialogs"""
    type: str  # 'confirmation', 'input', 'list', 'info', 'progress'
    title: str
    message: str
    choices: Optional[List[Dict]] = None  # For list/choice dialogs
    default_value: Optional[str] = None  # For input dialogs
    width_ratio: float = 0.6
    height_ratio: float = 0.7
    min_width: int = 40
    min_height: int = 15
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Before defining properties, let me analyze the acceptance criteria for testability:


### Property Reflection

After reviewing all testable criteria, I've identified the following consolidations to eliminate redundancy:

- Properties 3.4 and 3.5 (directory navigation) can be combined into a single comprehensive navigation property
- Properties 4.1, 4.2, 4.3 (mouse selection behaviors) are distinct and should remain separate
- Properties 5.3 and 5.4 (key bindings) can be combined into a general key binding property
- Properties 6.1, 6.3, 6.4 (dialog display) can be combined into a general dialog property
- Properties 7.2, 7.3, 7.4, 7.5 (progress behavior) are distinct aspects and should remain separate
- Properties 8.1, 8.2, 8.3 (external program integration) can be combined into a comprehensive external program property
- Properties 9.2, 9.3, 9.4, 9.5 (S3 operations) can be streamlined while maintaining distinct validation

### Correctness Properties

Property 1: Dual-pane layout consistency
*For any* UI backend (TUI or GUI), when the application launches, both backends should display two file listing panes with the same layout structure
**Validates: Requirements 1.3**

Property 2: Configuration consistency across modes
*For any* configuration file and user preferences, loading them in TUI mode or GUI mode should result in identical configuration data being used by the application
**Validates: Requirements 1.4**

Property 3: Feature parity between backends
*For any* core file management feature, both TUI and GUI backends should provide access to that feature through their respective interfaces
**Validates: Requirements 1.5**

Property 4: Business logic isolation
*For any* business logic module, analyzing its imports should show no direct dependencies on curses or Qt libraries
**Validates: Requirements 2.1, 2.5**

Property 5: File operation consistency
*For any* file operation (copy, move, delete, rename), executing it in TUI mode or GUI mode should produce identical results on the file system
**Validates: Requirements 2.2**

Property 6: Active pane highlighting
*For any* pane (left or right), when it becomes active, the UI should visually highlight it to indicate focus
**Validates: Requirements 3.2**

Property 7: File information display completeness
*For any* file displayed in a pane, the UI should show its filename, size, date, and permissions
**Validates: Requirements 3.3**

Property 8: Directory navigation
*For any* directory entry, selecting it should navigate into that directory, and selecting the parent directory entry should navigate up one level
**Validates: Requirements 3.4, 3.5**

Property 9: Mouse click selection toggle
*For any* file in GUI mode, clicking on it should toggle its selection state
**Validates: Requirements 4.1**

Property 10: Ctrl+click multi-selection
*For any* set of files in GUI mode, holding Ctrl and clicking each file should add all of them to the selection
**Validates: Requirements 4.2**

Property 11: Shift+click range selection
*For any* two files in GUI mode, selecting one file then Shift+clicking another should select all files between them (inclusive)
**Validates: Requirements 4.3**

Property 12: Selection visual feedback
*For any* selected file, the UI should visually highlight it to distinguish it from unselected files
**Validates: Requirements 4.4**

Property 13: Batch operation on selection
*For any* file operation invoked with multiple files selected, the operation should be applied to all selected files
**Validates: Requirements 4.5**

Property 14: Key binding consistency
*For any* key binding configured in the system, pressing that key in GUI mode should execute the same action as pressing it in TUI mode
**Validates: Requirements 5.1, 5.3, 5.4**

Property 15: Dialog display for operations
*For any* operation requiring user input (confirmation, text input, search), the system should display an appropriate dialog and wait for user response
**Validates: Requirements 6.1, 6.3, 6.4**

Property 16: Dialog modality
*For any* dialog displayed, the main window should be non-interactive until the dialog is dismissed
**Validates: Requirements 6.5**

Property 17: Progress bar updates
*For any* file copy operation, the progress bar should update to reflect the current completion percentage as files are copied
**Validates: Requirements 7.2**

Property 18: Current file display in progress
*For any* multi-file operation, the progress dialog should show the name of the file currently being processed
**Validates: Requirements 7.3**

Property 19: Progress dialog auto-close
*For any* long-running operation, when it completes successfully, the progress dialog should close automatically
**Validates: Requirements 7.4**

Property 20: Operation cancellation
*For any* cancellable operation, clicking Cancel in the progress dialog should abort the operation and stop further processing
**Validates: Requirements 7.5**

Property 21: External program integration
*For any* configured external program, it should be available in both TUI and GUI modes, receive selected files through environment variables, and use the same environment variable names in both modes
**Validates: Requirements 8.1, 8.2, 8.3**

Property 22: Post-operation refresh
*For any* external program that modifies files, when it completes, the file listing should be refreshed to show the changes
**Validates: Requirements 8.4**

Property 23: External program error handling
*For any* external program that fails, an error message should be displayed to the user
**Validates: Requirements 8.5**

Property 24: S3 object information display
*For any* S3 object displayed in a pane, the UI should show its name, size, and modification date
**Validates: Requirements 9.2**

Property 25: S3 backend consistency
*For any* S3 file operation, both TUI and GUI modes should use the same S3 backend implementation
**Validates: Requirements 9.3**

Property 26: S3 progress indicators
*For any* S3 operation in progress, appropriate progress indicators should be displayed
**Validates: Requirements 9.4**

Property 27: S3 error dialogs
*For any* S3 error in GUI mode, an error dialog should be displayed with the error message
**Validates: Requirements 9.5**

Property 28: Window geometry persistence
*For any* GUI window resize or move operation, the new dimensions and position should be saved to the configuration file
**Validates: Requirements 10.1, 10.2**

Property 29: Window geometry restoration
*For any* GUI launch with saved window geometry, the window should be restored to the saved size and position
**Validates: Requirements 10.3**

Property 30: Backend interface compliance
*For any* UI backend implementation, it should implement all methods defined in the IUIBackend interface
**Validates: Requirements 11.3**

Property 31: File operation behavior parity
*For any* file operation test case, executing it in TUI mode and GUI mode should produce identical results
**Validates: Requirements 11.4**

Property 32: Color scheme consistency
*For any* color definition used in TUI mode, the same color definition should be used in GUI mode where applicable
**Validates: Requirements 12.2**

Property 33: File type coloring
*For any* file type or attribute, files of that type should be displayed with consistent coloring based on the configured color scheme
**Validates: Requirements 12.3**

Property 34: Dialog style consistency
*For any* dialog displayed in the application, it should use the same styling approach as other dialogs
**Validates: Requirements 12.4**

Property 35: Dynamic theme switching
*For any* theme change operation, the GUI appearance should update immediately without requiring an application restart
**Validates: Requirements 12.5**

## Error Handling

### UI Backend Initialization Errors

- If curses initialization fails (TUI mode), display error message to stderr and exit gracefully
- If Qt initialization fails (GUI mode), display error dialog and exit gracefully
- Both modes should validate terminal/display capabilities before proceeding

### Input Event Handling Errors

- Invalid key codes should be logged but not crash the application
- Mouse events outside valid areas should be ignored
- Resize events should trigger safe re-layout calculations

### Dialog Errors

- If a dialog cannot be displayed (insufficient screen space), fall back to status bar messages
- Dialog rendering errors should not crash the application
- User cancellation of dialogs should be handled as a valid response

### Cross-Mode Compatibility Errors

- If a feature is not available in one mode, display appropriate message
- Configuration incompatibilities should use safe defaults
- Missing UI backend implementations should be caught at startup

## Testing Strategy

### Unit Testing

**Abstraction Layer Tests:**
- Test IUIBackend interface definition completeness
- Test InputEvent creation and conversion
- Test LayoutInfo calculations
- Test DialogConfig validation

**Business Logic Tests:**
- Test all managers (PaneManager, FileOperations, etc.) without UI dependencies
- Use mock UI backends to verify business logic behavior
- Test file operations produce identical results regardless of UI mode
- Test configuration loading and saving

**Backend Implementation Tests:**
- Test CursesBackend implements all IUIBackend methods
- Test QtBackend implements all IUIBackend methods
- Test input event conversion for both backends
- Test dialog display for both backends

### Integration Testing

**Cross-Mode Tests:**
- Launch both TUI and GUI modes and verify same configuration is loaded
- Perform same file operations in both modes and compare results
- Verify external programs work identically in both modes
- Verify S3 operations work identically in both modes

**UI Interaction Tests:**
- Test keyboard navigation in both modes
- Test mouse interaction in GUI mode
- Test dialog workflows in both modes
- Test progress indicators in both modes

### Property-Based Testing

Property-based tests will be written using the Hypothesis library for Python. Each correctness property will be implemented as a separate property-based test that generates random inputs and verifies the property holds.

**Test Configuration:**
- Each property-based test will run a minimum of 100 iterations
- Tests will use appropriate generators for file paths, selections, and operations
- Edge cases (empty directories, special characters, large files) will be explicitly included in generators

**Property Test Examples:**

```python
# Property 5: File operation consistency
@given(
    operation=st.sampled_from(['copy', 'move', 'delete', 'rename']),
    files=st.lists(st.text(min_size=1), min_size=1, max_size=10),
    mode=st.sampled_from(['tui', 'gui'])
)
def test_file_operation_consistency(operation, files, mode):
    """For any file operation, executing it in TUI or GUI mode should produce identical results"""
    # Setup test environment with files
    # Execute operation in specified mode
    # Verify file system state matches expected result
    pass

# Property 14: Key binding consistency
@given(
    key_binding=st.sampled_from(list(config.KEY_BINDINGS.keys())),
    mode=st.sampled_from(['tui', 'gui'])
)
def test_key_binding_consistency(key_binding, mode):
    """For any key binding, pressing it in GUI mode should execute same action as TUI mode"""
    # Get action for key binding
    # Execute in specified mode
    # Verify same action was triggered
    pass
```

### Manual Testing

**Visual Verification:**
- Verify GUI layout matches TUI layout conceptually
- Verify color schemes render correctly in both modes
- Verify dialogs are readable and properly sized
- Verify progress indicators animate smoothly

**Usability Testing:**
- Verify keyboard shortcuts work as expected in GUI
- Verify mouse interactions feel natural
- Verify window resizing works smoothly
- Verify theme switching updates immediately

## Implementation Notes

### Phase 1: Abstraction Layer
1. Define IUIBackend interface
2. Define InputEvent and supporting data structures
3. Extract business logic from FileManager into TFMApplication
4. Remove all curses dependencies from business logic modules

### Phase 2: Curses Backend
1. Implement CursesBackend wrapping existing curses code
2. Refactor existing dialog classes to work with abstraction
3. Test TUI mode works identically to current implementation
4. Ensure all tests pass with new architecture

### Phase 3: Qt Backend
1. Implement QtBackend with basic window and panes
2. Implement Qt dialogs matching TUI dialog functionality
3. Implement mouse interaction support
4. Implement keyboard shortcut handling

### Phase 4: Feature Parity
1. Implement all file operations in GUI mode
2. Implement external program support in GUI mode
3. Implement S3 support in GUI mode
4. Implement progress indicators in GUI mode

### Phase 5: Polish
1. Implement theme support in GUI mode
2. Implement window geometry persistence
3. Add GUI-specific enhancements (drag-and-drop, context menus)
4. Performance optimization

### Dependencies

**Required Libraries:**
- PySide6 or PyQt6 for Qt bindings
- Existing dependencies (curses, boto3, etc.) remain unchanged

**Optional Libraries:**
- QDarkStyle for dark theme support in Qt
- pytest-qt for Qt testing

### Configuration Changes

New configuration options to be added:

```python
# GUI-specific settings
GUI_WINDOW_WIDTH = 1200  # Default window width
GUI_WINDOW_HEIGHT = 800  # Default window height
GUI_WINDOW_X = None  # Saved window X position (None = center)
GUI_WINDOW_Y = None  # Saved window Y position (None = center)
GUI_FONT_FAMILY = 'Monospace'  # Font for file listings
GUI_FONT_SIZE = 10  # Font size
GUI_ENABLE_DRAG_DROP = True  # Enable drag-and-drop
GUI_SHOW_TOOLBAR = True  # Show toolbar with common actions
GUI_SHOW_MENUBAR = True  # Show menu bar
```

### Backward Compatibility

- Existing TUI mode remains fully functional
- Existing configuration files work without modification
- New GUI-specific config options are optional
- Users can continue using TUI exclusively if desired

### Performance Considerations

- GUI rendering should not block file operations
- Long operations should run in background threads
- Progress updates should be throttled to avoid UI lag
- File list updates should be incremental when possible

### Security Considerations

- GUI mode should respect same file permissions as TUI mode
- External program execution should use same security model
- No additional security risks introduced by GUI mode
- Configuration file permissions remain unchanged
