# Homebrew Python Support

## Overview

The TFM macOS app bundle build system now fully supports Homebrew Python installations. Homebrew installs Python as a Python.framework in `/opt/homebrew/opt/python@X.Y/Frameworks/Python.framework`, which requires special handling compared to standard Python installations.

## Changes Made

### 1. Framework Detection

Updated the build script to detect Python.framework installations regardless of location:

**Before:**
```bash
if [[ "${PYTHON_BASE_PREFIX}" == *"/Library/Frameworks/Python.framework"* ]]; then
    # Only detected python.org installations
```

**After:**
```bash
if [[ "${PYTHON_BASE_PREFIX}" == *"/Python.framework/Versions/"* ]]; then
    # Detects both python.org and Homebrew installations
```

### 2. Framework Root Extraction

Homebrew's `sys.base_prefix` includes the full path to the version-specific directory:
```
/opt/homebrew/opt/python@3.13/Frameworks/Python.framework/Versions/3.13
```

The build script now extracts the framework root by removing the `/Versions/X.Y` suffix:

```bash
PYTHON_FRAMEWORK="${PYTHON_BASE_PREFIX%/Versions/*}"
# Result: /opt/homebrew/opt/python@3.13/Frameworks/Python.framework
```

This allows the compiler flags to work correctly:
```bash
CFLAGS="${CFLAGS} -F${PYTHON_FRAMEWORK}/Versions/${PYTHON_VERSION}"
CFLAGS="${CFLAGS} -I${PYTHON_FRAMEWORK}/Versions/${PYTHON_VERSION}/include/python${PYTHON_VERSION}"
```

### 3. Sitecustomize.py for Framework Installations

Added sitecustomize.py installation for Python.framework builds to disable user site-packages:

```bash
# Add sitecustomize.py to disable user site-packages
SITECUSTOMIZE_SOURCE="${SCRIPT_DIR}/resources/sitecustomize.py"
SITECUSTOMIZE_DEST="${PYTHON_DEST}/lib/python${PYTHON_VERSION}/sitecustomize.py"
cp "${SITECUSTOMIZE_SOURCE}" "${SITECUSTOMIZE_DEST}"
```

This overrides Homebrew's default sitecustomize.py which adds `/opt/homebrew/lib/python3.13/site-packages` to sys.path.

## Supported Python Installations

The build system now supports:

1. **Python.org Framework** (`/Library/Frameworks/Python.framework`)
2. **Homebrew Framework** (`/opt/homebrew/opt/python@X.Y/Frameworks/Python.framework`)
3. **mise** (standard installation)
4. **pyenv** (standard installation)
5. **System Python** (standard installation)

## Build Process

### Detection Flow

1. Check if `sys.base_prefix` contains `/Python.framework/Versions/`
2. If yes → Framework installation (python.org or Homebrew)
3. If no → Standard installation (mise, pyenv, system)

### Framework Installation Handling

For framework installations:
1. Extract framework root from `base_prefix`
2. Set compiler flags with framework paths
3. Copy framework components to bundle
4. Install custom sitecustomize.py
5. Create version symlinks
6. Update install names

### Standard Installation Handling

For standard installations:
1. Use `base_prefix` directly
2. Set compiler flags with standard paths
3. Copy Python components to bundle
4. Install custom sitecustomize.py
5. Create framework-like structure
6. Update install names

## Verification

After building with Homebrew Python, verify:

1. **Python version:**
   ```bash
   ./macos_app/build/TFM.app/Contents/MacOS/TFM --version
   ```
   Should show Python 3.13.x

2. **No external paths in sys.path:**
   ```
   ✓ All sys.path entries are within bundle
   ```

3. **Bundled Python library:**
   ```
   Python library (bundled, ✓ USING THIS): .../libpython3.13.dylib
   ```

4. **Framework structure:**
   ```bash
   ls -la macos_app/build/TFM.app/Contents/Frameworks/Python.framework/Versions/
   ```
   Should show `Current -> 3.13` symlink

## Troubleshooting

### Compilation Fails with "Python.h not found"

**Cause:** Framework root extraction failed or compiler flags are incorrect.

**Solution:** Check that `PYTHON_FRAMEWORK` is set correctly:
```bash
echo "${PYTHON_FRAMEWORK}"
# Should be: /opt/homebrew/opt/python@3.13/Frameworks/Python.framework
```

### External Paths in sys.path

**Cause:** Homebrew's sitecustomize.py is still active.

**Solution:** Verify custom sitecustomize.py was installed:
```bash
cat macos_app/build/TFM.app/Contents/Frameworks/Python.framework/Versions/3.13/lib/python3.13/sitecustomize.py
```
Should contain "Site customization for bundled TFM Python"

### Wrong Python Version

**Cause:** Virtual environment is using a different Python version.

**Solution:** Recreate venv with desired Python:
```bash
rm -rf .venv
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./macos_app/build.sh
```

## Related Files

- `macos_app/build.sh` - Build script with framework detection
- `macos_app/resources/sitecustomize.py` - Custom site customization
- `macos_app/doc/VENV_BASED_BUILD.md` - Complete build documentation
- `macos_app/doc/VERSION_FLEXIBILITY.md` - Python version flexibility

## Technical Notes

### Homebrew Python Structure

Homebrew installs Python as a framework with this structure:
```
/opt/homebrew/opt/python@3.13/
  Frameworks/
    Python.framework/
      Versions/
        3.13/
          Python              # Shared library
          bin/
            python3.13
          lib/
            python3.13/
            libpython3.13.dylib
          include/
            python3.13/
```

### Why Framework Detection Matters

Framework installations require different compiler flags:
- `-F` flag to specify framework search path
- Different include path structure
- Different library linking approach

Without proper detection, compilation fails with "Python.h not found".

### Sitecustomize.py Priority

Python loads sitecustomize.py from the first location found in sys.path. By placing our custom version in the bundled Python's lib directory, it takes precedence over any system-wide sitecustomize.py.

## History

- **Issue:** Build script only detected python.org framework installations
- **Impact:** Homebrew Python builds failed with compilation errors
- **Fix:** Updated framework detection to work with any Python.framework location
- **Result:** Build system now supports both python.org and Homebrew Python installations
