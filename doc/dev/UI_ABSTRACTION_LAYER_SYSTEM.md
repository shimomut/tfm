# UI Abstraction Layer System

## Overview

The UI Abstraction Layer is the architectural foundation that enables TFM to support multiple user interface backends (TUI and GUI) while maintaining a single codebase for business logic. This document provides comprehensive technical documentation for developers working with or extending the abstraction layer.

## Architecture

### Design Principles

1. **Separation of Concerns**: Business logic is completely isolated from UI rendering
2. **Interface-Based Design**: All UI backends implement a common interface
3. **Event-Driven Architecture**: Input handling uses unified event objects
4. **Backend Agnostic**: Application code works with any compliant backend

### Component Hierarchy

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
│              TFMApplication (Controller)                     │
│  - Manages application lifecycle                             │
│  - Coordinates business logic                                │
│  - Delegates UI operations to backend                        │
└─────────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  IUIBackend Interface                        │
│  - initialize() / cleanup()                                  │
│  - render_*() methods                                        │
│  - show_dialog() / show_progress()                           │
│  - get_input_event()                                         │
│  - set_color_scheme()                                        │
└─────────────────────────────────────────────────────────────┘
          │                              │
    ┌─────┴─────┐                  ┌─────┴─────┐
    ▼           ▼                  ▼           ▼
┌─────────┐ ┌─────────┐      ┌─────────┐ ┌─────────┐
│ Curses  │ │  Qt     │      │ Curses  │ │  Qt     │
│ Backend │ │ Backend │      │ Dialogs │ │ Dialogs │
└─────────┘ └─────────┘      └─────────┘ └─────────┘
```

## Core Components

### 1. IUIBackend Interface

The `IUIBackend` abstract base class defines the contract that all UI backends must implement.

**Location**: `src/tfm_ui_backend.py`

#### Interface Definition

```python
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, List, Any

class IUIBackend(ABC):
    """Abstract interface for UI backends"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the UI backend.
        
        Returns:
            bool: True if initialization successful, False otherwise
            
        Implementation Notes:
            - Set up display/window
            - Initialize color system
            - Configure input handling
            - Return False on any initialization failure
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """
        Clean up UI resources.
        
        Implementation Notes:
            - Release display/window resources
            - Restore terminal state (for TUI)
            - Close any open dialogs
            - Save any pending state
        """
        pass
    
    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get current screen/window dimensions.
        
        Returns:
            Tuple[int, int]: (height, width) in characters or pixels
            
        Implementation Notes:
            - TUI: Return terminal size in characters
            - GUI: Return window size in pixels or logical units
            - Handle resize events appropriately
        """
        pass
    
    @abstractmethod
    def render_panes(self, left_pane: Dict, right_pane: Dict, 
                    active_pane: str, layout: Dict):
        """
        Render the dual-pane file browser.
        
        Args:
            left_pane: Left pane data (path, files, cursor, selection)
            right_pane: Right pane data
            active_pane: 'left' or 'right'
            layout: Layout dimensions and positions
            
        Implementation Notes:
            - Display file listings with proper formatting
            - Highlight active pane
            - Show selection state
            - Apply file type coloring
            - Handle scrolling
        """
        pass
    
    @abstractmethod
    def render_header(self, left_path: str, right_path: str, active_pane: str):
        """
        Render the header with directory paths.
        
        Args:
            left_path: Left pane directory path
            right_path: Right pane directory path
            active_pane: 'left' or 'right'
            
        Implementation Notes:
            - Display current directory paths
            - Highlight active pane path
            - Truncate long paths appropriately
        """
        pass
    
    @abstractmethod
    def render_footer(self, left_info: str, right_info: str, active_pane: str):
        """
        Render the footer with file counts and sort info.
        
        Args:
            left_info: Left pane info string
            right_info: Right pane info string
            active_pane: 'left' or 'right'
            
        Implementation Notes:
            - Display file/directory counts
            - Show sort mode and filter info
            - Highlight active pane footer
        """
        pass
    
    @abstractmethod
    def render_status_bar(self, message: str, controls: List[Dict]):
        """
        Render the status bar with message and controls.
        
        Args:
            message: Status message to display
            controls: List of control hints (key, description)
            
        Implementation Notes:
            - Display status message prominently
            - Show available controls/shortcuts
            - Handle message overflow
        """
        pass
    
    @abstractmethod
    def render_log_pane(self, messages: List[str], scroll_offset: int, 
                       height_ratio: float):
        """
        Render the log message pane.
        
        Args:
            messages: List of log messages
            scroll_offset: Current scroll position
            height_ratio: Proportion of screen for log pane (0.0-1.0)
            
        Implementation Notes:
            - Display recent log messages
            - Support scrolling
            - Format messages with timestamps
            - Handle long messages
        """
        pass
    
    @abstractmethod
    def show_dialog(self, dialog_type: str, **kwargs) -> Any:
        """
        Show a dialog and return user response.
        
        Args:
            dialog_type: Type of dialog ('confirmation', 'input', 'list', 
                        'info', 'progress')
            **kwargs: Dialog-specific parameters
            
        Returns:
            Dialog result (type depends on dialog_type)
            
        Dialog Types:
            - confirmation: Returns bool (True/False/None for cancel)
            - input: Returns str or None
            - list: Returns selected item(s) or None
            - info: Returns None
            - progress: Returns None (updates via separate calls)
            
        Implementation Notes:
            - Make dialogs modal (block main window)
            - Handle user cancellation
            - Validate input where appropriate
            - Support keyboard navigation
        """
        pass
    
    @abstractmethod
    def show_progress(self, operation: str, current: int, total: int, 
                     message: str):
        """
        Show progress indicator for long operations.
        
        Args:
            operation: Operation name
            current: Current progress value
            total: Total progress value
            message: Current status message
            
        Implementation Notes:
            - Update progress bar
            - Display current file/operation
            - Support cancellation
            - Auto-close on completion
        """
        pass
    
    @abstractmethod
    def get_input_event(self, timeout: int = -1) -> Optional['InputEvent']:
        """
        Get next input event (key press, mouse click, etc.).
        
        Args:
            timeout: Timeout in milliseconds (-1 = wait forever)
            
        Returns:
            InputEvent object or None if timeout
            
        Implementation Notes:
            - Convert native events to InputEvent
            - Handle keyboard events
            - Handle mouse events (GUI)
            - Handle resize events
            - Return None on timeout
        """
        pass
    
    @abstractmethod
    def refresh(self):
        """
        Refresh the display.
        
        Implementation Notes:
            - Update screen/window
            - Process pending events
            - Flush output buffers
        """
        pass
    
    @abstractmethod
    def set_color_scheme(self, scheme: str):
        """
        Set the color scheme (dark/light).
        
        Args:
            scheme: Color scheme name ('dark' or 'light')
            
        Implementation Notes:
            - Apply color scheme immediately
            - Update all UI elements
            - Persist preference if needed
        """
        pass
```

### 2. InputEvent Class

Unified representation of user input events across all backends.

**Location**: `src/tfm_ui_backend.py`

#### Class Definition

```python
from dataclasses import dataclass, field
from typing import Optional, Set

@dataclass
class InputEvent:
    """Represents a user input event"""
    
    type: str  # 'key', 'mouse', 'resize'
    key: Optional[int] = None  # Key code for keyboard events
    key_name: Optional[str] = None  # Human-readable key name
    mouse_x: Optional[int] = None  # Mouse coordinates
    mouse_y: Optional[int] = None
    mouse_button: Optional[int] = None  # Mouse button number (1=left, 2=middle, 3=right)
    modifiers: Set[str] = field(default_factory=set)  # 'ctrl', 'shift', 'alt', 'meta'
```

#### Event Types

**Keyboard Events** (`type='key'`):
- `key`: Numeric key code
- `key_name`: String representation (e.g., 'F5', 'Enter', 'a')
- `modifiers`: Set of active modifiers

**Mouse Events** (`type='mouse'`):
- `mouse_x`, `mouse_y`: Click coordinates
- `mouse_button`: Button number
- `modifiers`: Set of active modifiers

**Resize Events** (`type='resize'`):
- No additional fields needed
- Signals that screen/window size changed

#### Creating InputEvent Objects

**From Curses**:
```python
def _convert_curses_key(self, key: int) -> InputEvent:
    """Convert curses key code to InputEvent"""
    if key == curses.KEY_RESIZE:
        return InputEvent(type='resize')
    
    # Handle special keys
    if key == curses.KEY_F5:
        return InputEvent(type='key', key=key, key_name='F5')
    
    # Handle regular characters
    if 32 <= key <= 126:
        return InputEvent(type='key', key=key, key_name=chr(key))
    
    # ... handle other keys
```

**From Qt**:
```python
def _convert_qt_key(self, event: QKeyEvent) -> InputEvent:
    """Convert Qt key event to InputEvent"""
    modifiers = set()
    if event.modifiers() & Qt.ControlModifier:
        modifiers.add('ctrl')
    if event.modifiers() & Qt.ShiftModifier:
        modifiers.add('shift')
    if event.modifiers() & Qt.AltModifier:
        modifiers.add('alt')
    
    key_name = event.text() or event.key()
    
    return InputEvent(
        type='key',
        key=event.key(),
        key_name=key_name,
        modifiers=modifiers
    )
```

### 3. TFMApplication Controller

The main application controller that coordinates business logic and UI operations.

**Location**: `src/tfm_application.py`

#### Key Responsibilities

1. **Lifecycle Management**: Initialize, run main loop, cleanup
2. **Business Logic Coordination**: Manage panes, file operations, state
3. **UI Delegation**: Call backend methods for rendering and input
4. **Event Handling**: Process input events and trigger actions

#### Main Loop Structure

```python
def run(self):
    """Main application loop"""
    if not self.ui.initialize():
        return False
        
    try:
        while not self.should_quit:
            # Render UI
            self.render()
            
            # Get input with timeout for animations
            event = self.ui.get_input_event(timeout=100)
            
            # Handle input
            if event:
                self.handle_input(event)
                
            # Update animations/progress
            self.update_animations()
            
    finally:
        self.ui.cleanup()
```

#### Rendering Flow

```python
def render(self):
    """Render all UI components"""
    # Get screen dimensions
    height, width = self.ui.get_screen_size()
    
    # Calculate layout
    layout = self._calculate_layout(height, width)
    
    # Render header
    self.ui.render_header(
        str(self.pane_manager.left_pane['path']),
        str(self.pane_manager.right_pane['path']),
        self.pane_manager.active_pane
    )
    
    # Render panes
    self.ui.render_panes(
        self.pane_manager.left_pane,
        self.pane_manager.right_pane,
        self.pane_manager.active_pane,
        layout
    )
    
    # Render footer
    self.ui.render_footer(
        self._get_pane_info('left'),
        self._get_pane_info('right'),
        self.pane_manager.active_pane
    )
    
    # Render status bar
    self.ui.render_status_bar(
        self.status_message,
        self._get_control_hints()
    )
    
    # Render log pane if visible
    if self.log_pane_visible:
        self.ui.render_log_pane(
            self.log_manager.get_messages(),
            self.log_scroll_offset,
            self.log_height_ratio
        )
    
    # Refresh display
    self.ui.refresh()
```

## Implementing a New Backend

### Step 1: Create Backend Class

Create a new file `src/tfm_<backend>_backend.py`:

```python
from tfm_ui_backend import IUIBackend, InputEvent
from typing import Optional, Tuple, Dict, List, Any

class MyBackend(IUIBackend):
    """My custom UI backend"""
    
    def __init__(self, *args, **kwargs):
        # Initialize backend-specific resources
        pass
    
    def initialize(self) -> bool:
        # Set up display/window
        # Initialize color system
        # Configure input handling
        return True
    
    def cleanup(self):
        # Release resources
        pass
    
    # Implement all other required methods...
```

### Step 2: Implement Rendering Methods

Each rendering method receives structured data and should display it appropriately:

```python
def render_panes(self, left_pane: Dict, right_pane: Dict, 
                active_pane: str, layout: Dict):
    """
    Pane data structure:
    {
        'path': Path object,
        'files': List[Path],
        'selected_index': int,
        'scroll_offset': int,
        'selected_files': Set[str],
        'sort_mode': str,
        'sort_reverse': bool,
        'filter_pattern': str
    }
    
    Layout structure:
    {
        'screen_height': int,
        'screen_width': int,
        'left_pane_width': int,
        'right_pane_width': int,
        'pane_height': int,
        'panes_y': int,
        'left_pane_x': int,
        'right_pane_x': int
    }
    """
    # Render left pane
    self._render_single_pane(
        left_pane,
        layout['left_pane_x'],
        layout['panes_y'],
        layout['left_pane_width'],
        layout['pane_height'],
        active=(active_pane == 'left')
    )
    
    # Render right pane
    self._render_single_pane(
        right_pane,
        layout['right_pane_x'],
        layout['panes_y'],
        layout['right_pane_width'],
        layout['pane_height'],
        active=(active_pane == 'right')
    )
```

### Step 3: Implement Input Handling

Convert native input events to `InputEvent` objects:

```python
def get_input_event(self, timeout: int = -1) -> Optional[InputEvent]:
    # Get native event from your UI framework
    native_event = self._get_native_event(timeout)
    
    if native_event is None:
        return None
    
    # Convert to InputEvent
    if isinstance(native_event, KeyboardEvent):
        return self._convert_keyboard_event(native_event)
    elif isinstance(native_event, MouseEvent):
        return self._convert_mouse_event(native_event)
    elif isinstance(native_event, ResizeEvent):
        return InputEvent(type='resize')
    
    return None
```

### Step 4: Implement Dialog System

Create dialog implementations for each dialog type:

```python
def show_dialog(self, dialog_type: str, **kwargs) -> Any:
    if dialog_type == 'confirmation':
        return self._show_confirmation_dialog(
            kwargs.get('title', 'Confirm'),
            kwargs.get('message', ''),
            kwargs.get('choices', ['Yes', 'No'])
        )
    elif dialog_type == 'input':
        return self._show_input_dialog(
            kwargs.get('title', 'Input'),
            kwargs.get('prompt', ''),
            kwargs.get('default', '')
        )
    # ... handle other dialog types
```

### Step 5: Create Entry Point

Create `tfm_<backend>.py`:

```python
#!/usr/bin/env python3
import sys
from tfm_application import TFMApplication
from tfm_<backend>_backend import MyBackend
from tfm_config import Config

def main():
    # Initialize backend
    backend = MyBackend()
    
    # Load configuration
    config = Config()
    
    # Create application
    app = TFMApplication(backend, config)
    
    # Run application
    return app.run()

if __name__ == '__main__':
    sys.exit(main())
```

### Step 6: Test Backend

Create comprehensive tests:

```python
# test/test_<backend>_backend.py
import pytest
from tfm_<backend>_backend import MyBackend
from tfm_ui_backend import InputEvent

def test_backend_implements_interface():
    """Verify backend implements all required methods"""
    backend = MyBackend()
    
    # Check all methods exist
    assert hasattr(backend, 'initialize')
    assert hasattr(backend, 'cleanup')
    assert hasattr(backend, 'get_screen_size')
    # ... check all methods

def test_backend_initialization():
    """Test backend initialization"""
    backend = MyBackend()
    assert backend.initialize() == True
    backend.cleanup()

def test_input_event_conversion():
    """Test native event conversion to InputEvent"""
    backend = MyBackend()
    backend.initialize()
    
    # Test keyboard event
    event = backend.get_input_event(timeout=0)
    # ... verify event structure
    
    backend.cleanup()
```

## Testing Strategy

### Unit Tests

Test each component in isolation:

1. **Interface Tests**: Verify interface definition is complete
2. **InputEvent Tests**: Test event creation and conversion
3. **Backend Tests**: Test each backend method independently
4. **Application Tests**: Test controller logic with mock backend

### Integration Tests

Test components working together:

1. **Cross-Backend Tests**: Same operations in TUI and GUI
2. **Event Flow Tests**: Input → processing → rendering
3. **Dialog Tests**: Dialog workflows in both backends
4. **File Operation Tests**: Operations work identically

### Property-Based Tests

Use Hypothesis to test properties:

```python
from hypothesis import given, strategies as st

@given(
    operation=st.sampled_from(['copy', 'move', 'delete']),
    backend=st.sampled_from(['curses', 'qt'])
)
def test_file_operation_consistency(operation, backend):
    """File operations produce identical results in all backends"""
    # Setup test environment
    # Execute operation with specified backend
    # Verify file system state
    pass
```

### Test Coverage Requirements

- **Business Logic**: 90%+ coverage
- **Backend Implementations**: 80%+ coverage
- **Integration Tests**: All major workflows
- **Property Tests**: All correctness properties

## Best Practices

### For Backend Implementers

1. **Follow the Interface**: Implement all methods exactly as specified
2. **Handle Errors Gracefully**: Never crash on invalid input
3. **Test Thoroughly**: Test with various screen sizes and inputs
4. **Document Limitations**: Note any backend-specific constraints
5. **Optimize Rendering**: Minimize unnecessary redraws

### For Application Developers

1. **Use Abstraction**: Never call backend-specific code directly
2. **Handle All Events**: Process all InputEvent types
3. **Validate Data**: Check data before passing to backend
4. **Test Both Modes**: Verify features work in TUI and GUI
5. **Document Behavior**: Explain expected UI behavior

### For Testers

1. **Test Both Backends**: Run tests with TUI and GUI
2. **Test Edge Cases**: Small screens, long filenames, etc.
3. **Test Performance**: Ensure responsive UI
4. **Test Accessibility**: Keyboard navigation, screen readers
5. **Test Integration**: External programs, S3, etc.

## Common Patterns

### Pattern 1: Conditional Backend Features

Some features may not be available in all backends:

```python
def handle_drag_drop(self, event):
    """Handle drag and drop (GUI only)"""
    if hasattr(self.ui, 'supports_drag_drop') and self.ui.supports_drag_drop():
        # Handle drag and drop
        pass
    else:
        # Show message that feature not available
        self.show_message("Drag and drop not available in this mode")
```

### Pattern 2: Backend-Specific Optimizations

Optimize for backend capabilities:

```python
def render(self):
    """Render UI with backend-specific optimizations"""
    if self.needs_full_redraw or not self.ui.supports_partial_updates():
        # Full redraw
        self._render_all()
    else:
        # Partial update (faster)
        self._render_changed_only()
```

### Pattern 3: Graceful Degradation

Provide fallbacks when features unavailable:

```python
def show_progress(self, operation, current, total, message):
    """Show progress with fallback"""
    try:
        self.ui.show_progress(operation, current, total, message)
    except NotImplementedError:
        # Fallback to status bar
        self.ui.render_status_bar(
            f"{operation}: {current}/{total} - {message}",
            []
        )
```

## Troubleshooting

### Common Issues

**Issue**: Backend method not called
- **Cause**: Method not implemented or named incorrectly
- **Solution**: Verify method signature matches interface exactly

**Issue**: Events not processed
- **Cause**: Event conversion incorrect
- **Solution**: Debug event conversion, check InputEvent structure

**Issue**: UI not updating
- **Cause**: Missing refresh() call
- **Solution**: Ensure refresh() called after rendering

**Issue**: Dialogs not modal
- **Cause**: Dialog implementation doesn't block
- **Solution**: Use proper modal dialog mechanism for backend

### Debugging Tips

1. **Enable Logging**: Use LogManager to track execution
2. **Print Events**: Log all InputEvent objects
3. **Verify Data**: Check data structures passed to backend
4. **Test Incrementally**: Test each method individually
5. **Compare Backends**: Run same operation in both modes

## Performance Considerations

### Rendering Optimization

- **Minimize Redraws**: Only redraw changed areas
- **Batch Updates**: Group multiple updates together
- **Cache Calculations**: Cache layout calculations
- **Throttle Updates**: Limit update frequency for animations

### Input Handling

- **Non-Blocking**: Use timeouts to keep UI responsive
- **Event Queuing**: Queue events if processing is slow
- **Debouncing**: Debounce rapid events (resize, scroll)

### Memory Management

- **Release Resources**: Clean up in cleanup() method
- **Avoid Leaks**: Don't hold references to large objects
- **Limit History**: Cap log message history
- **Clear Caches**: Clear caches when appropriate

## Future Extensions

### Potential New Backends

- **Web Backend**: Browser-based interface
- **Mobile Backend**: Touch-optimized interface
- **Voice Backend**: Voice-controlled interface
- **VR Backend**: Virtual reality interface

### Interface Evolution

When adding new features to the interface:

1. **Propose Change**: Document proposed addition
2. **Discuss Impact**: Consider impact on all backends
3. **Provide Default**: Offer default implementation
4. **Update Docs**: Update this documentation
5. **Update Tests**: Add tests for new functionality

## References

- **Source Code**: `src/tfm_ui_backend.py` - Interface definition
- **TUI Backend**: `src/tfm_curses_backend.py` - Curses implementation
- **GUI Backend**: `src/tfm_qt_backend.py` - Qt implementation
- **Application**: `src/tfm_application.py` - Controller implementation
- **Tests**: `test/test_*_backend.py` - Backend tests

## Conclusion

The UI Abstraction Layer provides a clean, maintainable architecture for supporting multiple user interfaces in TFM. By following the patterns and practices outlined in this document, developers can create new backends, extend existing ones, and maintain the codebase effectively.

For questions or contributions, please refer to the project's contribution guidelines.
