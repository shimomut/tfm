#!/usr/bin/env python3
"""
TFM File List Manager - Manages file lists, sorting, filtering, and selection
"""

import os
import stat
import fnmatch
from tfm_path import Path
from datetime import datetime


class FileListManager:
    """Manages file lists, sorting, filtering, and selection.
    
    This class handles all file list management operations for file panes,
    including refreshing directory contents, sorting entries, applying filters,
    and managing file selection state.
    """
    
    def __init__(self, config):
        self.config = config
        self.show_hidden = getattr(config, 'SHOW_HIDDEN_FILES', False)
        self.log_manager = None  # Will be set by FileManager if available
        # Use module-level getLogger - no need to check if log_manager exists
        from tfm_log_manager import getLogger
        self.logger = getLogger("FileOp")
    
    def refresh_files(self, pane_data):
        """Refresh the file list for specified pane.
        
        This method reads the directory contents, applies filters, and updates
        the pane's file list. It handles both regular directories and archive
        virtual directories.
        
        Args:
            pane_data: Dictionary containing pane state including:
                - path: Path object for the directory
                - filter_pattern: Optional filename filter pattern
                - show_hidden: Whether to show hidden files
        
        Updates:
            - pane_data['files']: List of file Path objects
            - pane_data['error']: Error message if refresh fails
        
        Error Handling:
            - Logs errors and sets pane_data['error'] message
            - Handles archive-specific errors (corrupted, permissions, etc.)
            - Handles general I/O errors
        """
        try:
            # Import archive exceptions for specific error handling
            from tfm_archive import (
                ArchiveError, ArchiveNavigationError, ArchiveCorruptedError,
                ArchivePermissionError
            )
            
            # Get all entries in the directory
            all_entries = list(pane_data['path'].iterdir())
            
            # Filter hidden files if needed
            if not self.show_hidden:
                all_entries = [entry for entry in all_entries if not entry.name.startswith('.')]
            
            # Apply filename filter if active (only to files, not directories)
            if pane_data['filter_pattern']:
                filtered_entries = []
                for entry in all_entries:
                    # Always include directories, only filter files
                    if entry.is_dir() or fnmatch.fnmatch(entry.name.lower(), pane_data['filter_pattern'].lower()):
                        filtered_entries.append(entry)
                all_entries = filtered_entries
            
            # Sort the entries
            pane_data['files'] = self.sort_entries(
                all_entries, 
                pane_data['sort_mode'], 
                pane_data['sort_reverse']
            )
            
            # Ensure focused index is valid
            if pane_data['files']:
                pane_data['focused_index'] = min(pane_data['focused_index'], len(pane_data['files']) - 1)
            else:
                pane_data['focused_index'] = 0
            
            # Clean up selected files - remove any that no longer exist
            current_file_paths = {str(f) for f in pane_data['files']}
            pane_data['selected_files'] = pane_data['selected_files'] & current_file_paths
            
        except ArchiveNavigationError as e:
            # Archive navigation error - path doesn't exist in archive
            user_msg = getattr(e, 'user_message', str(e))
            self.logger.error(f"Archive navigation error: {user_msg}")
            self.logger.error(f"Archive navigation error: {pane_data['path']}: {e}")
            pane_data['files'] = []
            pane_data['focused_index'] = 0
        except ArchiveCorruptedError as e:
            # Archive is corrupted
            user_msg = getattr(e, 'user_message', str(e))
            self.logger.error(f"Corrupted archive: {user_msg}")
            self.logger.error(f"Corrupted archive: {pane_data['path']}: {e}")
            pane_data['files'] = []
            pane_data['focused_index'] = 0
        except ArchivePermissionError as e:
            # Permission denied for archive
            user_msg = getattr(e, 'user_message', str(e))
            self.logger.error(f"Permission denied: {user_msg}")
            self.logger.error(f"Archive permission denied: {pane_data['path']}: {e}")
            pane_data['files'] = []
            pane_data['focused_index'] = 0
        except ArchiveError as e:
            # Generic archive error
            user_msg = getattr(e, 'user_message', str(e))
            self.logger.error(f"Archive error: {user_msg}")
            self.logger.error(f"Archive error: {pane_data['path']}: {e}")
            pane_data['files'] = []
            pane_data['focused_index'] = 0
        except PermissionError as e:
            self.logger.error(f"Permission denied accessing directory {pane_data['path']}: {e}")
            pane_data['files'] = []
            pane_data['focused_index'] = 0
        except FileNotFoundError as e:
            self.logger.error(f"Directory not found: {pane_data['path']}: {e}")
            pane_data['files'] = []
            pane_data['focused_index'] = 0
        except OSError as e:
            self.logger.error(f"System error reading directory {pane_data['path']}: {e}")
            pane_data['files'] = []
            pane_data['focused_index'] = 0
        except Exception as e:
            self.logger.error(f"Unexpected error reading directory {pane_data['path']}: {e}")
            pane_data['files'] = []
            pane_data['focused_index'] = 0
    
    def sort_entries(self, entries, sort_mode, reverse=False):
        """Sort file entries based on the specified mode
        
        Args:
            entries: List of Path objects to sort
            sort_mode: 'name', 'ext', 'size', or 'date'
            reverse: Whether to reverse the sort order
            
        Returns:
            Sorted list with directories always first
        """
        def get_sort_key(entry):
            """Generate sort key for an entry"""
            try:
                if sort_mode == 'size':
                    return entry.stat().st_size if entry.is_file() else 0
                elif sort_mode == 'date':
                    return entry.stat().st_mtime
                elif sort_mode == 'type':
                    if entry.is_dir():
                        return ""  # Directories first
                    else:
                        return entry.suffix.lower()
                elif sort_mode == 'ext':
                    if entry.is_dir():
                        return ""  # Directories first (no extension)
                    else:
                        # Use the same extension logic as rendering
                        from tfm_main import FileManager
                        # Create a temporary instance to access the method
                        # We'll use a simpler approach here
                        filename = entry.name
                        dot_index = filename.rfind('.')
                        if dot_index <= 0:
                            return ""  # No extension
                        extension = filename[dot_index:]
                        # Check extension length limit (same as rendering)
                        max_ext_length = getattr(self.config, 'MAX_EXTENSION_LENGTH', 5)
                        if len(extension) > max_ext_length:
                            return ""  # Extension too long, treat as no extension
                        return extension.lower()
                else:  # name (default)
                    return entry.name.lower()
            except (OSError, PermissionError):
                # If we can't get file info, use name as fallback
                return entry.name.lower()
        
        # Separate directories and files
        directories = [entry for entry in entries if entry.is_dir()]
        files = [entry for entry in entries if not entry.is_dir()]
        
        # Sort each group separately
        sorted_dirs = sorted(directories, key=get_sort_key, reverse=reverse)
        sorted_files = sorted(files, key=get_sort_key, reverse=reverse)
        
        # Always put directories first
        return sorted_dirs + sorted_files
    
    def get_sort_description(self, pane_data):
        """Get a human-readable description of the current sort mode"""
        mode = pane_data['sort_mode']
        reverse = pane_data['sort_reverse']
        
        descriptions = {
            'name': 'Name',
            'ext':  'Ext',
            'size': 'Size', 
            'date': 'Date',
        }
        
        description = descriptions.get(mode, 'Name')
        if reverse:
            description += ' ↓'
        else:
            description += ' ↑'
        
        return description
    def _format_date(self, timestamp):
        """Format date/time based on configured format.
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            str: Formatted date/time string
        """
        from tfm_const import DATE_FORMAT_FULL, DATE_FORMAT_SHORT
        
        dt = datetime.fromtimestamp(timestamp)
        date_format = getattr(self.config, 'DATE_FORMAT', 'short')
        
        if date_format == DATE_FORMAT_FULL:
            # YYYY-MM-DD HH:mm:ss
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:  # DATE_FORMAT_SHORT (default)
            # YY-MM-DD HH:mm
            return dt.strftime("%y-%m-%d %H:%M")
    
    def get_file_info(self, path):
        """Get file information for display"""
        try:
            stat_info = path.stat()
            
            # Format size - display "<DIR>" for directories
            if path.is_dir():
                size_str = "<DIR>"
            else:
                size = stat_info.st_size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f}K"
                elif size < 1024 * 1024 * 1024:
                    size_str = f"{size/(1024*1024):.1f}M"
                else:
                    size_str = f"{size/(1024*1024*1024):.1f}G"
            
            # Format date based on configured format
            date_str = self._format_date(stat_info.st_mtime)
            
            return size_str, date_str
        except (OSError, PermissionError):
            return "---", "---"
    
    def toggle_selection(self, pane_data, move_cursor=True, direction=1):
        """Toggle selection of current file/directory and optionally move cursor.
        
        This method toggles the selection state of the currently focused file
        and optionally moves the cursor to the next/previous file.
        
        Args:
            pane_data: Dictionary containing pane state
            move_cursor: If True, move cursor after toggling selection
            direction: Direction to move cursor (1 for down, -1 for up)
        
        Returns:
            Tuple of (success: bool, message: str)
        
        Updates:
            - pane_data['selected_files']: Set of selected file paths
            - pane_data['focused_index']: Current cursor position (if move_cursor=True)
        """
        if not pane_data['files']:
            return False, "No files to select"
            
        focused_file = pane_data['files'][pane_data['focused_index']]
        file_path_str = str(focused_file)
        
        if file_path_str in pane_data['selected_files']:
            pane_data['selected_files'].remove(file_path_str)
            message = f"Deselected: {focused_file.name}"
        else:
            pane_data['selected_files'].add(file_path_str)
            message = f"Selected: {focused_file.name}"
        
        # Move cursor if requested
        if move_cursor:
            if direction > 0 and pane_data['focused_index'] < len(pane_data['files']) - 1:
                pane_data['focused_index'] += 1
            elif direction < 0 and pane_data['focused_index'] > 0:
                pane_data['focused_index'] -= 1
        
        return True, message
    
    def toggle_all_files_selection(self, pane_data):
        """Toggle selection status of all files (not directories) in current pane"""
        if not pane_data['files']:
            return False, "No files to select in current directory"
        
        # Get all files (not directories) in current pane
        files_only = []
        for file_path in pane_data['files']:
            if not file_path.is_dir():
                files_only.append(file_path)
        
        if not files_only:
            return False, "No files to select in current directory"
        
        # Inverse selection status for each file
        files_only_str = {str(f) for f in files_only}
        selected_count = 0
        deselected_count = 0
        
        for file_str in files_only_str:
            if file_str in pane_data['selected_files']:
                # Currently selected, deselect it
                pane_data['selected_files'].discard(file_str)
                deselected_count += 1
            else:
                # Currently not selected, select it
                pane_data['selected_files'].add(file_str)
                selected_count += 1
        
        message = f"Inversed selection: {selected_count} selected, {deselected_count} deselected"
        return True, message
    
    def toggle_all_items_selection(self, pane_data):
        """Toggle selection status of all items (files and directories) in current pane"""
        if not pane_data['files']:
            return False, "No items to select in current directory"
        
        # Get all items
        all_items = pane_data['files']
        
        if not all_items:
            return False, "No items to select in current directory"
        
        # Inverse selection status for each item
        all_items_str = {str(f) for f in all_items}
        selected_count = 0
        deselected_count = 0
        
        for item_str in all_items_str:
            if item_str in pane_data['selected_files']:
                # Currently selected, deselect it
                pane_data['selected_files'].discard(item_str)
                deselected_count += 1
            else:
                # Currently not selected, select it
                pane_data['selected_files'].add(item_str)
                selected_count += 1
        
        message = f"Inversed selection: {selected_count} selected, {deselected_count} deselected"
        return True, message
    
    def find_matches(self, pane_data, pattern, match_all=False, return_indices_only=False):
        """Find all files matching the fnmatch patterns in current pane
        
        Args:
            pane_data: Pane data dictionary
            pattern: Search pattern (supports multiple patterns separated by spaces)
            match_all: If True, all patterns must match (AND logic). If False, any pattern can match (OR logic)
            return_indices_only: If True, return list of indices. If False, return list of (index, filename) tuples
            
        Returns:
            List of matches (either indices or (index, filename) tuples based on return_indices_only)
        """
        if not pattern or not pane_data['files']:
            return []
        
        matches = []
        
        # Split pattern by spaces to get individual patterns
        patterns = pattern.strip().split()
        if not patterns:
            return []
        
        # Convert all patterns to lowercase for case-insensitive matching
        # and wrap each pattern with wildcards to match "contains" behavior
        wrapped_patterns = []
        for p in patterns:
            p_lower = p.lower()
            # If pattern doesn't start with *, add it for "contains" matching
            if not p_lower.startswith('*'):
                p_lower = '*' + p_lower
            # If pattern doesn't end with *, add it for "contains" matching  
            if not p_lower.endswith('*'):
                p_lower = p_lower + '*'
            wrapped_patterns.append(p_lower)
        
        for i, file_path in enumerate(pane_data['files']):
            filename_lower = file_path.name.lower()
            
            if match_all:
                # Check if filename matches ALL patterns (AND logic)
                all_match = True
                for wrapped_pattern in wrapped_patterns:
                    if not fnmatch.fnmatch(filename_lower, wrapped_pattern):
                        all_match = False
                        break
                
                if all_match:
                    if return_indices_only:
                        matches.append(i)
                    else:
                        matches.append((i, file_path.name))
            else:
                # Check if filename matches ANY of the patterns (OR logic)
                match_found = False
                for wrapped_pattern in wrapped_patterns:
                    if fnmatch.fnmatch(filename_lower, wrapped_pattern):
                        match_found = True
                        break
                
                if match_found:
                    if return_indices_only:
                        matches.append(i)
                    else:
                        matches.append((i, file_path.name))
        
        return matches
    
    def apply_filter(self, pane_data, pattern):
        """Apply filename filter pattern to the specified pane.
        
        This method sets the filter pattern and refreshes the file list to
        show only files matching the pattern. Directories are always shown.
        
        Args:
            pane_data: Dictionary containing pane state
            pattern: Filename pattern (e.g., "*.txt", "test*")
                    Empty string clears the filter
        
        Updates:
            - pane_data['filter_pattern']: Current filter pattern
            - pane_data['files']: Filtered file list (via refresh_files)
        """
        pane_data['filter_pattern'] = pattern
        
        # Reset selection and scroll when filter changes
        pane_data['focused_index'] = 0
        pane_data['scroll_offset'] = 0
        pane_data['selected_files'].clear()  # Clear selections when filter changes
        
        # Refresh files with new filter
        self.refresh_files(pane_data)
        
        return len(pane_data['files'])
    
    def clear_filter(self, pane_data):
        """Clear the filter for the specified pane"""
        if pane_data['filter_pattern']:
            pane_data['filter_pattern'] = ""
            pane_data['focused_index'] = 0
            pane_data['scroll_offset'] = 0
            self.refresh_files(pane_data)
            return True
        return False
    
    def toggle_hidden_files(self):
        """Toggle showing hidden files"""
        self.show_hidden = not self.show_hidden
        return self.show_hidden
