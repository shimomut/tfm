# Clipboard Support Feature

## Overview

TTK provides clipboard (pasteboard) support that enables applications to read from and write to the system clipboard. This feature allows users to copy text from TTK applications and paste it into other applications, or paste text from other applications into TTK applications.

**Current Support:**
- ✅ Plain-text clipboard operations in desktop mode (CoreGraphics backend)
- ✅ Graceful degradation in terminal mode (Curses backend)
- ⏳ Rich text and binary data support (planned for future releases)

## Quick Start

### Basic Usage

```python
from ttk import TtkApplication

# Create your TTK application
app = TtkApplication()

# Check if clipboard is supported
if app.renderer.supports_clipboard():
    # Read text from clipboard
    text = app.renderer.get_clipboard_text()
    print(f"Clipboard contains: {text}")
    
    # Write text to clipboard
    success = app.renderer.set_clipboard_text("Hello, clipboard!")
    if success:
        print("Text copied to clipboard")
```

### Copy and Paste Example

```python
# Copy selected text to clipboard
def copy_selection(app, selected_text):
    if app.renderer.supports_clipboard():
        if app.renderer.set_clipboard_text(selected_text):
            app.show_message("Copied to clipboard")
        else:
            app.show_message("Failed to copy")
    else:
        app.show_message("Clipboard not supported")

# Paste text from clipboard
def paste_from_clipboard(app):
    if app.renderer.supports_clipboard():
        text = app.renderer.get_clipboard_text()
        if text:
            app.insert_text(text)
        else:
            app.show_message("Clipboard is empty")
    else:
        app.show_message("Clipboard not supported")
```

## API Reference

### `supports_clipboard() -> bool`

Query whether the current backend supports clipboard operations.

**Returns:**
- `True` if clipboard operations are available (desktop mode)
- `False` if clipboard is not supported (terminal mode)

**Example:**
```python
if app.renderer.supports_clipboard():
    # Clipboard operations are available
    text = app.renderer.get_clipboard_text()
else:
    # Clipboard not supported, use alternative approach
    app.show_message("Clipboard not available in terminal mode")
```

### `get_clipboard_text() -> str`

Read plain-text content from the system clipboard.

**Returns:**
- Plain-text string from clipboard
- Empty string if:
  - Clipboard is empty
  - Clipboard contains no text data (only images, files, etc.)
  - Clipboard access fails
  - Backend doesn't support clipboard

**Example:**
```python
text = app.renderer.get_clipboard_text()
if text:
    print(f"Clipboard contains: {text}")
else:
    print("Clipboard is empty or contains no text")
```

**Special Characters:**
All Unicode characters are preserved, including:
- Newlines (`\n`)
- Tabs (`\t`)
- Emoji and Unicode symbols

```python
# Reading multi-line text
text = app.renderer.get_clipboard_text()
lines = text.split('\n')
for line in lines:
    print(line)
```

### `set_clipboard_text(text: str) -> bool`

Write plain-text content to the system clipboard.

**Parameters:**
- `text` (str): Plain-text string to write to clipboard

**Returns:**
- `True` if clipboard was updated successfully
- `False` if operation failed or clipboard is not supported

**Example:**
```python
# Copy simple text
success = app.renderer.set_clipboard_text("Hello, world!")

# Copy multi-line text
multi_line = "Line 1\nLine 2\nLine 3"
success = app.renderer.set_clipboard_text(multi_line)

# Clear clipboard
success = app.renderer.set_clipboard_text("")
```

## Backend Support

### Desktop Mode (CoreGraphics Backend)

**Full clipboard support** using macOS NSPasteboard API:
- ✅ Read plain-text from system clipboard
- ✅ Write plain-text to system clipboard
- ✅ Preserve all Unicode characters
- ✅ Handle multi-line text
- ✅ Clear clipboard with empty string

**Platform:** macOS only (CoreGraphics backend)

### Terminal Mode (Curses Backend)

**Graceful degradation** with stub implementations:
- `supports_clipboard()` returns `False`
- `get_clipboard_text()` returns empty string
- `set_clipboard_text()` returns `False`
- No exceptions raised

**Why terminal mode doesn't support clipboard:**
Terminal applications don't have standard clipboard access. While some terminals support OSC 52 escape sequences for clipboard operations, this is not universally supported and may require terminal-specific configuration.

**Alternative for terminal mode:**
- Use file-based data exchange
- Use named pipes or temporary files
- Implement custom copy/paste buffer within the application

## Limitations

### Current Limitations

1. **Plain-text only**: The current implementation supports only plain-text data. Rich text (HTML, RTF) and binary data (images, files) are not supported.

2. **Desktop mode only**: Full clipboard functionality is only available in desktop mode (CoreGraphics backend). Terminal mode provides stub implementations.

3. **macOS only**: The CoreGraphics backend is macOS-specific. Other platforms are not currently supported.

4. **No clipboard monitoring**: The API does not provide notifications when clipboard content changes. Applications must poll the clipboard if they need to detect changes.

### Planned Enhancements

Future releases may include:
- Rich text (HTML/RTF) clipboard support
- Image data clipboard support
- File URL clipboard support
- Terminal mode clipboard via OSC 52 escape sequences
- Clipboard change notifications

## Troubleshooting

### Clipboard operations return empty/False

**Problem:** `get_clipboard_text()` returns empty string or `set_clipboard_text()` returns `False`.

**Solutions:**

1. **Check backend support:**
   ```python
   if not app.renderer.supports_clipboard():
       print("Clipboard not supported in this mode")
   ```

2. **Verify you're in desktop mode:**
   - Clipboard only works with CoreGraphics backend
   - Terminal mode (Curses) doesn't support clipboard

3. **Check clipboard permissions:**
   - macOS may require clipboard access permissions
   - Check System Preferences → Security & Privacy → Privacy → Automation

4. **Verify clipboard contains text:**
   - If clipboard contains only images/files, `get_clipboard_text()` returns empty string
   - Copy some text to clipboard and try again

### Special characters not preserved

**Problem:** Unicode characters, newlines, or tabs are lost when copying/pasting.

**Solution:**
This should not happen with the current implementation. If you experience this issue:

1. **Verify the text before copying:**
   ```python
   text = "Test\nwith\nnewlines"
   print(repr(text))  # Should show '\n' characters
   app.renderer.set_clipboard_text(text)
   ```

2. **Verify the text after pasting:**
   ```python
   pasted = app.renderer.get_clipboard_text()
   print(repr(pasted))  # Should match original
   ```

3. **Check for application-level processing:**
   - Ensure your application isn't modifying the text
   - Check for text normalization or sanitization code

### Clipboard operations fail silently

**Problem:** Clipboard operations don't work but no error is reported.

**Solution:**

1. **Check return values:**
   ```python
   success = app.renderer.set_clipboard_text("test")
   if not success:
       print("Clipboard write failed")
   ```

2. **Enable debug logging:**
   - Clipboard errors are logged to console
   - Check terminal output for error messages

3. **Test with simple text:**
   ```python
   # Test with minimal text
   app.renderer.set_clipboard_text("test")
   result = app.renderer.get_clipboard_text()
   assert result == "test", f"Expected 'test', got '{result}'"
   ```

### Performance issues with large text

**Problem:** Clipboard operations are slow with large amounts of text.

**Solution:**

1. **Avoid polling clipboard in tight loops:**
   ```python
   # ❌ Bad: Polls clipboard continuously
   while True:
       text = app.renderer.get_clipboard_text()
       process(text)
   
   # ✅ Good: Only check clipboard when needed
   def on_paste_command():
       text = app.renderer.get_clipboard_text()
       process(text)
   ```

2. **Consider text size limits:**
   - Clipboard operations are fast for typical text (< 1MB)
   - Very large text (> 10MB) may be slow
   - Consider chunking or streaming for large data

## Examples

### Example 1: Copy File Path

```python
def copy_file_path(app, file_path):
    """Copy file path to clipboard."""
    if app.renderer.supports_clipboard():
        if app.renderer.set_clipboard_text(file_path):
            app.show_status(f"Copied: {file_path}")
        else:
            app.show_status("Failed to copy path")
    else:
        app.show_status("Clipboard not available")
```

### Example 2: Paste Text into Editor

```python
def paste_into_editor(app, editor):
    """Paste clipboard text into editor."""
    if not app.renderer.supports_clipboard():
        app.show_status("Clipboard not available")
        return
    
    text = app.renderer.get_clipboard_text()
    if text:
        editor.insert_text(text)
        app.show_status(f"Pasted {len(text)} characters")
    else:
        app.show_status("Clipboard is empty")
```

### Example 3: Copy Multiple Items

```python
def copy_selected_items(app, items):
    """Copy multiple items to clipboard (one per line)."""
    if not app.renderer.supports_clipboard():
        app.show_status("Clipboard not available")
        return
    
    # Join items with newlines
    text = '\n'.join(items)
    
    if app.renderer.set_clipboard_text(text):
        app.show_status(f"Copied {len(items)} items")
    else:
        app.show_status("Failed to copy items")
```

### Example 4: Clipboard History

```python
class ClipboardHistory:
    """Simple clipboard history manager."""
    
    def __init__(self, app, max_items=10):
        self.app = app
        self.history = []
        self.max_items = max_items
    
    def save_current(self):
        """Save current clipboard content to history."""
        if not self.app.renderer.supports_clipboard():
            return
        
        text = self.app.renderer.get_clipboard_text()
        if text and (not self.history or text != self.history[0]):
            self.history.insert(0, text)
            self.history = self.history[:self.max_items]
    
    def restore(self, index):
        """Restore clipboard content from history."""
        if 0 <= index < len(self.history):
            self.app.renderer.set_clipboard_text(self.history[index])
```

## See Also

- **Demo Application:** `ttk/demo/demo_clipboard.py` - Interactive demonstration
- **Design Document:** `.kiro/specs/clipboard-support/design.md` - Technical design
- **Requirements:** `.kiro/specs/clipboard-support/requirements.md` - Feature requirements
- **TTK Renderer API:** `ttk/renderer.py` - Base renderer interface
