# BeyondCompare Wrapper Script Rename

## Summary

The BeyondCompare directory comparison wrapper script has been renamed for better clarity:

**Old name**: `bcompare_wrapper.sh`  
**New name**: `bcompare_dirs_wrapper.sh`

This change makes it clear that this script is specifically for comparing directories, distinguishing it from the file comparison script `bcompare_files_wrapper.sh`.

## Files Updated

### Scripts
- ✅ Renamed `bcompare_wrapper.sh` → `bcompare_dirs_wrapper.sh`
- ✅ Maintained executable permissions

### Configuration Files
- ✅ `src/_config.py` - Updated template configuration
- ✅ `~/.tfm/config.py` - Updated user configuration

### Test Scripts
- ✅ `test_bcompare.py` - Updated to reference new filename

### Documentation
- ✅ `BEYONDCOMPARE_INTEGRATION.md` - Updated all references
- ✅ `EXTERNAL_PROGRAMS_OPTIONS.md` - Updated example

## Verification

All tests pass with the new filename:
- ✅ Configuration parsing works correctly
- ✅ Wrapper scripts are found and executable
- ✅ Options (auto_return) are properly configured
- ✅ Both directory and file comparison scripts are working

## Current BeyondCompare Scripts

1. **`bcompare_dirs_wrapper.sh`** - Compares left and right pane directories
2. **`bcompare_files_wrapper.sh`** - Compares selected files from both panes

Both scripts are configured with `auto_return: True` for seamless workflow integration.

## No Action Required

The rename has been completed and all references have been updated. Users can continue using TFM's external programs feature without any changes to their workflow.