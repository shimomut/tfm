#!/usr/bin/env python3
"""
TUI File Manager - Constants and Configuration

Note: Most key codes are now handled by TTK's KeyCode enum (ttk.input_event.KeyCode).
Standard keys like ENTER, TAB, ESCAPE, arrow keys, function keys, etc. should use
KeyCode values. Only terminal-specific key codes that aren't standardized in TTK
are defined here.
"""

# Version information
VERSION = "0.98"

# Application metadata
APP_NAME = "TUI File Manager"
APP_DESCRIPTION = "A terminal-based file manager"
GITHUB_URL = "https://github.com/shimomut/tfm"  # Update with actual repository URL

# Display constants
DEFAULT_LOG_HEIGHT_RATIO = 0.25  # Log pane takes 1/4 of screen
MIN_LOG_HEIGHT = 5
MAX_LOG_MESSAGES = 1000

# Terminal-specific key codes have been moved to TTK's curses backend
# Use KeyCode with ModifierKey.SHIFT for Shift+Arrow combinations instead

# File size formatting thresholds
SIZE_KB = 1024
SIZE_MB = 1024 * 1024
SIZE_GB = 1024 * 1024 * 1024

# Date/time formats
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
LOG_TIME_FORMAT = "%H:%M:%S"

# File list date format options
DATE_FORMAT_FULL = 'full'        # YYYY-MM-DD HH:mm:ss
DATE_FORMAT_SHORT = 'short'      # YY-MM-DD HH:mm (default)

# Pane layout constants
MIN_PANE_RATIO = 0.1  # Minimum left pane width (10%)
MAX_PANE_RATIO = 0.9  # Maximum left pane width (90%)
PANE_ADJUST_STEP = 0.05  # 5% adjustment per key press

# Vertical pane layout constants
MIN_LOG_HEIGHT_RATIO = 0.0   # Minimum log pane height (0% - can be hidden)
MAX_LOG_HEIGHT_RATIO = 0.9   # Maximum log pane height (60%)
LOG_HEIGHT_ADJUST_STEP = 0.05  # 5% adjustment per key press

# Isearch mode constants
SEARCH_KEY = ord('f')  # Key to enter isearch mode (F key)

# Text editor constants
DEFAULT_TEXT_EDITOR = 'vim'  # Default text editor to use
EDITOR_KEY = ord('e')  # Key to launch text editor (E key)