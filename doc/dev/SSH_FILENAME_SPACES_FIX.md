# SSH/SFTP Filename Spaces Fix

## Problem

SFTP operations failed when filenames contained spaces or special characters. This affected all file operations including:
- Copying files to/from remote systems
- Listing directories
- Renaming files
- Creating/deleting files and directories

The root cause was that SFTP batch mode commands were not properly quoting paths, causing the SFTP client to misinterpret filenames with spaces as multiple arguments.

## Solution

Added a `_quote_path()` helper method to the `SSHConnection` class that:
1. Escapes any double quotes in the path by replacing `"` with `\"`
2. Wraps the entire path in double quotes

All SFTP command constructions now use this method to ensure paths are properly quoted.

## Implementation Details

### New Helper Method

```python
def _quote_path(self, path: str) -> str:
    """
    Quote a path for use in SFTP commands.
    
    SFTP batch mode requires paths with spaces or special characters to be quoted.
    This method adds double quotes around the path and escapes any internal quotes.
    
    Args:
        path: Path to quote
        
    Returns:
        Quoted path safe for SFTP commands
    """
    # Escape any double quotes in the path
    escaped_path = path.replace('"', '\\"')
    # Wrap in double quotes
    return f'"{escaped_path}"'
```

### Updated Operations

All SFTP command constructions were updated to use `_quote_path()`:

**Before:**
```python
commands = [f'get {remote_path} {tmp_path}']
commands = [f'put {tmp_path} {remote_path}']
commands = [f'ls -la {remote_path}']
commands = [f'rm {remote_path}']
commands = [f'mkdir {remote_path}']
commands = [f'rmdir {remote_path}']
commands = [f'rename {old_path} {new_path}']
```

**After:**
```python
commands = [f'get {self._quote_path(remote_path)} {self._quote_path(tmp_path)}']
commands = [f'put {self._quote_path(tmp_path)} {self._quote_path(remote_path)}']
commands = [f'ls -la {self._quote_path(remote_path)}']
commands = [f'rm {self._quote_path(remote_path)}']
commands = [f'mkdir {self._quote_path(remote_path)}']
commands = [f'rmdir {self._quote_path(remote_path)}']
commands = [f'rename {self._quote_path(old_path)} {self._quote_path(new_path)}']
```

## Affected Methods

The following methods in `SSHConnection` were updated:
- `list_directory()` - Lists directory contents
- `stat()` - Gets file/directory metadata
- `read_file()` - Downloads file contents
- `write_file()` - Uploads file contents
- `delete_file()` - Deletes a file
- `delete_directory()` - Deletes a directory
- `create_directory()` - Creates a directory
- `rename()` - Renames/moves a file or directory

## Testing

### Unit Tests

Created `test/test_ssh_filename_spaces.py` with comprehensive tests:
- Path quoting for simple paths
- Path quoting for paths with spaces
- Path quoting for paths with special characters (quotes, parentheses, brackets)
- File operations with spaces in filenames
- Directory operations with spaces in names

All tests verify that:
1. The `_quote_path()` method correctly quotes paths
2. SFTP commands are constructed with quoted paths
3. Operations don't raise exceptions due to unquoted paths

### Demo Script

Created `demo/demo_ssh_filename_spaces.py` that demonstrates:
- Path quoting for various filename patterns
- Examples of affected operations
- Implementation details

## Examples

### Filenames That Now Work

- `my file.txt` - Simple space
- `document (draft).txt` - Parentheses
- `file[1].txt` - Brackets
- `My Document "final".txt` - Quotes
- `path/with  multiple   spaces/file.txt` - Multiple spaces

### SFTP Command Examples

**Copying a file with spaces:**
```
Before: get /remote/my file.txt /tmp/tmpXXX
After:  get "/remote/my file.txt" "/tmp/tmpXXX"
```

**Listing a directory with spaces:**
```
Before: ls -la /remote/my directory
After:  ls -la "/remote/my directory"
```

**Renaming with spaces:**
```
Before: rename /remote/old file.txt /remote/new file.txt
After:  rename "/remote/old file.txt" "/remote/new file.txt"
```

## Related Files

- `src/tfm_ssh_connection.py` - Main implementation
- `test/test_ssh_filename_spaces.py` - Unit tests
- `demo/demo_ssh_filename_spaces.py` - Demo script

## References

- SFTP batch mode documentation: `man sftp`
- SSH connection implementation: `doc/dev/SSH_CONNECTION_SYSTEM.md`
