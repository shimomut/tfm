# Broken Symlink Fix

## Problem

The TFM macOS app bundle contained broken symlinks in the embedded Python framework:

```
Versions/3.12/bin/bin -> Versions/Current/bin (broken)
Versions/3.12/lib/lib -> Versions/Current/lib (broken)
Versions/3.12/3.12 -> 3.12 (broken self-reference)
```

These symlinks were:
1. Copied from the source Python installation during the build process
2. Recreated by the framework-level symlink creation code due to `ln -sf` following symlinks

## Root Cause

The issue had two parts:

### Part 1: Symlinks Copied from Source
When copying Python from the venv's base_prefix, some Python installations (particularly mise-installed Python) include framework-level symlinks inside the version-specific directory. These symlinks use relative paths like `Versions/Current/bin` which are valid in the source location but broken when copied to the bundle.

### Part 2: Symlinks Recreated by Build Script
The build script's framework-level symlink creation code was inadvertently recreating these broken symlinks:

```bash
# This code was creating symlinks in the wrong location
cd "${FRAMEWORK_DIR}"
ln -sf "Versions/Current/bin" bin  # Without -n flag, follows symlinks
```

When `ln -sf` is used without the `-n` flag, it can follow existing symlinks and create new symlinks inside the target directory instead of replacing the symlink itself.

## Solution

### Step 1: Remove Broken Symlinks After Copy
After copying Python components from the source, explicitly remove any problematic symlinks:

```bash
# Remove problematic symlinks that were copied from source Python
log_info "Removing broken symlinks from copied Python..."
if [ -L "${PYTHON_DEST}/bin/bin" ]; then
    rm -f "${PYTHON_DEST}/bin/bin"
    log_info "  Removed ${PYTHON_DEST}/bin/bin"
fi
if [ -L "${PYTHON_DEST}/lib/lib" ]; then
    rm -f "${PYTHON_DEST}/lib/lib"
    log_info "  Removed ${PYTHON_DEST}/lib/lib"
fi
if [ -L "${PYTHON_DEST}/${PYTHON_VERSION}" ]; then
    rm -f "${PYTHON_DEST}/${PYTHON_VERSION}"
    log_info "  Removed ${PYTHON_DEST}/${PYTHON_VERSION}"
fi
```

### Step 2: Use `ln -sfn` for Framework-Level Symlinks
Use the `-n` flag with `ln` to prevent following existing symlinks:

```bash
# Create framework-level symlinks (use -n to avoid following symlinks)
(cd "${VERSIONS_DIR}" && ln -sfn "${PYTHON_VERSION}" Current)
(cd "${FRAMEWORK_DIR}" && ln -sfn "Versions/Current/bin" bin)
(cd "${FRAMEWORK_DIR}" && ln -sfn "Versions/Current/lib" lib)
```

The `-n` flag treats the link name as a normal file if it's a symlink to a directory, preventing `ln` from following the symlink and creating a new symlink inside the target directory.

## Correct Framework Structure

After the fix, the framework structure is:

```
Python.framework/
  Versions/
    3.12/                    # Version-specific directory (no broken symlinks)
      bin/
        python3.12           # Actual Python executable
        python3 -> python3.12
      lib/
        python3.12/          # Standard library
        libpython3.12.dylib  # Shared library
    Current -> 3.12          # Symlink to current version
  bin -> Versions/Current/bin  # Framework-level symlink
  lib -> Versions/Current/lib  # Framework-level symlink
```

## Verification

To verify no broken symlinks exist:

```bash
find macos_app/build/TFM.app/Contents/Frameworks/Python.framework -type l \
  -exec sh -c 'if [ ! -e "$1" ]; then echo "BROKEN: $1 -> $(readlink "$1")"; fi' _ {} \;
```

This command should produce no output if all symlinks are valid.

## Impact

This fix ensures:
1. Clean framework structure without broken symlinks
2. External programs work correctly using the bundled Python
3. Build process is more robust across different Python installation methods
4. No confusion from broken symlinks during debugging

## Related Files

- `macos_app/build.sh` - Build script with symlink fixes
- `macos_app/doc/VENV_BASED_BUILD.md` - Venv-based build documentation
- `macos_app/doc/EXTERNAL_PROGRAMS_FIX.md` - External programs documentation

## Technical Notes

### Why `-n` Flag is Critical

Without `-n`, `ln -sf` behaves differently depending on whether the target exists:
- If target doesn't exist: creates symlink at specified location
- If target is a directory: creates symlink INSIDE the directory
- If target is a symlink to a directory: follows the symlink and creates inside

With `-n`, `ln -sfn` always treats the target as a file, replacing it if it exists.

### Why These Symlinks Exist in Source Python

Some Python installation methods (mise, pyenv) create framework-like structures even for non-framework Python installations. These include symlinks like `bin -> Versions/Current/bin` at the version-specific level, which are meant to be at the framework level.

When these are copied verbatim to the bundle, they break because the relative paths don't resolve correctly in the new location.
