#!/usr/bin/env python3
"""
TFM Configuration System

Manages user configuration for the Two-File Manager.
Configuration is stored in ~/.tfm/config.py as a Python class.
"""

import fnmatch
import importlib.util
import os
import sys
from tfm_path import Path
from ttk import KeyCode


# Special key name to TTK KeyCode mapping
SPECIAL_KEY_MAP = {
    'HOME': KeyCode.HOME,
    'END': KeyCode.END,
    'PPAGE': KeyCode.PAGE_UP,
    'NPAGE': KeyCode.PAGE_DOWN,
    'UP': KeyCode.UP,
    'DOWN': KeyCode.DOWN,
    'LEFT': KeyCode.LEFT,
    'RIGHT': KeyCode.RIGHT,
    'BACKSPACE': KeyCode.BACKSPACE,
    'DELETE': KeyCode.DELETE,
    'INSERT': KeyCode.INSERT,
    'F1': KeyCode.F1,
    'F2': KeyCode.F2,
    'F3': KeyCode.F3,
    'F4': KeyCode.F4,
    'F5': KeyCode.F5,
    'F6': KeyCode.F6,
    'F7': KeyCode.F7,
    'F8': KeyCode.F8,
    'F9': KeyCode.F9,
    'F10': KeyCode.F10,
    'F11': KeyCode.F11,
    'F12': KeyCode.F12,
}

# Reverse mapping for display purposes
SPECIAL_KEY_NAMES = {v: k for k, v in SPECIAL_KEY_MAP.items()}


class DefaultConfig:
    """Default configuration values for TFM"""
    
    # Backend settings
    PREFERRED_BACKEND = 'curses'  # 'curses' or 'coregraphics'
    
    # Desktop mode settings (for CoreGraphics backend)
    DESKTOP_FONT_NAME = 'Menlo'
    DESKTOP_FONT_SIZE = 12
    DESKTOP_WINDOW_WIDTH = 1200
    DESKTOP_WINDOW_HEIGHT = 800
    
    # Display settings
    SHOW_HIDDEN_FILES = False
    DEFAULT_LEFT_PANE_RATIO = 0.5
    DEFAULT_LOG_HEIGHT_RATIO = 0.25
    DATE_FORMAT = 'short'  # 'full' or 'short'
    
    # Sorting settings
    DEFAULT_SORT_MODE = 'name'  # 'name', 'size', 'date'
    DEFAULT_SORT_REVERSE = False
    
    # Color settings
    USE_COLORS = True
    COLOR_SCHEME = 'dark'  # 'dark', 'light'
    
    # Behavior settings
    CONFIRM_DELETE = True
    CONFIRM_QUIT = True
    CONFIRM_COPY = True
    CONFIRM_MOVE = True
    CONFIRM_EXTRACT_ARCHIVE = True
    
    # Key bindings (can be customized)
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
        'select_all': ['HOME'],                # Select all items (Home key)
        'unselect_all': ['END'],               # Unselect all items (End key)
        'sync_current_to_other': ['o'],        # Sync current pane directory to other pane
        'sync_other_to_current': ['O'],        # Sync other pane directory to current pane
        'view_file': ['v', 'V'],              # View file using configured viewer
        'edit_file': ['e'],                    # Edit selected file with configured text editor
        'create_file': ['E'],                  # Create new file (prompts for filename)
        'create_directory': {'keys': ['m', 'M'], 'selection': 'none'},  # Create new directory (only when no files selected)
        'toggle_fallback_colors': ['T'],       # Toggle fallback color mode for compatibility
        'view_options': ['z'],                 # Show view options menu
        'settings_menu': ['Z'],                # Show settings and configuration menu
        'copy_files': {'keys': ['c', 'C'], 'selection': 'required'},  # Copy selected files to other pane
        'move_files': {'keys': ['m', 'M'], 'selection': 'required'},  # Move selected files to other pane
        'delete_files': {'keys': ['k', 'K'], 'selection': 'required'}, # Delete selected files/directories
        'rename_file': ['r', 'R'],            # Rename selected file/directory
        'favorites': ['j'],                   # Show favorite directories dialog
        'jump_dialog': ['J'],                 # Show jump to directory dialog (Shift+J)
        'history': ['h', 'H'],                # Show history for current pane
        'subshell': ['X'],                     # Enter subshell (command line) mode
        'programs': ['x'],                     # Show external programs menu
        'create_archive': {'keys': ['p', 'P'], 'selection': 'required'}, # Create archive from selected files
        'extract_archive': ['u', 'U'],        # Extract selected archive file
        'compare_selection': ['w', 'W'],      # Show file and directory comparison options
        'adjust_pane_left': ['['],            # Make left pane smaller (move boundary left)
        'adjust_pane_right': [']'],           # Make left pane larger (move boundary right)
        'adjust_log_up': ['{'],               # Make log pane larger (Shift+[)
        'adjust_log_down': ['}'],             # Make log pane smaller (Shift+])
        'reset_log_height': ['_'],            # Reset log pane height to default (Shift+-)
    }
    
    # Favorite directories - list of dictionaries with 'name' and 'path' keys
    FAVORITE_DIRECTORIES = [
        {'name': 'Home', 'path': '~'},
        {'name': 'Documents', 'path': '~/Documents'},
        {'name': 'Downloads', 'path': '~/Downloads'},
        {'name': 'Desktop', 'path': '~/Desktop'},
        {'name': 'Projects', 'path': '~/Projects'},
        {'name': 'Root', 'path': '/'},
        {'name': 'Temp', 'path': '/tmp'},
        {'name': 'Config', 'path': '~/.config'},
    ]
    
    # Performance settings
    MAX_LOG_MESSAGES = 1000
    MAX_SEARCH_RESULTS = 10000  # Maximum number of search results to prevent memory issues
    MAX_JUMP_DIRECTORIES = 5000  # Maximum directories to scan for jump dialog
    
    # Progress animation settings
    PROGRESS_ANIMATION_PATTERN = 'spinner'  # 'spinner', 'dots', 'progress', 'bounce', 'pulse', 'wave', 'clock', 'arrow'
    PROGRESS_ANIMATION_SPEED = 0.2  # Animation frame update interval in seconds
    
    # History settings
    MAX_HISTORY_ENTRIES = 100  # Maximum number of history entries to keep
    
    # File display settings
    SEPARATE_EXTENSIONS = True  # Show file extensions separately from basenames
    MAX_EXTENSION_LENGTH = 5    # Maximum extension length to show separately
    
    # Text editor settings
    TEXT_EDITOR = 'vim'  # Default text editor command
    
    # Dialog settings
    INFO_DIALOG_WIDTH_RATIO = 0.8
    INFO_DIALOG_HEIGHT_RATIO = 0.8
    INFO_DIALOG_MIN_WIDTH = 20
    INFO_DIALOG_MIN_HEIGHT = 10
    
    # List dialog settings
    LIST_DIALOG_WIDTH_RATIO = 0.6
    LIST_DIALOG_HEIGHT_RATIO = 0.7
    LIST_DIALOG_MIN_WIDTH = 40
    LIST_DIALOG_MIN_HEIGHT = 15
    
    # S3 settings
    S3_CACHE_TTL = 60  # S3 cache TTL in seconds (default: 60 seconds)
    
    # Unicode and wide character settings
    UNICODE_MODE = 'auto'  # 'auto', 'full', 'basic', 'ascii'
    UNICODE_WARNINGS = True  # Show warnings for Unicode processing errors
    UNICODE_FALLBACK_CHAR = '?'  # Character to use for unrepresentable characters in ASCII mode
    UNICODE_ENABLE_CACHING = True  # Enable caching of display width calculations for performance
    UNICODE_CACHE_SIZE = 1000  # Maximum number of cached width calculations
    UNICODE_TERMINAL_DETECTION = True  # Enable automatic terminal capability detection
    UNICODE_FORCE_FALLBACK = False  # Force ASCII fallback mode regardless of terminal capabilities
    
    # File extension associations
    # Maps file patterns to programs for different actions (open, view, edit)
    # 
    # Compact Format:
    # - Pattern: Can be a string '*.pdf' or list ['*.jpg', '*.jpeg', '*.png']
    # - Actions: Use 'open|view' to assign same command to multiple actions
    # - Commands: List ['open', '-a', 'Preview'] or string 'open -a Preview'
    # - None: Action not available
    #
    # Examples:
    #   {'pattern': ['*.jpg', '*.png'], 'open|view': ['open', '-a', 'Preview'], 'edit': ['photoshop']}
    #   {'pattern': '*.pdf', 'open|view': ['preview'], 'edit': ['acrobat']}
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
            'open|view': ['open', '-a', 'Preview'],
        },
        # Audio files
        {
            'pattern': ['*.mp3', '*.wav'],
            'open|view': ['open', '-a', 'Music'],
        },
    ]


class ConfigManager:
    """Manages TFM configuration loading and saving"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.tfm'
        self.config_file = self.config_dir / 'config.py'
        self.config = None
        
    def ensure_config_dir(self):
        """Ensure the configuration directory exists"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Warning: Could not create config directory {self.config_dir}: {e}")
            return False
    
    def create_default_config(self):
        """Create a default configuration file by copying from template"""
        if not self.ensure_config_dir():
            return False
        
        try:
            # Get the directory where this module is located
            current_dir = Path(__file__).parent
            template_file = current_dir / '_config.py'
            
            # Check if template file exists
            if not template_file.exists():
                print(f"Warning: Template file not found at {template_file}")
                return False
            
            # Read the template file
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Write to user config file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            print(f"Created default configuration at: {self.config_file}")
            return True
            
        except Exception as e:
            print(f"Error creating default config: {e}")
            return False
    
    def load_config(self):
        """Load configuration from file or create default if not exists"""
        # Check if config file exists
        if not self.config_file.exists():
            print(f"Configuration file not found at: {self.config_file}")
            if self.create_default_config():
                print("Created default configuration file")
            else:
                print("Using built-in default configuration")
                self.config = DefaultConfig()
                return self.config
        
        # Try to load the configuration file
        try:
            # Load the config module dynamically
            spec = importlib.util.spec_from_file_location("user_config", self.config_file)
            if spec is None or spec.loader is None:
                raise ImportError("Could not load config file")
                
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            
            # Get the Config class
            if hasattr(config_module, 'Config'):
                self.config = config_module.Config()
                print(f"Loaded configuration from: {self.config_file}")
            else:
                raise AttributeError("Config class not found in configuration file")
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            print("Using built-in default configuration")
            self.config = DefaultConfig()
        
        return self.config
    
    def get_config(self):
        """Get the current configuration, loading if necessary"""
        if self.config is None:
            self.load_config()
        return self.config
    
    def reload_config(self):
        """Reload configuration from file"""
        self.config = None
        return self.load_config()
    
    def validate_config(self, config):
        """Validate configuration values"""
        errors = []
        
        # Validate backend selection
        if hasattr(config, 'PREFERRED_BACKEND'):
            if config.PREFERRED_BACKEND not in ['curses', 'coregraphics']:
                errors.append("PREFERRED_BACKEND must be 'curses' or 'coregraphics'")
        
        # Validate desktop mode settings
        if hasattr(config, 'DESKTOP_FONT_SIZE'):
            if not isinstance(config.DESKTOP_FONT_SIZE, int) or config.DESKTOP_FONT_SIZE < 8 or config.DESKTOP_FONT_SIZE > 72:
                errors.append("DESKTOP_FONT_SIZE must be an integer between 8 and 72")
        
        if hasattr(config, 'DESKTOP_WINDOW_WIDTH'):
            if not isinstance(config.DESKTOP_WINDOW_WIDTH, int) or config.DESKTOP_WINDOW_WIDTH < 400:
                errors.append("DESKTOP_WINDOW_WIDTH must be an integer >= 400")
        
        if hasattr(config, 'DESKTOP_WINDOW_HEIGHT'):
            if not isinstance(config.DESKTOP_WINDOW_HEIGHT, int) or config.DESKTOP_WINDOW_HEIGHT < 300:
                errors.append("DESKTOP_WINDOW_HEIGHT must be an integer >= 300")
        
        # Validate ratios
        if hasattr(config, 'DEFAULT_LEFT_PANE_RATIO'):
            if not (0.1 <= config.DEFAULT_LEFT_PANE_RATIO <= 0.9):
                errors.append("DEFAULT_LEFT_PANE_RATIO must be between 0.1 and 0.9")
        
        if hasattr(config, 'DEFAULT_LOG_HEIGHT_RATIO'):
            if not (0.1 <= config.DEFAULT_LOG_HEIGHT_RATIO <= 0.5):
                errors.append("DEFAULT_LOG_HEIGHT_RATIO must be between 0.1 and 0.5")
        
        # Validate sort mode
        if hasattr(config, 'DEFAULT_SORT_MODE'):
            if config.DEFAULT_SORT_MODE not in ['name', 'ext', 'size', 'date']:
                errors.append("DEFAULT_SORT_MODE must be 'name', 'ext', 'size', or 'date'")
        
        # Validate color scheme
        if hasattr(config, 'COLOR_SCHEME'):
            if config.COLOR_SCHEME not in ['dark', 'light']:
                errors.append("COLOR_SCHEME must be 'dark' or 'light'")
        
        # Validate Unicode mode
        if hasattr(config, 'UNICODE_MODE'):
            if config.UNICODE_MODE not in ['auto', 'full', 'basic', 'ascii']:
                errors.append("UNICODE_MODE must be 'auto', 'full', 'basic', or 'ascii'")
        
        # Validate Unicode fallback character
        if hasattr(config, 'UNICODE_FALLBACK_CHAR'):
            if not isinstance(config.UNICODE_FALLBACK_CHAR, str) or len(config.UNICODE_FALLBACK_CHAR) != 1:
                errors.append("UNICODE_FALLBACK_CHAR must be a single character string")
        
        # Validate Unicode cache size
        if hasattr(config, 'UNICODE_CACHE_SIZE'):
            if not isinstance(config.UNICODE_CACHE_SIZE, int) or config.UNICODE_CACHE_SIZE < 0:
                errors.append("UNICODE_CACHE_SIZE must be a non-negative integer")
        
        return errors
    
    def get_key_for_action(self, action):
        """Get the key binding for a specific action"""
        config = self.get_config()
        binding = None
        
        if hasattr(config, 'KEY_BINDINGS') and action in config.KEY_BINDINGS:
            binding = config.KEY_BINDINGS[action]
        elif hasattr(DefaultConfig, 'KEY_BINDINGS') and action in DefaultConfig.KEY_BINDINGS:
            binding = DefaultConfig.KEY_BINDINGS[action]
        
        if binding is None:
            return []
        
        # Handle both simple and extended formats
        if isinstance(binding, list):
            return binding
        elif isinstance(binding, dict) and 'keys' in binding:
            return binding['keys']
        
        return []
    
    def get_selection_requirement(self, action):
        """Get the selection requirement for a specific action"""
        config = self.get_config()
        binding = None
        
        if hasattr(config, 'KEY_BINDINGS') and action in config.KEY_BINDINGS:
            binding = config.KEY_BINDINGS[action]
        elif hasattr(DefaultConfig, 'KEY_BINDINGS') and action in DefaultConfig.KEY_BINDINGS:
            binding = DefaultConfig.KEY_BINDINGS[action]
        
        if binding is None:
            return 'any'
        
        # Handle extended format
        if isinstance(binding, dict) and 'selection' in binding:
            return binding['selection']
        
        # Simple format defaults to 'any'
        return 'any'
    
    def is_action_available(self, action, has_selection):
        """Check if action is available based on current selection status"""
        requirement = self.get_selection_requirement(action)
        if requirement == 'required':
            return has_selection
        elif requirement == 'none':
            return not has_selection
        else:  # 'any'
            return True
    
    def is_key_bound_to_action(self, key_char, action):
        """Check if a key is bound to a specific action"""
        keys = self.get_key_for_action(action)
        return key_char in keys
    
    def is_key_bound_to_action_with_selection(self, key_char, action, has_selection):
        """Check if a key is bound to a specific action and available for current selection status"""
        if not self.is_key_bound_to_action(key_char, action):
            return False
        return self.is_action_available(action, has_selection)
    
    def is_special_key_bound_to_action(self, key_code, action):
        """Check if a special key code is bound to a specific action"""
        keys = self.get_key_for_action(action)
        
        # Check if any of the keys match the special key code
        for key in keys:
            if isinstance(key, str) and key in SPECIAL_KEY_MAP:
                if SPECIAL_KEY_MAP[key] == key_code:
                    return True
        
        return False
    
    def is_special_key_bound_to_action_with_selection(self, key_code, action, has_selection):
        """Check if a special key is bound to a specific action and available for current selection status"""
        if not self.is_special_key_bound_to_action(key_code, action):
            return False
        return self.is_action_available(action, has_selection)
    
    def is_input_event_bound_to_action(self, event, action):
        """
        Check if a KeyEvent is bound to a specific action.
        
        Args:
            event: KeyEvent from TTK renderer
            action: Action name to check
            
        Returns:
            bool: True if event is bound to the action
        """
        if not event:
            return False
        
        # Import here to avoid circular dependency
        from tfm_input_utils import input_event_to_key_char
        
        key_char = input_event_to_key_char(event)
        if not key_char:
            return False
        
        return self.is_key_bound_to_action(key_char, action)
    
    def is_input_event_bound_to_action_with_selection(self, event, action, has_selection):
        """
        Check if a KeyEvent is bound to a specific action and respects selection requirements.
        
        Args:
            event: KeyEvent from TTK renderer
            action: Action name to check
            has_selection: Whether files are currently selected
            
        Returns:
            bool: True if event is bound to the action and selection requirement is met
        """
        if not event:
            return False
        
        # Import here to avoid circular dependency
        from tfm_input_utils import input_event_to_key_char
        
        key_char = input_event_to_key_char(event)
        if not key_char:
            return False
        
        return self.is_key_bound_to_action_with_selection(key_char, action, has_selection)
    
    def get_action_for_key(self, key):
        """
        Get the action bound to a key (character or special key code).
        
        Args:
            key: Either a character string or a curses key code (int)
        
        Returns:
            Action name if found, None otherwise
        """
        config = self.get_config()
        
        # Check both user config and default config (user config takes precedence)
        configs_to_check = []
        if hasattr(config, 'KEY_BINDINGS') and config.KEY_BINDINGS:
            configs_to_check.append(config.KEY_BINDINGS)
        if hasattr(DefaultConfig, 'KEY_BINDINGS'):
            configs_to_check.append(DefaultConfig.KEY_BINDINGS)
        
        for key_bindings in configs_to_check:
            for action, binding in key_bindings.items():
                # Get keys list
                keys = binding if isinstance(binding, list) else binding.get('keys', []) if isinstance(binding, dict) else []
                
                # Check if key matches
                for bound_key in keys:
                    if isinstance(key, str):
                        # Character key
                        if bound_key == key:
                            return action
                    elif isinstance(key, int):
                        # Special key code
                        if isinstance(bound_key, str) and bound_key in SPECIAL_KEY_MAP:
                            if SPECIAL_KEY_MAP[bound_key] == key:
                                return action
        
        return None


# Global configuration manager instance
config_manager = ConfigManager()


def get_config():
    """Get the current configuration"""
    return config_manager.get_config()


def reload_config():
    """Reload configuration from file"""
    return config_manager.reload_config()


def is_key_bound_to(key_char, action):
    """Check if a key is bound to a specific action"""
    return config_manager.is_key_bound_to_action(key_char, action)


def is_key_bound_to_with_selection(key_char, action, has_selection):
    """Check if a key is bound to a specific action and available for current selection status"""
    return config_manager.is_key_bound_to_action_with_selection(key_char, action, has_selection)


def is_action_available(action, has_selection):
    """Check if action is available based on current selection status"""
    return config_manager.is_action_available(action, has_selection)


def is_special_key_bound_to(key_code, action):
    """Check if a special key code is bound to a specific action"""
    return config_manager.is_special_key_bound_to_action(key_code, action)


def is_special_key_bound_to_with_selection(key_code, action, has_selection):
    """Check if a special key is bound to a specific action and available for current selection status"""
    return config_manager.is_special_key_bound_to_action_with_selection(key_code, action, has_selection)


def is_input_event_bound_to(event, action):
    """
    Check if a KeyEvent is bound to a specific action.
    
    Args:
        event: KeyEvent from TTK renderer
        action: Action name to check
        
    Returns:
        bool: True if event is bound to the action
    """
    return config_manager.is_input_event_bound_to_action(event, action)


def is_input_event_bound_to_with_selection(event, action, has_selection):
    """
    Check if a KeyEvent is bound to a specific action and respects selection requirements.
    
    Args:
        event: KeyEvent from TTK renderer
        action: Action name to check
        has_selection: Whether files are currently selected
        
    Returns:
        bool: True if event is bound to the action and selection requirement is met
    """
    return config_manager.is_input_event_bound_to_action_with_selection(event, action, has_selection)


def get_action_for_key(key):
    """Get the action bound to a key (character or special key code)"""
    return config_manager.get_action_for_key(key)



def get_favorite_directories():
    """Get the list of favorite directories from configuration"""
    config = get_config()
    
    favorites = []
    
    # Get favorites from user config or fall back to defaults
    favorites_config = None
    if hasattr(config, 'FAVORITE_DIRECTORIES') and config.FAVORITE_DIRECTORIES:
        favorites_config = config.FAVORITE_DIRECTORIES
    else:
        # Fall back to default favorites if not configured
        favorites_config = DefaultConfig.FAVORITE_DIRECTORIES
    
    if favorites_config:
        for fav in favorites_config:
            if isinstance(fav, dict) and 'name' in fav and 'path' in fav:
                try:
                    # Expand user path and resolve
                    path = Path(fav['path']).expanduser().resolve()
                    if path.exists() and path.is_dir():
                        favorites.append({
                            'name': fav['name'],
                            'path': str(path)
                        })
                    else:
                        print(f"Warning: Favorite directory does not exist: {fav['name']} -> {fav['path']}")
                except Exception as e:
                    print(f"Warning: Invalid favorite directory path: {fav['name']} -> {fav['path']}: {e}")
    
    return favorites


def get_programs():
    """Get the list of external programs from configuration"""
    config = get_config()
    
    programs = []
    
    # Get programs from user config
    if hasattr(config, 'PROGRAMS') and config.PROGRAMS:
        for prog in config.PROGRAMS:
            if isinstance(prog, dict) and 'name' in prog and 'command' in prog:
                if isinstance(prog['command'], list) and prog['command']:
                    program_entry = {
                        'name': prog['name'],
                        'command': prog['command']
                    }
                    
                    # Add options if present
                    if 'options' in prog and isinstance(prog['options'], dict):
                        program_entry['options'] = prog['options']
                    else:
                        program_entry['options'] = {}
                    
                    programs.append(program_entry)
                else:
                    print(f"Warning: Program command must be a non-empty list: {prog['name']}")
            else:
                print(f"Warning: Invalid program configuration: {prog}")
    
    return programs


def get_file_associations():
    """Get the file extension associations from configuration"""
    config = get_config()
    
    # Get associations from user config or fall back to defaults
    if hasattr(config, 'FILE_ASSOCIATIONS') and config.FILE_ASSOCIATIONS:
        return config.FILE_ASSOCIATIONS
    elif hasattr(DefaultConfig, 'FILE_ASSOCIATIONS'):
        return DefaultConfig.FILE_ASSOCIATIONS
    
    return []


def _expand_association_entry(entry):
    """
    Expand a compact association entry into individual pattern-action mappings.
    
    Args:
        entry: Dictionary with 'pattern' key and action keys
    
    Returns:
        List of (pattern, action, command) tuples
    """
    if not isinstance(entry, dict) or 'pattern' not in entry:
        return []
    
    # Get patterns as a list
    patterns = entry['pattern']
    if isinstance(patterns, str):
        patterns = [patterns]
    elif not isinstance(patterns, list):
        return []
    
    # Expand action keys (handle 'open|view' format)
    expanded = []
    for key, command in entry.items():
        if key == 'pattern':
            continue
        
        # Split combined action keys like 'open|view'
        actions = key.split('|')
        
        # Add mapping for each pattern and action combination
        for pattern in patterns:
            for action in actions:
                expanded.append((pattern, action.strip(), command))
    
    return expanded


def get_program_for_file(filename, action='open'):
    """
    Get the program command for a specific file and action.
    
    Checks FILE_ASSOCIATIONS entries in order from top to bottom.
    For each entry:
    1. Check if filename matches the pattern
    2. If pattern matches, check if the action exists in that entry
    3. If action exists, return the command (even if None)
    4. If pattern doesn't match OR action doesn't exist, continue to next entry
    
    Args:
        filename: The filename to check (e.g., 'document.pdf')
        action: The action to perform ('open', 'view', or 'edit')
    
    Returns:
        Command list if found, None otherwise
    """
    associations = get_file_associations()
    if not associations:
        return None
    
    # Convert filename to lowercase for case-insensitive matching
    filename_lower = filename.lower()
    
    # Check each entry in order from top to bottom
    for entry in associations:
        if not isinstance(entry, dict) or 'pattern' not in entry:
            continue
        
        # Get patterns as a list
        patterns = entry['pattern']
        if isinstance(patterns, str):
            patterns = [patterns]
        elif not isinstance(patterns, list):
            continue
        
        # Check if filename matches any pattern in this entry
        pattern_matches = False
        for pattern in patterns:
            if fnmatch.fnmatch(filename_lower, pattern.lower()):
                pattern_matches = True
                break
        
        # If pattern doesn't match, continue to next entry
        if not pattern_matches:
            continue
        
        # Pattern matches - now check if action exists in this entry
        # Look for the action in both simple and combined formats
        action_found = False
        command = None
        
        for key, value in entry.items():
            if key == 'pattern':
                continue
            
            # Check if this key contains our action (handle 'open|view' format)
            actions_in_key = [a.strip() for a in key.split('|')]
            if action in actions_in_key:
                action_found = True
                command = value
                break
        
        # If action is found in this entry, return the command
        if action_found:
            # Convert string commands to list format
            if isinstance(command, str):
                return command.split()
            elif isinstance(command, list):
                return command
            elif command is None:
                return None
        
        # Pattern matched but action not in this entry - continue to next entry
    
    # No matching entry found
    return None


def has_action_for_file(filename, action='open'):
    """
    Check if a specific action is available for a file.
    
    Args:
        filename: The filename to check
        action: The action to check ('open', 'view', or 'edit')
    
    Returns:
        True if the action is available, False otherwise
    """
    program = get_program_for_file(filename, action)
    return program is not None


def has_explicit_association(filename, action='open'):
    """
    Check if a file has an explicit association (including None) for an action.
    
    This differs from has_action_for_file in that it returns True even when
    the association is explicitly set to None, which indicates "use built-in viewer".
    
    Checks FILE_ASSOCIATIONS entries in order from top to bottom.
    
    Args:
        filename: The filename to check
        action: The action to check ('open', 'view', or 'edit')
    
    Returns:
        True if an explicit association exists (even if None), False if no association
    """
    associations = get_file_associations()
    if not associations:
        return False
    
    # Convert filename to lowercase for case-insensitive matching
    filename_lower = filename.lower()
    
    # Check each entry in order from top to bottom
    for entry in associations:
        if not isinstance(entry, dict) or 'pattern' not in entry:
            continue
        
        # Get patterns as a list
        patterns = entry['pattern']
        if isinstance(patterns, str):
            patterns = [patterns]
        elif not isinstance(patterns, list):
            continue
        
        # Check if filename matches any pattern in this entry
        pattern_matches = False
        for pattern in patterns:
            if fnmatch.fnmatch(filename_lower, pattern.lower()):
                pattern_matches = True
                break
        
        # If pattern doesn't match, continue to next entry
        if not pattern_matches:
            continue
        
        # Pattern matches - check if action exists in this entry
        for key in entry.keys():
            if key == 'pattern':
                continue
            
            # Check if this key contains our action
            actions_in_key = [a.strip() for a in key.split('|')]
            if action in actions_in_key:
                # Found an explicit association (even if value is None)
                return True
        
        # Pattern matched but action not in this entry - continue to next entry
    
    return False