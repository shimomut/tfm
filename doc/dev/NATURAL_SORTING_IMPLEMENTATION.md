# Natural Sorting Implementation

## Overview

This document describes the implementation of natural sorting (alphanumeric sorting) in TFM's file list manager.

## Implementation Details

### Core Algorithm

Natural sorting is implemented in `src/tfm_file_list_manager.py` using a key generation function that splits filenames into alternating text and numeric parts.

### Key Components

#### 1. Natural Sort Key Function

```python
def _natural_sort_key(self, text):
    """
    Generate a natural sort key that handles numeric parts as numbers.
    
    Converts "Test10.txt" into ['test', 10, '.txt'] so it sorts numerically.
    """
    import re
    
    def convert(part):
        """Convert numeric strings to integers, leave others as lowercase strings"""
        return int(part) if part.isdigit() else part.lower()
    
    # Split on digit sequences, keeping the digits
    parts = re.split(r'(\d+)', text)
    return [convert(part) for part in parts]
```

**How it works:**
1. Uses regex `r'(\d+)'` to split on digit sequences while preserving them
2. Converts numeric strings to integers for numeric comparison
3. Converts text strings to lowercase for case-insensitive comparison
4. Returns a list that Python's `sorted()` can compare element-by-element

**Example transformation:**
- Input: `"Test10.txt"`
- After split: `['Test', '10', '.txt']`
- After convert: `['test', 10, '.txt']`
- Result: Sorts numerically by the integer 10, not the string "10"

#### 2. Integration with sort_entries()

The natural sort key is used in the `sort_entries()` method when sorting by name:

```python
def get_sort_key(entry):
    """Generate sort key for an entry"""
    try:
        if sort_mode == 'size':
            return entry.stat().st_size if entry.is_file() else 0
        elif sort_mode == 'date':
            return entry.stat().st_mtime
        # ... other modes ...
        else:  # name (default)
            return self._natural_sort_key(entry.name)
    except (OSError, PermissionError):
        # If we can't get file info, use name as fallback
        return self._natural_sort_key(entry.name)
```

### Algorithm Complexity

- **Time complexity**: O(n log n) for sorting, where n is the number of files
- **Space complexity**: O(n) for storing sort keys
- **Key generation**: O(m) where m is the length of the filename

The regex split operation is efficient and only performed once per filename during sorting.

### Edge Cases Handled

1. **No numeric parts**: Falls back to standard string comparison
   - `"abc.txt"` → `['abc.txt']`

2. **Only numeric parts**: Compares as integers
   - `"123"` → `[123]`

3. **Leading zeros**: Treated as part of the number
   - `"001"` → `[1]`
   - `"010"` → `[10]`

4. **Multiple numeric sequences**: Each is compared independently
   - `"file1-part10"` → `['file', 1, '-part', 10]`

5. **Empty strings**: Handled gracefully by regex split

6. **Special characters**: Treated as text, sorted lexicographically

### Testing

Comprehensive tests are in `test/test_natural_sorting.py`:

- Basic numeric sorting
- Mixed text and numbers
- Case insensitivity
- Files without numbers
- Files with only numbers
- Directory vs file sorting
- Reverse sorting
- Leading zeros

Run tests:
```bash
PYTHONPATH=.:src:ttk pytest test/test_natural_sorting.py -v
```

### Performance Considerations

1. **Regex compilation**: The regex pattern is compiled once per call, which is acceptable since sorting happens infrequently

2. **Memory usage**: Each filename generates a list of parts, but this is temporary and garbage collected after sorting

3. **Caching**: Sort keys are not cached since file lists change frequently and sorting is fast enough

### Comparison with Other Approaches

#### Alternative 1: natsort library
- **Pros**: Well-tested, handles edge cases
- **Cons**: External dependency, overkill for our needs
- **Decision**: Implemented custom solution to avoid dependency

#### Alternative 2: locale.strxfrm with ICU
- **Pros**: System-native sorting
- **Cons**: Platform-dependent, complex setup
- **Decision**: Custom solution is more portable

#### Alternative 3: Manual character-by-character comparison
- **Pros**: Fine-grained control
- **Cons**: Complex, error-prone, slower
- **Decision**: Regex-based approach is cleaner

### Future Enhancements

Potential improvements (not currently planned):

1. **Locale-aware sorting**: Handle non-ASCII characters better
2. **Version number sorting**: Special handling for semantic versions (1.2.3)
3. **Date sorting in filenames**: Recognize and sort date patterns
4. **Configurable behavior**: Allow users to toggle natural sorting

### Related Files

- **Implementation**: `src/tfm_file_list_manager.py`
- **Tests**: `test/test_natural_sorting.py`
- **Demo**: `demo/demo_natural_sorting.py`
- **User documentation**: `doc/NATURAL_SORTING_FEATURE.md`

### References

- Python `re.split()` documentation
- Natural sort order (Wikipedia)
- Alphanumeric sorting algorithms
