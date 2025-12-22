# Event Flow Analysis - TFMEventCallback Routing

## Summary

**The event routing follows proper layer architecture with a unified input handler.**

TFMEventCallback routes all events directly to the UI layer stack. FileManagerLayer delegates to FileManager.handle_input(), which is a unified handler for all FileManager input (special modes + main screen events).

## Event Flow

### Key/Char Events (Clean Layer Architecture)
```
TTK Backend
    ↓
TFMEventCallback.on_key_event()
    ↓
ui_layer_stack.handle_key_event()
    ↓
Top Layer (Dialog/Viewer/FileManagerLayer)
    ↓
FileManagerLayer.handle_key_event()
    ↓
FileManager.handle_input() [Unified Handler]
    ├─ Check isearch_mode → return True if handled
    ├─ Check quick_edit_bar → return True if handled
    ├─ Check quick_choice_bar → return True if handled
    └─ Handle main screen key events → return True/False
```

### System Events (Broadcast to All Layers)
```
TTK Backend
    ↓
TFMEventCallback.on_system_event()
    ↓
ui_layer_stack.handle_system_event()
    ↓
All Layers (broadcast)
```

## Design Principles

### 1. TFMEventCallback: Simple Event Router
**Responsibility**: Route events from TTK backend to UI layer stack

```python
class TFMEventCallback(EventCallback):
    def on_key_event(self, event: KeyEvent) -> bool:
        self.file_manager.adaptive_fps.mark_activity()
        
        # Route directly to UI layer stack
        consumed = self.file_manager.ui_layer_stack.handle_key_event(event)
        if consumed:
            self.file_manager.needs_full_redraw = True
        return consumed
```

**Key Points**:
- Simple, clean routing
- No knowledge of FileManager-specific features
- No knowledge of layer internals
- Just routes to layer stack

### 2. FileManagerLayer: Layer Adapter
**Responsibility**: Adapt FileManager to UILayer interface

```python
class FileManagerLayer(UILayer):
    def handle_key_event(self, event) -> bool:
        # Delegate to FileManager's unified input handler
        result = self.file_manager.handle_input(event)
        if result:
            self._dirty = True
        return result
```

**Key Points**:
- Simple delegation to FileManager
- Manages dirty state
- Proper layer abstraction
- No knowledge of FileManager internals

### 3. FileManager.handle_input(): Unified Input Handler
**Responsibility**: Handle all FileManager input (special modes + main screen)

```python
class FileManager:
    def handle_input(self, event):
        # Handle FileManager-specific input modes first
        if self.isearch_mode:
            result = self.handle_isearch_input(event)
            if result:
                self.file_manager_layer.mark_dirty()
                self.needs_full_redraw = True
            return result
        
        if self.quick_edit_bar.is_active:
            result = self.quick_edit_bar.handle_input(event)
            if result:
                self.file_manager_layer.mark_dirty()
                self.needs_full_redraw = True
            return result
        
        if isinstance(event, KeyEvent) and self.quick_choice_bar.is_active:
            result = self.handle_quick_choice_input(event)
            if result:
                self.file_manager_layer.mark_dirty()
                self.needs_full_redraw = True
            return result
        
        # Handle main screen key events
        if not isinstance(event, KeyEvent):
            return False
        
        return self.handle_main_screen_key_event(event)
```

**Key Points**:
- Unified handler for all FileManager input
- Checks special modes first
- Falls through to main screen handling
- Single entry point for all FileManager input

### 4. UILayerStack: Layer Manager
**Responsibility**: Route events to appropriate layer

- Routes key/char events to top layer only
- Broadcasts system events to all layers
- No knowledge of FileManager-specific features
- Pure layer management

## Why This Design is Correct

### 1. Proper Layer Architecture

Events flow through the layer stack, and each layer handles its own concerns:

```
TFMEventCallback (Event Router)
    ↓
UILayerStack (Layer Manager)
    ↓
FileManagerLayer (Layer Adapter)
    ↓
FileManager.handle_input() (Unified Input Handler)
```

### 2. Single Entry Point

FileManager has one unified input handler:
- No confusion about which method to call
- Special modes checked first, then main screen
- Clear, linear flow through the handler

### 3. Consistent with Other Layers

Just like Dialog and Viewer layers handle their own input:
- SearchDialog handles search input
- TextViewer handles viewer navigation
- FileManagerLayer handles main screen input (via unified handler)

### 4. Clean Separation of Concerns

**TFMEventCallback**: Routes events (no knowledge of layers or features)
**UILayerStack**: Manages layers (no knowledge of features)
**FileManagerLayer**: Adapts to UILayer interface (simple delegation)
**FileManager.handle_input()**: Handles all input (special modes + main screen)

## Key Improvements

### Before (Two Separate Methods)
```python
class FileManager:
    def handle_input(self, event):
        # Only handled special modes
        if self.isearch_mode:
            return self.handle_isearch_input(event)
        # ...
        return False  # Not handled
    
    def handle_main_screen_key_event(self, event):
        # Handled main screen events
        # ...

class FileManagerLayer(UILayer):
    def handle_key_event(self, event) -> bool:
        # Had to call both methods
        if self.file_manager.handle_input(event):
            return True
        return self.file_manager.handle_main_screen_key_event(event)
```

**Problems**:
- Two separate methods for FileManager input
- FileManagerLayer had to know about both
- Confusing which method does what

### After (Unified Handler)
```python
class FileManager:
    def handle_input(self, event):
        # Unified handler for all input
        # Check special modes first
        if self.isearch_mode:
            return self.handle_isearch_input(event)
        # ...
        
        # Then handle main screen
        if not isinstance(event, KeyEvent):
            return False
        return self.handle_main_screen_key_event(event)

class FileManagerLayer(UILayer):
    def handle_key_event(self, event) -> bool:
        # Simple delegation to unified handler
        result = self.file_manager.handle_input(event)
        if result:
            self._dirty = True
        return result
```

**Benefits**:
- Single entry point for all FileManager input
- FileManagerLayer is simple and clean
- Clear flow: special modes → main screen
- Easy to understand and maintain

## Benefits

1. **Proper Layer Architecture**: All events go through the layer stack
2. **Clean Separation**: TFMEventCallback doesn't know about FileManager features
3. **Unified Handler**: Single entry point for all FileManager input
4. **Simple Delegation**: FileManagerLayer just delegates to handle_input()
5. **Easier to Maintain**: Clear, linear flow through the input handler

## Conclusion

The design properly maintains layer architecture with a unified input handler:
- **TFMEventCallback**: Simple event router (TTK → UILayerStack)
- **UILayerStack**: Layer manager (routes to top layer)
- **FileManagerLayer**: Layer adapter (simple delegation)
- **FileManager.handle_input()**: Unified input handler (special modes + main screen)

This creates a clean, maintainable architecture where events always flow through the layer stack, and FileManager has a single, unified entry point for all input handling.
