# TFM macOS App - Manual Testing Guide

This guide provides step-by-step instructions for manually testing the TFM macOS application bundle.

## Prerequisites

- TFM.app built successfully (run `./build.sh` if not already built)
- macOS 10.13 or later
- Application bundle located at: `macos_app/build/TFM.app`

## Test 1: First Launch

### Steps
1. Open Terminal
2. Navigate to the project directory
3. Run:
   ```bash
   open macos_app/build/TFM.app
   ```

### Expected Results
- ✅ TFM icon appears in the Dock
- ✅ A TFM window opens showing the file manager interface
- ✅ Window title shows "TFM - Terminal File Manager"
- ✅ File listing displays correctly
- ✅ No error dialogs appear

### What to Check
- Window renders properly with no visual glitches
- File listings show current directory contents
- Status bar displays at bottom of window
- Cursor is visible and positioned correctly

---

## Test 2: Keyboard Input

### Steps
1. With TFM window focused, try these keys:
   - Arrow keys (↑↓) - Navigate file list
   - Tab - Switch between panes
   - Enter - Open directory or file
   - Backspace - Go to parent directory
   - Q - Quit application

### Expected Results
- ✅ Arrow keys move cursor up/down in file list
- ✅ Tab switches focus between left and right panes
- ✅ Enter opens directories/files
- ✅ Backspace navigates to parent directory
- ✅ Q quits the application

### What to Check
- Keyboard input is responsive
- Cursor moves smoothly
- No lag or delay in key handling
- Application responds to all key commands

---

## Test 3: Mouse Input

### Steps
1. Launch TFM.app
2. Try these mouse actions:
   - Click on different files in the list
   - Click on the other pane
   - Scroll with mouse wheel or trackpad
   - Double-click on a directory

### Expected Results
- ✅ Single click selects file/directory
- ✅ Clicking switches pane focus
- ✅ Scrolling moves through file list
- ✅ Double-click opens directory

### What to Check
- Mouse clicks are accurate
- Scrolling is smooth
- No visual artifacts during scrolling
- Cursor position updates correctly

---

## Test 4: Multi-Window Support

### Steps
1. Launch TFM.app (if not already running)
2. Right-click on the TFM icon in the Dock
3. Select "New Window" from the menu
4. Verify second window opens
5. Navigate to different directories in each window
6. Close one window (Cmd+W or click red close button)
7. Verify other window continues working
8. Close the last window

### Expected Results
- ✅ Right-click shows Dock menu with "New Window" option
- ✅ Selecting "New Window" creates a second TFM window
- ✅ Both windows operate independently
- ✅ Each window can navigate to different directories
- ✅ Closing one window doesn't affect the other
- ✅ Closing the last window terminates the application

### What to Check
- Each window maintains its own state
- File operations in one window don't affect the other
- Windows can be moved and resized independently
- Application terminates cleanly when last window closes

---

## Test 5: Dock Integration

### Steps
1. Launch TFM.app
2. Right-click the TFM icon in the Dock
3. Observe the Dock menu

### Expected Results
- ✅ Dock menu appears
- ✅ "New Window" option is present
- ✅ Standard macOS menu items appear (Quit, etc.)
- ✅ If multiple windows open, window list appears

### What to Check
- Dock menu is properly formatted
- "New Window" option works when clicked
- Window list (if present) shows all open windows
- Clicking window name brings that window to front

---

## Test 6: File Operations

### Steps
1. Launch TFM.app
2. Navigate to a test directory
3. Try these operations:
   - View a text file (press F3 or V)
   - Copy a file (press F5)
   - Move a file (press F6)
   - Delete a file (press F8)
   - Create a directory (press F7)

### Expected Results
- ✅ File viewer opens for text files
- ✅ Copy dialog appears with progress
- ✅ Move dialog appears with progress
- ✅ Delete confirmation dialog appears
- ✅ Create directory dialog appears

### What to Check
- All file operations complete successfully
- Progress indicators work correctly
- Error messages appear for invalid operations
- File system changes are reflected immediately

---

## Test 7: Application Quit

### Steps
1. Launch TFM.app
2. Try each quit method:
   - Press Q key in TFM window
   - Press Cmd+Q
   - Right-click Dock icon and select "Quit"
   - Close all windows

### Expected Results
- ✅ Q key quits immediately
- ✅ Cmd+Q quits immediately
- ✅ Dock "Quit" option quits immediately
- ✅ Closing last window quits application
- ✅ No error dialogs on quit
- ✅ No crash or hang

### What to Check
- Application terminates cleanly
- No zombie processes left running
- No error messages in Console.app
- Application can be relaunched successfully

---

## Test 8: Error Handling (Optional)

**Warning:** This test temporarily breaks the app bundle. Only perform if you want to verify error handling.

### Steps
1. Quit TFM.app if running
2. Temporarily rename Python.framework:
   ```bash
   cd macos_app/build/TFM.app/Contents/Frameworks
   mv Python.framework Python.framework.backup
   ```
3. Try to launch TFM.app:
   ```bash
   open ../../TFM.app
   ```
4. Observe error dialog
5. Restore Python.framework:
   ```bash
   mv Python.framework.backup Python.framework
   ```

### Expected Results
- ✅ Error dialog appears with clear message
- ✅ Message mentions Python initialization failure
- ✅ Message suggests possible causes
- ✅ Message suggests reinstalling TFM
- ✅ Application terminates gracefully after clicking OK

### What to Check
- Error dialog is properly formatted
- Error message is clear and helpful
- No crash or hang
- Console.app shows detailed error logs

---

## Test 9: Development Mode Compatibility

### Steps
1. Open Terminal
2. Navigate to project directory
3. Run TFM in terminal mode:
   ```bash
   python3 tfm.py
   ```
4. Quit (press Q)
5. Run TFM in desktop mode:
   ```bash
   python3 tfm.py --desktop
   ```
6. Quit (press Q)

### Expected Results
- ✅ Terminal mode launches with curses interface
- ✅ Desktop mode launches with CoreGraphics window
- ✅ Both modes work correctly
- ✅ No errors or warnings
- ✅ Source changes take effect immediately (no rebuild needed)

### What to Check
- Both modes launch successfully
- Terminal mode uses curses backend
- Desktop mode uses CoreGraphics backend
- No conflicts with app bundle
- Development workflow unchanged

---

## Test 10: Performance and Stability

### Steps
1. Launch TFM.app
2. Navigate through large directories (1000+ files)
3. Open and close multiple windows
4. Perform file operations on large files
5. Leave app running for extended period
6. Switch between TFM and other applications

### Expected Results
- ✅ Large directories load quickly
- ✅ Scrolling is smooth even with many files
- ✅ Multiple windows don't slow down the app
- ✅ Large file operations complete successfully
- ✅ No memory leaks or performance degradation
- ✅ App switching works smoothly

### What to Check
- Responsive UI at all times
- No memory leaks (check Activity Monitor)
- No CPU spikes during idle
- Stable performance over time
- No crashes or hangs

---

## Troubleshooting

### App Won't Launch
1. Check Console.app for error messages
2. Verify Python.framework exists in bundle
3. Verify TFM source files exist in Resources
4. Try rebuilding: `cd macos_app && ./build.sh`

### Window Doesn't Appear
1. Check if window is hidden behind other windows
2. Check Console.app for Python errors
3. Verify CoreGraphics backend is working
4. Try development mode: `python3 tfm.py --desktop`

### Keyboard/Mouse Not Working
1. Verify window has focus (click on it)
2. Check System Preferences > Security & Privacy
3. Grant accessibility permissions if prompted
4. Try restarting the application

### File Operations Fail
1. Check file permissions
2. Verify sufficient disk space
3. Check Console.app for error messages
4. Try operations in development mode to isolate issue

---

## Reporting Issues

If you encounter any issues during testing:

1. **Check Console.app** for detailed error logs
   - Open Console.app
   - Filter for "TFM" or "Python"
   - Copy relevant error messages

2. **Gather System Information**
   - macOS version: `sw_vers`
   - Python version: `python3 --version`
   - TFM version: Check Info.plist

3. **Document Steps to Reproduce**
   - What were you doing when the issue occurred?
   - Can you reproduce it consistently?
   - Does it happen in development mode too?

4. **Create Issue Report**
   - Include error messages from Console.app
   - Include system information
   - Include steps to reproduce
   - Include screenshots if relevant

---

## Success Criteria

All tests should pass with these results:
- ✅ Application launches successfully
- ✅ UI renders correctly
- ✅ Keyboard and mouse input work
- ✅ Multiple windows work independently
- ✅ Dock integration functions properly
- ✅ File operations complete successfully
- ✅ Application quits cleanly
- ✅ Error handling works as expected
- ✅ Development mode still works
- ✅ Performance is acceptable

If all tests pass, the TFM macOS application bundle is ready for distribution!

---

## Next Steps After Testing

1. **Create Application Icon** (optional)
   - Design icon in .icns format
   - Place at `macos_app/resources/TFM.icns`
   - Rebuild application

2. **Code Signing** (optional, for distribution)
   ```bash
   export CODESIGN_IDENTITY="Developer ID Application: Your Name"
   cd macos_app && ./build.sh
   ```

3. **Create DMG Installer** (optional)
   ```bash
   make macos-dmg
   ```

4. **Install to Applications** (optional)
   ```bash
   make macos-app-install
   ```

5. **Distribute**
   - Share TFM.app bundle directly, or
   - Share DMG installer, or
   - Submit to Mac App Store (requires additional steps)
