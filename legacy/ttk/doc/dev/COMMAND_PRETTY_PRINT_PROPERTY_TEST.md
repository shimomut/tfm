# Command Pretty-Print Property Test Implementation

## Overview

This document describes the property-based test implementation for command pretty-printing functionality in the TTK library. The test validates **Property 11: Pretty-print completeness** from the desktop-app-mode specification.

## Property Definition

**Property 11: Pretty-print completeness**

*For any* rendering command, pretty-printing should produce a non-empty string representation without raising exceptions.

**Validates:** Requirements 13.4

## Test Implementation

### Location

`ttk/test/test_pbt_command_pretty_print.py`

### Testing Framework

The property tests use Python's `hypothesis` library for property-based testing, which automatically generates hundreds of test cases with random valid inputs.

### Test Strategy

The test suite validates that `pretty_print_command()` handles all command types correctly by:

1. **Generating random valid command parameters** using hypothesis strategies
2. **Creating command instances** with the generated parameters
3. **Calling pretty_print_command()** on each command
4. **Verifying the output** meets the property requirements:
   - Returns a string
   - String is non-empty
   - String contains the command type identifier
   - No exceptions are raised

### Hypothesis Strategies

The test file defines several reusable strategies for generating valid test data:

```python
# RGB color tuples (0-255 for each component)
rgb_strategy = st.tuples(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
)

# Coordinates (0-1000)
coord_strategy = st.integers(min_value=0, max_value=1000)

# Dimensions (1-1000)
dimension_strategy = st.integers(min_value=1, max_value=1000)

# Color pair IDs (0-255)
color_pair_strategy = st.integers(min_value=0, max_value=255)

# Text attributes (0-7, representing combinations of BOLD, UNDERLINE, REVERSE)
attribute_strategy = st.integers(min_value=0, max_value=7)

# Text strings (1-100 characters)
text_strategy = st.text(min_size=1, max_size=100)

# Single printable characters
char_strategy = st.characters(min_codepoint=32, max_codepoint=126)
```

### Test Coverage

The test suite includes property tests for all 11 command types:

1. **DrawTextCommand** - Text rendering with color and attributes
2. **DrawRectCommand** - Rectangle drawing (filled and outlined)
3. **DrawHLineCommand** - Horizontal line drawing
4. **DrawVLineCommand** - Vertical line drawing
5. **ClearCommand** - Full window clearing
6. **ClearRegionCommand** - Partial region clearing
7. **RefreshCommand** - Full window refresh
8. **RefreshRegionCommand** - Partial region refresh
9. **InitColorPairCommand** - Color pair initialization
10. **SetCursorVisibilityCommand** - Cursor visibility control
11. **MoveCursorCommand** - Cursor positioning

Additionally, there's a test for serialized command dictionaries to ensure the function handles both dataclass instances and dictionary representations.

### Example Test

```python
@given(
    row=coord_strategy,
    col=coord_strategy,
    text=text_strategy,
    color_pair=color_pair_strategy,
    attributes=attribute_strategy,
)
def test_pretty_print_draw_text_command(row, col, text, color_pair, attributes):
    """
    Property: Pretty-printing DrawTextCommand produces non-empty string without exceptions.
    """
    cmd = DrawTextCommand(
        row=row, col=col, text=text, color_pair=color_pair, attributes=attributes
    )
    result = pretty_print_command(cmd)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "draw_text" in result
```

This test:
- Generates random valid parameters for a DrawTextCommand
- Creates the command instance
- Pretty-prints it
- Verifies the output is a non-empty string containing "draw_text"

### Test Execution

Run the property tests with:

```bash
python -m pytest ttk/test/test_pbt_command_pretty_print.py -v
```

By default, hypothesis runs 100 examples per test. To run more examples:

```bash
python -m pytest ttk/test/test_pbt_command_pretty_print.py -v --hypothesis-seed=random
```

### Expected Output Format

The tests verify that pretty-printed commands contain the command type identifier. For example:

```
draw_text:
  attributes: 0
  col: 0
  color_pair: 0
  row: 0
  text: "Hello"
```

The test checks for "draw_text" in the output, not the class name "DrawTextCommand".

## Property Validation

### What the Property Guarantees

This property test guarantees that:

1. **Robustness**: Pretty-printing never crashes, regardless of input values
2. **Output validity**: Always produces a non-empty string
3. **Identifiability**: Output contains the command type for debugging
4. **Completeness**: All command types are supported

### What the Property Does NOT Guarantee

The property test does NOT validate:

- **Exact formatting**: The specific layout or indentation of the output
- **Parameter completeness**: Whether all parameters are included in the output
- **Human readability**: Whether the output is actually easy to read
- **Consistency**: Whether the same command always produces identical output

These aspects are covered by the unit tests in `test_command_pretty_print.py`.

## Integration with Requirements

This property test directly validates **Requirement 13.4**:

> WHEN pretty-printing commands THEN the system SHALL format them in a human-readable way for debugging

The property ensures that:
- Commands can be pretty-printed without errors (robustness)
- Output is non-empty (produces actual output)
- Output identifies the command type (useful for debugging)

## Relationship to Other Tests

### Unit Tests

`test_command_pretty_print.py` provides detailed unit tests that verify:
- Specific formatting details
- Parameter inclusion and ordering
- Edge cases and special values
- Exact output format

### Property Tests

`test_pbt_command_pretty_print.py` (this file) provides broad coverage that verifies:
- Robustness across all valid inputs
- No crashes or exceptions
- Basic output validity

Both test suites are complementary and necessary for complete validation.

## Maintenance Notes

### Adding New Command Types

When adding a new command type:

1. Add the command import to the test file
2. Create a hypothesis strategy for any new parameter types
3. Add a new property test function following the existing pattern
4. Verify the test passes with the new command type

### Modifying Command Parameters

When modifying command parameters:

1. Update the hypothesis strategy if parameter constraints change
2. Update the test function signature to match new parameters
3. Verify the property still holds with the modified parameters

### Debugging Test Failures

If a property test fails:

1. **Check the falsifying example** - Hypothesis will show the specific input that caused the failure
2. **Reproduce manually** - Create a unit test with the failing input
3. **Fix the implementation** - Update `pretty_print_command()` to handle the case
4. **Verify the fix** - Run the property test again to ensure it passes

Example falsifying output:

```
Falsifying example: test_pretty_print_draw_text_command(
    row=0,
    col=0,
    text='0',
    color_pair=0,
    attributes=0,
)
```

This shows exactly which input values caused the failure.

## Performance Considerations

Property-based tests run many examples (default 100 per test), so they take longer than unit tests:

- **Unit tests**: ~0.1 seconds
- **Property tests**: ~1-2 seconds

This is acceptable for the comprehensive coverage provided. If test time becomes an issue, consider:

1. Reducing the number of examples for specific tests
2. Running property tests separately from unit tests
3. Using hypothesis profiles for different test scenarios

## Conclusion

The command pretty-print property test provides robust validation that the pretty-printing functionality works correctly across all valid inputs. Combined with the unit tests, this ensures the implementation meets Requirement 13.4 and provides reliable debugging output for all command types.
