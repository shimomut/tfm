# Python Pre-compilation

## Overview

The TFM macOS app bundle pre-compiles all Python source files (`.py`) to bytecode (`.pyc`) during the build process. This improves startup performance and ensures consistent behavior across different Python versions.

## Implementation

The build script uses Python's `compileall` module to pre-compile all Python files:

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

## Benefits

1. **Faster Startup**: Python doesn't need to compile `.py` files on first import
2. **Consistent Behavior**: Bytecode is generated once during build, not at runtime
3. **Reduced I/O**: Python can load `.pyc` files directly from `__pycache__` directories
4. **Version Compatibility**: Bytecode files are version-specific (e.g., `.cpython-313.pyc`)

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
# Check for __pycache__ directories
ls macos_app/build/TFM.app/Contents/Resources/tfm/__pycache__/
ls macos_app/build/TFM.app/Contents/Resources/ttk/__pycache__/

# Check bytecode files exist
ls macos_app/build/TFM.app/Contents/Resources/tfm/__pycache__/*.pyc | head -5
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
