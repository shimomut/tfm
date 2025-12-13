#!/usr/bin/env python3
"""
Demo: TFM with CoreGraphics Backend

This demo script launches TFM with the CoreGraphics backend to verify
desktop mode functionality on macOS.

Requirements:
- macOS operating system
- PyObjC framework installed (pip install pyobjc-framework-Cocoa)

Usage:
    python3 demo/demo_coregraphics_backend.py

What to test:
1. Window Creation:
   - A native macOS window should open
   - Window title should be "TFM - TUI File Manager"
   - Window should be resizable

2. Rendering:
   - TFM interface should be rendered correctly
   - File lists should be visible in both panes
   - Colors should be displayed correctly
   - Text should be crisp and readable
   - Status bar should show current directory

3. Basic Functionality:
   - Arrow keys should navigate file list
   - Tab should switch between panes
   - Enter should open directories
   - Backspace should go to parent directory
   - Space should select/deselect files
   - Q should quit the application

4. Input Handling:
   - All key bindings should work as expected
   - Special keys (F1-F12) should work
   - Modifier keys (Cmd, Ctrl, Alt) should work
   - Mouse input should work (if supported)

5. Rendering Quality:
   - No rendering artifacts or glitches
   - Window resizing should work smoothly
   - Interface should adapt to window size
   - Text should remain readable at different sizes
"""

import sys
import platform
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def check_requirements():
    """Check if all requirements are met"""
    print("Checking requirements...")
    print()
    
    # Check platform
    if platform.system() != 'Darwin':
        print(f"❌ Error: CoreGraphics backend requires macOS")
        print(f"   Current platform: {platform.system()}")
        print()
        print("This demo can only run on macOS.")
        return False
    
    print(f"✓ Platform: macOS ({platform.mac_ver()[0]})")
    
    # Check PyObjC
    try:
        import objc
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


def print_instructions():
    """Print testing instructions"""
    print("="*70)
    print("TFM COREGRAPHICS BACKEND DEMO")
    print("="*70)
    print()
    print("This demo will launch TFM with the CoreGraphics backend.")
    print("A native macOS window will open with TFM running inside.")
    print()
    print("TESTING CHECKLIST:")
    print()
    print("1. Window Creation:")
    print("   □ Native macOS window opens")
    print("   □ Window title is 'TFM - TUI File Manager'")
    print("   □ Window is resizable")
    print()
    print("2. Rendering:")
    print("   □ TFM interface renders correctly")
    print("   □ File lists visible in both panes")
    print("   □ Colors display correctly")
    print("   □ Text is crisp and readable")
    print("   □ Status bar shows current directory")
    print()
    print("3. Basic Functionality:")
    print("   □ Arrow keys navigate file list")
    print("   □ Tab switches between panes")
    print("   □ Enter opens directories")
    print("   □ Backspace goes to parent directory")
    print("   □ Space selects/deselects files")
    print("   □ Q quits the application")
    print()
    print("4. Input Handling:")
    print("   □ All key bindings work")
    print("   □ Special keys (F1-F12) work")
    print("   □ Modifier keys (Cmd, Ctrl, Alt) work")
    print()
    print("5. Rendering Quality:")
    print("   □ No rendering artifacts")
    print("   □ Window resizing works smoothly")
    print("   □ Interface adapts to window size")
    print("   □ Text remains readable at different sizes")
    print()
    print("="*70)
    print()
    print("Press Enter to launch TFM with CoreGraphics backend...")
    input()


def launch_tfm_with_coregraphics():
    """Launch TFM with CoreGraphics backend"""
    print("Launching TFM with CoreGraphics backend...")
    print()
    
    try:
        # Import required modules
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        from tfm_main import main as tfm_main
        
        # Create CoreGraphics backend
        backend_options = {
            'window_title': 'TFM - TUI File Manager',
            'font_name': 'Menlo',
            'font_size': 14,
            'rows': 24,
            'cols': 80,
        }
        
        print("Creating CoreGraphics backend...")
        renderer = CoreGraphicsBackend(**backend_options)
        
        print("Initializing renderer...")
        renderer.initialize()
        
        print("Starting TFM...")
        print()
        print("TFM is now running in desktop mode.")
        print("Use Q to quit when done testing.")
        print()
        
        # Run TFM
        tfm_main(renderer, remote_log_port=None, left_dir=None, right_dir=None)
        
        print()
        print("TFM exited normally.")
        
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


def print_results():
    """Print results and next steps"""
    print()
    print("="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print()
    print("If you encountered any issues, please check:")
    print()
    print("1. Rendering Issues:")
    print("   - Check that font 'Menlo' is available on your system")
    print("   - Try different font sizes in backend_options")
    print("   - Check console for error messages")
    print()
    print("2. Input Issues:")
    print("   - Verify keyboard layout is standard US")
    print("   - Check that no other apps are capturing input")
    print("   - Try different key combinations")
    print()
    print("3. Performance Issues:")
    print("   - Check Activity Monitor for CPU/memory usage")
    print("   - Try smaller window size")
    print("   - Check for background processes")
    print()
    print("To run TFM in desktop mode normally:")
    print("  python3 tfm.py --desktop")
    print()
    print("Or:")
    print("  python3 tfm.py --backend coregraphics")
    print()
    print("="*70)


def main():
    """Main demo function"""
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Print instructions
    print_instructions()
    
    # Launch TFM
    success = launch_tfm_with_coregraphics()
    
    # Print results
    print_results()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
