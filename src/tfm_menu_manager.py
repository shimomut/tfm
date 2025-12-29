"""
Menu Manager for TFM Desktop Mode

This module manages menu structure and state for TFM when running in Desktop mode.
It defines the menu hierarchy, menu item IDs, and logic for enabling/disabling
menu items based on application state.
"""

import platform


class MenuManager:
    """Manages menu structure and state for TFM Desktop mode."""
    
    # Menu item ID constants
    # App menu (macOS)
    APP_ABOUT = 'app.about'
    APP_QUIT = 'app.quit'
    
    # File menu
    FILE_NEW_FILE = 'file.new_file'
    FILE_NEW_FOLDER = 'file.new_folder'
    FILE_OPEN = 'file.open'
    FILE_COPY_TO_OTHER_PANE = 'file.copy_to_other_pane'
    FILE_MOVE_TO_OTHER_PANE = 'file.move_to_other_pane'
    FILE_DELETE = 'file.delete'
    FILE_RENAME = 'file.rename'
    
    # Edit menu
    EDIT_SELECT_ALL = 'edit.select_all'
    EDIT_COPY_NAMES = 'edit.copy_names'
    EDIT_COPY_PATHS = 'edit.copy_paths'
    
    # View menu
    VIEW_SHOW_HIDDEN = 'view.show_hidden'
    VIEW_SORT_BY_NAME = 'view.sort_by_name'
    VIEW_SORT_BY_SIZE = 'view.sort_by_size'
    VIEW_SORT_BY_DATE = 'view.sort_by_date'
    VIEW_SORT_BY_EXTENSION = 'view.sort_by_extension'
    VIEW_REFRESH = 'view.refresh'
    VIEW_MOVE_PANE_DIVIDER_LEFT = 'view.move_pane_divider_left'
    VIEW_MOVE_PANE_DIVIDER_RIGHT = 'view.move_pane_divider_right'
    VIEW_MOVE_LOG_DIVIDER_UP = 'view.move_log_divider_up'
    VIEW_MOVE_LOG_DIVIDER_DOWN = 'view.move_log_divider_down'
    
    # Go menu
    GO_PARENT = 'go.parent'
    GO_HOME = 'go.home'
    GO_FAVORITES = 'go.favorites'
    GO_RECENT = 'go.recent'
    
    # Help menu
    HELP_ABOUT = 'help.about'
    HELP_REPORT_ISSUE = 'help.report_issue'
    
    def __init__(self, file_manager):
        """Initialize MenuManager with reference to FileManager.
        
        Args:
            file_manager: Reference to the main FileManager instance
        """
        self.file_manager = file_manager
        self.menu_structure = self._build_menu_structure()
    
    def _get_shortcut_modifier(self):
        """Get the platform-appropriate modifier key for shortcuts.
        
        Returns:
            str: 'Cmd' for macOS, 'Ctrl' for other platforms
        """
        return 'Cmd' if platform.system() == 'Darwin' else 'Ctrl'
    
    def _build_menu_structure(self):
        """Build the complete menu structure.
        
        Returns:
            dict: Menu structure with menus and items
        """
        modifier = self._get_shortcut_modifier()
        
        menus = []
        
        # On macOS, add application menu as first menu
        # This will show "TFM" instead of "python"
        if platform.system() == 'Darwin':
            menus.append(self._build_app_menu(modifier))
        
        # Add standard menus
        menus.extend([
            self._build_file_menu(modifier),
            self._build_edit_menu(modifier),
            self._build_view_menu(modifier),
            self._build_go_menu(modifier),
            self._build_help_menu(modifier)
        ])
        
        return {
            'menus': menus
        }
    
    def _build_app_menu(self, modifier):
        """Build the Application menu structure (macOS only).
        
        Args:
            modifier: Keyboard modifier key (Cmd or Ctrl)
        
        Returns:
            dict: Application menu structure
        """
        return {
            'id': 'app',
            'label': 'TFM',  # This will show as the app name in the menu bar
            'items': [
                {
                    'id': self.APP_ABOUT,
                    'label': 'About TFM',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': self.APP_QUIT,
                    'label': 'Quit TFM',
                    'shortcut': f'{modifier}+Q',
                    'enabled': True
                }
            ]
        }
    
    def _build_file_menu(self, modifier):
        """Build the File menu structure.
        
        Args:
            modifier: Keyboard modifier key (Cmd or Ctrl)
        
        Returns:
            dict: File menu structure
        """
        return {
            'id': 'file',
            'label': 'File',
            'items': [
                {
                    'id': self.FILE_NEW_FILE,
                    'label': 'New File',
                    'shortcut': f'{modifier}+N',
                    'enabled': True
                },
                {
                    'id': self.FILE_NEW_FOLDER,
                    'label': 'New Folder',
                    'shortcut': f'{modifier}+Shift+N',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': self.FILE_OPEN,
                    'label': 'Open',
                    'shortcut': f'{modifier}+O',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': self.FILE_COPY_TO_OTHER_PANE,
                    'label': 'Copy to Other Pane',
                    'shortcut': 'F5',
                    'enabled': False  # Disabled when no selection
                },
                {
                    'id': self.FILE_MOVE_TO_OTHER_PANE,
                    'label': 'Move to Other Pane',
                    'shortcut': 'F6',
                    'enabled': False  # Disabled when no selection
                },
                {'separator': True},
                {
                    'id': self.FILE_DELETE,
                    'label': 'Delete',
                    'shortcut': 'F8',
                    'enabled': False  # Disabled when no selection
                },
                {
                    'id': self.FILE_RENAME,
                    'label': 'Rename',
                    'shortcut': f'{modifier}+R',
                    'enabled': False  # Disabled when no selection
                }
            ]
        }
    
    def _build_edit_menu(self, modifier):
        """Build the Edit menu structure.
        
        Args:
            modifier: Keyboard modifier key (Cmd or Ctrl)
        
        Returns:
            dict: Edit menu structure
        """
        return {
            'id': 'edit',
            'label': 'Edit',
            'items': [
                {
                    'id': self.EDIT_SELECT_ALL,
                    'label': 'Select All',
                    'shortcut': f'{modifier}+A',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': self.EDIT_COPY_NAMES,
                    'label': 'Copy Names to Clipboard',
                    'shortcut': f'{modifier}+C',
                    'enabled': True  # Always enabled - uses focused item if no selection
                },
                {
                    'id': self.EDIT_COPY_PATHS,
                    'label': 'Copy Full Paths to Clipboard',
                    'shortcut': f'{modifier}+Shift+C',
                    'enabled': True  # Always enabled - uses focused item if no selection
                }
            ]
        }
    
    def _build_view_menu(self, modifier):
        """Build the View menu structure.
        
        Args:
            modifier: Keyboard modifier key (Cmd or Ctrl)
        
        Returns:
            dict: View menu structure
        """
        return {
            'id': 'view',
            'label': 'View',
            'items': [
                {
                    'id': self.VIEW_SHOW_HIDDEN,
                    'label': 'Show Hidden Files',
                    'shortcut': f'{modifier}+H',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': self.VIEW_SORT_BY_NAME,
                    'label': 'Sort by Name',
                    'enabled': True
                },
                {
                    'id': self.VIEW_SORT_BY_SIZE,
                    'label': 'Sort by Size',
                    'enabled': True
                },
                {
                    'id': self.VIEW_SORT_BY_DATE,
                    'label': 'Sort by Date',
                    'enabled': True
                },
                {
                    'id': self.VIEW_SORT_BY_EXTENSION,
                    'label': 'Sort by Extension',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': self.VIEW_REFRESH,
                    'label': 'Refresh',
                    'shortcut': f'{modifier}+R',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': self.VIEW_MOVE_PANE_DIVIDER_LEFT,
                    'label': 'Move Pane Divider Left',
                    'shortcut': f'{modifier}+Left',
                    'enabled': True
                },
                {
                    'id': self.VIEW_MOVE_PANE_DIVIDER_RIGHT,
                    'label': 'Move Pane Divider Right',
                    'shortcut': f'{modifier}+Right',
                    'enabled': True
                },
                {
                    'id': self.VIEW_MOVE_LOG_DIVIDER_UP,
                    'label': 'Move Log Divider Up',
                    'shortcut': f'{modifier}+Up',
                    'enabled': True
                },
                {
                    'id': self.VIEW_MOVE_LOG_DIVIDER_DOWN,
                    'label': 'Move Log Divider Down',
                    'shortcut': f'{modifier}+Down',
                    'enabled': True
                }
            ]
        }
    
    def _build_go_menu(self, modifier):
        """Build the Go menu structure.
        
        Args:
            modifier: Keyboard modifier key (Cmd or Ctrl)
        
        Returns:
            dict: Go menu structure
        """
        return {
            'id': 'go',
            'label': 'Go',
            'items': [
                {
                    'id': self.GO_PARENT,
                    'label': 'Parent Directory',
                    'shortcut': f'{modifier}+Up',
                    'enabled': True  # Disabled at root
                },
                {
                    'id': self.GO_HOME,
                    'label': 'Home',
                    'shortcut': f'{modifier}+Shift+H',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': self.GO_FAVORITES,
                    'label': 'Favorites',
                    'shortcut': f'{modifier}+F',
                    'enabled': True
                },
                {
                    'id': self.GO_RECENT,
                    'label': 'Recent Locations',
                    'shortcut': f'{modifier}+Shift+R',
                    'enabled': True
                }
            ]
        }
    
    def _build_help_menu(self, modifier):
        """Build the Help menu structure.
        
        Args:
            modifier: Keyboard modifier key (Cmd or Ctrl)
        
        Returns:
            dict: Help menu structure
        """
        return {
            'id': 'help',
            'label': 'Help',
            'items': [
                {
                    'id': self.HELP_ABOUT,
                    'label': 'About TFM',
                    'enabled': True
                },
                {'separator': True},
                {
                    'id': self.HELP_REPORT_ISSUE,
                    'label': 'Report Issue',
                    'enabled': True
                }
            ]
        }
    
    def get_menu_structure(self):
        """Get current menu structure.
        
        Returns:
            dict: Complete menu structure
        """
        return self.menu_structure
    
    def update_menu_states(self):
        """Calculate current enable/disable state for all menu items.
        
        Returns:
            dict: Map of menu item IDs to enabled state
        """
        states = {}
        
        # Get current pane and selection info
        try:
            current_pane = self.file_manager.get_current_pane()
            has_selection = len(current_pane['selected_files']) > 0
            current_dir = current_pane['path']
            is_at_root = self._is_at_root(current_dir)
        except Exception as e:
            # If we can't get pane info, disable selection-dependent items
            has_selection = False
            is_at_root = True
        
        # App menu states
        states[self.APP_ABOUT] = True
        states[self.APP_QUIT] = True
        
        # File menu states
        states[self.FILE_NEW_FILE] = True
        states[self.FILE_NEW_FOLDER] = True
        states[self.FILE_OPEN] = True
        states[self.FILE_COPY_TO_OTHER_PANE] = has_selection
        states[self.FILE_MOVE_TO_OTHER_PANE] = has_selection
        states[self.FILE_DELETE] = has_selection
        states[self.FILE_RENAME] = has_selection
        
        # Edit menu states
        states[self.EDIT_SELECT_ALL] = True
        states[self.EDIT_COPY_NAMES] = True  # Always enabled - uses focused item if no selection
        states[self.EDIT_COPY_PATHS] = True  # Always enabled - uses focused item if no selection
        
        # View menu states (all always enabled)
        states[self.VIEW_SHOW_HIDDEN] = True
        states[self.VIEW_SORT_BY_NAME] = True
        states[self.VIEW_SORT_BY_SIZE] = True
        states[self.VIEW_SORT_BY_DATE] = True
        states[self.VIEW_SORT_BY_EXTENSION] = True
        states[self.VIEW_REFRESH] = True
        states[self.VIEW_MOVE_PANE_DIVIDER_LEFT] = True
        states[self.VIEW_MOVE_PANE_DIVIDER_RIGHT] = True
        states[self.VIEW_MOVE_LOG_DIVIDER_UP] = True
        states[self.VIEW_MOVE_LOG_DIVIDER_DOWN] = True
        
        # Go menu states
        states[self.GO_PARENT] = not is_at_root
        states[self.GO_HOME] = True
        states[self.GO_FAVORITES] = True
        states[self.GO_RECENT] = True
        
        # Help menu states (all always enabled)
        states[self.HELP_ABOUT] = True
        states[self.HELP_REPORT_ISSUE] = True
        
        return states
    
    def should_enable_item(self, item_id):
        """Determine if a menu item should be enabled.
        
        Args:
            item_id: Menu item identifier
        
        Returns:
            bool: True if item should be enabled
        """
        states = self.update_menu_states()
        return states.get(item_id, False)
    
    def _is_at_root(self, current_dir):
        """Check if current directory is at root.
        
        Args:
            current_dir: Current directory path
        
        Returns:
            bool: True if at root directory
        """
        try:
            # Check if parent is same as current (indicates root)
            parent = current_dir.parent
            return parent == current_dir
        except Exception:
            return True
