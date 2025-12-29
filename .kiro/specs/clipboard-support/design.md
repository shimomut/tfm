# Design Document

## Overview

This document describes the design for adding clipboard (pasteboard) support to the TTK library. The feature enables TTK applications to read from and write to the system clipboard, initially supporting plain-text data in desktop mode (CoreGraphics backend). The design follows TTK's existing architectural patterns with backend-specific implementations and a unified API.

## Architecture

The clipboard functionality will be integrated into TTK's existing backend architecture:

```
┌─────────────────────────────────────────────────────────┐
│                  TTK Application                        │
│                 (e.g., TFM)                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Uses Renderer API
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Renderer (Abstract Base)                   │
│  + get_clipboard_text() -> str                         │
│  + set_clipboard_text(text: str) -> bool               │
│  + supports_clipboard() -> bool                        │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ CoreGraphics     │    │ Curses           │
│ Backend          │    │ Backend          │
│                  │    │                  │
│ Uses NSPasteboard│    │ Stub             │
│ for real         │    │ implementation   │
│ clipboard access │    │ (returns empty)  │
└──────────────────┘    └──────────────────┘
```

### Design Rationale

1. **Backend-Specific Implementation**: Clipboard access is inherently platform-specific. Desktop mode (CoreGraphics) has full system clipboard access via NSPasteboard, while terminal mode (Curses) has no standard clipboard API.

2. **Unified API**: Applications use the same methods regardless of backend, with graceful degradation in terminal mode.

3. **Minimal API Surface**: Three methods provide complete functionality:
   - `supports_clipboard()`: Query capability
   - `get_clipboard_text()`: Read plain text
   - `set_clipboard_text()`: Write plain text

## Components and Interfaces

### 1. Renderer Base Class (ttk/renderer.py)

Add three abstract methods to the Renderer base class:

```python
@abstractmethod
def supports_clipboard(self) -> bool:
    """
    Query whether this backend supports clipboard operations.
    
    Returns:
        bool: True if clipboard operations are available, False otherwise.
    """
    pass

@abstractmethod
def get_clipboard_text() -> str:
    """
    Get plain-text content from the system clipboard.
    
    Returns:
        str: Plain-text content from clipboard, or empty string if:
            - Clipboard is empty
            - Clipboard contains no text data
            - Clipboard access fails
            - Backend doesn't support clipboard
    """
    pass

@abstractmethod
def set_clipboard_text(text: str) -> bool:
    """
    Set plain-text content to the system clipboard.
    
    Args:
        text: Plain-text string to write to clipboard
    
    Returns:
        bool: True if clipboard was updated successfully, False otherwise
    """
    pass
```

### 2. CoreGraphics Backend (ttk/backends/coregraphics_backend.py)

Implement clipboard methods using macOS NSPasteboard API:

```python
def supports_clipboard(self) -> bool:
    """CoreGraphics backend supports clipboard."""
    return True

def get_clipboard_text(self) -> str:
    """
    Get plain-text from macOS pasteboard.
    
    Uses NSPasteboard.generalPasteboard() to access the system clipboard
    and retrieves NSPasteboardTypeString data.
    """
    try:
        pasteboard = Cocoa.NSPasteboard.generalPasteboard()
        # Get string content from pasteboard
        text = pasteboard.stringForType_(Cocoa.NSPasteboardTypeString)
        return text if text else ""
    except Exception as e:
        # Log error and return empty string
        print(f"Error reading clipboard: {e}")
        return ""

def set_clipboard_text(self, text: str) -> bool:
    """
    Set plain-text to macOS pasteboard.
    
    Uses NSPasteboard.generalPasteboard() to access the system clipboard,
    clears existing content, and writes NSPasteboardTypeString data.
    """
    try:
        pasteboard = Cocoa.NSPasteboard.generalPasteboard()
        # Clear existing content
        pasteboard.clearContents()
        # Write string to pasteboard
        success = pasteboard.setString_forType_(text, Cocoa.NSPasteboardTypeString)
        return bool(success)
    except Exception as e:
        # Log error and return False
        print(f"Error writing clipboard: {e}")
        return False
```

### 3. Curses Backend (ttk/backends/curses_backend.py)

Implement stub methods that gracefully degrade:

```python
def supports_clipboard(self) -> bool:
    """Curses backend does not support clipboard."""
    return False

def get_clipboard_text(self) -> str:
    """Return empty string (clipboard not supported in terminal mode)."""
    return ""

def set_clipboard_text(self, text: str) -> bool:
    """Return False (clipboard not supported in terminal mode)."""
    return False
```

## Data Models

### Plain Text Format

The initial implementation supports only plain-text data:

- **Encoding**: UTF-8 (Python's default string encoding)
- **Line Endings**: Preserved as-is (no normalization)
- **Special Characters**: All Unicode characters supported, including:
  - Newlines (`\n`)
  - Tabs (`\t`)
  - Emoji and other Unicode symbols
- **Empty String**: Valid clipboard content (clears clipboard)
- **Rich Text Handling**: When the clipboard contains rich text (HTML, RTF, etc.), `get_clipboard_text()` will attempt to extract the plain-text representation. macOS NSPasteboard automatically provides plain-text conversion for rich content types.

### Future Extensions

The design allows for future rich-text and binary data support:

```python
# Future methods (not implemented in initial version)
def get_clipboard_html(self) -> str: ...
def set_clipboard_html(self, html: str) -> bool: ...
def get_clipboard_image(self) -> bytes: ...
def set_clipboard_image(self, image_data: bytes) -> bool: ...
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Clipboard Read Returns String

*For any* clipboard state, calling `get_clipboard_text()` should return a string (never None or raise an exception).

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Empty Clipboard Returns Empty String

*For any* backend, when the system clipboard is empty or contains no text data (only non-text data like images), `get_clipboard_text()` should return an empty string.

**Validates: Requirements 1.2, 1.3**

### Property 3: Clipboard Write Round Trip

*For any* valid UTF-8 string, writing it to the clipboard then immediately reading it back should return an equivalent string (in desktop mode).

**Validates: Requirements 2.1, 2.3**

### Property 4: Empty String Clears Clipboard

*For any* clipboard state, writing an empty string should result in subsequent reads returning an empty string (in desktop mode).

**Validates: Requirements 2.2**

### Property 5: Special Characters Preserved

*For any* string containing newlines, tabs, or Unicode characters, writing to clipboard then reading back should preserve all characters exactly (in desktop mode).

**Validates: Requirements 2.3**

### Property 6: Terminal Mode Graceful Degradation

*For any* clipboard operation in terminal mode (Curses backend), the operation should complete without raising exceptions, with reads returning empty string and writes returning False.

**Validates: Requirements 1.4, 2.4, 3.2, 3.3**

### Property 7: Capability Query Consistency

*For any* backend, `supports_clipboard()` should return True if and only if clipboard operations actually work (CoreGraphics returns True, Curses returns False).

**Validates: Requirements 3.1, 3.2, 3.4**

### Property 8: Error Handling Never Crashes

*For any* error condition (clipboard inaccessible, permission denied, etc.), clipboard methods should return safe default values (empty string or False) without raising exceptions.

**Validates: Requirements 4.1, 4.2, 4.3**

## Error Handling

### Error Categories

1. **Clipboard Unavailable**: System clipboard service not accessible
   - Return: Empty string (read) or False (write)
   - Log: Warning message with error details

2. **Permission Denied**: Application lacks clipboard access permissions
   - Return: Empty string (read) or False (write)
   - Log: Error message suggesting permission check

3. **Invalid Data**: Clipboard contains data that cannot be decoded as text
   - Return: Empty string (read)
   - Log: Warning message about data format

4. **Backend Not Supported**: Terminal mode (Curses) backend
   - Return: Empty string (read) or False (write)
   - Log: No logging (expected behavior)

### Error Handling Strategy

```python
def get_clipboard_text(self) -> str:
    """Get clipboard text with comprehensive error handling."""
    try:
        # Attempt clipboard access
        pasteboard = Cocoa.NSPasteboard.generalPasteboard()
        text = pasteboard.stringForType_(Cocoa.NSPasteboardTypeString)
        return text if text else ""
    except AttributeError as e:
        # PyObjC not available or API changed
        print(f"Clipboard API error: {e}")
        return ""
    except Exception as e:
        # Catch-all for unexpected errors
        print(f"Unexpected clipboard error: {e}")
        return ""

def set_clipboard_text(self, text: str) -> bool:
    """Set clipboard text with comprehensive error handling."""
    try:
        pasteboard = Cocoa.NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        success = pasteboard.setString_forType_(text, Cocoa.NSPasteboardTypeString)
        return bool(success)
    except AttributeError as e:
        print(f"Clipboard API error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected clipboard error: {e}")
        return False
```

## Testing Strategy

### Unit Tests

Unit tests verify specific examples and edge cases:

1. **Desktop Mode Tests** (`ttk/test/test_coregraphics_clipboard.py`):
   - Test reading empty clipboard
   - Test writing and reading simple text
   - Test writing and reading text with newlines
   - Test writing and reading text with tabs
   - Test writing and reading Unicode/emoji
   - Test writing empty string clears clipboard
   - Test `supports_clipboard()` returns True

2. **Terminal Mode Tests** (`ttk/test/test_curses_clipboard.py`):
   - Test `supports_clipboard()` returns False
   - Test `get_clipboard_text()` returns empty string
   - Test `set_clipboard_text()` returns False
   - Test operations don't raise exceptions

3. **Error Handling Tests**:
   - Test graceful handling of clipboard access errors
   - Test graceful handling of invalid data formats

### Property-Based Tests

Property tests verify universal properties across many inputs:

1. **Property Test: Clipboard Read Returns String** (`test_pbt_clipboard_read_returns_string`):
   - Generate: Random clipboard states
   - Test: `get_clipboard_text()` always returns a string
   - **Property 1: Clipboard Read Returns String**
   - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

2. **Property Test: Clipboard Write Round Trip** (`test_pbt_clipboard_write_round_trip`):
   - Generate: Random UTF-8 strings (including special characters)
   - Test: Write then read returns equivalent string (desktop mode)
   - **Property 3: Clipboard Write Round Trip**
   - **Validates: Requirements 2.1, 2.3**

3. **Property Test: Special Characters Preserved** (`test_pbt_special_characters_preserved`):
   - Generate: Strings with newlines, tabs, Unicode, emoji
   - Test: All characters preserved in round trip (desktop mode)
   - **Property 5: Special Characters Preserved**
   - **Validates: Requirements 2.3**

4. **Property Test: Terminal Mode Never Crashes** (`test_pbt_terminal_mode_never_crashes`):
   - Generate: Random strings and operations
   - Test: All operations complete without exceptions (terminal mode)
   - **Property 6: Terminal Mode Graceful Degradation**
   - **Validates: Requirements 1.4, 2.4, 3.2, 3.3**

### Integration Tests

Integration tests verify clipboard works with real TTK applications:

1. **Demo Application** (`ttk/demo/demo_clipboard.py`):
   - Interactive demo showing clipboard read/write
   - Tests both desktop and terminal modes
   - Provides visual confirmation of functionality

2. **TFM Integration** (future):
   - Test copying filenames to system clipboard
   - Test pasting text from system clipboard into text editor
   - Test clipboard operations in both desktop and terminal modes

### Test Configuration

- **Minimum 100 iterations** per property test (due to randomization)
- **Tag format**: `Feature: clipboard-support, Property {number}: {property_text}`
- **Test isolation**: Each test should not depend on system clipboard state
- **Cleanup**: Tests should restore original clipboard content after completion

## Implementation Notes

### macOS Pasteboard Types

The implementation uses `NSPasteboardTypeString` for plain text:

```python
# macOS 10.6+ modern pasteboard type
Cocoa.NSPasteboardTypeString  # Equivalent to "public.utf8-plain-text"

# Legacy type (deprecated but still works)
Cocoa.NSStringPboardType  # Equivalent to "NSStringPboardType"
```

We use the modern `NSPasteboardTypeString` for better compatibility with macOS 10.6+.

### Thread Safety

NSPasteboard operations are thread-safe on macOS, but TTK applications typically run on a single thread. No additional synchronization is needed.

### Performance Considerations

- Clipboard access is fast (< 1ms for typical text)
- No caching needed - system handles clipboard efficiently
- Applications should avoid polling clipboard in tight loops

### Future Enhancements

1. **Rich Text Support**: Add HTML clipboard support
2. **Image Support**: Add image data clipboard support
3. **File URLs**: Add file path/URL clipboard support
4. **Terminal Mode**: Investigate OSC 52 escape sequence for terminal clipboard
5. **Clipboard Monitoring**: Add callback for clipboard change notifications

## Dependencies

- **macOS**: PyObjC (already required for CoreGraphics backend)
- **Terminal**: No additional dependencies (stub implementation)

## Backward Compatibility

This is a new feature with no backward compatibility concerns. Existing TTK applications will continue to work without modification. Applications that want clipboard support can check `supports_clipboard()` before using the feature.
