# File Details Feature (I Key)

TFM now includes a comprehensive file details viewer that shows detailed information about files and directories using the **I** key.

## Usage

### Basic Operation

- **I Key**: Show detailed information about files
- **Smart Selection**: 
  - If files are selected → shows details for all selected files
  - If no files are selected → shows details for file at cursor position

### Navigation in Details Dialog

| Key | Action |
|-----|--------|
| **↑/↓** or **j/k** | Scroll up/down line by line |
| **Page Up/Down** | Scroll by page |
| **Home** | Go to top |
| **End** | Go to bottom |
| **Q** or **ESC** | Close dialog |

## Information Displayed

### For Files

1. **Basic Info**:
   - File name
   - Full path
   - File type (File/Directory/Symbolic Link/Special)

2. **Size Information**:
   - Human-readable size (bytes, KB, MB, GB)
   - Automatic unit conversion

3. **Timestamps**:
   - Last modified date and time
   - Last accessed date and time

4. **Permissions**:
   - Unix-style permissions (rwxrwxrwx format)
   - Owner and group information

5. **Symbolic Links**:
   - Target path for symlinks
   - Error handling for unreadable targets

### For Directories

1. **Basic Info**:
   - Directory name and path
   - Type identification

2. **Contents Summary**:
   - Number of subdirectories
   - Number of files
   - Permission-aware counting

3. **Timestamps & Permissions**:
   - Same as files (modified, accessed, permissions, owner)

## Visual Interface

### Dialog Layout

```
┌─────────────── Details: filename.txt ───────────────┐
│ File: filename.txt                                   │
│ Path: /home/user/documents/filename.txt              │
│ Type: File                                           │
│ Size: 1.2 MB                                         │
│ Modified: 2024-03-15 14:30:22                        │
│ Accessed: 2024-03-15 16:45:10                        │
│ Permissions: -rw-r--r--                              │
│ Owner: user:staff                                     │
│                                                       │
│ ↑↓:scroll PgUp/PgDn:page Home/End:top/bottom Q:close │
└───────────────────────────────────────────────────────┘
```

### Multiple Files Display

When multiple files are selected, details are shown for each file with separators:

```
┌─────────────── Details: 3 items ─────────────────┐
│ File: document1.txt                               │
│ Path: /home/user/document1.txt                    │
│ Type: File                                        │
│ Size: 2.5 KB                                      │
│ Modified: 2024-03-15 10:15:30                     │
│ ──────────────────────────────────────────────────│
│ File: image.jpg                                   │
│ Path: /home/user/image.jpg                        │
│ Type: File                                        │
│ Size: 1.8 MB                                      │
│ Modified: 2024-03-14 18:22:45                     │
│ ──────────────────────────────────────────────────│
│ File: folder                                      │
│ Path: /home/user/folder                           │
│ Type: Directory                                   │
│ Contents: 2 directories, 5 files                  │
│ Modified: 2024-03-15 12:00:00                     │
└───────────────────────────────────────────────────┘
```

## Features

### Smart Size Display

- **Bytes**: Files under 1 KB show exact byte count
- **Kilobytes**: 1 KB - 1 MB range with 1 decimal place
- **Megabytes**: 1 MB - 1 GB range with 1 decimal place  
- **Gigabytes**: Files over 1 GB with 1 decimal place

### Error Handling

- **Permission Errors**: Gracefully handled with error messages
- **Missing Files**: Detected and reported
- **Unreadable Symlinks**: Shows target as `<unreadable>`
- **Directory Access**: Shows `<permission denied>` for inaccessible directories

### Cross-Platform Support

- **Unix/Linux/macOS**: Full owner/group information
- **Windows**: Falls back to UID/GID numbers
- **Permissions**: Uses standard Unix permission format

## Integration with TFM

### Works With All Features

- **File Selection**: Shows details for all selected files
- **Search Mode**: Can view details of search results
- **Both Panes**: Works in left and right panes
- **Sorting**: Details reflect current file organization

### Performance Optimized

- **Lazy Loading**: File stats read only when needed
- **Efficient Display**: Scrollable interface for large content
- **Memory Conscious**: Handles large file lists efficiently

## Example Use Cases

### 1. Quick File Inspection
```
1. Navigate to file with arrow keys
2. Press 'I' to see details
3. Review size, permissions, timestamps
4. Press 'Q' to close
```

### 2. Multiple File Comparison
```
1. Select multiple files with Space
2. Press 'I' to see all details
3. Scroll through comparison
4. Use for size/date analysis
```

### 3. Directory Analysis
```
1. Navigate to directory
2. Press 'I' to see contents summary
3. Check permissions and timestamps
4. Understand directory structure
```

### 4. Symlink Investigation
```
1. Navigate to symbolic link
2. Press 'I' to see target information
3. Verify link validity
4. Understand link relationships
```

## Technical Implementation

### File Stat Reading

- Uses Python's `pathlib.Path.stat()` for file information
- Handles `PermissionError` and other exceptions gracefully
- Caches information during dialog display

### Dialog System

- **Scrollable Interface**: Handles content larger than screen
- **Responsive Layout**: Adapts to terminal size (80% of screen)
- **Border Drawing**: Unicode box-drawing characters
- **Scroll Indicators**: Visual scrollbar for long content

### Time Formatting

- **Human Readable**: YYYY-MM-DD HH:MM:SS format
- **Local Time**: Uses system local time zone
- **Consistent Display**: Same format for all timestamps

## Keyboard Reference

### File Details Operations
- **I**: Show file details dialog

### Dialog Navigation
- **↑/↓** or **j/k**: Line-by-line scrolling
- **Page Up/Down**: Page scrolling
- **Home**: Jump to top
- **End**: Jump to bottom
- **Q** or **ESC**: Close dialog

### Integration Keys
- **Space**: Select files before viewing details
- **A**: Select all files for bulk details view
- **F**: Search files, then view details of results

The file details feature provides comprehensive file system information in an intuitive, scrollable interface that integrates seamlessly with TFM's existing functionality.