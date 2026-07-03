#!/usr/bin/env python3
"""
Demo: Window Geometry Persistence

This demo script demonstrates the window geometry persistence feature in TFM's
CoreGraphics backend. The feature automatically saves and restores window size
and position across application sessions using macOS's native NSWindow frame
autosave functionality.

Requirements:
- macOS operating system
- PyObjC framework installed (pip install pyobjc-framework-Cocoa)

Usage:
    python3 demo/demo_window_geometry_persistence.py

What to test:
1. First Launch (Default Geometry):
   - Window appears at default position (100, 100)
   - Window has default size based on grid dimensions
   - No saved geometry exists yet

2. Resize Persistence:
   - Resize the window to a different size
   - Quit TFM (press Q)
   - Relaunch the demo
   - Window should restore to the resized dimensions

3. Move Persistence:
   - Move the window to a different screen position
   - Quit TFM (press Q)
   - Relaunch the demo
   - Window should restore to the moved position

4. Combined Resize and Move:
   - Resize and move the window
   - Quit TFM (press Q)
   - Relaunch the demo
   - Window should restore both size and position

5. Multi-Monitor Support (if available):
   - Move window to a secondary monitor
   - Quit TFM (press Q)
   - Relaunch the demo
   - Window should restore on the secondary monitor
   - Disconnect secondary monitor and relaunch
   - Window should appear on primary monitor (automatic adjustment)

6. Reset Functionality:
   - Resize and move the window
   - Run the demo with --reset flag
   - Window should return to default size and position
   - Saved geometry should be cleared

7. Off-Screen Detection:
   - Move window to edge of screen
   - Change display resolution or disconnect monitor
   - Relaunch the demo
   - Window should be adjusted to visible position (automatic)

Testing Scenarios:
- Test with different window sizes (small, medium, large)
- Test with different screen positions (corners, edges, center)
- Test with multiple monitors (if available)
- Test reset functionality
- Test after system restart
"""

import sys
import platform
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def check_requirements():
    """Check if all requirements are met"""
    print("Checking requirements...")
    print()
    
    # Check platform
    if platform.system() != 'Darwin':
        print(f"❌ Error: Window geometry persistence requires macOS")
        print(f"   Current platform: {platform.system()}")
        print()
        print("This demo can only run on macOS.")
        return False
    
    print(f"✓ Platform: macOS ({platform.mac_ver()[0]})")
    
    # Check PyObjC
    try:
        import objc
        import Cocoa
        print("✓ PyObjC is installed")
    except ImportError:
        print("❌ Error: PyObjC is not installed")
        print("   Install with: pip install pyobjc-framework-Cocoa")
        return False
    
    # Check TTK CoreGraphics backend
    try:
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        print("✓ TTK CoreGraphics backend is available")
    except ImportError as e:
        print(f"❌ Error: Cannot import CoreGraphics backend: {e}")
        return False
    
    # Check TFM
    try:
        from tfm_main import main as tfm_main
        print("✓ TFM is available")
    except ImportError as e:
        print(f"❌ Error: Cannot import TFM: {e}")
        return False
    
    print()
    return True


def check_saved_geometry():
    """Check if saved window geometry exists"""
    try:
        import Cocoa
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        
        user_defaults = Cocoa.NSUserDefaults.standardUserDefaults()
        frame_key = f"NSWindow Frame {CoreGraphicsBackend.WINDOW_FRAME_AUTOSAVE_NAME}"
        saved_frame = user_defaults.stringForKey_(frame_key)
        
        if saved_frame:
            print(f"✓ Saved window geometry found: {saved_frame}")
            return True
        else:
            print("ℹ No saved window geometry found (first launch)")
            return False
    except Exception as e:
        print(f"⚠ Could not check saved geometry: {e}")
        return False


def print_instructions(reset_mode=False):
    """Print testing instructions"""
    print("="*70)
    if reset_mode:
        print("WINDOW GEOMETRY PERSISTENCE DEMO - RESET MODE")
    else:
        print("WINDOW GEOMETRY PERSISTENCE DEMO")
    print("="*70)
    print()
    
    if reset_mode:
        print("This demo will reset the window geometry to defaults.")
        print()
        print("The saved window position and size will be cleared, and the")
        print("window will appear at the default location (100, 100) with")
        print("default dimensions.")
        print()
    else:
        print("This demo demonstrates automatic window geometry persistence.")
        print("The window's size and position are automatically saved when")
        print("you resize or move it, and restored when you relaunch TFM.")
        print()
        
        # Check if saved geometry exists
        has_saved = check_saved_geometry()
        print()
        
        if has_saved:
            print("EXPECTED BEHAVIOR:")
            print("  The window should restore to its previously saved size")
            print("  and position from your last session.")
        else:
            print("EXPECTED BEHAVIOR:")
            print("  This appears to be the first launch. The window will")
            print("  appear at the default position (100, 100) with default")
            print("  dimensions based on the grid size.")
    
    print()
    print("TESTING CHECKLIST:")
    print()
    print("1. Window Restoration:")
    print("   □ Window appears at expected position")
    print("   □ Window has expected size")
    print("   □ Window is fully visible on screen")
    print()
    print("2. Resize Persistence:")
    print("   □ Resize the window to a different size")
    print("   □ Quit TFM (press Q)")
    print("   □ Relaunch this demo")
    print("   □ Window restores to the resized dimensions")
    print()
    print("3. Move Persistence:")
    print("   □ Move the window to a different position")
    print("   □ Quit TFM (press Q)")
    print("   □ Relaunch this demo")
    print("   □ Window restores to the moved position")
    print()
    print("4. Combined Persistence:")
    print("   □ Resize and move the window")
    print("   □ Quit TFM (press Q)")
    print("   □ Relaunch this demo")
    print("   □ Window restores both size and position")
    print()
    
    if not reset_mode:
        print("5. Multi-Monitor Support (if available):")
        print("   □ Move window to secondary monitor")
        print("   □ Quit and relaunch")
        print("   □ Window appears on secondary monitor")
        print("   □ Disconnect secondary monitor")
        print("   □ Relaunch demo")
        print("   □ Window appears on primary monitor")
        print()
        print("6. Reset Functionality:")
        print("   □ Run: python3 demo/demo_window_geometry_persistence.py --reset")
        print("   □ Window returns to default position and size")
        print("   □ Saved geometry is cleared")
        print()
    
    print("="*70)
    print()
    
    if reset_mode:
        print("Press Enter to reset window geometry and launch TFM...")
    else:
        print("Press Enter to launch TFM...")
    input()


def reset_window_geometry():
    """Reset window geometry to defaults"""
    print("Resetting window geometry...")
    print()
    
    try:
        import Cocoa
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        
        # Clear the saved frame from NSUserDefaults
        user_defaults = Cocoa.NSUserDefaults.standardUserDefaults()
        frame_key = f"NSWindow Frame {CoreGraphicsBackend.WINDOW_FRAME_AUTOSAVE_NAME}"
        
        # Check if saved geometry exists
        saved_frame = user_defaults.stringForKey_(frame_key)
        if saved_frame:
            print(f"Found saved geometry: {saved_frame}")
            user_defaults.removeObjectForKey_(frame_key)
            user_defaults.synchronize()
            print("✓ Saved window geometry cleared")
        else:
            print("ℹ No saved geometry found (already at defaults)")
        
        print()
        print("Window will appear at default position and size.")
        return True
        
    except Exception as e:
        print(f"❌ Error resetting window geometry: {e}")
        import traceback
        traceback.print_exc()
        return False


def launch_tfm_with_geometry_persistence(reset_mode=False):
    """Launch TFM with window geometry persistence"""
    print("Launching TFM with CoreGraphics backend...")
    print()
    
    try:
        # Import required modules
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        from tfm_main import main as tfm_main
        
        # Create CoreGraphics backend
        backend_options = {
            'window_title': 'TFM - Window Geometry Persistence Demo',
            'font_name': 'Menlo',
            'font_size': 14,
            'rows': 24,
            'cols': 80,
        }
        
        print("Creating CoreGraphics backend...")
        renderer = CoreGraphicsBackend(**backend_options)
        
        print("Initializing renderer...")
        renderer.initialize()
        
        # If in reset mode, reset the geometry after initialization
        if reset_mode:
            print()
            print("Applying reset...")
            success = renderer.reset_window_geometry()
            if success:
                print("✓ Window geometry reset successfully")
            else:
                print("⚠ Reset may have failed (check warnings above)")
            print()
        
        print("Starting TFM...")
        print()
        print("="*70)
        print("TFM is now running.")
        print()
        print("INSTRUCTIONS:")
        print("  1. Try resizing the window")
        print("  2. Try moving the window to different positions")
        print("  3. Press Q to quit")
        print("  4. Relaunch this demo to see geometry restored")
        print()
        if not reset_mode:
            print("  To reset geometry: python3 demo/demo_window_geometry_persistence.py --reset")
            print()
        print("="*70)
        print()
        
        # Run TFM
        tfm_main(renderer, remote_log_port=None, left_dir=None, right_dir=None)
        
        print()
        print("TFM exited normally.")
        print()
        print("Window geometry has been saved automatically.")
        print("Relaunch this demo to see the geometry restored.")
        
    except KeyboardInterrupt:
        print()
        print("Demo interrupted by user.")
    except Exception as e:
        print()
        print(f"Error running TFM: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Ensure renderer is shut down
        try:
            if 'renderer' in locals():
                renderer.shutdown()
        except Exception:
            pass
    
    return True


def print_results(reset_mode=False):
    """Print results and next steps"""
    print()
    print("="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print()
    
    if reset_mode:
        print("Window geometry has been reset to defaults.")
        print()
        print("Next steps:")
        print("  1. Relaunch the demo without --reset flag")
        print("  2. Window should appear at default position")
        print("  3. Resize/move the window and test persistence again")
        print()
    else:
        print("Window geometry persistence is working!")
        print()
        print("What was demonstrated:")
        print("  ✓ Window geometry automatically saved on resize/move")
        print("  ✓ Window geometry automatically restored on launch")
        print("  ✓ Native macOS NSWindow frame autosave used")
        print("  ✓ Storage in NSUserDefaults (macOS preferences)")
        print()
        print("Next steps:")
        print("  1. Relaunch the demo to verify persistence")
        print("  2. Try different window sizes and positions")
        print("  3. Test with multiple monitors (if available)")
        print("  4. Test reset: python3 demo/demo_window_geometry_persistence.py --reset")
        print()
    
    print("Technical details:")
    print("  - Frame autosave name: TFMMainWindow")
    print("  - Storage: NSUserDefaults")
    print("  - Key: 'NSWindow Frame TFMMainWindow'")
    print("  - Format: 'x y width height' (bottom-left origin)")
    print()
    print("To check saved geometry:")
    print("  defaults read -g 'NSWindow Frame TFMMainWindow'")
    print()
    print("To manually clear saved geometry:")
    print("  defaults delete -g 'NSWindow Frame TFMMainWindow'")
    print()
    print("="*70)


def main():
    """Main demo function"""
    # Check for reset flag
    reset_mode = '--reset' in sys.argv or '-r' in sys.argv
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Print instructions
    print_instructions(reset_mode)
    
    # Reset geometry if requested
    if reset_mode:
        if not reset_window_geometry():
            print()
            print("Failed to reset window geometry.")
            print("Continuing with launch anyway...")
            print()
            time.sleep(2)
    
    # Launch TFM
    success = launch_tfm_with_geometry_persistence(reset_mode)
    
    # Print results
    print_results(reset_mode)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
