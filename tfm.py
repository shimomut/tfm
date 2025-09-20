#!/usr/bin/env python3
"""
TFM (Terminal File Manager) - Main Entry Point

A terminal-based file manager using curses with dual-pane interface.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

# Set ESC delay to 100ms BEFORE any curses-related imports for responsive ESC key
os.environ.setdefault('ESCDELAY', '100')

# Import and run the main application
try:
    from tfm_main import main
    import curses
    
    if __name__ == "__main__":
        curses.wrapper(main)
        
except ImportError as e:
    print(f"Error importing TFM modules: {e}")
    print("Make sure you're running from the TFM root directory")
    sys.exit(1)
except Exception as e:
    print(f"Error running TFM: {e}")
    sys.exit(1)