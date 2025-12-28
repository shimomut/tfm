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
from tfm_log_manager import getLogger




# Module-level logger
logger = getLogger("Config")


class KeyBindings:
    """
    Manages key bindings and provides lookup functionality.
    
    This class encapsulates all key binding logic, including:
    - Parsing key expressions with modifiers
    - Matching KeyEvents against configured bindings
    - Looking up actions from key events
    - Looking up key expressions from actions
    """
    
    def __init__(self, key_bindings_config: dict):
        """
        Initialize KeyBindings with configuration.
        
        Args:
            key_bindings_config: KEY_BINDINGS dictionary from Config
        """
        self.logger = getLogger("KeyBindings")
        self._bindings = key_bindings_config
        
        # Build reverse lookup: (main_key, modifiers) -> [(action, selection_req), ...]
        self._key_to_actions = self._build_key_lookup()
    
    def _parse_key_expression(self, key_expr: str) -> tuple:
        """
        Parse a key expression into main key and modifier flags.
        
        Args:
            key_expr: Key expression string (e.g., "Shift-Down", "Command-Shift-X", "q")
        
        Returns:
            Tuple of (main_key, modifier_flags)
            - main_key: The main key as uppercase string
            - modifier_flags: Bitwise OR of ModifierKey values
        
        Examples:
            "q" -> ("Q", 0)
            "Shift-Down" -> ("DOWN", ModifierKey.SHIFT)
            "Command-Shift-X" -> ("X", ModifierKey.COMMAND | ModifierKey.SHIFT)
        """
        # Import ModifierKey here to avoid circular dependency
        from ttk import ModifierKey
        
        # Single character - return as-is with no modifiers
        if len(key_expr) == 1:
            return (key_expr.upper(), 0)
        
        # Multi-character - parse as key expression
        parts = key_expr.split('-')
        
        # Last part is the main key
        main_key = parts[-1].upper()
        
        # Earlier parts are modifiers
        modifiers = 0
        for part in parts[:-1]:
            modifier_name = part.upper()
            if modifier_name == 'SHIFT':
                modifiers |= ModifierKey.SHIFT
            elif modifier_name == 'CONTROL' or modifier_name == 'CTRL':
                modifiers |= ModifierKey.CONTROL
            elif modifier_name == 'ALT' or modifier_name == 'OPTION':
                modifiers |= ModifierKey.ALT
            elif modifier_name == 'COMMAND' or modifier_name == 'CMD':
                modifiers |= ModifierKey.COMMAND
            else:
                self.logger.warning(f"Unknown modifier in key expression: {part}")
        
        return (main_key, modifiers)
    
    def _keycode_from_string(self, key_str: str):
        """
        Convert a KeyCode name string to its integer value.
        
        Args:
            key_str: KeyCode name (e.g., "DOWN", "ENTER", "A")
        
        Returns:
            KeyCode integer value, or None if not found
        """
        try:
            # KeyCode is a StrEnum, so we can access by name
            keycode = getattr(KeyCode, key_str, None)
            if keycode is None:
                self.logger.warning(f"Unknown KeyCode name: {key_str}")
            return keycode
        except AttributeError:
            self.logger.warning(f"Invalid KeyCode name: {key_str}")
            return None
    
    def _build_key_lookup(self) -> dict:
        """
        Build a reverse lookup table from key expressions to actions.
        
        Returns:
            Dictionary mapping (main_key, modifier_flags) to list of (action, selection_req) tuples
        """
        lookup = {}
        
        for action, binding in self._bindings.items():
            # Extract keys and selection requirement
            if isinstance(binding, list):
                keys = binding
                selection_req = 'any'
            elif isinstance(binding, dict) and 'keys' in binding:
                keys = binding['keys']
                selection_req = binding.get('selection', 'any')
            else:
                continue
            
            # Process each key expression
            for key_expr in keys:
                # Parse key expression to get main key and modifiers
                main_key, modifiers = self._parse_key_expression(key_expr)
                
                # Add to lookup table
                lookup_key = (main_key, modifiers)
                if lookup_key not in lookup:
                    lookup[lookup_key] = []
                lookup[lookup_key].append((action, selection_req))
        
        return lookup
    
    def _match_key_event(self, event, main_key: str, modifiers: int) -> bool:
        """
        Check if a KeyEvent matches a key expression.
        
        Args:
            event: KeyEvent from TTK
            main_key: Main key string (uppercase)
            modifiers: Expected modifier flags
        
        Returns:
            True if event matches the key expression
        """
        # Single character - match against event.char (ignore modifiers for backward compatibility)
        # This allows "?" to match even though it's technically Shift-Slash
        if len(main_key) == 1:
            return event.char and event.char.upper() == main_key
        
        # Multi-character keys (KeyCode names) - check modifiers AND key_code
        if event.modifiers != modifiers:
            return False
        
        # KeyCode name - match against event.key_code
        expected_keycode = self._keycode_from_string(main_key)
        if expected_keycode is None:
            return False
        
        return event.key_code == expected_keycode
    
    def _check_selection_requirement(self, requirement: str, has_selection: bool) -> bool:
        """
        Check if selection requirement is satisfied.
        
        Args:
            requirement: 'required', 'none', or 'any'
            has_selection: Whether files are currently selected
        
        Returns:
            True if requirement is satisfied
        """
        if requirement == 'required':
            return has_selection
        elif requirement == 'none':
            return not has_selection
        else:  # 'any'
            return True
    
    def find_action_for_event(self, event, has_selection: bool):
        """
        Find the action bound to a KeyEvent, respecting selection requirements.
        
        Args:
            event: KeyEvent from TTK
            has_selection: Whether files are currently selected
        
        Returns:
            Action name if found, None otherwise
        """
        if not event:
            return None
        
        # Try to match against all key bindings
        for (main_key, modifiers), actions in self._key_to_actions.items():
            if self._match_key_event(event, main_key, modifiers):
                # Found a matching key - check selection requirements
                for action, selection_req in actions:
                    if self._check_selection_requirement(selection_req, has_selection):
                        return action
        
        return None
    
    def get_keys_for_action(self, action: str) -> tuple:
        """
        Get the key expressions and selection requirement for an action.
        
        Args:
            action: Action name
        
        Returns:
            Tuple of (key_expressions, selection_requirement)
            - key_expressions: List of key expression strings
            - selection_requirement: 'required', 'none', or 'any'
        """
        if action not in self._bindings:
            return ([], 'any')
        
        binding = self._bindings[action]
        
        # Extract keys and selection requirement
        if isinstance(binding, list):
            return (binding, 'any')
        elif isinstance(binding, dict) and 'keys' in binding:
            keys = binding['keys']
            selection_req = binding.get('selection', 'any')
            return (keys, selection_req)
        
        return ([], 'any')
    
    def format_key_for_display(self, key_expr: str) -> str:
        """
        Format a key expression for display in UI.
        
        Args:
            key_expr: Key expression string
        
        Returns:
            Formatted string suitable for display
        
        Examples:
            "q" -> "q"
            "Shift-Down" -> "Shift-Down"
            "Command-Shift-X" -> "Cmd-Shift-X"
        """
        # Single character - return as-is
        if len(key_expr) == 1:
            return key_expr
        
        # Multi-character - format nicely
        parts = key_expr.split('-')
        
        # Format modifiers
        formatted_parts = []
        for part in parts[:-1]:
            modifier = part.capitalize()
            # Abbreviate Command to Cmd
            if modifier == 'Command':
                modifier = 'Cmd'
            formatted_parts.append(modifier)
        
        # Add main key
        formatted_parts.append(parts[-1].upper())
        
        return '-'.join(formatted_parts)


class DefaultConfig:
    """Default configuration values for TFM"""
    
    # Backend settings
    PREFERRED_BACKEND = 'curses'  # 'curses' or 'coregraphics'
    
    # Desktop mode settings (for CoreGraphics backend)
    DESKTOP_FONT_NAME = ['Menlo', 'Monaco', 'Courier', 'Osaka-Mono', 'Hiragino Sans GB']  # Font names for desktop mode (first is primary, rest are cascade fallbacks)
    DESKTOP_FONT_SIZE = 12  # Font size for desktop mode (8-72 points)
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
        'delete_files': {'keys': ['k', 'K', 'DELETE', 'Command-Backspace'], 'selection': 'required'}, # Delete selected files/directories
        'rename_file': ['r', 'R'],            # Rename selected file/directory
        'favorites': ['j'],                   # Show favorite directories dialog
        'jump_to_path': ['J'],                # Jump to path (Shift+J)
        'history': ['h', 'H'],                # Show history for current pane
        'subshell': ['X'],                     # Enter subshell (command line) mode
        'programs': ['x'],                     # Show external programs menu
        'create_archive': {'keys': ['p', 'P'], 'selection': 'required'}, # Create archive from selected files
        'extract_archive': ['u', 'U'],        # Extract selected archive file
        'compare_selection': ['w', 'W'],      # Show file and directory comparison options
        'adjust_pane_left': ['['],            # Make left pane smaller (move boundary left)
        'adjust_pane_right': [']'],           # Make left pane larger (move boundary right)
        'reset_pane_boundary': ['-'],         # Reset pane split to 50% | 50%
        'adjust_log_up': ['{'],               # Make log pane larger (Shift+[)
        'adjust_log_down': ['}'],             # Make log pane smaller (Shift+])
        'reset_log_height': ['_'],            # Reset log pane height to default (Shift+-)
        # Navigation with modifier keys
        'move_up': ['UP', 'k'],               # Move cursor up one item
        'move_down': ['DOWN', 'j'],           # Move cursor down one item
        'move_left': ['LEFT', 'h'],           # Move to parent directory
        'move_right': ['RIGHT', 'l'],         # Enter directory or view file
        'page_up': ['PAGE_UP', 'Shift-UP'],   # Move up one page
        'page_down': ['PAGE_DOWN', 'Shift-DOWN'],  # Move down one page
        'jump_to_top': ['Command-UP'],        # Jump to first item in list
        'jump_to_bottom': ['Command-DOWN'],   # Jump to last item in list
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
        self.logger = getLogger("Config")
        self.config_dir = Path.home() / '.tfm'
        self.config_file = self.config_dir / 'config.py'
        self.config = None
        self._key_bindings = None
        
    def ensure_config_dir(self):
        """Ensure the configuration directory exists"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.warning(f"Could not create config directory {self.config_dir}: {e}")
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
                self.logger.warning(f"Template file not found at {template_file}")
                return False
            
            # Read the template file
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Write to user config file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            self.logger.info(f"Created default configuration at: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating default config: {e}")
            return False
    
    def load_config(self):
        """Load configuration from file or create default if not exists"""
        # Check if config file exists
        if not self.config_file.exists():
            self.logger.info(f"Configuration file not found at: {self.config_file}")
            if self.create_default_config():
                self.logger.info("Created default configuration file")
            else:
                self.logger.info("Using built-in default configuration")
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
                self.logger.info(f"Loaded configuration from: {self.config_file}")
            else:
                raise AttributeError("Config class not found in configuration file")
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.logger.info("Using built-in default configuration")
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
        self._key_bindings = None
        return self.load_config()
    
    def get_key_bindings(self) -> KeyBindings:
        """Get the KeyBindings instance for current configuration."""
        config = self.get_config()
        
        # Rebuild if config changed or not yet built
        if self._key_bindings is None:
            # Get key bindings config with fallback to defaults
            if hasattr(config, 'KEY_BINDINGS') and config.KEY_BINDINGS:
                key_bindings_config = config.KEY_BINDINGS
            else:
                self.logger.info("Using default key bindings")
                key_bindings_config = DefaultConfig.KEY_BINDINGS
            
            self._key_bindings = KeyBindings(key_bindings_config)
        
        return self._key_bindings
    
    def validate_config(self, config):
        """Validate configuration values"""
        errors = []
        
        # Validate backend selection
        if hasattr(config, 'PREFERRED_BACKEND'):
            if config.PREFERRED_BACKEND not in ['curses', 'coregraphics']:
                errors.append("PREFERRED_BACKEND must be 'curses' or 'coregraphics'")
        
        # Validate desktop mode settings
        if hasattr(config, 'DESKTOP_FONT_NAME'):
            # Accept both string (single font) and list (with fallbacks)
            if isinstance(config.DESKTOP_FONT_NAME, str):
                if not config.DESKTOP_FONT_NAME.strip():
                    errors.append("DESKTOP_FONT_NAME must be a non-empty string")
            elif isinstance(config.DESKTOP_FONT_NAME, list):
                if not config.DESKTOP_FONT_NAME:
                    errors.append("DESKTOP_FONT_NAME list must not be empty")
                elif not all(isinstance(name, str) and name.strip() for name in config.DESKTOP_FONT_NAME):
                    errors.append("DESKTOP_FONT_NAME list must contain only non-empty strings")
            else:
                errors.append("DESKTOP_FONT_NAME must be a string or list of strings")
        
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
            if isinstance(key, str):
                # Try to get KeyCode value from string
                try:
                    keycode_value = getattr(KeyCode, key, None)
                    if keycode_value == key_code:
                        return True
                except AttributeError:
                    pass
        
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
                        if isinstance(bound_key, str):
                            # Try to get KeyCode value from string
                            try:
                                keycode_value = getattr(KeyCode, bound_key, None)
                                if keycode_value == key:
                                    return action
                            except AttributeError:
                                pass
        
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
    """
    DEPRECATED: Use find_action_for_event() instead.
    
    Check if a key is bound to a specific action.
    
    This function is deprecated and maintained only for backward compatibility.
    New code should use find_action_for_event() which supports modifier keys
    and provides more flexible key binding matching.
    
    Args:
        key_char: Character key to check
        action: Action name
    
    Returns:
        bool: True if key is bound to action
    """
    import warnings
    warnings.warn(
        "is_key_bound_to() is deprecated. Use find_action_for_event() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return config_manager.is_key_bound_to_action(key_char, action)


def is_key_bound_to_with_selection(key_char, action, has_selection):
    """
    DEPRECATED: Use find_action_for_event() instead.
    
    Check if a key is bound to a specific action and available for current selection status.
    
    This function is deprecated and maintained only for backward compatibility.
    New code should use find_action_for_event() which supports modifier keys
    and provides more flexible key binding matching.
    
    Args:
        key_char: Character key to check
        action: Action name
        has_selection: Whether files are currently selected
    
    Returns:
        bool: True if key is bound to action and selection requirement is met
    """
    import warnings
    warnings.warn(
        "is_key_bound_to_with_selection() is deprecated. Use find_action_for_event() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return config_manager.is_key_bound_to_action_with_selection(key_char, action, has_selection)


def is_action_available(action, has_selection):
    """Check if action is available based on current selection status"""
    return config_manager.is_action_available(action, has_selection)


def is_special_key_bound_to(key_code, action):
    """
    DEPRECATED: Use find_action_for_event() instead.
    
    Check if a special key code is bound to a specific action.
    
    This function is deprecated and maintained only for backward compatibility.
    New code should use find_action_for_event() which supports modifier keys
    and provides more flexible key binding matching.
    
    Args:
        key_code: KeyCode value to check
        action: Action name
    
    Returns:
        bool: True if key code is bound to action
    """
    import warnings
    warnings.warn(
        "is_special_key_bound_to() is deprecated. Use find_action_for_event() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return config_manager.is_special_key_bound_to_action(key_code, action)


def is_special_key_bound_to_with_selection(key_code, action, has_selection):
    """
    DEPRECATED: Use find_action_for_event() instead.
    
    Check if a special key is bound to a specific action and available for current selection status.
    
    This function is deprecated and maintained only for backward compatibility.
    New code should use find_action_for_event() which supports modifier keys
    and provides more flexible key binding matching.
    
    Args:
        key_code: KeyCode value to check
        action: Action name
        has_selection: Whether files are currently selected
    
    Returns:
        bool: True if key code is bound to action and selection requirement is met
    """
    import warnings
    warnings.warn(
        "is_special_key_bound_to_with_selection() is deprecated. Use find_action_for_event() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return config_manager.is_special_key_bound_to_action_with_selection(key_code, action, has_selection)


def is_input_event_bound_to(event, action):
    """
    DEPRECATED: Use find_action_for_event() instead.
    
    Check if a KeyEvent is bound to a specific action.
    
    This function is deprecated and maintained only for backward compatibility.
    New code should use find_action_for_event() which supports modifier keys
    and provides more flexible key binding matching.
    
    Args:
        event: KeyEvent from TTK renderer
        action: Action name to check
        
    Returns:
        bool: True if event is bound to the action
    """
    import warnings
    warnings.warn(
        "is_input_event_bound_to() is deprecated. Use find_action_for_event() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return config_manager.is_input_event_bound_to_action(event, action)


def is_input_event_bound_to_with_selection(event, action, has_selection):
    """
    DEPRECATED: Use find_action_for_event() instead.
    
    Check if a KeyEvent is bound to a specific action and respects selection requirements.
    
    This function is deprecated and maintained only for backward compatibility.
    New code should use find_action_for_event() which supports modifier keys
    and provides more flexible key binding matching.
    
    Args:
        event: KeyEvent from TTK renderer
        action: Action name to check
        has_selection: Whether files are currently selected
        
    Returns:
        bool: True if event is bound to the action and selection requirement is met
    """
    import warnings
    warnings.warn(
        "is_input_event_bound_to_with_selection() is deprecated. Use find_action_for_event() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return config_manager.is_input_event_bound_to_action_with_selection(event, action, has_selection)


def get_action_for_key(key):
    """
    DEPRECATED: Use find_action_for_event() instead.
    
    Get the action bound to a key (character or special key code).
    
    This function is deprecated and maintained only for backward compatibility.
    New code should use find_action_for_event() which supports modifier keys
    and provides more flexible key binding matching.
    
    Args:
        key: Either a character string or a curses key code (int)
    
    Returns:
        Action name if found, None otherwise
    """
    import warnings
    warnings.warn(
        "get_action_for_key() is deprecated. Use find_action_for_event() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return config_manager.get_action_for_key(key)


def find_action_for_event(event, has_selection: bool = False):
    """
    Find the action bound to a KeyEvent.
    
    Args:
        event: KeyEvent from TTK
        has_selection: Whether files are currently selected
    
    Returns:
        Action name if found, None otherwise
    """
    key_bindings = config_manager.get_key_bindings()
    return key_bindings.find_action_for_event(event, has_selection)


def get_keys_for_action(action: str) -> tuple:
    """
    Get the key expressions and selection requirement for an action.
    
    Args:
        action: Action name
    
    Returns:
        Tuple of (key_expressions, selection_requirement)
    """
    key_bindings = config_manager.get_key_bindings()
    return key_bindings.get_keys_for_action(action)


def format_key_for_display(key_expr: str) -> str:
    """
    Format a key expression for display in UI.
    
    Args:
        key_expr: Key expression string
    
    Returns:
        Formatted string suitable for display
    """
    key_bindings = config_manager.get_key_bindings()
    return key_bindings.format_key_for_display(key_expr)



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
                        logger.warning(f"Favorite directory does not exist: {fav['name']} -> {fav['path']}")
                except Exception as e:
                    logger.warning(f"Invalid favorite directory path: {fav['name']} -> {fav['path']}: {e}")
    
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
                    logger.warning(f"Program command must be a non-empty list: {prog['name']}")
            else:
                logger.warning(f"Invalid program configuration: {prog}")
    
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