# Virtual Environment Based Build System

## Overview

The TFM macOS app bundle build system uses the project's virtual environment (`.venv`) as the single source of truth for all Python components. This ensures consistency between development and bundled app environments.

## Build Philosophy

**Everything comes from `.venv`:**
- Python interpreter
- Python shared library
- Python standard libraries
- Third-party packages

This approach eliminates hardcoded system paths and works with any Python installation method (Python.framework, mise, pyenv, homebrew, etc.).

## Build Process

### 1. Python Detection

The build script detects Python configuration from `.venv`:

```bash
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python3"
PYTHON_VERSION=$("${VENV_PYTHON}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_BASE_PREFIX=$("${VENV_PYTHON}" -c "import sys; print(sys.base_prefix)")
```

### 2. Installation Type Detection

The script detects whether Python is installed as:
- **Python.framework** (python.org installer or Homebrew)
- **Standard Python** (mise, pyenv, system Python)

```bash
if [[ "${PYTHON_BASE_PREFIX}" == *"/Python.framework/Versions/"* ]]; then
    # Framework installation (python.org or Homebrew)
    PYTHON_FRAMEWORK="${PYTHON_BASE_PREFIX%/Versions/*}"
    USE_FRAMEWORK=true
else
    # Standard installation
    USE_FRAMEWORK=false
fi
```

For Homebrew Python, the framework root is extracted from the full base_prefix path.

### 3. Component Collection

All Python components are copied from the venv's base_prefix:

**Python Interpreter:**
- Source: `${PYTHON_BASE_PREFIX}/bin/python3.13`
- Destination: `TFM.app/Contents/Frameworks/Python.framework/Versions/3.13/bin/python3.13`
- Symlink created: `python3 -> python3.13`

**Python Shared Library:**
- Source: `${PYTHON_BASE_PREFIX}/lib/libpython3.13.dylib`
- Destination: `TFM.app/Contents/Frameworks/Python.framework/Versions/3.13/lib/libpython3.13.dylib`

**Python Standard Libraries:**
- Source: `${PYTHON_BASE_PREFIX}/lib/python3.12/`
- Destination: `TFM.app/Contents/Frameworks/Python.framework/Versions/3.12/lib/python3.12/`

**Third-Party Packages:**
- Source: `${PROJECT_ROOT}/.venv/lib/python3.12/site-packages/`
- Destination: `TFM.app/Contents/Resources/python_packages/`

### 4. Framework Structure Creation

The build script creates a Python.framework-like structure for consistency:

```
TFM.app/Contents/Frameworks/Python.framework/
  Versions/
    3.13/                    # Version-specific directory (auto-detected)
      Python                 # Shared library (framework style only)
      bin/
        python3.13           # Actual Python executable
        python3 -> python3.13
      lib/
        python3.13/          # Standard library
        libpython3.13.dylib  # Shared library (standard style)
    Current -> 3.13          # Symlink to current version
  bin -> Versions/Current/bin
  lib -> Versions/Current/lib
```

**Version Flexibility:** The Objective-C launcher uses the `Current` symlink instead of hardcoded version numbers, allowing the app to work with any Python version embedded during build time.

### 5. Install Name Updates

The build script updates the TFM executable to use the bundled Python:

```bash
install_name_tool -change \
    "${PYTHON_BASE_PREFIX}/lib/libpython3.13.dylib" \
    "@executable_path/../Frameworks/Python.framework/Versions/3.13/lib/libpython3.13.dylib" \
    "${MACOS_DIR}/TFM"
```

The version number is automatically detected from the venv and used in the install name path.

## Benefits

### 1. Consistency
Development and bundled app use the same Python version and packages.

### 2. Portability
Works with any Python installation method - no hardcoded paths.

### 3. Self-Contained
App bundle includes everything needed - no system dependencies.

### 4. Version Control
Python version is determined by the venv, not the build script.

### 5. Reproducibility
Same venv always produces the same bundle.

## External Program Support

The `tfm_python` variable in `src/tfm_external_programs.py` automatically detects app bundle execution and uses the bundled Python:

```python
if sys.platform == 'darwin' and '.app/Contents/MacOS' in sys.executable:
    # Running from macOS app bundle - use bundled python3
    bundle_path = sys.executable.rsplit('.app/Contents/MacOS', 1)[0] + '.app'
    tfm_python = os.path.join(bundle_path, 'Contents', 'Frameworks', 
                               'Python.framework', 'bin', 'python3')
else:
    # Normal execution - use current Python interpreter
    tfm_python = sys.executable
```

This ensures external programs (like preview scripts) use the bundled Python when running from the app bundle.

## Build Requirements

1. **Virtual environment must exist:**
   ```bash
   python3 -m venv .venv
   ```

2. **Dependencies must be installed:**
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Build script must be run from project root:**
   ```bash
   ./macos_app/build.sh
   ```

## Troubleshooting

### Python Not Found
```
[ERROR] Virtual environment not found at /path/to/project/.venv
```
**Solution:** Create virtual environment: `python3 -m venv .venv`

### Missing Dependencies
```
[ERROR] Failed to collect dependencies
```
**Solution:** Install dependencies: `pip install -r requirements.txt`

### Wrong Python Version
The bundled Python version matches the venv's Python version. To change:
1. Delete the venv: `rm -rf .venv`
2. Create new venv with desired Python: `python3.13 -m venv .venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Rebuild: `./macos_app/build.sh`

The Objective-C launcher automatically uses whatever Python version is embedded via the `Current` symlink.

## Related Files

- `macos_app/build.sh` - Main build script
- `macos_app/collect_dependencies.py` - Dependency collection script
- `src/tfm_external_programs.py` - Defines `tfm_python` variable
- `macos_app/doc/EXTERNAL_PROGRAMS_FIX.md` - External programs documentation

## Technical Notes

### Why Framework Structure?

Even for non-framework Python installations, we create a framework-like structure because:
1. Provides consistent paths regardless of source Python type
2. Simplifies install name updates
3. Matches macOS conventions for embedded frameworks
4. Makes the bundle structure predictable

### Symlink Strategy

Framework-level symlinks (`Python.framework/bin`, `Python.framework/lib`) point to version-specific directories. This allows:
- Easy version upgrades (just change `Current` symlink)
- Consistent paths for external programs
- Multiple Python versions in future (if needed)

**Important:** The build script uses `ln -sfn` (with `-n` flag) to prevent following existing symlinks when creating framework-level symlinks. This avoids creating broken symlinks inside the version-specific directory. See `macos_app/doc/SYMLINK_FIX.md` for details.

### Install Name Tool

The `install_name_tool` command updates dynamic library references in the TFM executable. This is necessary because:
1. Python shared library path is hardcoded at compile time
2. We need to redirect to bundled Python instead of system Python
3. `@executable_path` makes paths relative to the executable location
