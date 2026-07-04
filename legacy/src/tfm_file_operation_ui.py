#!/usr/bin/env python3
"""
TFM File Operation UI - Handles file operation UI interactions
"""

import os
from tfm_path import Path


class FileOperationUI:
    """Handles file operation UI interactions.
    
    This class provides the user interface layer for file operations,
    including confirmation dialogs, conflict resolution dialogs, and
    rename dialogs. It creates and starts FileOperationTask instances.
    
    Architecture (Post-Refactoring):
        FileOperationUI is part of a clean four-layer architecture:
        - Layer 1: FileListManager - File list management
        - Layer 2: FileOperationUI - UI interactions (this class)
        - Layer 3: FileOperationTask - Orchestration (state machine)
        - Layer 4: FileOperationExecutor - I/O operations
    
    Responsibilities:
        - Entry points for file operations (copy/move/delete)
        - UI dialog creation and display
        - Confirmation dialogs
        - Conflict resolution dialogs
        - Rename dialogs
        - Creating FileOperationTask instances
        - NO I/O operations (delegated to FileOperationExecutor)
    
    Task Usage:
        1. User initiates operation (copy/move/delete)
        2. FileOperationUI creates FileOperationTask with ui=self and executor
        3. Task is started via file_manager.start_task()
        4. Task manages workflow and calls back to UI for dialogs
        5. Task delegates I/O to FileOperationExecutor
        6. Task completes and cleans up
    
    Key Methods:
        - copy_selected_files(): Entry point for copy operation
        - move_selected_files(): Entry point for move operation
        - delete_selected_files(): Entry point for delete operation
        - show_confirmation_dialog(): Show confirmation dialog
        - show_conflict_dialog(): Show conflict resolution dialog
        - show_rename_dialog(): Show rename dialog
    
    See Also:
        - tfm_file_operation_task.py: FileOperationTask implementation
        - tfm_file_operation_executor.py: FileOperationExecutor implementation
        - tfm_file_list_manager.py: FileListManager implementation
        - doc/dev/TASK_FRAMEWORK_IMPLEMENTATION.md: Complete architecture documentation
    """
    
    def __init__(self, file_manager, file_list_manager):
        """Initialize file operations UI with file manager and file list manager
        
        Args:
            file_manager: FileManager instance for UI interactions and task management
            file_list_manager: FileListManager instance for file list operations
        """
        self.file_manager = file_manager
        self.file_list_manager = file_list_manager
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
        task = FileOperationTask(self.file_manager, self, self.file_manager.file_operations_executor)
        task.start_operation('copy', files_to_copy, destination_dir)
        self.file_manager.start_task(task)
    
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
        task = FileOperationTask(self.file_manager, self, self.file_manager.file_operations_executor)
        task.start_operation('move', files_to_move, destination_dir)
        self.file_manager.start_task(task)
    
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
        task = FileOperationTask(self.file_manager, self, self.file_manager.file_operations_executor)
        task.start_operation('delete', files_to_delete)
        self.file_manager.start_task(task)
    
    # UI Methods for FileOperationTask
    def show_confirmation_dialog(self, operation_type, files, destination, callback):
        """Show confirmation dialog for file operation.
        
        This method provides a centralized UI interaction for file operation
        confirmations. It builds an appropriate confirmation message and
        delegates to file_manager.show_confirmation().
        
        Args:
            operation_type: Type of operation ('copy', 'move', or 'delete')
            files: List of Path objects to operate on
            destination: Destination Path (for copy/move, None for delete)
            callback: Function to call with confirmation result (True/False)
        """
        # Build confirmation message
        if len(files) == 1:
            # Single file operation
            file_name = files[0].name
            if operation_type == 'copy':
                message = f"Copy '{file_name}' to {destination}?"
            elif operation_type == 'move':
                message = f"Move '{file_name}' to {destination}?"
            elif operation_type == 'delete':
                message = f"Delete '{file_name}'?"
            else:
                message = f"Confirm {operation_type} operation?"
        else:
            # Multiple file operation
            file_count = len(files)
            if operation_type == 'copy':
                message = f"Copy {file_count} files to {destination}?"
            elif operation_type == 'move':
                message = f"Move {file_count} files to {destination}?"
            elif operation_type == 'delete':
                message = f"Delete {file_count} files?"
            else:
                message = f"Confirm {operation_type} operation on {file_count} files?"
        
        # Show confirmation dialog
        self.file_manager.show_confirmation(message, callback)
    
    def show_conflict_dialog(self, source_file, dest_file, conflict_num, total_conflicts, callback):
        """Show conflict resolution dialog.
        
        This method provides a centralized UI interaction for file conflict
        resolution. It builds an appropriate conflict message and delegates
        to file_manager.show_dialog().
        
        Args:
            source_file: Source file Path
            dest_file: Destination file Path
            conflict_num: Current conflict number (1-based)
            total_conflicts: Total number of conflicts
            callback: Function to call with user's choice and apply_to_all flag
        """
        # Build conflict message
        message = f"File exists: {dest_file.name} ({conflict_num}/{total_conflicts})"
        
        # Build choices for conflict resolution
        choices = [
            {"text": "Overwrite", "key": "o", "value": "overwrite"},
            {"text": "Rename", "key": "r", "value": "rename"},
            {"text": "Skip", "key": "s", "value": "skip"}
        ]
        
        # Show conflict dialog with shift modifier enabled for apply-to-all
        self.file_manager.show_dialog(
            message,
            choices,
            callback,
            enable_shift_modifier=True
        )
    
    def show_rename_dialog(self, source_file, destination, callback, cancel_callback):
        """Show rename dialog.
        
        This method provides a centralized UI interaction for file renaming
        during conflict resolution. It sets up the QuickEditBar with the
        current filename and handles callbacks.
        
        Args:
            source_file: Source file Path to rename
            destination: Destination directory Path
            callback: Function to call with new name (receives source_file and new_name)
            cancel_callback: Function to call if cancelled
        """
        # Build prompt with current filename
        prompt = f"Rename '{source_file.name}' to: "
        
        # Define wrapper for confirmation callback
        def on_confirm(new_name: str):
            callback(source_file, new_name)
        
        # Show QuickEditBar with current filename as initial text
        self.file_manager.quick_edit_bar.show_status_line_input(
            prompt=prompt,
            initial_text=source_file.name,
            callback=on_confirm,
            cancel_callback=cancel_callback
        )
        
        # Mark UI as dirty to trigger redraw
        self.file_manager.mark_dirty()
