#!/usr/bin/env python3
"""
TFM User Configuration

This file contains your personal TFM configuration.
You can modify any of these settings to customize TFM behavior.
"""

import platform
import sys

# Import tfm_tool function and tfm_python variable for external program configuration
from tfm_external_programs import tfm_tool, tfm_python

# Import backend detector for runtime backend detection
from tfm_backend_detector import is_desktop_mode

class Config:
    """User configuration for TFM"""
    
    # Backend settings
    PREFERRED_BACKEND = 'curses'  # 'curses' or 'coregraphics'
    # - 'curses': Terminal mode (default, works on all platforms)
    # - 'coregraphics': Desktop mode (macOS only, requires PyObjC)
    
    # Desktop mode settings (for CoreGraphics backend)
    DESKTOP_FONT_NAME = ['Menlo', 'Monaco', 'Courier', 'Osaka-Mono', 'Hiragino Sans GB']  # Font names for desktop mode (first is primary, rest are cascade fallbacks)
    DESKTOP_FONT_SIZE = 12  # Font size for desktop mode (8-72 points)
    DESKTOP_WINDOW_WIDTH = 1200  # Initial window width in pixels
    DESKTOP_WINDOW_HEIGHT = 800  # Initial window height in pixels
    
    # Display settings
    SHOW_HIDDEN_FILES = False
    DEFAULT_LEFT_PANE_RATIO = 0.5  # 0.1 to 0.9
    DEFAULT_LOG_HEIGHT_RATIO = 0.25  # 0.1 to 0.5
    DATE_FORMAT = 'short'  # 'short' (YY-MM-DD HH:mm) or 'full' (YYYY-MM-DD HH:mm:ss)
    
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
    # 
    # Supported formats:
    # 1. Simple format: 'action': ['key1', 'key2']
    #    - Works regardless of selection status
    #    - Keys can be characters ('a', 'Q') or special key names ('HOME', 'END')
    # 
    # 2. Extended format: 'action': {'keys': ['key1', 'key2'], 'selection': 'any|required|none'}
    #    - 'any': works regardless of selection status (default)
    #    - 'required': only works when at least one item is explicitly selected
    #    - 'none': only works when no items are explicitly selected
    #
    # Special key names (use these strings in the keys list):
    #   'HOME', 'END', 'PPAGE', 'NPAGE', 'UP', 'DOWN',
    #   'LEFT', 'RIGHT', 'BACKSPACE', 'DELETE', 'INSERT',
    #   'F1' through 'F12'
    #
    KEY_BINDINGS = {
        # === Application Control ===
        'quit': ['Q'],                         # Exit TFM application
        'help': ['?'],                         # Show help dialog with all key bindings
        
        # === Navigation ===
        'cursor_up': ['UP'],                   # Move cursor up one item
        'cursor_down': ['DOWN'],               # Move cursor down one item
        'page_up': ['PAGE_UP'],                # Move cursor up one page
        'page_down': ['PAGE_DOWN'],            # Move cursor down one page
        'open_item': ['ENTER'],                # Open file/directory or enter directory
        'go_parent': ['BACKSPACE'],            # Go to parent directory
        'switch_pane': ['TAB'],                # Switch between left and right panes
        'nav_left': ['LEFT'],                  # Left pane: go to parent, Right pane: switch to left pane
        'nav_right': ['RIGHT'],                # Right pane: go to parent, Left pane: switch to right pane
        
        # === File Selection ===
        'select_file': ['SPACE'],              # Toggle selection of current file
        'select_file_up': ['Shift-SPACE'],     # Toggle selection and move up
        'select_all': ['HOME'],                # Select all items (Home key)
        'unselect_all': ['END'],               # Unselect all items (End key)
        'select_all_files': ['A'],             # Toggle selection of all files in current pane
        'select_all_items': ['Shift-A'],       # Toggle selection of all items (files + dirs)
        
        # === File Operations ===
        'copy_files': {'keys': ['C'], 'selection': 'required'},  # Copy selected files to other pane
        'move_files': {'keys': ['M'], 'selection': 'required'},  # Move selected files to other pane
        'delete_files': {'keys': ['K', 'DELETE', 'Command-Backspace'], 'selection': 'required'}, # Delete selected files/directories
        'rename_file': ['R'],                  # Rename selected file/directory
        'create_file': ['Shift-E'],            # Create new file (prompts for filename)
        'create_directory': {'keys': ['M'], 'selection': 'none'},  # Create new directory (only when no files selected)
        
        # === File Viewing & Editing ===
        'view_file': ['V'],                    # View file using configured viewer
        'edit_file': ['E'],                    # Edit selected file with configured text editor
        'file_details': ['I'],                 # Show detailed file information dialog
        
        # === File Comparison ===
        'diff_files': ['EQUAL'],               # Compare two selected files side-by-side
        'diff_directories': ['Shift-EQUAL'],   # Compare directories recursively
        
        # === Archive Operations ===
        'create_archive': {'keys': ['P'], 'selection': 'required'}, # Create archive from selected files
        'extract_archive': ['U'],              # Extract selected archive file
        
        # === Search & Filter ===
        'search': ['F'],                       # Enter incremental search mode (isearch)
        'search_dialog': ['Shift-F'],          # Show filename search dialog
        'search_content': ['Shift-G'],         # Show content search dialog (grep)
        'filter': [';'],                       # Enter filter mode to show only matching files
        'clear_filter': [':'],                 # Clear current file filter
        
        # === Sorting ===
        'sort_menu': ['S'],                    # Show sort options menu
        'quick_sort_name': ['1'],              # Quick sort by filename
        'quick_sort_ext': ['2'],               # Quick sort by file extension
        'quick_sort_size': ['3'],              # Quick sort by file size
        'quick_sort_date': ['4'],              # Quick sort by modification date
        
        # === Directory Navigation ===
        'favorites': ['J'],                    # Show favorite directories dialog
        'jump_to_path': ['Shift-J'],           # Jump to path
        'history': ['H'],                      # Show history for current pane
        'drives_dialog': ['D'],                # Show drives/volumes dialog
        
        # === Pane Management ===
        'sync_current_to_other': ['O'],        # Sync current pane directory to other pane
        'sync_other_to_current': ['Shift-O'],  # Sync other pane directory to current pane
        'compare_selection': ['W'],            # Show file and directory comparison options
        'adjust_pane_left': ['['],             # Make left pane smaller (move boundary left)
        'adjust_pane_right': [']'],            # Make left pane larger (move boundary right)
        'reset_pane_boundary': ['-'],          # Reset pane split to 50% | 50%
        
        # === Log Pane Control ===
        'adjust_log_up': ['{'],                # Make log pane larger (Shift+[)
        'adjust_log_down': ['}'],              # Make log pane smaller (Shift+])
        'reset_log_height': ['_'],             # Reset log pane height to default (Shift+-)
        'scroll_log_up': ['Shift-UP'],         # Scroll log pane up one line
        'scroll_log_down': ['Shift-DOWN'],     # Scroll log pane down one line
        'scroll_log_page_up': ['Shift-LEFT'],  # Scroll log pane up one page (to older messages)
        'scroll_log_page_down': ['Shift-RIGHT'], # Scroll log pane down one page (to newer messages)
        
        # === Display & Appearance ===
        'toggle_hidden': ['.'],                # Toggle visibility of hidden files (dotfiles)
        'toggle_color_scheme': ['T'],          # Switch between dark and light color schemes
        'toggle_fallback_colors': ['Shift-T'], # Toggle fallback color mode for compatibility
        'view_options': ['Z'],                 # Show view options menu
        'settings_menu': ['Shift-Z'],          # Show settings and configuration menu
        
        # === External Programs ===
        'programs': ['X'],                     # Show external programs menu
        'subshell': ['Shift-X'],               # Enter subshell (command line) mode
    }
    
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
    MAX_SEARCH_RESULTS = 10000  # Maximum number of search results to prevent memory issues
    MAX_JUMP_DIRECTORIES = 5000  # Maximum directories to scan for jump dialog
    
    # History settings
    MAX_HISTORY_ENTRIES = 100  # Maximum number of history entries to keep
    
    # Progress animation settings
    PROGRESS_ANIMATION_PATTERN = 'spinner'  # 'spinner', 'dots', 'progress', 'bounce', 'pulse', 'wave', 'clock', 'arrow'
    PROGRESS_ANIMATION_SPEED = 0.2  # Animation frame update interval in seconds
    
    # File display settings
    SEPARATE_EXTENSIONS = True  # Show file extensions separately from basenames
    MAX_EXTENSION_LENGTH = 5    # Maximum extension length to show separately
    
    # Text editor settings
    # Supports both string and list formats:
    # - String format: 'vim' (single command, no arguments)
    # - List format: ['code', '--wait'] (command with arguments)
    # Automatically set based on actual running backend mode:
    # - Terminal mode (curses): vim
    # - Desktop mode (coregraphics): code (VS Code)
    TEXT_EDITOR = 'code' if is_desktop_mode() else 'vim'
    
    # Text diff tool settings
    # Tool invoked when pressing 'E' (edit_file) key in DiffViewer or DirectoryDiffViewer
    # Supports both string and list formats:
    # - String format: 'vimdiff' (single command, no arguments)
    # - List format: ['code', '--diff'] (command with arguments)
    # Automatically set based on actual running backend mode:
    # - Terminal mode (curses): vimdiff (string format example)
    # - Desktop mode (coregraphics): code --diff (list format example)
    TEXT_DIFF = ['code', '--diff'] if is_desktop_mode() else 'vimdiff'
    
    # S3 settings
    S3_CACHE_TTL = 60  # S3 cache TTL in seconds (default: 60 seconds)
    
    # Unicode and wide character settings
    UNICODE_MODE = 'auto'  # 'auto', 'full', 'basic', 'ascii'
    # - 'auto': Automatically detect terminal capabilities (recommended)
    # - 'full': Full Unicode support with wide character handling
    # - 'basic': Basic Unicode support, treat all characters as single-width
    # - 'ascii': ASCII-only fallback mode for limited terminals
    UNICODE_WARNINGS = True  # Show warnings for Unicode processing errors
    UNICODE_FALLBACK_CHAR = '?'  # Character to use for unrepresentable characters in ASCII mode
    UNICODE_TERMINAL_DETECTION = True  # Enable automatic terminal capability detection
    
    # File extension associations
    # Maps file patterns to programs for different actions (open, view, edit)
    # 
    # Compact Format Features:
    # 1. Multiple patterns in one entry: ['*.jpg', '*.jpeg', '*.png']
    # 2. Combined actions: 'open|view' assigns same command to both actions
    # 3. Commands: List ['open', '-a', 'Preview'] or string 'open -a Preview'
    # 4. None: Action not available
    #
    # Format:
    # {
    #     'pattern': '*.pdf' or ['*.jpg', '*.png'],  # Single or multiple fnmatch patterns
    #     'open|view': ['command'],  # Same command for open and view
    #     'edit': ['command']        # Different command for edit
    # }
    FILE_ASSOCIATIONS = [
        # PDF files
        {
            'pattern': '*.pdf',
            'open|view': ['open', '-a', 'Preview'],
        },
        # Image files
        {
            'pattern': ['*.jpg', '*.jpeg', '*.png', '*.gif'],
            'open|view': ['open', '-a', 'Preview'],
        },
        # Video files
        {
            'pattern': ['*.mp4', '*.mov'],
            'open|view': ['open', '-a', 'QuickTime Player'],
        },
        # Audio files
        {
            'pattern': ['*.mp3', '*.wav'],
            'open': ['open', '-a', 'Music'],
        },
        # Microsoft Word documents
        {
            'pattern': ['*.doc', '*.docx'],
            'open|view|edit': ['open', '-a', 'Microsoft Word'],
        },
        # Microsoft Excel spreadsheets
        {
            'pattern': ['*.xls', '*.xlsx'],
            'open|view|edit': ['open', '-a', 'Microsoft Excel'],
        },
        # Microsoft PowerPoint presentations
        {
            'pattern': ['*.ppt', '*.pptx'],
            'open|view|edit': ['open', '-a', 'Microsoft PowerPoint'],
        },
        # Add your own file associations here:
        # {
        #     'pattern': ['*.ext1', '*.ext2'],
        #     'open|view': ['command', 'args'],
        #     'edit': ['command', 'args']
        # },
    ]
    
    # External programs - each item has "name", "command", and optional "options" fields
    # The "command" field is a list for safe subprocess execution
    # Relative paths in the first element are resolved relative to the TFM root directory (where tfm.py is located)
    # Use tfm_tool('tool_name') to search for tools in:
    #   1. ~/.tfm/tools/ (user-specific tools, highest priority)
    #   2. {tfm.py directory}/tools/ (system tools, fallback)
    # The "options" field is a dictionary with program-specific options:
    #   - auto_return: if True, automatically returns to TFM without waiting for user input
    PROGRAMS = [
        {'name': 'Git Status', 'command': ['git', 'status']},
        {'name': 'Git Log', 'command': ['git', 'log', '--oneline', '-10']},
        {'name': 'Disk Usage', 'command': ['du', '-sh', '*']},
        {'name': 'List Processes', 'command': ['ps', 'aux']},
        {'name': 'System Info', 'command': ['uname', '-a']},
        {'name': 'Network Connections', 'command': ['netstat', '-tuln']},
        {'name': 'Compare Files (BeyondCompare)', 'command': [tfm_python, tfm_tool('bcompare_files.py')], 'options': {'auto_return': True}},
        {'name': 'Compare Directories (BeyondCompare)', 'command': [tfm_python, tfm_tool('bcompare_dirs.py')], 'options': {'auto_return': True}},
        {'name': 'Open in VSCode', 'command': [tfm_python, tfm_tool('vscode.py')], 'options': {'auto_return': True}},
        {'name': 'Open in Kiro', 'command': [tfm_python, tfm_tool('kiro.py')], 'options': {'auto_return': True}},
        {'name': 'Preview Files', 'command': [tfm_python, tfm_tool('preview_files.py')], 'options': {'auto_return': True}},
        {'name': 'Reveal in File Manager', 'command': [tfm_python, tfm_tool('reveal_in_finder.py')], 'options': {'auto_return': True}},

        # Add your own programs here:
        # {'name': 'My Custom Tool', 'command': [tfm_python, tfm_tool('my_custom_tool.py')], 'options': {'auto_return': True}},
        # {'name': 'My Script (direct path)', 'command': [tfm_python, '/path/to/script.py']},
        # {'name': 'Python REPL', 'command': ['python3']},
        # {'name': 'Quick Command', 'command': ['ls', '-la'], 'options': {'auto_return': True}},
    ]