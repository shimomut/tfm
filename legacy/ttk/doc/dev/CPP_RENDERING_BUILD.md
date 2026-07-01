# C++ Rendering Backend Build and Installation Guide

## Overview

This guide provides step-by-step instructions for building and installing the C++ rendering backend for the TTK CoreGraphics backend.

## Prerequisites

### System Requirements

- **Operating System**: macOS 10.13+ (High Sierra or later)
- **Architecture**: x86_64 or arm64 (Apple Silicon)
- **Python**: 3.7 or later
- **Xcode Command Line Tools**: Required for C++ compiler and frameworks

### Required Software

1. **Xcode Command Line Tools**
   ```bash
   xcode-select --install
   ```

2. **Python 3.7+**
   ```bash
   python3 --version
   # Should show 3.7 or later
   ```

3. **pip** (Python package installer)
   ```bash
   python3 -m pip --version
   ```

### Required Frameworks

The following macOS frameworks are required (included with Xcode Command Line Tools):
- CoreGraphics
- CoreText
- CoreFoundation

## Quick Start

For most users, the standard installation process will build the C++ extension automatically:

```bash
# Clone the repository
git clone <repository-url>
cd tfm

# Create and activate virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install with C++ extension
pip install -e .

# Verify installation
python3 -c "import cpp_renderer; print('C++ renderer available')"
```

If the import succeeds, the C++ renderer is ready to use!

## Detailed Build Instructions

### Step 1: Verify Prerequisites

Check that all prerequisites are installed:

```bash
# Check Xcode Command Line Tools
xcode-select -p
# Should output: /Library/Developer/CommandLineTools

# Check Python version
python3 --version
# Should be 3.7 or later

# Check compiler
clang++ --version
# Should show Apple clang version
```

### Step 2: Set Up Python Environment

Create a virtual environment (recommended):

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 3: Build the C++ Extension

The C++ extension is built automatically during installation:

```bash
# Install in development mode (recommended for development)
pip install -e .

# Or install normally
pip install .
```

The build process will:
1. Compile `ttk/backends/coregraphics_render.cpp` with C++17 standard
2. Link against CoreGraphics, CoreText, and CoreFoundation frameworks
3. Create `cpp_renderer.cpython-<version>-darwin.so` in the project directory

### Step 4: Verify Installation

Test that the C++ renderer can be imported:

```bash
python3 -c "import cpp_renderer; print('Success!')"
```

If successful, you should see "Success!" printed.

### Step 5: Enable C++ Rendering

Set the environment variable to use C++ rendering:

```bash
export TTK_USE_CPP_RENDERING=true
```

To make this permanent, add to your shell configuration:

```bash
# For bash
echo 'export TTK_USE_CPP_RENDERING=true' >> ~/.bash_profile

# For zsh
echo 'export TTK_USE_CPP_RENDERING=true' >> ~/.zshrc
```

### Step 6: Test the Application

Run the application to verify C++ rendering works:

```bash
python3 tfm.py
```

You should see a message in the console:
```
Using C++ rendering backend
```

## Manual Build (Advanced)

If you need to build the extension manually:

```bash
# Build extension in-place
python3 setup.py build_ext --inplace

# The .so file will be created in the current directory
ls -l cpp_renderer*.so
```

## Build Configuration

### Compiler Flags

The default build uses these compiler flags (configured in `setup.py`):

```python
extra_compile_args=[
    '-std=c++17',      # C++17 standard
    '-O3',             # Maximum optimization
    '-Wall',           # All warnings
    '-Wextra',         # Extra warnings
]
```

### Framework Linking

The extension links against these frameworks:

```python
extra_link_args=[
    '-framework', 'CoreGraphics',
    '-framework', 'CoreText',
    '-framework', 'CoreFoundation'
]
```

### Custom Build Options

To customize the build, edit `setup.py`:

```python
cpp_renderer = Extension(
    'cpp_renderer',
    sources=['ttk/backends/coregraphics_render.cpp'],
    include_dirs=['/usr/include'],
    extra_compile_args=[
        '-std=c++17',
        '-O3',              # Change to -O0 for debugging
        '-Wall',
        '-Wextra',
        # '-g',             # Uncomment for debug symbols
        # '-DDEBUG',        # Uncomment for debug logging
    ],
    extra_link_args=[
        '-framework', 'CoreGraphics',
        '-framework', 'CoreText',
        '-framework', 'CoreFoundation'
    ],
    language='c++'
)
```

## Troubleshooting Build Issues

### Issue: "xcode-select: error: tool 'xcodebuild' requires Xcode"

**Solution**: Install Xcode Command Line Tools:
```bash
xcode-select --install
```

### Issue: "clang: error: linker command failed"

**Cause**: Missing or incompatible frameworks.

**Solution**: Ensure Xcode Command Line Tools are properly installed:
```bash
xcode-select --install
xcode-select --reset
```

### Issue: "fatal error: 'Python.h' file not found"

**Cause**: Python development headers not found.

**Solution**: Ensure you're using the correct Python installation:
```bash
# Check Python installation
which python3
python3-config --includes

# If using Homebrew Python
brew reinstall python3
```

### Issue: "error: no member named 'optional' in namespace 'std'"

**Cause**: Compiler doesn't support C++17.

**Solution**: Update Xcode Command Line Tools:
```bash
softwareupdate --list
softwareupdate --install -a
```

### Issue: Build succeeds but import fails

**Cause**: Extension built for wrong architecture or Python version.

**Solution**: Rebuild with correct Python:
```bash
# Clean previous build
rm -rf build/ dist/ *.egg-info cpp_renderer*.so

# Rebuild
pip install -e . --force-reinstall --no-cache-dir
```

### Issue: "Symbol not found" error when importing

**Cause**: Missing framework or ABI incompatibility.

**Solution**: Check that frameworks are available:
```bash
# Verify frameworks exist
ls /System/Library/Frameworks/CoreGraphics.framework
ls /System/Library/Frameworks/CoreText.framework
ls /System/Library/Frameworks/CoreFoundation.framework
```

## Platform-Specific Notes

### Apple Silicon (M1/M2/M3)

The C++ extension builds natively for arm64 on Apple Silicon:

```bash
# Verify architecture
file cpp_renderer*.so
# Should show: Mach-O 64-bit bundle arm64
```

### Intel Macs

The extension builds for x86_64 on Intel Macs:

```bash
# Verify architecture
file cpp_renderer*.so
# Should show: Mach-O 64-bit bundle x86_64
```

### Universal Binaries

To build a universal binary (both architectures):

```bash
# Set architecture flags
export ARCHFLAGS="-arch x86_64 -arch arm64"
pip install -e .
```

## Development Build

For development with debugging:

1. Edit `setup.py` to add debug flags:
   ```python
   extra_compile_args=[
       '-std=c++17',
       '-O0',           # No optimization
       '-g',            # Debug symbols
       '-DDEBUG',       # Enable debug logging
       '-Wall',
       '-Wextra',
   ]
   ```

2. Rebuild:
   ```bash
   pip install -e . --force-reinstall --no-cache-dir
   ```

3. Debug with lldb:
   ```bash
   lldb python3
   (lldb) run tfm.py
   ```

## Performance Build

For maximum performance:

1. Edit `setup.py` to add aggressive optimization:
   ```python
   extra_compile_args=[
       '-std=c++17',
       '-O3',                    # Maximum optimization
       '-march=native',          # Optimize for current CPU
       '-flto',                  # Link-time optimization
       '-DNDEBUG',              # Disable assertions
       '-Wall',
       '-Wextra',
   ]
   ```

2. Rebuild:
   ```bash
   pip install -e . --force-reinstall --no-cache-dir
   ```

## Uninstallation

To remove the C++ extension:

```bash
# Uninstall package
pip uninstall tfm

# Remove built extension
rm -f cpp_renderer*.so

# Remove build artifacts
rm -rf build/ dist/ *.egg-info
```

## Continuous Integration

For CI/CD pipelines:

```bash
#!/bin/bash
set -e

# Install dependencies
pip install --upgrade pip setuptools wheel

# Build and install
pip install -e .

# Verify installation
python3 -c "import cpp_renderer; print('C++ renderer available')"

# Run tests
python3 -m pytest test/
```

## Docker Build (Not Recommended)

The C++ renderer requires macOS frameworks and cannot be built in Docker on Linux. For containerized builds, use macOS-based CI runners (e.g., GitHub Actions with `macos-latest`).

## Build Artifacts

After a successful build, you should have:

```
cpp_renderer.cpython-<version>-darwin.so  # The compiled extension
build/                                     # Build directory (can be deleted)
ttk/backends/coregraphics_render.cpp       # Source file
```

## Verification Checklist

After installation, verify:

- [ ] `import cpp_renderer` succeeds
- [ ] `cpp_renderer.render_frame` is callable
- [ ] `cpp_renderer.get_performance_metrics` returns a dict
- [ ] Application starts with "Using C++ rendering backend" message
- [ ] Rendering works correctly (no visual artifacts)
- [ ] No memory leaks (check with Instruments)

## Next Steps

After successful installation:

1. Read the [API Documentation](CPP_RENDERING_API.md) to understand the interface
2. Review the [Architecture Documentation](CPP_RENDERING_ARCHITECTURE.md) for design details
3. Check the [Performance Guide](CPP_RENDERING_PERFORMANCE.md) for optimization tips
4. Consult the [Troubleshooting Guide](CPP_RENDERING_TROUBLESHOOTING.md) if issues arise

## Support

If you encounter build issues not covered in this guide:

1. Check the [Troubleshooting Guide](CPP_RENDERING_TROUBLESHOOTING.md)
2. Verify all prerequisites are installed
3. Try a clean rebuild: `rm -rf build/ *.so && pip install -e . --force-reinstall`
4. Check the build log for specific error messages

## Appendix: Build System Details

### setup.py Configuration

The C++ extension is configured in `setup.py`:

```python
from setuptools import setup, Extension

cpp_renderer = Extension(
    'cpp_renderer',
    sources=['ttk/backends/coregraphics_render.cpp'],
    include_dirs=['/usr/include'],
    extra_compile_args=[
        '-std=c++17',
        '-O3',
        '-Wall',
        '-Wextra'
    ],
    extra_link_args=[
        '-framework', 'CoreGraphics',
        '-framework', 'CoreText',
        '-framework', 'CoreFoundation'
    ],
    language='c++'
)

setup(
    name='tfm',
    version='1.0.0',
    ext_modules=[cpp_renderer],
    # ... other setup parameters
)
```

### Build Process

The build process follows these steps:

1. **Preprocessing**: Expand macros and includes
2. **Compilation**: Compile C++ to object files
3. **Linking**: Link object files with frameworks
4. **Extension Creation**: Create Python-importable .so file

### Build Output

Typical build output:

```
running build_ext
building 'cpp_renderer' extension
creating build/temp.macosx-13.0-arm64-cpython-312
clang++ -std=c++17 -O3 -Wall -Wextra -c ttk/backends/coregraphics_render.cpp -o build/temp.macosx-13.0-arm64-cpython-312/ttk/backends/coregraphics_render.o
clang++ -bundle -undefined dynamic_lookup build/temp.macosx-13.0-arm64-cpython-312/ttk/backends/coregraphics_render.o -framework CoreGraphics -framework CoreText -framework CoreFoundation -o cpp_renderer.cpython-312-darwin.so
```

### Compiler Versions

Tested with:
- Apple clang version 14.0+ (Xcode 14+)
- Apple clang version 15.0+ (Xcode 15+)

### Python Versions

Tested with:
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.11
- Python 3.12

## References

- [Python Extension Building](https://docs.python.org/3/extending/building.html)
- [setuptools Documentation](https://setuptools.pypa.io/)
- [CoreGraphics Framework](https://developer.apple.com/documentation/coregraphics)
- [CoreText Framework](https://developer.apple.com/documentation/coretext)
