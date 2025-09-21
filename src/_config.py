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
    # Each action can have multiple keys assigned to it
    KEY_BINDINGS = {
        'quit': ['q', 'Q'],                    # Exit TFM application
        'help': ['?'],                         # Show help dialog with all key bindings
        'toggle_hidden': ['.'],                # Toggle visibility of hidden files (dotfiles)
        'toggle_color_scheme': ['t'],          # Switch between dark and light color schemes
        'search': ['f'],                       # Enter incremental search mode (isearch)
        'search_dialog': ['F'],                # Show filename search dialog
        'search_content': ['G'],               # Show content search dialog (grep)
        'filter': [';'],                       # Enter filter mode to show only matching files
        'clear_filter': [':'],                 # Clear current file filter
        'sort_menu': ['s', 'S'],              # Show sort options menu
        'file_details': ['i', 'I'],           # Show detailed file information dialog
        'quick_sort_name': ['1'],              # Quick sort by filename
        'quick_sort_ext': ['2'],               # Quick sort by file extension
        'quick_sort_size': ['3'],              # Quick sort by file size
        'quick_sort_date': ['4'],              # Quick sort by modification date
        'select_file': [' '],                  # Toggle selection of current file (Space)
        'select_all_files': ['a'],             # Toggle selection of all files in current pane
        'select_all_items': ['A'],             # Toggle selection of all items (files + dirs)
        'sync_current_to_other': ['o'],        # Sync current pane directory to other pane
        'sync_other_to_current': ['O'],        # Sync other pane directory to current pane
        'view_text': ['v', 'V'],              # View text file in built-in viewer
        'edit_file': ['e'],                    # Edit selected file with configured text editor
        'create_file': ['E'],                  # Create new file (prompts for filename)
        'file_type_filter': ['T'],             # Show file type filter dialog
        'toggle_fallback_colors': ['z'],       # Toggle fallback color mode for compatibility
        'view_options': ['Z'],                 # Show view options menu
        'settings_menu': ['L'],                # Show settings and configuration menu
        'copy_files': ['c', 'C'],             # Copy selected files to other pane
        'move_files': ['m', 'M'],             # Move selected files to other pane
        'delete_files': ['k', 'K'],           # Delete selected files/directories
        'rename_file': ['r', 'R'],            # Rename selected file/directory
        'favorites': ['j', 'J'],              # Show favorite directories dialog
        'subshell': ['X'],                     # Enter subshell (command line) mode
        'programs': ['x'],                     # Show external programs menu
        'create_archive': ['p', 'P'],         # Create archive from selected files
        'extract_archive': ['u', 'U'],        # Extract selected archive file
        'compare_selection': ['w', 'W'],      # Show file comparison options
        'adjust_pane_left': ['['],            # Make left pane smaller (move boundary left)
        'adjust_pane_right': [']'],           # Make left pane larger (move boundary right)
        'adjust_log_up': ['{'],               # Make log pane larger (Shift+[)
        'adjust_log_down': ['}'],             # Make log pane smaller (Shift+])
        'reset_log_height': ['_'],            # Reset log pane height to default (Shift+-)
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