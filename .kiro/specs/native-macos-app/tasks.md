# Implementation Plan: Native macOS App Bundle

## Overview

This implementation plan breaks down the creation of a native macOS application bundle for TFM into discrete, testable tasks. The implementation uses Objective-C to embed Python and launch TFM with its CoreGraphics backend, providing full native macOS integration including Dock menus and multi-window support.

**Note:** This is a fresh implementation using Objective-C to embed Python, replacing the previous py2app approach which encountered build issues.

## Tasks

- [x] 1. Set up project structure and build system
  - [x] 1.1 Create macos_app/ directory structure
    - Create macos_app/ in project root
    - Create macos_app/src/ for Objective-C source files
    - Create macos_app/resources/ for Info.plist template and icon
    - Create macos_app/build/ for build output (in .gitignore)
    - _Requirements: 9.1, 13.1_
  
  - [x] 1.2 Create Info.plist template
    - Create macos_app/resources/Info.plist.template
    - Include all required keys (CFBundleIdentifier, CFBundleName, etc.)
    - Use placeholder variables for version and paths
    - _Requirements: 5.5, 5.6, 5.7, 6.3, 6.4, 6.5, 6.6, 6.7_
  
  - [x] 1.3 Create build.sh shell script
    - Create macos_app/build.sh
    - Set up build configuration variables
    - Define paths for source and output
    - Define compiler flags for Cocoa and Python frameworks
    - Make script executable
    - _Requirements: 9.4, 9.5_

- [x] 2. Implement Objective-C launcher main entry point
  - [x] 2.1 Create main.m with NSApplication initialization
    - Create macos_app/src/main.m
    - Import Cocoa framework
    - Create NSApplication shared instance
    - Create and set application delegate
    - Start main event loop with [NSApp run]
    - _Requirements: 1.1, 14.1_

  - [ ]* 2.2 Write unit tests for main entry point
    - Test NSApplication is created
    - Test delegate is set correctly
    - _Requirements: 1.1_

- [x] 3. Implement TFMAppDelegate class
  - [x] 3.1 Create TFMAppDelegate.h header file
    - Create macos_app/src/TFMAppDelegate.h
    - Define TFMAppDelegate interface
    - Declare NSApplicationDelegate protocol conformance
    - Declare public methods (launchNewTFMWindow, initializePython, etc.)
    - Declare instance variables (pythonInitialized flag, window tracking array)
    - _Requirements: 1.1, 14.1_

  - [x] 3.2 Create TFMAppDelegate.m implementation skeleton
    - Create macos_app/src/TFMAppDelegate.m
    - Implement init method with instance variable initialization
    - Implement applicationDidFinishLaunching
    - Implement applicationWillTerminate
    - Implement applicationShouldTerminateAfterLastWindowClosed
    - _Requirements: 14.2, 14.3, 8.6_

  - [ ]* 3.3 Write unit tests for delegate lifecycle
    - Test init creates instance
    - Test lifecycle methods are called
    - _Requirements: 14.1_

- [x] 4. Implement Python initialization
  - [x] 4.1 Add Python/C API imports and configuration
    - Include Python.h header
    - Create initializePython method
    - Configure PyConfig with PyConfig_InitPythonConfig
    - _Requirements: 1.2, 1.3, 2.1_

  - [x] 4.2 Implement Python home directory configuration
    - Get bundle's Frameworks path
    - Locate Python.framework
    - Set config.home to framework path
    - _Requirements: 2.3, 2.4_

  - [x] 4.3 Implement Python initialization and sys.path setup
    - Call Py_InitializeFromConfig
    - Add TFM source directory to sys.path
    - Add TTK library directory to sys.path
    - Add python_packages directory to sys.path
    - _Requirements: 1.4, 2.5, 3.4_

  - [x] 4.4 Implement Python shutdown
    - Create shutdownPython method
    - Call Py_Finalize
    - Set pythonInitialized flag to NO
    - _Requirements: 1.6, 14.6_

  - [ ]* 4.5 Write property test for Python initialization
    - **Property 1: Python Initialization Success**
    - **Validates: Requirements 2.6**
    - Test with valid Python.framework path
    - Verify Py_InitializeFromConfig succeeds
    - Verify no exception PyStatus returned

  - [ ]* 4.6 Write property test for Python home configuration
    - **Property 4: Python Home Configuration**
    - **Validates: Requirements 2.4**
    - Test setting Py_SetPythonHome
    - Verify Python uses embedded interpreter
    - Verify sys.prefix points to embedded framework

- [x] 5. Implement error handling for Python initialization
  - [x] 5.1 Add error checking for Python initialization
    - Check PyStatus for exceptions
    - Log error message to console
    - Return NO on failure
    - _Requirements: 1.7, 12.1_

  - [x] 5.2 Implement error dialog display
    - Create showErrorDialog method
    - Use NSAlert for error display
    - Set alert style to critical
    - _Requirements: 12.4_

  - [x] 5.3 Handle initialization failure in applicationDidFinishLaunching
    - Check initializePython return value
    - Display error dialog on failure
    - Terminate application gracefully
    - _Requirements: 12.1, 12.6_

  - [ ]* 5.4 Write property test for error dialog display
    - **Property 10: Error Dialog Display**
    - **Validates: Requirements 12.1**
    - Test Python initialization failure
    - Verify NSAlert is displayed
    - Verify error message is shown

- [x] 6. Checkpoint - Ensure Python initialization works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement TFM window launching
  - [x] 7.1 Create launchNewTFMWindow method
    - Check pythonInitialized flag
    - Import tfm_main module using PyImport_ImportModule
    - Get create_window function with PyObject_GetAttrString
    - Verify function is callable
    - _Requirements: 4.1, 4.2_

  - [x] 7.2 Call Python create_window function
    - Call PyObject_CallObject with create_window
    - Check for Python exceptions with PyErr_Occurred
    - Print Python traceback with PyErr_Print
    - Clean up Python object references
    - _Requirements: 1.5, 4.3_

  - [x] 7.3 Handle window creation errors
    - Check for NULL return from PyObject_CallObject
    - Display error dialog on failure
    - Log error to console
    - _Requirements: 12.2, 12.3_

  - [ ]* 7.4 Write property test for TFM window creation
    - **Property 5: TFM Window Creation**
    - **Validates: Requirements 4.3**
    - Test calling create_window()
    - Verify NSWindow is created
    - Verify no exceptions raised

  - [ ]* 7.5 Write property test for module import
    - **Property 2: Module Import Path Resolution**
    - **Validates: Requirements 3.4**
    - Test importing tfm_main module
    - Verify import succeeds
    - Verify no ImportError raised

- [x] 8. Implement Dock menu integration
  - [x] 8.1 Implement applicationDockMenu delegate method
    - Create NSMenu instance
    - Add "New Window" menu item
    - Set target and action for menu item
    - Return dock menu
    - _Requirements: 7.2, 7.3_

  - [x] 8.2 Implement newDocument action method
    - Create newDocument: method
    - Call launchNewTFMWindow
    - _Requirements: 7.3, 8.2_

  - [ ]* 8.3 Write property test for Dock menu
    - **Property 6: Dock Menu Availability**
    - **Validates: Requirements 7.3**
    - Test applicationDockMenu returns menu
    - Verify "New Window" item exists
    - Verify menu item has correct action

- [x] 9. Implement multi-window support
  - [x] 9.1 Add window tracking
    - Create NSMutableArray for tracking windows
    - Initialize array in init method
    - _Requirements: 8.1_

  - [x] 9.2 Update launchNewTFMWindow to track windows
    - Add window reference to tracking array
    - _Requirements: 8.2_

  - [x] 9.3 Implement window close handling
    - Remove window from tracking array on close
    - Check if last window closed
    - _Requirements: 8.5, 8.6_

  - [ ]* 9.4 Write property test for multi-window independence
    - **Property 7: Multi-Window Independence**
    - **Validates: Requirements 8.3**
    - Test creating two windows
    - Close one window
    - Verify other window still operates

- [x] 10. Checkpoint - Ensure window management works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Create Python integration in tfm_main.py
  - [x] 11.1 Add create_window function to tfm_main.py
    - Add create_window() function at module level in src/tfm_main.py
    - Import necessary backend and FileManager classes
    - Create CoreGraphicsBackend instance with configuration
    - Initialize backend
    - Create FileManager instance
    - Run file manager
    - Return True on success
    - Handle exceptions and return False on failure
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 11.2 Verify main function preserves command-line usage
    - Check existing argparse setup is intact
    - Check --desktop flag handling works
    - Check terminal mode with curses backend works
    - Ensure no breaking changes to existing functionality
    - _Requirements: 10.1, 10.2, 10.3_

  - [ ]* 11.3 Write unit tests for create_window
    - Test create_window creates backend
    - Test create_window creates FileManager
    - Test create_window returns True on success
    - Test create_window returns False on exception

  - [ ]* 11.4 Write property test for development mode
    - **Property 8: Development Mode Preservation**
    - **Validates: Requirements 10.5**
    - Test running python3 tfm.py
    - Verify uses source files directly
    - Verify not using bundled copies

- [x] 12. Implement build script compilation and bundling
  - [x] 12.1 Implement compilation step in build.sh
    - Compile main.m and TFMAppDelegate.m with clang
    - Link with Cocoa and Python frameworks
    - Set rpath for framework loading (@executable_path/../Frameworks)
    - Output executable to build directory
    - Add error checking for compilation failures
    - _Requirements: 9.5, 9.6_

  - [x] 12.2 Implement bundle structure creation in build.sh
    - Create TFM.app/Contents/MacOS directory
    - Create TFM.app/Contents/Resources directory
    - Create TFM.app/Contents/Frameworks directory
    - Copy executable to MacOS directory
    - Set executable permissions on launcher
    - _Requirements: 5.2, 5.3, 5.4, 9.7_

  - [x] 12.3 Implement resource copying in build.sh
    - Copy TFM Python source from src/ to Resources/tfm/
    - Copy TTK library from ttk/ to Resources/ttk/
    - Copy Python packages to Resources/python_packages/
    - Copy application icon to Resources/
    - Preserve directory structure and __init__.py files
    - _Requirements: 3.1, 3.2, 3.3, 6.2_

  - [x] 12.4 Implement Python.framework embedding in build.sh
    - Locate system Python.framework
    - Copy Python.framework to Frameworks directory
    - Preserve framework structure (Versions/3.12/)
    - Update framework install names if needed
    - _Requirements: 2.1, 2.2_

  - [x] 12.5 Implement Info.plist generation in build.sh
    - Read Info.plist.template
    - Substitute version number from VERSION file or constant
    - Substitute bundle identifier, name, executable name
    - Copy processed Info.plist to Contents directory
    - Validate Info.plist is valid XML
    - _Requirements: 5.5, 5.6, 5.7, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [ ]* 12.6 Write property test for bundle structure
    - **Property 3: Bundle Structure Completeness**
    - **Validates: Requirements 5.2, 5.3, 5.4, 5.5**
    - Test all required directories exist
    - Test all required files exist
    - Test Info.plist is valid XML

  - [ ]* 12.7 Write property test for build artifact isolation
    - **Property 11: Build Artifact Isolation**
    - **Validates: Requirements 13.2**
    - Test build creates files in build directory
    - Verify no files created in source directory

- [x] 13. Implement dependency bundling
  - [x] 13.1 Create script to collect Python dependencies
    - Create macos_app/collect_dependencies.sh or Python script
    - Read requirements.txt
    - Locate site-packages for each dependency
    - Copy to Resources/python_packages with proper structure
    - Handle package metadata (.dist-info directories)
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 13.2 Verify PyObjC frameworks are included
    - Check for objc module in python_packages
    - Check for Cocoa module
    - Check for AppKit module
    - Add to dependency collection if missing
    - _Requirements: 11.4_

  - [ ]* 13.3 Write property test for dependency availability
    - **Property 9: Dependency Availability**
    - **Validates: Requirements 11.6**
    - Test importing each required package
    - Verify imports succeed from bundle

- [x] 14. Checkpoint - Ensure build system works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Add code signing support (optional)
  - [x] 15.1 Add code signing to build script
    - Accept CODESIGN_IDENTITY parameter
    - Check if identity is provided
    - Sign executable if identity provided
    - _Requirements: 15.1, 15.2_

  - [x] 15.2 Implement framework signing
    - Sign Python.framework
    - Sign any other embedded frameworks
    - _Requirements: 15.4_

  - [x] 15.3 Implement bundle signing
    - Sign complete app bundle
    - Verify signature with codesign -v
    - _Requirements: 15.3_

- [x] 16. Create Makefile integration
  - [x] 16.1 Add macos-app target to Makefile
    - Add target that calls macos_app/build.sh
    - Add help text for the target
    - _Requirements: 9.4_

  - [x] 16.2 Add macos-app-clean target
    - Remove macos_app/build/ directory
    - Remove any temporary build files
    - _Requirements: 13.4_

  - [x] 16.3 Add macos-app-install target
    - Copy TFM.app to /Applications
    - Provide option to install to ~/Applications
    - _Requirements: 13.5_

- [x] 17. Create DMG installer
  - [x] 17.1 Create create_dmg.sh script
    - Create macos_app/create_dmg.sh
    - Create temporary DMG directory
    - Copy TFM.app to DMG directory
    - Create INSTALL.md if not exists
    - Copy INSTALL.md to DMG directory
    - Create DMG with hdiutil
    - Make script executable
    - _Requirements: 13.6_

  - [x] 17.2 Add version number to DMG filename
    - Extract version from Info.plist or VERSION constant
    - Name DMG as TFM-{version}.dmg
    - _Requirements: 13.7_

  - [x] 17.3 Add macos-dmg target to Makefile
    - Call create_dmg.sh script
    - Depend on macos-app target
    - _Requirements: 13.6_

- [x] 18. Create documentation
  - [x] 18.1 Create macos_app/README.md
    - Explain project structure (src/, resources/, build/)
    - Document build requirements (Xcode Command Line Tools, Python 3.9+)
    - Provide build instructions (running build.sh)
    - Document what each script does
    - _Requirements: 16.1, 16.3_

  - [x] 18.2 Document Xcode Command Line Tools installation
    - Provide xcode-select --install command
    - Explain what gets installed (clang, frameworks)
    - Explain why it's needed (Cocoa framework, compiler)
    - _Requirements: 16.2_

  - [x] 18.3 Document bundle structure
    - Explain Contents directory layout
    - Document what goes in MacOS/ (executable)
    - Document what goes in Resources/ (Python code, icon)
    - Document what goes in Frameworks/ (Python.framework)
    - _Requirements: 16.4_

  - [x] 18.4 Document customization options
    - How to change app icon (replace TFM.icns)
    - How to update Python version (modify build.sh)
    - How to modify launcher code (edit .m files)
    - How to change bundle identifier (edit Info.plist.template)
    - _Requirements: 16.5, 16.6_

  - [x] 18.5 Create troubleshooting guide
    - Common build errors and solutions
    - Python initialization errors (missing framework, wrong version)
    - Module import errors (missing dependencies, wrong sys.path)
    - Compilation errors (missing Xcode tools, framework not found)
    - _Requirements: 16.7_

- [x] 19. Final integration testing
  - [x]* 19.1 Test complete build process
    - Run build.sh from clean state
    - Verify TFM.app is created
    - Verify app launches successfully

  - [x]* 19.2 Test development mode still works
    - Run python3 tfm.py
    - Run python3 tfm.py --desktop
    - Verify both modes work

  - [x]* 19.3 Test multi-window functionality
    - Launch app
    - Create second window from Dock
    - Verify both windows work independently
    - Close one window, verify other continues

  - [x]* 19.4 Test Dock integration
    - Right-click Dock icon
    - Verify menu appears
    - Verify "New Window" works
    - Verify window list appears

  - [x]* 19.5 Test error handling
    - Test with missing Python.framework
    - Test with missing TFM modules
    - Verify error dialogs appear

- [x] 20. Optimize bundle size
  - [x] 20.1 Remove unnecessary files from embedded Python
    - Remove Python.app GUI launcher (~172KB)
    - Remove development tools (idle, pip, pydoc, python-config) (~60KB)
    - Remove pkg-config files (~8KB)
    - Remove Resources directory entirely (~176KB)
    - Log all cleanup operations
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.7_

  - [x] 20.2 Create framework-level bin symlink
    - Create Python.framework/bin -> Versions/Current/bin symlink
    - Use ln -sfn to prevent following existing symlinks
    - Required for external programs to find bundled Python
    - _Requirements: 17.6_

  - [x] 20.3 Create verification script
    - Create temp/verify_cleanup.sh
    - Check that unnecessary files are removed
    - Check that essential files exist
    - Check framework-level symlinks exist
    - _Requirements: 17.7_

  - [x] 20.4 Document cleanup process
    - Create macos_app/doc/UNNECESSARY_FILES_CLEANUP.md
    - Document what files are removed and why
    - Document space savings (~400KB total)
    - Document verification process
    - _Requirements: 17.7_

- [x] 21. Implement Python pre-compilation
  - [x] 21.1 Add pre-compilation step to build script
    - Use Python's compileall module
    - Pre-compile TFM source files
    - Pre-compile TTK library files
    - Use -q flag for quiet mode
    - _Requirements: 18.1, 18.2, 18.4_

  - [x] 21.2 Verify bytecode generation
    - Check __pycache__ directories are created
    - Check .pyc files exist for all .py files
    - Verify version-specific naming (.cpython-313.pyc)
    - _Requirements: 18.3, 18.6_

  - [x] 21.3 Keep source files alongside bytecode
    - Keep both .py and .pyc files in bundle
    - Preserve for debugging and introspection
    - Document trade-off in documentation
    - _Requirements: 18.5_

  - [x] 21.4 Document pre-compilation
    - Create macos_app/doc/PYTHON_PRECOMPILATION.md
    - Document benefits (faster startup, consistent performance)
    - Document file structure with __pycache__
    - Document why source files are kept
    - _Requirements: 18.7_

- [x] 22. Final checkpoint - Complete implementation
  - All automated tests passed successfully
  - Comprehensive documentation created
  - Bundle size optimized (~400KB savings)
  - Python pre-compilation implemented
  - Ready for manual testing and distribution

## Notes

- Tasks marked with `*` are optional testing tasks that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Build system is command-line only, no Xcode IDE required
- Development mode (python3 tfm.py) remains fully functional throughout
- This implementation replaces the previous py2app approach which had build issues
- All tasks start from scratch - no existing Objective-C code or macos_app directory exists yet
