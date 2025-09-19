#!/usr/bin/env python3
"""
TUI File Manager - Constants and Configuration
"""

# Version information
VERSION = "0.10"

# Application metadata
APP_NAME = "TUI File Manager"
APP_DESCRIPTION = "A terminal-based file manager using curses"
GITHUB_URL = "https://github.com/shimomut/tfm"  # Update with actual repository URL

# Display constants
DEFAULT_LOG_HEIGHT_RATIO = 0.25  # Log pane takes 1/4 of screen
MIN_LOG_HEIGHT = 5
MAX_LOG_MESSAGES = 1000

# Color constants moved to tfm_colors.py

# Key codes (for reference)
KEY_TAB = 9
KEY_ENTER_1 = 10
KEY_ENTER_2 = 13
KEY_BACKSPACE_1 = 8
KEY_BACKSPACE_2 = 127
# Modifier key combinations
KEY_CTRL_SPACE = 0   # Ctrl+Space
KEY_CTRL_S = 19      # Ctrl+S
KEY_OPTION_SPACE_1 = 194  # Option+Space first byte (macOS)
KEY_OPTION_SPACE_2 = 160  # Option+Space second byte (macOS)
KEY_ESC = 27              # ESC key (used for Option+arrow sequences)
KEY_OPTION_LEFT_2 = 98    # Option+Left second byte (ESC + 'b')
KEY_OPTION_RIGHT_2 = 102  # Option+Right second byte (ESC + 'f')
KEY_CTRL_U = 21           # Ctrl+U (vertical resize up)
KEY_CTRL_D = 4            # Ctrl+D (vertical resize down)
KEY_CTRL_K = 11           # Ctrl+K (log scroll up)
KEY_CTRL_L = 12           # Ctrl+L (log scroll down)
# Shift key combinations for log scrolling (terminal-dependent)
KEY_SHIFT_UP_1 = 337      # Shift+Up in some terminals
KEY_SHIFT_DOWN_1 = 336    # Shift+Down in some terminals  
KEY_SHIFT_UP_2 = 393      # Alternative Shift+Up code
KEY_SHIFT_DOWN_2 = 402    # Alternative Shift+Down code
# Note: Shift+Arrow keys may send regular arrow codes (258/259) in some terminals

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

# Search mode constants
SEARCH_KEY = ord('/')  # Key to enter search mode