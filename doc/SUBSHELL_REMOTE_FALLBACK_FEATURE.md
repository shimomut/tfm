# TFM Subshell Remote Directory Fallback Feature

## Overview

This feature ensures that TFM's subshell and external program execution work reliably when browsing remote directories (such as S3 buckets). When the current pane is browsing a remote directory that cannot be used as a shell working directory, TFM automatically falls back to using TFM's own working directory.

## Problem Solved

Previously, when users tried to open a subshell or run external programs while browsing remote directories (like S3), the operation would fail because:

1. Remote paths (e.g., `s3://bucket/folder/`) cannot be used as shell working directories
2. `os.chdir()` would fail with remote paths
3. This made subshell and external programs unusable when browsing remote storage

## Solution

The feature implements intelligent working directory selection:

- **Remote directories**: Use TFM's working directory (`os.getcwd()`) as fallback
- **Local directories**: Use the pane's directory normally
- **Environment variables**: Always contain actual pane paths regardless of working directory

## Implementation Details

### Core Logic

```python
# Determine working directory for subshell/external programs
if current_pane['path'].is_remote():
    working_dir = os.getcwd()  # TFM's working directory
    print(f"Note: Current pane is browsing remote directory: {current_pane['path']}")
    print(f"Working directory set to TFM's directory: {working_dir}")
else:
    working_dir = str(current_pane['path'])  # Use pane directory normally

# Change to the selected working directory
os.chdir(working_dir)
```

### Remote Path Detection

The feature uses the `is_remote()` method from the TFM Path system:

```python
# Examples of remote path detection
s3_path = Path('s3://my-bucket/folder/')
local_path = Path('/home/user/documents')

s3_path.is_remote()    # Returns True
local_path.is_remote() # Returns False
```

### Affected Components

1. **Subshell Mode** (`enter_subshell_mode`)
   - Falls back to TFM working directory for remote paths
   - Informs user about the fallback behavior
   - Environment variables still contain remote paths

2. **External Programs** (`execute_external_program`)
   - Same fallback behavior for consistency
   - External programs can still access remote paths via `TFM_*` variables

## User Experience

### When Browsing Local Directories

```bash
# Normal behavior - no changes
TFM Sub-shell Mode
==================================================
TFM_THIS_DIR:      /home/user/documents
Working Directory: /home/user/documents
==================================================
```

### When Browsing Remote Directories

```bash
# Fallback behavior with user notification
TFM Sub-shell Mode
==================================================
TFM_THIS_DIR:      s3://my-bucket/folder/
Working Directory: /home/user/tfm
==================================================
Note: Current pane is browsing remote directory: s3://my-bucket/folder/
Subshell working directory set to TFM's directory: /home/user/tfm
```

## Environment Variables

All TFM environment variables are set correctly regardless of the working directory fallback:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `TFM_THIS_DIR` | Current pane directory | `s3://my-bucket/folder/` |
| `TFM_OTHER_DIR` | Other pane directory | `/home/user/local` |
| `TFM_LEFT_DIR` | Left pane directory | `/home/user/local` |
| `TFM_RIGHT_DIR` | Right pane directory | `s3://my-bucket/folder/` |
| `TFM_THIS_SELECTED` | Selected files in current pane | `"file1.txt" "file2.txt"` |
| `TFM_ACTIVE` | TFM indicator | `1` |

## Use Cases

### 1. S3 File Management

```bash
# While browsing s3://my-bucket/logs/ in TFM
$ aws s3 ls $TFM_THIS_DIR
$ aws s3 cp $TFM_THIS_DIR/error.log .
$ aws s3 sync $TFM_THIS_DIR ./backup/
```

### 2. Remote Development Workflow

```bash
# While browsing s3://code-bucket/projects/
$ git clone https://github.com/user/repo.git
$ aws s3 cp $TFM_THIS_DIR/config.json ./repo/
$ cd repo && make build
```

### 3. Data Processing

```bash
# While browsing s3://data-bucket/datasets/
$ python analyze.py --input $TFM_THIS_DIR
$ aws s3 cp results.csv $TFM_THIS_DIR/processed/
```

## Benefits

1. **Reliability**: Subshell and external programs work consistently
2. **Transparency**: Users are informed when fallback occurs
3. **Functionality**: No loss of remote directory access via environment variables
4. **Consistency**: Same behavior for subshell and external programs
5. **Flexibility**: Works with any remote storage type (S3, SCP, FTP, etc.)

## Technical Implementation

### Files Modified

- `src/tfm_external_programs.py`: Core implementation in both `enter_subshell_mode` and `execute_external_program` methods

### Key Changes

1. **Working Directory Selection Logic**:
   ```python
   if current_pane['path'].is_remote():
       working_dir = os.getcwd()
   else:
       working_dir = str(current_pane['path'])
   ```

2. **User Notification**:
   - Inform users when fallback occurs
   - Show both remote path and fallback directory

3. **Consistent Behavior**:
   - Applied to both subshell and external programs
   - Environment variables always reflect actual paths

### Testing

The feature includes comprehensive tests:

- `test/test_subshell_remote_fallback.py`: Full integration tests
- `test/test_subshell_remote_simple.py`: Core logic tests
- `demo/demo_subshell_remote_fallback.py`: Interactive demonstration

## Backward Compatibility

This feature is fully backward compatible:

- **Local directories**: Behavior unchanged
- **Existing scripts**: Continue to work normally
- **Environment variables**: Same format and content
- **External programs**: No changes required

## Future Enhancements

Potential improvements for future versions:

1. **Configurable Fallback Directory**: Allow users to specify custom fallback directory
2. **Remote Working Directory Emulation**: Create temporary local mirror of remote directory
3. **Enhanced Notifications**: More detailed information about remote storage capabilities
4. **Integration with Cloud CLIs**: Automatic detection and setup of cloud CLI tools

## Configuration

No configuration is required. The feature works automatically based on path type detection.

## Troubleshooting

### Common Issues

1. **"Permission denied" errors**: Ensure TFM has write access to its working directory
2. **Environment variables not set**: Verify external programs are launched through TFM
3. **Remote paths not accessible**: Check cloud CLI configuration (AWS CLI, etc.)

### Debug Information

When fallback occurs, TFM provides clear information:
- Current remote directory being browsed
- Fallback working directory being used
- Reason for the fallback

## Related Features

- [Subshell Feature](SUBSHELL_FEATURE.md): Core subshell functionality
- [External Programs](EXTERNAL_PROGRAMS_FEATURE.md): External program execution
- [S3 Support](S3_SUPPORT_FEATURE.md): S3 storage integration
- [Path System](PATH_SYSTEM_FEATURE.md): TFM's unified path handling