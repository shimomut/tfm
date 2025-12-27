//
//  TFMAppDelegate.h
//  TFM - Terminal File Manager
//
//  Application delegate for TFM macOS app bundle.
//  Manages Python embedding, window lifecycle, and Dock integration.
//

#import <Cocoa/Cocoa.h>

@interface TFMAppDelegate : NSObject <NSApplicationDelegate>

// Python initialization and shutdown
- (BOOL)initializePython;
- (void)shutdownPython;

// Window management
- (void)launchNewTFMWindow;
- (void)windowWillClose:(NSNotification *)notification;

// Utility methods
- (NSString *)getBundleResourcePath;
- (void)showErrorDialog:(NSString *)message;

// Dock menu action
- (void)newDocument:(id)sender;

@end
