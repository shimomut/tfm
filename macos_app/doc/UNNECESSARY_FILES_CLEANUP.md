# Unnecessary Files Cleanup

## Overview

This document identifies unnecessary files in the TFM.app bundle and explains the cleanup process implemented in the build script.

## Problem

The bundled Python.framework contains several files that are not needed for TFM runtime:

1. **Python.app** (172KB) - GUI launcher application for Python
2. **Development tools** - idle, pip, pydoc, python-config
3. **pkg-config files** - Build system metadata

These files add ~250KB to the bundle size and serve no purpose in the embedded context.

## Files Identified for Removal

### 1. Python.app Directory
- **Location**: `Frameworks/Python.framework/Versions/3.13/Resources/Python.app`
- **Size**: 172KB
- **Purpose**: Standalone GUI launcher for Python interpreter
- **Why unnecessary**: TFM uses embedded Python through C API, not as standalone app

### 2. Development Tools in bin/
- **idle3.13** - Python IDE (IDLE)
- **pip3**, **pip3.13** - Package installer
- **pydoc3.13** - Documentation browser
- **python3.13-config** - Compiler configuration script

**Why unnecessary**: These are development/installation tools. TFM only needs the Python interpreter (`python3.13`) at runtime for external programs.

### 3. pkg-config Files
- **Location**: `Frameworks/Python.framework/Versions/3.13/lib/pkgconfig/`
- **Files**: `python-3.13.pc`, `python-3.13-embed.pc`
- **Purpose**: Build system metadata for compiling Python extensions
- **Why unnecessary**: TFM doesn't compile extensions at runtime

## Files to Keep

### Essential Runtime Files
- `bin/python3.13` - Python interpreter executable (needed for external programs)
- `bin/python3` - Symlink to python3.13
- `lib/libpython3.13.dylib` - Python shared library
- `lib/python3.13/` - Python standard library
- `Python` - Framework executable (main shared library)

## Implementation

The build script now includes a cleanup step after embedding Python:

```bash
# Remove unnecessary files from embedded Python
log_info "Removing unnecessary files from embedded Python..."

# Remove Python.app (GUI launcher)
if [ -d "${PYTHON_DEST}/Resources/Python.app" ]; then
    rm -rf "${PYTHON_DEST}/Resources/Python.app"
    log_info "  Removed Python.app"
fi

# Remove development tools from bin/
for tool in idle3.13 pip3 pip3.13 pydoc3.13 python3.13-config; do
    if [ -f "${PYTHON_DEST}/bin/${tool}" ]; then
        rm -f "${PYTHON_DEST}/bin/${tool}"
        log_info "  Removed bin/${tool}"
    fi
done

# Remove pkg-config files
if [ -d "${PYTHON_DEST}/lib/pkgconfig" ]; then
    rm -rf "${PYTHON_DEST}/lib/pkgconfig"
    log_info "  Removed lib/pkgconfig/"
fi
```

**Important**: The build script also creates a framework-level `bin` symlink for both Python.framework and standard Python installations. This symlink is required for external programs to find the bundled Python interpreter at `Python.framework/bin/python3`.

## Space Savings

- Python.app: ~172KB
- Development tools: ~60KB
- pkg-config: ~8KB
- **Total savings**: ~240KB

While not a huge reduction, this cleanup:
1. Removes clutter from the bundle
2. Eliminates potential confusion (users might try to use pip)
3. Follows best practices for embedded Python distributions

## Verification

After building, verify the cleanup:

```bash
# Should not exist
ls macos_app/build/TFM.app/Contents/Frameworks/Python.framework/Versions/3.13/Resources/Python.app
ls macos_app/build/TFM.app/Contents/Frameworks/Python.framework/Versions/3.13/bin/idle3.13
ls macos_app/build/TFM.app/Contents/Frameworks/Python.framework/Versions/3.13/bin/pip3
ls macos_app/build/TFM.app/Contents/Frameworks/Python.framework/Versions/3.13/lib/pkgconfig

# Should exist
ls macos_app/build/TFM.app/Contents/Frameworks/Python.framework/Versions/3.13/bin/python3.13
ls macos_app/build/TFM.app/Contents/Frameworks/Python.framework/Versions/3.13/bin/python3
ls macos_app/build/TFM.app/Contents/Frameworks/Python.framework/bin/python3  # Framework-level symlink
```

Use the verification script:

```bash
bash temp/verify_cleanup.sh
```

## Related Documentation

- `VENV_BASED_BUILD.md` - Build system architecture
- `SYSTEM_INDEPENDENCE.md` - Runtime independence verification
