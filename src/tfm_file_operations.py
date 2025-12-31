#!/usr/bin/env python3
"""
TFM File Operations - Handles file system operations and file management
"""

import os
import stat
import fnmatch
import shutil
import threading
from tfm_path import Path
from tfm_progress_manager import ProgressManager, OperationType
from datetime import datetime


class FileOperations:
    """Handles file system operations and file management"""
    
    def __init__(self, config):
        self.config = config
        self.show_hidden = getattr(config, 'SHOW_HIDDEN_FILES', False)
        self.log_manager = None  # Will be set by FileManager if available
        # Use module-level getLogger - no need to check if log_manager exists
        from tfm_log_manager import getLogger
        self.logger = getLogger("FileOp")
    
    def refresh_files(self, pane_data):
        """Refresh the file list for specified pane"""
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
        """Toggle selection of current file/directory and optionally move cursor"""
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
        """Apply the current filter pattern to the specified pane"""
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


class FileOperationsUI:
    """Handles file operation UI interactions for the file manager
    
    This class provides the user interface layer for file operations (copy, move, delete).
    It uses a task-based architecture where operations are managed by FileOperationTask
    instances that handle state transitions, user confirmations, conflict resolution,
    and background execution.
    
    Architecture:
        FileOperationsUI creates and starts FileOperationTask instances for each operation.
        The task manages the complete workflow including:
        - User confirmation dialogs
        - Conflict detection and resolution
        - Rename handling
        - Background execution with progress tracking
        - Completion and cleanup
    
    Task Usage:
        1. User initiates operation (copy/move/delete)
        2. FileOperationsUI creates FileOperationTask
        3. Task is started via file_manager.start_task()
        4. Task manages all UI interactions and state transitions
        5. Task calls back to FileOperationsUI for actual file operations
        6. Task completes and cleans up
    
    Key Methods:
        - copy_selected_files(): Initiates copy operation via FileOperationTask
        - move_selected_files(): Initiates move operation via FileOperationTask
        - delete_selected_files(): Initiates delete operation via FileOperationTask
        - perform_copy_operation(): Executes copy in background thread (called by task)
        - perform_move_operation(): Executes move in background thread (called by task)
        - perform_delete_operation(): Executes delete in background thread (called by task)
    
    See Also:
        - tfm_file_operation_task.py: FileOperationTask implementation
        - tfm_base_task.py: BaseTask abstract class
        - doc/dev/TASK_FRAMEWORK_IMPLEMENTATION.md: Complete architecture documentation
    """
    
    def __init__(self, file_manager, file_operations):
        """Initialize file operations UI with file manager and file operations
        
        Args:
            file_manager: FileManager instance for UI interactions and task management
            file_operations: FileOperations instance for file system operations
        """
        self.file_manager = file_manager
        self.file_operations = file_operations
        self.log_manager = file_manager.log_manager
        self.progress_manager = file_manager.progress_manager
        self.cache_manager = file_manager.cache_manager
        self.config = file_manager.config
        # Initialize logger
        from tfm_log_manager import getLogger
        self.logger = getLogger("FileOp")
    
    def _validate_operation_capabilities(self, operation, source_paths, dest_path=None):
        """
        Validate if an operation is allowed based on storage capabilities.
        
        Args:
            operation: 'delete', 'move', or 'copy'
            source_paths: List of source Path objects
            dest_path: Optional destination Path object
            
        Returns:
            (is_valid, error_message) tuple
        """
        if operation == 'delete':
            # Check if all source paths support write operations (required for deletion)
            for path in source_paths:
                if not path.supports_write_operations():
                    return False, "Cannot delete files from read-only storage."
        
        elif operation == 'move':
            # Check if all source paths support write operations (required for deletion after move)
            for path in source_paths:
                if not path.supports_write_operations():
                    return False, "Cannot move files from read-only storage. Use copy instead."
            
            # Check if destination supports write operations (required for writing)
            if dest_path and not dest_path.supports_write_operations():
                return False, "Cannot move files to read-only storage."
        
        elif operation == 'copy':
            # Can copy FROM any storage, but destination must support write operations
            if dest_path and not dest_path.supports_write_operations():
                return False, "Cannot copy files to read-only storage."
            # Copying FROM read-only storage is OK (extraction)
        
        return True, None
    
    def _show_unsupported_operation_error(self, message):
        """Show error dialog for unsupported operations"""
        choices = [
            {"text": "OK", "key": "enter", "value": True}
        ]
        self.file_manager.show_dialog(message, choices, lambda _: None)
    
    def copy_selected_files(self):
        """Copy selected files to the opposite pane's directory
        
        This method initiates a copy operation using the task-based architecture.
        It creates a FileOperationTask and starts it via file_manager.start_task().
        The task handles all user interactions including confirmation, conflict
        resolution, and progress tracking.
        
        Workflow:
            1. Gather files to copy (selected files or current file)
            2. Validate operation capabilities (read-only storage checks)
            3. Create FileOperationTask with 'copy' operation
            4. Start task via file_manager.start_task()
            5. Task manages confirmation, conflicts, and execution
        
        The actual file copying is performed by perform_copy_operation() which
        is called by the task during the EXECUTING state.
        """
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
                focused_file = current_pane['files'][current_pane['focused_index']]
                files_to_copy.append(focused_file)
        
        if not files_to_copy:
            self.logger.info("No files to copy")
            return
        
        destination_dir = other_pane['path']
        
        # Validate operation capabilities - check BEFORE any other checks
        is_valid, error_msg = self._validate_operation_capabilities('copy', files_to_copy, destination_dir)
        if not is_valid:
            self._show_unsupported_operation_error(error_msg)
            return
        
        # Check if destination directory is writable (only for local paths)
        if destination_dir.get_scheme() == 'file' and not os.access(destination_dir, os.W_OK):
            self.logger.error(f"Permission denied: Cannot write to {destination_dir}")
            return
        
        # Create FileOperationTask and start the operation
        from tfm_file_operation_task import FileOperationTask
        task = FileOperationTask(self.file_manager, self)
        task.start_operation('copy', files_to_copy, destination_dir)
        self.file_manager.start_task(task)
    
    
    def perform_copy_operation(self, files_to_copy, destination_dir, overwrite=False, completion_callback=None):
        """Perform the actual copy operation with fine-grained progress tracking in a background thread
        
        This method is called by FileOperationTask during the EXECUTING state. It runs
        the copy operation in a background thread with progress tracking and cancellation
        support.
        
        Args:
            files_to_copy: List of Path objects to copy
            destination_dir: Destination directory Path
            overwrite: If True, overwrite existing files without prompting
            completion_callback: Optional callback function called when operation completes.
                                Receives (copied_count, error_count) as arguments.
                                If provided, suppresses the default summary logging.
        
        Threading:
            - Runs in background thread to keep UI responsive
            - Uses operation_in_progress flag to block user input
            - Uses operation_cancelled flag for cancellation
            - Updates progress via progress_manager
            - Triggers UI refresh via mark_dirty()
        
        Progress Tracking:
            - Shows "Preparing..." message during file counting
            - Updates progress for each file copied
            - Tracks errors separately
            - Shows completion summary
        
        Note: This method is called by FileOperationTask, not directly by user code.
        """
        # Set operation in progress flag to block user input
        self.file_manager.operation_in_progress = True
        self.file_manager.operation_cancelled = False
        
        # Show "Preparing..." message immediately
        self.progress_manager.start_operation(
            OperationType.COPY,
            1,
            f"Preparing to copy to {destination_dir.name}",
            self._progress_callback
        )
        
        # Start animation refresh thread so "Preparing" animates
        animation_stop_event = threading.Event()
        animation_thread = threading.Thread(
            target=self._animation_refresh_loop,
            args=(animation_stop_event,),
            daemon=True
        )
        animation_thread.start()
        
        # Run the copy operation in a background thread
        def copy_thread():
            # Count files in background thread so "Preparing" message displays
            total_individual_files = self._count_files_recursively(files_to_copy)
            
            # Update progress with correct total
            self.progress_manager.update_operation_total(
                total_individual_files if total_individual_files > 0 else 1,
                f"to {destination_dir.name}"
            )
            
            copied_count = 0
            error_count = 0
            processed_files = 0
            
            try:
                for source_file in files_to_copy:
                    # Check for cancellation
                    if self.file_manager.operation_cancelled:
                        self.logger.info("Copy operation cancelled by user")
                        break
                    
                    try:
                        dest_path = destination_dir / source_file.name
                        
                        # Skip if file exists and we're not overwriting
                        if dest_path.exists() and not overwrite:
                            # Still need to count skipped files for progress
                            if source_file.is_file() or source_file.is_symlink():
                                processed_files += 1
                                self.progress_manager.update_progress(f"Skipped: {source_file.name}", processed_files)
                            elif source_file.is_dir():
                                # Count files in skipped directory
                                skipped_count = self._count_files_recursively([source_file])
                                processed_files += skipped_count
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
                                processed_files = self._copy_directory_cross_storage_with_progress(
                                    source_file, dest_path, processed_files, total_individual_files, overwrite
                                )
                            
                            self.logger.info(f"Copied directory: {source_file.name}")
                        else:
                            # Copy single file with progress tracking
                            processed_files += 1
                            self.progress_manager.update_progress(source_file.name, processed_files)
                            
                            self._copy_file_with_progress(source_file, dest_path, overwrite)
                            self.logger.info(f"Copied file: {source_file.name}")
                        
                        copied_count += 1
                        
                    except PermissionError as e:
                        self.logger.error(f"Permission denied copying {source_file.name}: {e}")
                        error_count += 1
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                        elif source_file.is_dir():
                            processed_files += self._count_files_recursively([source_file])
                    except Exception as e:
                        self.logger.error(f"Error copying {source_file.name}: {e}")
                        error_count += 1
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if source_file.is_file() or source_file.is_symlink():
                            processed_files += 1
                        elif source_file.is_dir():
                            processed_files += self._count_files_recursively([source_file])
            
            finally:
                # Stop animation refresh thread
                animation_stop_event.set()
                
                # Finish progress tracking
                self.progress_manager.finish_operation()
                
                # Clear operation in progress flag
                self.file_manager.operation_in_progress = False
            
            # Invalidate cache for affected directories
            if copied_count > 0:
                self.cache_manager.invalidate_cache_for_copy_operation(files_to_copy, destination_dir)
            
            # Refresh both panes to show the copied files
            self.file_manager.refresh_files()
            self.file_manager.mark_dirty()
            
            # Clear selections after successful copy
            if copied_count > 0:
                current_pane = self.file_manager.get_current_pane()
                current_pane['selected_files'].clear()
            
            # Print completion message (unless callback will handle it)
            if not completion_callback:
                if self.file_manager.operation_cancelled:
                    self.logger.info(f"Copy cancelled: {copied_count} items copied before cancellation")
                elif error_count > 0:
                    self.logger.warning(f"Copy completed: {copied_count} items copied, {error_count} errors")
                elif copied_count > 0:
                    self.logger.info(f"Successfully copied {copied_count} items")
                else:
                    self.logger.info("No items copied")
            
            # Call completion callback if provided
            if completion_callback:
                completion_callback(copied_count, error_count)
        
        # Start the copy thread
        thread = threading.Thread(target=copy_thread, daemon=True)
        thread.start()
    
    def move_selected_files(self):
        """Move selected files to the opposite pane's directory
        
        This method initiates a move operation using the task-based architecture.
        It creates a FileOperationTask and starts it via file_manager.start_task().
        The task handles all user interactions including confirmation, conflict
        resolution, and progress tracking.
        
        Workflow:
            1. Gather files to move (selected files or current file)
            2. Validate operation capabilities (read-only storage checks)
            3. Check for cross-storage moves (requires copy+delete)
            4. Create FileOperationTask with 'move' operation
            5. Start task via file_manager.start_task()
            6. Task manages confirmation, conflicts, and execution
        
        The actual file moving is performed by perform_move_operation() which
        is called by the task during the EXECUTING state.
        
        Note: Cross-storage moves (e.g., local to S3) are implemented as
        copy followed by delete, which is handled transparently by the task.
        """
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
                focused_file = current_pane['files'][current_pane['focused_index']]
                files_to_move.append(focused_file)
        
        if not files_to_move:
            self.logger.info("No files to move")
            return
        
        destination_dir = other_pane['path']
        
        # Validate operation capabilities - check BEFORE any other checks
        is_valid, error_msg = self._validate_operation_capabilities('move', files_to_move, destination_dir)
        if not is_valid:
            self._show_unsupported_operation_error(error_msg)
            return
        
        # Check if destination directory is writable (only for local paths)
        if destination_dir.get_scheme() == 'file' and not os.access(destination_dir, os.W_OK):
            self.logger.error(f"Permission denied: Cannot write to {destination_dir}")
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
            self.logger.info(f"Cross-storage move: {'/'.join(set(source_names))} → {dest_name}")
        
        # Check if any files are being moved to the same directory
        same_dir_files = [f for f in files_to_move if f.parent == destination_dir]
        if same_dir_files:
            if len(same_dir_files) == len(files_to_move):
                self.logger.info("Cannot move files to the same directory")
                return
            else:
                # Remove files that are already in the destination directory
                files_to_move = [f for f in files_to_move if f.parent != destination_dir]
                self.logger.info(f"Skipping {len(same_dir_files)} files already in destination directory")
        
        # Create FileOperationTask and start the operation
        from tfm_file_operation_task import FileOperationTask
        task = FileOperationTask(self.file_manager, self)
        task.start_operation('move', files_to_move, destination_dir)
        self.file_manager.start_task(task)
    
    
    def perform_move_operation(self, files_to_move, destination_dir, overwrite=False, completion_callback=None):
        """Perform the actual move operation with fine-grained progress tracking in a background thread
        
        This method is called by FileOperationTask during the EXECUTING state. It runs
        the move operation in a background thread with progress tracking and cancellation
        support.
        
        Args:
            files_to_move: List of Path objects to move
            destination_dir: Destination directory Path
            overwrite: If True, overwrite existing files without prompting
            completion_callback: Optional callback function called when operation completes.
                                Receives (moved_count, error_count) as arguments.
                                If provided, suppresses the default summary logging.
        
        Threading:
            - Runs in background thread to keep UI responsive
            - Uses operation_in_progress flag to block user input
            - Uses operation_cancelled flag for cancellation
            - Updates progress via progress_manager
            - Triggers UI refresh via mark_dirty()
        
        Progress Tracking:
            - Shows "Preparing..." message during file counting
            - Updates progress for each file moved
            - Tracks errors separately
            - Shows completion summary
        
        Cross-Storage Moves:
            - Detects cross-storage moves (e.g., local to S3)
            - Implements as copy followed by delete
            - Handles both same-storage and cross-storage transparently
        
        Note: This method is called by FileOperationTask, not directly by user code.
        """
        # Set operation in progress flag to block user input
        self.file_manager.operation_in_progress = True
        self.file_manager.operation_cancelled = False
        
        # Show "Preparing..." message immediately
        self.progress_manager.start_operation(
            OperationType.MOVE,
            1,
            f"Preparing to move to {destination_dir.name}",
            self._progress_callback
        )
        
        # Start animation refresh thread
        animation_stop_event = threading.Event()
        animation_thread = threading.Thread(
            target=self._animation_refresh_loop,
            args=(animation_stop_event,),
            daemon=True
        )
        animation_thread.start()
        
        # Run the move operation in a background thread
        def move_thread():
            # Count files in background thread
            total_individual_files = self._count_files_recursively(files_to_move)
            
            # Update progress with correct total
            self.progress_manager.update_operation_total(
                total_individual_files if total_individual_files > 0 else 1,
                f"to {destination_dir.name}"
            )
            
            moved_count = 0
            error_count = 0
            processed_files = 0
            
            try:
                for source_file in files_to_move:
                    # Check for cancellation
                    if self.file_manager.operation_cancelled:
                        self.logger.info("Move operation cancelled by user")
                        break
                    
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
                            self.logger.info(f"Moved symbolic link: {source_file.name}")
                        elif source_file.is_dir():
                            # For directories, we need to track individual files being moved
                            processed_files = self._move_directory_with_progress(
                                source_file, dest_path, processed_files, total_individual_files, is_cross_storage
                            )
                            self.logger.info(f"Moved directory: {source_file.name}")
                        else:
                            # Move single file
                            processed_files += 1
                            if total_individual_files > 1:
                                self.progress_manager.update_progress(source_file.name, processed_files)
                            
                            if is_cross_storage:
                                # Cross-storage move: copy then delete
                                source_file.copy_to(dest_path, overwrite=overwrite)
                                source_file.unlink()
                                self.logger.info(f"Moved file (cross-storage): {source_file.name}")
                            else:
                                # Same-storage move: use rename
                                source_file.rename(dest_path)
                                self.logger.info(f"Moved file: {source_file.name}")
                        
                        moved_count += 1
                        
                    except PermissionError as e:
                        self.logger.error(f"Permission denied moving {source_file.name}: {e}")
                        error_count += 1
                        if total_individual_files > 1:
                            self.progress_manager.increment_errors()
                            # Still count the file for progress tracking
                            if source_file.is_file() or source_file.is_symlink():
                                processed_files += 1
                            elif source_file.is_dir():
                                processed_files += self._count_files_recursively([source_file])
                    except Exception as e:
                        self.logger.error(f"Error moving {source_file.name}: {e}")
                        error_count += 1
                        if total_individual_files > 1:
                            self.progress_manager.increment_errors()
                            # Still count the file for progress tracking
                            if source_file.is_file() or source_file.is_symlink():
                                processed_files += 1
                            elif source_file.is_dir():
                                processed_files += self._count_files_recursively([source_file])
            
            finally:
                # Stop animation refresh thread
                animation_stop_event.set()
                
                # Always finish progress tracking
                self.progress_manager.finish_operation()
                
                # Clear operation in progress flag
                self.file_manager.operation_in_progress = False
                
                # Invalidate cache for affected directories
                if moved_count > 0:
                    self.cache_manager.invalidate_cache_for_move_operation(files_to_move, destination_dir)
                
                # Refresh both panes to show the moved files
                self.file_manager.refresh_files()
                self.file_manager.mark_dirty()
                
                # Clear selections after successful move
                if moved_count > 0:
                    current_pane = self.file_manager.get_current_pane()
                    current_pane['selected_files'].clear()
                
                # Print completion message (unless callback will handle it)
                if not completion_callback:
                    if self.file_manager.operation_cancelled:
                        self.logger.info(f"Move cancelled: {moved_count} items moved before cancellation")
                    elif error_count > 0:
                        self.logger.warning(f"Move completed: {moved_count} items moved, {error_count} errors")
                    elif moved_count > 0:
                        self.logger.info(f"Successfully moved {moved_count} items")
                    else:
                        self.logger.info("No items moved")
                
                # Call completion callback if provided
                if completion_callback:
                    completion_callback(moved_count, error_count)
        
        # Start the thread
        thread = threading.Thread(target=move_thread, daemon=True)
        thread.start()
    
    def delete_selected_files(self):
        """Delete selected files or current file with confirmation
        
        This method initiates a delete operation using the task-based architecture.
        It creates a FileOperationTask and starts it via file_manager.start_task().
        The task handles user confirmation and progress tracking.
        
        Workflow:
            1. Gather files to delete (selected files or current file)
            2. Validate operation capabilities (read-only storage checks)
            3. Create FileOperationTask with 'delete' operation
            4. Start task via file_manager.start_task()
            5. Task manages confirmation and execution
        
        The actual file deletion is performed by perform_delete_operation() which
        is called by the task during the EXECUTING state.
        
        Note: Delete operations require confirmation based on the CONFIRM_DELETE
        configuration setting. The task handles this automatically.
        """
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
                focused_file = current_pane['files'][current_pane['focused_index']]
                files_to_delete.append(focused_file)
        
        if not files_to_delete:
            self.logger.info("No files to delete")
            return
        
        # Validate operation capabilities - check BEFORE confirmation dialog
        is_valid, error_msg = self._validate_operation_capabilities('delete', files_to_delete)
        if not is_valid:
            self._show_unsupported_operation_error(error_msg)
            return
        
        # Create FileOperationTask and start the operation
        from tfm_file_operation_task import FileOperationTask
        task = FileOperationTask(self.file_manager, self)
        task.start_operation('delete', files_to_delete)
        self.file_manager.start_task(task)
    
    def perform_delete_operation(self, files_to_delete):
        """Perform the actual delete operation with fine-grained progress tracking in a background thread
        
        This method is called by FileOperationTask during the EXECUTING state. It runs
        the delete operation in a background thread with progress tracking and cancellation
        support.
        
        Args:
            files_to_delete: List of Path objects to delete
        
        Threading:
            - Runs in background thread to keep UI responsive
            - Uses operation_in_progress flag to block user input
            - Uses operation_cancelled flag for cancellation
            - Updates progress via progress_manager
            - Triggers UI refresh via mark_dirty()
        
        Progress Tracking:
            - Shows "Preparing..." message during file counting
            - Updates progress for each file deleted
            - Tracks errors separately
            - Shows completion summary
        
        Note: This method is called by FileOperationTask, not directly by user code.
        """
        # Set operation in progress flag to block user input
        self.file_manager.operation_in_progress = True
        self.file_manager.operation_cancelled = False
        
        # Start operation without description
        self.progress_manager.start_operation(
            OperationType.DELETE,
            1,
            "",
            self._progress_callback
        )
        
        # Start animation refresh thread
        animation_stop_event = threading.Event()
        animation_thread = threading.Thread(
            target=self._animation_refresh_loop,
            args=(animation_stop_event,),
            daemon=True
        )
        animation_thread.start()
        
        # Run the delete operation in a background thread
        def delete_thread():
            # Count files in background thread
            total_individual_files = self._count_files_recursively(files_to_delete)
            
            # Update progress with correct total
            self.progress_manager.update_operation_total(
                total_individual_files if total_individual_files > 0 else 1,
                ""
            )
            
            deleted_count = 0
            error_count = 0
            processed_files = 0
            
            try:
                
                for file_path in files_to_delete:
                    # Check for cancellation
                    if self.file_manager.operation_cancelled:
                        self.logger.info("Delete operation cancelled by user")
                        break
                    
                    try:
                        if file_path.is_symlink():
                            # Delete symbolic link (not its target)
                            processed_files += 1
                            self.progress_manager.update_progress(f"Link: {file_path.name}", processed_files)
                            
                            file_path.unlink()
                            self.logger.info(f"Deleted symbolic link: {file_path.name}")
                        elif file_path.is_dir():
                            # Delete directory recursively with progress tracking
                            processed_files = self._delete_directory_with_progress(
                                file_path, processed_files, total_individual_files
                            )
                            self.logger.info(f"Deleted directory: {file_path.name}")
                        else:
                            # Delete single file
                            processed_files += 1
                            self.progress_manager.update_progress(file_path.name, processed_files)
                            
                            file_path.unlink()
                            self.logger.info(f"Deleted file: {file_path.name}")
                        
                        deleted_count += 1
                        
                    except PermissionError as e:
                        self.logger.error(f"Permission denied deleting {file_path.name}: {e}")
                        error_count += 1
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if file_path.is_file() or file_path.is_symlink():
                            processed_files += 1
                        elif file_path.is_dir():
                            processed_files += self._count_files_recursively([file_path])
                    except FileNotFoundError:
                        self.logger.warning(f"File not found (already deleted?): {file_path.name}")
                        error_count += 1
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if file_path.is_file() or file_path.is_symlink():
                            processed_files += 1
                        elif file_path.is_dir():
                            processed_files += self._count_files_recursively([file_path])
                    except Exception as e:
                        self.logger.error(f"Error deleting {file_path.name}: {e}")
                        error_count += 1
                        self.progress_manager.increment_errors()
                        # Still count the file for progress tracking
                        if file_path.is_file() or file_path.is_symlink():
                            processed_files += 1
                        elif file_path.is_dir():
                            processed_files += self._count_files_recursively([file_path])
            
            finally:
                # Stop animation refresh thread
                animation_stop_event.set()
                
                # Always finish progress tracking
                self.progress_manager.finish_operation()
                
                # Clear operation in progress flag
                self.file_manager.operation_in_progress = False
                
                # Invalidate cache for affected directories
                if deleted_count > 0:
                    self.cache_manager.invalidate_cache_for_delete_operation(files_to_delete)
                
                # Refresh current pane to show the changes
                self.file_manager.refresh_files(self.file_manager.get_current_pane())
                self.file_manager.mark_dirty()
                
                # Clear selections after delete operation
                current_pane = self.file_manager.get_current_pane()
                current_pane['selected_files'].clear()
                
                # Adjust cursor position if it's now out of bounds
                if current_pane['focused_index'] >= len(current_pane['files']):
                    current_pane['focused_index'] = max(0, len(current_pane['files']) - 1)
                
                # Print completion message
                if self.file_manager.operation_cancelled:
                    self.logger.info(f"Delete cancelled: {deleted_count} files deleted before cancellation")
                elif error_count > 0:
                    self.logger.warning(f"Delete completed: {deleted_count} files deleted, {error_count} errors")
                elif deleted_count > 0:
                    self.logger.info(f"Successfully deleted {deleted_count} files")
        
        # Start the thread
        thread = threading.Thread(target=delete_thread, daemon=True)
        thread.start()
    
    # Helper methods
    def _count_files_recursively(self, paths):
        """Count total number of individual files in the given paths (including files in directories)"""
        total_files = 0
        for path in paths:
            if path.is_file() or path.is_symlink():
                total_files += 1
            elif path.is_dir():
                try:
                    # Check if this is an archive path
                    if path.get_scheme() == 'archive':
                        # For archive paths, use iterdir recursively
                        for item in path.rglob('*'):
                            if item.is_file():
                                total_files += 1
                    else:
                        # For local/S3 paths, use os.walk
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
        """Callback for progress manager updates
        
        Note: This is called from background threads. We do NOT call curses functions
        here because curses is not thread-safe. Instead, we set a flag that tells the
        main loop to redraw on its next iteration.
        """
        # Set flag to trigger redraw in main loop (thread-safe)
        # This is safe because it's just setting a boolean flag
        self.file_manager.mark_dirty()
    
    def _animation_refresh_loop(self, stop_event):
        """Background loop to refresh animation periodically
        
        Args:
            stop_event: Threading event to signal when to stop
        """
        import time
        
        while not stop_event.is_set():
            # Refresh animation to keep spinner moving
            self.progress_manager.refresh_animation()
            
            # Sleep for a short time (100ms) to keep animation smooth
            # This is independent of progress updates
            time.sleep(0.1)
    
    def _copy_file_with_progress(self, source_file, dest_file, overwrite=False):
        """Copy a single file with byte-level progress tracking"""
        try:
            # Get file size
            file_size = source_file.stat().st_size
            
            # For files smaller than 10MB, use simple copy
            if file_size < 10 * 1024 * 1024:
                source_file.copy_to(dest_file, overwrite=overwrite)
                return
            
            # For large files, copy with byte-level progress and cancellation support
            chunk_size = 1024 * 1024  # 1MB chunks
            bytes_copied = 0
            
            # Handle different storage combinations
            source_scheme = source_file.get_scheme()
            dest_scheme = dest_file.get_scheme()
            
            # Create destination directory if needed (for local destinations)
            if dest_scheme == 'file':
                dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Open source for reading
            if source_scheme == 'file':
                src = open(str(source_file), 'rb')
            elif source_scheme == 's3':
                # For S3, get the streaming body
                import boto3
                from botocore.exceptions import ClientError
                s3_client = boto3.client('s3')
                # Parse S3 URI
                s3_uri = str(source_file)
                if s3_uri.startswith('s3://'):
                    path_part = s3_uri[5:]
                    if '/' in path_part:
                        bucket, key = path_part.split('/', 1)
                    else:
                        raise ValueError(f"Invalid S3 URI: {s3_uri}")
                    response = s3_client.get_object(Bucket=bucket, Key=key)
                    src = response['Body']
                else:
                    raise ValueError(f"Invalid S3 URI: {s3_uri}")
            elif source_scheme == 'archive':
                # For archive files, use the open method which returns a file-like object
                src = source_file.open('rb')
            else:
                # Fallback to simple copy for other schemes
                source_file.copy_to(dest_file, overwrite=overwrite)
                return
            
            # Open destination for writing
            if dest_scheme == 'file':
                dst = open(str(dest_file), 'wb')
            elif dest_scheme == 's3':
                # For S3 destination, we need to buffer in memory or use multipart upload
                # For now, fall back to simple copy
                src.close()
                source_file.copy_to(dest_file, overwrite=overwrite)
                return
            else:
                src.close()
                source_file.copy_to(dest_file, overwrite=overwrite)
                return
            
            # Copy with progress tracking and cancellation support
            try:
                while True:
                    # Check for cancellation
                    if self.file_manager.operation_cancelled:
                        # Close files and remove partial copy
                        dst.close()
                        src.close()
                        try:
                            dest_file.unlink()
                        except Exception:
                            pass
                        return
                    
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    bytes_copied += len(chunk)
                    
                    # Update progress with bytes copied and total
                    self.progress_manager.update_file_byte_progress(bytes_copied, file_size)
            finally:
                dst.close()
                src.close()
            
            # Copy file metadata (only for local to local)
            if source_scheme == 'file' and dest_scheme == 'file':
                shutil.copystat(str(source_file), str(dest_file))
            
        except Exception as e:
            raise e
    
    def _copy_directory_with_progress(self, source_dir, dest_dir, processed_files, total_files):
        """Copy directory recursively with fine-grained progress updates"""
        try:
            # Create destination directory
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if source is an archive path
            if source_dir.get_scheme() == 'archive':
                # For archive paths, use rglob to iterate through all files
                for item in source_dir.rglob('*'):
                    # Check for cancellation
                    if self.file_manager.operation_cancelled:
                        return processed_files
                    
                    if item.is_file():
                        # Calculate relative path
                        rel_path = item.relative_to(source_dir)
                        dest_file = dest_dir / rel_path
                        
                        # Create parent directory if needed
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        processed_files += 1
                        self.progress_manager.update_progress(str(rel_path), processed_files)
                        
                        try:
                            # Copy file with byte-level progress for large files
                            self._copy_file_with_progress(item, dest_file, overwrite=True)
                        except Exception as e:
                            self.logger.error(f"Error copying {item}: {e}")
                            self.progress_manager.increment_errors()
                
                return processed_files
            
            # For non-archive paths, use os.walk
            for root, dirs, files in os.walk(source_dir):
                # Check for cancellation
                if self.file_manager.operation_cancelled:
                    return processed_files
                
                root_path = Path(root)
                
                # Calculate relative path from source directory
                rel_path = root_path.relative_to(source_dir)
                dest_root = dest_dir / rel_path
                
                # Create subdirectories
                dest_root.mkdir(parents=True, exist_ok=True)
                
                # Copy files in current directory
                for file_name in files:
                    # Check for cancellation
                    if self.file_manager.operation_cancelled:
                        return processed_files
                    
                    source_file = root_path / file_name
                    dest_file = dest_root / file_name
                    
                    processed_files += 1
                    # Show relative path for files in subdirectories
                    display_name = str(rel_path / file_name) if rel_path != Path('.') else file_name
                    self.progress_manager.update_progress(display_name, processed_files)
                    
                    try:
                        if source_file.is_symlink():
                            # Copy symbolic link
                            link_target = os.readlink(str(source_file))
                            dest_file.symlink_to(link_target)
                        else:
                            # Copy regular file with byte-level progress for large files
                            self._copy_file_with_progress(source_file, dest_file, overwrite=True)
                    except Exception as e:
                        self.logger.error(f"Error copying {source_file}: {e}")
                        self.progress_manager.increment_errors()
                
                # Handle symbolic links to directories
                for dir_name in dirs:
                    source_subdir = root_path / dir_name
                    if source_subdir.is_symlink():
                        processed_files += 1
                        display_name = str(rel_path / dir_name) if rel_path != Path('.') else dir_name
                        self.progress_manager.update_progress(f"Link: {display_name}", processed_files)
                        
                        dest_subdir = dest_root / dir_name
                        try:
                            link_target = os.readlink(str(source_subdir))
                            dest_subdir.symlink_to(link_target)
                        except Exception as e:
                            self.logger.error(f"Error copying symlink {source_subdir}: {e}")
                            self.progress_manager.increment_errors()
            
            return processed_files
            
        except Exception as e:
            self.logger.error(f"Error copying directory {source_dir}: {e}")
            self.progress_manager.increment_errors()
            return processed_files
    
    def _copy_directory_cross_storage_with_progress(self, source_dir, dest_dir, processed_files, total_files, overwrite=False):
        """Copy directory across storage systems with fine-grained progress updates"""
        try:
            # For cross-storage, we need to recursively copy files
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Get all files in the source directory recursively
            for item in source_dir.rglob('*'):
                # Check for cancellation
                if self.file_manager.operation_cancelled:
                    return processed_files
                
                if item.is_file():
                    # Calculate relative path
                    rel_path = item.relative_to(source_dir)
                    dest_item = dest_dir / rel_path
                    
                    # Create parent directory if needed
                    dest_item.parent.mkdir(parents=True, exist_ok=True)
                    
                    processed_files += 1
                    self.progress_manager.update_progress(str(rel_path), processed_files)
                    
                    try:
                        # Use _copy_file_with_progress for byte-level progress and cancellation support
                        self._copy_file_with_progress(item, dest_item, overwrite=overwrite)
                    except Exception as e:
                        self.logger.error(f"Error copying {item}: {e}")
                        self.progress_manager.increment_errors()
            
            return processed_files
            
        except Exception as e:
            self.logger.error(f"Error copying directory {source_dir}: {e}")
            self.progress_manager.increment_errors()
            return processed_files
    
    def _move_directory_with_progress(self, source_dir, dest_dir, processed_files, total_files, is_cross_storage=False):
        """Move directory using copy + delete with fine-grained progress updates"""
        try:
            # Check for cancellation
            if self.file_manager.operation_cancelled:
                return processed_files
            
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
            self.logger.error(f"Error moving directory {source_dir}: {e}")
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
                # Check for cancellation
                if self.file_manager.operation_cancelled:
                    return processed_files
                
                root_path = Path(root)
                
                # Delete files in current directory
                for file_name in files:
                    # Check for cancellation
                    if self.file_manager.operation_cancelled:
                        return processed_files
                    file_path = root_path / file_name
                    processed_files += 1
                    
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
                        self.logger.error(f"Error deleting {file_path}: {e}")
                        self.progress_manager.increment_errors()
                
                # Delete empty subdirectories (they should be empty now since we're going bottom-up)
                for dir_name in dirs:
                    subdir_path = root_path / dir_name
                    try:
                        # Only try to remove if it's empty or a symlink
                        if subdir_path.is_symlink():
                            # Count symlinks to directories as files for progress
                            processed_files += 1
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
                        self.logger.error(f"Error deleting directory {subdir_path}: {e}")
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
                    self.logger.warning(f"Warning: Could not remove directory {dir_path}: {e}")
            
            return processed_files
            
        except Exception as e:
            self.logger.error(f"Error deleting directory {dir_path}: {e}")
    
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
                # Check for cancellation
                if self.file_manager.operation_cancelled:
                    return processed_files
                
                for obj in page.get('Contents', []):
                    # Check for cancellation
                    if self.file_manager.operation_cancelled:
                        return processed_files
                    
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
                            self.logger.error(f"Error deleting S3 objects batch: {e}")
                            if total_files > 1:
                                self.progress_manager.increment_errors()
                        objects_to_delete = []
            
            # Delete remaining objects
            if objects_to_delete:
                try:
                    s3_impl._delete_objects_batch(objects_to_delete)
                except Exception as e:
                    self.logger.error(f"Error deleting S3 objects batch: {e}")
                    if total_files > 1:
                        self.progress_manager.increment_errors()
            
            return processed_files
            
        except Exception as e:
            self.logger.error(f"Error deleting S3 directory {dir_path}: {e}")
            if total_files > 1:
                self.progress_manager.increment_errors()
            return processed_files
    
    
    def _perform_single_copy(self, source_file, dest_path, overwrite=False, suppress_log=False):
        """Perform copy operation for a single file
        
        Args:
            suppress_log: If True, suppresses the default log message (caller will log instead)
        """
        try:
            is_directory = source_file.is_dir()
            
            if is_directory:
                # Copy directory recursively
                if dest_path.exists() and overwrite:
                    if dest_path.is_dir():
                        pass  # Let copy_to handle it
                    else:
                        dest_path.unlink()
                
                source_file.copy_to(dest_path, overwrite=overwrite)
            else:
                # Copy single file
                source_file.copy_to(dest_path, overwrite=overwrite)
            
            if not suppress_log:
                action = "Overwrote" if overwrite else "Copied"
                item_type = "directory" if is_directory else "file"
                self.logger.info(f"{action} {item_type}: {source_file.name}")
            
            # Invalidate cache
            self.cache_manager.invalidate_cache_for_copy_operation([source_file], dest_path.parent)
            
            # Refresh both panes
            self.file_manager.refresh_files()
            self.file_manager.mark_dirty()
            
            # Clear selections
            current_pane = self.file_manager.get_current_pane()
            current_pane['selected_files'].clear()
            
        except Exception as e:
            self.logger.error(f"Error copying {source_file.name}: {e}")
    
    def _perform_single_move(self, source_file, dest_path, overwrite=False, suppress_log=False):
        """Perform move operation for a single file
        
        Args:
            suppress_log: If True, suppresses the default log message (caller will log instead)
        """
        try:
            is_directory = source_file.is_dir()
            
            # Remove destination if it exists and we're overwriting
            if dest_path.exists() and overwrite:
                if dest_path.is_dir():
                    self._delete_directory_with_progress(dest_path, 0, 1)
                else:
                    dest_path.unlink()
            
            # Determine if this is a cross-storage move
            source_scheme = source_file.get_scheme()
            dest_scheme = dest_path.parent.get_scheme()
            is_cross_storage = source_scheme != dest_scheme
            
            # Move the file/directory
            if is_directory:
                if is_cross_storage:
                    source_file.copy_to(dest_path, overwrite=overwrite)
                    if hasattr(source_file._impl, 'rmtree'):
                        source_file._impl.rmtree()
                    else:
                        self._delete_directory_with_progress(source_file, 0, 1)
                else:
                    source_file.copy_to(dest_path, overwrite=overwrite)
                    self._delete_directory_with_progress(source_file, 0, 1)
            else:
                if is_cross_storage:
                    source_file.copy_to(dest_path, overwrite=overwrite)
                    source_file.unlink()
                else:
                    source_file.rename(dest_path)
            
            if not suppress_log:
                action = "Overwrote" if overwrite else "Moved"
                item_type = "directory" if is_directory else "file"
                self.logger.info(f"{action} {item_type}: {source_file.name}")
            
            # Invalidate cache
            self.cache_manager.invalidate_cache_for_move_operation([source_file], dest_path.parent)
            
            # Refresh both panes
            self.file_manager.refresh_files()
            self.file_manager.mark_dirty()
            
            # Clear selections
            current_pane = self.file_manager.get_current_pane()
            current_pane['selected_files'].clear()
            
        except Exception as e:
            self.logger.error(f"Error moving {source_file.name}: {e}")