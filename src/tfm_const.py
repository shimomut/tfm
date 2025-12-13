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

# Color constants moved to tfm_colors.py

# Terminal-specific key codes
# These are terminal-dependent codes that may vary across different terminal emulators.
# For standard keys (ENTER, TAB, arrows, etc.), use TTK's KeyCode enum instead.

# Shift+Arrow key combinations for log scrolling (terminal-dependent)
# Note: These codes vary by terminal emulator and may not work in all environments.
# Some terminals send regular arrow codes (258/259) for Shift+Arrow.
KEY_SHIFT_UP_1 = 337      # Shift+Up in some terminals
KEY_SHIFT_DOWN_1 = 336    # Shift+Down in some terminals  
KEY_SHIFT_UP_2 = 393      # Alternative Shift+Up code
KEY_SHIFT_DOWN_2 = 402    # Alternative Shift+Down code
KEY_SHIFT_LEFT_1 = 545    # Shift+Left in some terminals
KEY_SHIFT_RIGHT_1 = 560   # Shift+Right in some terminals
KEY_SHIFT_LEFT_2 = 393    # Alternative Shift+Left code
KEY_SHIFT_RIGHT_2 = 402   # Alternative Shift+Right code

# File size formatting thresholds
SIZE_KB = 1024
SIZE_MB = 1024 * 1024
SIZE_GB = 1024 * 1024 * 1024

# Date/time formats
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
LOG_TIME_FORMAT = "%H:%M:%S"

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