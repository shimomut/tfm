# S3 Empty Names Fix

## Issue Description

When browsing S3 buckets in TFM, directories were appearing with empty names and showing as "0B" in size. This made it impossible to identify or navigate to these directories.

## Root Cause

The issue was in the `name` property of the `S3PathImpl` class in `src/tfm_s3.py`. When S3 directory keys end with a forward slash (e.g., `test1/`), the original implementation:

```python
return self._key.split('/')[-1] if '/' in self._key else self._key
```

Would return an empty string because `"test1/".split('/')[-1]` returns `""` (the empty string after the final slash).

## Solution

The fix strips trailing slashes before splitting the key:

```python
# Strip trailing slash before splitting to handle directory keys properly
key_without_slash = self._key.rstrip('/')
return key_without_slash.split('/')[-1] if '/' in key_without_slash else key_without_slash
```

This ensures that:
- `test1/` becomes `test1` before splitting, resulting in name `test1`
- `path/to/dir/` becomes `path/to/dir` before splitting, resulting in name `dir`
- Regular files like `file.txt` continue to work correctly
- Bucket names (empty keys) continue to work correctly

## Test Cases

The fix handles all S3 path formats correctly:

| S3 URI | Key | Expected Name | Result |
|--------|-----|---------------|---------|
| `s3://bucket/` | `""` | `bucket` | ✓ |
| `s3://bucket/file.txt` | `file.txt` | `file.txt` | ✓ |
| `s3://bucket/dir/` | `dir/` | `dir` | ✓ |
| `s3://bucket/dir` | `dir` | `dir` | ✓ |
| `s3://bucket/path/to/file.txt` | `path/to/file.txt` | `file.txt` | ✓ |
| `s3://bucket/path/to/dir/` | `path/to/dir/` | `dir` | ✓ |

## Files Modified

- `src/tfm_s3.py`: Fixed the `name` property in `S3PathImpl` class
- `test/test_s3_integration.py`: Added test cases for the name property
- `demo/demo_s3_empty_names_fix.py`: Added demo script to verify the fix

## Verification

The fix can be verified by:

1. Running the integration test: `python test/test_s3_integration.py`
2. Running the demo script: `python demo/demo_s3_empty_names_fix.py`
3. Using TFM to browse S3 buckets - directories should now show proper names

## Impact

This fix resolves the issue where S3 directories appeared with empty names in the TFM file browser, making S3 navigation functional and user-friendly.