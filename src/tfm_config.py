#!/usr/bin/env python3
"""
TFM Configuration System

Manages user configuration for the Two-File Manager.
Configuration is stored in ~/.tfm/config.py as a Python class.
"""

import os
import sys
from pathlib import Path
import importlib.util


class DefaultConfig:
    """Default configuration values for TFM"""
    
    # Display settings
    SHOW_HIDDEN_FILES = False
    DEFAULT_LEFT_PANE_RATIO = 0.5
    DEFAULT_LOG_HEIGHT_RATIO = 0.25
    
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
        'sync_current_to_other': ['o'],        # Sync current pane directory to other pane
        'sync_other_to_current': ['O'],        # Sync other pane directory to current pane
        'view_text': ['v', 'V'],              # View text file in built-in viewer
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
        'favorites': ['j', 'J'],              # Show favorite directories dialog
        'history': ['h', 'H'],                # Show history for current pane
        'subshell': ['X'],                     # Enter subshell (command line) mode
        'programs': ['x'],                     # Show external programs menu
        'create_archive': {'keys': ['p', 'P'], 'selection': 'required'}, # Create archive from selected files
        'extract_archive': ['u', 'U'],        # Extract selected archive file
        'compare_selection': {'keys': ['w', 'W'], 'selection': 'required'}, # Show file comparison options
        'adjust_pane_left': ['['],            # Make left pane smaller (move boundary left)
        'adjust_pane_right': [']'],           # Make left pane larger (move boundary right)
        'adjust_log_up': ['{'],               # Make log pane larger (Shift+[)
        'adjust_log_down': ['}'],             # Make log pane smaller (Shift+])
        'reset_log_height': ['_'],            # Reset log pane height to default (Shift+-)
    }
    
    # Directory settings
    STARTUP_LEFT_PATH = None  # None = current directory
    STARTUP_RIGHT_PATH = None  # None = home directory
    
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
    
    # Search animation settings
    SEARCH_ANIMATION_PATTERN = 'spinner'  # 'spinner', 'dots', 'progress'
    SEARCH_ANIMATION_SPEED = 0.2  # Animation frame update interval in seconds
    
    # History settings
    MAX_HISTORY_ENTRIES = 100  # Maximum number of history entries to keep
    
    # File display settings
    SEPARATE_EXTENSIONS = True  # Show file extensions separately from basenames
    MAX_EXTENSION_LENGTH = 5    # Maximum extension length to show separately
    
    # Text editor settings
    TEXT_EDITOR = 'vim'  # Default text editor command
    
    # Info dialog settings
    INFO_DIALOG_WIDTH_RATIO = 0.8
    INFO_DIALOG_HEIGHT_RATIO = 0.8
    INFO_DIALOG_MIN_WIDTH = 20
    INFO_DIALOG_MIN_HEIGHT = 10


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


def get_startup_paths():
    """Get the configured startup paths for left and right panes"""
    config = get_config()
    
    left_path = None
    right_path = None
    
    if hasattr(config, 'STARTUP_LEFT_PATH') and config.STARTUP_LEFT_PATH:
        try:
            left_path = Path(config.STARTUP_LEFT_PATH).expanduser().resolve()
            if not left_path.exists() or not left_path.is_dir():
                print(f"Warning: Configured left startup path does not exist: {left_path}")
                left_path = None
        except Exception as e:
            print(f"Warning: Invalid left startup path: {e}")
            left_path = None
    
    if hasattr(config, 'STARTUP_RIGHT_PATH') and config.STARTUP_RIGHT_PATH:
        try:
            right_path = Path(config.STARTUP_RIGHT_PATH).expanduser().resolve()
            if not right_path.exists() or not right_path.is_dir():
                print(f"Warning: Configured right startup path does not exist: {right_path}")
                right_path = None
        except Exception as e:
            print(f"Warning: Invalid right startup path: {e}")
            right_path = None
    
    # Use defaults if not configured or invalid
    if left_path is None:
        left_path = Path.cwd()
    if right_path is None:
        right_path = Path.home()
    
    return left_path, right_path


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