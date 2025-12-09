# Archive Virtual Directory Browsing

## Overview

TFM allows you to browse the contents of archive files (`.zip`, `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`) as if they were regular directories, without extracting them to disk. You can navigate into archives, view files, copy files out of archives, and search within archive contents using familiar TFM operations.

## Supported Archive Formats

TFM supports the following archive formats:
- **ZIP**: `.zip`
- **TAR**: `.tar`
- **Compressed TAR**: `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`

## Basic Usage

### Entering an Archive

1. Navigate to an archive file in TFM
2. Position the cursor on the archive file
3. Press **ENTER**

The archive contents will be displayed as a virtual directory. You'll see files and directories with their names, sizes, and modification dates, just like browsing a regular directory.

### Visual Indicators

When browsing archive contents, you'll see:
- The archive filename in the path display
- The internal path within the archive (e.g., `archive:///path/to/file.zip#folder/subfolder`)
- A visual indicator in the status bar showing you're inside an archive
- Directory entries marked with the same indicators as regular directories
- File sizes showing the uncompressed size

### Navigating Within Archives

Once inside an archive, you can navigate using standard TFM keys:

| Key | Action |
|-----|--------|
| **↑/↓** | Move cursor up/down |
| **Page Up/Down** | Scroll by page |
| **Home/End** | Jump to first/last entry |
| **ENTER** | Enter a directory within the archive |
| **Backspace** | Go to parent directory within archive |
| **Backspace** (at root) | Exit archive and return to filesystem |

### Example Navigation Flow

```
1. Start in: /home/user/documents/
2. Press ENTER on: backup.zip
3. Now viewing: archive:///home/user/documents/backup.zip#
4. Press ENTER on: projects/
5. Now viewing: archive:///home/user/documents/backup.zip#projects/
6. Press Backspace
7. Back to: archive:///home/user/documents/backup.zip#
8. Press Backspace again
9. Back to: /home/user/documents/
```

## File Operations

### Viewing Files

To view a text file within an archive:

1. Navigate to the file within the archive
2. Press **F3** (or your configured view key)
3. The file will be extracted to a temporary location and displayed in the built-in text viewer
4. The viewer title shows the full archive path
5. When you close the viewer, temporary files are automatically cleaned up

### Copying Files from Archives

You can copy files from archives to your local filesystem or S3:

#### Copy Single File
1. Navigate to the file within the archive
2. Press **F5** (or your configured copy key)
3. Specify the destination directory
4. The file will be extracted to the destination

#### Copy Multiple Files
1. Select multiple files using **Insert** or **Space**
2. Press **F5** to copy
3. All selected files will be extracted to the destination

#### Copy Directories
1. Navigate to a directory within the archive
2. Press **F5** to copy
3. The entire directory structure and all contained files will be extracted recursively

#### Cross-Storage Copy
- **Archive to Local**: Works as described above
- **Archive to S3**: Files are extracted and uploaded directly to S3
- **Archive to Archive**: Not supported (archives are read-only)

### File Selection

File selection works the same way inside archives as in regular directories:

| Key | Action |
|-----|--------|
| **Insert** | Toggle selection on current file and move down |
| **Space** | Toggle selection on current file |
| **+** | Select files by pattern |
| **-** | Deselect files by pattern |
| **\*** | Invert selection |

## Search Within Archives

You can search for files within archive contents:

1. While browsing an archive, press **Alt+F7** (or your configured search key)
2. Enter a filename pattern (supports wildcards like `*.txt`)
3. Search results will show matching files with their full paths within the archive
4. Press **ENTER** on a search result to navigate to that file's location
5. For large archives, a progress indicator shows search progress

### Search Scope

When searching from within an archive:
- The search is limited to the current archive only
- The search starts from your current location within the archive
- Subdirectories are searched recursively

## Dual-Pane Operations

Archive browsing works seamlessly with TFM's dual-pane view:

### Viewing Archives in Both Panes
- You can browse an archive in the left pane while viewing a regular directory in the right pane
- You can browse different archives in both panes simultaneously
- You can browse the same archive in both panes at different locations

### Copying Between Panes
- Copy files from an archive pane to a filesystem pane
- Copy files from an archive pane to an S3 pane
- Copy files from one archive pane to another (extracts from source, copies to destination)

### Pane Synchronization
- Use **Alt+I** to show the same directory in both panes (works with archives)
- Use **Alt+O** to show the other pane's directory in the current pane

## Sorting and Display

### Sorting Archive Contents

Archive entries can be sorted using the same keys as regular directories:

| Key | Sort Mode |
|-----|-----------|
| **Ctrl+F3** | Sort by name |
| **Ctrl+F4** | Sort by extension |
| **Ctrl+F5** | Sort by modification time |
| **Ctrl+F6** | Sort by size |

Directories are always shown first, regardless of sort mode.

### File Details

To view detailed information about an archive entry:

1. Position cursor on the file or directory
2. Press **Ctrl+L** (or your configured details key)
3. The details dialog shows:
   - Entry name
   - Uncompressed size
   - Compressed size
   - Compression ratio
   - Modification time
   - File permissions
   - Archive type
   - Internal path within archive

## Key Bindings Summary

| Key | Action |
|-----|--------|
| **ENTER** | Enter archive / Enter directory within archive |
| **Backspace** | Go to parent directory / Exit archive |
| **F3** | View file from archive |
| **F5** | Copy file(s) from archive |
| **Insert/Space** | Select files within archive |
| **Alt+F7** | Search within archive |
| **Ctrl+F3-F6** | Sort archive contents |
| **Ctrl+L** | Show file details |

## Troubleshooting

### Archive Won't Open

**Problem**: Pressing ENTER on an archive file doesn't open it.

**Solutions**:
- Verify the file has a supported extension (`.zip`, `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`)
- Check if the archive file is corrupted by trying to open it with a standard archive tool
- Ensure you have read permissions for the archive file
- Check the TFM log for error messages (if logging is enabled)

**Error Message**: "Error: Cannot open archive file"
- The archive may be corrupted or in an unsupported format
- Try opening the archive with a standard tool to verify it's valid

### Cannot View Files

**Problem**: Pressing F3 on a file within an archive doesn't open the viewer.

**Solutions**:
- Ensure the file is a text file (binary files may not be viewable)
- Check if you have write permissions for the temporary directory
- Verify there's sufficient disk space for temporary file extraction
- Check if the file path within the archive is valid

**Error Message**: "Error: Cannot extract file for viewing"
- The archive entry may be corrupted
- There may be insufficient disk space
- The temporary directory may not be writable

### Copy Operations Fail

**Problem**: Copying files from an archive fails or produces errors.

**Solutions**:
- Ensure you have write permissions for the destination directory
- Verify there's sufficient disk space at the destination
- Check if the destination path is valid
- For S3 destinations, verify your AWS credentials are configured

**Error Message**: "Error: Extraction failed"
- The archive entry may be corrupted
- There may be insufficient disk space
- The destination may not be writable

### Search Not Working

**Problem**: Search within archive returns no results or fails.

**Solutions**:
- Verify your search pattern is correct (use `*` for wildcards)
- Ensure you're searching from within the archive (not from the filesystem)
- Check if the archive contains files matching your pattern
- For large archives, wait for the search to complete

**Error Message**: "Error: Search failed"
- The archive may be corrupted
- The search pattern may be invalid

### Performance Issues

**Problem**: Browsing large archives is slow.

**Solutions**:
- TFM caches archive structures to improve performance
- First access to a large archive may be slow while the structure is read
- Subsequent navigation within the same archive should be faster
- Consider extracting very large archives if you need frequent access

**Tips for Large Archives**:
- Archives with >10,000 files may take longer to open initially
- Archives >1GB may have slower extraction times
- Deeply nested directory structures may impact navigation speed
- Use search to quickly find files in large archives

### Temporary Files Not Cleaned Up

**Problem**: Temporary files remain after viewing files from archives.

**Solutions**:
- Temporary files should be automatically cleaned up when the viewer closes
- If files remain, they're typically in your system's temporary directory
- You can manually delete files matching the pattern `tfm_archive_*`
- Restart TFM to ensure all cleanup handlers run

### Archive Path Display Issues

**Problem**: The path display doesn't clearly show I'm in an archive.

**Solutions**:
- Look for the `archive://` prefix in the path
- Look for the `#` separator between archive path and internal path
- Check the status bar for archive browsing indicators
- The path should show: `archive:///full/path/to/archive.zip#internal/path`

## Tips and Best Practices

### Efficient Archive Browsing

1. **Use Search**: For large archives, use search (Alt+F7) to quickly find files instead of browsing manually
2. **Select Before Copying**: Select multiple files before copying to extract them all at once
3. **Check File Details**: Use Ctrl+L to verify file sizes before extracting large files
4. **Use Dual Panes**: Keep the destination directory visible in one pane while browsing the archive in the other

### Working with Multiple Archives

1. **Open in Different Panes**: Browse two archives simultaneously by opening them in different panes
2. **Compare Contents**: Use dual-pane view to compare contents of two archives
3. **Selective Extraction**: Copy specific files from multiple archives to a common destination

### Archive Organization

1. **Preview Before Extracting**: Browse archive contents to see what's inside before extracting
2. **Selective Extraction**: Extract only the files you need instead of the entire archive
3. **Verify Contents**: Use search to verify an archive contains expected files

### Performance Optimization

1. **Keep Archives Closed**: Exit archives when done to free up cache memory
2. **Avoid Repeated Opens**: Stay within an archive for multiple operations instead of exiting and re-entering
3. **Use Filters**: Use search patterns to limit results in large archives

## Limitations

### Read-Only Access
- Archives are read-only in TFM
- You cannot create, modify, or delete files within archives
- To modify archive contents, extract files, modify them, and create a new archive

### Archive Creation
- TFM supports browsing archives but not creating them
- Use standard archive tools to create archives
- TFM can extract files from archives for modification

### Nested Archives
- Archives within archives are shown as files
- You cannot directly browse nested archives
- Extract the inner archive first, then browse it

### Special Files
- Symbolic links within archives are shown but may not work correctly when extracted
- Special device files are not supported
- File permissions may not be fully preserved on all platforms

## Related Features

- **File Associations**: Configure external programs to open specific file types from archives
- **Text Viewer**: Built-in viewer for text files extracted from archives
- **Search Dialog**: Find files within archives by name or pattern
- **Dual-Pane View**: Browse archives alongside regular directories
- **Progress Display**: Visual feedback during extraction operations

## See Also

- [TFM User Guide](TFM_USER_GUIDE.md) - Complete TFM documentation
- [File Associations](FILE_ASSOCIATIONS_FEATURE.md) - Configure external programs
- [Search Feature](SEARCH_ANIMATION_FEATURE.md) - Advanced search options
- [Copy Progress](COPY_PROGRESS_FEATURE.md) - Understanding progress display
