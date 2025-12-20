# Changelog

All notable changes to TTK (TUI Toolkit) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-12-20

### Breaking Changes

This release removes polling mode support entirely, migrating to a callback-only event delivery system. This is a **breaking change** that requires code updates for all TTK users.

#### Removed APIs

- **`Renderer.get_event()`** - Removed polling mode event retrieval
- **`Renderer.get_input()`** - Removed backward compatibility alias
- **`CoreGraphicsBackend.get_event()`** - Removed implementation
- **Event queue management** - Removed internal event queue for polling mode

#### Changed APIs

- **`Renderer.set_event_callback(callback)`** - The `callback` parameter is now **required** (not optional)
  - Passing `None` will raise `ValueError`
  - Must be called before running the event loop
- **`Renderer.run_event_loop_iteration()`** - Now requires event callback to be set
  - Will raise `RuntimeError` if callback not set
  - Events are delivered via callbacks only

#### Migration Guide

**Before (Polling Mode):**
```python
renderer = CoreGraphicsBackend()
renderer.initialize()

while True:
    event = renderer.get_event(timeout_ms=16)
    if event:
        if event.key_code == KeyCode.ESCAPE:
            break
    renderer.draw_text(0, 0, "Hello")
    renderer.refresh()
```

**After (Callback Mode):**
```python
from ttk.renderer import EventCallback

class MyAppCallback(EventCallback):
    def __init__(self):
        self.should_quit = False
    
    def on_key_event(self, event):
        if event.key_code == KeyCode.ESCAPE:
            self.should_quit = True
            return True
        return False
    
    def on_char_event(self, event):
        return False
    
    def should_close(self):
        return self.should_quit

renderer = CoreGraphicsBackend()
renderer.initialize()

callback = MyAppCallback()
renderer.set_event_callback(callback)  # Required!

while not callback.should_quit:
    renderer.run_event_loop_iteration(timeout_ms=16)
    renderer.draw_text(0, 0, "Hello")
    renderer.refresh()
```

See [MIGRATION_GUIDE_V0.2.0.md](doc/MIGRATION_GUIDE_V0.2.0.md) for complete migration instructions.

### Added

- **Event callback validation** - `set_event_callback()` now validates that callback is not None
- **Runtime validation** - `run_event_loop_iteration()` validates callback is set before processing events
- **Improved error messages** - Clear error messages when callback requirements are not met
- **Test utilities** - New `EventCapture` helper class for testing callback mode (in `ttk/test/test_utils.py`)

### Changed

- **Event delivery** - All events are now delivered exclusively via `EventCallback` methods
- **IME support** - IME (Input Method Editor) now works correctly with callback-only mode
- **CoreGraphics backend** - Simplified event handling by removing dual-mode logic
- **Documentation** - Updated all documentation to reflect callback-only architecture

### Removed

- **Polling mode support** - Completely removed to simplify architecture
- **Event queue** - Removed internal event queue management
- **Conditional callback logic** - Removed `if self.event_callback:` checks throughout codebase
- **Dual-mode complexity** - Removed approximately 450 lines of code

### Fixed

- **IME compatibility** - IME now works correctly without polling mode interference
- **Event delivery consistency** - Events are always delivered the same way (via callbacks)
- **Code maintainability** - Simplified codebase is easier to understand and maintain

### Why This Change?

1. **IME Requirements** - Input Method Editors (Japanese, Chinese, Korean input) require callback mode
2. **Code Simplification** - Removed 450+ lines of dead code and complexity
3. **Single Path** - One event delivery mechanism is easier to understand and maintain
4. **Modern Architecture** - Callback-based event handling is the standard pattern
5. **No Actual Users** - TFM (the only TTK user) already uses callback mode exclusively

### Impact

- **All TTK users must update their code** to use callback mode
- **Tests must be updated** to use `EventCapture` helper or implement `EventCallback`
- **Demo scripts must be updated** to use callback mode
- **No functionality is lost** - callback mode provides all the same capabilities

### Documentation Updates

- Updated [README.md](README.md) with callback-only examples
- Updated [USER_GUIDE.md](doc/USER_GUIDE.md) to remove polling mode
- Updated [API_REFERENCE.md](doc/API_REFERENCE.md) with new API signatures
- Updated [EVENT_SYSTEM.md](doc/EVENT_SYSTEM.md) with callback-only architecture
- Created [MIGRATION_GUIDE_V0.2.0.md](doc/MIGRATION_GUIDE_V0.2.0.md) for migration help
- Updated developer documentation in [CALLBACK_MODE_VS_POLLING_MODE.md](../doc/dev/CALLBACK_MODE_VS_POLLING_MODE.md)

## [0.1.0] - 2024-11-15

### Initial Release

- Core rendering API with abstract `Renderer` base class
- Curses backend for terminal applications
- CoreGraphics backend for native macOS desktop applications
- Input event system with `KeyEvent` and `CharEvent`
- Color management with RGB color pairs
- Text attributes (bold, underline, reverse)
- Drawing operations (text, lines, rectangles)
- Window management (clear, refresh, dimensions)
- Command serialization for remote rendering
- Comprehensive documentation and examples
- Test suite with unit and integration tests
- Demo applications showing TTK features

### Features

- **Backend Agnostic** - Write once, run on multiple platforms
- **Dual Mode Support** - Both polling and callback event delivery (deprecated in 0.2.0)
- **Performance** - Efficient rendering with partial updates
- **Extensible** - Easy to implement custom backends

---

## Version History

- **0.2.0** (2024-12-20) - Callback-only mode (breaking changes)
- **0.1.0** (2024-11-15) - Initial release

## Upgrade Notes

### From 0.1.0 to 0.2.0

This is a **major breaking change**. You must update all code that uses TTK:

1. Remove all `get_event()` and `get_input()` calls
2. Implement `EventCallback` interface for your application
3. Call `set_event_callback()` during initialization
4. Update event loop to use `run_event_loop_iteration()` only
5. Update tests to use `EventCapture` helper or implement `EventCallback`

See [MIGRATION_GUIDE_V0.2.0.md](doc/MIGRATION_GUIDE_V0.2.0.md) for detailed instructions and examples.

## Links

- [Repository](https://github.com/tfm/ttk)
- [Documentation](doc/)
- [Migration Guide](doc/MIGRATION_GUIDE_V0.2.0.md)
- [API Reference](doc/API_REFERENCE.md)
