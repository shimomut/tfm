# Font Rendering Diagnosis Guide

## Issue Description

User reports different text rendering between running TFM via CLI (`python3 tfm.py --desktop`) and running via app bundle (`open TFM.app`).

Both methods should use the same font configuration from `~/.tfm/config.py`.

## Configuration Flow

1. **CLI Mode**: `python3 tfm.py --desktop`
   - `tfm.py` → `cli_main()` in `tfm_main.py`
   - `cli_main()` → `select_backend(args)` in `tfm_backend_selector.py`
   - `select_backend()` → `get_backend_options()` → `get_config()` from `tfm_config.py`
   - Config loaded from `~/.tfm/config.py`
   - Font settings (`DESKTOP_FONT_NAME`, `DESKTOP_FONT_SIZE`) passed to `CoreGraphicsBackend`

2. **App Bundle Mode**: `open TFM.app`
   - `TFMAppDelegate.m` → Sets `sys.argv = ['TFM', '--desktop']`
   - Calls `cli_main()` from `tfm_main.py`
   - **Same flow as CLI mode from this point**

## Diagnostic Steps

### Step 1: Verify Config Loading

Run this test to verify config is loaded correctly:

```bash
python3 temp/test_config_loading.py
```

Expected output should show:
- Config file exists at `~/.tfm/config.py`
- `DESKTOP_FONT_NAME` is set (string or list)
- `DESKTOP_FONT_SIZE` is set (integer 8-72)

### Step 2: Verify Backend Initialization

Run this test to verify backend receives correct font settings:

```bash
python3 temp/test_backend_init.py
```

Expected output should show:
- Backend options include `font_names` (list) and `font_size` (int)
- Values match your config file

### Step 3: Compare Visual Rendering

To help diagnose the visual difference, please describe:

1. **Font appearance**:
   - Is the font family different? (e.g., Menlo vs Monaco)
   - Is the font size different? (larger/smaller)
   - Is the font weight different? (bold vs regular)

2. **Character spacing**:
   - Is character spacing wider or narrower?
   - Are characters overlapping or too far apart?

3. **Character rendering**:
   - Are characters blurry or sharp?
   - Are box-drawing characters (borders) rendering correctly?
   - Are wide characters (Japanese, Chinese) rendering correctly?

4. **Window size**:
   - Is the window size different?
   - Are there more or fewer rows/columns visible?

### Step 4: Check Font Availability

Verify the configured font is available on your system:

```bash
# List available monospace fonts
system_profiler SPFontsDataType | grep -i menlo
```

Or use Font Book.app to verify "Menlo" (or your configured font) is installed.

### Step 5: Check C++ Renderer

The CoreGraphics backend uses a C++ renderer module (`ttk_coregraphics_render.cpython-312-darwin.so`).

This module caches font information for performance. If the module was compiled with different font settings, it might cause rendering differences.

To rebuild the C++ renderer:

```bash
cd ttk
python3 setup.py build_ext --inplace
```

## Possible Causes

### 1. Font Cascade Fallback

The config supports font cascade (list of fonts). If the primary font is not available, it falls back to the next font in the list.

Example:
```python
DESKTOP_FONT_NAME = ['Menlo', 'Monaco', 'Courier']
```

If "Menlo" is not available, it uses "Monaco", then "Courier".

**Check**: Verify your primary font is installed and available.

### 2. Font Size Scaling

macOS may apply display scaling (Retina displays). The font size in points should be the same, but pixel rendering might differ.

**Check**: Compare font size in points (shown in TFM log or via Cmd+Plus/Minus).

### 3. Environment Differences

The app bundle runs in a different environment than the CLI:
- Different `$PATH`
- Different `$HOME` (should be the same)
- Different working directory (app bundle starts in `/`)

**Check**: Verify `~/.tfm/config.py` is accessible from both environments.

### 4. Python Environment

The app bundle uses embedded Python from `.venv/lib/python3.12/site-packages`.
The CLI uses system Python or virtualenv Python.

**Check**: Verify both use the same PyObjC version:

```bash
# CLI
python3 -c "import Cocoa; print(Cocoa.__file__)"

# App bundle (check in app log)
```

## Resolution Steps

### If Config Not Loading

1. Verify `~/.tfm/config.py` exists and is readable
2. Check file permissions: `ls -la ~/.tfm/config.py`
3. Check for syntax errors in config file

### If Font Not Available

1. Install the configured font (e.g., Menlo)
2. Or change config to use an available font
3. Restart TFM

### If C++ Renderer Issue

1. Rebuild C++ renderer: `cd ttk && python3 setup.py build_ext --inplace`
2. Copy rebuilt module to app bundle: `cp ttk_coregraphics_render.*.so ../macos_app/build/TFM.app/Contents/Resources/lib/python3.12/site-packages/`
3. Rebuild app bundle: `cd macos_app && ./build_app.sh`

### If Still Different

Please provide:
1. Screenshot of CLI rendering
2. Screenshot of app bundle rendering
3. Output of diagnostic scripts above
4. Contents of `~/.tfm/config.py` (font settings section)

## Related Files

- `src/tfm_config.py` - Config loading
- `src/tfm_backend_selector.py` - Backend option selection
- `ttk/backends/coregraphics_backend.py` - CoreGraphics backend
- `macos_app/src/TFMAppDelegate.m` - App bundle entry point
