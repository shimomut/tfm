# Syntax Highlighting Fix

## Problem
When syntax highlighting was enabled in the TFM text viewer, users saw ANSI escape sequences (like `^[[33m`) instead of actual colors. This happened because the original implementation used pygments' `TerminalFormatter`, which outputs ANSI escape sequences that curses doesn't interpret as colors.

## Root Cause
- **Pygments TerminalFormatter** outputs ANSI escape sequences for terminal colors
- **Curses library** doesn't interpret ANSI escape sequences - it has its own color system
- **Mismatch** between pygments output format and curses color expectations

## Solution
Completely rewrote the syntax highlighting system to use **curses-native colors**:

### 1. Token-Based Approach
- Use pygments for **tokenization only** (not formatting)
- Get raw tokens with `lexer.get_tokens(content)`
- Map token types to curses color pairs directly

### 2. Curses Color System
- Added 7 new color pairs for syntax highlighting:
  - `COLOR_SYNTAX_KEYWORD` - Orange for keywords (def, class, if, etc.)
  - `COLOR_SYNTAX_STRING` - Green for string literals
  - `COLOR_SYNTAX_COMMENT` - Gray for comments
  - `COLOR_SYNTAX_NUMBER` - Yellow for numbers
  - `COLOR_SYNTAX_OPERATOR` - Magenta for operators
  - `COLOR_SYNTAX_BUILTIN` - Cyan for built-in functions
  - `COLOR_SYNTAX_NAME` - Light gray for variable names

### 3. Line-by-Line Rendering
- Convert tokens to lines of `(text, color)` tuples
- Render each text segment with its appropriate curses color
- Handle line breaks and horizontal scrolling properly

## Code Changes

### New Data Structure
```python
# Before: List of strings with ANSI escape sequences
self.lines = ["^[[33mdef^[[0m hello():"]

# After: List of lists of (text, color) tuples  
self.highlighted_lines = [
    [("def", COLOR_SYNTAX_KEYWORD), (" ", COLOR_REGULAR_FILE), 
     ("hello", COLOR_SYNTAX_NAME), ("():", COLOR_SYNTAX_OPERATOR)]
]
```

### Token Processing
```python
def tokens_to_highlighted_lines(self, tokens):
    """Convert pygments tokens to curses-compatible format"""
    for token_type, text in tokens:
        color = get_syntax_color(token_type)  # Map to curses color
        # Handle newlines and build line structure
```

### Rendering
```python
def draw_content(self):
    """Render with proper curses colors"""
    for text, color in highlighted_line:
        self.stdscr.addstr(y_pos, x_pos, text, color)  # Direct curses color
```

## Benefits

### ✅ Proper Color Display
- **No more escape sequences** visible in text
- **True syntax highlighting** with proper colors
- **Terminal compatibility** across different terminal types

### ✅ Performance Improvement
- **No string parsing** of ANSI sequences
- **Direct color application** is faster
- **Better memory usage** with structured data

### ✅ Maintainability
- **Clear separation** between tokenization and rendering
- **Easy color customization** through curses color pairs
- **Robust error handling** with graceful fallbacks

## Testing
- ✅ Python files show proper keyword, string, and comment colors
- ✅ JSON files display with appropriate data structure highlighting
- ✅ Markdown files render with proper formatting colors
- ✅ Toggle functionality (s key) works correctly
- ✅ Fallback to plain text when pygments unavailable

## Result
The text viewer now displays **professional syntax highlighting** with proper colors instead of escape sequences, providing a clean and readable code viewing experience within TFM.