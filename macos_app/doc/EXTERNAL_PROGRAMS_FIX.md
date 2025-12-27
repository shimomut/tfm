# External Programs Fix for macOS App Bundle

## Problem

When running TFM from the macOS app bundle, executing external programs would launch a new TFM process instead of the intended program.

## Root Cause

In the default configuration (`src/_config.py`), external programs that run Python scripts use `sys.executable` to invoke the Python interpreter:

```python
{'name': 'Preview Files', 'command': [sys.executable, tfm_tool('preview_files.py')], ...}
```

When running TFM normally (from command line), `sys.executable` points to the Python interpreter (e.g., `/usr/local/bin/python3`).

However, when running from the macOS app bundle, `sys.executable` points to the TFM executable itself:
```
/Applications/TFM.app/Contents/MacOS/TFM
```

This caused the external program execution to launch TFM again instead of running the Python script.

## Solution

Created a `tfm_python` variable in `src/tfm_external_programs.py` that:

1. Detects if running from a macOS app bundle by checking if `.app/Contents/MacOS` is in `sys.executable`
2. Returns the bundled Python executable path when running from app bundle
3. Returns `sys.executable` (current Python) for normal execution

The bundled Python path is:
```
TFM.app/Contents/Frameworks/Python.framework/bin/python3
```

Updated all external program definitions to use `tfm_python` instead of `sys.executable`:

```python
# In src/tfm_external_programs.py
if sys.platform == 'darwin' and '.app/Contents/MacOS' in sys.executable:
    # Running from macOS app bundle - use bundled python3 executable
    bundle_path = sys.executable.rsplit('.app/Contents/MacOS', 1)[0] + '.app'
    tfm_python = os.path.join(bundle_path, 'Contents', 'Frameworks', 
                               'Python.framework', 'bin', 'python3')
else:
    # Normal execution - use current Python interpreter
    tfm_python = sys.executable
```

The build script was updated to:
1. Detect Python installation from `.venv` (supports both Python.framework and standard Python installations like mise/pyenv/homebrew)
2. Copy the Python interpreter, shared library, and standard libraries from the venv's base_prefix
3. Copy all 3rd party packages from `.venv/lib/python3.12/site-packages`
4. Create framework-level symlinks for easy access to `bin/` directory

## Changes Made

### Modified Files

1. **src/tfm_external_programs.py**
   - Added `tfm_python` variable at module level
   - Detects app bundle execution and sets appropriate Python path

2. **src/_config.py**
   - Imports `tfm_python` from `tfm_external_programs`
   - Updated all `PROGRAMS` entries to use `tfm_python` instead of `sys.executable`
   - Updated example comments to show correct usage

3. **macos_app/build.sh**
   - Updated to detect Python from `.venv` instead of hardcoded system paths
   - Supports both Python.framework and standard Python installations (mise, pyenv, homebrew)
   - Copies Python interpreter from venv's base_prefix
   - Copies Python shared library from venv's base_prefix
   - Copies Python standard libraries from venv's base_prefix
   - Copies 3rd party packages from `.venv/lib/python3.12/site-packages`
   - Creates framework-level symlinks for `bin/` directory

4. **macos_app/collect_dependencies.py**
   - Already uses `.venv/lib/python3.12/site-packages` as source for dependencies

### Example Configuration

**Before:**
```python
PROGRAMS = [
    {'name': 'Preview Files', 'command': [sys.executable, tfm_tool('preview_files.py')], ...},
]
```

**After:**
```python
from tfm_external_programs import tfm_tool, tfm_python

PROGRAMS = [
    {'name': 'Preview Files', 'command': [tfm_python, tfm_tool('preview_files.py')], ...},
]
```

## User Impact

### For Command-Line Users
- No change in behavior
- External programs continue to work as before
- Uses the same Python interpreter that launched TFM

### For App Bundle Users
- External programs now work correctly
- Python scripts are executed with the bundled Python.framework
- No dependency on system Python installation

### For Custom Configurations

If users have custom external programs in their `~/.tfm/config.py`, they should update them to use `tfm_python`:

**Old (broken in app bundle):**
```python
{'name': 'My Script', 'command': [sys.executable, '/path/to/script.py']}
```

**New (works everywhere):**
```python
from tfm_external_programs import tfm_python
{'name': 'My Script', 'command': [tfm_python, '/path/to/script.py']}
```

## Testing

To verify the fix:

1. Build and launch the app bundle:
   ```bash
   make macos-app
   open macos_app/build/TFM.app
   ```

2. Navigate to a directory with files

3. Press `Shift+F2` to open external programs menu

4. Select "Preview Files" or any other Python-based external program

5. Verify that the correct program launches (not a new TFM window)

## Benefits of Using Bundled Python

Using the bundled Python.framework instead of system Python provides:

1. **Self-contained**: App doesn't depend on system Python installation
2. **Version consistency**: Always uses Python 3.12 (the bundled version)
3. **Reliability**: Works even if user doesn't have Python installed or has different version
4. **Package availability**: Has access to all bundled dependencies

## Related Files

- `src/tfm_external_programs.py` - Defines `tfm_python` variable
- `src/_config.py` - Configuration with external programs definitions
- `macos_app/src/TFMAppDelegate.m` - App bundle launcher
- `macos_app/build.sh` - Bundles Python.framework

## Technical Details

The bundled Python.framework structure:
```
TFM.app/
  Contents/
    MacOS/
      TFM                    # TFM executable (sys.executable points here)
    Frameworks/
      Python.framework/
        Versions/
          3.12/
            Python           # Python shared library
            bin/
              python3        # Python executable (tfm_python points here)
              python3.12     # Actual Python executable
            lib/
              python3.12/    # Python standard library
    Resources/
      tfm/                   # TFM source code
      ttk/                   # TTK library
      python_packages/       # Bundled dependencies
```

The `bin/python3` executable is copied from the system Python.framework during the build process.
