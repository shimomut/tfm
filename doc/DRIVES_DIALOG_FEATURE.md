# TFM Drives Dialog Feature

## Overview

The Drives Dialog is a new TFM component that provides a unified interface for selecting and navigating to different storage locations, including local filesystem directories and remote S3 buckets. This feature enhances TFM's navigation capabilities by offering quick access to commonly used storage locations.

## Features

### Storage Types Supported

1. **Local Filesystem**
   - Home directory
   - Root directory
   - Current working directory
   - Common system directories (Documents, Downloads, Desktop, etc.)
   - Applications directory (macOS)
   - System directories (/usr/local, /opt, /tmp)

2. **AWS S3 Storage**
   - All accessible S3 buckets
   - Automatic bucket discovery using AWS credentials
   - Graceful handling of credential issues
   - Error reporting for inaccessible buckets

### User Interface

- **Dialog Layout**: Clean, centered dialog with consistent TFM styling
- **Visual Indicators**: 
  - 🏠 Home directory icon
  - 📁 Local directory icon  
  - ☁️ S3 bucket icon
  - 💾 Generic storage icon
- **Real-time Filtering**: Type to filter drives by name, path, or description
- **Progress Animation**: Animated loading indicator while scanning S3 buckets
- **Status Information**: Shows count of local vs S3 drives

### Navigation Controls

| Key | Action |
|-----|--------|
| `↑/↓` | Navigate up/down through drives |
| `Page Up/Down` | Navigate by pages |
| `Home/End` | Jump to first/last drive |
| `Type` | Filter drives by text |
| `Enter` | Select and navigate to drive |
| `ESC` | Cancel and close dialog |

## Technical Implementation

### Architecture

The Drives Dialog follows TFM's modular dialog architecture:

- **`DrivesDialog`**: Main dialog class extending `BaseListDialog`
- **`DriveEntry`**: Data class representing individual storage locations
- **`DrivesDialogHelpers`**: Static helper methods for navigation integration

### Key Components

1. **Threading Support**
   - S3 bucket scanning runs in background thread
   - Thread-safe access to drive lists
   - Cancellable operations for responsive UI

2. **Error Handling**
   - Graceful handling of missing AWS credentials
   - Network error recovery for S3 operations
   - Permission error handling for local directories

3. **Performance Optimization**
   - Lazy loading of S3 buckets
   - Efficient filtering algorithms
   - Minimal memory footprint

### Integration Points

- **Main TFM Application**: Integrated into main input handling loop
- **Pane Manager**: Updates focused pane path when drive is selected
- **Configuration**: Key bindings configurable in `_config.py`
- **State Management**: Preserves selection during filtering

## Configuration

### Key Bindings

Default key bindings in `src/_config.py`:

```python
'drives_dialog': ['d', 'D'],  # Show drives/storage selection dialog
```

### Customization Options

The drives dialog respects existing TFM configuration:
- Color scheme settings
- Animation preferences
- Dialog sizing ratios

## Usage Examples

### Basic Usage

1. Press `d` or `D` to open the drives dialog
2. Use arrow keys to navigate through available drives
3. Type to filter drives (e.g., type "s3" to show only S3 buckets)
4. Press `Enter` to navigate to selected drive
5. Press `ESC` to cancel

### Filtering Examples

- Type "home" → Shows home directory and related paths
- Type "s3" → Shows only S3 buckets
- Type "doc" → Shows Documents directory and S3 buckets with "doc" in name
- Type "tmp" → Shows temporary directories

### S3 Integration

When AWS credentials are configured:
- All accessible S3 buckets are automatically discovered
- Bucket creation dates are shown in descriptions
- Navigation to S3 buckets enables S3 file operations

When AWS credentials are not configured:
- Placeholder entry shows "S3 (No Credentials)"
- Instructions for configuring AWS credentials

## Error Handling

### Local Filesystem Errors

- **Permission Denied**: Directories are skipped silently
- **Path Not Found**: Stale entries are filtered out
- **Access Errors**: Graceful fallback to available directories

### S3 Errors

- **No Credentials**: Shows helpful placeholder with configuration instructions
- **Network Errors**: Shows error message with retry capability
- **Permission Errors**: Shows accessible buckets only
- **Service Errors**: Graceful degradation to local-only mode

## Benefits

### User Experience

- **Unified Interface**: Single dialog for all storage types
- **Quick Access**: Faster navigation to frequently used locations
- **Visual Clarity**: Clear icons and descriptions for each drive
- **Responsive**: Real-time filtering and background loading

### Developer Benefits

- **Extensible**: Easy to add new storage types
- **Maintainable**: Clean separation of concerns
- **Testable**: Comprehensive unit test coverage
- **Consistent**: Follows established TFM patterns

## Future Enhancements

### Potential Additions

1. **Additional Storage Types**
   - SFTP/SSH remote directories
   - FTP servers
   - Network shares (SMB/CIFS)
   - Cloud storage (Google Drive, Dropbox)

2. **Enhanced Features**
   - Favorite drives management
   - Recent drives history
   - Custom drive aliases
   - Drive usage statistics

3. **Advanced S3 Features**
   - Multi-region bucket support
   - Bucket metadata display
   - Cost estimation
   - Access policy information

## Testing

### Test Coverage

- **Unit Tests**: `test/test_drives_dialog.py`
- **Demo Script**: `demo/demo_drives_dialog.py`
- **Integration Tests**: Covered in main TFM test suite

### Test Scenarios

- Drive entry creation and formatting
- Dialog state management
- Threading and cancellation
- Error handling and recovery
- Navigation integration
- Filtering functionality

## Dependencies

### Required

- **Python 3.6+**: Core language support
- **curses**: Terminal UI library
- **threading**: Background S3 scanning

### Optional

- **boto3**: AWS S3 integration (graceful fallback if not available)
- **botocore**: AWS error handling

## Installation Notes

The drives dialog is automatically available when TFM is installed. For S3 functionality:

```bash
pip install boto3
aws configure  # Set up AWS credentials
```

## Troubleshooting

### Common Issues

1. **S3 Buckets Not Showing**
   - Check AWS credentials: `aws s3 ls`
   - Verify network connectivity
   - Check IAM permissions

2. **Slow Loading**
   - Large number of S3 buckets may take time to load
   - Network latency affects S3 discovery
   - Consider filtering to reduce visible items

3. **Permission Errors**
   - Some local directories may not be accessible
   - S3 buckets may have restricted access
   - Check user permissions and IAM policies

### Debug Information

Enable debug logging to troubleshoot issues:
- S3 operations are logged with error details
- Thread operations show timing information
- Navigation events are tracked

## Conclusion

The Drives Dialog enhances TFM's navigation capabilities by providing a unified, user-friendly interface for accessing both local and remote storage locations. Its clean design, robust error handling, and extensible architecture make it a valuable addition to the TFM feature set.