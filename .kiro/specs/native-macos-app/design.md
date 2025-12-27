# Design Document

## Overview

This design describes a native macOS application bundle for TFM that uses Objective-C to embed a Python interpreter and launch TFM with its CoreGraphics backend. The solution provides a polished native macOS experience while maintaining the ability to run TFM directly from Python during development.

The architecture consists of three main layers:
1. **Objective-C Launcher** - Minimal native code that embeds Python
2. **Embedded Python Runtime** - Self-contained Python interpreter and packages
3. **TFM Application** - Existing Python codebase with CoreGraphics backend

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     TFM.app Bundle                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────┐    │
│  │         Objective-C Launcher Layer            │    │
│  │  - NSApplication initialization               │    │
│  │  - Python/C API embedding                     │    │
│  │  - Dock menu integration                      │    │
│  │  - Multi-window management                    │    │
│  └───────────────┬───────────────────────────────┘    │
│                  │                                      │
│                  ▼                                      │
│  ┌───────────────────────────────────────────────┐    │
│  │         Embedded Python Runtime               │    │
│  │  - Python.framework (3.9+)                    │    │
│  │  - Standard library                           │    │
│  │  - Third-party packages (boto3, pygments)     │    │
│  │  - PyObjC frameworks                          │    │
│  └───────────────┬───────────────────────────────┘    │
│                  │                                      │
│                  ▼                                      │
│  ┌───────────────────────────────────────────────┐    │
│  │         TFM Application Layer                 │    │
│  │  - TFM Python source code                     │    │
│  │  - TTK library                                │    │
│  │  - CoreGraphics backend                       │    │
│  │  - File manager logic                         │    │
│  └───────────────────────────────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘

Shared NSApplication Instance:
┌──────────────────────────────────────────────────┐
│  NSApplication.sharedApplication() (Singleton)   │
│  ┌────────────────┬──────────────────────────┐  │
│  │ Objective-C    │ Python (via PyObjC)      │  │
│  │ - Dock menu    │ - NSWindow creation      │  │
│  │ - App delegate │ - Event handling         │  │
│  │ - Lifecycle    │ - CoreGraphics rendering │  │
│  └────────────────┴──────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Event Loop Coordination

The Objective-C launcher starts the NSApplication event loop, and Python code runs within that loop:

```
┌─────────────────────────────────────────────┐
│  Objective-C: [NSApp run]                   │
│  ┌───────────────────────────────────────┐  │
│  │  NSApplication Event Loop             │  │
│  │  ┌─────────────────────────────────┐  │  │
│  │  │  Python: create_window()        │  │  │
│  │  │  ┌───────────────────────────┐  │  │  │
│  │  │  │  CoreGraphics Backend     │  │  │  │
│  │  │  │  - Creates NSWindow       │  │  │  │
│  │  │  │  - Handles events         │  │  │  │
│  │  │  │  - Renders UI             │  │  │  │
│  │  │  └───────────────────────────┘  │  │  │
│  │  └─────────────────────────────────┘  │  │
│  │                                        │  │
│  │  Events dispatched to NSWindow        │  │
│  │  ↓                                     │  │
│  │  Python event handlers called         │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**Key Points:**
1. Objective-C starts the main event loop with `[NSApp run]`
2. Python code is called from within this event loop
3. Python creates NSWindow objects that integrate with the event loop
4. Events are dispatched to Python handlers automatically
5. No separate event loop needed in Python - uses NSApplication's loop

### Bundle Structure

```
TFM.app/
├── Contents/
│   ├── Info.plist                    # App metadata
│   ├── MacOS/
│   │   └── TFM                       # Objective-C launcher executable
│   ├── Resources/
│   │   ├── TFM.icns                  # Application icon
│   │   ├── tfm/                      # TFM Python source
│   │   │   ├── __init__.py
│   │   │   ├── tfm_main.py
│   │   │   ├── tfm_*.py
│   │   │   └── ...
│   │   ├── ttk/                      # TTK library
│   │   │   ├── __init__.py
│   │   │   ├── backends/
│   │   │   │   ├── coregraphics_backend.py
│   │   │   │   └── ...
│   │   │   └── ...
│   │   └── python_packages/          # Third-party packages
│   │       ├── pygments/
│   │       ├── boto3/
│   │       └── ...
│   └── Frameworks/
│       └── Python.framework/         # Embedded Python interpreter
│           └── Versions/
│               └── 3.12/
│                   ├── Python        # Python library
│                   ├── Resources/
│                   └── lib/
│                       └── python3.12/
```

## Components and Interfaces

### Component 1: Objective-C Launcher (main.m)

The launcher is responsible for initializing the macOS application, embedding Python, and starting TFM.

```objective-c
// main.m - Entry point
#import <Cocoa/Cocoa.h>
#import "TFMAppDelegate.h"

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        NSApplication *app = [NSApplication sharedApplication];
        TFMAppDelegate *delegate = [[TFMAppDelegate alloc] init];
        [app setDelegate:delegate];
        [app run];
    }
    return 0;
}
```

**Key Responsibilities:**
- Initialize NSApplication for macOS integration
- Create and set application delegate
- Run the main event loop

### Component 2: Application Delegate (TFMAppDelegate.m)

The delegate manages the application lifecycle and Python embedding.

```objective-c
// TFMAppDelegate.h
#import <Cocoa/Cocoa.h>

@interface TFMAppDelegate : NSObject <NSApplicationDelegate>
- (void)launchNewTFMWindow;
- (NSString *)getBundleResourcePath;
- (BOOL)initializePython;
- (void)shutdownPython;
@end

// TFMAppDelegate.m
#import "TFMAppDelegate.h"
#include <Python.h>

@implementation TFMAppDelegate {
    BOOL pythonInitialized;
    NSMutableArray *tfmWindows;
}

- (instancetype)init {
    self = [super init];
    if (self) {
        pythonInitialized = NO;
        tfmWindows = [[NSMutableArray alloc] init];
    }
    return self;
}

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    // Initialize Python
    if (![self initializePython]) {
        [self showErrorDialog:@"Failed to initialize Python interpreter"];
        [NSApp terminate:self];
        return;
    }
    
    // Launch first TFM window
    [self launchNewTFMWindow];
}

- (void)applicationWillTerminate:(NSNotification *)notification {
    [self shutdownPython];
}

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender {
    return YES;
}

- (NSMenu *)applicationDockMenu:(NSApplication *)sender {
    NSMenu *dockMenu = [[NSMenu alloc] init];
    
    NSMenuItem *newWindowItem = [[NSMenuItem alloc] 
        initWithTitle:@"New Window" 
        action:@selector(newDocument:) 
        keyEquivalent:@""];
    [newWindowItem setTarget:self];
    [dockMenu addItem:newWindowItem];
    
    return dockMenu;
}

- (void)newDocument:(id)sender {
    [self launchNewTFMWindow];
}

@end
```

**Key Responsibilities:**
- Manage application lifecycle (launch, terminate)
- Initialize and shutdown Python interpreter
- Handle Dock menu interactions
- Manage multiple TFM windows
- Display error dialogs

### Component 3: Python Initialization (TFMAppDelegate.m)

```objective-c
- (BOOL)initializePython {
    // Get bundle paths
    NSBundle *mainBundle = [NSBundle mainBundle];
    NSString *frameworksPath = [[mainBundle privateFrameworksPath] 
        stringByAppendingPathComponent:@"Python.framework/Versions/3.12"];
    NSString *resourcesPath = [mainBundle resourcePath];
    
    // Configure Python
    PyConfig config;
    PyConfig_InitPythonConfig(&config);
    
    // Set Python home to embedded framework
    PyConfig_SetBytesString(&config, &config.home, 
        [frameworksPath UTF8String]);
    
    // Set program name
    PyConfig_SetBytesString(&config, &config.program_name, 
        "TFM");
    
    // Initialize Python
    PyStatus status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    
    if (PyStatus_Exception(status)) {
        NSLog(@"Python initialization failed: %s", status.err_msg);
        return NO;
    }
    
    // Configure sys.path
    NSString *tfmPath = [resourcesPath stringByAppendingPathComponent:@"tfm"];
    NSString *ttkPath = [resourcesPath stringByAppendingPathComponent:@"ttk"];
    NSString *packagesPath = [resourcesPath 
        stringByAppendingPathComponent:@"python_packages"];
    
    PyRun_SimpleString("import sys");
    PyRun_SimpleString([[NSString stringWithFormat:
        @"sys.path.insert(0, '%@')", tfmPath] UTF8String]);
    PyRun_SimpleString([[NSString stringWithFormat:
        @"sys.path.insert(0, '%@')", ttkPath] UTF8String]);
    PyRun_SimpleString([[NSString stringWithFormat:
        @"sys.path.insert(0, '%@')", packagesPath] UTF8String]);
    
    pythonInitialized = YES;
    return YES;
}

- (void)shutdownPython {
    if (pythonInitialized) {
        Py_Finalize();
        pythonInitialized = NO;
    }
}
```

**Key Responsibilities:**
- Configure Python home directory
- Initialize Python interpreter
- Set up sys.path for module imports
- Handle initialization errors
- Clean up Python on shutdown

### Component 4: TFM Window Launcher (TFMAppDelegate.m)

```objective-c
- (void)launchNewTFMWindow {
    if (!pythonInitialized) {
        NSLog(@"Cannot launch TFM: Python not initialized");
        return;
    }
    
    // Import TFM main module
    PyObject *tfmModule = PyImport_ImportModule("tfm_main");
    if (!tfmModule) {
        PyErr_Print();
        [self showErrorDialog:@"Failed to import TFM module"];
        return;
    }
    
    // Get create_window function
    PyObject *createWindowFunc = PyObject_GetAttrString(tfmModule, 
        "create_window");
    if (!createWindowFunc || !PyCallable_Check(createWindowFunc)) {
        PyErr_Print();
        Py_XDECREF(createWindowFunc);
        Py_DECREF(tfmModule);
        [self showErrorDialog:@"TFM create_window function not found"];
        return;
    }
    
    // Call create_window()
    PyObject *result = PyObject_CallObject(createWindowFunc, NULL);
    if (!result) {
        PyErr_Print();
        [self showErrorDialog:@"Failed to create TFM window"];
    }
    
    // Clean up
    Py_XDECREF(result);
    Py_DECREF(createWindowFunc);
    Py_DECREF(tfmModule);
}

- (void)showErrorDialog:(NSString *)message {
    NSAlert *alert = [[NSAlert alloc] init];
    [alert setMessageText:@"TFM Error"];
    [alert setInformativeText:message];
    [alert setAlertStyle:NSAlertStyleCritical];
    [alert addButtonWithTitle:@"OK"];
    [alert runModal];
}
```

**Key Responsibilities:**
- Import TFM Python module
- Call TFM's window creation function
- Handle Python errors
- Display error dialogs to user

### Component 5: NSApplication Sharing Between Layers

The NSApplication instance created in Objective-C is automatically shared with Python through PyObjC. When Python code imports `Cocoa` or `AppKit`, it can access the shared application instance.

**Objective-C Side:**
```objective-c
// In main.m
NSApplication *app = [NSApplication sharedApplication];
// This creates the singleton NSApplication instance
```

**Python Side:**
```python
# In Python code (e.g., CoreGraphics backend)
from Cocoa import NSApplication

# Get the same shared instance
app = NSApplication.sharedApplication()
# This returns the SAME instance created in Objective-C
```

**Key Points:**
1. NSApplication is a singleton - only one instance exists per process
2. PyObjC bridges Objective-C objects to Python seamlessly
3. Both layers work with the same NSApplication instance
4. Python can access all NSApplication methods and properties
5. Windows created in Python automatically belong to the app

**Integration Flow:**
```
Objective-C Layer          Python Layer
─────────────────          ────────────
NSApplication.sharedApplication()
        │                         │
        └─────────────────────────┘
                  │
          Shared Instance
                  │
        ┌─────────┴─────────┐
        │                   │
   Dock Menu          NSWindow (TFM)
   App Delegate       CoreGraphics Backend
```

### Component 6: TFM Python Integration (tfm_main.py)

The TFM Python code needs a new entry point for the app bundle:

```python
# tfm_main.py

def create_window():
    """
    Create a new TFM window with CoreGraphics backend.
    Called by the Objective-C launcher.
    
    The CoreGraphics backend will automatically use the shared
    NSApplication instance created by the Objective-C launcher.
    """
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend
    from tfm_file_manager import FileManager
    
    # Create backend - it will use NSApplication.sharedApplication()
    backend = CoreGraphicsBackend(
        window_title="TFM - Terminal File Manager",
        font_name="Menlo",
        font_size=12,
        rows=40,
        cols=120
    )
    
    # Initialize backend
    backend.initialize()
    
    # Create file manager
    file_manager = FileManager(backend)
    
    # Run TFM
    file_manager.run()
    
    return True

def main():
    """
    Main entry point for command-line usage.
    Preserves existing behavior.
    """
    import sys
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--desktop', action='store_true',
                       help='Run in desktop mode with CoreGraphics')
    args = parser.parse_args()
    
    if args.desktop:
        create_window()
    else:
        # Terminal mode with curses
        from ttk.backends.curses_backend import CursesBackend
        from tfm_file_manager import FileManager
        
        backend = CursesBackend()
        backend.initialize()
        file_manager = FileManager(backend)
        file_manager.run()

if __name__ == '__main__':
    main()
```

**Key Responsibilities:**
- Provide `create_window()` function for app bundle
- Maintain existing `main()` for command-line usage
- Initialize appropriate backend based on mode
- Create and run FileManager instance

## Data Models

### Info.plist Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.tfm.app</string>
    
    <key>CFBundleName</key>
    <string>TFM</string>
    
    <key>CFBundleDisplayName</key>
    <string>Terminal File Manager</string>
    
    <key>CFBundleExecutable</key>
    <string>TFM</string>
    
    <key>CFBundleIconFile</key>
    <string>TFM.icns</string>
    
    <key>CFBundleVersion</key>
    <string>0.98</string>
    
    <key>CFBundleShortVersionString</key>
    <string>0.98</string>
    
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    
    <key>CFBundleSignature</key>
    <string>????</string>
    
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    
    <key>NSHighResolutionCapable</key>
    <true/>
    
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2025 TFM Developer</string>
    
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>
```

### Build Configuration

```bash
# build_config.sh - Build configuration variables

# Paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"
APP_NAME="TFM"
APP_BUNDLE="${BUILD_DIR}/${APP_NAME}.app"

# Python configuration
PYTHON_VERSION="3.12"
PYTHON_FRAMEWORK="/Library/Frameworks/Python.framework"

# Compiler settings
CC="clang"
CFLAGS="-framework Cocoa -framework Python -F${PYTHON_FRAMEWORK}/Versions/${PYTHON_VERSION}"
LDFLAGS="-rpath @executable_path/../Frameworks"

# Code signing (optional)
CODESIGN_IDENTITY=""  # Set to developer ID for signing
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Python Initialization Success

*For any* valid TFM.app bundle with embedded Python.framework, initializing Python with Py_InitializeFromConfig should succeed and return a non-exception PyStatus.

**Validates: Requirements 2.6**

### Property 2: Module Import Path Resolution

*For any* bundled TFM Python module, after Python initialization and sys.path configuration, importing the module should succeed without ImportError.

**Validates: Requirements 3.4**

### Property 3: Bundle Structure Completeness

*For any* built TFM.app bundle, all required directories (Contents/MacOS, Contents/Resources, Contents/Frameworks) and files (Info.plist, TFM executable, TFM.icns) should exist.

**Validates: Requirements 5.2, 5.3, 5.4, 5.5**

### Property 4: Python Home Configuration

*For any* embedded Python.framework path, setting Py_SetPythonHome to that path should result in Python using the embedded interpreter rather than system Python.

**Validates: Requirements 2.4**

### Property 5: TFM Window Creation

*For any* successful Python initialization, calling tfm_main.create_window() should create an NSWindow instance without raising exceptions.

**Validates: Requirements 4.3**

### Property 6: Dock Menu Availability

*For any* running TFM.app instance, right-clicking the Dock icon should display a menu containing at least the "New Window" item.

**Validates: Requirements 7.3**

### Property 7: Multi-Window Independence

*For any* two TFM windows created from the same app instance, closing one window should not affect the other window's operation.

**Validates: Requirements 8.3**

### Property 8: Development Mode Preservation

*For any* Python source file in the project, running "python3 tfm.py" should execute using the source file directly, not any bundled copy.

**Validates: Requirements 10.5**

### Property 9: Dependency Availability

*For any* Python package listed in requirements.txt, after bundle creation, importing that package from within the app should succeed.

**Validates: Requirements 11.6**

### Property 10: Error Dialog Display

*For any* Python initialization failure, the launcher should display an NSAlert dialog with an error message before terminating.

**Validates: Requirements 12.1**

### Property 11: Build Artifact Isolation

*For any* build process execution, all generated files should be created in the build directory, not in the source directory.

**Validates: Requirements 13.2**

### Property 12: Application Termination Cleanup

*For any* running TFM.app instance, when the application terminates, Py_Finalize() should be called exactly once.

**Validates: Requirements 14.6**

## Error Handling

### Python Initialization Errors

**Error Scenario:** Python.framework not found or incompatible version

**Handling Strategy:**
1. Check for Python.framework existence before initialization
2. Verify Python version matches expected version
3. Display NSAlert with specific error message
4. Log detailed error to system console
5. Terminate application gracefully

**Error Message Example:**
```
Title: "Python Initialization Failed"
Message: "The embedded Python interpreter could not be initialized. 
          Expected Python 3.12 but found Python 3.9.
          Please reinstall TFM."
```

### Module Import Errors

**Error Scenario:** TFM modules not found in bundle

**Handling Strategy:**
1. Catch ImportError when importing tfm_main
2. Check if sys.path includes Resources directory
3. Display NSAlert with troubleshooting steps
4. Log sys.path contents to console
5. Provide option to open Console.app for logs

**Error Message Example:**
```
Title: "TFM Module Not Found"
Message: "Could not import TFM modules. The application bundle may be corrupted.
          Check Console.app for detailed logs.
          Try reinstalling TFM."
```

### Window Creation Errors

**Error Scenario:** CoreGraphics backend fails to create window

**Handling Strategy:**
1. Catch Python exceptions from create_window()
2. Extract Python traceback using PyErr_Print()
3. Display NSAlert with error details
4. Allow user to try again or quit
5. Log full traceback to console

**Error Message Example:**
```
Title: "Window Creation Failed"
Message: "Failed to create TFM window: NSWindow initialization error.
          This may be due to insufficient permissions or display issues.
          
          [Try Again] [Quit]"
```

### Memory Management Errors

**Error Scenario:** Python object reference counting errors

**Handling Strategy:**
1. Use Py_XDECREF for all Python objects
2. Check for NULL before calling Py_DECREF
3. Clear Python error state after handling
4. Log reference count issues to console
5. Prevent crashes from double-free

**Code Pattern:**
```objective-c
PyObject *obj = PyObject_CallObject(func, NULL);
if (!obj) {
    PyErr_Print();  // Log error
    PyErr_Clear();  // Clear error state
    // Handle error...
}
Py_XDECREF(obj);  // Safe even if obj is NULL
```

## Testing Strategy

### Unit Testing

**Objective-C Unit Tests:**
- Test Python initialization with valid/invalid framework paths
- Test sys.path configuration with various bundle structures
- Test error dialog display with different error messages
- Test Dock menu creation and item handling
- Test application delegate lifecycle methods

**Python Unit Tests:**
- Test create_window() function with mocked backend
- Test main() function with different command-line arguments
- Test module imports from bundled paths
- Test error handling in window creation

### Integration Testing

**Bundle Structure Tests:**
- Verify all required files exist in built bundle
- Verify Info.plist contains correct metadata
- Verify Python.framework is properly embedded
- Verify TFM source files are copied correctly
- Verify icon file is in correct location

**Python Embedding Tests:**
- Test Python initialization from embedded framework
- Test module imports from bundled Resources
- Test sys.path includes all necessary directories
- Test Python can create CoreGraphics backend
- Test Python can import all required packages

**Multi-Window Tests:**
- Test creating multiple windows from Dock menu
- Test each window operates independently
- Test closing one window doesn't affect others
- Test application terminates when last window closes
- Test window list appears in Dock menu

### Build System Testing

**Build Script Tests:**
- Test build script creates correct bundle structure
- Test build script copies all necessary files
- Test build script compiles Objective-C code
- Test build script handles missing dependencies
- Test clean target removes all build artifacts

**Development Mode Tests:**
- Test python3 tfm.py runs from source
- Test python3 tfm.py --desktop uses CoreGraphics
- Test source modifications don't require rebuild
- Test bundle and source are independent

### Property-Based Testing

Each correctness property will be tested with property-based tests using Hypothesis:

**Property Test Example:**
```python
from hypothesis import given, strategies as st
import subprocess
import os

@given(st.text(min_size=1))
def test_module_import_path_resolution(module_name):
    """
    Property 2: Module Import Path Resolution
    For any bundled module, import should succeed after initialization.
    """
    # This would be run inside the app bundle context
    # Test that sys.path configuration allows imports
    pass
```

### Manual Testing Checklist

**First Launch:**
- [ ] App icon appears in Dock
- [ ] TFM window opens with CoreGraphics backend
- [ ] File manager UI renders correctly
- [ ] Keyboard input works
- [ ] Mouse input works

**Dock Integration:**
- [ ] Right-click Dock icon shows menu
- [ ] "New Window" creates second window
- [ ] Window list shows all open windows
- [ ] Clicking window name brings it to front
- [ ] Cmd+Q quits application

**Multi-Window:**
- [ ] Multiple windows can be opened
- [ ] Each window operates independently
- [ ] Closing one window doesn't close others
- [ ] Last window close terminates app

**Error Handling:**
- [ ] Missing Python.framework shows error dialog
- [ ] Missing TFM modules shows error dialog
- [ ] Window creation failure shows error dialog
- [ ] Error messages are clear and actionable

**Development Mode:**
- [ ] python3 tfm.py runs in terminal mode
- [ ] python3 tfm.py --desktop runs in desktop mode
- [ ] Source changes take effect immediately
- [ ] No rebuild needed for Python changes
