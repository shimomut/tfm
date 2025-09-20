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
    CONFIRM_DELETE = True
    CONFIRM_QUIT = True
    AUTO_REFRESH = True
    
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
        'quick_sort_size': ['2'],
        'quick_sort_date': ['3'],
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
    }
    
    # File associations (for future use)
    FILE_ASSOCIATIONS = {
        '.txt': 'text_editor',
        '.py': 'python_editor',
        '.md': 'markdown_viewer',
        '.jpg': 'image_viewer',
        '.png': 'image_viewer',
        '.pdf': 'pdf_viewer',
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
    REFRESH_INTERVAL = 1.0  # seconds
    
    # Text editor settings
    TEXT_EDITOR = 'vim'  # Text editor command (vim, nano, emacs, code, etc.)
    
    # Info dialog settings
    INFO_DIALOG_WIDTH_RATIO = 0.8
    INFO_DIALOG_HEIGHT_RATIO = 0.8
    INFO_DIALOG_MIN_WIDTH = 20
    INFO_DIALOG_MIN_HEIGHT = 10
    
    # Advanced settings
    DEBUG_MODE = False
    LOG_LEVEL = 'INFO'  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    
    # Custom commands (for future use)
    CUSTOM_COMMANDS = {
        # Example: 'git_status': 'git status --short',
        # Example: 'disk_usage': 'du -sh *',
    }
    
    # External programs - each item has "name", "command", and optional "options" fields
    # The "command" field is a list for safe subprocess execution
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
        # Add your own programs here:
        # {'name': 'My Script', 'command': ['/path/to/script.sh']},
        # {'name': 'Python REPL', 'command': ['python3']},
        # {'name': 'Quick Command', 'command': ['ls', '-la'], 'options': {'auto_return': True}},
    ]