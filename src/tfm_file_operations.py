#!/usr/bin/env python3
"""
TFM File Operations - Handles file system operations and file management
"""

import os
import stat
import fnmatch
import shutil
from tfm_path import Path
from tfm_progress_manager import ProgressManager, OperationType
from datetime import datetime


class FileOperations:
    """Handles file system operations and file management"""
    
    def __init__(self, config):
        self.config = config
        self.show_hidden = getattr(config, 'SHOW_HIDDEN_FILES', False)
    
    def refresh_files(self, pane_data):
        """Refresh the file list for specified pane"""
        try:
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
            
            # Ensure selected index is valid
            if pane_data['files']:
                pane_data['selected_index'] = min(pane_data['selected_index'], len(pane_data['files']) - 1)
            else:
                pane_data['selected_index'] = 0
            
            # Clean up selected files - remove any that no longer exist
            current_file_paths = {str(f) for f in pane_data['files']}
            pane_data['selected_files'] = pane_data['selected_files'] & current_file_paths
            
        except PermissionError as e:
            print(f"Permission denied accessing directory {pane_data['path']}: {e}")
            pane_data['files'] = []
            pane_data['selected_index'] = 0
        except FileNotFoundError as e:
            print(f"Directory not found: {pane_data['path']}: {e}")
            pane_data['files'] = []
            pane_data['selected_index'] = 0
        except OSError as e:
            print(f"System error reading directory {pane_data['path']}: {e}")
            pane_data['files'] = []
            pane_data['selected_index'] = 0
        except Exception as e:
            print(f"Unexpected error reading directory {pane_data['path']}: {e}")
            pane_data['files'] = []
            pane_data['selected_index'] = 0
    
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
    
    def get_file_info(self, path):
        """Get file information for display"""
        try:
            stat_info = path.stat()
            
            # Format size
            size = stat_info.st_size
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f}K"
            elif size < 1024 * 1024 * 1024:
                size_str = f"{size/(1024*1024):.1f}M"
            else:
                size_str = f"{size/(1024*1024*1024):.1f}G"
            
            # Format date
            date_str = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
            
            return size_str, date_str
        except (OSError, PermissionError):
            return "---", "---"
    
    def toggle_selection(self, pane_data, move_cursor=True, direction=1):
        """Toggle selection of current file/directory and optionally move cursor"""
        if not pane_data['files']:
            return False, "No files to select"
            
        selected_file = pane_data['files'][pane_data['selected_index']]
        file_path_str = str(selected_file)
        
        if file_path_str in pane_data['selected_files']:
            pane_data['selected_files'].remove(file_path_str)
            message = f"Deselected: {selected_file.name}"
        else:
            pane_data['selected_files'].add(file_path_str)
            message = f"Selected: {selected_file.name}"
        
        # Move cursor if requested
        if move_cursor:
            if direction > 0 and pane_data['selected_index'] < len(pane_data['files']) - 1:
                pane_data['selected_index'] += 1
            elif direction < 0 and pane_data['selected_index'] > 0:
                pane_data['selected_index'] -= 1
        
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
        
        # Check if all files are currently selected
        files_only_str = {str(f) for f in files_only}
        currently_selected_files = pane_data['selected_files'] & files_only_str
        
        if len(currently_selected_files) == len(files_only):
            # All files are selected, deselect them all
            pane_data['selected_files'] -= files_only_str
            message = f"Deselected all {len(files_only)} files"
        else:
            # Not all files are selected, select them all
            pane_data['selected_files'].update(files_only_str)
            message = f"Selected all {len(files_only)} files"
        
        return True, message
    
    def toggle_all_items_selection(self, pane_data):
        """Toggle selection status of all items (files and directories) in current pane"""
        if not pane_data['files']:
            return False, "No items to select in current directory"
        
        # Get all items
        all_items = pane_data['files']
        
        if not all_items:
            return False, "No items to select in current directory"
        
        # Check if all items are currently selected
        all_items_str = {str(f) for f in all_items}
        currently_selected_items = pane_data['selected_files'] & all_items_str
        
        if len(currently_selected_items) == len(all_items):
            # All items are selected, deselect them all
            pane_data['selected_files'] -= all_items_str
            message = f"Deselected all {len(all_items)} items"
        else:
            # Not all items are selected, select them all
            pane_data['selected_files'].update(all_items_str)
            message = f"Selected all {len(all_items)} items"
        
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
        """Apply the current filter pattern to the specified pane"""
        pane_data['filter_pattern'] = pattern
        
        # Reset selection and scroll when filter changes
        pane_data['selected_index'] = 0
        pane_data['scroll_offset'] = 0
        pane_data['selected_files'].clear()  # Clear selections when filter changes
        
        # Refresh files with new filter
        self.refresh_files(pane_data)
        
        return len(pane_data['files'])
    
    def clear_filter(self, pane_data):
        """Clear the filter for the specified pane"""
        if pane_data['filter_pattern']:
            pane_data['filter_pattern'] = ""
            pane_data['selected_index'] = 0
            pane_data['scroll_offset'] = 0
            self.refresh_files(pane_data)
            return True
        return False
    
    def toggle_hidden_files(self):
        """Toggle showing hidden files"""
        self.show_hidden = not self.show_hidden
        return self.show_hidden


class FileOperationsUI:
    """Handles file operation UI interactions for the file manager"""
    
    def __init__(self, file_manager, file_operations):
        """Initialize file operations UI with file manager and file operations"""
        self.file_manager = file_manager
        self.file_operations = file_operations
        self.log_manager = file_manager.log_manager
        self.progress_manager = file_manager.progress_manager
        self.cache_manager = file_manager.cache_manager
        self.config = file_manager.config
    
    def copy_selected_files(self):
        """Copy selected files to the opposite pane's directory"""
        current_pane = self.file_manager.get_current_pane()
        other_pane = self.file_manager.get_inactive_pane()
        
        # Get files to copy - either selected files or current file if none selected
        files_to_copy = []
        
        if current_pane['selected_files']:
            # Copy all selected files
            for file_path_str in current_pane['selected_files']:
                file_path = Path(file_path_str)
                if file_path.exists():
                    files_to_copy.append(file_path)
        else:
            # Copy current file if no files are selected
            if current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']]
                files_to_copy.append(selected_file)
        
        if not files_to_copy:
            print("No files to copy")
            return
        
        destination_dir = other_pane['path']
        
        # Check if destination directory is writable (only for local paths)
        if destination_dir.get_scheme() == 'file' and not os.access(destination_dir, os.W_OK):
            print(f"Permission denied: Cannot write to {destination_dir}")
            return
        
        # Check if copy confirmation is enabled
        if getattr(self.config, 'CONFIRM_COPY', True):
            # Show confirmation dialog
            if len(files_to_copy) == 1:
                message = f"Copy '{files_to_copy[0].name}' to {destination_dir}?"
            else:
                message = f"Copy {len(files_to_copy)} items to {destination_dir}?"
            
            def copy_callback(confirmed):
                if confirmed:
                    self.copy_files_to_directory(files_to_copy, destination_dir)
                else:
                    print("Copy operation cancelled")
            
            self.file_manager.show_confirmation(message, copy_callback)
        else:
            # Start copying files without confirmation
            self.copy_files_to_directory(files_to_copy, destination_dir)
    
    def copy_files_to_directory(self, files_to_copy, destination_dir):
        """Copy a list of files to the destination directory with conflict resolution"""
        conflicts = []
        
        # Check for conflicts first
        for source_file in files_to_copy:
            dest_path = destination_dir / source_file.name
            if dest_path.exists():
                conflicts.append((source_file, dest_path))
        
        if conflicts:
            # Show conflict resolution dialog
            conflict_names = [f.name for f, _ in conflicts]
            if len(conflicts) == 1:
                message = f"'{conflict_names[0]}' already exists in destination."
            else:
                message = f"{len(conflicts)} files already exist in destination."
            
            choices = [
                {"text": "Overwrite", "key": "o", "value": "overwrite"},
                {"text": "Skip", "key": "s", "value": "skip"},
                {"text": "Cancel", "key": "c", "value": "cancel"}
            ]
            
            def handle_conflict_choice(choice):
                if choice == "cancel":
                    print("Copy operation cancelled")
                    return
                elif choice == "skip":
                    # Copy only non-conflicting files
                    non_conflicting = [f for f in files_to_copy 
                                     if not (destination_dir / f.name).exists()]
                    if non_conflicting:
                        self.perform_copy_operation(non_conflicting, destination_dir)
                        print(f"Copied {len(non_conflicting)} files, skipped {len(conflicts)} conflicts")
                    else:
                        print("No files copied (all had conflicts)")
                elif choice == "overwrite":
                    # Copy all files, overwriting conflicts
                    self.perform_copy_operation(files_to_copy, destination_dir, overwrite=True)
                    print(f"Copied {len(files_to_copy)} files (overwrote {len(conflicts)} existing)")
            
            self.file_manager.show_dialog(message, choices, handle_conflict_choice)
        else:
            # No conflicts, copy directly
            self.perform_copy_operation(files_to_copy, destination_dir)
            print(f"Copied {len(files_to_copy)} files")
    
    def perform_copy_operation(self, files_to_copy, destination_dir, overwrite=False):
        """Perform the actual copy operation with fine-grained progress tracking"""
        copied_count = 0
        error_count = 0
        
        # Count total individual files for fine-grained progress
        total_individual_files = self._count_files_recursively(files_to_copy)
        
        # Start progress tracking for copy operation
        if total_individual_files > 1:  # Only show progress for multiple files
            self.progress_manager.start_operation(
                OperationType.COPY, 
                total_individual_files, 
                f"to {destination_dir.name}",
                self._progress_callback
            )
        
        processed_files = 0
        
        try:
            for source_file in files_to_copy:
                try:
                    dest_path = destination_dir / source_file.name
                    
                    # Skip if file exists and we're not overwriting
                    if dest_path.exists() and not overwrite:
                        # Still need to count skipped files for progress
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                            if total_individual_files > 1:
                                self.progress_manager.update_progress(f"Skipped: {source_file.name}", processed_files)
                        elif source_file.is_dir():
                            # Count files in skipped directory
                            skipped_count = self._count_files_recursively([source_file])
                            processed_files += skipped_count
                            if total_individual_files > 1:
                                self.progress_manager.update_progress(f"Skipped: {source_file.name}", processed_files)
                        continue
                    
                    if source_file.is_dir():
                        # Copy directory recursively with progress tracking
                        if dest_path.exists() and overwrite:
                            if dest_path.is_dir():
                                # For S3, we can't use rmtree, so we'll let copy_to handle it
                                pass
                            else:
                                dest_path.unlink()
                        
                        if source_file.get_scheme() == dest_path.get_scheme() == 'file':
                            # Local to local - use the existing progress method
                            processed_files = self._copy_directory_with_progress(
                                source_file, dest_path, processed_files, total_individual_files
                            )
                        else:
                            # Cross-storage copy - use the new method
                            source_file.copy_to(dest_path, overwrite=overwrite)
                            # Update progress for the entire directory
                            dir_file_count = self._count_files_recursively([source_file])
                            processed_files += dir_file_count
                            if total_individual_files > 1:
                                self.progress_manager.update_progress(source_file.name, processed_files)
                        
                        print(f"Copied directory: {source_file.name}")
                    else:
                        # Copy single file
                        processed_files += 1
                        if total_individual_files > 1:
                            self.progress_manager.update_progress(source_file.name, processed_files)
                        
                        source_file.copy_to(dest_path, overwrite=overwrite)
                        print(f"Copied file: {source_file.name}")
                    
                    copied_count += 1
                    
                except PermissionError as e:
                    print(f"Permission denied copying {source_file.name}: {e}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                        elif source_file.is_dir():
                            processed_files += self._count_files_recursively([source_file])
                except Exception as e:
                    print(f"Error copying {source_file.name}: {e}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                        elif source_file.is_dir():
                            processed_files += self._count_files_recursively([source_file])
        
        finally:
            # Finish progress tracking
            if total_individual_files > 1:
                self.progress_manager.finish_operation()
        
        # Invalidate cache for affected directories
        if copied_count > 0:
            self.cache_manager.invalidate_cache_for_copy_operation(files_to_copy, destination_dir)
        
        # Refresh both panes to show the copied files
        self.file_manager.refresh_files()
        self.file_manager.needs_full_redraw = True
        
        # Clear selections after successful copy
        if copied_count > 0:
            current_pane = self.file_manager.get_current_pane()
            current_pane['selected_files'].clear()
        
        if error_count > 0:
            print(f"Copy completed with {error_count} errors")
    
    def move_selected_files(self):
        """Move selected files to the opposite pane's directory"""
        current_pane = self.file_manager.get_current_pane()
        other_pane = self.file_manager.get_inactive_pane()
        
        # Get files to move - either selected files or current file if none selected
        files_to_move = []
        
        if current_pane['selected_files']:
            # Move all selected files
            for file_path_str in current_pane['selected_files']:
                file_path = Path(file_path_str)
                if file_path.exists():
                    files_to_move.append(file_path)
        else:
            # Move current file if no files are selected
            if current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']]
                files_to_move.append(selected_file)
        
        if not files_to_move:
            print("No files to move")
            return
        
        destination_dir = other_pane['path']
        
        # Check if destination directory is writable (only for local paths)
        if destination_dir.get_scheme() == 'file' and not os.access(destination_dir, os.W_OK):
            print(f"Permission denied: Cannot write to {destination_dir}")
            return
        
        # Check for cross-storage move and inform user
        source_schemes = {f.get_scheme() for f in files_to_move}
        dest_scheme = destination_dir.get_scheme()
        is_cross_storage = any(scheme != dest_scheme for scheme in source_schemes)
        
        if is_cross_storage:
            # Inform user about cross-storage move
            scheme_names = {'file': 'Local', 's3': 'S3', 'scp': 'SCP', 'ftp': 'FTP'}
            source_names = [scheme_names.get(scheme, scheme.upper()) for scheme in source_schemes]
            dest_name = scheme_names.get(dest_scheme, dest_scheme.upper())
            print(f"Cross-storage move: {'/'.join(set(source_names))} → {dest_name}")
        
        # Check if any files are being moved to the same directory
        same_dir_files = [f for f in files_to_move if f.parent == destination_dir]
        if same_dir_files:
            if len(same_dir_files) == len(files_to_move):
                print("Cannot move files to the same directory")
                return
            else:
                # Remove files that are already in the destination directory
                files_to_move = [f for f in files_to_move if f.parent != destination_dir]
                print(f"Skipping {len(same_dir_files)} files already in destination directory")
        
        # Check if move confirmation is enabled
        if getattr(self.config, 'CONFIRM_MOVE', True):
            # Show confirmation dialog
            if len(files_to_move) == 1:
                message = f"Move '{files_to_move[0].name}' to {destination_dir}?"
            else:
                message = f"Move {len(files_to_move)} items to {destination_dir}?"
            
            def move_callback(confirmed):
                if confirmed:
                    self.move_files_to_directory(files_to_move, destination_dir)
                else:
                    print("Move operation cancelled")
            
            self.file_manager.show_confirmation(message, move_callback)
        else:
            # Start moving files without confirmation
            self.move_files_to_directory(files_to_move, destination_dir)
    
    def move_files_to_directory(self, files_to_move, destination_dir):
        """Move a list of files to the destination directory with conflict resolution"""
        conflicts = []
        
        # Check for conflicts first
        for source_file in files_to_move:
            dest_path = destination_dir / source_file.name
            if dest_path.exists():
                conflicts.append((source_file, dest_path))
        
        if conflicts:
            # Show conflict resolution dialog
            conflict_names = [f.name for f, _ in conflicts]
            if len(conflicts) == 1:
                message = f"'{conflict_names[0]}' already exists in destination."
            else:
                message = f"{len(conflicts)} files already exist in destination."
            
            choices = [
                {"text": "Overwrite", "key": "o", "value": "overwrite"},
                {"text": "Skip", "key": "s", "value": "skip"},
                {"text": "Cancel", "key": "c", "value": "cancel"}
            ]
            
            def handle_conflict_choice(choice):
                if choice == "cancel":
                    print("Move operation cancelled")
                    return
                elif choice == "skip":
                    # Move only non-conflicting files
                    non_conflicting = [f for f in files_to_move 
                                     if not (destination_dir / f.name).exists()]
                    if non_conflicting:
                        self.perform_move_operation(non_conflicting, destination_dir)
                        print(f"Moved {len(non_conflicting)} files, skipped {len(conflicts)} conflicts")
                    else:
                        print("No files moved (all had conflicts)")
                elif choice == "overwrite":
                    # Move all files, overwriting conflicts
                    self.perform_move_operation(files_to_move, destination_dir, overwrite=True)
                    print(f"Moved {len(files_to_move)} files (overwrote {len(conflicts)} existing)")
            
            self.file_manager.show_dialog(message, choices, handle_conflict_choice)
        else:
            # No conflicts, move directly
            self.perform_move_operation(files_to_move, destination_dir)
            print(f"Moved {len(files_to_move)} files")
    
    def perform_move_operation(self, files_to_move, destination_dir, overwrite=False):
        """Perform the actual move operation with fine-grained progress tracking"""
        moved_count = 0
        error_count = 0
        
        # Count total individual files for fine-grained progress
        total_individual_files = self._count_files_recursively(files_to_move)
        
        # Start progress tracking for move operation
        if total_individual_files > 1:  # Only show progress for multiple files
            self.progress_manager.start_operation(
                OperationType.MOVE, 
                total_individual_files, 
                f"to {destination_dir.name}",
                self._progress_callback
            )
        
        processed_files = 0
        
        try:
            for source_file in files_to_move:
                try:
                    dest_path = destination_dir / source_file.name
                    
                    # Skip if file exists and we're not overwriting
                    if dest_path.exists() and not overwrite:
                        # Still need to count skipped files for progress
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                            if total_individual_files > 1:
                                self.progress_manager.update_progress(f"Skipped: {source_file.name}", processed_files)
                        elif source_file.is_dir():
                            # Count files in skipped directory
                            skipped_count = self._count_files_recursively([source_file])
                            processed_files += skipped_count
                            if total_individual_files > 1:
                                self.progress_manager.update_progress(f"Skipped: {source_file.name}", processed_files)
                        continue
                    
                    # Remove destination if it exists and we're overwriting
                    if dest_path.exists() and overwrite:
                        if dest_path.is_dir():
                            # Use the existing delete method for recursive directory removal
                            self._delete_directory_with_progress(dest_path, 0, 1)
                        else:
                            dest_path.unlink()
                    
                    # Determine if this is a cross-storage move
                    source_scheme = source_file.get_scheme()
                    dest_scheme = destination_dir.get_scheme()
                    is_cross_storage = source_scheme != dest_scheme
                    
                    # Move the file/directory
                    if source_file.is_symlink() and not is_cross_storage:
                        # For symbolic links on same storage, copy the link itself (not the target)
                        processed_files += 1
                        if total_individual_files > 1:
                            self.progress_manager.update_progress(f"Link: {source_file.name}", processed_files)
                        
                        link_target = os.readlink(str(source_file))
                        dest_path.symlink_to(link_target)
                        source_file.unlink()
                        print(f"Moved symbolic link: {source_file.name}")
                    elif source_file.is_dir():
                        # For directories, we need to track individual files being moved
                        processed_files = self._move_directory_with_progress(
                            source_file, dest_path, processed_files, total_individual_files, is_cross_storage
                        )
                        print(f"Moved directory: {source_file.name}")
                    else:
                        # Move single file
                        processed_files += 1
                        if total_individual_files > 1:
                            self.progress_manager.update_progress(source_file.name, processed_files)
                        
                        if is_cross_storage:
                            # Cross-storage move: copy then delete
                            source_file.copy_to(dest_path, overwrite=overwrite)
                            source_file.unlink()
                            print(f"Moved file (cross-storage): {source_file.name}")
                        else:
                            # Same-storage move: use rename
                            source_file.rename(dest_path)
                            print(f"Moved file: {source_file.name}")
                    
                    moved_count += 1
                    
                except PermissionError as e:
                    print(f"Permission denied moving {source_file.name}: {e}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                        elif source_file.is_dir():
                            processed_files += self._count_files_recursively([source_file])
                except Exception as e:
                    print(f"Error moving {source_file.name}: {e}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                        elif source_file.is_dir():
                            processed_files += self._count_files_recursively([source_file])
        
        finally:
            # Finish progress tracking
            if total_individual_files > 1:
                self.progress_manager.finish_operation()
        
        # Invalidate cache for affected directories
        if moved_count > 0:
            self.cache_manager.invalidate_cache_for_move_operation(files_to_move, destination_dir)
        
        # Refresh both panes to show the moved files
        self.file_manager.refresh_files()
        self.file_manager.needs_full_redraw = True
        
        # Clear selections after successful move
        if moved_count > 0:
            current_pane = self.file_manager.get_current_pane()
            current_pane['selected_files'].clear()
        
        if error_count > 0:
            print(f"Move completed with {error_count} errors")
    
    def delete_selected_files(self):
        """Delete selected files or current file with confirmation"""
        current_pane = self.file_manager.get_current_pane()
        
        # Get files to delete - either selected files or current file if none selected
        files_to_delete = []
        
        if current_pane['selected_files']:
            # Delete all selected files
            for file_path_str in current_pane['selected_files']:
                file_path = Path(file_path_str)
                if file_path.exists():
                    files_to_delete.append(file_path)
        else:
            # Delete current file if no files are selected
            if current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']]
                files_to_delete.append(selected_file)
        
        if not files_to_delete:
            print("No files to delete")
            return
        
        def handle_delete_confirmation(confirmed):
            if confirmed:
                self.perform_delete_operation(files_to_delete)
            else:
                print("Delete operation cancelled")
        
        # Check if delete confirmation is enabled
        if getattr(self.config, 'CONFIRM_DELETE', True):
            # Show confirmation dialog
            if len(files_to_delete) == 1:
                file_name = files_to_delete[0].name
                if files_to_delete[0].is_dir():
                    message = f"Delete directory '{file_name}' and all its contents?"
                else:
                    message = f"Delete file '{file_name}'?"
            else:
                dir_count = sum(1 for f in files_to_delete if f.is_dir())
                file_count = len(files_to_delete) - dir_count
                if dir_count > 0 and file_count > 0:
                    message = f"Delete {len(files_to_delete)} items ({dir_count} directories, {file_count} files)?"
                elif dir_count > 0:
                    message = f"Delete {dir_count} directories and all their contents?"
                else:
                    message = f"Delete {file_count} files?"
            
            choices = [
                {"text": "Yes", "key": "y", "value": True},
                {"text": "No", "key": "n", "value": False}
            ]
            
            self.file_manager.show_dialog(message, choices, handle_delete_confirmation)
        else:
            # Delete without confirmation
            handle_delete_confirmation(True)
    
    def perform_delete_operation(self, files_to_delete):
        """Perform the actual delete operation with fine-grained progress tracking"""
        deleted_count = 0
        error_count = 0
        
        # Count total individual files for fine-grained progress
        total_individual_files = self._count_files_recursively(files_to_delete)
        
        # Start progress tracking for delete operation
        if total_individual_files > 1:  # Only show progress for multiple files
            self.progress_manager.start_operation(
                OperationType.DELETE, 
                total_individual_files, 
                "",
                self._progress_callback
            )
        
        processed_files = 0
        
        try:
            for file_path in files_to_delete:
                try:
                    if file_path.is_symlink():
                        # Delete symbolic link (not its target)
                        processed_files += 1
                        if total_individual_files > 1:
                            self.progress_manager.update_progress(f"Link: {file_path.name}", processed_files)
                        
                        file_path.unlink()
                        print(f"Deleted symbolic link: {file_path.name}")
                    elif file_path.is_dir():
                        # Delete directory recursively with progress tracking
                        processed_files = self._delete_directory_with_progress(
                            file_path, processed_files, total_individual_files
                        )
                        print(f"Deleted directory: {file_path.name}")
                    else:
                        # Delete single file
                        processed_files += 1
                        if total_individual_files > 1:
                            self.progress_manager.update_progress(file_path.name, processed_files)
                        
                        file_path.unlink()
                        print(f"Deleted file: {file_path.name}")
                    
                    deleted_count += 1
                    
                except PermissionError as e:
                    print(f"Permission denied deleting {file_path.name}: {e}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if file_path.is_file() or file_path.is_symlink():
                            processed_files += 1
                        elif file_path.is_dir():
                            processed_files += self._count_files_recursively([file_path])
                except FileNotFoundError:
                    print(f"File not found (already deleted?): {file_path.name}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if file_path.is_file() or file_path.is_symlink():
                            processed_files += 1
                        elif file_path.is_dir():
                            processed_files += self._count_files_recursively([file_path])
                except Exception as e:
                    print(f"Error deleting {file_path.name}: {e}")
                    error_count += 1
                    if total_individual_files > 1:
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if file_path.is_file() or file_path.is_symlink():
                            processed_files += 1
                        elif file_path.is_dir():
                            processed_files += self._count_files_recursively([file_path])
        
        finally:
            # Finish progress tracking
            if total_individual_files > 1:
                self.progress_manager.finish_operation()
        
        # Invalidate cache for affected directories
        if deleted_count > 0:
            self.cache_manager.invalidate_cache_for_delete_operation(files_to_delete)
        
        # Refresh current pane to show the changes
        self.file_manager.refresh_files(self.file_manager.get_current_pane())
        self.file_manager.needs_full_redraw = True
        
        # Clear selections after delete operation
        current_pane = self.file_manager.get_current_pane()
        current_pane['selected_files'].clear()
        
        # Adjust cursor position if it's now out of bounds
        if current_pane['selected_index'] >= len(current_pane['files']):
            current_pane['selected_index'] = max(0, len(current_pane['files']) - 1)
        
        # Report results
        if deleted_count > 0:
            print(f"Successfully deleted {deleted_count} items")
    
    # Helper methods
    def _count_files_recursively(self, paths):
        """Count total number of individual files in the given paths (including files in directories)"""
        total_files = 0
        for path in paths:
            if path.is_file() or path.is_symlink():
                total_files += 1
            elif path.is_dir():
                try:
                    for root, dirs, files in os.walk(path):
                        total_files += len(files)
                        # Count symlinks to directories as files
                        for d in dirs:
                            dir_path = Path(root) / d
                            if dir_path.is_symlink():
                                total_files += 1
                except (PermissionError, OSError):
                    # If we can't walk the directory, count it as 1 item
                    total_files += 1
        return total_files
    
    def _progress_callback(self, progress_data):
        """Callback for progress manager updates"""
        # Force a screen refresh to show progress
        try:
            self.file_manager.draw_status()
            self.file_manager.stdscr.refresh()
        except Exception as e:
            print(f"Warning: Progress callback display update failed: {e}")
    
    def _copy_directory_with_progress(self, source_dir, dest_dir, processed_files, total_files):
        """Copy directory recursively with fine-grained progress updates"""
        try:
            # Create destination directory
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Walk through source directory and copy files one by one
            for root, dirs, files in os.walk(source_dir):
                root_path = Path(root)
                
                # Calculate relative path from source directory
                rel_path = root_path.relative_to(source_dir)
                dest_root = dest_dir / rel_path
                
                # Create subdirectories
                dest_root.mkdir(parents=True, exist_ok=True)
                
                # Copy files in current directory
                for file_name in files:
                    source_file = root_path / file_name
                    dest_file = dest_root / file_name
                    
                    processed_files += 1
                    if total_files > 1:
                        # Show relative path for files in subdirectories
                        display_name = str(rel_path / file_name) if rel_path != Path('.') else file_name
                        self.progress_manager.update_progress(display_name, processed_files)
                    
                    try:
                        if source_file.is_symlink():
                            # Copy symbolic link
                            link_target = os.readlink(str(source_file))
                            dest_file.symlink_to(link_target)
                        else:
                            # Copy regular file
                            source_file.copy_to(dest_file, overwrite=True)
                    except Exception as e:
                        print(f"Error copying {source_file}: {e}")
                        if total_files > 1:
                            self.progress_manager.increment_errors()
                
                # Handle symbolic links to directories
                for dir_name in dirs:
                    source_subdir = root_path / dir_name
                    if source_subdir.is_symlink():
                        processed_files += 1
                        if total_files > 1:
                            display_name = str(rel_path / dir_name) if rel_path != Path('.') else dir_name
                            self.progress_manager.update_progress(f"Link: {display_name}", processed_files)
                        
                        dest_subdir = dest_root / dir_name
                        try:
                            link_target = os.readlink(str(source_subdir))
                            dest_subdir.symlink_to(link_target)
                        except Exception as e:
                            print(f"Error copying symlink {source_subdir}: {e}")
                            if total_files > 1:
                                self.progress_manager.increment_errors()
            
            return processed_files
            
        except Exception as e:
            print(f"Error copying directory {source_dir}: {e}")
            if total_files > 1:
                self.progress_manager.increment_errors()
            return processed_files
    
    def _move_directory_with_progress(self, source_dir, dest_dir, processed_files, total_files, is_cross_storage=False):
        """Move directory using copy + delete with fine-grained progress updates"""
        try:
            if is_cross_storage:
                # Cross-storage move: use copy_to then delete
                source_dir.copy_to(dest_dir, overwrite=True)
                
                # Count files for progress tracking
                dir_file_count = self._count_files_recursively([source_dir])
                processed_files += dir_file_count
                
                if total_files > 1:
                    self.progress_manager.update_progress(f"Copied: {source_dir.name}", processed_files)
                
                # Delete source directory
                if hasattr(source_dir._impl, 'rmtree'):
                    # S3 has optimized recursive delete
                    source_dir._impl.rmtree()
                else:
                    # Use standard recursive delete for local directories
                    self._delete_directory_with_progress(source_dir, 0, 1)
            else:
                # Same-storage move: first copy the directory with progress tracking
                processed_files = self._copy_directory_with_progress(
                    source_dir, dest_dir, processed_files, total_files
                )
                
                # Then remove the source directory
                if source_dir.is_dir():
                    # For directories, we need to delete recursively
                    # Use the existing delete method without progress tracking
                    self._delete_directory_with_progress(source_dir, 0, 1)
                else:
                    source_dir.unlink()
            
            return processed_files
            
        except Exception as e:
            print(f"Error moving directory {source_dir}: {e}")
            if total_files > 1:
                self.progress_manager.increment_errors()
            return processed_files
    
    def _delete_directory_with_progress(self, dir_path, processed_files, total_files):
        """Delete directory recursively with fine-grained progress updates"""
        try:
            # Check if this is an S3 path
            from tfm_s3 import S3PathImpl
            if isinstance(dir_path._impl, S3PathImpl):
                return self._delete_s3_directory_with_progress(dir_path, processed_files, total_files)
            
            # Walk through directory and delete files one by one (bottom-up for safety)
            for root, dirs, files in os.walk(dir_path, topdown=False):
                root_path = Path(root)
                
                # Delete files in current directory
                for file_name in files:
                    file_path = root_path / file_name
                    processed_files += 1
                    
                    if total_files > 1:
                        # Show relative path from the main directory being deleted
                        try:
                            rel_path = file_path.relative_to(dir_path)
                            display_name = str(rel_path)
                        except ValueError:
                            display_name = file_path.name
                        
                        self.progress_manager.update_progress(display_name, processed_files)
                    
                    try:
                        file_path.unlink()  # Remove file or symlink
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
                        if total_files > 1:
                            self.progress_manager.increment_errors()
                
                # Delete empty subdirectories (they should be empty now since we're going bottom-up)
                for dir_name in dirs:
                    subdir_path = root_path / dir_name
                    try:
                        # Only try to remove if it's empty or a symlink
                        if subdir_path.is_symlink():
                            # Count symlinks to directories as files for progress
                            processed_files += 1
                            if total_files > 1:
                                try:
                                    rel_path = subdir_path.relative_to(dir_path)
                                    display_name = f"Link: {rel_path}"
                                except ValueError:
                                    display_name = f"Link: {subdir_path.name}"
                                self.progress_manager.update_progress(display_name, processed_files)
                            subdir_path.unlink()
                        else:
                            # Try to remove empty directory (no progress update for empty dirs)
                            subdir_path.rmdir()
                    except OSError:
                        # Directory not empty or permission error - skip it
                        # The directory will be handled by shutil.rmtree fallback if needed
                        pass
                    except Exception as e:
                        print(f"Error deleting directory {subdir_path}: {e}")
                        if total_files > 1:
                            self.progress_manager.increment_errors()
            
            # Finally remove the main directory
            try:
                dir_path.rmdir()
            except OSError:
                # If directory is not empty, try to remove it using Path method
                # This shouldn't happen if our bottom-up deletion worked correctly
                try:
                    # For S3 paths, this will handle directory deletion properly
                    dir_path.rmdir()
                except Exception as e:
                    print(f"Warning: Could not remove directory {dir_path}: {e}")
            
            return processed_files
            
        except Exception as e:
            print(f"Error deleting directory {dir_path}: {e}")
    
    def _delete_s3_directory_with_progress(self, dir_path, processed_files, total_files):
        """Delete S3 directory recursively with fine-grained progress updates"""
        try:
            from tfm_s3 import S3PathImpl
            s3_impl = dir_path._impl
            
            # List all objects in the directory
            prefix = s3_impl._key.rstrip('/') + '/'
            
            # Use paginator to handle large directories
            paginator = s3_impl._client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=s3_impl._bucket,
                Prefix=prefix
            )
            
            objects_to_delete = []
            
            for page in page_iterator:
                for obj in page.get('Contents', []):
                    processed_files += 1
                    
                    if total_files > 1:
                        # Show relative path from the main directory being deleted
                        try:
                            rel_key = obj['Key'][len(prefix):]  # Remove the prefix
                            display_name = rel_key if rel_key else obj['Key']
                        except:
                            display_name = obj['Key']
                        
                        self.progress_manager.update_progress(display_name, processed_files)
                    
                    objects_to_delete.append({'Key': obj['Key']})
                    
                    # Delete in batches of 1000 (S3 limit)
                    if len(objects_to_delete) >= 1000:
                        try:
                            s3_impl._delete_objects_batch(objects_to_delete)
                        except Exception as e:
                            print(f"Error deleting S3 objects batch: {e}")
                            if total_files > 1:
                                self.progress_manager.increment_errors()
                        objects_to_delete = []
            
            # Delete remaining objects
            if objects_to_delete:
                try:
                    s3_impl._delete_objects_batch(objects_to_delete)
                except Exception as e:
                    print(f"Error deleting S3 objects batch: {e}")
                    if total_files > 1:
                        self.progress_manager.increment_errors()
            
            return processed_files
            
        except Exception as e:
            print(f"Error deleting S3 directory {dir_path}: {e}")
            if total_files > 1:
                self.progress_manager.increment_errors()
            return processed_files