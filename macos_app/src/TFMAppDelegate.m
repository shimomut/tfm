//
//  TFMAppDelegate.m
//  TFM - Terminal File Manager
//
//  Application delegate implementation for TFM macOS app bundle.
//  Handles Python embedding, window lifecycle, and Dock integration.
//

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
        
        // Register for window close notifications
        [[NSNotificationCenter defaultCenter] addObserver:self
                                                 selector:@selector(windowWillClose:)
                                                     name:NSWindowWillCloseNotification
                                                   object:nil];
    }
    return self;
}

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    // Initialize Python interpreter
    if (![self initializePython]) {
        // Display detailed error dialog
        NSString *errorMessage = @"Failed to initialize Python interpreter.\n\n"
                                 @"Possible causes:\n"
                                 @"• Python.framework is missing or corrupted\n"
                                 @"• TFM source files are missing from the bundle\n"
                                 @"• Incompatible Python version\n\n"
                                 @"Please reinstall TFM or check Console.app for detailed error logs.";
        [self showErrorDialog:errorMessage];
        
        // Terminate application gracefully
        [NSApp terminate:self];
        return;
    }
    
    // Launch first TFM window
    [self launchNewTFMWindow];
}

- (void)applicationWillTerminate:(NSNotification *)notification {
    // Clean up Python interpreter
    [self shutdownPython];
}

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender {
    // Terminate the application when the last window is closed
    return YES;
}

- (NSMenu *)applicationDockMenu:(NSApplication *)sender {
    // Create custom Dock menu
    NSMenu *dockMenu = [[NSMenu alloc] init];
    
    // Add "New Window" menu item
    NSMenuItem *newWindowItem = [[NSMenuItem alloc] 
        initWithTitle:@"New Window" 
        action:@selector(newDocument:) 
        keyEquivalent:@""];
    [newWindowItem setTarget:self];
    [dockMenu addItem:newWindowItem];
    
    return dockMenu;
}

- (void)newDocument:(id)sender {
    // Handle "New Window" action from Dock menu
    [self launchNewTFMWindow];
}

#pragma mark - Python Management

- (BOOL)initializePython {
    // Get bundle paths
    NSBundle *mainBundle = [NSBundle mainBundle];
    NSString *frameworksPath = [[mainBundle privateFrameworksPath] 
        stringByAppendingPathComponent:@"Python.framework/Versions/3.12"];
    NSString *resourcesPath = [mainBundle resourcePath];
    
    // Verify Python.framework exists
    NSFileManager *fileManager = [NSFileManager defaultManager];
    if (![fileManager fileExistsAtPath:frameworksPath]) {
        NSLog(@"ERROR: Python.framework not found at path: %@", frameworksPath);
        return NO;
    }
    
    // Configure Python initialization
    PyConfig config;
    PyConfig_InitPythonConfig(&config);
    
    // Set Python home to embedded framework
    PyStatus homeStatus = PyConfig_SetBytesString(&config, &config.home, 
        [frameworksPath UTF8String]);
    if (PyStatus_Exception(homeStatus)) {
        NSLog(@"ERROR: Failed to set Python home: %s", homeStatus.err_msg);
        PyConfig_Clear(&config);
        return NO;
    }
    
    // Set program name
    PyStatus nameStatus = PyConfig_SetBytesString(&config, &config.program_name, 
        "TFM");
    if (PyStatus_Exception(nameStatus)) {
        NSLog(@"ERROR: Failed to set program name: %s", nameStatus.err_msg);
        PyConfig_Clear(&config);
        return NO;
    }
    
    // Initialize Python
    PyStatus status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    
    // Check for initialization errors
    if (PyStatus_Exception(status)) {
        NSLog(@"ERROR: Python initialization failed: %s", status.err_msg);
        NSLog(@"ERROR: Python home was set to: %@", frameworksPath);
        return NO;
    }
    
    // Configure sys.path to include bundled modules
    NSString *tfmPath = [resourcesPath stringByAppendingPathComponent:@"tfm"];
    NSString *ttkPath = [resourcesPath stringByAppendingPathComponent:@"ttk"];
    NSString *packagesPath = [resourcesPath 
        stringByAppendingPathComponent:@"python_packages"];
    
    // Verify required directories exist
    if (![fileManager fileExistsAtPath:tfmPath]) {
        NSLog(@"ERROR: TFM source directory not found at: %@", tfmPath);
        Py_Finalize();
        return NO;
    }
    if (![fileManager fileExistsAtPath:ttkPath]) {
        NSLog(@"ERROR: TTK library directory not found at: %@", ttkPath);
        Py_Finalize();
        return NO;
    }
    
    // Add paths to sys.path
    PyRun_SimpleString("import sys");
    
    NSString *tfmPathCmd = [NSString stringWithFormat:@"sys.path.insert(0, '%@')", tfmPath];
    PyRun_SimpleString([tfmPathCmd UTF8String]);
    
    NSString *ttkPathCmd = [NSString stringWithFormat:@"sys.path.insert(0, '%@')", ttkPath];
    PyRun_SimpleString([ttkPathCmd UTF8String]);
    
    NSString *packagesPathCmd = [NSString stringWithFormat:@"sys.path.insert(0, '%@')", packagesPath];
    PyRun_SimpleString([packagesPathCmd UTF8String]);
    
    // Check for Python errors after sys.path configuration
    if (PyErr_Occurred()) {
        NSLog(@"ERROR: Python error occurred during sys.path configuration");
        PyErr_Print();
        Py_Finalize();
        return NO;
    }
    
    pythonInitialized = YES;
    NSLog(@"Python initialized successfully");
    return YES;
}

- (void)shutdownPython {
    if (pythonInitialized) {
        Py_Finalize();
        pythonInitialized = NO;
        NSLog(@"Python finalized");
    }
}

- (void)dealloc {
    // Unregister from notifications
    [[NSNotificationCenter defaultCenter] removeObserver:self];
}

#pragma mark - Window Close Handling

- (void)windowWillClose:(NSNotification *)notification {
    // Sub-task 9.3: Remove window from tracking array on close
    NSWindow *closingWindow = [notification object];
    
    if ([tfmWindows containsObject:closingWindow]) {
        [tfmWindows removeObject:closingWindow];
        NSLog(@"Window closed, removed from tracking. Remaining windows: %lu", 
              (unsigned long)[tfmWindows count]);
        
        // Sub-task 9.3: Check if last window closed
        // Note: applicationShouldTerminateAfterLastWindowClosed handles termination
        if ([tfmWindows count] == 0) {
            NSLog(@"Last TFM window closed");
        }
    }
}

#pragma mark - Window Management

- (void)launchNewTFMWindow {
    // Sub-task 7.1: Check pythonInitialized flag
    if (!pythonInitialized) {
        NSLog(@"ERROR: Cannot launch TFM window - Python not initialized");
        [self showErrorDialog:@"Cannot create window: Python interpreter not initialized"];
        return;
    }
    
    // Get current window count before creating new window
    NSArray *windowsBefore = [[NSApplication sharedApplication] windows];
    NSInteger windowCountBefore = [windowsBefore count];
    
    // Sub-task 7.1: Import tfm_main module using PyImport_ImportModule
    PyObject *tfmModule = PyImport_ImportModule("tfm_main");
    if (!tfmModule) {
        // Sub-task 7.3: Handle import error
        NSLog(@"ERROR: Failed to import tfm_main module");
        PyErr_Print();
        [self showErrorDialog:@"Failed to import TFM module.\n\n"
                               @"The application bundle may be corrupted.\n"
                               @"Check Console.app for detailed logs.\n\n"
                               @"Try reinstalling TFM."];
        return;
    }
    
    // Sub-task 7.1: Get create_window function with PyObject_GetAttrString
    PyObject *createWindowFunc = PyObject_GetAttrString(tfmModule, "create_window");
    if (!createWindowFunc) {
        // Sub-task 7.3: Handle missing function error
        NSLog(@"ERROR: create_window function not found in tfm_main module");
        PyErr_Print();
        Py_DECREF(tfmModule);
        [self showErrorDialog:@"TFM create_window function not found.\n\n"
                               @"The application bundle may be corrupted.\n"
                               @"Check Console.app for detailed logs.\n\n"
                               @"Try reinstalling TFM."];
        return;
    }
    
    // Sub-task 7.1: Verify function is callable
    if (!PyCallable_Check(createWindowFunc)) {
        // Sub-task 7.3: Handle non-callable error
        NSLog(@"ERROR: create_window is not callable");
        Py_DECREF(createWindowFunc);
        Py_DECREF(tfmModule);
        [self showErrorDialog:@"TFM create_window is not a callable function.\n\n"
                               @"The application bundle may be corrupted.\n"
                               @"Check Console.app for detailed logs.\n\n"
                               @"Try reinstalling TFM."];
        return;
    }
    
    // Sub-task 7.2: Call PyObject_CallObject with create_window
    PyObject *result = PyObject_CallObject(createWindowFunc, NULL);
    
    // Sub-task 7.3: Check for NULL return from PyObject_CallObject
    if (!result) {
        // Sub-task 7.2: Check for Python exceptions with PyErr_Occurred
        if (PyErr_Occurred()) {
            // Sub-task 7.2: Print Python traceback with PyErr_Print
            NSLog(@"ERROR: Python exception occurred while creating TFM window");
            PyErr_Print();
        }
        
        // Sub-task 7.3: Display error dialog on failure
        [self showErrorDialog:@"Failed to create TFM window.\n\n"
                               @"This may be due to:\n"
                               @"• Missing dependencies\n"
                               @"• Display/graphics issues\n"
                               @"• Insufficient permissions\n\n"
                               @"Check Console.app for detailed error logs."];
        
        // Sub-task 7.2: Clean up Python object references
        Py_DECREF(createWindowFunc);
        Py_DECREF(tfmModule);
        return;
    }
    
    // Sub-task 7.3: Log error to console (success case)
    NSLog(@"TFM window created successfully");
    
    // Sub-task 9.2: Add window reference to tracking array
    // Get the newly created window(s)
    NSArray *windowsAfter = [[NSApplication sharedApplication] windows];
    NSInteger windowCountAfter = [windowsAfter count];
    
    // Track any new windows that were created
    if (windowCountAfter > windowCountBefore) {
        for (NSWindow *window in windowsAfter) {
            if (![windowsBefore containsObject:window]) {
                [tfmWindows addObject:window];
                NSLog(@"Tracking new TFM window: %@", [window title]);
            }
        }
    }
    
    // Sub-task 7.2: Clean up Python object references
    Py_XDECREF(result);
    Py_DECREF(createWindowFunc);
    Py_DECREF(tfmModule);
}

#pragma mark - Utility Methods

- (NSString *)getBundleResourcePath {
    NSBundle *mainBundle = [NSBundle mainBundle];
    return [mainBundle resourcePath];
}

- (void)showErrorDialog:(NSString *)message {
    NSAlert *alert = [[NSAlert alloc] init];
    [alert setMessageText:@"TFM Error"];
    [alert setInformativeText:message];
    [alert setAlertStyle:NSAlertStyleCritical];
    [alert addButtonWithTitle:@"OK"];
    [alert runModal];
}

@end
