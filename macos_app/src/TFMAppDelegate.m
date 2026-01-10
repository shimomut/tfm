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
}

- (instancetype)init {
    self = [super init];
    if (self) {
        pythonInitialized = NO;
    }
    return self;
}

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    // Single-process, single-window architecture
    NSLog(@"Launching TFM in single-process mode");
    
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
    
    // Launch TFM window in current process
    [self launchTFMWindow];
}

- (void)applicationWillTerminate:(NSNotification *)notification {
    // Clean up Python interpreter
    [self shutdownPython];
}

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender {
    // Single-window mode: terminate when window closes
    return YES;
}

- (NSMenu *)applicationDockMenu:(NSApplication *)sender {
    // Single-window mode: no custom Dock menu needed
    return nil;
}

#pragma mark - Python Management

- (BOOL)initializePython {
    // Get bundle paths
    NSBundle *mainBundle = [NSBundle mainBundle];
    // Use "Current" symlink to support any Python version
    NSString *frameworksPath = [[mainBundle privateFrameworksPath] 
        stringByAppendingPathComponent:@"Python.framework/Versions/Current"];
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
    // Add Resources directory to sys.path so Python can find tfm and ttk packages
    NSString *packagesPath = [resourcesPath 
        stringByAppendingPathComponent:@"python_packages"];
    
    // Verify required directories exist
    NSString *tfmPath = [resourcesPath stringByAppendingPathComponent:@"tfm"];
    NSString *ttkPath = [resourcesPath stringByAppendingPathComponent:@"ttk"];
    
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
    // Add Resources directory so Python can import tfm and ttk packages
    PyRun_SimpleString("import sys");
    
    NSString *resourcesPathCmd = [NSString stringWithFormat:@"sys.path.insert(0, '%@')", resourcesPath];
    PyRun_SimpleString([resourcesPathCmd UTF8String]);
    
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
    // Clean up if needed
    [super dealloc];
}

#pragma mark - Window Management

- (void)launchTFMWindow {
    // Launch TFM window in current process (single-window mode)
    
    if (!pythonInitialized) {
        NSLog(@"ERROR: Cannot launch TFM window - Python not initialized");
        exit(1);
        return;
    }
    
    // Set up environment PATH to include common binary locations
    // This ensures SSH ProxyCommand can find tools like 'aws', 'gcloud', etc.
    [self setupEnvironmentPath];
    
    // Import tfm_main module
    PyObject *tfmModule = PyImport_ImportModule("tfm.tfm_main");
    if (!tfmModule) {
        NSLog(@"ERROR: Failed to import tfm.tfm_main module");
        PyErr_Print();
        exit(1);
        return;
    }
    
    // Set up sys.argv to simulate --desktop mode
    PyRun_SimpleString("import sys");
    PyRun_SimpleString("sys.argv = ['TFM', '--desktop']");
    
    // Get cli_main function
    PyObject *cliMainFunc = PyObject_GetAttrString(tfmModule, "cli_main");
    if (!cliMainFunc || !PyCallable_Check(cliMainFunc)) {
        NSLog(@"ERROR: cli_main function not found or not callable");
        Py_XDECREF(cliMainFunc);
        Py_DECREF(tfmModule);
        exit(1);
        return;
    }
    
    // Call cli_main() - this will block until the window is closed
    NSLog(@"Calling cli_main()");
    PyObject *result = PyObject_CallObject(cliMainFunc, NULL);
    
    if (!result) {
        NSLog(@"ERROR: cli_main() failed");
        PyErr_Print();
    }
    
    // Clean up
    Py_XDECREF(result);
    Py_DECREF(cliMainFunc);
    Py_DECREF(tfmModule);
    
    // When cli_main() returns, the window was closed
    NSLog(@"cli_main() returned, terminating application");
    
    // Use exit() instead of [NSApp terminate:self] to avoid issues
    // when running directly from command line
    exit(0);
}

- (void)setupEnvironmentPath {
    // Get current PATH
    NSString *currentPath = [[[NSProcessInfo processInfo] environment] objectForKey:@"PATH"];
    if (!currentPath) {
        currentPath = @"";
    }
    
    // Common locations for CLI tools (aws, gcloud, etc.)
    NSArray *additionalPaths = @[
        @"/usr/local/bin",           // Homebrew (Intel Mac)
        @"/usr/bin",                 // System binaries
        @"/bin",                     // Core system binaries
        [@"~/bin" stringByExpandingTildeInPath],                    // User binaries
        [@"~/.local/bin" stringByExpandingTildeInPath]              // Python user binaries
    ];
    
    // Build new PATH by prepending additional paths
    NSMutableArray *pathComponents = [NSMutableArray array];
    
    // Add additional paths first (higher priority)
    for (NSString *path in additionalPaths) {
        // Check if path exists before adding
        BOOL isDirectory;
        if ([[NSFileManager defaultManager] fileExistsAtPath:path isDirectory:&isDirectory] && isDirectory) {
            [pathComponents addObject:path];
        }
    }
    
    // Add current PATH components
    if ([currentPath length] > 0) {
        [pathComponents addObjectsFromArray:[currentPath componentsSeparatedByString:@":"]];
    }
    
    // Remove duplicates while preserving order
    NSMutableArray *uniquePaths = [NSMutableArray array];
    NSMutableSet *seenPaths = [NSMutableSet set];
    for (NSString *path in pathComponents) {
        if (![seenPaths containsObject:path]) {
            [uniquePaths addObject:path];
            [seenPaths addObject:path];
        }
    }
    
    // Join into PATH string
    NSString *newPath = [uniquePaths componentsJoinedByString:@":"];
    
    // Set environment variable for current process
    setenv("PATH", [newPath UTF8String], 1);
    
    NSLog(@"Updated PATH: %@", newPath);
    
    // Also update Python's os.environ so subprocess calls see the new PATH
    NSString *pythonCmd = [NSString stringWithFormat:@"import os; os.environ['PATH'] = '%@'", 
                          [newPath stringByReplacingOccurrencesOfString:@"'" withString:@"\\'"]];
    PyRun_SimpleString([pythonCmd UTF8String]);
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
