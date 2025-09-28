# TFM AWS S3 Support Feature

## Overview

TFM now supports AWS S3 operations through an extended Path implementation. This allows users to navigate, browse, and manipulate S3 buckets and objects using the same interface as local file operations.

## Features

### Path Support
- **S3 URI Format**: `s3://bucket-name/key/path`
- **Seamless Integration**: S3 paths work alongside local paths
- **Pathlib Compatibility**: All standard pathlib operations supported

### Supported Operations

#### Navigation and Browsing
- Navigate to S3 buckets: `s3://my-bucket/`
- Browse S3 objects like local files
- List bucket contents and nested "directories"
- Support for S3 prefix-based directory simulation

#### File Operations
- **Read Operations**: `read_text()`, `read_bytes()`, `open()`
- **Write Operations**: `write_text()`, `write_bytes()`, `open('w')`
- **File Info**: `stat()`, `exists()`, `is_file()`, `is_dir()`
- **File Management**: `unlink()`, `rename()`, `touch()`

#### Path Manipulation
- **Path Building**: `joinpath()`, `/` operator
- **Name Changes**: `with_name()`, `with_suffix()`, `with_stem()`
- **Path Properties**: `name`, `stem`, `suffix`, `parent`, `parts`

#### Directory Operations
- **Listing**: `iterdir()`, `glob()`, `rglob()`
- **Creation**: `mkdir()` (creates directory markers)
- **Removal**: `rmdir()` (removes empty directories)

## Requirements

### Dependencies
- **boto3**: AWS SDK for Python
- **Valid AWS Credentials**: Configured via AWS CLI, environment variables, or IAM roles

### Installation
```bash
pip install boto3
```

### AWS Configuration
```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment Variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-west-2

# Option 3: IAM Roles (for EC2 instances)
# Automatically detected when running on AWS infrastructure
```

## Usage Examples

### Basic Path Operations
```python
from tfm_path import Path

# Create S3 paths
bucket = Path('s3://my-bucket/')
file_path = Path('s3://my-bucket/documents/report.pdf')

# Path properties
print(file_path.name)        # 'report.pdf'
print(file_path.suffix)     # '.pdf'
print(file_path.parent)     # 's3://my-bucket/documents/'

# Path manipulation
new_file = file_path.with_name('summary.pdf')
csv_file = file_path.with_suffix('.csv')
```

### File Operations
```python
# Read file content
content = file_path.read_text()

# Write file content
file_path.write_text("Hello S3!")

# Check file existence
if file_path.exists():
    print("File exists in S3")

# Get file information
stat_info = file_path.stat()
print(f"Size: {stat_info.st_size} bytes")
```

### Directory Operations
```python
# List bucket contents
bucket = Path('s3://my-bucket/')
for item in bucket.iterdir():
    print(f"Found: {item}")

# Create directory (marker)
new_dir = Path('s3://my-bucket/new-folder/')
new_dir.mkdir()

# Search with patterns
for pdf_file in bucket.glob('*.pdf'):
    print(f"PDF: {pdf_file}")
```

### Mixed Local and S3 Operations
```python
# Copy from local to S3 (conceptual - actual implementation depends on TFM)
local_file = Path('/tmp/data.txt')
s3_file = Path('s3://my-bucket/backup/data.txt')

# Both paths work with the same interface
print(f"Local: {local_file.get_scheme()}")  # 'file'
print(f"S3: {s3_file.get_scheme()}")        # 's3'
```

## TFM Integration

### Navigation
- Navigate to S3 buckets in TFM: `s3://bucket-name/`
- Browse S3 objects like local directories
- Use standard TFM navigation keys

### File Operations
- Copy files between local and S3 storage
- Move and rename S3 objects
- Delete S3 objects with confirmation dialogs

### External Programs
- TFM environment variables work with S3 paths
- `TFM_THIS_DIR` can be an S3 path: `s3://bucket/folder/`
- `TFM_THIS_SELECTED` can include S3 objects
- External scripts can process S3 paths using boto3

### Search and Filter
- Search within S3 buckets using TFM's search functionality
- Filter S3 objects by name patterns
- Content search (if objects are text files)

## Implementation Details

### Architecture
- **S3PathImpl**: Extends `PathImpl` abstract base class
- **boto3 Integration**: Uses AWS SDK for all S3 operations
- **Lazy Loading**: S3 client created only when needed
- **Error Handling**: Proper exception handling for AWS errors

### S3 Directory Simulation
- S3 doesn't have true directories, only key prefixes
- Directories are simulated using common prefixes
- Directory markers (keys ending with '/') are supported
- Empty directories can be created using `mkdir()`

### Performance Considerations
- **Lazy Client Initialization**: S3 client created on first use
- **Paginated Listing**: Large buckets handled efficiently
- **Minimal API Calls**: Operations optimized for S3 API limits

### Error Handling
- **Credential Errors**: Clear messages when AWS credentials missing
- **Permission Errors**: Proper handling of access denied scenarios
- **Network Errors**: Graceful handling of connection issues
- **S3 Errors**: Specific handling for NoSuchBucket, NoSuchKey, etc.

## Limitations

### S3 Constraints
- **No Symbolic Links**: S3 doesn't support symlinks
- **No Hard Links**: S3 doesn't support hard links
- **No File Permissions**: chmod() is a no-op
- **No True Directories**: Directory operations are simulated

### Performance
- **Network Latency**: S3 operations slower than local file operations
- **API Rate Limits**: AWS S3 has request rate limits
- **Large Listings**: Very large buckets may be slow to browse

### AWS Costs
- **API Requests**: Each operation incurs AWS charges
- **Data Transfer**: Downloading/uploading data has costs
- **Storage**: S3 storage charges apply

## Security Considerations

### Credentials
- **Never Hardcode**: Don't embed AWS credentials in code
- **Use IAM Roles**: Preferred method for AWS infrastructure
- **Least Privilege**: Grant minimal required permissions

### Permissions
- **Bucket Access**: Requires appropriate S3 bucket permissions
- **Object Access**: Requires read/write permissions for objects
- **Cross-Account**: May require additional configuration

## Troubleshooting

### Common Issues

#### Credentials Not Found
```
Error: AWS credentials not found
Solution: Configure AWS credentials using 'aws configure' or environment variables
```

#### Permission Denied
```
Error: Access Denied
Solution: Check IAM permissions for the S3 bucket and objects
```

#### Bucket Not Found
```
Error: NoSuchBucket
Solution: Verify bucket name and region, check if bucket exists
```

#### Network Issues
```
Error: Connection timeout
Solution: Check internet connectivity and AWS service status
```

### Debug Tips
- Use AWS CLI to test connectivity: `aws s3 ls s3://bucket-name/`
- Check AWS credentials: `aws sts get-caller-identity`
- Verify region settings: `aws configure get region`
- Test with simple operations first

## Future Enhancements

### Planned Features
- **Multi-part Upload**: Support for large file uploads
- **Presigned URLs**: Generate shareable links
- **S3 Select**: Query data directly in S3
- **Versioning**: Support for S3 object versioning

### Integration Improvements
- **Progress Indicators**: Show upload/download progress
- **Caching**: Cache directory listings for better performance
- **Batch Operations**: Optimize multiple file operations

## Related Documentation
- [TFM Path Architecture](TFM_PATH_ARCHITECTURE.md)
- [External Programs Policy](../external-programs-policy.md)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)