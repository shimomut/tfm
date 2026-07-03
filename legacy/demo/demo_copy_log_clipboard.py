#!/usr/bin/env python3
"""
Demo: Copy Log Pane Contents to Clipboard

This demo demonstrates the new feature to copy log pane contents to clipboard
in desktop mode. It shows:
- Menu items for copying visible logs
- Menu items for copying all logs
- Clipboard integration with log pane

The demo generates sample log messages and allows testing the clipboard copy
functionality through the Edit menu.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from ttk import TtkApplication, TtkDesktopRenderer
from tfm_log_manager import getLogger


def main():
    """Run the demo"""
    
    # Create desktop renderer
    renderer = TtkDesktopRenderer()
    
    # Import FileManager after renderer is created
    from tfm_main import FileManager
    
    # Create file manager with desktop mode
    fm = FileManager(renderer, debug=False)
    
    # Get logger and add some sample messages
    logger = getLogger("Demo")
    logger.info("Welcome to the Copy Log Clipboard demo!")
    logger.info("This demo shows the new clipboard copy feature for logs")
    logger.info("Try the following:")
    logger.info("1. Open the Edit menu")
    logger.info("2. Select 'Copy Visible Logs to Clipboard'")
    logger.info("3. Or select 'Copy All Logs to Clipboard'")
    logger.info("4. Paste the clipboard contents in another application")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Add more messages to test scrolling
    for i in range(20):
        logger.info(f"Sample log message {i+1}")
    
    logger.info("Scroll the log pane to see different messages")
    logger.info("The 'Copy Visible Logs' will copy only what you see")
    logger.info("The 'Copy All Logs' will copy everything including scrolled content")
    
    # Run the application
    fm.run()


if __name__ == '__main__':
    main()
