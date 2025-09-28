#!/usr/bin/env python3
"""
TFM Pane Manager - Handles dual pane management and navigation
"""

from tfm_path import Path
from collections import deque


class PaneManager:
    """Manages dual pane functionality and navigation"""
    
    def __init__(self, config, left_startup_path, right_startup_path, state_manager=None):
        # Store reference to state manager for persistent history
        self.state_manager = state_manager
        self.config = config
        
        # Dual pane setup with configuration
        self.left_pane = {
            'path': left_startup_path,
            'selected_index': 0,
            'scroll_offset': 0,
            'files': [],
            'selected_files': set(),  # Track multi-selected files
            'sort_mode': getattr(config, 'DEFAULT_SORT_MODE', 'name'),
            'sort_reverse': getattr(config, 'DEFAULT_SORT_REVERSE', False),
            'filter_pattern': "",  # Filename filter pattern for this pane
        }
        self.right_pane = {
            'path': right_startup_path,
            'selected_index': 0,
            'scroll_offset': 0,
            'files': [],
            'selected_files': set(),  # Track multi-selected files
            'sort_mode': getattr(config, 'DEFAULT_SORT_MODE', 'name'),
            'sort_reverse': getattr(config, 'DEFAULT_SORT_REVERSE', False),
            'filter_pattern': "",  # Filename filter pattern for this pane
        }
        
        self.active_pane = 'left'  # 'left' or 'right'
        
        # Pane layout - track left pane width ratio (0.1 to 0.9)
        self.left_pane_ratio = getattr(config, 'DEFAULT_LEFT_PANE_RATIO', 0.5)
    
    def get_current_pane(self):
        """Get the currently active pane"""
        return self.left_pane if self.active_pane == 'left' else self.right_pane
    
    def get_inactive_pane(self):
        """Get the inactive pane"""
        return self.right_pane if self.active_pane == 'left' else self.left_pane
    
    def switch_pane(self):
        """Switch between left and right panes"""
        self.active_pane = 'right' if self.active_pane == 'left' else 'left'
    
    def save_cursor_position(self, pane_data):
        """Save current cursor position to persistent history"""
        if not pane_data['files'] or pane_data['selected_index'] >= len(pane_data['files']):
            return
            
        current_file = pane_data['files'][pane_data['selected_index']]
        current_dir = str(pane_data['path'])
        
        # If no state manager available, skip saving
        if not self.state_manager:
            return
        
        # Determine which pane this is
        pane_name = 'left' if pane_data is self.left_pane else 'right'
        
        # Get max entries from config
        max_entries = getattr(self.config, 'MAX_HISTORY_ENTRIES', 100)
        
        # Use the StateManager's method with pane-specific key
        self.state_manager.save_pane_cursor_position(pane_name, current_dir, current_file.name, max_entries)
    
    def restore_cursor_position(self, pane_data, display_height):
        """Restore cursor position from persistent history when changing to a directory"""
        current_dir = str(pane_data['path'])
        
        # If no state manager available, skip restoration
        if not self.state_manager:
            return False
        
        # Determine which pane this is
        pane_name = 'left' if pane_data is self.left_pane else 'right'
        
        # Use the StateManager's method to load cursor position for this specific pane
        target_filename = self.state_manager.load_pane_cursor_position(pane_name, current_dir)
        
        if target_filename:
            # Try to find this filename in current files
            for i, file_path in enumerate(pane_data['files']):
                if file_path.name == target_filename:
                    pane_data['selected_index'] = i
                    
                    # Adjust scroll offset to keep selection visible
                    if pane_data['selected_index'] < pane_data['scroll_offset']:
                        pane_data['scroll_offset'] = pane_data['selected_index']
                    elif pane_data['selected_index'] >= pane_data['scroll_offset'] + display_height:
                        pane_data['scroll_offset'] = pane_data['selected_index'] - display_height + 1
                    
                    return True
        
        return False
    
    def sync_current_to_other(self, log_callback=None):
        """Change current pane's directory to match the other pane's directory"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Check if both panes are already showing the same directory
        if current_pane['path'] == other_pane['path']:
            # Both panes show same directory, nothing to sync
            if log_callback:
                log_callback("Both panes already show the same directory")
            return False
        
        # Get the other pane's directory
        target_directory = other_pane['path']
        
        # Check if target directory exists and is accessible
        if not target_directory.exists():
            if log_callback:
                log_callback(f"Target directory does not exist: {target_directory}")
            return False
            
        if not target_directory.is_dir():
            if log_callback:
                log_callback(f"Target is not a directory: {target_directory}")
            return False
            
        try:
            # Test if we can access the directory
            list(target_directory.iterdir())
        except PermissionError:
            if log_callback:
                log_callback(f"Permission denied accessing: {target_directory}")
            return False
        except Exception as e:
            if log_callback:
                log_callback(f"Error accessing directory: {e}")
            return False
        
        # Save current cursor position before changing directory
        self.save_cursor_position(current_pane)
        
        # Change current pane to the other pane's directory
        old_directory = current_pane['path']
        current_pane['path'] = target_directory
        current_pane['selected_index'] = 0
        current_pane['scroll_offset'] = 0
        current_pane['selected_files'].clear()  # Clear selections when changing directory
        
        # Log the change
        if log_callback:
            pane_name = "left" if self.active_pane == 'left' else "right"
            log_callback(f"Synchronized {pane_name} pane: {old_directory} → {target_directory}")
        
        return True
    
    def sync_other_to_current(self, log_callback=None):
        """Change other pane's directory to match the current pane's directory"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Check if both panes are already showing the same directory
        if current_pane['path'] == other_pane['path']:
            # Both panes show same directory, nothing to sync
            if log_callback:
                log_callback("Both panes already show the same directory")
            return False
        
        # Get the current pane's directory
        target_directory = current_pane['path']
        
        # Check if target directory exists and is accessible
        if not target_directory.exists():
            if log_callback:
                log_callback(f"Current directory does not exist: {target_directory}")
            return False
            
        if not target_directory.is_dir():
            if log_callback:
                log_callback(f"Current path is not a directory: {target_directory}")
            return False
            
        try:
            # Test if we can access the directory
            list(target_directory.iterdir())
        except PermissionError:
            if log_callback:
                log_callback(f"Permission denied accessing: {target_directory}")
            return False
        except Exception as e:
            if log_callback:
                log_callback(f"Error accessing directory: {e}")
            return False
        
        # Save current cursor position in other pane before changing directory
        self.save_cursor_position(other_pane)
        
        # Change other pane to the current pane's directory
        old_directory = other_pane['path']
        other_pane['path'] = target_directory
        other_pane['selected_index'] = 0
        other_pane['scroll_offset'] = 0
        other_pane['selected_files'].clear()  # Clear selections when changing directory
        
        # Log the change
        if log_callback:
            other_pane_name = "right" if self.active_pane == 'left' else "left"
            current_pane_name = "left" if self.active_pane == 'left' else "right"
            log_callback(f"Synchronized {other_pane_name} pane to {current_pane_name} pane: {old_directory} → {target_directory}")
        
        return True
    
    def sync_cursor_to_other_pane(self, log_callback=None):
        """Move cursor in current pane to the same filename as the other pane's cursor"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Get the currently selected file in the other pane
        if not other_pane['files'] or other_pane['selected_index'] >= len(other_pane['files']):
            if log_callback:
                log_callback("No file selected in other pane")
            return False
            
        other_selected_file = other_pane['files'][other_pane['selected_index']]
        target_filename = other_selected_file.name
        
        # Find the same filename in current pane
        target_index = None
        for i, file_path in enumerate(current_pane['files']):
            if file_path.name == target_filename:
                target_index = i
                break
        
        if target_index is not None:
            # Move cursor to the matching file
            current_pane['selected_index'] = target_index
            
            if log_callback:
                pane_name = "left" if self.active_pane == 'left' else "right"
                log_callback(f"Moved {pane_name} pane cursor to: {target_filename}")
            return True
        else:
            if log_callback:
                log_callback(f"File '{target_filename}' not found in current pane")
            return False
    
    def sync_cursor_from_current_pane(self, log_callback=None):
        """Move cursor in other pane to the same filename as the current pane's cursor"""
        current_pane = self.get_current_pane()
        other_pane = self.get_inactive_pane()
        
        # Get the currently selected file in the current pane
        if not current_pane['files'] or current_pane['selected_index'] >= len(current_pane['files']):
            if log_callback:
                log_callback("No file selected in current pane")
            return False
            
        current_selected_file = current_pane['files'][current_pane['selected_index']]
        target_filename = current_selected_file.name
        
        # Find the same filename in other pane
        target_index = None
        for i, file_path in enumerate(other_pane['files']):
            if file_path.name == target_filename:
                target_index = i
                break
        
        if target_index is not None:
            # Move cursor to the matching file in other pane
            other_pane['selected_index'] = target_index
            
            if log_callback:
                other_pane_name = "right" if self.active_pane == 'left' else "left"
                log_callback(f"Moved {other_pane_name} pane cursor to: {target_filename}")
            return True
        else:
            if log_callback:
                other_pane_name = "right" if self.active_pane == 'left' else "left"
                log_callback(f"File '{target_filename}' not found in {other_pane_name} pane")
            return False
    
    def adjust_scroll_for_selection(self, pane_data, display_height):
        """Ensure the selected item is visible by adjusting scroll offset"""
        if pane_data['selected_index'] < pane_data['scroll_offset']:
            pane_data['scroll_offset'] = pane_data['selected_index']
        elif pane_data['selected_index'] >= pane_data['scroll_offset'] + display_height:
            pane_data['scroll_offset'] = pane_data['selected_index'] - display_height + 1
    
    def count_files_and_dirs(self, pane_data):
        """Count directories and files in a pane"""
        if not pane_data['files']:
            return 0, 0
            
        files = pane_data['files']
        
        dir_count = 0
        file_count = 0
        
        for file_path in files:
            if file_path.is_dir():
                dir_count += 1
            else:
                file_count += 1
                
        return dir_count, file_count