#!/usr/bin/env python3
"""
TUI File Manager - Constants and Configuration
"""

# Version information
VERSION = "0.10"

# Application metadata
APP_NAME = "TUI File Manager"
APP_DESCRIPTION = "A terminal-based file manager using curses"

# Display constants
DEFAULT_LOG_HEIGHT_RATIO = 0.25  # Log pane takes 1/4 of screen
MIN_LOG_HEIGHT = 5
MAX_LOG_MESSAGES = 1000

# Color pair constants
COLOR_DIRECTORIES = 1
COLOR_EXECUTABLES = 2
COLOR_SELECTED = 3
COLOR_ERROR = 4
COLOR_HEADER = 5

# Key codes (for reference)
KEY_TAB = 9
KEY_ENTER_1 = 10
KEY_ENTER_2 = 13
KEY_BACKSPACE_1 = 8
KEY_BACKSPACE_2 = 127

# File size formatting thresholds
SIZE_KB = 1024
SIZE_MB = 1024 * 1024
SIZE_GB = 1024 * 1024 * 1024

# Date/time formats
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
LOG_TIME_FORMAT = "%H:%M:%S"