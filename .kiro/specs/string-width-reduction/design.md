# Design Document: String Width Reduction Utility

## Overview

The String Width Reduction utility provides intelligent string shortening functionality for terminal UI components. It accounts for wide characters (CJK, emoji), supports multiple shortening strategies (removal, abbreviation), and offers both simple and advanced APIs for different use cases.

The module will be implemented as `src/tfm_string_width.py` and will integrate with existing TFM UI components like QuickChoiceBar, status bars, and dialogs.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                  Public API Layer                        │
│  - reduce_width()                                        │
│  - abbreviate_middle()                                   │
│  - abbreviate_path()                                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Width Calculation Engine                    │
│  - Uses TTK's wide_char_utils.get_display_width()       │
│  - normalize_unicode()                                   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│            Shortening Strategy Engine                    │
│  - RemovalStrategy                                       │
│  - AbbreviationStrategy (left/middle/right)              │
│  - FilepathStrategy                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Region Processing Engine                    │
│  - ShorteningRegion                                      │
│  - Priority-based region processor                       │
│  - Fallback to entire string                             │
└─────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: Width calculation, strategy selection, and region processing are independent
2. **Composability**: Strategies can be combined and configured flexibly
3. **Unicode-First**: All operations respect Unicode normalization and wide character semantics
4. **Fail-Safe**: Always produces valid output even with extreme constraints
5. **Leverage Existing Code**: Use TTK's battle-tested `wide_char_utils` for width calculations

## Components and Interfaces

### 1. Width Calculation Module

**Purpose**: Calculate accurate display width accounting for wide characters.

**Implementation**: Leverage TTK's existing `wide_char_utils` module.

```python
from ttk.wide_char_utils import get_display_width
import unicodedata

def calculate_display_width(text: str) -> int:
    """
    Calculate the display width of a string in terminal columns.
    
    Delegates to TTK's get_display_width() which handles:
    - Wide characters (CJK, emoji) count as 2 columns
    - Narrow characters count as 1 column
    - Combining characters count as 0 columns (via NFC normalization)
    
    Args:
        text: Input string (will be NFC normalized by get_display_width)
        
    Returns:
        Display width in columns
    """
    return get_display_width(text)

def normalize_unicode(text: str) -> str:
    """
    Normalize string to NFC form for consistent processing.
    
    Args:
        text: Input string
        
    Returns:
        NFC normalized string
    """
    return unicodedata.normalize('NFC', text)
```

**Implementation Notes**:
- Use TTK's `get_display_width()` which already handles wide character detection
- TTK's implementation uses `unicodedata.east_asian_width()` internally
- TTK's implementation includes NFC normalization and caching for performance
- Characters with width 'F' (Fullwidth) or 'W' (Wide) count as 2
- Characters with width 'Na' (Narrow), 'H' (Halfwidth), 'A' (Ambiguous) count as 1
- Combining marks are handled via NFC normalization

### 2. Shortening Region

**Purpose**: Define a region of the string that can be shortened with a priority.

```python
@dataclass
class ShorteningRegion:
    """Defines a region that can be shortened."""
    start: int  # Start index (inclusive)
    end: int    # End index (exclusive)
    priority: int  # Higher values shortened first
    strategy: str  # 'remove' or 'abbreviate'
    abbrev_position: str = 'right'  # 'left', 'middle', 'right'
    filepath_mode: bool = False
```

### 3. Strategy Classes

**Purpose**: Encapsulate different shortening algorithms.

```python
class ShorteningStrategy(Protocol):
    """Protocol for shortening strategies."""
    
    def shorten(self, text: str, target_width: int, region: ShorteningRegion) -> str:
        """
        Shorten text within the specified region to meet target width.
        
        Args:
            text: Full string to process
            target_width: Target display width
            region: Region to shorten
            
        Returns:
            Shortened string
        """
        pass

class RemovalStrategy:
    """Remove characters without adding ellipsis."""
    
    def shorten(self, text: str, target_width: int, region: ShorteningRegion) -> str:
        # Remove characters from region until width fits
        pass

class AbbreviationStrategy:
    """Replace removed content with ellipsis."""
    
    def shorten(self, text: str, target_width: int, region: ShorteningRegion) -> str:
        # Abbreviate based on position (left/middle/right)
        pass

class FilepathStrategy:
    """Abbreviate filesystem paths intelligently."""
    
    def shorten(self, text: str, target_width: int, region: ShorteningRegion) -> str:
        # Parse path, abbreviate directories before filename
        pass
```

### 4. Main API Functions

```python
def reduce_width(
    text: str,
    target_width: int,
    regions: Optional[List[ShorteningRegion]] = None,
    default_strategy: str = 'abbreviate',
    default_position: str = 'right'
) -> str:
    """
    Reduce string display width to fit within target.
    
    Args:
        text: Input string
        target_width: Maximum display width in columns
        regions: Optional list of regions to shorten with priorities
        default_strategy: Strategy when no regions specified ('remove' or 'abbreviate')
        default_position: Abbreviation position ('left', 'middle', 'right')
        
    Returns:
        Shortened string fitting within target_width
    """
    pass

def abbreviate_middle(text: str, target_width: int) -> str:
    """
    Convenience function: abbreviate with ellipsis in the middle.
    
    Example: "very_long_filename.txt" -> "very_lo…name.txt"
    """
    return reduce_width(text, target_width, default_position='middle')

def abbreviate_path(path: str, target_width: int) -> str:
    """
    Convenience function: abbreviate filesystem path intelligently.
    
    Example: "/home/user/documents/file.txt" -> "/home/…/file.txt"
    
    This creates a region covering the entire path with filepath_mode enabled.
    """
    region = ShorteningRegion(
        start=0,
        end=len(path),
        priority=1,
        strategy='abbreviate',
        abbrev_position='middle',
        filepath_mode=True
    )
    return reduce_width(path, target_width, regions=[region])
```

## Data Models

### Character Width Categories

Width calculation is handled by TTK's `wide_char_utils.get_display_width()`, which implements:

```python
# Based on Unicode East Asian Width property (from TTK)
# 'F' (Fullwidth) and 'W' (Wide) = 2 columns
# 'Na' (Narrow), 'H' (Halfwidth), 'A' (Ambiguous), 'N' (Neutral) = 1 column
# Combining marks handled via NFC normalization (zero width)
```

### Algorithm Flow

```
1. Normalize input to NFC
2. Calculate current display width
3. If width <= target, return original
4. If target <= 0, return empty string
5. If regions specified:
   a. Sort regions by priority (descending)
   b. For each region:
      - Apply strategy to region
      - Check if target met
      - If met, return result
6. If target not met or no regions:
   - Apply default strategy to entire string
   - Return result (even if still too wide)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I've identified the following consolidations:

- **Property 2.3** (ellipsis counted in width) is subsumed by **Property 1.1** (output width constraint) - if the output meets the width constraint, the ellipsis must be counted
- **Property 6.4** (preserve maximum content) is subsumed by **Property 1.1** - meeting the width constraint implies maximizing preserved content
- **Properties 4.1, 4.2, 4.3** (abbreviation positions) can be combined into a single comprehensive property about abbreviation position correctness
- **Properties 7.3 and 7.4** (combining characters and emoji width) can be combined into a single property about complex character width calculation

### Correctness Properties

Property 1: Output width constraint
*For any* string and positive target width, the display width of the shortened string should be less than or equal to the target width
**Validates: Requirements 1.1**

Property 2: Wide character width calculation
*For any* string containing wide characters (CJK, emoji), the calculated display width should count wide characters as 2 columns and narrow characters as 1 column
**Validates: Requirements 1.2**

Property 3: Idempotence for fitting strings
*For any* string whose display width is already less than or equal to the target width, the shortened string should be identical to the original string
**Validates: Requirements 1.3**

Property 4: Removal strategy excludes ellipsis
*For any* string shortened using the removal strategy, the output should not contain the ellipsis character "…"
**Validates: Requirements 2.1**

Property 5: Abbreviation strategy includes ellipsis
*For any* string shortened using the abbreviation strategy where shortening occurs, the output should contain the ellipsis character "…"
**Validates: Requirements 2.2**

Property 6: Mixed strategy support
*For any* string with multiple regions using different strategies (removal and abbreviation), each region should be processed according to its specified strategy
**Validates: Requirements 2.4**

Property 7: Priority ordering
*For any* string with multiple regions having different priorities, regions with higher priority values should be shortened before regions with lower priority values
**Validates: Requirements 3.1**

Property 8: Region boundary preservation
*For any* string with specified shortening regions, characters outside all region boundaries should remain unchanged in the output
**Validates: Requirements 3.3**

Property 9: Overlapping region handling
*For any* string with overlapping regions, the region with higher priority should be processed first, and subsequent regions should respect already-shortened content
**Validates: Requirements 3.4**

Property 10: Abbreviation position correctness
*For any* string shortened with abbreviation, the ellipsis should appear at the specified position (left = beginning, middle = center with content on both sides, right = end)
**Validates: Requirements 4.1, 4.2, 4.3**

Property 11: Middle abbreviation balance
*For any* string shortened with middle abbreviation, the number of preserved characters on the left and right of the ellipsis should differ by at most 1
**Validates: Requirements 4.4**

Property 12: Filepath directory priority
*For any* filesystem path shortened in filepath mode, directory components should be abbreviated before the filename component
**Validates: Requirements 5.3**

Property 13: Filepath separator preservation
*For any* filesystem path shortened in filepath mode, all path separators (/ or \) present in the original path should be present in the shortened path
**Validates: Requirements 5.4**

Property 14: Fallback to entire string
*For any* string where all specified regions have been fully shortened and the target width is not met, the entire string should be shortened using the default abbreviation strategy
**Validates: Requirements 6.1**

Property 15: Fallback position respect
*For any* string shortened via fallback to entire string, the abbreviation position specified in the default strategy should be used
**Validates: Requirements 6.2**

Property 16: Unicode NFC normalization
*For any* string processed by the reducer, the output should be in Unicode NFC (Canonical Decomposition followed by Canonical Composition) form
**Validates: Requirements 7.1, 7.2**

Property 17: Complex character width calculation
*For any* string containing combining characters or emoji with modifiers, the display width should correctly account for zero-width combining marks and multi-codepoint emoji sequences
**Validates: Requirements 7.3, 7.4**

## Error Handling

### Invalid Input Handling

1. **Negative or zero target width**: Return empty string
2. **None or empty string input**: Return empty string
3. **Invalid region boundaries** (start > end, negative indices): Ignore invalid regions, log warning
4. **Overlapping regions with equal priority**: Process in definition order
5. **Invalid strategy name**: Fall back to 'abbreviate' strategy, log warning
6. **Invalid abbreviation position**: Fall back to 'right' position, log warning

### Edge Cases

1. **String shorter than ellipsis**: Return ellipsis only when abbreviation is used
2. **Target width = 1**: Return first character (or ellipsis if abbreviating)
3. **All wide characters**: Handle correctly with width = 2 per character
4. **Mixed RTL/LTR text**: Process based on character positions, not visual order
5. **Malformed Unicode**: Normalize and process best-effort

### Logging

All error conditions should be logged using the TFM logging system:

```python
from tfm_log_manager import getLogger

logger = getLogger("StrWidth")

# Example usage
logger.warning(f"Invalid region boundaries: start={start}, end={end}")
logger.error(f"Unknown strategy '{strategy}', falling back to 'abbreviate'")
```

## Testing Strategy

### Dual Testing Approach

The implementation will use both unit tests and property-based tests:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs

### Property-Based Testing Configuration

- **Library**: Use `hypothesis` for Python property-based testing
- **Iterations**: Minimum 100 iterations per property test
- **Test tags**: Each property test must reference its design document property

Tag format: `# Feature: string-width-reduction, Property {number}: {property_text}`

### Test Organization

```
test/
  test_string_width_basic.py          # Unit tests for basic functionality
  test_string_width_properties.py     # Property-based tests
  test_string_width_unicode.py        # Unicode-specific tests
  test_string_width_filepath.py       # Filepath mode tests
  test_string_width_edge_cases.py     # Edge case tests
```

### Key Test Scenarios

**Unit Tests**:
- Empty string handling
- Single character strings
- Strings with only wide characters
- Strings with only narrow characters
- Mixed wide/narrow strings
- Strings with combining characters
- Emoji with modifiers
- Path abbreviation examples
- Region boundary cases
- Priority ordering examples

**Property Tests**:
- Width constraint (Property 1)
- Wide character calculation (Property 2)
- Idempotence (Property 3)
- Strategy correctness (Properties 4-6)
- Region processing (Properties 7-9)
- Abbreviation positions (Properties 10-11)
- Filepath mode (Properties 12-13)
- Fallback behavior (Properties 14-15)
- Unicode normalization (Property 16-17)

### Test Data Generation

For property-based tests, use Hypothesis strategies:

```python
from hypothesis import given, strategies as st

# Generate strings with various character types
@st.composite
def text_with_wide_chars(draw):
    """Generate strings containing wide and narrow characters."""
    narrow = draw(st.text(alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E)))
    wide = draw(st.text(alphabet=st.characters(min_codepoint=0x4E00, max_codepoint=0x9FFF)))
    return narrow + wide

# Generate valid regions
@st.composite
def shortening_regions(draw, text_length):
    """Generate valid shortening regions for a given text length."""
    start = draw(st.integers(min_value=0, max_value=text_length-1))
    end = draw(st.integers(min_value=start+1, max_value=text_length))
    priority = draw(st.integers(min_value=1, max_value=10))
    strategy = draw(st.sampled_from(['remove', 'abbreviate']))
    return ShorteningRegion(start, end, priority, strategy)
```

## Integration Points

### UI Components

The utility will be integrated into:

1. **QuickChoiceBar** (`src/tfm_quick_choice_bar.py`): Shorten option labels
2. **Status Bar** (`src/tfm_main.py`): Shorten path displays
3. **Dialogs** (`src/tfm_base_list_dialog.py`): Shorten list items
4. **File List** (`src/tfm_file_list_manager.py`): Shorten long filenames

### Usage Example

```python
from tfm_string_width import reduce_width, abbreviate_path

# In QuickChoiceBar
def format_option(self, label: str, available_width: int) -> str:
    return reduce_width(label, available_width, default_position='middle')

# In status bar
def format_path(self, path: str, available_width: int) -> str:
    return abbreviate_path(path, available_width)
```

## Performance Considerations

1. **Width Calculation Caching**: Cache width calculations for repeated strings
2. **Unicode Normalization**: Normalize once at entry point
3. **Region Sorting**: Sort regions once before processing
4. **Early Exit**: Return immediately if string already fits

Expected performance: O(n) where n is string length, with small constant factors for Unicode operations.
