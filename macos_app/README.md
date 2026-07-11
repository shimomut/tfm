# TFM macOS Application Bundle

This directory contains the build system for creating a native macOS application bundle for TFM (Terminal File Manager). The bundle embeds a Python interpreter and provides a polished native macOS experience with full Dock integration.

## Architecture

**Single-Process, Single-Window**

The application uses a simple single-process architecture:
- One process runs the entire application
- One Python interpreter embedded in the process
- One TFM window per application instance
- Clean user experience with single Dock icon

## Documentation

Comprehensive documentation is available in the main project documentation directory:

- **[Build System Documentation](../doc/dev/MACOS_APP_BUILD_SYSTEM.md)** - Complete build system guide
  - Build philosophy and process
  - Python detection and component collection
  - Framework structure creation
  - Bundle optimization (pre-compilation, cleanup)
  - System independence verification
  - External program support
  - Troubleshooting and verification

- **[Testing Guide](../doc/dev/MACOS_APP_TESTING.md)** - Comprehensive testing procedures
  - Quick test checklist
  - Detailed test procedures (10 tests)
  - Troubleshooting guide
  - Issue reporting guidelines
  - Distribution preparation

## Table of Contents

- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Build Requirements](#build-requirements)
- [Build Scripts](#build-scripts)
- [Bundle Structure](#bundle-structure)
- [Customization](#customization)
- [Development Workflow](#development-workflow)

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

### Testing the App

```bash
# Launch the app
open macos_app/build/TFM.app

# Or double-click TFM.app in Finder

# Run manual tests (see Testing Guide)
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

## Project Structure

```
macos_app/
├── README.md                    # This file
├── build.sh                     # Main build script
├── create_dmg.sh               # DMG installer creator
├── test_single_process.sh      # Single-process architecture test
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
   - Copies the PuiKit framework (resolved via `import puikit`, typically from `../puikit`) to `Resources/puikit/`
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

### tools/collect_dependencies.py

Shared, platform-agnostic script that resolves the runtime dependency closure of
`requirements.txt` and copies those distributions (with their `.dist-info`
license text) into the bundle. Lives in the repo-root `tools/` directory because
it is shared with the Windows build (`windows_app/build.ps1`).

**What it does:**

1. Reads `requirements.txt` seeds and resolves their full runtime dependency
   closure from installed package metadata (honouring environment markers)
2. Copies each distribution file-for-file from its `RECORD`, preserving layout
3. Skips build/test tooling (pip, setuptools, pytest, …) and editable shims
4. `--include-deps-of NAME` pulls in a separately-bundled package's deps
   (e.g. PuiKit's numpy) without copying the package itself

**Usage:**

```bash
# Collect dependencies
python3 ../tools/collect_dependencies.py \
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
    │                           # - Version: 0.99
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
    │   ├── puikit/            # PuiKit framework
    │   │   ├── __init__.py
    │   │   ├── backends/
    │   │   │   ├── macos_backend.py
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
- Calls TFM's `cli_main()` function
- Handles application lifecycle

**Resources/** - All Python code and dependencies:
- TFM source code (from `src/`)
- PuiKit framework (from the installed `puikit` package)
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
3. Test the app thoroughly (see Testing Guide)
4. Create DMG: `./create_dmg.sh`
5. (Optional) Code sign: `CODESIGN_IDENTITY="..." ./build.sh`
6. Distribute `TFM-{version}.dmg`

## Quick Links

- **[Build System Documentation](../doc/dev/MACOS_APP_BUILD_SYSTEM.md)** - Complete build system guide
- **[Testing Guide](../doc/dev/MACOS_APP_TESTING.md)** - Comprehensive testing procedures
- **[Build Script](build.sh)** - Main build automation with inline documentation
- **[Source Code](src/)** - Objective-C implementation
- **[Project Makefile](../Makefile)** - Build automation targets

## Support

For issues or questions:
1. Check the Build System Documentation for troubleshooting
2. Check Console.app for error messages
3. Review the build script output
4. Open an issue on the project repository

