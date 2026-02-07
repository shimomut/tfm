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
            key_expr: Key expression string (e.g., "Shift-Down", "Command-Shift-X", "q", "?")
        
        Returns:
            Tuple of (main_key, modifier_flags)
            - main_key: The main key as string
              * Non-alphabet single chars: preserved as-is (e.g., "?" stays "?")
              * Alphabet single chars: normalized to uppercase (e.g., "q" -> "Q", "A" -> "A")
              * Multi-char keys: normalized to uppercase (e.g., "Down" -> "DOWN")
            - modifier_flags: Bitwise OR of ModifierKey values
              * Single chars (both alphabet and non-alphabet): always 0
              * Multi-char expressions: parsed from prefix (e.g., "Shift-Down" -> SHIFT)
        
        Key Behavior:
            - Non-alphabet single characters (?, /, ., etc.): Case-sensitive, match on char, ignore modifiers
            - Alphabet single characters (a-z, A-Z): Case-insensitive (normalized to uppercase), 
              match on KeyCode, RESPECT modifiers (modifiers=0 means no modifiers)
            - Multi-character keys (KeyCode names): Match on KeyCode with modifiers
        
        Important:
            To bind uppercase letters separately, users must use "Shift-A" instead of just "A".
            Just "A" or "a" in config will match KeyCode.A with NO modifiers (lowercase 'a' press).
        
        Examples:
            "q" -> ("Q", 0)  # Matches lowercase 'q' press (no Shift)
            "A" -> ("A", 0)  # Matches lowercase 'a' press (no Shift) - same as "q"
            "Shift-A" -> ("A", SHIFT)  # Matches uppercase 'A' press (with Shift)
            "?" -> ("?", 0)  # Matches '?' character regardless of modifiers
            "/" -> ("/", 0)  # Matches '/' character regardless of modifiers
            "Shift-Down" -> ("DOWN", ModifierKey.SHIFT)
            "Command-Shift-X" -> ("X", ModifierKey.COMMAND | ModifierKey.SHIFT)
        """
        # Import ModifierKey here to avoid circular dependency
        from ttk import ModifierKey
        
        # Single non-alphabet character - preserve case for case-sensitive matching
        if len(key_expr) == 1 and not key_expr.isalpha():
            return (key_expr, 0)
        
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
        
        This method implements the key matching logic that distinguishes between:
        1. Non-alphabet single characters: Match on event.char (case-sensitive, ignore modifiers)
        2. Alphabet characters: Match on event.key_code (case-insensitive, RESPECT modifiers)
        3. Multi-character keys: Match on event.key_code (respect modifiers)
        
        Args:
            event: KeyEvent from TTK
            main_key: Main key string from _parse_key_expression()
              * Non-alphabet single chars: original case (e.g., "?", "/")
              * Alphabet chars: uppercase (e.g., "Q", "A")
              * Multi-char keys: uppercase KeyCode name (e.g., "DOWN", "ENTER")
            modifiers: Expected modifier flags (0 for non-alphabet single chars, may be non-zero for alphabet)
        
        Returns:
            True if event matches the key expression
        
        Examples:
            - "?" matches KeyEvent(char="?") regardless of modifiers
            - "q" matches KeyEvent(key_code=KeyCode.Q, modifiers=0) but NOT with Shift
            - "Shift-A" matches KeyEvent(key_code=KeyCode.A, modifiers=SHIFT)
        
        Note:
            To bind uppercase letters separately from lowercase, users must use "Shift-A" 
            instead of just "A" in the configuration.
        """
        # Single non-alphabet character - match on char field (case-sensitive, ignore modifiers)
        if len(main_key) == 1 and not main_key.isalpha():
            return event.char and event.char == main_key
        
        # Alphabet or multi-character keys - check modifiers first
        if event.modifiers != modifiers:
            return False
        
        # Match against KeyCode (case-insensitive for alphabet, exact for multi-char)
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


def _load_template_config():
    """
    Load the Config class from _config.py template.
    
    Returns:
        Config class from _config.py, or None if loading fails
    """
    try:
        # Get the directory where this module is located
        current_dir = Path(__file__).parent
        template_file = current_dir / '_config.py'
        
        # Check if template file exists
        if not template_file.exists():
            logger.warning(f"Template file not found at {template_file}")
            return None
        
        # Load the template module
        spec = importlib.util.spec_from_file_location("_config_template", template_file)
        if spec is None or spec.loader is None:
            logger.warning("Could not create spec for template config")
            return None
        
        template_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(template_module)
        
        # Get the Config class
        if hasattr(template_module, 'Config'):
            return template_module.Config
        else:
            logger.warning("Config class not found in template file")
            return None
    
    except Exception as e:
        logger.error(f"Error loading template config: {e}")
        return None


def _copy_missing_fields(user_config, template_config_class):
    """
    Copy missing fields from template Config class to user config instance.
    
    Args:
        user_config: User's config instance (may be incomplete or empty)
        template_config_class: Template Config class from _config.py
    """
    if template_config_class is None:
        return
    
    # Get all class attributes from template (excluding private/magic attributes)
    template_attrs = {
        name: value 
        for name, value in vars(template_config_class).items()
        if not name.startswith('_')
    }
    
    # Copy missing attributes to user config
    copied_count = 0
    for name, value in template_attrs.items():
        if not hasattr(user_config, name):
            setattr(user_config, name, value)
            copied_count += 1
            logger.info(f"Added missing config field: {name}")
    
    if copied_count > 0:
        logger.info(f"Copied {copied_count} missing fields from template config")


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
        # Load template config class for filling in missing fields
        template_config_class = _load_template_config()
        
        # Check if config file exists
        if not self.config_file.exists():
            self.logger.info(f"Configuration file not found at: {self.config_file}")
            if self.create_default_config():
                self.logger.info("Created default configuration file")
            else:
                self.logger.warning("Could not create default configuration file")
                # Create empty config and fill from template
                class EmptyConfig:
                    pass
                self.config = EmptyConfig()
                _copy_missing_fields(self.config, template_config_class)
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
            self.logger.info("Creating empty config and filling from template")
            # Create empty config and fill from template
            class EmptyConfig:
                pass
            self.config = EmptyConfig()
        
        # Copy any missing fields from template
        _copy_missing_fields(self.config, template_config_class)
        
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
            # Get key bindings config - should always exist after load_config
            if hasattr(config, 'KEY_BINDINGS') and config.KEY_BINDINGS:
                key_bindings_config = config.KEY_BINDINGS
            else:
                # This shouldn't happen after _copy_missing_fields, but handle it
                self.logger.warning("KEY_BINDINGS not found in config, using empty bindings")
                key_bindings_config = {}
            
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
        
        return errors
    
    def get_key_for_action(self, action):
        """Get the key binding for a specific action"""
        config = self.get_config()
        
        if hasattr(config, 'KEY_BINDINGS') and action in config.KEY_BINDINGS:
            binding = config.KEY_BINDINGS[action]
        else:
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
        
        if hasattr(config, 'KEY_BINDINGS') and action in config.KEY_BINDINGS:
            binding = config.KEY_BINDINGS[action]
        else:
            return 'any'
        
        # Handle extended format
        if isinstance(binding, dict) and 'selection' in binding:
            return binding['selection']
        
        # Simple format defaults to 'any'
        return 'any'
    



# Global configuration manager instance
config_manager = ConfigManager()


def get_config():
    """Get the current configuration"""
    return config_manager.get_config()


def reload_config():
    """Reload configuration from file"""
    return config_manager.reload_config()


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
    
    # Get favorites from config (should always exist after _copy_missing_fields)
    if hasattr(config, 'FAVORITE_DIRECTORIES') and config.FAVORITE_DIRECTORIES:
        favorites_config = config.FAVORITE_DIRECTORIES
    else:
        # This shouldn't happen, but handle gracefully
        logger.warning("FAVORITE_DIRECTORIES not found in config")
        return []
    
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
    
    # Get associations from config (should always exist after _copy_missing_fields)
    if hasattr(config, 'FILE_ASSOCIATIONS') and config.FILE_ASSOCIATIONS:
        return config.FILE_ASSOCIATIONS
    
    # This shouldn't happen, but handle gracefully
    logger.warning("FILE_ASSOCIATIONS not found in config")
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