#!/usr/bin/env python3
"""
TUI File Manager - Constants and Configuration
"""

# Version information
VERSION = "1.00"

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
KEY_ESC = 27              # ESC key
KEY_CTRL_U = 21           # Ctrl+U (vertical resize up)
KEY_CTRL_D = 4            # Ctrl+D (vertical resize down)
KEY_CTRL_K = 11           # Ctrl+K (log scroll up)
KEY_CTRL_L = 12           # Ctrl+L (log scroll down)
KEY_SHIFT_COMMA = 60      # '<' - Shift+comma
KEY_SHIFT_PERIOD = 62     # '>' - Shift+period
KEY_SHIFT_LBRACKET = 123  # '{' - Shift+[
KEY_SHIFT_RBRACKET = 125  # '}' - Shift+]
# Shift key combinations for log scrolling (terminal-dependent)
KEY_SHIFT_UP_1 = 337      # Shift+Up in some terminals
KEY_SHIFT_DOWN_1 = 336    # Shift+Down in some terminals  
KEY_SHIFT_UP_2 = 393      # Alternative Shift+Up code
KEY_SHIFT_DOWN_2 = 402    # Alternative Shift+Down code
KEY_SHIFT_LEFT_1 = 545    # Shift+Left in some terminals (fast scroll to older messages)
KEY_SHIFT_RIGHT_1 = 560   # Shift+Right in some terminals (fast scroll to newer messages)
KEY_SHIFT_LEFT_2 = 393    # Alternative Shift+Left code
KEY_SHIFT_RIGHT_2 = 402   # Alternative Shift+Right code
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

# Isearch mode constants
SEARCH_KEY = ord('f')  # Key to enter isearch mode (F key)

# Text editor constants
DEFAULT_TEXT_EDITOR = 'vim'  # Default text editor to use
EDITOR_KEY = ord('e')  # Key to launch text editor (E key)