# Dependency Collection Fix

## Problem

The initial implementation of `collect_dependencies.py` used a selective approach:
1. Read packages from `requirements.txt`
2. For each package, find it in site-packages
3. Recursively collect dependencies using `pip show`
4. Copy only the packages and their dependencies

This approach had a critical flaw: **it missed many PyObjC framework modules** that weren't explicitly listed as dependencies but were required by the CoreGraphics backend.

### Symptoms
- Build succeeded but app failed to launch
- Error: "PyObjC is required for CoreGraphics backend"
- PyObjC modules (Cocoa, AppKit, objc) were present but import check failed
- Root cause: Many PyObjC framework packages weren't being collected

## Solution

Changed to a comprehensive approach:
1. Copy **ALL packages** from `.venv/lib/python3.12/site-packages`
2. Skip only build tools (pip, setuptools, wheel, pkg_resources)
3. Skip special directories (__pycache__, _distutils_hack)
4. Verify PyObjC frameworks are present

### Code Changes

**Before (Selective):**
```python
def collect_dependencies(requirements_file, dest_dir):
    # Read requirements.txt
    packages = read_requirements(requirements_file)
    
    # Collect packages and their dependencies
    success_count, failed_packages = collect_all_dependencies(
        packages, site_packages_dir, dest_dir
    )
```

**After (Comprehensive):**
```python
def collect_dependencies(requirements_file, dest_dir):
    # Copy all packages from site-packages
    for item in site_packages_dir.iterdir():
        # Skip build tools and special directories
        if should_skip(item):
            continue
        
        # Copy everything else
        copy_item(item, dest_dir)
```

## Results

### Before Fix
- Copied: 8 packages (pygments, boto3, botocore, jmespath, s3transfer, dateutil, urllib3, six)
- Missing: 400+ PyObjC framework packages
- Status: App failed to launch

### After Fix
- Copied: 435 items from site-packages
- Includes: All PyObjC frameworks (Cocoa, AppKit, Foundation, etc.)
- Skipped: 7 build tools (pip, setuptools, wheel, etc.)
- Status: **App launches successfully**

## Why This Approach Works

1. **Complete Coverage**: Ensures all dependencies are included, even indirect ones
2. **Simple Logic**: No complex dependency resolution needed
3. **Reliable**: Works for all Python packages, not just those with proper metadata
4. **Fast**: Single directory copy operation
5. **Maintainable**: Easy to understand and modify

## Trade-offs

### Pros
- ✅ Guaranteed to include all dependencies
- ✅ No missing packages
- ✅ Simple implementation
- ✅ Works for all Python packages

### Cons
- ❌ Larger bundle size (includes unused packages)
- ❌ Includes development dependencies if present in venv

### Bundle Size Impact
- Before: ~50 MB (8 packages)
- After: ~100 MB (435 packages)
- Acceptable trade-off for reliability

## Best Practices

For future Python app bundling projects:

1. **Start comprehensive**: Copy everything from site-packages
2. **Optimize later**: Remove unused packages only after testing
3. **Use clean venv**: Create fresh virtual environment with only runtime dependencies
4. **Test thoroughly**: Verify app launches and all features work
5. **Document dependencies**: Keep requirements.txt up to date

## Alternative Approaches Considered

### 1. Selective with Better Metadata
- Use `importlib.metadata` to find all dependencies
- Problem: Still misses indirect dependencies and PyObjC frameworks

### 2. Static Analysis
- Parse Python files to find all imports
- Problem: Doesn't handle dynamic imports or conditional imports

### 3. Runtime Tracing
- Run app and trace all imports
- Problem: Requires running app, may miss code paths

### 4. Copy Everything (Chosen)
- Copy all packages from site-packages
- **Winner**: Simple, reliable, works for all cases

## Lessons Learned

1. **PyObjC is complex**: Many framework packages with interdependencies
2. **Metadata isn't perfect**: `pip show` doesn't list all dependencies
3. **Simplicity wins**: Comprehensive approach is more reliable than selective
4. **Test early**: Verify app launches before optimizing bundle size
5. **Clean venv matters**: Use dedicated venv for app bundling

## Verification

To verify the fix works:

```bash
# Clean build
cd macos_app
rm -rf build

# Rebuild
./build.sh

# Launch app
open build/TFM.app

# Check if running
ps aux | grep TFM.app
```

Expected output:
- Build completes successfully
- "Copied 435 items from site-packages"
- App launches and window appears
- Process shows in `ps` output

## Future Improvements

1. **Optimize bundle size**: Create clean venv with only runtime dependencies
2. **Exclude test packages**: Skip pytest, hypothesis, etc. if not needed
3. **Strip debug symbols**: Reduce binary sizes
4. **Compress resources**: Use compression for Python packages
5. **Lazy loading**: Load packages on demand instead of at startup

## References

- `macos_app/collect_dependencies.py` - Implementation
- `macos_app/build.sh` - Build script that calls collect_dependencies.py
- `requirements.txt` - Runtime dependencies
- `.venv/lib/python3.12/site-packages` - Source of packages

---

**Fix implemented: December 27, 2024**
**Status: Verified working**
