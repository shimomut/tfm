# Requirements Document

## Introduction

This specification defines a native macOS application bundle for TFM (Terminal File Manager) that embeds a Python interpreter and launches TFM with its CoreGraphics backend. The solution uses Objective-C to create a minimal launcher that initializes Python and executes TFM's existing Python codebase, providing a polished native macOS experience while preserving the ability to run TFM directly from the command line during development.

## Glossary

- **TFM**: Terminal File Manager - the dual-pane file manager application
- **App Bundle**: macOS application package (.app) containing executable and resources
- **Embedded Python**: Python interpreter bundled within the app bundle
- **CoreGraphics Backend**: TFM's native macOS rendering backend using CoreGraphics/Cocoa
- **Launcher**: Objective-C executable that initializes Python and starts TFM
- **Python/C API**: C API for embedding Python interpreter in applications
- **NSApplication**: macOS application class providing app lifecycle and Dock integration
- **Command Line Tools**: Xcode command-line compiler tools (clang, xcodebuild)
- **Development Mode**: Running TFM directly with Python interpreter (python3 tfm.py)
- **Production Mode**: Running TFM as a bundled macOS application (TFM.app)

## Requirements

### Requirement 1: Objective-C Launcher Implementation

**User Story:** As a developer, I want a minimal Objective-C launcher that embeds Python, so that TFM can run as a native macOS application without py2app dependencies.

#### Acceptance Criteria

1. THE Launcher SHALL be implemented in Objective-C using standard macOS frameworks
2. THE Launcher SHALL use Python/C API to embed the Python interpreter
3. THE Launcher SHALL initialize Python with PyConfig_InitPythonConfig and Py_InitializeFromConfig
4. THE Launcher SHALL configure PYTHONPATH to locate bundled TFM modules
5. THE Launcher SHALL execute TFM's main entry point using PyRun_SimpleString or equivalent
6. THE Launcher SHALL properly finalize Python with Py_Finalize on exit
7. THE Launcher SHALL handle Python initialization errors gracefully with error messages

### Requirement 2: Python Interpreter Embedding

**User Story:** As a user, I want Python embedded in the app bundle, so that I don't need to install Python separately to run TFM.

#### Acceptance Criteria

1. THE App_Bundle SHALL include Python.framework in Contents/Frameworks/
2. THE Python_Framework SHALL be version 3.9 or later
3. THE Launcher SHALL locate the embedded Python.framework at runtime
4. THE Launcher SHALL set Py_SetPythonHome to the embedded framework path
5. THE Launcher SHALL configure sys.path to include bundled TFM modules
6. THE Launcher SHALL verify Python initialization succeeded before executing TFM code
7. THE App_Bundle SHALL be self-contained and not depend on system Python

### Requirement 3: TFM Source Code Bundling

**User Story:** As a developer, I want TFM's Python source code bundled in the app, so that the application is self-contained and portable.

#### Acceptance Criteria

1. THE App_Bundle SHALL include all TFM Python source files in Contents/Resources/
2. THE App_Bundle SHALL include the TTK library in Contents/Resources/
3. THE App_Bundle SHALL include all required Python dependencies
4. THE Launcher SHALL add Contents/Resources to sys.path before importing TFM
5. THE Bundled_Code SHALL be a copy of the source, not the original development files
6. THE Build_Process SHALL preserve Python module structure and __init__.py files
7. THE App_Bundle SHALL include all necessary data files and resources

### Requirement 4: CoreGraphics Backend Integration

**User Story:** As a user, I want TFM to use its CoreGraphics backend automatically, so that I get a native macOS desktop experience.

#### Acceptance Criteria

1. THE Launcher SHALL initialize TFM with the CoreGraphics backend enabled
2. THE Launcher SHALL pass appropriate arguments to TFM to enable desktop mode
3. THE CoreGraphics_Backend SHALL create NSWindow instances for TFM windows
4. THE App SHALL support TFM's existing CoreGraphics rendering capabilities
5. THE App SHALL handle keyboard and mouse events through TFM's event system
6. THE App SHALL support all TFM features available in desktop mode
7. THE Launcher SHALL NOT interfere with TFM's window management

### Requirement 5: macOS Application Bundle Structure

**User Story:** As a user, I want a properly structured macOS app bundle, so that the application integrates seamlessly with macOS.

#### Acceptance Criteria

1. THE App_Bundle SHALL follow standard macOS bundle structure with Contents/ directory
2. THE App_Bundle SHALL include Contents/MacOS/ with the launcher executable
3. THE App_Bundle SHALL include Contents/Resources/ with Python code and resources
4. THE App_Bundle SHALL include Contents/Frameworks/ with Python.framework
5. THE App_Bundle SHALL include Contents/Info.plist with proper metadata
6. THE Info.plist SHALL specify CFBundleIdentifier as com.tfm.app
7. THE Info.plist SHALL specify CFBundleExecutable pointing to the launcher

### Requirement 6: Application Icon and Metadata

**User Story:** As a user, I want TFM to have a proper application icon and metadata, so that it looks professional in Finder and the Dock.

#### Acceptance Criteria

1. THE App_Bundle SHALL include an application icon in .icns format
2. THE Icon SHALL be located at Contents/Resources/TFM.icns
3. THE Info.plist SHALL reference the icon with CFBundleIconFile
4. THE Info.plist SHALL specify CFBundleName as "TFM"
5. THE Info.plist SHALL specify CFBundleDisplayName as "Terminal File Manager"
6. THE Info.plist SHALL specify CFBundleVersion and CFBundleShortVersionString
7. THE Info.plist SHALL specify NSHumanReadableCopyright with appropriate text

### Requirement 7: Dock Integration

**User Story:** As a user, I want full macOS Dock integration, so that I can manage TFM windows and access features from the Dock.

#### Acceptance Criteria

1. THE App SHALL appear in the Dock when running
2. THE App SHALL support right-click Dock menu with standard items
3. THE Dock_Menu SHALL include "New Window" option to launch additional TFM windows
4. THE Dock_Menu SHALL list all open TFM windows
5. THE App SHALL support clicking window names in Dock menu to bring them to front
6. THE App SHALL implement NSApplicationDelegate for Dock menu customization
7. THE App SHALL handle applicationDockMenu: to provide custom menu items

### Requirement 8: Multi-Window Support

**User Story:** As a user, I want to open multiple TFM windows, so that I can work with multiple directories simultaneously.

#### Acceptance Criteria

1. THE App SHALL support launching multiple TFM windows from the Dock menu
2. WHEN a user selects "New Window" from Dock menu THEN the App SHALL create a new TFM instance
3. THE App SHALL allow each window to operate independently
4. THE App SHALL maintain separate Python state for each window if needed
5. THE App SHALL properly handle window closing without terminating the app
6. THE App SHALL terminate when the last window is closed
7. THE App SHALL support Cmd+N keyboard shortcut for new windows

### Requirement 9: Command-Line Build System

**User Story:** As a developer, I want to build the app from the command line, so that I don't need Xcode IDE and can automate builds.

#### Acceptance Criteria

1. THE Build_System SHALL use command-line tools only (clang, xcodebuild)
2. THE Build_System SHALL NOT require Xcode IDE to be installed
3. THE Build_System SHALL work with Xcode Command Line Tools only
4. THE Build_System SHALL provide a shell script for building the app
5. THE Build_Script SHALL compile Objective-C source files
6. THE Build_Script SHALL create the app bundle structure
7. THE Build_Script SHALL copy all necessary files into the bundle

### Requirement 10: Development Mode Preservation

**User Story:** As a developer, I want to continue running TFM directly from Python, so that I can iterate quickly during development.

#### Acceptance Criteria

1. THE Project SHALL maintain the existing tfm.py entry point
2. THE Developer SHALL be able to run "python3 tfm.py" for terminal mode
3. THE Developer SHALL be able to run "python3 tfm.py --desktop" for desktop mode
4. THE Development_Mode SHALL NOT require building the app bundle
5. THE Development_Mode SHALL use the source files directly, not bundled copies
6. THE App_Bundle SHALL be completely separate from development source files
7. THE Build_Process SHALL NOT modify or move original source files

### Requirement 11: Python Dependency Management

**User Story:** As a developer, I want Python dependencies bundled correctly, so that the app works without external pip installations.

#### Acceptance Criteria

1. THE App_Bundle SHALL include all Python packages from requirements.txt
2. THE App_Bundle SHALL include pygments for syntax highlighting
3. THE App_Bundle SHALL include boto3 for AWS S3 support
4. THE App_Bundle SHALL include PyObjC frameworks for macOS integration
5. THE Build_Process SHALL copy site-packages into the bundle
6. THE Launcher SHALL configure sys.path to find bundled packages
7. THE App SHALL verify required packages are available at startup

### Requirement 12: Error Handling and Diagnostics

**User Story:** As a user, I want clear error messages if the app fails to start, so that I can troubleshoot issues.

#### Acceptance Criteria

1. WHEN Python initialization fails THEN the Launcher SHALL display an error dialog
2. WHEN TFM modules are missing THEN the Launcher SHALL display a descriptive error
3. WHEN Python version is incompatible THEN the Launcher SHALL display version requirements
4. THE Error_Messages SHALL use NSAlert for native macOS dialogs
5. THE Launcher SHALL log errors to system console for debugging
6. THE Launcher SHALL provide actionable error messages with solutions
7. THE App SHALL gracefully handle missing dependencies with clear messages

### Requirement 13: Build Artifact Management

**User Story:** As a developer, I want build artifacts organized properly, so that I can easily distribute the app.

#### Acceptance Criteria

1. THE Build_Process SHALL create output in a dedicated build directory
2. THE Build_Directory SHALL be separate from source code directories
3. THE Build_Process SHALL create TFM.app in the build output directory
4. THE Build_Process SHALL support "make clean" to remove build artifacts
5. THE Build_Process SHALL support "make install" to copy app to /Applications
6. THE Build_Process SHALL create a DMG installer for distribution
7. THE Build_Process SHALL include version number in DMG filename

### Requirement 14: Application Lifecycle Management

**User Story:** As a user, I want proper application lifecycle behavior, so that TFM behaves like a native macOS app.

#### Acceptance Criteria

1. THE App SHALL implement NSApplicationDelegate protocol
2. THE App SHALL handle applicationDidFinishLaunching to initialize TFM
3. THE App SHALL handle applicationWillTerminate to clean up Python
4. THE App SHALL support Cmd+Q to quit the application
5. THE App SHALL support "Quit" from Dock menu
6. THE App SHALL properly release resources on termination
7. THE App SHALL save window state before quitting if applicable

### Requirement 15: Code Signing and Notarization Support

**User Story:** As a developer, I want the app to support code signing, so that users don't get security warnings on macOS.

#### Acceptance Criteria

1. THE Build_Process SHALL support optional code signing with developer certificate
2. THE Build_Script SHALL accept code signing identity as a parameter
3. THE Build_Process SHALL sign the app bundle if identity is provided
4. THE Build_Process SHALL sign embedded frameworks and executables
5. THE Build_Process SHALL create a signed DMG if requested
6. THE Build_Process SHALL support notarization workflow for distribution
7. THE Build_Process SHALL work without code signing for development builds

### Requirement 16: Documentation and Examples

**User Story:** As a developer, I want clear documentation, so that I can build and modify the app bundle.

#### Acceptance Criteria

1. THE Project SHALL include a README for the macOS app build process
2. THE Documentation SHALL explain how to install Xcode Command Line Tools
3. THE Documentation SHALL provide step-by-step build instructions
4. THE Documentation SHALL explain the app bundle structure
5. THE Documentation SHALL document how to customize the launcher
6. THE Documentation SHALL explain how to update bundled Python version
7. THE Documentation SHALL include troubleshooting guide for common issues
