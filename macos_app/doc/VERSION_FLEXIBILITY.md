# Python Version Flexibility

## Overview

The TFM macOS app bundle supports any Python 3.x version without code changes. The Objective-C launcher uses symlinks to automatically detect and use whatever Python version is embedded during the build process.

## Implementation

### Objective-C Launcher

The launcher uses the `Current` symlink instead of hardcoded version numbers:

```objective-c
// Version-flexible approach (current)
NSString *frameworksPath = [[mainBundle privateFrameworksPath] 
    stringByAppendingPathComponent:@"Python.framework/Versions/Current"];

// Old hardcoded approach (removed)
// NSString *frameworksPath = [[mainBundle privateFrameworksPath] 
//     stringByAppendingPathComponent:@"Python.framework/Versions/3.12"];
```

### Framework Structure

The build script creates a `Current` symlink that points to the embedded Python version:

```
Python.framework/
  Versions/
    3.13/              # Actual Python installation
    Current -> 3.13    # Symlink to current version
  bin -> Versions/Current/bin
  lib -> Versions/Current/lib
```

## Benefits

1. **No Code Changes Required**: Switching Python versions only requires rebuilding with a different venv
2. **Automatic Detection**: The launcher automatically uses whatever Python version is embedded
3. **Future-Proof**: Works with Python 3.12, 3.13, 3.14, and beyond
4. **Consistent Behavior**: Same code works across all Python 3.x versions

## Version Switching

To switch Python versions:

1. **Create new venv with desired Python:**
   ```bash
   rm -rf .venv
   python3.13 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Rebuild the app:**
   ```bash
   ./macos_app/build.sh
   ```

3. **Verify the version:**
   ```bash
   ./macos_app/build/TFM.app/Contents/MacOS/TFM
   # Check diagnostic output for Python version
   ```

The launcher will automatically use Python 3.13 without any code changes.

## Technical Details

### Symlink Resolution

When the launcher initializes Python:

1. Reads `Python.framework/Versions/Current` symlink
2. Resolves to actual version directory (e.g., `3.13`)
3. Sets `PYTHONHOME` to the resolved path
4. Python initialization uses the correct version-specific libraries

### Build-Time vs Runtime

- **Build-time**: The build script detects Python version from venv and creates version-specific directories
- **Runtime**: The launcher uses `Current` symlink to find the embedded Python, regardless of version

This separation allows the same launcher code to work with any Python version.

## Related Files

- `macos_app/src/TFMAppDelegate.m` - Objective-C launcher with version-flexible paths
- `macos_app/build.sh` - Build script that creates version-specific structure and `Current` symlink
- `macos_app/doc/VENV_BASED_BUILD.md` - Complete build system documentation

## History

- **Before**: Launcher hardcoded `Python.framework/Versions/3.12` path
- **After**: Launcher uses `Python.framework/Versions/Current` symlink
- **Result**: App works with any Python 3.x version without code changes
