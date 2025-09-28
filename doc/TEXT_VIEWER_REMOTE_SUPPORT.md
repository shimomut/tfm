# TextViewer Remote File Support

## Overview

The TextViewer component has been enhanced to support remote files (such as S3 objects) using the tfm_path abstraction mechanism. This allows users to view text files stored in remote storage systems with the same interface and functionality as local files.

## Key Features

### 1. Unified File Access
- Uses tfm_path's abstraction layer for both local and remote file operations
- Transparent handling of different storage backends (local filesystem, S3, etc.)
- Consistent API regardless of file location

### 2. Remote File Detection
- Automatically detects remote files based on URI scheme (e.g., `s3://`)
- Shows remote scheme in the header (e.g., "S3: filename.txt")
- Maintains all existing functionality for local files

### 3. Enhanced Error Handling
- Specific exception handling for different error types:
  - `FileNotFoundError` for missing files
  - `PermissionError` for access denied
  - `OSError` for general I/O errors
- Informative error messages displayed in the viewer
- Graceful fallback for unsupported file types

### 4. Binary File Detection
- Works with remote files using tfm_path's `read_bytes()` method
- Detects binary files by checking for null bytes
- Supports multiple encoding fallbacks for text files

## Implementation Details

### File Loading Process

1. **Text Reading**: Uses `file_path.read_text()` with multiple encoding attempts:
   - UTF-8 (primary)
   - Latin-1 (fallback)
   - CP1252 (Windows fallback)

2. **Binary Detection**: If text reading fails, attempts `file_path.read_bytes()`:
   - Checks for null bytes to identify binary files
   - Uses Latin-1 as final fallback for edge cases

3. **Error Handling**: Specific exception types are caught and handled:
   ```python
   except FileNotFoundError:
       # File doesn't exist
   except PermissionError:
       # Access denied
   except OSError as e:
       # General I/O error
   ```

### Header Display

Remote files show their storage scheme in the header:
- Local files: `File: example.txt`
- S3 files: `S3: example.txt`
- Other remote: `SCHEME: example.txt`

### File Size Calculation

Uses tfm_path's `stat()` method which works for both local and remote files:
```python
file_size = self.file_path.stat().st_size
```

## Usage Examples

### Viewing Local Files
```python
from tfm_path import Path
from tfm_text_viewer import view_text_file

# Local file
local_path = Path('/home/user/document.txt')
view_text_file(stdscr, local_path)
```

### Viewing S3 Files
```python
# S3 file
s3_path = Path('s3://my-bucket/document.txt')
view_text_file(stdscr, s3_path)
```

### Text File Detection
```python
from tfm_text_viewer import is_text_file

# Works for both local and remote files
if is_text_file(file_path):
    view_text_file(stdscr, file_path)
```

## Supported Remote Storage

Currently supports any storage backend implemented in the tfm_path system:
- **S3**: AWS S3 buckets (`s3://bucket/key`)
- **Extensible**: New storage backends can be added by implementing `PathImpl`

## Error Scenarios

### File Not Found
```
File not found: s3://bucket/missing.txt
```

### Permission Denied
```
Permission denied: s3://private-bucket/restricted.txt
```

### Binary File
```
[Binary file - cannot display as text]
```

### Network/Connection Issues
```
Error reading file: Connection timeout
```

## Performance Considerations

### Caching
- S3 implementation includes built-in caching for metadata and content
- Reduces API calls for repeated operations
- Configurable TTL (Time To Live) settings

### Large Files
- Binary detection only reads first 1024 bytes
- Efficient for large remote files
- Streaming support through tfm_path abstraction

### Network Efficiency
- Uses tfm_path's optimized remote operations
- Minimal data transfer for file detection
- Proper error handling for network issues

## Testing

### Unit Tests
- `test/test_text_viewer_remote.py` - Comprehensive test suite
- Tests local and remote file scenarios
- Mock-based testing for S3 operations
- Error handling verification

### Demo Script
- `demo/demo_text_viewer_remote.py` - Interactive demonstration
- Shows local vs remote file handling
- Error scenario examples
- Binary file detection examples

## Integration with TFM

### File Manager Integration
The TextViewer is automatically used when viewing text files in TFM:
- Press `Enter` or `Space` on a text file to view
- Works seamlessly with both local and remote files
- Same keyboard shortcuts and interface

### Configuration
No additional configuration required:
- Remote support is automatic when tfm_path detects remote URIs
- Uses existing TFM color schemes and settings
- Inherits syntax highlighting preferences

## Future Enhancements

### Planned Features
1. **Streaming Support**: For very large remote files
2. **Progress Indicators**: For slow remote file loading
3. **Caching Controls**: User-configurable cache settings
4. **Additional Storage**: Support for more remote storage types

### Extension Points
- New storage backends can be added to tfm_path
- TextViewer automatically supports new backends
- No changes required to TextViewer code

## Troubleshooting

### Common Issues

1. **S3 Credentials**: Ensure AWS credentials are configured
2. **Network Connectivity**: Check internet connection for remote files
3. **Permissions**: Verify read access to remote resources
4. **File Size**: Very large files may take time to load

### Debug Information
Enable debug logging to see detailed error information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Conclusion

The TextViewer remote file support provides a seamless experience for viewing text files regardless of their storage location. By leveraging the tfm_path abstraction, it maintains consistency while adding powerful remote capabilities.