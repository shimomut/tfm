"""Task implementation for file operations (copy, move, delete).

This module provides the FileOperationTask class, which implements the task
framework for file operations. It manages the complete lifecycle of file
operations including confirmation, conflict detection, conflict resolution,
execution, and completion.

The task uses a state machine pattern to coordinate:
- User confirmations
- Conflict detection and resolution
- Background thread execution
- Progress tracking
- Error handling
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tfm_base_task import BaseTask
from tfm_log_manager import getLogger


class State(Enum):
    """States for file operation task lifecycle.
    
    State transitions:
        IDLE → CONFIRMING → CHECKING_CONFLICTS → RESOLVING_CONFLICT → EXECUTING → COMPLETED → IDLE
    
    States:
        IDLE: No operation in progress
        CONFIRMING: Waiting for user confirmation
        CHECKING_CONFLICTS: Detecting file conflicts
        RESOLVING_CONFLICT: User resolving conflicts
        EXECUTING: Operation executing in background thread
        COMPLETED: Operation finished, preparing to return to IDLE
    """
    IDLE = "idle"
    CONFIRMING = "confirming"
    CHECKING_CONFLICTS = "checking_conflicts"
    RESOLVING_CONFLICT = "resolving_conflict"
    EXECUTING = "executing"
    COMPLETED = "completed"


@dataclass
class OperationContext:
    """Context for a file operation.
    
    This dataclass holds all state for an ongoing file operation, ensuring
    that all operation state is self-contained and not scattered across
    multiple objects.
    
    Attributes:
        operation_type: Type of operation ('copy', 'move', 'delete')
        files: List of source files to operate on
        destination: Destination path (for copy/move, None for delete)
        conflicts: List of (source, dest) path pairs that conflict
        current_conflict_index: Index of conflict currently being resolved
        results: Dictionary tracking operation results by category
        options: Dictionary of user choices for batch operations
    """
    operation_type: str
    files: List[Path]
    destination: Optional[Path] = None
    conflicts: List[Tuple[Path, Path]] = field(default_factory=list)
    current_conflict_index: int = 0
    results: Dict[str, List] = field(default_factory=lambda: {
        'success': [],
        'skipped': [],
        'errors': []
    })
    options: Dict[str, bool] = field(default_factory=lambda: {
        'overwrite_all': False,
        'skip_all': False,
        'rename_all': False
    })


class FileOperationTask(BaseTask):
    """Task for file operations (copy, move, delete).
    
    This class implements the task framework for file operations, managing
    the complete lifecycle from confirmation through execution to completion.
    
    The task coordinates:
    - User confirmations (if configured)
    - Conflict detection for copy/move operations
    - Conflict resolution (overwrite, rename, skip)
    - Background thread execution via FileOperationExecutor
    - Progress tracking and error handling
    - Operation completion and cleanup
    
    Architecture:
        The task delegates responsibilities to specialized components:
        - UI interactions → FileOperationUI (via self.ui)
        - I/O operations → FileOperationExecutor (via self.executor)
        - State machine logic → FileOperationTask (this class)
    
    Example usage:
        task = FileOperationTask(file_manager, ui, executor)
        task.start_operation('copy', files, destination)
        file_manager.start_task(task)
    """
    
    def __init__(self, file_manager, ui, executor=None):
        """Initialize file operation task.
        
        Args:
            file_manager: Reference to FileManager for task management
            ui: Reference to FileOperationUI for UI interactions
            executor: Reference to FileOperationExecutor for I/O operations
                     (optional, primarily for testing state machine without I/O)
        """
        super().__init__(file_manager, logger_name="FileOp")
        self.ui = ui
        self.executor = executor
        self.state = State.IDLE
        self.context: Optional[OperationContext] = None
    
    def start(self):
        """Start the task (called by FileManager).
        
        Note: The task is actually started via start_operation() which is
        called by FileOperationUI. This method exists to satisfy the
        BaseTask interface but doesn't need to do anything.
        """
        pass
    
    def cancel(self):
        """Cancel the task.
        
        Transitions the task to IDLE state, clears the operation context,
        and notifies FileManager that the task is complete.
        """
        if self.is_active():
            # Set cancellation flag if operation is executing
            if self.state == State.EXECUTING:
                self.request_cancellation()
                self.logger.info("Cancellation requested during execution")
                # Don't clear context yet - let _complete_operation handle it
                # when the executor finishes
            else:
                # For non-executing states, we can clean up immediately
                self._transition_to_state(State.IDLE)
                self.context = None
                self.logger.info("Task cancelled")
                self.file_manager._clear_task()
    
    def is_active(self) -> bool:
        """Check if task is active.
        
        Returns:
            True if task is not in IDLE or COMPLETED state, False otherwise
        """
        return self.state not in (State.IDLE, State.COMPLETED)
    
    def get_state(self) -> str:
        """Get current state.
        
        Returns:
            String representation of current state
        """
        return self.state.value
    
    def start_operation(self, operation_type: str, files: List[Path], destination: Optional[Path] = None):
        """Start a new file operation.
        
        This is the main entry point for starting a file operation. It creates
        the operation context and begins the state machine workflow.
        
        Args:
            operation_type: Type of operation ('copy', 'move', or 'delete')
            files: List of Path objects to operate on
            destination: Destination Path (required for copy/move, None for delete)
        
        Raises:
            ValueError: If operation_type is invalid or destination is missing for copy/move
        """
        # Validate operation type
        valid_operations = ('copy', 'move', 'delete')
        if operation_type not in valid_operations:
            raise ValueError(f"Invalid operation type: {operation_type}. Must be one of {valid_operations}")
        
        # Validate destination for copy/move
        if operation_type in ('copy', 'move') and destination is None:
            raise ValueError(f"Destination required for {operation_type} operation")
        
        # Create operation context
        self.context = OperationContext(
            operation_type=operation_type,
            files=files,
            destination=destination
        )
        
        self.logger.info(f"Starting {operation_type} operation with {len(files)} file(s)")
        
        # Check if confirmation is required based on configuration
        config_attr = f'CONFIRM_{operation_type.upper()}'
        confirm_required = getattr(self.ui.config, config_attr)
        
        if confirm_required:
            # Transition to CONFIRMING state and show confirmation dialog
            self._transition_to_state(State.CONFIRMING)
            
            # Show confirmation dialog via UI
            self.ui.show_confirmation_dialog(
                operation_type,
                files,
                destination,
                self.on_confirmed
            )
        else:
            # Skip confirmation and proceed directly to conflict checking
            self.logger.info(f"{operation_type.capitalize()} confirmation disabled, proceeding directly")
            self._transition_to_state(State.CHECKING_CONFLICTS)
            self._check_conflicts()
    
    def on_confirmed(self, confirmed: bool):
        """Handle confirmation response.
        
        Called when user responds to confirmation dialog.
        
        Args:
            confirmed: True if user confirmed, False if cancelled
        """
        if not self.context:
            self.logger.error("on_confirmed called with no operation context")
            return
        
        if confirmed:
            # User confirmed the operation, proceed to conflict checking
            self.logger.info(f"{self.context.operation_type.capitalize()} operation confirmed")
            self._transition_to_state(State.CHECKING_CONFLICTS)
            self._check_conflicts()
        else:
            # User cancelled the operation
            self.logger.info(f"{self.context.operation_type.capitalize()} operation cancelled by user")
            self._transition_to_state(State.IDLE)
            self.context = None
            self.file_manager._clear_task()
    
    def on_conflict_resolved(self, choice: str, apply_to_all: bool = False):
        """Handle conflict resolution choice.
        
        Called when user makes a choice for resolving a file conflict.
        Processes the choice and either continues to the next conflict or
        shows a rename dialog.
        
        Args:
            choice: User's choice ('overwrite', 'rename', 'skip', or None for cancel)
            apply_to_all: If True, apply choice to all remaining conflicts
        """
        if not self.context:
            self.logger.error("on_conflict_resolved called with no operation context")
            return
        
        # Handle cancellation (ESC key pressed)
        if choice is None:
            self.logger.info(f"{self.context.operation_type.capitalize()} operation cancelled during conflict resolution")
            self._transition_to_state(State.IDLE)
            self.context = None
            self.file_manager._clear_task()
            return
        
        # Get current conflict
        if self.context.current_conflict_index >= len(self.context.conflicts):
            self.logger.error("on_conflict_resolved called with no remaining conflicts")
            return
        
        source_file, dest_path = self.context.conflicts[self.context.current_conflict_index]
        
        # Handle the choice
        if choice == 'overwrite':
            # Mark file for overwrite
            self.context.results['success'].append((source_file, dest_path, True))
            self.logger.info(f"Overwrite selected for: {source_file.name}")
            
            # Set apply-to-all option if requested
            if apply_to_all:
                self.context.options['overwrite_all'] = True
                self.logger.info("Overwrite will be applied to all remaining conflicts")
            
            # Move to next conflict
            self.context.current_conflict_index += 1
            self._resolve_next_conflict()
        
        elif choice == 'skip':
            # Mark file as skipped
            self.context.results['skipped'].append(source_file)
            self.logger.info(f"Skip selected for: {source_file.name}")
            
            # Set apply-to-all option if requested
            if apply_to_all:
                self.context.options['skip_all'] = True
                self.logger.info("Skip will be applied to all remaining conflicts")
            
            # Move to next conflict
            self.context.current_conflict_index += 1
            self._resolve_next_conflict()
        
        elif choice == 'rename':
            # Show rename dialog
            self.logger.info(f"Rename selected for: {source_file.name}")
            
            # Set apply-to-all option if requested (for future implementation)
            if apply_to_all:
                self.context.options['rename_all'] = True
                self.logger.info("Rename will be applied to all remaining conflicts")
            
            # Show rename dialog (will be implemented in task 7)
            self._show_rename_dialog(source_file)
        
        else:
            self.logger.error(f"Invalid conflict resolution choice: {choice}")
            # Continue to next conflict to avoid getting stuck
            self.context.current_conflict_index += 1
            self._resolve_next_conflict()
    
    def on_renamed(self, source_file: Path, new_name: str):
        """Handle rename confirmation.
        
        Called when user provides a new name for a conflicting file.
        Validates the new name, checks for conflicts, and updates results.
        
        Args:
            source_file: The source file being renamed
            new_name: The new name provided by user
        """
        if not self.context:
            self.logger.error("on_renamed called with no operation context")
            return
        
        # Validate new name is not empty (strip whitespace)
        new_name = new_name.strip()
        if not new_name:
            self.logger.warning("Rename rejected: empty name provided")
            # Show error message and return to rename dialog
            self.file_manager.show_dialog(
                "Error: Filename cannot be empty",
                [{"text": "OK", "key": "o", "value": "ok"}],
                lambda choice: self._show_rename_dialog(source_file)
            )
            return
        
        # Construct new destination path
        new_dest_path = self.context.destination / new_name
        
        # Check if new name also conflicts
        if new_dest_path.exists():
            self.logger.warning(f"Rename conflict: {new_name} already exists")
            # Show secondary conflict dialog
            message = f"File '{new_name}' already exists. Choose action:"
            choices = [
                {"text": "Overwrite", "key": "o", "value": "overwrite"},
                {"text": "Try Again", "key": "r", "value": "retry"},
                {"text": "Skip", "key": "s", "value": "skip"}
            ]
            
            def handle_secondary_conflict(choice):
                if choice == 'overwrite':
                    # Mark file for copy/move with new name and overwrite
                    self.context.results['success'].append((source_file, new_dest_path, True))
                    self.logger.info(f"Renamed with overwrite: {source_file.name} → {new_name}")
                    # Move to next conflict
                    self.context.current_conflict_index += 1
                    self._resolve_next_conflict()
                elif choice == 'retry':
                    # Show rename dialog again
                    self._show_rename_dialog(source_file)
                elif choice == 'skip':
                    # Mark file as skipped
                    self.context.results['skipped'].append(source_file)
                    self.logger.info(f"Skipped after rename conflict: {source_file.name}")
                    # Move to next conflict
                    self.context.current_conflict_index += 1
                    self._resolve_next_conflict()
            
            self.file_manager.show_dialog(message, choices, handle_secondary_conflict)
        else:
            # New name is unique, mark file for copy/move with new name
            self.context.results['success'].append((source_file, new_dest_path, False))
            self.logger.info(f"Renamed: {source_file.name} → {new_name}")
            
            # Move to next conflict
            self.context.current_conflict_index += 1
            self._resolve_next_conflict()
    
    def on_rename_cancelled(self):
        """Handle rename cancellation.
        
        Called when user cancels the rename dialog. Returns to the conflict
        resolution dialog to give the user another chance to choose a different
        resolution option.
        """
        if not self.context:
            self.logger.error("on_rename_cancelled called with no operation context")
            return
        
        # Log cancellation
        self.logger.info("Rename cancelled, returning to conflict resolution")
        
        # Return to conflict resolution dialog for the current conflict
        # This gives the user another chance to choose overwrite or skip
        self._resolve_next_conflict()
    
    def _show_rename_dialog(self, source_file: Path):
        """Show rename dialog for a conflicting file.
        
        Displays a text input dialog for the user to enter a new name.
        
        Args:
            source_file: The source file to be renamed
        """
        # Show rename dialog via UI
        self.ui.show_rename_dialog(
            source_file,
            self.context.destination,
            self.on_renamed,
            self.on_rename_cancelled
        )
    
    def _transition_to_state(self, new_state: State):
        """Transition to a new state with hooks.
        
        This method handles state transitions, calling the appropriate hooks
        for exiting the old state and entering the new state.
        
        Args:
            new_state: The state to transition to
        """
        old_state = self.state
        self.on_state_exit(old_state)
        self.state = new_state
        self.on_state_enter(new_state)
        self.logger.debug(f"State transition: {old_state.value} → {new_state.value}")
    
    def _check_conflicts(self):
        """Check for file conflicts.
        
        Detects conflicts for copy/move operations by checking if destination
        files already exist. Stores conflicts in the operation context.
        
        For copy and move operations:
        - Checks each source file against its destination path
        - If destination exists, adds (source, dest) pair to conflicts list
        
        For delete operations:
        - No conflicts to check, proceeds directly to execution
        
        After checking:
        - If conflicts found: transitions to RESOLVING_CONFLICT state
        - If no conflicts: transitions to EXECUTING state
        """
        if not self.context:
            self.logger.error("_check_conflicts called with no operation context")
            return
        
        operation_type = self.context.operation_type
        
        # Delete operations have no conflicts to check
        if operation_type == 'delete':
            self.logger.info("Delete operation has no conflicts to check")
            self._transition_to_state(State.EXECUTING)
            self._execute_operation()
            return
        
        # Check conflicts for copy/move operations
        destination = self.context.destination
        conflicts = []
        
        for source_file in self.context.files:
            # Construct destination path
            dest_path = destination / source_file.name
            
            # Check if destination already exists
            if dest_path.exists():
                conflicts.append((source_file, dest_path))
                self.logger.info(f"Conflict detected: {source_file.name} → {dest_path}")
        
        # Store conflicts in context
        self.context.conflicts = conflicts
        
        if conflicts:
            # Conflicts found, transition to resolution state
            self.logger.info(f"Found {len(conflicts)} conflict(s), transitioning to resolution")
            self._transition_to_state(State.RESOLVING_CONFLICT)
            self._resolve_next_conflict()
        else:
            # No conflicts, proceed to execution
            self.logger.info("No conflicts detected, proceeding to execution")
            self._transition_to_state(State.EXECUTING)
            self._execute_operation()
    
    def _build_confirmation_message(self) -> str:
        """Build confirmation message for the operation.
        
        Creates an appropriate confirmation message based on the operation type
        and number of files.
        
        Returns:
            Confirmation message string
        """
        if not self.context:
            return "Confirm operation?"
        
        operation_type = self.context.operation_type
        files = self.context.files
        destination = self.context.destination
        
        # Build message based on operation type and file count
        if len(files) == 1:
            # Single file operation
            file_name = files[0].name
            if operation_type == 'copy':
                return f"Copy '{file_name}' to {destination}?"
            elif operation_type == 'move':
                return f"Move '{file_name}' to {destination}?"
            elif operation_type == 'delete':
                return f"Delete '{file_name}'?"
        else:
            # Multiple file operation
            file_count = len(files)
            if operation_type == 'copy':
                return f"Copy {file_count} files to {destination}?"
            elif operation_type == 'move':
                return f"Move {file_count} files to {destination}?"
            elif operation_type == 'delete':
                return f"Delete {file_count} files?"
        
        # Fallback
        return f"Confirm {operation_type} operation?"
    
    def _validate_operation(self) -> Tuple[bool, Optional[str]]:
        """Validate if the operation is allowed based on storage capabilities.
        
        Checks if the source and destination paths support the requested operation
        based on their storage capabilities (read-only vs read-write).
        
        Validation rules:
        - Delete: Source paths must support write operations
        - Move: Source and destination paths must support write operations
        - Copy: Destination path must support write operations (source can be read-only)
        
        Returns:
            Tuple of (is_valid, error_message):
            - is_valid: True if operation is allowed, False otherwise
            - error_message: Error message if operation is not allowed, None otherwise
        """
        if not self.context:
            return False, "No operation context available"
        
        operation_type = self.context.operation_type
        files = self.context.files
        destination = self.context.destination
        
        # Validate delete operations
        if operation_type == 'delete':
            # Check if all source paths support write operations (required for deletion)
            for path in files:
                if not path.supports_write_operations():
                    return False, "Cannot delete files from read-only storage."
        
        # Validate move operations
        elif operation_type == 'move':
            # Check if all source paths support write operations (required for deletion after move)
            for path in files:
                if not path.supports_write_operations():
                    return False, "Cannot move files from read-only storage. Use copy instead."
            
            # Check if destination supports write operations (required for writing)
            if destination and not destination.supports_write_operations():
                return False, "Cannot move files to read-only storage."
        
        # Validate copy operations
        elif operation_type == 'copy':
            # Can copy FROM any storage, but destination must support write operations
            if destination and not destination.supports_write_operations():
                return False, "Cannot copy files to read-only storage."
            # Copying FROM read-only storage is OK (extraction)
        
        # Operation is valid
        return True, None
    
    def _resolve_next_conflict(self):
        """Resolve the next conflict in the queue.
        
        Shows conflict dialog for the current conflict and handles user's choice.
        Processes conflicts sequentially, showing a dialog for each one unless
        an apply-to-all option has been set.
        
        If all conflicts have been resolved, transitions to EXECUTING state.
        """
        if not self.context:
            self.logger.error("_resolve_next_conflict called with no operation context")
            return
        
        # Check if we've processed all conflicts
        if self.context.current_conflict_index >= len(self.context.conflicts):
            self.logger.info("All conflicts resolved, proceeding to execution")
            self._transition_to_state(State.EXECUTING)
            self._execute_operation()
            return
        
        # Check if apply-to-all options are set
        if self.context.options['overwrite_all']:
            # Apply overwrite to current conflict
            source_file, dest_path = self.context.conflicts[self.context.current_conflict_index]
            self.context.results['success'].append((source_file, dest_path, True))
            self.logger.info(f"Auto-overwrite (apply-to-all): {source_file.name}")
            
            # Move to next conflict
            self.context.current_conflict_index += 1
            self._resolve_next_conflict()
            return
        
        if self.context.options['skip_all']:
            # Apply skip to current conflict
            source_file, dest_path = self.context.conflicts[self.context.current_conflict_index]
            self.context.results['skipped'].append(source_file)
            self.logger.info(f"Auto-skip (apply-to-all): {source_file.name}")
            
            # Move to next conflict
            self.context.current_conflict_index += 1
            self._resolve_next_conflict()
            return
        
        # Get current conflict
        source_file, dest_path = self.context.conflicts[self.context.current_conflict_index]
        
        # Calculate conflict numbers
        conflict_num = self.context.current_conflict_index + 1
        total_conflicts = len(self.context.conflicts)
        
        # Show conflict dialog via UI
        self.ui.show_conflict_dialog(
            source_file,
            dest_path,
            conflict_num,
            total_conflicts,
            lambda choice, apply_to_all=False: self.on_conflict_resolved(choice, apply_to_all)
        )
    
    def _execute_operation(self):
        """Execute the file operation.
        
        Prepares the file list and delegates to operation-specific execution
        methods. Combines non-conflicting files with resolved conflicts.
        """
        if not self.context:
            self.logger.error("_execute_operation called with no operation context")
            return
        
        # Prepare file list for execution
        # Start with files that had no conflicts
        files_to_process = []
        
        # Add non-conflicting files (those not in conflicts list)
        conflict_sources = {source for source, _ in self.context.conflicts}
        for file in self.context.files:
            if file not in conflict_sources:
                # This file had no conflict, add it to process list
                if self.context.operation_type == 'delete':
                    files_to_process.append(file)
                else:
                    # For copy/move, add as (source, dest, overwrite) tuple
                    dest_path = self.context.destination / file.name
                    files_to_process.append((file, dest_path, False))
        
        # Add resolved conflicts from results['success']
        # These are already in (source, dest, overwrite) format for copy/move
        files_to_process.extend(self.context.results['success'])
        
        # Log what we're about to execute
        total_files = len(files_to_process)
        skipped_count = len(self.context.results['skipped'])
        self.logger.info(f"Executing {self.context.operation_type} operation: {total_files} files to process, {skipped_count} skipped")
        
        # Delegate to operation-specific execution method
        if self.context.operation_type == 'copy':
            self._execute_copy(files_to_process)
        elif self.context.operation_type == 'move':
            self._execute_move(files_to_process)
        elif self.context.operation_type == 'delete':
            self._execute_delete(files_to_process)
        else:
            self.logger.error(f"Unknown operation type: {self.context.operation_type}")
            self._transition_to_state(State.IDLE)
            self.context = None
            self.file_manager._clear_task()
    
    def _execute_copy(self, files_to_copy):
        """Execute copy operation in background thread.
        
        Delegates to FileOperationExecutor to perform the actual copy operation
        with pre-resolved files.
        
        Args:
            files_to_copy: List of (source, dest, overwrite) tuples
        """
        import threading
        
        # Check if executor is available
        if not self.executor:
            self.logger.error("Cannot execute copy operation: no executor available")
            self._transition_to_state(State.COMPLETED)
            self._complete_operation()
            return
        
        # Reset cancellation flag
        self._cancelled = False
        
        self.logger.info(f"Starting copy operation with {len(files_to_copy)} files")
        
        # Create background worker thread
        def copy_worker():
            try:
                # Separate files by overwrite flag
                files_no_overwrite = []
                files_with_overwrite = []
                
                for source, dest, overwrite in files_to_copy:
                    if overwrite:
                        files_with_overwrite.append(source)
                    else:
                        files_no_overwrite.append(source)
                
                # Get destination directory from first file
                if files_to_copy:
                    destination_dir = files_to_copy[0][1].parent
                    
                    # Track pending batches to know when all operations are complete
                    pending_batches = 0
                    if files_no_overwrite:
                        pending_batches += 1
                    if files_with_overwrite:
                        pending_batches += 1
                    
                    # Store pending count in context for tracking
                    if self.context:
                        self.context.pending_batches = pending_batches
                    
                    # Copy files without overwrite first
                    if files_no_overwrite:
                        self.executor.perform_copy_operation(
                            files_no_overwrite,
                            destination_dir,
                            overwrite=False,
                            completion_callback=self._on_copy_complete,
                            continue_progress=False,  # Start new progress
                            task=self
                        )
                    
                    # Copy files with overwrite, continuing the same progress operation
                    if files_with_overwrite:
                        self.executor.perform_copy_operation(
                            files_with_overwrite,
                            destination_dir,
                            overwrite=True,
                            completion_callback=self._on_copy_complete,
                            continue_progress=True,  # Continue existing progress
                            task=self
                        )
                else:
                    # No files to copy, complete immediately
                    self._on_copy_complete(0, 0)
                    
            except Exception as e:
                self.logger.error(f"Error in copy worker thread: {e}")
                # Ensure we clean up even on error
                self._transition_to_state(State.COMPLETED)
                self._complete_operation()
        
        # Start the worker thread
        worker_thread = threading.Thread(target=copy_worker, daemon=True)
        worker_thread.start()
    
    def _on_copy_complete(self, copied_count, error_count):
        """Callback when copy operation completes.
        
        Args:
            copied_count: Number of files successfully copied
            error_count: Number of files that failed to copy
        """
        # Store results in context
        if self.context:
            # Update success count in results
            self.context.results['success'].extend([None] * copied_count)
            # Update error count in results
            self.context.results['errors'].extend([None] * error_count)
            
            # Decrement pending batches
            if hasattr(self.context, 'pending_batches'):
                self.context.pending_batches -= 1
                
                # Only complete when all batches are done
                if self.context.pending_batches > 0:
                    self.logger.debug(f"Batch completed, {self.context.pending_batches} batch(es) remaining")
                    return
        
        # All batches complete - transition to COMPLETED state
        self._transition_to_state(State.COMPLETED)
        self._complete_operation()
    
    def _execute_move(self, files_to_move):
        """Execute move operation in background thread.
        
        Delegates to FileOperationExecutor to perform the actual move operation
        with pre-resolved files.
        
        Args:
            files_to_move: List of (source, dest, overwrite) tuples
        """
        import threading
        
        # Check if executor is available
        if not self.executor:
            self.logger.error("Cannot execute move operation: no executor available")
            self._transition_to_state(State.COMPLETED)
            self._complete_operation()
            return
        
        # Reset cancellation flag
        self._cancelled = False
        
        self.logger.info(f"Starting move operation with {len(files_to_move)} files")
        
        # Create background worker thread
        def move_worker():
            try:
                # Separate files by overwrite flag
                files_no_overwrite = []
                files_with_overwrite = []
                
                for source, dest, overwrite in files_to_move:
                    if overwrite:
                        files_with_overwrite.append(source)
                    else:
                        files_no_overwrite.append(source)
                
                # Get destination directory from first file
                if files_to_move:
                    destination_dir = files_to_move[0][1].parent
                    
                    # Track pending batches to know when all operations are complete
                    pending_batches = 0
                    if files_no_overwrite:
                        pending_batches += 1
                    if files_with_overwrite:
                        pending_batches += 1
                    
                    # Store pending count in context for tracking
                    if self.context:
                        self.context.pending_batches = pending_batches
                    
                    # Move files without overwrite first
                    if files_no_overwrite:
                        self.executor.perform_move_operation(
                            files_no_overwrite,
                            destination_dir,
                            overwrite=False,
                            completion_callback=self._on_move_complete,
                            continue_progress=False,  # Start new progress
                            task=self
                        )
                    
                    # Move files with overwrite, continuing the same progress operation
                    if files_with_overwrite:
                        self.executor.perform_move_operation(
                            files_with_overwrite,
                            destination_dir,
                            overwrite=True,
                            completion_callback=self._on_move_complete,
                            continue_progress=True,  # Continue existing progress
                            task=self
                        )
                else:
                    # No files to move, complete immediately
                    self._on_move_complete(0, 0)
                    
            except Exception as e:
                self.logger.error(f"Error in move worker thread: {e}")
                # Ensure we clean up even on error
                self._transition_to_state(State.COMPLETED)
                self._complete_operation()
        
        # Start the worker thread
        worker_thread = threading.Thread(target=move_worker, daemon=True)
        worker_thread.start()
    
    def _on_move_complete(self, moved_count, error_count):
        """Callback when move operation completes.
        
        Args:
            moved_count: Number of files successfully moved
            error_count: Number of files that failed to move
        """
        # Store results in context
        if self.context:
            # Update success count in results
            self.context.results['success'].extend([None] * moved_count)
            # Update error count in results
            self.context.results['errors'].extend([None] * error_count)
            
            # Decrement pending batches
            if hasattr(self.context, 'pending_batches'):
                self.context.pending_batches -= 1
                
                # Only complete when all batches are done
                if self.context.pending_batches > 0:
                    self.logger.debug(f"Batch completed, {self.context.pending_batches} batch(es) remaining")
                    return
        
        # All batches complete - transition to COMPLETED state
        self._transition_to_state(State.COMPLETED)
        self._complete_operation()
    
    def _execute_delete(self, files_to_delete):
        """Execute delete operation in background thread.
        
        Delegates to FileOperationExecutor to perform the actual delete operation.
        
        Args:
            files_to_delete: List of Path objects to delete
        """
        # Check if executor is available
        if not self.executor:
            self.logger.error("Cannot execute delete operation: no executor available")
            self._transition_to_state(State.COMPLETED)
            self._complete_operation()
            return
        
        # Reset cancellation flag
        self._cancelled = False
        
        self.logger.info(f"Starting delete operation with {len(files_to_delete)} files")
        
        # Call executor to perform delete operation
        # The executor will handle threading, progress tracking, and completion
        self.executor.perform_delete_operation(
            files_to_delete,
            completion_callback=self._on_delete_complete,
            task=self
        )
    
    def _on_delete_complete(self, deleted_count, error_count):
        """Callback when delete operation completes.
        
        Args:
            deleted_count: Number of files successfully deleted
            error_count: Number of files that failed to delete
        """
        # Store results in context
        if self.context:
            # Update success count in results
            self.context.results['success'].extend([None] * deleted_count)
            # Update error count in results
            self.context.results['errors'].extend([None] * error_count)
        
        # Transition to COMPLETED state
        self._transition_to_state(State.COMPLETED)
        self._complete_operation()


    
    def _complete_operation(self):
        """Complete the operation.
        
        Builds summary message, logs results, transitions to IDLE state,
        clears the operation context, and notifies FileManager that the task
        is complete.
        
        This method is called when the operation finishes (successfully or with
        errors) or when it's cancelled. It:
        1. Builds a summary message with operation counts
        2. Logs the summary at appropriate level (info/warning)
        3. Transitions to IDLE state
        4. Clears the operation context
        5. Calls file_manager._clear_task() to release the task
        """
        if not self.context:
            self.logger.warning("_complete_operation called with no operation context")
            # Still need to clean up and transition to IDLE
            self._transition_to_state(State.IDLE)
            self.file_manager._clear_task()
            return
        
        # Build summary message with counts
        operation_type = self.context.operation_type
        success_count = len(self.context.results['success'])
        skipped_count = len(self.context.results['skipped'])
        error_count = len(self.context.results['errors'])
        total_count = len(self.context.files)
        
        # Check if operation was cancelled
        was_cancelled = self.is_cancelled()
        
        # Build summary message
        if was_cancelled:
            summary = f"{operation_type.capitalize()} operation cancelled"
            if success_count > 0:
                summary += f" ({success_count} completed before cancellation)"
        else:
            summary = f"{operation_type.capitalize()} operation completed: "
            summary += f"{success_count} successful"
            
            if skipped_count > 0:
                summary += f", {skipped_count} skipped"
            
            if error_count > 0:
                summary += f", {error_count} errors"
        
        # Log summary at appropriate level
        if error_count > 0 or was_cancelled:
            # Use warning level if there were errors or cancellation
            self.logger.warning(summary)
        else:
            # Use info level for successful completion
            self.logger.info(summary)
        
        # Transition to IDLE state
        self._transition_to_state(State.IDLE)
        
        # Clear operation context
        self.context = None
        
        # Notify FileManager that task is complete
        self.file_manager._clear_task()
