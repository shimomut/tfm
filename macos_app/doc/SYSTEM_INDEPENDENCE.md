# System Python Independence

## Overview

The TFM macOS app bundle is designed to be independent of system Python installations. All Python components are bundled within the app, ensuring consistent behavior across different systems.

## Verification

The app bundle has been verified to have no dependencies on system Python installations:

### Runtime Verification

When TFM.app launches, it prints comprehensive diagnostic information:

```
================================================================================
TFM macOS App Bundle - Python Environment Diagnostics
================================================================================
Python executable: /Users/.../TFM.app/Contents/MacOS/TFM
Python version: 3.12.6 (main, Sep 10 2024, 14:05:22) [Clang 15.0.0 (clang-1500.3.9.4)]
Python prefix: /Users/.../TFM.app/Contents/Frameworks/Python.framework/Versions/3.12
Python base_prefix: /Users/.../TFM.app/Contents/Frameworks/Python.framework/Versions/3.12
Python library (build-time config, does not exist): /Users/.../.local/share/mise/installs/python/3.12.6/lib/libpython3.12.dylib
Python library (bundled, ✓ USING THIS): /Users/.../TFM.app/Contents/Frameworks/Python.framework/Versions/3.12/lib/libpython3.12.dylib

sys.path entries:
  [0] .../TFM.app/Contents/Resources/python_packages
  [1] .../TFM.app/Contents/Resources/ttk
  [2] .../TFM.app/Contents/Resources/tfm
  [3] .../TFM.app/Contents/Frameworks/Python.framework/Versions/3.12/lib/python312.zip
  [4] .../TFM.app/Contents/Frameworks/Python.framework/Versions/3.12/lib/python3.12
  [5] .../TFM.app/Contents/Frameworks/Python.framework/Versions/3.12/lib/python3.12/lib-dynload
  [6] .../TFM.app/Contents/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages

✓ All sys.path entries are within bundle

Loaded dynamic libraries (Python modules):
  ✓ _bisect: .../TFM.app/Contents/Frameworks/Python.framework/.../lib-dynload/_bisect.cpython-312-darwin.so
  ✓ _blake2: .../TFM.app/Contents/Frameworks/Python.framework/.../lib-dynload/_blake2.cpython-312-darwin.so
  ... (all loaded .so files are within bundle)

Process-level shared libraries (TFM executable dependencies):
  ✓ @executable_path/../Frameworks/Python.framework/Versions/3.12/lib/libpython3.12.dylib (bundled)
  ? /usr/lib/libSystem.B.dylib (system)
  ? /usr/lib/libobjc.A.dylib (system)

Total: 3 direct dependencies of TFM executable

Python library dependencies:
  ⚠ @executable_path/../Frameworks/Python.framework/Versions/3.12/lib/libpython3.12.dylib (external)
  ✓ /opt/homebrew/opt/gettext/lib/libintl.8.dylib (external)
  ○ /usr/lib/libSystem.B.dylib (system)

Total: 3 dependencies of Python library
================================================================================
```

**Key Points:**
- The "build-time config" path shows where Python was built (metadata only, file doesn't exist)
- The "bundled" path shows the actual runtime library being used (within app bundle)
- All Python modules (.so files) are loaded from within the bundle
- TFM executable has only 3 dependencies: bundled Python + 2 system libraries
- Python library has only 1 external dependency: Homebrew gettext (acceptable)

### 1. TFM Executable Dependencies
✓ The TFM executable uses relative paths (`@executable_path`) for Python library
✓ No hardcoded paths to system Python installations

### 2. Python sys.path
✓ All sys.path entries point to bundled Python components
✓ No system Python directories in sys.path
✓ User site-packages directory is explicitly disabled

### 3. User Site-Packages
✓ `site.ENABLE_USER_SITE` is set to `False` via `sitecustomize.py`
✓ User's `~/.local/lib/python3.12/site-packages` is not included

### 4. Python Library Install Names
✓ Python shared library uses relative path: `@executable_path/../Frameworks/Python.framework/...`
✓ No absolute paths to source Python installation

### 5. Loaded Dynamic Libraries
✓ All 38 loaded `.so` files are within the bundle
✓ No system Python modules are loaded at runtime

## External Dependencies

The bundled Python has one external library dependency:

- **gettext** (`/opt/homebrew/opt/gettext/lib/libintl.8.dylib`)
  - Used for internationalization support
  - Compile-time dependency of Python interpreter
  - Commonly available on macOS systems with Homebrew
  - Does not affect app functionality if missing (Python still works)

## Implementation Details

### sitecustomize.py

The bundle includes a `sitecustomize.py` file that disables user site-packages:

```python
import site
import sys

# Disable user site-packages for bundled app
site.ENABLE_USER_SITE = False

# Remove user site-packages from sys.path if it was already added
user_site = site.USER_SITE
if user_site in sys.path:
    sys.path.remove(user_site)
```

This file is automatically imported by Python's `site` module during startup, ensuring user site-packages are never included.

### Install Name Updates

The build script updates install names to use relative paths:

```bash
# Update Python library's install name (id)
install_name_tool -id \
    "@executable_path/../Frameworks/Python.framework/Versions/3.12/lib/libpython3.12.dylib" \
    "${PYTHON_LIB}"

# Update TFM executable to use bundled Python
install_name_tool -change \
    "${PYTHON_BASE_PREFIX}/lib/libpython3.12.dylib" \
    "@executable_path/../Frameworks/Python.framework/Versions/3.12/lib/libpython3.12.dylib" \
    "${MACOS_DIR}/TFM"
```

## Verification Script

A verification script is provided to check system Python independence:

```bash
./temp/verify_no_system_python_deps.sh
```

This script checks:
1. TFM executable dynamic library dependencies
2. Python sys.path entries
3. User site-packages status
4. Python library install names
5. External library dependencies
6. Standard library imports
7. Bundled package imports

## Benefits

### Consistency
- Same Python version and packages across all systems
- No conflicts with system Python installations
- Predictable behavior regardless of user's Python setup

### Portability
- App works on systems without Python installed
- No dependency on specific Python installation methods
- Users don't need to manage Python environments

### Security
- Isolated from system Python modifications
- No risk of importing untrusted packages from user site-packages
- Controlled dependency versions

### Reliability
- No breakage from system Python upgrades
- No conflicts with other Python applications
- Consistent package versions

## Related Files

- `macos_app/build.sh` - Build script with install name updates
- `macos_app/resources/sitecustomize.py` - Disables user site-packages
- `temp/verify_no_system_python_deps.sh` - Verification script
- `macos_app/doc/VENV_BASED_BUILD.md` - Build system documentation

## Testing

To verify system independence after building:

```bash
# Run verification script
./temp/verify_no_system_python_deps.sh

# Manual checks
otool -L macos_app/build/TFM.app/Contents/MacOS/TFM
macos_app/build/TFM.app/Contents/Frameworks/Python.framework/bin/python3 -c "import sys; print(sys.path)"
macos_app/build/TFM.app/Contents/Frameworks/Python.framework/bin/python3 -c "import site; print(site.ENABLE_USER_SITE)"
```

## Known Limitations

### Gettext Dependency
The bundled Python has a compile-time dependency on Homebrew's gettext library. This is acceptable because:
- It's a system library, not a Python package
- It's commonly available on macOS systems with Homebrew
- Python still functions if it's missing (internationalization features may be limited)
- It's not a dependency on system Python

### Future Improvements
To achieve complete independence, we could:
1. Bundle the gettext library within the app
2. Use a Python build that doesn't depend on gettext
3. Statically link gettext into Python

However, these improvements are not necessary for the current use case.
