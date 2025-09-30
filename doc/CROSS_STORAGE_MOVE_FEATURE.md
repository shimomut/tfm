# Cross-Storage Move Feature

## Overview

TFM can move files between different types of storage - like moving files from your computer to Amazon S3, or between different S3 buckets. This works seamlessly with the regular move operation.

## Supported Storage Types

### Currently Supported
- **Local Files** - Files on your computer
- **Amazon S3** - AWS S3 buckets and files

### Coming Soon
- **SSH/SCP** - Remote servers
- **FTP/SFTP** - FTP servers
- **Other cloud storage** - Azure, Google Cloud

## How It Works

### Moving Within Same Storage
When moving files on the same storage (like local to local):
- Uses fast rename operation
- Happens instantly
- No data copying needed

### Moving Between Different Storage
When moving between different storage types (like local to S3):
- Copies the file to the destination
- Verifies the copy was successful
- Removes the original file
- Shows progress for large files
## Usage Examples

### Moving Files in TFM

The move operation works the same way regardless of storage type:

1. **Select files** you want to move (use Space to select)
2. **Press M** to start the move operation
3. **Navigate** to the destination (can be different storage type)
4. **Confirm** the move when prompted

### Example Scenarios

**Local to Local** (same computer):
- Move files between folders on your computer
- Happens instantly

**Local to S3** (upload to cloud):
- Move files from your computer to S3 bucket
- Shows progress for large files
- Requires AWS credentials

**S3 to Local** (download from cloud):
- Move files from S3 bucket to your computer
- Shows progress and transfer speed

**S3 to S3** (between buckets):
- Move files between different S3 buckets
- Can be faster than downloading and re-uploading

## What You'll See

### Cross-Storage Move Confirmation
When moving between different storage types, TFM shows:
```
Cross-storage move: Local → S3
Move 'document.txt' to s3://my-bucket/?
```

### Progress Display
For large files, you'll see:
- Current file being moved
- Progress percentage
- Transfer speed
- Estimated time remaining

## Performance

### Fast Moves (Same Storage)
- **Local to Local**: Instant
- **S3 to S3 (same bucket)**: Very fast

### Slower Moves (Cross-Storage)
- **Local to S3**: Depends on your upload speed
- **S3 to Local**: Depends on your download speed
- **S3 to S3 (different buckets)**: Moderate speed

## Configuration

You can adjust these settings in your config file:

```python
# Show confirmation dialogs
CONFIRM_MOVE = True
CONFIRM_CROSS_STORAGE = True  # Extra confirmation for cross-storage

# Show progress for large moves
SHOW_MOVE_PROGRESS = True
```

## Troubleshooting

### S3 Connection Issues
- Make sure you have AWS credentials set up
- Test with: `aws s3 ls s3://your-bucket/`
- Check your internet connection

### Permission Problems
- Check file permissions on local files
- Verify AWS credentials have proper S3 access
- Make sure you can write to the destination

### Network Problems
- Check your internet connection
- Try with smaller files first
- Some firewalls may block S3 access

## Tips

- **Test with small files first** when setting up S3
- **Large files show progress** so you know they're working
- **Failed moves don't delete the original** - your files are safe
- **Cross-storage moves take longer** than local moves
- **Directory moves work too** - all files are moved recursively

## Requirements

For S3 support, you need:
- AWS credentials configured
- `boto3` Python package installed
- Internet connection
- Proper S3 permissions

The cross-storage move feature makes it easy to move files between your computer and cloud storage!