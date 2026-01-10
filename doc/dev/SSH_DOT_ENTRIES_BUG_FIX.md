# SSH Dot Entries Bug Fix

## Problem

When searching for `*.py` files in SSH directories using the Search Dialog, the search returned **0 results** even though Python files existed in the directory.

## Root Cause

The `list_directory()` method in `src/tfm_ssh_connection.py` was not correctly filtering out `.` (current directory) and `..` (parent directory) entries from the SFTP `ls -la` output.

### Why the Filter Failed

The original code tried to filter these entries by checking if lines ended with ` .` or ` ..`:

```python
# Original (BROKEN) code
if line.endswith(' .') or line.endswith(' ..'):
    continue
```

However, SFTP's `ls -la` output includes **full paths** in the filename field:

```
drwxrwxr-x  ? ubuntu ubuntu 4096 Oct 16 16:15 /home/ubuntu/projects/tfm/.
drwxrwxr-x  ? ubuntu ubuntu 4096 Jan  1 12:03 /home/ubuntu/projects/tfm/..
```

So the lines end with `/home/ubuntu/projects/tfm/.` and `/home/ubuntu/projects/tfm/..`, not ` .` and ` ..`.

### Impact

When `.` and `..` entries were not filtered:

1. `iterdir()` returned `.` and `..` as valid entries
2. `rglob()` recursively processed these entries
3. `.` points to the current directory, creating an **infinite loop**
4. All items in `rglob()` appeared to have `name='.'`
5. Pattern matching in search failed because all files looked like `.`
6. Search returned **0 results**

## Solution

Move the filter check to **after parsing** the ls line, where we can check the extracted basename:

```python
# Fixed code
entry = self._parse_ls_line(line)
if entry:
    # Skip . and .. entries (check after parsing)
    if entry['name'] in ('.', '..'):
        continue
    
    entries.append(entry)
```

The `_parse_ls_line()` method extracts the basename using `posixpath.basename()`, which correctly returns `.` or `..` from the full path.

## Changes Made

**File**: `src/tfm_ssh_connection.py`  
**Method**: `SSHConnection.list_directory()` (around line 550-570)

**Change**:
- Removed: `if line.endswith(' .') or line.endswith(' ..'):` check before parsing
- Added: `if entry['name'] in ('.', '..'):` check after parsing

## Verification

Created comprehensive test suite in `temp/test_ssh_dot_entries_fix.py`:

### Test Results

```
✓ iterdir correctly excludes . and .. entries
  Found 17 valid entries

✓ rglob returns actual files
  First 10 items: ['.git', 'FETCH_HEAD', 'HEAD', ...]

✓ Search for *.py files works correctly
  Found 10 .py files
  Examples: ['__init__.py', 'demo_archive_operations.py', ...]

✓ rglob completes without infinite loop
  Iterated through 100 items
  Found 89 unique names
```

### Manual Testing

Searching for `*.py` in `ssh://Ec2-Dev-Ubuntu24/home/ubuntu/projects/tfm` now correctly returns Python files:

```
MATCH: __init__.py
MATCH: demo_archive_operations.py
MATCH: demo_base_list_dialog_refactoring.py
MATCH: demo_color_debugging.py
...
Total *.py files found: 20+
```

## Impact Assessment

### Fixed Issues

1. ✅ Search for `*.py` files now returns results
2. ✅ `rglob()` no longer enters infinite loops
3. ✅ `iterdir()` correctly excludes `.` and `..` entries
4. ✅ All file names display correctly (not all showing as `.`)

### No Regressions

- Cache behavior unchanged (still caches stat info for each entry)
- Performance unchanged (same number of network calls)
- API unchanged (no public interface changes)
- Backward compatible (only fixes broken behavior)

## Related Code

- `src/tfm_ssh_connection.py`: `list_directory()` method
- `src/tfm_ssh_connection.py`: `_parse_ls_line()` method
- `src/tfm_ssh.py`: `iterdir()` method
- `src/tfm_ssh.py`: `rglob()` method
- `src/tfm_search_dialog.py`: `_search_worker()` method

## Lessons Learned

1. **Parse before filtering**: When dealing with structured output (like ls), parse the structure first, then filter on the parsed data
2. **Test with real data**: The bug only appeared with actual SFTP output, not with mocked data
3. **Check assumptions**: The assumption that ls output would have simple filenames was incorrect
4. **Infinite loops are subtle**: The `.` entry caused an infinite loop that manifested as "all files named `.`" rather than an obvious hang
