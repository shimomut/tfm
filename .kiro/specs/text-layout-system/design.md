# Design Document: Text Layout System

## Overview

The Text Layout System is a comprehensive module for rendering text segments with intelligent width management, color attributes, and flexible shortening strategies in terminal applications. Unlike the existing `tfm_string_width.py` which only reduces text width, this system handles the complete pipeline: layout calculation, text shortening, and rendering to screen.

The system is designed to be independent of the legacy string width module and will eventually replace it. It provides a clean, object-oriented API that integrates seamlessly with TTK's rendering backend and wide character utilities.

## Architecture

The system follows a layered architecture:

```
┌─────────────────────────────────────────────────┐
│         Public API Layer                        │
│  (layout_text, TextSegment, create_spacer)      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         Layout Engine                           │
│  (calculate layout, apply priorities)           │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         Shortening Strategies                   │
│  (abbreviation, filepath, truncate, etc.)       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         Rendering Layer                         │
│  (TTK renderer.draw_text)                       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         Foundation                              │
│  (TTK wide_char_utils, Unicode normalization)   │
└─────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: Layout calculation, shortening, and rendering are distinct phases
2. **Strategy Pattern**: Shortening strategies are pluggable and extensible
3. **Priority-Based Processing**: Segments are shortened in priority order with restoration
4. **Wide Character Awareness**: All operations account for CJK and emoji characters
5. **Backend Agnostic**: Works with any TTK renderer implementation

## Components and Interfaces

### TextSegment Class Hierarchy

See "Data Models" section above for the complete class hierarchy. Each TextSegment subclass implements its own `shorten()` method that encapsulates the shortening logic for that strategy.

### Layout Engine Interface

The main layout and rendering function:

```python
def draw_text_segments(
    renderer: Renderer,
    row: int,
    col: int,
    segments: List[Union[TextSegment, SpacerSegment]],
    rendering_width: int,
    default_color: int = 0,
    default_attributes: int = 0
) -> None:
    """
    Calculate layout, shorten segments, and render text to screen.
    
    This is the primary entry point for the text layout system. It:
    1. Collapses spacers if shortening is needed
    2. Shortens segments by priority until target width is met
    3. Expands spacers if extra space is available
    4. Renders each segment with its color and attributes
    
    Args:
        renderer: TTK renderer instance
        row: Row position for rendering (0-based)
        col: Starting column position (0-based)
        segments: List of text/spacer segments to layout
        rendering_width: Target width in terminal columns
        default_color: Default color pair for segments without color
        default_attributes: Default attributes for segments without attributes
    """
    pass
```

## Data Models

### Internal Layout State

During layout calculation, the engine maintains:

```python
@dataclass
class LayoutState:
    """Internal state during layout calculation."""
    segments: List[Union[TextSegment, SpacerSegment]]
    current_widths: List[int]  # Current width of each segment
    original_widths: List[int]  # Original width of each segment (0 for spacers)
    total_width: int
    target_width: int
    spacer_indices: List[int]  # Indices of spacer segments
```

### Rendering Context

For rendering phase:

```python
@dataclass
class RenderContext:
    """Context for rendering segments."""
    renderer: Renderer
    row: int
    current_col: int  # Tracks position as we render
    default_color: int
    default_attributes: int
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Width Constraint Satisfaction

*For any* list of text segments and rendering width, after layout calculation, the total display width of all segments SHALL NOT exceed the rendering width.

**Validates: Requirements 6.6, 7.6**

### Property 2: Priority-Based Shortening Order

*For any* list of segments with priorities, when shortening is needed, segments SHALL be shortened in descending priority order (higher values first), and segments with equal priority SHALL be shortened in their definition order.

**Validates: Requirements 4.1, 4.2**

### Property 3: Priority-Based Restoration Order

*For any* layout where shortening occurred and extra space becomes available, segments SHALL be restored in ascending priority order (lower values first).

**Validates: Requirements 4.4**

### Property 4: Minimum Length Preservation

*For any* segment with a minimum length specified, after shortening, the segment SHALL contain at least min_length characters OR the maximum possible characters if min_length cannot be satisfied.

**Validates: Requirements 5.1, 5.2**

### Property 5: Spacer Collapse Before Shortening

*For any* layout where shortening is needed, all spacer segments SHALL be collapsed to zero width before any non-spacer segments are shortened.

**Validates: Requirements 6.5**

### Property 6: Spacer Equal Distribution

*For any* layout where total width is less than rendering width and spacers exist, the extra space SHALL be distributed equally among all spacer segments (with at most 1 column difference due to rounding).

**Validates: Requirements 6.2, 6.3**

### Property 7: No Padding Without Spacers

*For any* layout without spacer segments where total width is less than rendering width, no padding SHALL be added to any segment.

**Validates: Requirements 6.4**

### Property 8: Abbreviation Strategy Ellipsis Presence

*For any* segment using abbreviation strategy that is shortened, the resulting text SHALL contain exactly one ellipsis character, and the ellipsis SHALL appear at the start (left position), center (middle position), or end (right position) according to the abbrev_position setting.

**Validates: Requirements 2.1, 3.1, 3.2, 3.3**

### Property 9: Truncate Strategy No Ellipsis

*For any* segment using truncate strategy that is shortened, the resulting text SHALL NOT contain an ellipsis character.

**Validates: Requirements 2.3**

### Property 10: All-or-Nothing Behavior

*For any* segment with strategy "all-or-nothing", the segment SHALL either be kept in full OR removed entirely (empty string), never partially shortened.

**Validates: Requirements 2.4**

### Property 11: As-Is Strategy Preservation

*For any* segment with strategy "as-is", the segment's text SHALL never be modified regardless of width constraints.

**Validates: Requirements 2.5**

### Property 12: Filepath Abbreviation Directory Preservation

*For any* filesystem path using filepath-abbreviation strategy, when shortening is needed, entire directory components SHALL be removed (replaced with ellipsis) before the filename is abbreviated.

**Validates: Requirements 2.2**

### Property 13: Wide Character Boundary Preservation

*For any* text containing wide characters, when shortening at a boundary, if a wide character would be split, it SHALL be excluded entirely rather than partially included.

**Validates: Requirements 8.3**

### Property 14: Wide Character Width Accounting

*For any* text containing wide characters, the calculated display width SHALL count each wide character as 2 columns and each narrow character as 1 column.

**Validates: Requirements 8.2**

### Property 15: Color and Attribute Application

*For any* segment with a specified color pair or attributes, when rendered to a mock renderer, the renderer SHALL receive draw_text calls with those color and attribute values for that segment's text.

**Validates: Requirements 7.3, 7.4, 9.1, 9.2**

### Property 16: Default Color and Attribute Usage

*For any* segment without a specified color pair or attributes, when rendered, the segment SHALL use the default color and default attributes provided to the layout function.

**Validates: Requirements 9.3, 9.4**

### Property 17: Rendering Position Continuity

*For any* sequence of segments, each segment SHALL be rendered at a column position immediately following the previous segment (current_col + previous_segment_width).

**Validates: Requirements 7.5**

## Error Handling

### Input Validation

1. **Invalid Segment Configuration**
   - Invalid strategy names → Log warning, fall back to 'abbreviation'
   - Invalid abbreviation position → Log warning, fall back to 'right'
   - Negative min_length → Treat as 0
   - Invalid color_pair (< 0 or > 255) → Use default_color

2. **Invalid Layout Parameters**
   - Negative rendering_width → Treat as 0, render nothing
   - Empty segments list → Return immediately, render nothing
   - None renderer → Raise ValueError with clear message

3. **Wide Character Errors**
   - Unicode normalization failures → Log error, use original text
   - Width calculation errors → Fall back to character count

### Runtime Errors

1. **Renderer Failures**
   - draw_text exceptions → Log error, continue with next segment
   - Position out of bounds → Clip to valid range

2. **Strategy Failures**
   - Strategy.shorten() exceptions → Log error, use original text
   - Infinite loops in shortening → Timeout after max iterations

### Logging Strategy

All errors and warnings use TFM's unified logging system:

```python
from tfm_log_manager import getLogger

logger = getLogger("TextLayout")

# Error levels:
# ERROR: Failures that prevent correct rendering
# WARNING: Invalid configuration with fallback
# INFO: Normal operation milestones
# DEBUG: Detailed layout decisions
```

## Testing Strategy

### Unit Tests

Unit tests verify specific examples and edge cases:

1. **Segment Creation**
   - Default values are applied correctly
   - Invalid values are handled gracefully

2. **Strategy Implementations**
   - Each strategy produces expected output for known inputs
   - Edge cases (empty text, single character, all wide characters)
   - Boundary conditions (target_width = 0, 1, 2)

3. **Layout Calculation**
   - Spacer collapse and expansion
   - Priority ordering
   - Minimum length enforcement

4. **Rendering**
   - Correct positioning
   - Color and attribute application
   - Multi-segment layouts

### Property-Based Tests

Property tests verify universal properties across all inputs:

1. **Width Constraint (Property 1)**
   - Generate random segment lists and rendering widths
   - Verify total width never exceeds target

2. **Priority Ordering (Property 2)**
   - Generate segments with random priorities
   - Verify higher priority segments shortened first

3. **Minimum Length (Property 3)**
   - Generate segments with random min_length values
   - Verify segments never shortened below minimum

4. **Spacer Behavior (Properties 4, 5)**
   - Generate layouts with random spacer positions
   - Verify spacers collapse before shortening
   - Verify spacers expand when space available

5. **Strategy Correctness (Properties 6, 9, 10, 12)**
   - Generate random text with each strategy
   - Verify strategy-specific invariants hold

6. **Wide Character Handling (Property 7)**
   - Generate text with random wide characters
   - Verify boundaries never split wide characters

7. **Rendering Properties (Properties 8, 11)**
   - Generate random segment configurations
   - Verify colors/attributes applied correctly
   - Verify continuous positioning

### Test Configuration

- Minimum 100 iterations per property test
- Each test tagged with feature name and property number
- Example tag: `# Feature: text-layout-system, Property 1: Width Constraint Satisfaction`

### Integration Tests

1. **End-to-End Scenarios**
   - File list rendering with mixed content
   - Status bar with dynamic segments
   - Dialog prompts with long paths

2. **Backend Compatibility**
   - Test with curses backend
   - Test with CoreGraphics backend
   - Verify consistent behavior across backends

## Implementation Notes

### Performance Considerations

1. **Caching**: Use TTK's cached width calculation functions
2. **Early Exit**: Stop shortening once target width is met
3. **Lazy Evaluation**: Only calculate widths when needed
4. **Batch Rendering**: Minimize renderer calls

### Unicode Normalization

All text is normalized to NFC (Canonical Composition) before processing:
- Ensures consistent character representation
- Handles macOS NFD filenames correctly
- Enables accurate width calculation

### Spacer Distribution Algorithm

When distributing extra space among spacers:

```python
extra_space = rendering_width - total_width
num_spacers = len(spacer_indices)
base_space = extra_space // num_spacers
remainder = extra_space % num_spacers

# First 'remainder' spacers get base_space + 1
# Remaining spacers get base_space
```

### Priority Processing Algorithm

1. **Collapse Phase**: Set all spacers to zero width
2. **Shortening Phase**: Process priorities from high to low
   - For each priority level, shorten all segments at that level
   - Stop when target width is met
3. **Restoration Phase**: Process priorities from low to high
   - Try to restore content to segments
   - Stop when no more space available

## Dependencies

### External Dependencies

- `ttk.wide_char_utils`: For display width calculation
- `ttk.renderer`: For rendering interface
- `tfm_log_manager`: For unified logging

### Internal Dependencies

- `unicodedata`: For NFC normalization
- `dataclasses`: For data structures
- `typing`: For type hints
- `abc`: For abstract base classes

## Migration Path

The new system is designed to coexist with `tfm_string_width.py` during transition:

1. **Phase 1**: Implement new system independently
2. **Phase 2**: Migrate one component at a time (e.g., status bar)
3. **Phase 3**: Update all components to use new system
4. **Phase 4**: Remove `tfm_string_width.py`

Components can use both systems during migration without conflicts.
