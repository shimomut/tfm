#!/usr/bin/env python3
"""
TFM User Configuration

This file contains your personal TFM configuration.
You can modify any of these settings to customize TFM behavior.
"""

class Config:
    """User configuration for TFM"""
    
    # Display settings
    SHOW_HIDDEN_FILES = False
    DEFAULT_LEFT_PANE_RATIO = 0.5  # 0.1 to 0.9
    DEFAULT_LOG_HEIGHT_RATIO = 0.25  # 0.1 to 0.5
    
    # Sorting settings
    DEFAULT_SORT_MODE = 'name'  # 'name', 'size', 'date'
    DEFAULT_SORT_REVERSE = False
    
    # Color settings
    USE_COLORS = True
    COLOR_SCHEME = 'dark'  # 'dark', 'light'
    
    # Behavior settings
    CONFIRM_DELETE = True   # Show confirmation dialog before deleting files/directories
    CONFIRM_QUIT = True     # Show confirmation dialog before quitting TFM
    CONFIRM_COPY = True     # Show confirmation dialog before copying files/directories
    CONFIRM_MOVE = True     # Show confirmation dialog before moving files/directories
    CONFIRM_EXTRACT_ARCHIVE = True  # Show confirmation dialog before extracting archives
    
    # Key bindings - customize your shortcuts
    KEY_BINDINGS = {
        'quit': ['q', 'Q'],
        'help': ['?'],
        'toggle_hidden': ['.'],
        'toggle_color_scheme': ['t'],
        'search': ['f', 'F'],
        'sort_menu': ['s', 'S'],
        'file_details': ['i', 'I'],
        'quick_sort_name': ['1'],
        'quick_sort_ext': ['2'],
        'quick_sort_size': ['3'],
        'quick_sort_date': ['4'],
        'select_file': [' '],  # Space
        'select_all_files': ['a'],
        'select_all_items': ['A'],
        'sync_panes': ['o', 'O'],
        'view_text': ['v', 'V'],
        'edit_file': ['e', 'E'],
        'copy_files': ['c', 'C'],
        'delete_files': ['k', 'K'],
        'rename_file': ['r', 'R'],
        'favorites': ['j', 'J'],
        'subshell': ['X'],
        'programs': ['x'],
        'create_archive': ['p', 'P'],
        'extract_archive': ['u', 'U'],
        'compare_selection': ['w', 'W'],
    }
    
    # Directory settings
    STARTUP_LEFT_PATH = None  # None = current directory, or specify path like "/home/user/projects"
    STARTUP_RIGHT_PATH = None  # None = home directory, or specify path
    
    # Favorite directories - customize your frequently used directories
    # Each entry should have 'name' and 'path' keys
    FAVORITE_DIRECTORIES = [
        {'name': 'Home', 'path': '~'},
        {'name': 'Documents', 'path': '~/Documents'},
        {'name': 'Downloads', 'path': '~/Downloads'},
        {'name': 'Desktop', 'path': '~/Desktop'},
        {'name': 'Projects', 'path': '~/Projects'},
        {'name': 'Root', 'path': '/'},
        {'name': 'Temp', 'path': '/tmp'},
        {'name': 'Config', 'path': '~/.config'},
        # Add your own favorites here:
        # {'name': 'Work', 'path': '/path/to/work'},
        # {'name': 'Scripts', 'path': '~/bin'},
    ]
    
    # Performance settings
    MAX_LOG_MESSAGES = 1000
    
    # File display settings
    SEPARATE_EXTENSIONS = True  # Show file extensions separately from basenames
    MAX_EXTENSION_LENGTH = 5    # Maximum extension length to show separately
    
    # Text editor settings
    TEXT_EDITOR = 'vim'  # Text editor command (vim, nano, emacs, code, etc.)
    
    # External programs - each item has "name", "command", and optional "options" fields
    # The "command" field is a list for safe subprocess execution
    # Relative paths in the first element are resolved relative to the TFM root directory (where tfm.py is located)
    # The "options" field is a dictionary with program-specific options:
    #   - auto_return: if True, automatically returns to TFM without waiting for user input
    PROGRAMS = [
        {'name': 'Git Status', 'command': ['git', 'status']},
        {'name': 'Git Log', 'command': ['git', 'log', '--oneline', '-10']},
        {'name': 'Disk Usage', 'command': ['du', '-sh', '*']},
        {'name': 'List Processes', 'command': ['ps', 'aux']},
        {'name': 'System Info', 'command': ['uname', '-a']},
        {'name': 'Network Connections', 'command': ['netstat', '-tuln']},
        {'name': 'Compare Files (BeyondCompare)', 'command': ['./tools/bcompare_files_wrapper.sh'], 'options': {'auto_return': True}},
        {'name': 'Compare Directories (BeyondCompare)', 'command': ['./tools/bcompare_dirs_wrapper.sh'], 'options': {'auto_return': True}},
        {'name': 'Tail Files (Last 10 Lines)', 'command': ['./tools/tail_files.sh'], 'options': {'auto_return': False}},
        # Add your own programs here:
        # {'name': 'My Script', 'command': ['/path/to/script.sh']},
        # {'name': 'Python REPL', 'command': ['python3']},
        # {'name': 'Quick Command', 'command': ['ls', '-la'], 'options': {'auto_return': True}},
    ]