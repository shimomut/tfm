# Search Mode to Isearch Mode Rename Summary

## Overview
Successfully renamed "Search mode" and related variables to "isearch mode" (incremental search mode) to clearly differentiate from the "search_dialog_mode".

## Changes Made

### Variable Names
- `search_mode` → `isearch_mode`
- `search_pattern` → `isearch_pattern`
- `search_matches` → `isearch_matches`
- `search_match_index` → `isearch_match_index`

### Function Names
- `enter_search_mode()` → `enter_isearch_mode()`
- `exit_search_mode()` → `exit_isearch_mode()`
- `handle_search_input()` → `handle_isearch_input()`
- `update_search_matches()` → `update_isearch_matches()`

### Display Text
- "Search mode" → "isearch mode"
- "Search:" prompt → "Isearch:" prompt
- "incremental search" → "isearch"
- "enter search mode" → "enter isearch mode"

### Files Modified

#### Core Files
- `src/tfm_main.py` - Main file manager implementation
- `src/tfm_text_viewer.py` - Text viewer implementation
- `src/tfm_const.py` - Constants file

#### Test Files
- `test/test_dialog_exclusivity.py`
- `test/test_dialog_fix_verification.py`
- `test/test_help_integration.py`
- `test/test_list_dialog_feature.py`
- `test/test_search.py`

#### Demo Files
- `demo_list_dialog.py`

## Key Benefits

1. **Clear Differentiation**: Now clearly distinguishes between:
   - `isearch_mode` - Incremental search within file lists/text
   - `search_dialog_mode` - Full search dialog interface

2. **Consistent Terminology**: All references now use "isearch" terminology consistently

3. **Maintained Functionality**: All existing functionality preserved, only naming changed

## Notes

- The functionality remains exactly the same
- All keyboard shortcuts (F key) remain unchanged
- All search behavior and features are preserved
- Documentation files in `doc/` folder were not modified to preserve historical context