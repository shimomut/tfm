# Drives Dialog Feature

## Overview

The Drives Dialog provides quick access to storage locations and drives in TFM. It allows you to navigate to local filesystem locations and S3 buckets from a single, searchable interface.

## Key Binding

- **d** or **D** - Open the drives dialog

## Features

### Local Filesystem Locations

The drives dialog shows common local filesystem locations:

- **Home Directory** - Your user home directory (~)
- **Root Directory** - Filesystem root (/)
- **Current Directory** - The directory TFM was started from
- **Desktop** - ~/Desktop (if it exists)
- **Documents** - ~/Documents (if it exists)
- **Downloads** - ~/Downloads (if it exists)

### S3 Buckets

When boto3 is installed and AWS credentials are configured, the drives dialog also shows:

- **S3 Buckets** - All S3 buckets accessible with your AWS credentials
- **S3 Status** - Connection status and credential information

## Usage

### Opening the Drives Dialog

1. Press **d** or **D** to open the drives dialog
2. The dialog shows all available storage locations
3. Use arrow keys to navigate the list
4. Press **Enter** to navigate to the selected location
5. Press **Escape** or **q** to cancel

### Searching for Drives

The drives dialog supports incremental search:

1. Start typing to filter the list
2. The list updates as you type
3. Press **Backspace** to remove characters
4. Press **Escape** to clear the search

### Navigating to S3 Buckets

When S3 buckets are available:

1. Select an S3 bucket from the list
2. Press **Enter** to navigate to the bucket
3. The current pane will show the bucket contents
4. Navigate S3 like a regular filesystem

## Configuration

### S3 Setup

To enable S3 bucket listing in the drives dialog:

1. Install boto3: `pip install boto3`
2. Configure AWS credentials (one of):
   - AWS CLI: `aws configure`
   - Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - AWS credentials file: `~/.aws/credentials`

### Customizing Local Locations

The drives dialog automatically detects common directories. To customize which directories appear, you can use the Favorite Directories feature (press **j**) for frequently accessed locations.

## Visual Indicators

- 🏠 - Home directory
- 📁 - Local filesystem directory
- ☁️  - S3 bucket

## Troubleshooting

### S3 Buckets Not Showing

**Problem:** S3 buckets don't appear in the drives dialog

**Solutions:**
1. Verify boto3 is installed: `pip list | grep boto3`
2. Check AWS credentials are configured: `aws s3 ls`
3. Verify network connectivity to AWS
4. Check IAM permissions for S3 ListBuckets

### "S3 (boto3 not available)" Message

**Problem:** Message indicates boto3 is not installed

**Solution:** Install boto3: `pip install boto3`

### "S3 (No credentials configured)" Message

**Problem:** AWS credentials are not configured

**Solution:** Configure credentials using one of the methods above

### Permission Denied Errors

**Problem:** Cannot access certain directories

**Solution:** Check filesystem permissions for the directory

## Related Features

- **Favorite Directories** (j) - Quick access to frequently used directories
- **Jump Dialog** (J) - Fast directory navigation with search
- **S3 Integration** - Full S3 filesystem support

## See Also

- [Favorite Directories Feature](FAVORITE_DIRECTORIES_FEATURE.md)
- [S3 Integration](TFM_USER_GUIDE.md#s3-integration) (in User Guide)
- [Jump Dialog Feature](JUMP_DIALOG_FEATURE.md)
