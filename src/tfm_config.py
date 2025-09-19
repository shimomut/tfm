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
    COLOR_SCHEME = 'default'  # 'default', 'dark', 'light'
    
    # Behavior settings
    CONFIRM_DELETE = True
    CONFIRM_QUIT = True
    AUTO_REFRESH = True
    
    # Key bindings (can be customized)
    KEY_BINDINGS = {
        'quit': ['q', 'Q'],
        'help': ['?', 'h'],
        'toggle_hidden': ['H'],
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
        'move_files': ['m', 'M'],
        'delete_files': ['k', 'K'],
        'rename_file': ['r', 'R'],
    }
    
    # File associations (for future use)
    FILE_ASSOCIATIONS = {
        '.txt': 'text_editor',
        '.py': 'python_editor',
        '.md': 'markdown_viewer',
    }
    
    # Directory settings
    STARTUP_LEFT_PATH = None  # None = current directory
    STARTUP_RIGHT_PATH = None  # None = home directory
    
    # Performance settings
    MAX_LOG_MESSAGES = 1000
    REFRESH_INTERVAL = 1.0  # seconds
    
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
            if config.DEFAULT_SORT_MODE not in ['name', 'size', 'date']:
                errors.append("DEFAULT_SORT_MODE must be 'name', 'size', or 'date'")
        
        # Validate color scheme
        if hasattr(config, 'COLOR_SCHEME'):
            if config.COLOR_SCHEME not in ['default', 'dark', 'light']:
                errors.append("COLOR_SCHEME must be 'default', 'dark', or 'light'")
        
        return errors
    
    def get_key_for_action(self, action):
        """Get the key binding for a specific action"""
        config = self.get_config()
        if hasattr(config, 'KEY_BINDINGS') and action in config.KEY_BINDINGS:
            return config.KEY_BINDINGS[action]
        elif hasattr(DefaultConfig, 'KEY_BINDINGS') and action in DefaultConfig.KEY_BINDINGS:
            return DefaultConfig.KEY_BINDINGS[action]
        return []
    
    def is_key_bound_to_action(self, key_char, action):
        """Check if a key is bound to a specific action"""
        keys = self.get_key_for_action(action)
        return key_char in keys


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