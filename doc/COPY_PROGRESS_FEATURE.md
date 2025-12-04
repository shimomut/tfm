# Enhanced Copy Progress Feature

## Overview

TFM now provides detailed, real-time progress tracking for copy operations, especially when copying directories with many files or large files. The progress system runs operations in a background thread and provides frequent updates showing:

1. **Current filename** being copied
2. **File count progress** (e.g., "5/100")
3. **Byte-level progress** for large files (>1MB) in human-readable format (e.g., "15M/32.0G")
4. **Animated progress indicator** showing the operation is active

## Features

### Background Threading

Copy operations now run in a background thread, allowing the UI to remain responsive and update progress information in real-time without blocking.

### Fine-Grained Progress Updates

Instead of showing only top-level directory names, TFM now shows:
- Individual filenames as they're being copied
- Relative paths for files in subdirectories (e.g., `subdir/file.txt`)
- Progress updates for every file, not just directories

### Byte-Level Progress for Large Files

When copying large files (>1MB), TFM shows byte-level progress in human-readable format:
- Files are copied in 1MB chunks
- Progress is shown as bytes copied vs total size
- Example: `large_file.iso [15M/32.0G]` shows 15 megabytes copied of 32 gigabytes total
- Only displayed for files that require multiple read/write operations
- Formats: B (bytes), K (kilobytes), M (megabytes), G (gigabytes), T (terabytes)

### Progress Animation

A spinning animation indicator shows that the operation is actively running:
- Uses Unicode spinner characters: ⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
- Updates every 80ms for smooth animation
- Continues animating even during long file copies without progress updates
- Runs in a separate background thread for smooth, continuous animation
- Provides visual feedback that the operation hasn't frozen

## Usage

The enhanced progress tracking is automatic and requires no user configuration. When you copy files:

1. **Single file**: Progress shows immediately with filename
2. **Multiple files**: Progress shows file count and current filename
3. **Large files**: Additional byte-level progress appears in brackets
4. **Directories**: Shows each file being copied with its relative path

### Operation Control

During file operations:
- **Input is blocked**: You cannot move cursor or execute other commands
- **ESC to cancel**: Press ESC key to cancel the operation at any time
- **Clean cancellation**: Partial files are removed, operation stops gracefully
- **UI remains responsive**: Progress updates continue, animation keeps running

## Progress Display Format

The progress information appears in the status bar with this format:

```
⠋ Copying (to destination)... 45/100 (45%) - subdir/large_file.dat [67%]
```

Breaking down the components:
- `⠋` - Animated spinner showing active operation
- `Copying (to destination)` - Operation type and destination
- `45/100` - Files processed out of total
- `(45%)` - Overall percentage complete
- `subdir/large_file.dat` - Current file being copied
- `[67%]` - Byte-level progress for current large file

## Technical Details

### Threading Model

Copy operations use two background threads:

1. **Copy Thread**: Performs the actual file copying
   - Starts immediately when the operation begins
   - Updates progress through a callback mechanism
   - Automatically cleans up when complete
   - Doesn't block the main UI thread

2. **Animation Thread**: Keeps the spinner animating
   - Refreshes animation every 100ms
   - Continues even when no progress updates occur
   - Ensures smooth animation during large file copies
   - Stops automatically when operation completes

### Progress Throttling

To avoid overwhelming the UI with updates:
- Progress callbacks are throttled to minimum 50ms intervals
- Ensures smooth display without excessive redraws
- Balances responsiveness with performance

### File Size Thresholds

Different progress tracking based on file size:
- **Small files (<10MB)**: Simple copy with filename progress
- **Large files (≥10MB)**: Chunked copy with byte-level progress
- **Chunk size**: 1MB per chunk for optimal performance

### Cross-Storage Support

The enhanced progress tracking works across different storage types:
- **Local to local**: Uses optimized file walking with progress
- **Cross-storage** (e.g., local to S3): Uses recursive copy with progress
- **S3 to S3**: Uses S3-specific operations with progress tracking

## Performance Impact

The enhanced progress tracking has minimal performance impact:
- Background threading prevents UI blocking
- Progress throttling limits callback frequency
- Chunked copying for large files is efficient
- No significant overhead for small files

## Benefits

1. **Better user experience**: Users can see exactly what's happening
2. **No more "frozen" appearance**: Animation shows active progress
3. **Accurate time estimation**: File-level progress helps estimate completion
4. **Debugging aid**: Detailed progress helps identify slow operations
5. **Confidence**: Users know the operation is working, not stuck

## Examples

### Copying a Directory with Many Small Files

```
⠙ Copying (to backup)... 234/500 (47%) - documents/report_2024.pdf
```

### Copying a Large File

```
⠹ Copying (to archive)... 1/1 (100%) - video.mp4 [78%]
```

### Copying Mixed Content

```
⠸ Copying (to destination)... 15/50 (30%) - data/large_dataset.csv [23%]
```

## Related Features

- **Move operations**: Also use enhanced progress tracking
- **Delete operations**: Show file-by-file deletion progress
- **Archive operations**: Show progress for creating/extracting archives

## Configuration

No configuration is required. The feature is always enabled and automatically adapts to:
- File sizes (small vs. large)
- Number of files (single vs. multiple)
- Storage types (local vs. remote)
- Terminal width (truncates long filenames as needed)

## Troubleshooting

### Progress Appears Stuck

If progress appears stuck on a single file:
- Large files take time to copy
- Check the byte-level progress percentage
- Network operations may be slow for remote storage
- Press ESC to cancel if needed

### Progress Updates Too Fast

If progress updates are too fast to read:
- This is normal for many small files
- The final count will be accurate
- Check the log for detailed information

### No Progress Shown

If no progress appears:
- Progress only shows for operations with multiple files
- Single small file copies complete too quickly
- Check that the operation actually started

### Cannot Cancel Operation

If ESC doesn't cancel:
- Cancellation is checked between files
- Large file copies check cancellation every 1MB chunk
- Wait for current chunk to complete
- Operation will stop at next checkpoint

### Input Not Working

If keyboard input doesn't work:
- Check if a file operation is in progress
- Look for progress indicator in status bar
- Wait for operation to complete or press ESC to cancel
- Only ESC key works during operations

## Future Enhancements

Potential improvements for future versions:
- Transfer speed display (MB/s)
- Estimated time remaining
- Pause/resume capability
- Parallel file copying for better performance
- Progress history/log
