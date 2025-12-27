/*
 * main.m - TFM macOS Application Launcher
 *
 * This is the main entry point for the TFM native macOS application.
 * It initializes NSApplication and sets up the application delegate
 * that will handle Python embedding and TFM window creation.
 *
 * Requirements: 1.1, 14.1
 */

#import <Cocoa/Cocoa.h>
#import "TFMAppDelegate.h"

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        // Create the shared NSApplication instance
        // This is the singleton that manages the application lifecycle
        NSApplication *app = [NSApplication sharedApplication];
        
        // Create and set the application delegate
        // The delegate handles application lifecycle events and Python embedding
        TFMAppDelegate *delegate = [[TFMAppDelegate alloc] init];
        [app setDelegate:delegate];
        
        // Start the main event loop
        // This call blocks until the application terminates
        [app run];
    }
    return 0;
}
