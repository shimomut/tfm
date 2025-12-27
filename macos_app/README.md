# TFM macOS Application Bundle

This directory contains the build system for creating a native macOS application bundle for TFM (Terminal File Manager). The bundle embeds a Python interpreter and provides a polished native macOS experience with full Dock integration and multi-window support.

## Table of Contents

- [Project Structure](#project-structure)
- [Build Requirements](#build-requirements)
- [Quick Start](#quick-start)
- [Build Scripts](#build-scripts)
- [Bundle Structure](#bundle-structure)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)

## Project Structure

```
macos_app/
├── README.md                    # This file
├── build.sh                     # Main build script
├── collect_dependencies.py      # Python dependency collector
├── create_dmg.sh               # DMG installer creator
├── src/                        # Objective-C source files
│   ├── main.m                  # Application entry point
│   ├── TFMAppDelegate.h        # App delegate header
│   └── TFMAppDelegate.m        # App delegate implementation
├── resources/                  # Build resources
│   ├── Info.plist.template     # App metadata template
│   └── TFM.icns               # Application icon (optional)
└── build/                      # Build output (created by build.sh)
    ├── TFM                     # Compiled executable
    ├── TFM.app/               # Complete app bundle
    └── TFM-{version}.dmg      # DMG installer
```

## Build Requirements

### Required Software

1. **Xcode Command Line Tools**
   - Provides the `clang` compiler and macOS frameworks
   - Install with: `xcode-select --install`
   - Verify installation: `clang --version`

2. **Python 3.9 or later**
   - Must be installed as a framework (standard macOS Python installer)
   - Verify installation: `python3 --version`
   - Check framework: `ls /Library/Frameworks/Python.framework/Versions/`

3. **Python Dependencies**
   - All packages from `requirements.txt` must be installed
   - Install with: `pip install -r ../requirements.txt`
   - Required packages include: pygments, boto3, PyObjC frameworks

### Why These Requirements?

- **Xcode Command Line Tools**: Provides the Cocoa framework (for native macOS UI) and the `clang` compiler (to compile Objective-C code)
- **Python Framework**: The app embeds Python, so it needs to be installed as a framework (not just a standalone binary)
- **Python Dependencies**: All packages TFM uses must be bundled into the app for it to be self-contained

## Quick Start

### Building the App

From the project root directory:

```bash
# Build the app bundle
make macos-app

# Or run the build script directly
cd macos_app
./build.sh
```

The built application will be at `macos_app/build/TFM.app`.

### Running the App

```bash
# Open the app
open macos_app/build/TFM.app

# Or double-click TFM.app in Finder
```

### Creating a DMG Installer

```bash
# Create DMG installer
make macos-dmg

# Or run the script directly
cd macos_app
./create_dmg.sh
```

The DMG will be at `macos_app/build/TFM-{version}.dmg`.

### Installing to Applications

```bash
# Install to /Applications
make macos-app-install

# Or copy manually
cp -R macos_app/build/TFM.app /Applications/
```

### Cleaning Build Artifacts

```bash
# Clean all build artifacts
make macos-app-clean

# Or remove manually
rm -rf macos_app/build
```

## Build Scripts

### build.sh

The main build script that creates the complete app bundle.

**What it does:**

1. **Compiles Objective-C source files** (`main.m`, `TFMAppDelegate.m`)
   - Uses `clang` with Cocoa and Python frameworks
   - Links against embedded Python interpreter
   - Sets up runtime paths for framework loading

2. **Creates bundle structure**
   - Creates `TFM.app/Contents/MacOS/` for the executable
   - Creates `TFM.app/Contents/Resources/` for Python code and resources
   - Creates `TFM.app/Contents/Frameworks/` for Python.framework

3. **Copies resources**
   - Copies TFM Python source from `src/` to `Resources/tfm/`
   - Copies TTK library from `ttk/` to `Resources/ttk/`
   - Collects Python dependencies to `Resources/python_packages/`
   - Copies application icon (if present)

4. **Embeds Python.framework**
   - Copies Python.framework from system location
   - Updates install names to use embedded framework
   - Creates version symlinks

5. **Generates Info.plist**
   - Substitutes version number from template
   - Validates XML structure

6. **Code signing (optional)**
   - Signs frameworks, executable, and bundle
   - Only if `CODESIGN_IDENTITY` is set

**Usage:**

```bash
# Basic build
./build.sh

# Build with specific Python version
PYTHON_VERSION=3.11 ./build.sh

# Build with code signing
CODESIGN_IDENTITY="Developer ID Application: Your Name" ./build.sh

# Build with custom version
VERSION=1.0.0 ./build.sh
```

### collect_dependencies.py

Python script that collects dependencies from `requirements.txt` and copies them to the bundle.

**What it does:**

1. Reads `requirements.txt` and extracts package names
2. Locates each package in site-packages
3. Copies packages with proper directory structure
4. Copies package metadata (.dist-info directories)
5. Recursively collects dependencies of dependencies
6. Verifies PyObjC frameworks are included

**Usage:**

```bash
# Collect dependencies
python3 collect_dependencies.py \
    --requirements ../requirements.txt \
    --dest build/TFM.app/Contents/Resources/python_packages
```

**Note:** This script is called automatically by `build.sh`.

### create_dmg.sh

Creates a distributable DMG installer containing TFM.app.

**What it does:**

1. Verifies TFM.app exists (requires running `build.sh` first)
2. Extracts version number from Info.plist
3. Creates temporary directory with TFM.app
4. Creates or copies INSTALL.md documentation
5. Creates compressed DMG with `hdiutil`
6. Names DMG as `TFM-{version}.dmg`

**Usage:**

```bash
# Create DMG (requires TFM.app to exist)
./create_dmg.sh

# Create DMG with custom version
VERSION=1.0.0 ./create_dmg.sh
```

## Bundle Structure

The built `TFM.app` follows the standard macOS application bundle structure:

```
TFM.app/
└── Contents/
    ├── Info.plist              # Application metadata
    │                           # - Bundle identifier: com.tfm.app
    │                           # - Bundle name: TFM
    │                           # - Executable name: TFM
    │                           # - Version: 0.98
    │                           # - Icon file: TFM.icns
    │                           # - Minimum macOS: 10.13
    │
    ├── MacOS/                  # Executable directory
    │   └── TFM                 # Objective-C launcher executable
    │                           # - Initializes NSApplication
    │                           # - Embeds Python interpreter
    │                           # - Handles Dock menu
    │                           # - Manages app lifecycle
    │
    ├── Resources/              # Application resources
    │   ├── TFM.icns           # Application icon (optional)
    │   │
    │   ├── tfm/               # TFM Python source code
    │   │   ├── __init__.py
    │   │   ├── tfm_main.py    # Main entry point
    │   │   ├── tfm_*.py       # All TFM modules
    │   │   └── ...
    │   │
    │   ├── ttk/               # TTK library
    │   │   ├── __init__.py
    │   │   ├── backends/
    │   │   │   ├── coregraphics_backend.py
    │   │   │   └── ...
    │   │   └── ...
    │   │
    │   └── python_packages/   # Third-party dependencies
    │       ├── pygments/      # Syntax highlighting
    │       ├── boto3/         # AWS S3 support
    │       ├── objc/          # PyObjC bridge
    │       ├── Cocoa/         # Cocoa bindings
    │       └── ...
    │
    └── Frameworks/             # Embedded frameworks
        └── Python.framework/   # Embedded Python interpreter
            └── Versions/
                └── 3.12/       # Python version
                    ├── Python  # Python library
                    ├── Resources/
                    └── lib/
                        └── python3.12/  # Standard library
```

### Key Components

**Info.plist** - Application metadata that macOS uses to identify and configure the app:
- Bundle identifier (com.tfm.app)
- Display name and version
- Icon file reference
- Minimum macOS version
- High resolution support

**MacOS/TFM** - The Objective-C launcher that:
- Creates NSApplication for macOS integration
- Initializes embedded Python interpreter
- Configures Python's sys.path
- Calls TFM's `create_window()` function
- Handles Dock menu and multi-window support

**Resources/** - All Python code and dependencies:
- TFM source code (from `src/`)
- TTK library (from `ttk/`)
- Python packages (from site-packages)
- Application icon

**Frameworks/Python.framework** - Self-contained Python interpreter:
- Python runtime library
- Standard library modules
- No dependency on system Python

## Customization

### Changing the Application Icon

1. Create or obtain a `.icns` file (macOS icon format)
2. Place it at `macos_app/resources/TFM.icns`
3. Rebuild the app with `./build.sh`

**Creating an .icns file:**

```bash
# From a PNG file (1024x1024 recommended)
mkdir TFM.iconset
sips -z 16 16     icon.png --out TFM.iconset/icon_16x16.png
sips -z 32 32     icon.png --out TFM.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out TFM.iconset/icon_32x32.png
sips -z 64 64     icon.png --out TFM.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out TFM.iconset/icon_128x128.png
sips -z 256 256   icon.png --out TFM.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out TFM.iconset/icon_256x256.png
sips -z 512 512   icon.png --out TFM.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out TFM.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out TFM.iconset/icon_512x512@2x.png
iconutil -c icns TFM.iconset
```

### Updating Python Version

To use a different Python version (e.g., Python 3.11 instead of 3.12):

1. Install the desired Python version as a framework
2. Modify `build.sh`:
   ```bash
   # Change this line:
   PYTHON_VERSION="3.12"
   # To:
   PYTHON_VERSION="3.11"
   ```
3. Rebuild the app

**Note:** Ensure the Python version is installed at `/Library/Frameworks/Python.framework/Versions/{version}/`

### Modifying the Launcher Code

The Objective-C launcher consists of two files:

**main.m** - Application entry point:
- Creates NSApplication
- Sets up application delegate
- Starts main event loop

**TFMAppDelegate.m** - Application delegate:
- Initializes Python interpreter
- Configures sys.path
- Launches TFM windows
- Handles Dock menu
- Manages app lifecycle

To modify the launcher:

1. Edit `src/main.m` or `src/TFMAppDelegate.m`
2. Rebuild with `./build.sh`

**Common modifications:**
- Change window title or size
- Add custom Dock menu items
- Modify Python initialization
- Add error handling

### Changing Bundle Identifier

The bundle identifier uniquely identifies your app to macOS.

1. Edit `resources/Info.plist.template`
2. Change the `CFBundleIdentifier` value:
   ```xml
   <key>CFBundleIdentifier</key>
   <string>com.yourcompany.tfm</string>
   ```
3. Rebuild the app

**Note:** Bundle identifiers should use reverse domain notation (com.company.app).

### Customizing App Metadata

Edit `resources/Info.plist.template` to change:

- **CFBundleName**: Short name (appears in menu bar)
- **CFBundleDisplayName**: Full name (appears in Finder)
- **CFBundleVersion**: Build version number
- **CFBundleShortVersionString**: User-visible version
- **NSHumanReadableCopyright**: Copyright notice
- **LSMinimumSystemVersion**: Minimum macOS version

After editing, rebuild with `./build.sh`.

## Troubleshooting

### Build Errors

#### "clang: command not found"

**Problem:** Xcode Command Line Tools not installed.

**Solution:**
```bash
xcode-select --install
```

Follow the prompts to install the tools, then try building again.

#### "Python.framework not found"

**Problem:** Python not installed as a framework, or wrong version.

**Solution:**
1. Check installed Python versions:
   ```bash
   ls /Library/Frameworks/Python.framework/Versions/
   ```
2. Install Python from python.org (not Homebrew)
3. Or modify `PYTHON_VERSION` in `build.sh` to match installed version

#### "Compilation failed" with framework errors

**Problem:** Python framework headers not found.

**Solution:**
1. Verify Python framework installation:
   ```bash
   ls /Library/Frameworks/Python.framework/Versions/3.12/include/
   ```
2. Reinstall Python from python.org if headers are missing

#### "Failed to collect dependencies"

**Problem:** Python packages not installed.

**Solution:**
```bash
cd ..  # Go to project root
pip install -r requirements.txt
cd macos_app
./build.sh
```

### Runtime Errors

#### "Failed to initialize Python interpreter"

**Problem:** Python.framework not properly embedded or wrong version.

**Diagnosis:**
1. Check Console.app for detailed error messages
2. Verify Python.framework exists in bundle:
   ```bash
   ls build/TFM.app/Contents/Frameworks/Python.framework/
   ```

**Solution:**
- Rebuild the app with correct Python version
- Ensure Python.framework was copied correctly

#### "Failed to import TFM module"

**Problem:** TFM source code not properly bundled or sys.path misconfigured.

**Diagnosis:**
1. Check Console.app for Python traceback
2. Verify TFM source exists in bundle:
   ```bash
   ls build/TFM.app/Contents/Resources/tfm/
   ```

**Solution:**
- Ensure all TFM source files are present in `src/`
- Rebuild the app
- Check for Python syntax errors in source files

#### "Module 'pygments' not found" or similar import errors

**Problem:** Python dependencies not bundled.

**Diagnosis:**
1. Check if package exists in bundle:
   ```bash
   ls build/TFM.app/Contents/Resources/python_packages/
   ```

**Solution:**
```bash
# Install missing packages
pip install pygments boto3 pyobjc-framework-Cocoa

# Rebuild
./build.sh
```

#### "Window creation failed"

**Problem:** CoreGraphics backend initialization error.

**Diagnosis:**
1. Check Console.app for Python exceptions
2. Verify TTK library is bundled:
   ```bash
   ls build/TFM.app/Contents/Resources/ttk/
   ```

**Solution:**
- Ensure TTK library exists in project root
- Rebuild the app
- Check for errors in CoreGraphics backend code

### Code Signing Issues

#### "Code signature invalid"

**Problem:** Code signing failed or identity not found.

**Solution:**
1. List available signing identities:
   ```bash
   security find-identity -v -p codesigning
   ```
2. Use correct identity:
   ```bash
   CODESIGN_IDENTITY="Developer ID Application: Your Name" ./build.sh
   ```
3. Or skip code signing for development:
   ```bash
   unset CODESIGN_IDENTITY
   ./build.sh
   ```

### DMG Creation Issues

#### "TFM.app not found"

**Problem:** Trying to create DMG before building app.

**Solution:**
```bash
# Build app first
./build.sh

# Then create DMG
./create_dmg.sh
```

### Getting More Information

**View detailed logs:**
1. Open Console.app
2. Search for "TFM" or "Python"
3. Look for error messages and stack traces

**Enable verbose build output:**
```bash
# Add -v flag to see detailed compilation
bash -x ./build.sh
```

**Check bundle contents:**
```bash
# List all files in bundle
find build/TFM.app -type f

# Check executable dependencies
otool -L build/TFM.app/Contents/MacOS/TFM
```

## Development Workflow

### Iterative Development

The app bundle is completely separate from development source files. You can continue developing TFM normally:

```bash
# Run TFM in terminal mode (no rebuild needed)
python3 tfm.py

# Run TFM in desktop mode (no rebuild needed)
python3 tfm.py --desktop

# Make changes to Python source files
vim src/tfm_main.py

# Test changes immediately
python3 tfm.py --desktop
```

Only rebuild the app bundle when you want to test the bundled version or create a release.

### Testing the Bundle

After building:

```bash
# Test the app
open build/TFM.app

# Test Dock integration
# 1. Right-click Dock icon
# 2. Select "New Window"
# 3. Verify new window opens

# Test multi-window
# 1. Open multiple windows
# 2. Close one window
# 3. Verify others remain open
```

### Release Process

1. Update version number in `resources/Info.plist.template`
2. Build the app: `./build.sh`
3. Test the app thoroughly
4. Create DMG: `./create_dmg.sh`
5. (Optional) Code sign: `CODESIGN_IDENTITY="..." ./build.sh`
6. Distribute `TFM-{version}.dmg`

## Additional Resources

- **TFM Documentation**: `../doc/`
- **TTK Documentation**: `../ttk/doc/`
- **Apple Bundle Documentation**: https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/
- **Python/C API**: https://docs.python.org/3/c-api/
- **PyObjC Documentation**: https://pyobjc.readthedocs.io/

## Support

For issues or questions:
1. Check this README's troubleshooting section
2. Check Console.app for error messages
3. Review the build script output
4. Open an issue on the project repository
