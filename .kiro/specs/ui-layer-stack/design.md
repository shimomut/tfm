# Design Document: UI Layer Stack System

## Overview

The UI Layer Stack System replaces the current if-elif based dialog and viewer management in TFM with a dynamic stack-based architecture. This design introduces a `UILayerStack` class that manages UI components as layers, with proper event routing, rendering order, and performance optimizations for full-screen layers.

The key insight is that UI components in TFM naturally form a stack: the FileManager main screen is always at the bottom, dialogs and viewers are pushed on top, and only the topmost layer receives input events. By making this stack structure explicit, we eliminate complex conditional logic and make the system more maintainable and extensible.

## Architecture

### High-Level Structure

```
┌─────────────────────────────────────┐
│      TFMEventCallback               │
│  (receives events from TTK)         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      FileManager                    │
│  - Owns UILayerStack                │
│  - Delegates to stack               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      UILayerStack                   │
│  - Manages layer stack              │
│  - Routes events to top layer       │
│  - Coordinates rendering            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      UILayer (interface)            │
│  - handle_key_event()               │
│  - handle_char_event()              │
│  - render()                         │
│  - is_full_screen()                 │
│  - should_close()                   │
│  - on_activate() / on_deactivate()  │
└─────────────────────────────────────┘
               │
               ├─────────────────────────┬─────────────────────────┐
               │                         │                         │
               ▼                         ▼                         ▼
┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
│  FileManagerLayer    │   │  ListDialog          │   │  TextViewer          │
│  (bottom layer)      │   │  InfoDialog          │   │  DiffViewer          │
│  (wraps FileManager) │   │  SearchDialog        │   │  (full-screen)       │
│                      │   │  JumpDialog          │   │                      │
│                      │   │  DrivesDialog        │   │                      │
│                      │   │  BatchRenameDialog   │   │                      │
│                      │   │  (regular layers)    │   │                      │
└──────────────────────┘   └──────────────────────┘   └──────────────────────┘
```

**Key Changes from Current Architecture:**
- Dialog and viewer classes directly implement UILayer interface (no wrapper classes)
- FileManagerLayer wraps FileManager main screen logic
- UILayerStack manages all layers uniformly
- Event routing and rendering are centralized in UILayerStack

### Layer Stack Behavior

The stack maintains layers in LIFO order:
- **Bottom**: FileManagerLayer (always present, never removed)
- **Middle**: Any combination of dialog layers and full-screen viewers
- **Top**: The most recently added layer (dialog or viewer)

**Important**: Full-screen layers can appear anywhere in the stack, not just at the top. For example:
- User opens TextViewer (full-screen) → Stack: [FileManager, TextViewer]
- User presses a key that opens a help dialog → Stack: [FileManager, TextViewer, HelpDialog]
- The TextViewer is now in the middle, but it's still full-screen

Event flow:
1. Event arrives at TFMEventCallback
2. FileManager.handle_input() delegates to UILayerStack
3. UILayerStack routes event to top layer (HelpDialog in example above)
4. If top layer doesn't consume event, propagate to next layer (TextViewer)
5. Continue until event is consumed or bottom layer is reached

Rendering flow (intelligent dirty tracking):
1. UILayerStack.render() called from main loop
2. Scan layers from bottom to top to find which layers need redrawing:
   - If a layer has dirty content (needs_redraw() returns True), it must be redrawn
   - When a layer is redrawn, all layers above it must also be redrawn (mark_dirty())
3. Identify topmost full-screen layer (if any) by scanning from top to bottom
4. Determine the starting layer for rendering:
   - Start from the topmost full-screen layer (skip all layers below it)
   - OR start from the lowest dirty layer (if no full-screen layer obscures it)
5. Render layers from starting point upward, but only if they need redrawing
6. Clear dirty flags after successful rendering
7. Coordinate screen refresh with TTK backend

**Rendering Optimization Examples**:

Example 1: Dialog content changes
- Stack: [FileManager (full-screen, clean), TextViewer (full-screen, clean), HelpDialog (overlay, dirty)]
- Topmost full-screen layer: TextViewer (at index 1)
- Starting layer: TextViewer (full-screen layer)
- Layers to check: TextViewer (clean, skip), HelpDialog (dirty, render)
- Result: Only HelpDialog is redrawn

Example 2: FileManager content changes
- Stack: [FileManager (full-screen, dirty), HelpDialog (overlay, clean)]
- No full-screen layer above FileManager
- Starting layer: FileManager (lowest dirty layer)
- When FileManager is redrawn, HelpDialog is marked dirty (lower layer redrew)
- Layers to render: FileManager (dirty, render), HelpDialog (now dirty, render)
- Result: Both layers are redrawn

Example 3: Full-screen viewer obscures dirty lower layer
- Stack: [FileManager (full-screen, dirty), TextViewer (full-screen, clean)]
- Topmost full-screen layer: TextViewer (at index 1)
- Starting layer: TextViewer (full-screen layer)
- Layers to check: TextViewer (clean, skip)
- Result: Nothing is redrawn (FileManager is obscured, TextViewer is clean)

This optimization ensures:
- Only dirty layers are redrawn
- Layers above a redrawn layer are also redrawn (to maintain visual correctness)
- Layers below full-screen layers are never redrawn (they're not visible)

## Components and Interfaces

### UILayer Interface

The `UILayer` interface defines the contract that all UI layers must implement:

```python
from abc import ABC, abstractmethod
from ttk import KeyEvent, CharEvent

class UILayer(ABC):
    """
    Abstract base class for UI layers in the layer stack.
    
    All UI components that participate in the layer stack must implement
    this interface to handle events, rendering, and lifecycle management.
    """
    
    @abstractmethod
    def handle_key_event(self, event: KeyEvent) -> bool:
        """
        Handle a key event.
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed, False to propagate to next layer
        """
        pass
    
    @abstractmethod
    def handle_char_event(self, event: CharEvent) -> bool:
        """
        Handle a character event.
        
        Args:
            event: CharEvent to handle
        
        Returns:
            True if the event was consumed, False to propagate to next layer
        """
        pass
    
    @abstractmethod
    def render(self, renderer) -> None:
        """
        Render the layer's content.
        
        Args:
            renderer: TTK renderer instance for drawing
        """
        pass
    
    @abstractmethod
    def is_full_screen(self) -> bool:
        """
        Query if this layer occupies the full screen.
        
        Full-screen layers obscure all layers below them, enabling
        rendering optimizations.
        
        Returns:
            True if this layer is full-screen, False otherwise
        """
        pass
    
    @abstractmethod
    def needs_redraw(self) -> bool:
        """
        Query if this layer has dirty content that needs redrawing.
        
        The layer stack uses this to optimize rendering by only redrawing
        layers that have changed. A layer should return True if:
        - Its content has changed since last render
        - It needs to redraw due to a lower layer redrawing
        
        Returns:
            True if the layer needs redrawing, False otherwise
        """
        pass
    
    @abstractmethod
    def mark_dirty(self) -> None:
        """
        Mark this layer as needing a redraw.
        
        Called by the layer itself when its content changes, or by the
        layer stack when a lower layer has been redrawn.
        """
        pass
    
    @abstractmethod
    def clear_dirty(self) -> None:
        """
        Clear the dirty flag after rendering.
        
        Called by the layer stack after successfully rendering this layer.
        """
        pass
    
    @abstractmethod
    def should_close(self) -> bool:
        """
        Query if this layer wants to close.
        
        The layer stack checks this after event handling to determine
        if the layer should be popped from the stack.
        
        Returns:
            True if the layer should be closed, False otherwise
        """
        pass
    
    @abstractmethod
    def on_activate(self) -> None:
        """
        Called when this layer becomes the top layer.
        
        Use this to initialize state, show cursor, etc.
        """
        pass
    
    @abstractmethod
    def on_deactivate(self) -> None:
        """
        Called when this layer is no longer the top layer.
        
        Use this to clean up state, hide cursor, etc.
        """
        pass
```

### UILayerStack Class

The `UILayerStack` class manages the stack of UI layers:

```python
from typing import List, Optional
from ttk import KeyEvent, CharEvent

class UILayerStack:
    """
    Manages a stack of UI layers with event routing and rendering coordination.
    
    The stack maintains layers in LIFO order, with the FileManager main screen
    as the permanent bottom layer. Events are routed to the top layer first,
    with propagation to lower layers if not consumed. Rendering is optimized
    by skipping layers obscured by full-screen layers.
    """
    
    def __init__(self, bottom_layer: UILayer, log_manager=None):
        """
        Initialize the layer stack with a bottom layer.
        
        Args:
            bottom_layer: The permanent bottom layer (FileManager main screen)
            log_manager: Optional LogManager for error logging
        """
        self._layers: List[UILayer] = [bottom_layer]
        self._log_manager = log_manager
    
    def push(self, layer: UILayer) -> None:
        """
        Push a new layer onto the top of the stack.
        
        The previous top layer is deactivated, and the new layer is activated.
        
        Args:
            layer: Layer to push onto the stack
        """
        # Deactivate current top layer
        if self._layers:
            self._layers[-1].on_deactivate()
        
        # Push new layer and activate it
        self._layers.append(layer)
        layer.on_activate()
    
    def pop(self) -> Optional[UILayer]:
        """
        Pop the top layer from the stack.
        
        The bottom layer cannot be popped. After popping, the new top layer
        is activated.
        
        Returns:
            The popped layer, or None if the operation was rejected
        """
        # Prevent removal of bottom layer
        if len(self._layers) <= 1:
            if self._log_manager:
                self._log_manager.add_message("WARNING", "Cannot remove bottom layer from UI stack")
            return None
        
        # Pop top layer and deactivate it
        layer = self._layers.pop()
        layer.on_deactivate()
        
        # Activate new top layer
        if self._layers:
            self._layers[-1].on_activate()
        
        return layer
    
    def get_top_layer(self) -> UILayer:
        """
        Get the current top layer.
        
        Returns:
            The top layer in the stack
        """
        return self._layers[-1]
    
    def get_layer_count(self) -> int:
        """
        Get the number of layers in the stack.
        
        Returns:
            Number of layers (always >= 1)
        """
        return len(self._layers)
    
    def handle_key_event(self, event: KeyEvent) -> bool:
        """
        Route a key event to layers, starting from the top.
        
        Args:
            event: KeyEvent to route
        
        Returns:
            True if any layer consumed the event, False otherwise
        """
        # Iterate from top to bottom
        for layer in reversed(self._layers):
            try:
                if layer.handle_key_event(event):
                    return True
            except Exception as e:
                if self._log_manager:
                    self._log_manager.add_message("ERROR", f"Layer {layer.__class__.__name__} raised exception during key event: {e}")
                # Continue to next layer despite error
        
        return False
    
    def handle_char_event(self, event: CharEvent) -> bool:
        """
        Route a character event to layers, starting from the top.
        
        Args:
            event: CharEvent to route
        
        Returns:
            True if any layer consumed the event, False otherwise
        """
        # Iterate from top to bottom
        for layer in reversed(self._layers):
            try:
                if layer.handle_char_event(event):
                    return True
            except Exception as e:
                if self._log_manager:
                    self._log_manager.add_message("ERROR", f"Layer {layer.__class__.__name__} raised exception during char event: {e}")
                # Continue to next layer despite error
        
        return False
    
    def render(self, renderer) -> None:
        """
        Render visible layers with intelligent dirty tracking.
        
        Only renders layers that have dirty content or are above a dirty layer.
        Layers below the topmost full-screen layer are skipped for performance.
        
        Args:
            renderer: TTK renderer instance for drawing
        """
        # Find topmost full-screen layer
        topmost_fullscreen_index = 0
        for i in range(len(self._layers) - 1, -1, -1):
            if self._layers[i].is_full_screen():
                topmost_fullscreen_index = i
                break
        
        # Find lowest dirty layer at or above the topmost full-screen layer
        lowest_dirty_index = None
        for i in range(topmost_fullscreen_index, len(self._layers)):
            if self._layers[i].needs_redraw():
                lowest_dirty_index = i
                break
        
        # If no dirty layers, nothing to render
        if lowest_dirty_index is None:
            return
        
        # Mark all layers above the lowest dirty layer as dirty
        # (they need to redraw because a lower layer changed)
        for i in range(lowest_dirty_index + 1, len(self._layers)):
            self._layers[i].mark_dirty()
        
        # Render from lowest dirty layer to top
        for i in range(lowest_dirty_index, len(self._layers)):
            layer = self._layers[i]
            if layer.needs_redraw():
                try:
                    layer.render(renderer)
                    layer.clear_dirty()
                except Exception as e:
                    if self._log_manager:
                        self._log_manager.add_message("ERROR", f"Layer {layer.__class__.__name__} raised exception during rendering: {e}")
                    # Continue rendering other layers despite error
        
        # Refresh screen after rendering
        renderer.refresh()
    
    def check_and_close_top_layer(self) -> bool:
        """
        Check if the top layer wants to close and pop it if so.
        
        Returns:
            True if a layer was closed, False otherwise
        """
        top_layer = self.get_top_layer()
        if top_layer.should_close():
            self.pop()
            return True
        return False
```

### Layer Implementations

#### FileManagerLayer

Wraps the existing FileManager main screen logic:

```python
class FileManagerLayer(UILayer):
    """
    Layer wrapper for the FileManager main screen.
    
    This is the permanent bottom layer that handles file browsing,
    selection, and main application commands.
    """
    
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self._close_requested = False
        self._dirty = True  # Start dirty to ensure initial render
    
    def handle_key_event(self, event: KeyEvent) -> bool:
        # Delegate to existing FileManager key handling logic
        # This will handle navigation, selection, commands, etc.
        result = self.file_manager._handle_main_screen_key_event(event)
        # Mark dirty if event was consumed (content likely changed)
        if result:
            self._dirty = True
        return result
    
    def handle_char_event(self, event: CharEvent) -> bool:
        # FileManager main screen doesn't handle char events
        # (no text input on main screen)
        return False
    
    def render(self, renderer) -> None:
        # Delegate to existing FileManager rendering logic
        self.file_manager._render_main_screen(renderer)
    
    def is_full_screen(self) -> bool:
        return True  # Main screen occupies full screen
    
    def needs_redraw(self) -> bool:
        return self._dirty or self.file_manager.needs_full_redraw
    
    def mark_dirty(self) -> None:
        self._dirty = True
    
    def clear_dirty(self) -> None:
        self._dirty = False
        self.file_manager.needs_full_redraw = False
    
    def should_close(self) -> bool:
        return self._close_requested
    
    def request_close(self):
        """Request that the application quit."""
        self._close_requested = True
    
    def on_activate(self) -> None:
        # Main screen is always active, no special activation needed
        pass
    
    def on_deactivate(self) -> None:
        # Main screen remains active even when covered by dialogs
        pass
```

#### Dialog Classes Implementing UILayer

Dialog classes (ListDialog, InfoDialog, SearchDialog, JumpDialog, DrivesDialog, BatchRenameDialog) will be modified to directly inherit from UILayer:

```python
class ListDialog(UILayer):
    """
    Searchable list dialog that implements UILayer interface.
    
    This dialog displays a list of items with search functionality
    and integrates directly with the layer stack system.
    """
    
    def __init__(self, config, renderer):
        self.config = config
        self.renderer = renderer
        self.is_active = False
        self._dirty = False
        # ... existing dialog state ...
    
    def handle_key_event(self, event: KeyEvent) -> bool:
        # Existing handle_input logic for KeyEvents
        # Returns True if event was consumed
        result = self._handle_key_input(event)
        # Mark dirty if event was consumed (content likely changed)
        if result:
            self._dirty = True
        return result
    
    def handle_char_event(self, event: CharEvent) -> bool:
        # Existing handle_input logic for CharEvents
        # Returns True if event was consumed (e.g., text input)
        result = self._handle_char_input(event)
        # Mark dirty if event was consumed (text changed)
        if result:
            self._dirty = True
        return result
    
    def render(self, renderer) -> None:
        # Existing draw() logic
        self.draw()
    
    def is_full_screen(self) -> bool:
        return False  # Dialogs are overlays, not full-screen
    
    def needs_redraw(self) -> bool:
        # Check if dialog content has changed
        return self._dirty or self._check_content_changed()
    
    def mark_dirty(self) -> None:
        self._dirty = True
    
    def clear_dirty(self) -> None:
        self._dirty = False
    
    def should_close(self) -> bool:
        # Check if dialog has been closed by user
        return not self.is_active
    
    def on_activate(self) -> None:
        # Called when dialog becomes top layer
        # Can be used for cursor management, etc.
        self._dirty = True  # Ensure dialog is drawn when activated
    
    def on_deactivate(self) -> None:
        # Called when dialog is covered by another layer
        pass
    
    # ... existing dialog methods ...
```

The same pattern applies to all dialog classes:
- **InfoDialog**: Information display dialog
- **SearchDialog**: File search dialog with text input
- **JumpDialog**: Quick directory navigation dialog
- **DrivesDialog**: Drive/mount point selection dialog
- **BatchRenameDialog**: Batch file renaming dialog

Each dialog will:
1. Inherit from UILayer
2. Implement all required UILayer methods
3. Maintain existing functionality through existing methods
4. Use `is_active` flag to signal when dialog should close
5. Track dirty state to optimize rendering

#### Viewer Classes Implementing UILayer

TextViewer and DiffViewer will be modified to directly inherit from UILayer:

```python
class TextViewer(UILayer):
    """
    Full-screen text file viewer that implements UILayer interface.
    
    This viewer displays text files with scrolling, search, and
    line number display, integrating directly with the layer stack.
    """
    
    def __init__(self, renderer, file_path):
        self.renderer = renderer
        self.file_path = file_path
        self.should_close = False
        self._dirty = True  # Start dirty to ensure initial render
        # ... existing viewer state ...
    
    def handle_key_event(self, event: KeyEvent) -> bool:
        # Existing handle_input logic for KeyEvents
        # Handles scrolling, search, quit, etc.
        # Returns True if event was consumed
        result = self._handle_key_input(event)
        # Mark dirty if event was consumed (view likely changed)
        if result:
            self._dirty = True
        return result
    
    def handle_char_event(self, event: CharEvent) -> bool:
        # Viewers typically don't handle char events
        # (no text input in viewer mode)
        return False
    
    def render(self, renderer) -> None:
        # Existing draw() logic
        self.draw()
    
    def is_full_screen(self) -> bool:
        return True  # Viewers occupy full screen
    
    def needs_redraw(self) -> bool:
        return self._dirty
    
    def mark_dirty(self) -> None:
        self._dirty = True
    
    def clear_dirty(self) -> None:
        self._dirty = False
    
    def should_close(self) -> bool:
        # Check if viewer wants to close (user pressed quit key)
        return self.should_close
    
    def on_activate(self) -> None:
        # Hide cursor when viewer becomes active
        self.renderer.set_cursor_visibility(False)
        self._dirty = True  # Ensure viewer is drawn when activated
    
    def on_deactivate(self) -> None:
        # Viewer is being covered or closed
        pass
    
    # ... existing viewer methods ...
```

```python
class DiffViewer(UILayer):
    """
    Full-screen diff viewer that implements UILayer interface.
    
    This viewer displays side-by-side or unified diffs between two files,
    integrating directly with the layer stack.
    """
    
    def __init__(self, renderer, file1_path, file2_path):
        self.renderer = renderer
        self.file1_path = file1_path
        self.file2_path = file2_path
        self.should_close = False
        self._dirty = True  # Start dirty to ensure initial render
        # ... existing viewer state ...
    
    def handle_key_event(self, event: KeyEvent) -> bool:
        # Existing handle_input logic for KeyEvents
        # Handles scrolling, mode switching, quit, etc.
        # Returns True if event was consumed
        result = self._handle_key_input(event)
        # Mark dirty if event was consumed (view likely changed)
        if result:
            self._dirty = True
        return result
    
    def handle_char_event(self, event: CharEvent) -> bool:
        # Viewers typically don't handle char events
        return False
    
    def render(self, renderer) -> None:
        # Existing draw() logic
        self.draw()
    
    def is_full_screen(self) -> bool:
        return True  # Viewers occupy full screen
    
    def needs_redraw(self) -> bool:
        return self._dirty
    
    def mark_dirty(self) -> None:
        self._dirty = True
    
    def clear_dirty(self) -> None:
        self._dirty = False
    
    def should_close(self) -> bool:
        # Check if viewer wants to close
        return self.should_close
    
    def on_activate(self) -> None:
        # Hide cursor when viewer becomes active
        self.renderer.set_cursor_visibility(False)
        self._dirty = True  # Ensure viewer is drawn when activated
    
    def on_deactivate(self) -> None:
        # Viewer is being covered or closed
        pass
    
    # ... existing viewer methods ...
```

### Migration Strategy

The migration from the current architecture to the layer-based system will be incremental:

1. **Phase 1**: Create UILayer interface and UILayerStack class
2. **Phase 2**: Modify dialog classes to inherit from UILayer
3. **Phase 3**: Modify viewer classes to inherit from UILayer
4. **Phase 4**: Create FileManagerLayer wrapper
5. **Phase 5**: Integrate UILayerStack into FileManager
6. **Phase 6**: Remove old if-elif chains from handle_input and rendering methods
7. **Phase 7**: Test and validate the new system

## Data Models

### Layer Stack State

The `UILayerStack` maintains the following state:

```python
class UILayerStack:
    _layers: List[UILayer]      # Stack of layers (index 0 = bottom)
    _log_manager: LogManager    # For error logging (optional)
```

### Layer State

Each layer implementation maintains its own state:

- **FileManagerLayer**: References the FileManager instance
- **DialogLayer**: References the dialog instance (ListDialog, InfoDialog, etc.)
- **ViewerLayer**: References the viewer instance (TextViewer, DiffViewer)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: LIFO Stack Ordering

*For any* sequence of push and pop operations on the UI layer stack, the layers should be removed in the reverse order they were added (Last In, First Out).

**Validates: Requirements 1.1, 1.3, 1.4**

### Property 2: Bottom Layer Persistence

*For any* sequence of operations on the UI layer stack, the bottom layer (FileManager main screen) should never be removed, and attempting to remove it should fail gracefully.

**Validates: Requirements 1.6, 9.4**

### Property 3: Top Layer Query Consistency

*For any* UI layer stack state, querying the top layer should return the most recently pushed layer that hasn't been popped.

**Validates: Requirements 1.5**

### Property 4: Event Routing to Top Layer

*For any* key event or character event, the UI layer stack should route it to the top layer first before considering lower layers.

**Validates: Requirements 2.1, 2.2**

### Property 5: Event Consumption Stops Propagation

*For any* event that is consumed by a layer, the UI layer stack should not propagate that event to any lower layers.

**Validates: Requirements 2.3**

### Property 6: Event Propagation Chain

*For any* event that is not consumed by the top layer, the UI layer stack should propagate it to the next layer below, continuing until a layer consumes it or the bottom layer is reached.

**Validates: Requirements 2.4, 2.5**

### Property 7: Bottom-to-Top Rendering Order

*For any* rendering operation, the UI layer stack should render layers in order from bottom to top, ensuring higher layers draw over lower layers.

**Validates: Requirements 3.1**

### Property 8: Rendering Context Provision

*For any* layer being rendered, the UI layer stack should provide it with the renderer instance needed to draw its content.

**Validates: Requirements 3.3**

### Property 9: State Change Triggers Redraw

*For any* layer state change that affects visual appearance, the UI layer stack should trigger a re-render of that layer.

**Validates: Requirements 3.4**

### Property 10: Full-Screen Layer Obscures Lower Layers

*For any* UI layer stack containing a full-screen layer, all layers below the topmost full-screen layer should be marked as obscured.

**Validates: Requirements 4.1**

### Property 11: Rendering Optimization for Full-Screen Layers

*For any* rendering operation when a full-screen layer is present, the UI layer stack should skip rendering all layers below the topmost full-screen layer.

**Validates: Requirements 4.2, 4.5**

### Property 12: Full-Screen Layer Removal Restores Rendering

*For any* UI layer stack where a full-screen layer is removed, the UI layer stack should resume rendering all previously obscured layers.

**Validates: Requirements 4.3**

### Property 13: Activation Lifecycle Callback

*For any* layer that becomes the top layer (either by being pushed or by the layer above being popped), the UI layer stack should call its on_activate() method.

**Validates: Requirements 8.1**

### Property 14: Deactivation Lifecycle Callback

*For any* layer that stops being the top layer (either by another layer being pushed or by being popped), the UI layer stack should call its on_deactivate() method.

**Validates: Requirements 8.2**

### Property 15: State Preservation During Push

*For any* layer that is covered by a new layer being pushed onto the stack, the covered layer's state should remain unchanged.

**Validates: Requirements 8.4**

### Property 16: State Restoration During Pop

*For any* layer that becomes the top layer after the layer above it is popped, the layer's state should be the same as when it was last the top layer.

**Validates: Requirements 8.5**

### Property 17: Exception Handling During Event Processing

*For any* layer that raises an exception during event handling, the UI layer stack should catch the exception, log an error, and continue processing with the next layer.

**Validates: Requirements 9.1**

### Property 18: Exception Handling During Rendering

*For any* layer that raises an exception during rendering, the UI layer stack should catch the exception, log an error, and continue rendering other layers.

**Validates: Requirements 9.2**

### Property 19: Stack Never Empty

*For any* sequence of operations on the UI layer stack, the stack should always contain at least one layer (the bottom layer).

**Validates: Requirements 9.3**

## Error Handling

### Exception Handling Strategy

The `UILayerStack` implements defensive error handling:

1. **Event Handling Errors**: If a layer raises an exception during `handle_key_event()` or `handle_char_event()`, the stack catches it, logs an error message, and continues propagating the event to the next layer.

2. **Rendering Errors**: If a layer raises an exception during `render()`, the stack catches it, logs an error message, and continues rendering other layers.

3. **Invalid Operations**: Attempting to pop the bottom layer is rejected with a warning message, and the operation returns None.

### Error Logging

All errors are logged through the `LogManager` if available:
- Event handling exceptions: `"ERROR: Layer {name} raised exception during key/char event: {error}"`
- Rendering exceptions: `"ERROR: Layer {name} raised exception during rendering: {error}"`
- Invalid operations: `"WARNING: Cannot remove bottom layer from UI stack"`

## Testing Strategy

### Unit Testing

Unit tests will verify specific behaviors and edge cases:

1. **Stack Operations**:
   - Test pushing and popping layers
   - Test that bottom layer cannot be removed
   - Test querying top layer

2. **Event Routing**:
   - Test events go to top layer first
   - Test event propagation when not consumed
   - Test event consumption stops propagation

3. **Rendering**:
   - Test rendering order (bottom to top)
   - Test full-screen layer optimization
   - Test rendering context is provided

4. **Lifecycle**:
   - Test activation callbacks are called
   - Test deactivation callbacks are called
   - Test state preservation

5. **Error Handling**:
   - Test exception handling during events
   - Test exception handling during rendering
   - Test invalid operations are rejected

### Property-Based Testing

Property-based tests will verify universal properties across many generated inputs. Each test will run a minimum of 100 iterations to ensure comprehensive coverage.

1. **Property 1: LIFO Stack Ordering**
   - Generate random sequences of push/pop operations
   - Verify layers are removed in reverse order of addition
   - **Feature: ui-layer-stack, Property 1: LIFO Stack Ordering**

2. **Property 2: Bottom Layer Persistence**
   - Generate random sequences of operations
   - Verify bottom layer is never removed
   - **Feature: ui-layer-stack, Property 2: Bottom Layer Persistence**

3. **Property 3: Top Layer Query Consistency**
   - Generate random stack states
   - Verify top layer query returns correct layer
   - **Feature: ui-layer-stack, Property 3: Top Layer Query Consistency**

4. **Property 4: Event Routing to Top Layer**
   - Generate random events and stack states
   - Verify events go to top layer first
   - **Feature: ui-layer-stack, Property 4: Event Routing to Top Layer**

5. **Property 5: Event Consumption Stops Propagation**
   - Generate random events with consuming layers
   - Verify lower layers don't receive consumed events
   - **Feature: ui-layer-stack, Property 5: Event Consumption Stops Propagation**

6. **Property 6: Event Propagation Chain**
   - Generate random events with non-consuming layers
   - Verify events propagate to lower layers
   - **Feature: ui-layer-stack, Property 6: Event Propagation Chain**

7. **Property 7: Bottom-to-Top Rendering Order**
   - Generate random stack states
   - Track rendering order
   - Verify layers render bottom to top
   - **Feature: ui-layer-stack, Property 7: Bottom-to-Top Rendering Order**

8. **Property 8: Rendering Context Provision**
   - Generate random stack states
   - Verify all layers receive renderer
   - **Feature: ui-layer-stack, Property 8: Rendering Context Provision**

9. **Property 10: Full-Screen Layer Obscures Lower Layers**
   - Generate stacks with full-screen layers
   - Verify lower layers are marked obscured
   - **Feature: ui-layer-stack, Property 10: Full-Screen Layer Obscures Lower Layers**

10. **Property 11: Rendering Optimization for Full-Screen Layers**
    - Generate stacks with full-screen layers
    - Track which layers are rendered
    - Verify obscured layers are skipped
    - **Feature: ui-layer-stack, Property 11: Rendering Optimization for Full-Screen Layers**

11. **Property 12: Full-Screen Layer Removal Restores Rendering**
    - Generate stacks with full-screen layers
    - Remove full-screen layer
    - Verify previously obscured layers are rendered
    - **Feature: ui-layer-stack, Property 12: Full-Screen Layer Removal Restores Rendering**

12. **Property 13: Activation Lifecycle Callback**
    - Generate random push operations
    - Verify on_activate() is called
    - **Feature: ui-layer-stack, Property 13: Activation Lifecycle Callback**

13. **Property 14: Deactivation Lifecycle Callback**
    - Generate random push/pop operations
    - Verify on_deactivate() is called
    - **Feature: ui-layer-stack, Property 14: Deactivation Lifecycle Callback**

14. **Property 15: State Preservation During Push**
    - Generate random stack states
    - Push new layer
    - Verify lower layer state unchanged
    - **Feature: ui-layer-stack, Property 15: State Preservation During Push**

15. **Property 16: State Restoration During Pop**
    - Generate random stack states
    - Pop top layer
    - Verify new top layer state is preserved
    - **Feature: ui-layer-stack, Property 16: State Restoration During Pop**

16. **Property 17: Exception Handling During Event Processing**
    - Generate events with exception-throwing layers
    - Verify exceptions are caught and logged
    - Verify event processing continues
    - **Feature: ui-layer-stack, Property 17: Exception Handling During Event Processing**

17. **Property 18: Exception Handling During Rendering**
    - Generate rendering with exception-throwing layers
    - Verify exceptions are caught and logged
    - Verify rendering continues
    - **Feature: ui-layer-stack, Property 18: Exception Handling During Rendering**

18. **Property 19: Stack Never Empty**
    - Generate random sequences of operations
    - Verify stack always has at least one layer
    - **Feature: ui-layer-stack, Property 19: Stack Never Empty**

### Integration Testing

Integration tests will verify the system works correctly with real TFM components:

1. **FileManager Integration**: Test that FileManagerLayer correctly wraps FileManager functionality
2. **Dialog Integration**: Test that DialogLayer correctly wraps dialog components
3. **Viewer Integration**: Test that ViewerLayer correctly wraps viewer components
4. **End-to-End Workflows**: Test complete user workflows (open dialog, navigate, close, etc.)

### Testing Framework

We will use Python's `hypothesis` library for property-based testing, which provides:
- Automatic generation of test inputs
- Shrinking of failing examples to minimal cases
- Configurable number of test iterations (we'll use 100 minimum)
- Integration with pytest for easy test execution

Example property test structure:

```python
from hypothesis import given, strategies as st
import pytest

@given(st.lists(st.text(), min_size=1))
def test_lifo_ordering(layer_names):
    """
    Feature: ui-layer-stack, Property 1: LIFO Stack Ordering
    
    For any sequence of push and pop operations, layers should be
    removed in reverse order of addition.
    """
    # Test implementation here
    pass
```
