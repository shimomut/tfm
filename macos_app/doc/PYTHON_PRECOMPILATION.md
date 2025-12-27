# Python Pre-compilation

## Overview

The TFM macOS app bundle pre-compiles all Python source files (`.py`) to bytecode (`.pyc`) during the build process. This includes:

1. **TFM application code** (`Resources/tfm/`)
2. **TTK library code** (`Resources/ttk/`)
3. **Third-party packages** (`Resources/python_packages/`)
4. **Python standard library** (`Frameworks/Python.framework/.../lib/python3.13/`)

Pre-compilation improves startup performance and ensures consistent behavior across different Python versions.

## Implementation

The build script uses Python's `compileall` module to pre-compile all Python files:

### Application Code (TFM and TTK)

```bash
# Pre-compile TFM Python files
log_info "Pre-compiling TFM Python files..."
if "${VENV_PYTHON}" -m compileall -q "${TFM_DEST}"; then
    log_info "  Compiled TFM Python files"
else
    log_info "  Warning: Compilation failed"
fi

# Pre-compile TTK Python files
log_info "Pre-compiling TTK Python files..."
if "${VENV_PYTHON}" -m compileall -q "${TTK_DEST}"; then
    log_info "  Compiled TTK Python files"
else
    log_info "  Warning: Compilation failed"
fi
```

### Python Standard Library

```bash
# Pre-compile Python standard library
log_info "Pre-compiling Python standard library..."
STDLIB_PATH="${PYTHON_DEST}/lib/python${PYTHON_VERSION}"
if [ -d "${STDLIB_PATH}" ]; then
    BUNDLE_PYTHON="${PYTHON_DEST}/bin/python3"
    if [ -f "${BUNDLE_PYTHON}" ]; then
        # -q: quiet mode (only show errors)
        # -f: force recompilation even if .pyc files exist
        if "${BUNDLE_PYTHON}" -m compileall -q -f "${STDLIB_PATH}"; then
            log_info "  Compiled Python standard library"
            PYC_COUNT=$(find "${STDLIB_PATH}" -name "*.pyc" | wc -l | tr -d ' ')
            PY_COUNT=$(find "${STDLIB_PATH}" -name "*.py" | wc -l | tr -d ' ')
            log_info "  Created ${PYC_COUNT} .pyc files from ${PY_COUNT} .py files"
        fi
    fi
fi
```

**Note**: The standard library compilation uses the bundled Python interpreter to ensure bytecode compatibility. A few test files with intentional syntax errors will fail to compile (this is expected and non-critical).

## Benefits

1. **Faster Startup**: Python doesn't need to compile `.py` files on first import
2. **Consistent Behavior**: Bytecode is generated once during build, not at runtime
3. **Reduced I/O**: Python can load `.pyc` files directly from `__pycache__` directories
4. **Version Compatibility**: Bytecode files are version-specific (e.g., `.cpython-313.pyc`)
5. **Complete Coverage**: All Python code (application, libraries, and standard library) is pre-compiled

## Compilation Statistics

Typical compilation results:

- **TFM**: ~50 Python files
- **TTK**: ~20 Python files
- **Third-party packages**: ~350 packages (varies by dependencies)
- **Python standard library**: ~1751 files (out of 1756 total, 5 intentionally broken test files excluded)

## File Structure

After pre-compilation, the bundle contains:

```
Resources/
├── tfm/
│   ├── __init__.py
│   ├── tfm_main.py
│   ├── tfm_colors.py
│   ├── ...
│   └── __pycache__/
│       ├── __init__.cpython-313.pyc
│       ├── tfm_main.cpython-313.pyc
│       ├── tfm_colors.cpython-313.pyc
│       └── ...
└── ttk/
    ├── __init__.py
    ├── ttk_application.py
    ├── ...
    └── __pycache__/
        ├── __init__.cpython-313.pyc
        ├── ttk_application.cpython-313.pyc
        └── ...
```

## Why Keep Source Files?

We keep both `.py` source files and `.pyc` bytecode files because:

1. **Debugging**: Stack traces show source file names and line numbers
2. **Introspection**: Tools can read source code for documentation and analysis
3. **Compatibility**: Some Python features require source files (e.g., `inspect.getsource()`)
4. **Size Trade-off**: The additional space (~2-3MB) is minimal compared to total bundle size

## Python Version Compatibility

The bytecode files are specific to Python 3.13 (`.cpython-313.pyc`). If the bundled Python version changes, the build script will automatically recompile with the correct version.

## Verification

To verify pre-compilation worked:

```bash
# Check TFM and TTK __pycache__ directories
ls macos_app/build/TFM.app/Contents/Resources/tfm/__pycache__/
ls macos_app/build/TFM.app/Contents/Resources/ttk/__pycache__/

# Check bytecode files exist
ls macos_app/build/TFM.app/Contents/Resources/tfm/__pycache__/*.pyc | head -5

# Check standard library pre-compilation
find macos_app/build/TFM.app/Contents/Frameworks/Python.framework/Versions/3.13/lib/python3.13 \
  -name "*.pyc" | wc -l
# Expected: ~1751 files
```

## Performance Impact

Pre-compilation provides:
- **Faster first import**: No compilation overhead on first run
- **Consistent performance**: Same startup time every time
- **Reduced CPU usage**: No compilation at runtime

The performance improvement is most noticeable on:
- First launch after installation
- Cold starts (when Python caches are cleared)
- Systems with slower disk I/O

## Related Documentation

- `VENV_BASED_BUILD.md` - Build system architecture
- `UNNECESSARY_FILES_CLEANUP.md` - Bundle optimization
