# TFM macOS App Bundle - Build System

## Overview

The TFM macOS application bundle uses a native Objective-C launcher that embeds Python and launches TFM with its CoreGraphics backend. The build system is command-line based (no Xcode IDE required) and uses the project's virtual environment as the single source of truth for all Python components.

## Quick Start

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Build the app
cd macos_app
./build.sh

# Run the app
open build/TFM.app
```

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
    # Framework installation
    USE_FRAMEWORK=true
else
    # Standard installation
    USE_FRAMEWORK=false
fi
```

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
- Source: `${PYTHON_BASE_PREFIX}/lib/python3.13/`
- Destination: `TFM.app/Contents/Frameworks/Python.framework/Versions/3.13/lib/python3.13/`

**Third-Party Packages:**
- Source: `${PROJECT_ROOT}/.venv/lib/python3.13/site-packages/`
- Destination: `TFM.app/Contents/Resources/python_packages/`

**TFM Source:**
- Source: `${PROJECT_ROOT}/src/`
- Destination: `TFM.app/Contents/Resources/tfm/`

**TTK Library:**
- Source: `${PROJECT_ROOT}/ttk/` (runtime files only)
- Destination: `TFM.app/Contents/Resources/ttk/`

### 4. Framework Structure

The build script creates a Python.framework-like structure:

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

### 5. Bundle Optimization

The build script optimizes the bundle size by:

**Removing unnecessary Python files (~400KB savings):**
- Python.app GUI launcher (~172KB)
- Development tools (idle, pip, pydoc, python-config) (~60KB)
- pkg-config files (~8KB)
- Resources directory (~176KB)

**Selective TTK copying (~12.4MB savings):**
- Excludes doc/, demo/, test/, build/ directories
- Excludes development files (setup.py, py.typed, *.cpp)
- Includes only runtime files (Python modules, backends, serialization, utils)

**Total bundle size savings: ~12.8MB**

### 6. Python Pre-compilation

All Python source files are pre-compiled to bytecode for faster startup:

```bash
# Pre-compile TFM source
python3 -m compileall -q "${TFM_DEST}"

# Pre-compile TTK library
python3 -m compileall -q "${TTK_DEST}"

# Pre-compile Python standard library
python3 -m compileall -q -f "${STDLIB_PATH}"
```

**Benefits:**
- Faster application startup
- Consistent performance (no first-run compilation)
- Reduced I/O during module imports

**Note:** Source files (.py) are kept alongside bytecode (.pyc) for debugging and introspection.

### 7. Install Name Updates

The build script updates the TFM executable to use the bundled Python:

```bash
install_name_tool -change \
    "${PYTHON_BASE_PREFIX}/lib/libpython3.13.dylib" \
    "@executable_path/../Frameworks/Python.framework/Versions/3.13/lib/libpython3.13.dylib" \
    "${MACOS_DIR}/TFM"
```

## System Independence

The app bundle is completely independent of system Python installations:

### User Site-Packages Disabled

A `sitecustomize.py` file disables user site-packages:

```python
import site
import sys

# Disable user site-packages for bundled app
site.ENABLE_USER_SITE = False

# Remove user site-packages from sys.path if already added
user_site = site.USER_SITE
if user_site in sys.path:
    sys.path.remove(user_site)
```

### Relative Library Paths

All dynamic library references use relative paths (`@executable_path`) instead of absolute paths, ensuring the app works on any system without depending on specific Python installations.

### External Dependencies

The bundled Python has one external library dependency:
- **gettext** (`/opt/homebrew/opt/gettext/lib/libintl.8.dylib`)
  - Used for internationalization support
  - Commonly available on macOS systems with Homebrew
  - Does not affect core functionality if missing

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

1. **macOS 10.13 or later**
2. **Xcode Command Line Tools:**
   ```bash
   xcode-select --install
   ```
3. **Python 3.9 or later**
4. **Virtual environment with dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Makefile Integration

The build system integrates with the project Makefile:

```bash
# Build the app
make macos-app

# Clean build artifacts
make macos-app-clean

# Install to /Applications
make macos-app-install

# Create DMG installer
make macos-dmg
```

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

### 6. Performance
Pre-compiled bytecode provides faster startup and consistent performance.

### 7. Size Optimized
Unnecessary files removed, saving ~12.8MB of bundle size.

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

### Compilation Errors
```
[ERROR] Compilation failed
```
**Solution:** Ensure Xcode Command Line Tools are installed: `xcode-select --install`

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

**Important:** The build script uses `ln -sfn` (with `-n` flag) to prevent following existing symlinks when creating framework-level symlinks. This avoids creating broken symlinks inside the version-specific directory.

### Install Name Tool

The `install_name_tool` command updates dynamic library references in the TFM executable. This is necessary because:
1. Python shared library path is hardcoded at compile time
2. We need to redirect to bundled Python instead of system Python
3. `@executable_path` makes paths relative to the executable location

## Related Files

- `macos_app/build.sh` - Main build script
- `macos_app/collect_dependencies.py` - Dependency collection script
- `macos_app/src/main.m` - Objective-C entry point
- `macos_app/src/TFMAppDelegate.m` - Application delegate
- `macos_app/resources/Info.plist.template` - Bundle metadata template
- `macos_app/resources/sitecustomize.py` - Disables user site-packages
- `src/tfm_external_programs.py` - Defines `tfm_python` variable
- `Makefile` - Build system integration
