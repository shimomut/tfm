#!/usr/bin/env python3
"""
TFM Qt (Terminal File Manager - GUI Mode) - Main Entry Point

A graphical file manager using Qt for Python with dual-pane interface.
"""

import sys
import os
import argparse
from pathlib import Path

# Setup module path for both development and installed package environments
def setup_module_path():
    """Setup module path - src directory exists next to tfm_qt.py in both environments"""
    current_dir = Path(__file__).parent
    src_dir = current_dir / 'src'
    
    # Add src directory to path (works for both development and installed package)
    sys.path.insert(0, str(src_dir))
    return str(src_dir)

# Setup the module path
module_path = setup_module_path()

def create_parser():
    """Create and configure the argument parser"""
    # Import version info after adding src to path
    try:
        from tfm_const import VERSION, APP_NAME, APP_DESCRIPTION, GITHUB_URL
    except ImportError:
        VERSION = "1.00"
        APP_NAME = "TUI File Manager"
        APP_DESCRIPTION = "A terminal-based file manager using curses"
    
    parser = argparse.ArgumentParser(
        prog='tfm-qt',
        description=f"{APP_DESCRIPTION} - GUI Mode",
        epilog=f"For more information, visit: {GITHUB_URL}"
    )
    
    parser.add_argument(
        '-v', '--version', 
        action='version', 
        version=f'{APP_NAME} (GUI) {VERSION}'
    )
    
    parser.add_argument(
        '--remote-log-port',
        type=int,
        metavar='PORT',
        help='Enable remote log monitoring on specified port (e.g., --remote-log-port 8888)'
    )
    
    parser.add_argument(
        '--left',
        type=str,
        metavar='PATH',
        help='Specify directory path for left pane (default: current directory)'
    )
    
    parser.add_argument(
        '--right',
        type=str,
        metavar='PATH',
        help='Specify directory path for right pane (default: home directory)'
    )
    
    return parser

def main():
    """Main entry point with argument parsing"""
    parser = create_parser()
    
    try:
        # Parse arguments
        args = parser.parse_args()
        
        # Import required modules
        from PySide6.QtWidgets import QApplication
        from tfm_qt_backend import QtBackend
        from tfm_application import TFMApplication
        from tfm_state_manager import cleanup_state_manager
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("TFM")
        app.setOrganizationName("TFM")
        
        # Set application style (optional - can be configured later)
        # app.setStyle('Fusion')
        
        try:
            # Create Qt backend
            backend = QtBackend(app)
            
            # Initialize backend
            if not backend.initialize():
                print("Error: Failed to initialize Qt backend", file=sys.stderr)
                return 1
            
            # Create application with backend
            tfm_app = TFMApplication(
                ui_backend=backend,
                remote_log_port=args.remote_log_port,
                left_dir=args.left,
                right_dir=args.right
            )
            
            # Run application (this will start the main loop)
            tfm_app.run()
            
            # Start Qt event loop
            # Note: The event loop is integrated into TFMApplication.run()
            # which processes Qt events through backend.refresh()
            return 0
            
        except KeyboardInterrupt:
            # Clean exit on Ctrl+C
            print("\nTFM interrupted by user", file=sys.stderr)
            return 130  # Standard exit code for SIGINT
            
        except Exception as e:
            # Print error information
            print(f"\nTFM encountered an unexpected error:", file=sys.stderr)
            print(f"Error: {type(e).__name__}: {e}", file=sys.stderr)
            print("\nFull traceback:", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1
            
        finally:
            # Clean up state manager
            cleanup_state_manager()
        
    except ImportError as e:
        print(f"Error importing TFM modules: {e}", file=sys.stderr)
        print("Make sure you have PySide6 installed: pip install PySide6", file=sys.stderr)
        print("And that you're running from the TFM root directory", file=sys.stderr)
        return 1
        
    except Exception as e:
        print(f"Error running TFM: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
