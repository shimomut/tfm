# Design Document

## Overview

This design document outlines the implementation of wide character (Zenkaku) support in TFM to fix layout issues when displaying filenames containing Japanese and other wide Unicode characters. The solution involves creating a centralized wide character handling system and updating all text rendering components to use proper display width calculations.

## Architecture

### Core Components

1. **Wide Character Utilities Module** (`tfm_wide_char_utils.py`)
   - Centralized functions for measuring and handling wide characters
   - String truncation and padding utilities that respect character boundaries
   - Terminal capability detection for Unicode support

2. **Text Rendering Updates**
   - Update `draw_pane()` method in `tfm_main.py` to use wide character utilities
   - Modify column width calculations throughout the codebase
   - Update cursor positioning logic to account for display width

3. **TextViewer Updates**
   - Update `tfm_text_viewer.py` to handle wide characters in file content
   - Fix text wrapping and line display for wide character content
   - Ensure proper cursor positioning and scrolling in text files

4. **Dialog System Updates**
   - Update all dialog components to handle wide characters properly
   - Ensure text input fields work correctly with wide characters

## Components and Interfaces

### Wide Character Utilities Module

```python
# tfm_wide_char_utils.py

def get_display_width(text: str) -> int:
    """Calculate the display width of a string, accounting for wide characters."""
    
def truncate_to_width(text: str, max_width: int, ellipsis: str = "...") -> str:
    """Truncate text to fit within max_width display columns."""
    
def pad_to_width(text: str, width: int, align: str = 'left') -> str:
    """Pad text to exact display width, accounting for wide characters."""
    
def split_at_width(text: str, width: int) -> tuple[str, str]:
    """Split text at display width boundary, preserving character integrity."""
    
def is_wide_character(char: str) -> bool:
    """Check if a character is a wide (double-width) character."""
    
def detect_terminal_unicode_support() -> bool:
    """Detect if terminal supports Unicode wide characters properly."""
```

### Updated File Display Interface

The `draw_pane()` method will be updated to use wide character utilities:

```python
def draw_pane(self, pane_data, start_x, pane_width, is_active):
    """Draw a single pane with proper wide character support."""
    # Use get_display_width() instead of len() for all width calculations
    # Use truncate_to_width() instead of string slicing
    # Use pad_to_width() for column alignment
```

### TextViewer Interface

The TextViewer will be updated to handle wide characters in file content:

```python
class TextViewer:
    def _wrap_line(self, line: str, width: int) -> list[str]:
        """Wrap line accounting for wide character display width."""
        # Use wide character utilities for proper line wrapping
        
    def _draw_line(self, stdscr, y: int, x: int, line: str, max_width: int):
        """Draw line with proper wide character handling."""
        # Use truncate_to_width() for line display
```

### Dialog System Interface

All dialog components will be updated to use wide character utilities:

```python
class SingleLineTextEdit:
    def draw(self, stdscr, y, x, max_width, label="", is_active=True):
        # Use wide character utilities for cursor positioning and text display
```

## Data Models

### Wide Character Metadata

```python
@dataclass
class TextMetrics:
    """Metadata about text display characteristics."""
    char_count: int          # Number of Unicode characters
    display_width: int       # Display width in terminal columns
    has_wide_chars: bool     # Whether text contains wide characters
    has_combining_chars: bool # Whether text contains combining characters
```

### Terminal Capabilities

```python
@dataclass
class TerminalCapabilities:
    """Terminal Unicode support capabilities."""
    supports_unicode: bool
    supports_wide_chars: bool
    supports_combining_chars: bool
    fallback_mode: bool
```

## Error Handling

### Character Encoding Issues

1. **Invalid Unicode Sequences**
   - Gracefully handle malformed Unicode in filenames
   - Provide fallback display using replacement characters
   - Log warnings for debugging

2. **Terminal Limitations**
   - Detect terminal capabilities at startup
   - Provide ASCII-safe fallback mode for limited terminals
   - Handle terminals with partial Unicode support

3. **Width Calculation Failures**
   - Fallback to character count if width calculation fails
   - Handle edge cases with zero-width and combining characters
   - Provide safe defaults for unknown character types

### Implementation Strategy

```python
def safe_get_display_width(text: str) -> int:
    """Safely calculate display width with fallback."""
    try:
        return get_display_width(text)
    except (UnicodeError, ValueError) as e:
        # Log warning and fallback to character count
        return len(text)
```

## Testing Strategy

### Unit Tests

1. **Wide Character Utilities Tests**
   - Test display width calculation for various character types
   - Test truncation at character boundaries
   - Test padding with mixed character widths
   - Test edge cases (empty strings, only wide chars, mixed content)

2. **Integration Tests**
   - Test file display with Japanese filenames
   - Test text viewer with wide character file content
   - Test dialog input with wide characters
   - Test cursor positioning accuracy
   - Test column alignment with mixed character types

3. **Terminal Compatibility Tests**
   - Test behavior in different terminal environments
   - Test fallback modes for limited terminals
   - Test with various locale settings

### Test Data

```python
TEST_FILENAMES = [
    "normal_file.txt",           # ASCII only
    "日本語ファイル.txt",          # Japanese characters
    "mixed_英語_file.txt",        # Mixed ASCII and Japanese
    "emoji_📁_folder",           # Emoji characters
    "combining_é_chars.txt",     # Combining characters
    "zero_width_‌_chars.txt",    # Zero-width characters
]
```

### Performance Tests

1. **Display Width Calculation Performance**
   - Benchmark width calculation for large file lists
   - Compare performance with current len() approach
   - Ensure acceptable performance impact

2. **Memory Usage**
   - Monitor memory usage with wide character processing
   - Test with directories containing many wide character filenames

## Implementation Details

### Phase 1: Core Utilities

1. Create `tfm_wide_char_utils.py` with basic width calculation functions
2. Implement Unicode character classification using `unicodedata` module
3. Add terminal capability detection
4. Create comprehensive unit tests

### Phase 2: File Display Updates

1. Update `draw_pane()` method to use wide character utilities
2. Fix column width calculations in file list display
3. Update filename truncation logic
4. Test with various filename types

### Phase 3: TextViewer Updates

1. Update `tfm_text_viewer.py` to use wide character utilities
2. Fix line wrapping for wide character content
3. Update text display and cursor positioning in text viewer
4. Test text viewer with files containing wide characters

### Phase 4: Dialog System Updates

1. Update `SingleLineTextEdit` for proper cursor positioning
2. Fix text input handling for wide characters
3. Update all dialog components to use wide character utilities
4. Test dialog functionality with wide character input

### Phase 5: Integration and Testing

1. Comprehensive integration testing
2. Performance optimization
3. Terminal compatibility testing
4. Documentation updates

## Technical Specifications

### Unicode Character Width Detection

The implementation will use Python's `unicodedata` module and East Asian Width property:

```python
import unicodedata

def is_wide_character(char: str) -> bool:
    """Check if character has double display width."""
    if len(char) != 1:
        return False
    
    # East Asian Width property
    width = unicodedata.east_asian_width(char)
    return width in ('F', 'W')  # Fullwidth or Wide
```

### Display Width Calculation Algorithm

```python
def get_display_width(text: str) -> int:
    """Calculate display width accounting for all character types."""
    width = 0
    i = 0
    while i < len(text):
        char = text[i]
        
        # Handle combining characters
        if unicodedata.combining(char):
            # Combining characters don't add width
            pass
        elif is_wide_character(char):
            width += 2
        else:
            width += 1
        
        i += 1
    
    return width
```

### Safe Truncation Algorithm

```python
def truncate_to_width(text: str, max_width: int, ellipsis: str = "...") -> str:
    """Truncate text preserving character boundaries."""
    if get_display_width(text) <= max_width:
        return text
    
    ellipsis_width = get_display_width(ellipsis)
    target_width = max_width - ellipsis_width
    
    if target_width <= 0:
        return ellipsis[:max_width]
    
    result = ""
    current_width = 0
    
    for char in text:
        char_width = get_display_width(char)
        if current_width + char_width > target_width:
            break
        result += char
        current_width += char_width
    
    return result + ellipsis
```

## Future Enhancements

### Advanced Unicode Support

1. **Grapheme Cluster Support**
   - Handle complex Unicode sequences (emoji with modifiers)
   - Support for regional indicator sequences (flag emojis)

2. **Bidirectional Text Support**
   - Handle right-to-left text in filenames
   - Proper cursor positioning in mixed-direction text

3. **Font-Aware Width Calculation**
   - Detect terminal font characteristics
   - Adjust width calculations based on font metrics

### Performance Optimizations

1. **Caching**
   - Cache display width calculations for frequently accessed filenames
   - Implement LRU cache for width calculations

2. **Lazy Evaluation**
   - Calculate widths only when needed for display
   - Optimize for common ASCII-only cases

## Migration Strategy

### Backward Compatibility

1. **Graceful Degradation**
   - Maintain current behavior for ASCII-only filenames
   - Provide fallback mode for terminals without Unicode support

2. **Configuration Options**
   - Allow users to disable wide character support if needed
   - Provide configuration for different Unicode handling modes

### Rollout Plan

1. **Development Phase**
   - Implement core utilities with comprehensive tests
   - Update file display components incrementally

2. **Testing Phase**
   - Beta testing with users who have wide character filenames
   - Performance testing on various systems

3. **Production Release**
   - Gradual rollout with monitoring
   - Quick rollback capability if issues arise