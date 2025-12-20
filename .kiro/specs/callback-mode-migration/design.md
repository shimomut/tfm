# Design Document: Callback Mode Migration

## Overview

This design describes the migration of TTK from dual-mode (polling + callback) to callback-only event delivery. The migration removes approximately 450 lines of code, simplifies the architecture, and aligns with IME requirements that mandate callback mode.

The migration affects three main areas:
1. **TTK Core** - Renderer interface and CoreGraphics backend
2. **TFM Application** - Main application event handling
3. **Supporting Code** - Tests, demos, and documentation

## Architecture

### Current Architecture (Dual Mode)

```
┌─────────────────┐
│   Application   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    v         v
┌───────┐  ┌──────────┐
│Polling│  │ Callback │
│ Mode  │  │   Mode   │
└───┬───┘  └────┬─────┘
    │           │
    v           v
┌───────────────────┐
│  Event Queue      │
│  (CoreGraphics)   │
└─────────┬─────────┘
          │
          v
┌─────────────────┐
│   OS Events     │
└─────────────────┘
```

**Problems:**
- Dual code paths increase complexity
- Event queue management overhead
- Conditional logic throughout
- IME incompatible with polling mode
- Dead code (TFM only uses callback mode)

### Target Architecture (Callback Only)

```
┌─────────────────┐
│   Application   │
│  (implements    │
│ EventCallback)  │
└────────┬────────┘
         │
         │ set_event_callback()
         v
┌─────────────────┐
│   Renderer      │
│ (CoreGraphics)  │
└────────┬────────┘
         │
         │ run_event_loop_iteration()
         v
┌─────────────────┐
│   OS Events     │
│  (NSEvent)      │
└────────┬────────┘
         │
         │ Callbacks
         v
┌─────────────────┐
│ EventCallback   │
│  - on_key_event │
│  - on_char_event│
│  - on_resize    │
└─────────────────┘
```

**Benefits:**
- Single event delivery path
- No event queue overhead
- No conditional logic
- IME fully supported
- Simpler to understand and maintain

## Components and Interfaces

### 1. Renderer Interface (ttk/renderer.py)

**Current Interface:**
```python
class Renderer(ABC):
    def set_event_callback(self, callback: Optional[EventCallback]) -> None:
        """Optional callback for event delivery."""
        pass
    
    def get_event(self, timeout_ms: int = -1) -> Optional[Event]:
        """Get next event (polling mode)."""
        pass
    
    def get_input(self, timeout_ms: int = -1) -> Optional[Event]:
        """Backward compatibility alias."""
        pass
```

**New Interface:**
```python
class Renderer(ABC):
    @abstractmethod
    def set_event_callback(self, callback: EventCallback) -> None:
        """
        Set the event callback for event delivery (REQUIRED).
        
        Must be called before run_event_loop() or run_event_loop_iteration().
        All events are delivered via callback methods.
        
        Args:
            callback: EventCallback instance (required, not optional)
        
        Raises:
            ValueError: If callback is None
        """
        pass
    
    @abstractmethod
    def run_event_loop(self) -> None:
        """
        Run the main event loop until application quits.
        
        Blocks until the application terminates. Events are delivered
        via the EventCallback set with set_event_callback().
        
        Raises:
            RuntimeError: If event callback not set
        """
        pass
    
    @abstractmethod
    def run_event_loop_iteration(self, timeout_ms: int = -1) -> None:
        """
        Process one iteration of the event loop.
        
        Processes pending OS events and delivers them via callbacks.
        Returns after processing events or timeout.
        
        Args:
            timeout_ms: Maximum time to wait for events (-1 = indefinite)
        
        Raises:
            RuntimeError: If event callback not set
        """
        pass
```

**Changes:**
- Remove `get_event()` method
- Remove `get_input()` method
- Make `callback` parameter non-optional
- Add validation and error handling
- Update docstrings to reflect callback-only design

### 2. CoreGraphics Backend (ttk/backends/coregraphics_backend.py)

**Current Implementation:**
```python
class CoreGraphicsBackend(Renderer):
    def __init__(self):
        self.event_callback = None  # Optional
        self.event_queue = []       # For polling mode
    
    def get_event(self, timeout_ms=-1):
        """Dual-mode implementation."""
        if self.event_callback:
            # Callback mode - process events
            self._process_events(timeout_ms)
            return None
        else:
            # Polling mode - return from queue
            self._process_events(timeout_ms)
            return self.event_queue.pop(0) if self.event_queue else None
    
    def keyDown_(self, event):
        """Handle key event - dual mode."""
        key_event = self._translate_event(event)
        
        if self.event_callback:
            # Callback mode
            consumed = self.event_callback.on_key_event(key_event)
            if consumed:
                return
        else:
            # Polling mode
            self.event_queue.append(key_event)
            return  # Can't call interpretKeyEvents_() - breaks IME!
        
        self.interpretKeyEvents_([event])
```

**New Implementation:**
```python
class CoreGraphicsBackend(Renderer):
    def __init__(self):
        self.event_callback = None  # Set via set_event_callback()
    
    def set_event_callback(self, callback):
        """Set event callback (required)."""
        if callback is None:
            raise ValueError("Event callback cannot be None")
        self.event_callback = callback
    
    def run_event_loop_iteration(self, timeout_ms=-1):
        """Process one iteration of events."""
        if self.event_callback is None:
            raise RuntimeError("Event callback not set")
        
        # Process OS events (NSApp processEvents)
        # Events delivered via keyDown_(), etc.
        self._process_os_events(timeout_ms)
    
    def keyDown_(self, event):
        """Handle key event - callback only."""
        # Check if IME composition is active
        if self.hasMarkedText():
            self.interpretKeyEvents_([event])
            return
        
        # Translate to KeyEvent
        key_event = self._translate_event(event)
        
        # Deliver to application (callback always set)
        consumed = self.event_callback.on_key_event(key_event)
        
        if consumed:
            return
        
        # Not consumed - invoke IME
        self.interpretKeyEvents_([event])
```

**Changes:**
- Remove `get_event()` method
- Remove `_process_events()` method
- Remove `event_queue` instance variable
- Remove conditional `if self.event_callback:` checks
- Simplify `keyDown_()` to always use callback
- Add validation in `set_event_callback()`
- Add validation in `run_event_loop_iteration()`

### 3. TFM Application (src/tfm_main.py)

**Current Implementation:**
```python
class TFM:
    def __init__(self, renderer):
        self.renderer = renderer
        self.callback_mode_enabled = False
        self.event_callback = None
    
    def enable_callback_mode(self):
        """Enable callback mode."""
        self.callback_mode_enabled = True
        self.event_callback = TFMEventCallback(self)
        self.renderer.set_event_callback(self.event_callback)
    
    def run_with_callbacks(self):
        """Run in callback mode."""
        self.enable_callback_mode()
        while not self.should_quit:
            self.renderer.get_event(timeout_ms=16)  # Unnecessary!
            self.draw_interface()
```

**New Implementation:**
```python
class TFM:
    def __init__(self, renderer):
        self.renderer = renderer
        
        # Set up event callback (always required)
        self.event_callback = TFMEventCallback(self)
        self.renderer.set_event_callback(self.event_callback)
    
    def run(self):
        """Main application loop."""
        # Draw initial interface
        self.draw_interface()
        
        # Run event loop
        while not self.should_quit:
            # Process events (delivered via callbacks)
            self.renderer.run_event_loop_iteration(timeout_ms=16)
            
            # Draw interface after event processing
            self.draw_interface()
```

**Changes:**
- Remove `enable_callback_mode()` method
- Remove `disable_callback_mode()` method
- Remove `callback_mode_enabled` instance variable
- Remove `run_with_callbacks()` method
- Set event callback in `__init__`
- Simplify main loop
- Remove unnecessary `get_event()` call

### 4. Test Utilities

**New Test Helper:**
```python
# ttk/test/test_utils.py

class EventCapture(EventCallback):
    """Helper for capturing events in tests."""
    
    def __init__(self):
        self.events = []
        self.should_quit = False
    
    def on_key_event(self, event):
        self.events.append(('key', event))
        return False
    
    def on_char_event(self, event):
        self.events.append(('char', event))
        return False
    
    def on_resize(self, width, height):
        self.events.append(('resize', width, height))
    
    def should_close(self):
        return self.should_quit
    
    def get_next_event(self, backend, timeout_ms=100):
        """Get next event synchronously (for tests)."""
        self.events.clear()
        backend.run_event_loop_iteration(timeout_ms)
        return self.events[0] if self.events else None
    
    def wait_for_event(self, backend, event_type, timeout_ms=1000):
        """Wait for specific event type."""
        start = time.time()
        while time.time() - start < timeout_ms / 1000:
            backend.run_event_loop_iteration(10)
            for evt in self.events:
                if evt[0] == event_type:
                    return evt
        return None
```

**Usage in Tests:**
```python
def test_key_event():
    backend = CoreGraphicsBackend()
    capture = EventCapture()
    backend.set_event_callback(capture)
    
    # Simulate key press
    simulate_key_press(backend, 'a')
    
    # Get event
    event = capture.get_next_event(backend)
    assert event[0] == 'key'
    assert event[1].char == 'a'
```

## Data Models

### EventCallback Interface

```python
class EventCallback(ABC):
    """Interface for receiving events from the renderer."""
    
    @abstractmethod
    def on_key_event(self, event: KeyEvent) -> bool:
        """
        Handle key event.
        
        Args:
            event: Key event to handle
        
        Returns:
            True if event was consumed, False to pass to IME
        """
        pass
    
    @abstractmethod
    def on_char_event(self, event: CharEvent) -> bool:
        """
        Handle character event (from IME or direct input).
        
        Args:
            event: Character event to handle
        
        Returns:
            True if event was consumed
        """
        pass
    
    @abstractmethod
    def on_resize(self, width: int, height: int) -> None:
        """Handle window resize."""
        pass
    
    @abstractmethod
    def should_close(self) -> bool:
        """Check if application should quit."""
        pass
```

### Event Types

```python
@dataclass
class KeyEvent:
    """Key event from keyboard."""
    key: str           # Key name (e.g., 'a', 'Enter', 'F1')
    char: str          # Character representation
    modifiers: int     # Modifier flags (Shift, Ctrl, Alt, Cmd)
    is_repeat: bool    # True if key repeat

@dataclass
class CharEvent:
    """Character event from IME or direct input."""
    char: str          # Character(s) to insert
    source: str        # 'ime' or 'direct'
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Event callback required before event loop

*For any* Renderer instance, calling `run_event_loop()` or `run_event_loop_iteration()` without first calling `set_event_callback()` should raise a RuntimeError.

**Validates: Requirements 2.1, 2.2**

### Property 2: All events delivered via callbacks

*For any* event that occurs during event loop execution (key events, character events, resize events), the event should be delivered via the corresponding EventCallback method and not returned directly from event loop methods.

**Validates: Requirements 2.3, 2.5, 3.3, 3.5, 4.1, 4.3**

### Property 3: IME unconsumed events passed to interpretKeyEvents

*For any* key event that is not consumed by the application (on_key_event returns False), the CoreGraphics backend should call `interpretKeyEvents_()` to allow IME processing.

**Validates: Requirements 9.2**

### Property 4: IME composed text delivered via callback

*For any* IME composition that produces text, the resulting characters should be delivered via `on_char_event()` callback.

**Validates: Requirements 9.3**

### Property 5: IME composition handled correctly

*For any* IME composition sequence (marked text set, composition, finalization), the system should handle it correctly without interfering with the composition process.

**Validates: Requirements 9.1**

## Error Handling

### Validation Errors

**Missing Event Callback:**
- **When**: `run_event_loop()` or `run_event_loop_iteration()` called without callback
- **Error**: `RuntimeError("Event callback not set. Call set_event_callback() first.")`
- **Recovery**: Application must set callback before retrying

**None Event Callback:**
- **When**: `set_event_callback(None)` called
- **Error**: `ValueError("Event callback cannot be None")`
- **Recovery**: Application must provide valid EventCallback instance

### IME Errors

**IME State Errors:**
- **When**: IME methods called in invalid state
- **Handling**: Log warning, continue gracefully
- **Recovery**: IME state automatically resets on next key event

**IME Positioning Errors:**
- **When**: Cannot calculate IME candidate window position
- **Handling**: Use default position (bottom-left of window)
- **Recovery**: Position recalculated on next composition

### Event Processing Errors

**Event Translation Errors:**
- **When**: Cannot translate OS event to TTK event
- **Handling**: Log warning, skip event
- **Recovery**: Continue processing next event

**Callback Errors:**
- **When**: EventCallback method raises exception
- **Handling**: Log error with traceback, continue event loop
- **Recovery**: Application responsible for handling errors in callbacks

## Testing Strategy

### Dual Testing Approach

This migration requires both unit tests and property-based tests:

**Unit Tests:**
- Verify specific API changes (methods removed, methods added)
- Test error conditions (missing callback, None callback)
- Test specific IME scenarios (composition, finalization)
- Integration tests for TFM functionality

**Property-Based Tests:**
- Verify event delivery across many event types
- Test IME handling across various composition sequences
- Verify callback requirement across different execution paths

### Property-Based Testing Configuration

We will use Python's `hypothesis` library for property-based testing:

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1))
def test_property_2_event_delivery(event_char):
    """
    Feature: callback-mode-migration, Property 2: All events delivered via callbacks
    
    For any event that occurs, it should be delivered via callback.
    """
    backend = CoreGraphicsBackend()
    capture = EventCapture()
    backend.set_event_callback(capture)
    
    # Simulate event
    simulate_char_event(backend, event_char)
    
    # Verify delivered via callback
    assert len(capture.events) > 0
    assert capture.events[0][0] == 'char'
    assert capture.events[0][1].char == event_char
```

Each property test should:
- Run minimum 100 iterations
- Reference the design property in a comment
- Use format: `Feature: callback-mode-migration, Property N: <property text>`

### Unit Test Coverage

**Core API Tests:**
- Test `set_event_callback()` with valid callback
- Test `set_event_callback()` with None (should raise ValueError)
- Test `run_event_loop_iteration()` without callback (should raise RuntimeError)
- Test that `get_event()` method doesn't exist
- Test that `get_input()` method doesn't exist

**Event Delivery Tests:**
- Test key event delivery via callback
- Test character event delivery via callback
- Test resize event delivery via callback
- Test event consumption (return True/False)

**IME Tests:**
- Test IME composition with marked text
- Test IME finalization
- Test unconsumed events passed to IME
- Test IME character delivery

**TFM Integration Tests:**
- Test TFM initialization sets callback
- Test TFM main loop processes events
- Test TFM key bindings work
- Test TFM dialogs work

**Test Migration Tests:**
- Test EventCapture helper class
- Test get_next_event() helper
- Test wait_for_event() helper

### Manual Testing

**IME Testing:**
- Japanese input (Hiragana, Katakana, Kanji)
- Chinese input (Simplified, Traditional)
- Korean input (Hangul)
- Verify candidate window positioning
- Verify composition display

**TFM Regression Testing:**
- All key bindings
- All dialogs
- All file operations
- All menu items
- Search functionality
- Archive browsing
- S3 operations

### Test Execution

```bash
# Run all tests
python -m pytest test/ ttk/test/

# Run property-based tests with verbose output
python -m pytest test/ -v -k "property"

# Run IME tests
python -m pytest test/ -v -k "ime"

# Run integration tests
python -m pytest test/ -v -k "integration"
```

## Migration Implementation Plan

### Phase 1: Core API Changes

1. Update `ttk/renderer.py`:
   - Remove `get_event()` method
   - Remove `get_input()` method
   - Make `callback` parameter non-optional in `set_event_callback()`
   - Add validation to `set_event_callback()`
   - Add validation to `run_event_loop_iteration()`
   - Update docstrings

2. Update `ttk/backends/coregraphics_backend.py`:
   - Remove `get_event()` method
   - Remove `_process_events()` method
   - Remove `event_queue` instance variable
   - Remove conditional checks for `event_callback`
   - Simplify `keyDown_()` method
   - Add validation to `set_event_callback()`
   - Add validation to `run_event_loop_iteration()`

### Phase 2: Application Updates

3. Update `src/tfm_main.py`:
   - Remove `enable_callback_mode()` method
   - Remove `disable_callback_mode()` method
   - Remove `callback_mode_enabled` variable
   - Set callback in `__init__`
   - Simplify main loop
   - Remove unnecessary `get_event()` call

### Phase 3: Test Infrastructure

4. Create `ttk/test/test_utils.py`:
   - Implement `EventCapture` helper class
   - Implement `get_next_event()` helper
   - Implement `wait_for_event()` helper

5. Update test files (28 files):
   - Convert to use EventCapture
   - Remove `get_event()` and `get_input()` calls
   - Update to callback mode patterns

### Phase 4: Demo Updates

6. Update demo scripts (10 files):
   - Convert to callback mode
   - Remove `get_event()` and `get_input()` calls
   - Add EventCallback implementations

### Phase 5: Documentation

7. Update documentation:
   - Remove polling mode examples
   - Add callback mode examples
   - Update architecture docs
   - Create migration guide (if needed)

### Phase 6: Testing and Validation

8. Run test suite
9. Manual IME testing
10. TFM regression testing
11. Performance validation

## Success Criteria

- ✅ All unit tests pass
- ✅ All property-based tests pass
- ✅ IME works correctly (Japanese, Chinese, Korean)
- ✅ All TFM functionality works
- ✅ All demo scripts work
- ✅ Code is simpler (400+ lines removed)
- ✅ Documentation is updated
- ✅ No `get_event()` or `get_input()` references in production code

## References

- `doc/dev/CALLBACK_MODE_MIGRATION.md` - Detailed migration plan
- `temp/CALLBACK_MIGRATION_AUDIT.md` - Code audit results
- `doc/dev/CALLBACK_MODE_VS_POLLING_MODE.md` - Architecture comparison
- `doc/dev/IME_SUPPORT_IMPLEMENTATION.md` - IME requirements
- `ttk/renderer.py` - Current interface
- `ttk/backends/coregraphics_backend.py` - Current implementation
- `src/tfm_main.py` - Current TFM usage
