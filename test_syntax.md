# TFM Text Viewer Test

This is a **test file** for the TFM text viewer with *syntax highlighting*.

## Features

The text viewer supports:

- ✅ **Syntax highlighting** for popular file formats
- ✅ **Line numbers** (toggle with `n`)
- ✅ **Horizontal scrolling** (arrow keys)
- ✅ **Vertical scrolling** (arrow keys, page up/down)
- ✅ **Multiple file formats**

### Supported File Types

1. **Programming Languages**
   - Python (`.py`)
   - JavaScript (`.js`)
   - Java (`.java`)
   - C/C++ (`.c`, `.cpp`, `.h`, `.hpp`)
   - Go (`.go`)
   - Rust (`.rs`)

2. **Markup Languages**
   - HTML (`.html`)
   - XML (`.xml`)
   - Markdown (`.md`)

3. **Data Formats**
   - JSON (`.json`)
   - YAML (`.yml`, `.yaml`)
   - CSV (`.csv`)

4. **Configuration Files**
   - INI (`.ini`, `.cfg`, `.conf`)
   - TOML (`.toml`)

## Usage

### Navigation
- `↑↓` or `j/k` - Scroll vertically
- `←→` or `h/l` - Scroll horizontally  
- `Page Up/Down` - Page scrolling
- `Home/End` - Jump to start/end

### Controls
- `q` or `ESC` - Quit viewer
- `n` - Toggle line numbers
- `w` - Toggle line wrapping
- `s` - Toggle syntax highlighting

## Code Example

```python
def example_function():
    """Example Python code with syntax highlighting"""
    message = "Hello from TFM!"
    print(f"Message: {message}")
    return True
```

```javascript
function exampleFunction() {
    // Example JavaScript code
    const message = "Hello from TFM!";
    console.log(`Message: ${message}`);
    return true;
}
```

## Installation Note

For **full syntax highlighting**, install pygments:

```bash
pip install pygments
```

If pygments is not available, the viewer will still work but without syntax highlighting.

---

*This file demonstrates the TFM text viewer capabilities.*