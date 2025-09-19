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
    COLOR_SCHEME = 'default'  # 'default', 'dark', 'light'
    
    # Behavior settings
    CONFIRM_DELETE = True
    CONFIRM_QUIT = True
    AUTO_REFRESH = True
    
    # Key bindings - customize your shortcuts
    KEY_BINDINGS = {
        'quit': ['q', 'Q'],
        'help': ['?', 'h'],
        'toggle_hidden': ['H'],
        'search': ['f', 'F'],
        'file_operations': ['m', 'M'],
        'sort_menu': ['s', 'S'],
        'file_details': ['i', 'I'],
        'quick_sort_name': ['1'],
        'quick_sort_size': ['2'],
        'quick_sort_date': ['3'],
        'toggle_reverse_sort': ['r', 'R'],
        'select_file': [' '],  # Space
        'select_all_files': ['a'],
        'select_all_items': ['A'],
        'sync_panes': ['o', 'O'],
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
    
    # Performance settings
    MAX_LOG_MESSAGES = 1000
    REFRESH_INTERVAL = 1.0  # seconds
    
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