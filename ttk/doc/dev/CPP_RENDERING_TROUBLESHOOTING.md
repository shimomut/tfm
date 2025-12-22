# C++ Rendering Backend Troubleshooting Guide

## Overview

This guide provides solutions to common issues encountered when using the C++ rendering backend. Issues are organized by category with symptoms, causes, and solutions.

## Quick Diagnostics

Run these commands to quickly diagnose common issues:

```bash
# Check if C++ renderer is available
python3 -c "import cpp_renderer; print('Available')" 2>&1

# Check environment variable
echo $TTK_USE_CPP_RENDERING

# Check which backend is being used
python3 -c "
from ttk.backends.coregraphics_backend import CoreGraphicsBackend
backend = CoreGraphicsBackend(24, 80)
print('C++ enabled:', backend.USE_CPP_RENDERING)
print('C++ available:', backend._cpp_renderer is not None)
"

# Get performance metrics
python3 -c "
import cpp_renderer
metrics = cpp_renderer.get_performance_metrics()
print('Frames rendered:', metrics['frames_rendered'])
"
```

## Build and Installation Issues

### Issue: "ModuleNotFoundError: No module named 'cpp_renderer'"

**Symptoms:**
```
ModuleNotFoundError: No module named 'cpp_renderer'
```

**Causes:**
1. C++ extension not built
2. Extension built for wrong Python version
3. Extension not in Python path

**Solutions:**

1. **Build the extension:**
   ```bash
   pip install -e . --force-reinstall --no-cache-dir
   ```

2. **Verify extension exists:**
   ```bash
   ls -l cpp_renderer*.so
   # Should show: cpp_renderer.cpython-<version>-darwin.so
   ```

3. **Check Python version match:**
   ```bash
   python3 --version
   # Compare with extension filename
   ```

4. **Verify extension is in correct location:**
   ```bash
   python3 -c "import sys; print('\n'.join(sys.path))"
   # Extension should be in one of these directories
   ```

### Issue: "Symbol not found" or "Library not loaded"

**Symptoms:**
```
ImportError: dlopen(...): Symbol not found: _CGContextFillRect
```

**Causes:**
1. Missing CoreGraphics framework
2. Incompatible macOS version
3. Wrong architecture (x86_64 vs arm64)

**Solutions:**

1. **Verify frameworks exist:**
   ```bash
   ls /System/Library/Frameworks/CoreGraphics.framework
   ls /System/Library/Frameworks/CoreText.framework
   ```

2. **Check macOS version:**
   ```bash
   sw_vers
   # Should be 10.13 or later
   ```

3. **Verify architecture match:**
   ```bash
   # Check extension architecture
   file cpp_renderer*.so
   
   # Check Python architecture
   python3 -c "import platform; print(platform.machine())"
   
   # Should match (both x86_64 or both arm64)
   ```

4. **Rebuild for correct architecture:**
   ```bash
   rm -f cpp_renderer*.so
   pip install -e . --force-reinstall --no-cache-dir
   ```

### Issue: Build fails with "Python.h not found"

**Symptoms:**
```
fatal error: 'Python.h' file not found
```

**Causes:**
1. Python development headers not installed
2. Wrong Python installation

**Solutions:**

1. **Check Python installation:**
   ```bash
   python3-config --includes
   # Should show include directories
   ```

2. **Reinstall Python (if using Homebrew):**
   ```bash
   brew reinstall python3
   ```

3. **Use system Python:**
   ```bash
   /usr/bin/python3 -m pip install -e .
   ```

### Issue: Build fails with C++17 errors

**Symptoms:**
```
error: no member named 'optional' in namespace 'std'
```

**Causes:**
1. Compiler doesn't support C++17
2. Outdated Xcode Command Line Tools

**Solutions:**

1. **Update Xcode Command Line Tools:**
   ```bash
   softwareupdate --list
   softwareupdate --install -a
   ```

2. **Verify compiler version:**
   ```bash
   clang++ --version
   # Should be Apple clang 14.0 or later
   ```

3. **Reinstall Command Line Tools:**
   ```bash
   sudo rm -rf /Library/Developer/CommandLineTools
   xcode-select --install
   ```

## Runtime Issues

### Issue: Application uses PyObjC instead of C++

**Symptoms:**
- No "Using C++ rendering backend" message
- Performance not improved

**Causes:**
1. Environment variable not set
2. C++ renderer import failed silently
3. Backend selector disabled

**Solutions:**

1. **Set environment variable:**
   ```bash
   export TTK_USE_CPP_RENDERING=true
   python3 tfm.py
   ```

2. **Check for import errors:**
   ```bash
   python3 -c "
   import sys
   try:
       import cpp_renderer
       print('Import successful')
   except Exception as e:
       print(f'Import failed: {e}')
       import traceback
       traceback.print_exc()
   "
   ```

3. **Verify backend configuration:**
   ```bash
   python3 -c "
   from ttk.backends.coregraphics_backend import CoreGraphicsBackend
   print('USE_CPP_RENDERING:', CoreGraphicsBackend.USE_CPP_RENDERING)
   "
   ```

4. **Check console output:**
   ```bash
   python3 tfm.py 2>&1 | grep -i "rendering\|cpp"
   ```

### Issue: "ValueError: Invalid parameters"

**Symptoms:**
```
ValueError: Invalid parameters
```

**Causes:**
1. Null CGContext
2. Invalid grid dimensions
3. Out-of-bounds cursor position
4. Invalid color values

**Solutions:**

1. **Check CGContext:**
   ```python
   graphics_context = Cocoa.NSGraphicsContext.currentContext()
   if graphics_context is None:
       print("ERROR: No graphics context")
       return
   
   context = graphics_context.CGContext()
   if context is None:
       print("ERROR: No CG context")
       return
   ```

### Issue: "render_frame() argument 1 must be int, not CGContextRef"

**Symptoms:**
```
CoreGraphicsBackend: C++ rendering failed: render_frame() argument 1 must be int, not CGContextRef
CoreGraphicsBackend: Falling back to PyObjC rendering
```

**Causes:**
The C++ `render_frame()` function expects the CGContext as an `unsigned long long` (pointer as integer), but the code is passing the PyObjC `CGContextRef` object directly.

**Solutions:**

1. **Verify the fix is applied:**
   Check that `ttk/backends/coregraphics_backend.py` contains the pointer conversion code in `_render_with_cpp()`:
   
   ```python
   # Get the CoreGraphics context
   context = Cocoa.NSGraphicsContext.currentContext().CGContext()
   
   # Convert CGContextRef to integer pointer for C++
   if hasattr(context, '__c_void_p__'):
       context_ptr = context.__c_void_p__().value
   else:
       context_ptr = int(context)
   
   # Convert NSRect to tuple for C++
   dirty_rect = (
       float(rect.origin.x),
       float(rect.origin.y),
       float(rect.size.width),
       float(rect.size.height)
   )
   
   # Call C++ render_frame() with converted parameters
   self.backend._cpp_renderer.render_frame(
       context_ptr,  # Integer pointer, not PyObjC object
       self.backend.grid,
       self.backend.color_pairs,
       dirty_rect,   # Tuple, not NSRect
       ...
   )
   ```

2. **Test the conversion:**
   ```python
   import Cocoa
   import Quartz
   
   # Create test context
   width, height = 100, 100
   color_space = Quartz.CGColorSpaceCreateDeviceRGB()
   context = Quartz.CGBitmapContextCreate(
       None, width, height, 8, width * 4,
       color_space, Quartz.kCGImageAlphaPremultipliedLast
   )
   
   # Test pointer conversion
   if hasattr(context, '__c_void_p__'):
       ptr = context.__c_void_p__().value
       print(f"Pointer: {ptr:#x}")
       assert isinstance(ptr, int) and ptr > 0
   ```

3. **Rebuild if necessary:**
   If the fix was recently applied, rebuild the C++ extension:
   ```bash
   python3 setup.py build_ext --inplace
   ```

**Note:** This issue was fixed in the implementation. If you encounter it, ensure you have the latest version of the code.

2. **Validate grid dimensions:**
   ```python
   if rows <= 0 or cols <= 0:
       print(f"ERROR: Invalid dimensions: {rows}x{cols}")
   ```

3. **Validate cursor position:**
   ```python
   if cursor_row < 0 or cursor_row >= rows:
       print(f"ERROR: Cursor row {cursor_row} out of bounds [0, {rows})")
   if cursor_col < 0 or cursor_col >= cols:
       print(f"ERROR: Cursor col {cursor_col} out of bounds [0, {cols})")
   ```

4. **Validate color values:**
   ```python
   for pair_id, (fg, bg) in color_pairs.items():
       for component in fg + bg:
           if not 0 <= component <= 255:
               print(f"ERROR: Color component {component} out of range [0, 255]")
   ```

### Issue: Visual artifacts or incorrect rendering

**Symptoms:**
- Characters in wrong positions
- Colors incorrect
- Missing characters
- Garbled text

**Causes:**
1. Grid data corruption
2. Coordinate transformation error
3. Cache corruption
4. Wide character handling issue

**Solutions:**

1. **Clear caches:**
   ```python
   import cpp_renderer
   cpp_renderer.clear_caches()
   ```

2. **Verify grid data:**
   ```python
   # Check grid structure
   print(f"Grid size: {len(grid)}x{len(grid[0]) if grid else 0}")
   
   # Check cell format
   for row in grid[:5]:  # First 5 rows
       for col in row[:10]:  # First 10 cols
           char, color_pair, attrs = col
           print(f"({repr(char)}, {color_pair}, {attrs})", end=" ")
       print()
   ```

3. **Compare with PyObjC rendering:**
   ```bash
   # Render with PyObjC
   unset TTK_USE_CPP_RENDERING
   python3 tfm.py
   
   # Render with C++
   export TTK_USE_CPP_RENDERING=true
   python3 tfm.py
   
   # Compare visually
   ```

4. **Check for wide characters:**
   ```python
   # Wide characters should have empty string in placeholder cell
   for row in grid:
       for i, cell in enumerate(row):
           char = cell[0]
           if len(char.encode('utf-8')) > 1:  # Multi-byte character
               if i + 1 < len(row):
                   next_char = row[i + 1][0]
                   if next_char != "":
                       print(f"ERROR: Wide char at ({row}, {i}) missing placeholder")
   ```

### Issue: Application crashes or segfaults

**Symptoms:**
```
Segmentation fault: 11
```

**Causes:**
1. Memory corruption
2. Invalid pointer access
3. CoreFoundation object use-after-free
4. Stack overflow

**Solutions:**

1. **Run with debugging:**
   ```bash
   lldb python3
   (lldb) run tfm.py
   # When crash occurs:
   (lldb) bt
   # Shows stack trace
   ```

2. **Check for memory leaks:**
   ```bash
   # Use Instruments
   instruments -t Leaks python3 tfm.py
   ```

3. **Enable debug logging:**
   ```python
   # Rebuild with debug flags
   # Edit setup.py: add '-DDEBUG' to extra_compile_args
   pip install -e . --force-reinstall --no-cache-dir
   ```

4. **Verify grid bounds:**
   ```python
   # Ensure grid is properly sized
   assert len(grid) == rows
   for row in grid:
       assert len(row) == cols
   ```

5. **Fall back to PyObjC:**
   ```bash
   unset TTK_USE_CPP_RENDERING
   python3 tfm.py
   # If crash persists, issue is not in C++ renderer
   ```

## Performance Issues

### Issue: C++ rendering slower than PyObjC

**Symptoms:**
- Higher render times with C++
- Lower FPS with C++

**Causes:**
1. Cold caches
2. Debug build
3. Excessive cache misses
4. Large grid size

**Solutions:**

1. **Warm up caches:**
   ```python
   # Render a few frames to populate caches
   for _ in range(10):
       backend.refresh()
   
   # Then measure performance
   ```

2. **Check build optimization:**
   ```bash
   # Verify -O3 flag is used
   python3 setup.py build_ext --inplace --verbose
   # Should show: -O3
   ```

3. **Check cache hit rates:**
   ```python
   import cpp_renderer
   metrics = cpp_renderer.get_performance_metrics()
   print(f"Cache hit rate: {metrics['attr_dict_cache_hit_rate']:.1f}%")
   # Should be >90%
   ```

4. **Profile rendering:**
   ```bash
   # Use built-in profiling
   python3 tools/profile_cpp_renderer.sh
   ```

5. **Reduce grid size:**
   ```python
   # Test with smaller grid
   backend = CoreGraphicsBackend(24, 80)  # Instead of 50x200
   ```

### Issue: High memory usage

**Symptoms:**
- Memory usage increases over time
- Application becomes slow

**Causes:**
1. Memory leak
2. Cache not evicting
3. Large grid allocations

**Solutions:**

1. **Check for leaks:**
   ```bash
   instruments -t Leaks python3 tfm.py
   # Run for several minutes, check for leaks
   ```

2. **Clear caches periodically:**
   ```python
   import cpp_renderer
   
   # Clear every N frames
   frame_count = 0
   def render():
       global frame_count
       frame_count += 1
       if frame_count % 1000 == 0:
           cpp_renderer.clear_caches()
   ```

3. **Monitor memory:**
   ```python
   import psutil
   import os
   
   process = psutil.Process(os.getpid())
   print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
   ```

4. **Reduce cache sizes:**
   ```cpp
   // Edit cpp_renderer.cpp
   // Reduce ColorCache max_size from 256 to 128
   ColorCache color_cache_(128);
   ```

### Issue: Low cache hit rates

**Symptoms:**
```
Cache hit rate: 45.2%  # Should be >90%
```

**Causes:**
1. Frequently changing colors
2. Many unique attribute combinations
3. Cache size too small

**Solutions:**

1. **Check color usage:**
   ```python
   # Count unique colors
   unique_colors = set()
   for pair_id, (fg, bg) in color_pairs.items():
       unique_colors.add(fg)
       unique_colors.add(bg)
   print(f"Unique colors: {len(unique_colors)}")
   # Should be <256
   ```

2. **Check attribute combinations:**
   ```python
   # Count unique attribute combinations
   unique_attrs = set()
   for row in grid:
       for cell in row:
           unique_attrs.add((cell[1], cell[2]))  # (color_pair, attributes)
   print(f"Unique combinations: {len(unique_attrs)}")
   ```

3. **Increase cache size:**
   ```cpp
   // Edit cpp_renderer.cpp
   // Increase ColorCache max_size
   ColorCache color_cache_(512);  // Instead of 256
   ```

## Debugging Tips

### Enable Verbose Logging

Add debug prints to C++ code:

```cpp
#ifdef DEBUG
#define DEBUG_LOG(msg) std::cerr << "[CPP] " << msg << std::endl
#else
#define DEBUG_LOG(msg)
#endif

// Usage
DEBUG_LOG("Rendering frame " << frames_rendered_);
DEBUG_LOG("Cache hit rate: " << (hits_ * 100.0 / (hits_ + misses_)) << "%");
```

Rebuild with debug flag:
```bash
# Edit setup.py: add '-DDEBUG' to extra_compile_args
pip install -e . --force-reinstall --no-cache-dir
```

### Use Instruments for Profiling

Profile rendering performance:

```bash
# Time Profiler
instruments -t "Time Profiler" python3 tfm.py

# Allocations
instruments -t "Allocations" python3 tfm.py

# Leaks
instruments -t "Leaks" python3 tfm.py
```

### Compare with PyObjC

Create side-by-side comparison:

```python
import time

# Test PyObjC
backend.USE_CPP_RENDERING = False
start = time.time()
for _ in range(100):
    backend.refresh()
pyobjc_time = time.time() - start

# Test C++
backend.USE_CPP_RENDERING = True
cpp_renderer.reset_metrics()
start = time.time()
for _ in range(100):
    backend.refresh()
cpp_time = time.time() - start

print(f"PyObjC: {pyobjc_time*10:.2f}ms per frame")
print(f"C++:    {cpp_time*10:.2f}ms per frame")
print(f"Speedup: {pyobjc_time/cpp_time:.2f}x")
```

### Capture Rendering Output

Render to offscreen buffer for inspection:

```python
import Cocoa

# Create offscreen context
width = cols * char_width
height = rows * char_height
colorspace = Cocoa.CGColorSpaceCreateDeviceRGB()
context = Cocoa.CGBitmapContextCreate(
    None, int(width), int(height), 8, 0, colorspace,
    Cocoa.kCGImageAlphaPremultipliedLast
)

# Render
cpp_renderer.render_frame(context, grid, color_pairs, ...)

# Save to file
image = Cocoa.CGBitmapContextCreateImage(context)
url = Cocoa.NSURL.fileURLWithPath_("/tmp/render_output.png")
dest = Cocoa.CGImageDestinationCreateWithURL(url, "public.png", 1, None)
Cocoa.CGImageDestinationAddImage(dest, image, None)
Cocoa.CGImageDestinationFinalize(dest)

print("Saved to /tmp/render_output.png")
```

## Common Error Messages

### "RuntimeError: Font loading failed"

**Cause**: Base font not available or invalid.

**Solution**:
```python
# Verify font exists
font = Cocoa.NSFont.userFixedPitchFontOfSize_(12.0)
if font is None:
    print("ERROR: No fixed-pitch font available")
```

### "MemoryError: Memory allocation failed"

**Cause**: Insufficient memory for large grid or caches.

**Solution**:
```python
# Reduce grid size
backend = CoreGraphicsBackend(24, 80)  # Smaller grid

# Or clear caches
cpp_renderer.clear_caches()
```

### "TypeError: argument 1 must be int, not NoneType"

**Cause**: CGContext is None.

**Solution**:
```python
graphics_context = Cocoa.NSGraphicsContext.currentContext()
if graphics_context is None:
    print("ERROR: No graphics context available")
    return

context = graphics_context.CGContext()
if context is None:
    print("ERROR: CGContext is None")
    return
```

## Platform-Specific Issues

### Apple Silicon (M1/M2/M3)

**Issue**: Extension built for x86_64 instead of arm64

**Solution**:
```bash
# Force arm64 build
export ARCHFLAGS="-arch arm64"
pip install -e . --force-reinstall --no-cache-dir

# Verify
file cpp_renderer*.so
# Should show: arm64
```

### Intel Macs

**Issue**: Extension built for arm64 instead of x86_64

**Solution**:
```bash
# Force x86_64 build
export ARCHFLAGS="-arch x86_64"
pip install -e . --force-reinstall --no-cache-dir

# Verify
file cpp_renderer*.so
# Should show: x86_64
```

### Rosetta 2

**Issue**: Running under Rosetta 2 causes performance issues

**Solution**:
```bash
# Check if running under Rosetta
sysctl sysctl.proc_translated
# 0 = native, 1 = Rosetta

# Use native Python
arch -arm64 python3 tfm.py  # On Apple Silicon
arch -x86_64 python3 tfm.py  # On Intel
```

## Getting Help

If issues persist after trying these solutions:

1. **Collect diagnostic information:**
   ```bash
   # System info
   sw_vers
   python3 --version
   clang++ --version
   
   # Extension info
   file cpp_renderer*.so
   python3 -c "import cpp_renderer; print(dir(cpp_renderer))"
   
   # Performance metrics
   python3 -c "import cpp_renderer; print(cpp_renderer.get_performance_metrics())"
   ```

2. **Check documentation:**
   - [API Documentation](CPP_RENDERING_API.md)
   - [Architecture Documentation](CPP_RENDERING_ARCHITECTURE.md)
   - [Build Guide](CPP_RENDERING_BUILD.md)
   - [Performance Guide](CPP_RENDERING_PERFORMANCE.md)

3. **Try clean rebuild:**
   ```bash
   # Remove all build artifacts
   rm -rf build/ dist/ *.egg-info cpp_renderer*.so
   
   # Clean Python cache
   find . -type d -name __pycache__ -exec rm -rf {} +
   find . -type f -name "*.pyc" -delete
   
   # Rebuild
   pip install -e . --force-reinstall --no-cache-dir
   ```

4. **Test with minimal example:**
   ```python
   import cpp_renderer
   import Cocoa
   
   # Create minimal test
   grid = [[(' ', 0, 0)] * 10] * 5
   color_pairs = {0: ((255, 255, 255), (0, 0, 0))}
   
   # Create offscreen context
   colorspace = Cocoa.CGColorSpaceCreateDeviceRGB()
   context = Cocoa.CGBitmapContextCreate(
       None, 100, 50, 8, 0, colorspace,
       Cocoa.kCGImageAlphaPremultipliedLast
   )
   
   # Try rendering
   try:
       cpp_renderer.render_frame(
           context, grid, color_pairs,
           (0, 0, 100, 50),  # dirty_rect
           10.0, 10.0,  # char_width, char_height
           5, 10,  # rows, cols
           0.0, 0.0,  # offset_x, offset_y
           False, 0, 0,  # cursor
           ""  # marked_text
       )
       print("SUCCESS: Minimal rendering works")
   except Exception as e:
       print(f"FAILED: {e}")
       import traceback
       traceback.print_exc()
   ```

## Appendix: Diagnostic Script

Save as `diagnose_cpp_renderer.py`:

```python
#!/usr/bin/env python3
"""Diagnostic script for C++ renderer issues."""

import sys
import os
import platform

print("=== C++ Renderer Diagnostics ===\n")

# System info
print("System Information:")
print(f"  OS: {platform.system()} {platform.release()}")
print(f"  Architecture: {platform.machine()}")
print(f"  Python: {sys.version}")
print()

# Environment
print("Environment:")
print(f"  TTK_USE_CPP_RENDERING: {os.environ.get('TTK_USE_CPP_RENDERING', 'not set')}")
print()

# Import test
print("Import Test:")
try:
    import cpp_renderer
    print("  ✓ cpp_renderer imported successfully")
    
    # Check functions
    functions = ['render_frame', 'get_performance_metrics', 'reset_metrics', 'clear_caches']
    for func in functions:
        if hasattr(cpp_renderer, func):
            print(f"  ✓ {func} available")
        else:
            print(f"  ✗ {func} missing")
    
    # Get metrics
    print("\nPerformance Metrics:")
    metrics = cpp_renderer.get_performance_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
except ImportError as e:
    print(f"  ✗ Import failed: {e}")
    print("\nPossible causes:")
    print("  - Extension not built (run: pip install -e .)")
    print("  - Wrong Python version")
    print("  - Missing frameworks")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Backend test
print("\nBackend Configuration:")
try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    print(f"  USE_CPP_RENDERING: {CoreGraphicsBackend.USE_CPP_RENDERING}")
    
    backend = CoreGraphicsBackend(24, 80)
    print(f"  C++ renderer available: {backend._cpp_renderer is not None}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n=== End Diagnostics ===")
```

Run with:
```bash
python3 diagnose_cpp_renderer.py
```
