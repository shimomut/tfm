# SingleLineTextEdit Word-Level Navigation Implementation

## Overview

Added word-level cursor movement and deletion features to the `SingleLineTextEdit` component, enabling faster text editing through keyboard shortcuts commonly found in modern text editors.

## Features Implemented

### 1. Word-Level Cursor Movement

- **Alt+Left**: Move cursor to the beginning of the previous word
- **Alt+Right**: Move cursor to the beginning of the next word

### 2. Word-Level Deletion

- **Alt+Backspace**: Delete from cursor position to the beginning of the previous word

## Implementation Details

### Word Character Definition

A "word character" is defined as any alphanumeric character (letter or digit) or underscore. All other characters are treated as word boundaries, including:
- Whitespace (spaces, tabs, newlines)
- Punctuation marks: `~` `` ` `` `[` `]` `-` `=` `|` `\` `/` `.` `,` etc.
- Special symbols: `!` `@` `#` `$` `%` `^` `&` `*` `(` `)` `+` etc.

This matches the behavior of most modern text editors and IDEs.

### Word Boundary Detection

Three utility functions were added to support word-level operations:

#### `_is_word_char(char)`

Determines if a character is a word character (alphanumeric or underscore).

```python
return char.isalnum() or char == '_'
```

#### `_find_previous_word_boundary(pos)`

Finds the position of the previous word boundary from a given position. The algorithm:
1. Moves back one position from the current cursor
2. Skips any non-word characters (whitespace, punctuation, etc.)
3. Skips word characters (the word itself)
4. Adjusts position to land after non-word characters if needed

#### `_find_next_word_boundary(pos)`

Finds the position of the next word boundary from a given position. The algorithm:
1. Skips word characters (current word)
2. Skips any non-word characters (whitespace, punctuation, etc.)
3. Returns the position at the start of the next word

### Navigation Methods

#### `move_cursor_word_left()`

Moves the cursor to the beginning of the previous word using `_find_previous_word_boundary()`.

#### `move_cursor_word_right()`

Moves the cursor to the beginning of the next word using `_find_next_word_boundary()`.

#### `delete_word_backward()`

Deletes text from the cursor position back to the previous word boundary, combining word boundary detection with text deletion.

### Key Event Handling

The `handle_key()` method was updated to check for Alt modifier key combinations before processing standard character-level navigation:

```python
# Word-level navigation with Alt modifier
if event.key_code == KeyCode.LEFT and event.modifiers == ModifierKey.ALT:
    return self.move_cursor_word_left()
elif event.key_code == KeyCode.RIGHT and event.modifiers == ModifierKey.ALT:
    return self.move_cursor_word_right()
# Word-level deletion with Alt+Backspace
elif event.key_code == KeyCode.BACKSPACE and event.modifiers == ModifierKey.ALT:
    return self.delete_word_backward()
```

## Testing

Comprehensive test suite added in `test/test_single_line_text_edit_word_navigation.py`:

- **TestWordNavigation**: 9 tests covering word-level cursor movement
  - Basic left/right navigation
  - Multiple spaces handling
  - Navigation from middle of words
  - Edge cases (empty text, single word, only spaces)

- **TestWordDeletion**: 7 tests covering word-level deletion
  - Basic backward deletion
  - Deletion from middle of words
  - Multiple spaces handling
  - Edge cases (at start, single word, only spaces)
  - Preservation of text after cursor

- **TestWordBoundaryHelpers**: 2 tests for utility functions
  - Previous word boundary detection
  - Next word boundary detection

- **TestPunctuationWordBoundaries**: 9 tests for punctuation handling
  - Word character detection (`_is_word_char`)
  - Navigation with hyphens, brackets, slashes, equals signs
  - Navigation with multiple consecutive punctuation marks
  - Deletion with punctuation in paths and hyphenated words
  - Underscore treated as word character

All 27 tests pass, and existing SingleLineTextEdit tests remain unaffected.

## Examples

### Navigation with Punctuation

```
Text: "hello-world-test"
Position 0 → Alt+Right → Position 6 (start of "world")
Position 6 → Alt+Right → Position 12 (start of "test")
```

```
Text: "/usr/local/bin"
Position 0 → Alt+Right → Position 1 (start of "usr")
Position 1 → Alt+Right → Position 5 (start of "local")
Position 5 → Alt+Right → Position 11 (start of "bin")
```

### Deletion with Punctuation

```
Text: "hello-world" (cursor at end)
Alt+Backspace → "hello-" (deleted "world")
Alt+Backspace → "" (deleted "-" and "hello")
```

## Demo

Interactive demo available at `demo/demo_single_line_text_edit_word_navigation.py` showcasing:
- Word-level navigation with Alt+Left/Right
- Word-level deletion with Alt+Backspace
- Visual feedback showing cursor position

## Files Modified

- `src/tfm_single_line_text_edit.py`: Core implementation
- `test/test_single_line_text_edit_word_navigation.py`: Test suite (new)
- `demo/demo_single_line_text_edit_word_navigation.py`: Interactive demo (new)

## Compatibility

- Fully backward compatible with existing SingleLineTextEdit usage
- No changes to public API beyond new methods
- All existing tests pass without modification
