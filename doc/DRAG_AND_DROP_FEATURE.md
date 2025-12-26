# Drag-and-Drop Feature

## Overview

TFM supports drag-and-drop functionality in desktop mode, allowing you to drag files from the file manager to external applications. This feature enables seamless integration with your operating system and other applications, making it easy to transfer files, open them in specific programs, or perform other drag-based operations.

## How to Use Drag-and-Drop

### Basic Drag Operation

1. **Navigate to the files** you want to drag in TFM
2. **Select files** (optional):
   - Use `Space` to select individual files
   - Use `+` to select files matching a pattern
   - Use `*` to select all files
3. **Click and hold** the mouse button on a file
4. **Move the mouse** while holding the button down
5. **Drag over** the target application or location
6. **Release the mouse button** to drop the files

### What Gets Dragged

- **With selection**: All selected files are dragged together
- **Without selection**: Only the file under the cursor is dragged
- **Multiple files**: You can drag up to 1,000 files at once

### Visual Feedback

During a drag operation, you'll see:
- **Single file**: The filename appears in the drag image
- **Multiple files**: A count like "5 files" appears in the drag image
- **Cursor changes**: The system cursor indicates valid/invalid drop targets

## Supported Platforms

### macOS Desktop Mode

Drag-and-drop is **fully supported** when running TFM in desktop mode on macOS:
- Uses native macOS drag-and-drop system
- Works with Finder, applications, and the Dock
- Supports standard macOS drag modifiers:
  - **No modifier**: Default operation (usually copy)
  - **Option (⌥)**: Force copy operation
  - **Command (⌘)**: Force move operation

### Terminal Mode

Drag-and-drop is **not available** in terminal mode:
- Terminal environments don't support graphical drag-and-drop
- This applies to all platforms when running in terminal mode
- Use traditional copy/move commands instead (`F5` for copy, `F6` for move)

### Other Platforms

- **Windows**: Not yet implemented (planned for future release)
- **Linux**: Not yet implemented (planned for future release)

## Limitations

### Remote Files

You **cannot drag remote files** (S3, SSH, etc.):
- Only local files can be dragged
- Remote files must be copied locally first
- Error message: "Cannot drag remote files"

### Archive Contents

You **cannot drag files from inside archives**:
- Files viewed inside .zip, .tar, .gz archives cannot be dragged
- You can drag the archive file itself
- Extract files first if you need to drag them
- Error message: "Cannot drag files from inside archives"

### Parent Directory Marker

You **cannot drag the parent directory marker** (".."):
- The ".." entry is for navigation only
- No error is shown; drag simply doesn't start

### File Count Limit

You **cannot drag more than 1,000 files** at once:
- This limit prevents performance issues
- Error message: "Too many files selected (limit: 1000)"
- Drag files in smaller batches if needed

### Missing Files

Drag operations **validate file existence**:
- If a selected file no longer exists, drag is cancelled
- Error message: "File no longer exists: [filename]"
- Refresh the file list (`Ctrl+R`) if files have changed

## Common Use Cases

### Opening Files in Applications

Drag files to application icons or windows:
- Drag an image to Preview or Photoshop
- Drag a document to TextEdit or Word
- Drag a video to VLC or QuickTime

### Copying to Other Locations

Drag files to Finder windows or the Desktop:
- Hold **Option (⌥)** to ensure copy operation
- Useful for quick backups or file organization

### Moving Files

Drag files between locations on the same volume:
- Hold **Command (⌘)** to force move operation
- Files are moved instead of copied

### Adding to Applications

Drag files to the Dock or application launchers:
- Add files to application queues
- Create new documents from templates

## Troubleshooting

### Drag Doesn't Start

**Problem**: Clicking and moving doesn't initiate a drag

**Solutions**:
- Ensure you're in desktop mode (not terminal mode)
- Move the mouse at least 5 pixels before releasing
- Check that the file isn't a remote file or archive content
- Verify the file isn't the parent directory marker ("..")

### Drop Doesn't Work

**Problem**: Files don't drop when releasing the mouse

**Solutions**:
- Ensure the target application accepts file drops
- Check that you're dropping on a valid drop target
- Try holding modifier keys (Option or Command)
- Some applications only accept specific file types

### Error Messages

**"Cannot drag remote files"**
- You're trying to drag files from S3, SSH, or other remote storage
- Copy files locally first, then drag them

**"Cannot drag files from inside archives"**
- You're viewing files inside a .zip or .tar archive
- Extract the files first, or drag the archive file itself

**"Too many files selected (limit: 1000)"**
- You've selected more than 1,000 files
- Deselect some files or drag in smaller batches

**"File no longer exists: [filename]"**
- A selected file was deleted or moved
- Refresh the file list with `Ctrl+R`

## Tips and Best Practices

### Efficient Multi-File Dragging

- Use pattern selection (`+`) to select related files quickly
- Check the drag image to confirm the file count
- For large batches, consider using copy/move commands instead

### Working with Archives

- To drag files from an archive, extract them first (`F9`)
- You can drag the archive file itself without extracting
- Extracted files can be dragged normally

### Remote File Workflow

1. Navigate to remote files (S3, SSH)
2. Copy files locally (`F5`)
3. Navigate to the local copy
4. Drag files to your target application

### Performance Considerations

- Dragging many large files may take time
- The operating system handles the actual transfer
- TFM remains responsive during drag operations
- Cancel a drag by pressing `Escape` or dropping on an invalid target

## Related Features

- **Mouse Support**: See `MOUSE_EVENT_SUPPORT_FEATURE.md`
- **File Operations**: See `TFM_USER_GUIDE.md` for copy/move commands
- **Archive Support**: See `ARCHIVE_VIRTUAL_DIRECTORY_FEATURE.md`
- **S3 Support**: See `S3_SUPPORT_FEATURE.md`

## Technical Details

For developers interested in the implementation:
- See `doc/dev/DRAG_AND_DROP_IMPLEMENTATION.md` for architecture details
- Drag-and-drop uses the TTK backend abstraction layer
- Platform-specific implementations in backend modules
- Gesture detection uses distance and time thresholds
