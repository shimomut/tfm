#!/usr/bin/env python3
"""
TFM (Terminal File Manager) - Main Entry Point

A terminal-based file manager using curses with dual-pane interface.
"""

import sys
import os
import argparse
from pathlib import Path

# Setup module path for both development and installed package environments
def setup_module_path():
    """Setup module path - src directory exists next to tfm.py in both environments"""
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
        prog='tfm',
        description=APP_DESCRIPTION,
        epilog=f"For more information, visit: {GITHUB_URL}"
    )
    
    parser.add_argument(
        '-v', '--version', 
        action='version', 
        version=f'{APP_NAME} {VERSION}'
    )
    
    parser.add_argument(
        '--backend',
        type=str,
        choices=['curses', 'coregraphics'],
        help='Rendering backend to use (default: curses)'
    )
    
    parser.add_argument(
        '--desktop',
        action='store_true',
        help='Run as desktop application (shorthand for --backend coregraphics)'
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
    
    parser.add_argument(
        '--color-test',
        type=str,
        metavar='MODE',
        choices=['info', 'schemes', 'capabilities', 'rgb-test', 'fallback-test', 'interactive', 'tfm-init', 'diagnose'],
        help='Run color debugging tests: info (show current colors), schemes (list all schemes), '
             'capabilities (terminal color support), rgb-test (force RGB mode), '
             'fallback-test (force fallback mode), interactive (interactive color tester), '
             'tfm-init (test exact TFM initialization sequence), diagnose (diagnose color issues)'
    )
    
    return parser

def main():
    """Main entry point with argument parsing"""
    parser = create_parser()
    
    try:
        # Parse arguments
        args = parser.parse_args()
        
        # Handle color testing mode
        if args.color_test:
            # Set ESC delay for color tests that use curses
            os.environ.setdefault('ESCDELAY', '100')
            
            # Import color testing module
            from tfm_color_tester import run_color_test
            run_color_test(args.color_test)
            return
        
        # Set ESC delay to 100ms BEFORE any curses-related imports for responsive ESC key
        os.environ.setdefault('ESCDELAY', '100')
        
        # Select backend based on arguments and configuration
        from tfm_backend_selector import select_backend
        backend_name, backend_options = select_backend(args)
        
        # Create TTK renderer directly based on selected backend
        if backend_name == 'curses':
            from ttk.backends.curses_backend import CursesBackend
            renderer = CursesBackend()
        elif backend_name == 'coregraphics':
            from ttk.backends.coregraphics_backend import CoreGraphicsBackend
            renderer = CoreGraphicsBackend(**backend_options)
        else:
            raise ValueError(f"Unknown backend: {backend_name}")
        
        try:
            # Initialize the renderer
            renderer.initialize()
            
            # Import and run the main application
            from tfm_main import main as tfm_main
            
            # Pass renderer to tfm_main instead of using curses.wrapper
            tfm_main(renderer,
                    remote_log_port=args.remote_log_port,
                    left_dir=args.left,
                    right_dir=args.right)
        finally:
            # Ensure renderer is properly shut down
            renderer.shutdown()
        
    except ImportError as e:
        print(f"Error importing TFM modules: {e}", file=sys.stderr)
        print("Make sure you're running from the TFM root directory", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nTFM interrupted by user", file=sys.stderr)
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Error running TFM: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()