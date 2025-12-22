# Event Flow Analysis - TFMEventCallback Routing

## Summary

**The event routing follows proper layer architecture.**

TFMEventCallback routes all events directly to the UI layer stack. FileManager-specific features (isearch, quick_edit_bar, quick_choice_bar) are handled by FileManagerLayer, maintaining clean layer separation.

## Event Flow

### Key/Char Events (Correct Layer Architecture)
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
    ├─ FileManager.handle_input() → Check FileManager-specific features
    │   ├─ isearch_mode → return True if handled
    │   ├─ quick_edit_bar → return True if handled
    │   ├─ quick_choice_bar → return True if handled
    │   └─ return False (not handled)
    │
    └─ FileManager.handle_main_screen_key_event() → if not handled
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
        # Check FileManager-specific input modes first
        result = self.file_manager.handle_input(event)
        if result:
            self._dirty = True
            return True
        
        # Delegate to main screen key handling
        result = self.file_manager.handle_main_screen_key_event(event)
        if result:
            self._dirty = True
        
        return result
```

**Key Points**:
- Handles FileManager-specific features (via handle_input())
- Delegates to main screen logic if not handled
- Manages dirty state
- Proper layer abstraction

### 3. FileManager.handle_input(): Feature Handler
**Responsibility**: Handle FileManager-specific input features only

```python
class FileManager:
    def handle_input(self, event):
        # Handle FileManager-specific features
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
        
        # Not handled by FileManager-specific features
        return False
```

**Key Points**:
- Only handles FileManager-specific features
- Returns True if handled, False if not
- Called by FileManagerLayer, not TFMEventCallback

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
FileManager (Business Logic)
```

### 2. FileManager-Specific Features in the Right Place

The isearch, quick_edit_bar, and quick_choice_bar are:
- Part of the FileManager main screen (not separate layers)
- Handled by FileManagerLayer (the layer that represents the main screen)
- Not visible to TFMEventCallback (proper encapsulation)

### 3. Consistent with Other Layers

Just like Dialog and Viewer layers handle their own input:
- SearchDialog handles search input
- TextViewer handles viewer navigation
- FileManagerLayer handles main screen input (including special modes)

### 4. Clean Separation of Concerns

**TFMEventCallback**: Routes events (no knowledge of layers or features)
**UILayerStack**: Manages layers (no knowledge of features)
**FileManagerLayer**: Handles main screen (knows about FileManager features)
**FileManager**: Business logic (knows about its own features)

## Key Improvements

### Before (Incorrect - Bypassing Layer Stack)
```python
class TFMEventCallback(EventCallback):
    def on_key_event(self, event: KeyEvent) -> bool:
        # Bypassing layer stack!
        if self.file_manager.handle_input(event):
            return True
        
        # Then routing to layer stack
        return self.file_manager.ui_layer_stack.handle_key_event(event)
```

**Problems**:
- TFMEventCallback knows about FileManager features
- Bypasses layer architecture
- Inconsistent with how other layers work

### After (Correct - Through Layer Stack)
```python
class TFMEventCallback(EventCallback):
    def on_key_event(self, event: KeyEvent) -> bool:
        # Always route through layer stack
        consumed = self.file_manager.ui_layer_stack.handle_key_event(event)
        if consumed:
            self.file_manager.needs_full_redraw = True
        return consumed

class FileManagerLayer(UILayer):
    def handle_key_event(self, event) -> bool:
        # FileManagerLayer handles FileManager features
        result = self.file_manager.handle_input(event)
        if result:
            self._dirty = True
            return True
        
        # Then delegates to main screen logic
        result = self.file_manager.handle_main_screen_key_event(event)
        if result:
            self._dirty = True
        return result
```

**Benefits**:
- TFMEventCallback is simple and clean
- Proper layer architecture maintained
- FileManager features handled by FileManagerLayer
- Consistent with other layers

## Benefits

1. **Proper Layer Architecture**: All events go through the layer stack
2. **Clean Separation**: TFMEventCallback doesn't know about FileManager features
3. **Consistent Pattern**: FileManagerLayer works like other layers
4. **Better Encapsulation**: FileManager features hidden from TFMEventCallback
5. **Easier to Understand**: Clear, consistent event flow

## Conclusion

The corrected design properly maintains layer architecture:
- **TFMEventCallback**: Simple event router (TTK → UILayerStack)
- **UILayerStack**: Layer manager (routes to top layer)
- **FileManagerLayer**: Layer adapter (handles FileManager features + main screen)
- **FileManager**: Business logic (implements features)

This creates a clean, maintainable architecture where events always flow through the layer stack, and each layer handles its own concerns.
