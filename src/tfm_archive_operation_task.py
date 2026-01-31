"""Task implementation for archive operations (create, extract).

This module provides the ArchiveOperationTask class, which implements the task
framework for archive operations. It manages the complete lifecycle of archive
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
from typing import Dict, List, Optional

from tfm_base_task import BaseTask


class State(Enum):
    """States for archive operation task lifecycle.
    
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
class ArchiveOperationContext:
    """Context for an archive operation.
    
    This dataclass holds all state for an ongoing archive operation, ensuring
    that all operation state is self-contained and not scattered across
    multiple objects.
    
    Attributes:
        operation_type: Type of operation ('create' or 'extract')
        source_paths: List of source files to archive or archive file to extract
        destination: Archive file path (for create) or extraction directory (for extract)
        format_type: Archive format ('tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'zip')
        conflicts: List of ConflictInfo objects
        current_conflict_index: Index of conflict currently being resolved
        results: Dictionary tracking operation results by category
        options: Dictionary of user choices for batch operations
    """
    operation_type: str
    source_paths: List[Path]
    destination: Path
    format_type: str = 'tar.gz'
    conflicts: List = field(default_factory=list)  # List of ConflictInfo objects
    current_conflict_index: int = 0
    results: Dict[str, List] = field(default_factory=lambda: {
        'success': [],
        'skipped': [],
        'errors': []
    })
    options: Dict[str, bool] = field(default_factory=lambda: {
        'overwrite_all': False,
        'skip_all': False
    })


class ArchiveOperationTask(BaseTask):
    """Task for archive operations (create, extract).
    
    This class implements the task framework for archive operations, managing
    the complete lifecycle from confirmation through execution to completion.
    
    The task coordinates:
    - User confirmations (if configured)
    - Conflict detection for archive operations
    - Conflict resolution (overwrite, skip)
    - Background thread execution via ArchiveOperationExecutor
    - Progress tracking and error handling
    - Operation completion and cleanup
    
    Architecture:
        The task delegates responsibilities to specialized components:
        - UI interactions → ArchiveOperationUI (via self.ui)
        - I/O operations → ArchiveOperationExecutor (via self.executor)
        - State machine logic → ArchiveOperationTask (this class)
    
    Example usage:
        task = ArchiveOperationTask(file_manager, archive_operations_ui, executor)
        task.start_operation('create', files, archive_path, 'tar.gz')
        file_manager.start_task(task)
    """
    
    def __init__(self, file_manager, ui, executor):
        """Initialize archive operation task.
        
        Args:
            file_manager: Reference to FileManager for task management
            ui: Reference to ArchiveOperationUI for UI interactions
            executor: Reference to ArchiveOperationExecutor for I/O operations
        """
        super().__init__(file_manager, logger_name="ArcvOp")
        self.ui = ui
        self.executor = executor
        self.state = State.IDLE
        self.context: Optional[ArchiveOperationContext] = None
    
    def start(self):
        """Start the task (called by FileManager).
        
        Note: The task is actually started via start_operation() which is
        called by the initiating component. This method exists to satisfy the
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
                self.file_manager.operation_cancelled = True
                self.logger.info("Cancellation requested during execution")
            
            self._transition_to_state(State.IDLE)
            self.context = None
            self.logger.info("Task cancelled")
            self.file_manager._clear_task()
    
    def handle_key_event(self, event):
        """Handle key events for the task.
        
        This method handles ESC key to cancel operations in progress.
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed, False otherwise
        """
        from ttk.input_event import KeyEvent, KeyCode
        
        if not isinstance(event, KeyEvent):
            return False
        
        # Handle ESC key to cancel operation
        if event.key_code == KeyCode.ESCAPE:
            if self.state == State.EXECUTING:
                # Set cancellation flag
                self.file_manager.operation_cancelled = True
                self.logger.info("Operation cancellation requested by user (ESC key)")
                return True
        
        return False
    
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
    
    def start_operation(self, operation_type: str, source_paths: List[Path], 
                       destination: Path, format_type: str = 'tar.gz'):
        """Start a new archive operation.
        
        This is the main entry point for starting an archive operation. It creates
        the operation context and begins the state machine workflow.
        
        Args:
            operation_type: Type of operation ('create' or 'extract')
            source_paths: List of Path objects to archive or archive file to extract
            destination: Archive file path (for create) or extraction directory (for extract)
            format_type: Archive format ('tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'zip')
        
        Raises:
            ValueError: If operation_type is invalid
        """
        # Validate operation type
        valid_operations = ('create', 'extract')
        if operation_type not in valid_operations:
            raise ValueError(f"Invalid operation type: {operation_type}. Must be one of {valid_operations}")
        
        # Create operation context
        self.context = ArchiveOperationContext(
            operation_type=operation_type,
            source_paths=source_paths,
            destination=destination,
            format_type=format_type
        )
        
        self.logger.info(f"Starting {operation_type} operation with {len(source_paths)} file(s)")
        
        # Check if confirmation is required based on configuration
        config_attr = f'CONFIRM_ARCHIVE_{operation_type.upper()}'
        confirm_required = getattr(self.ui.config, config_attr, True)
        
        if confirm_required:
            # Transition to CONFIRMING state and show confirmation dialog
            self._transition_to_state(State.CONFIRMING)
            
            # Show confirmation dialog via UI
            self.ui.show_confirmation_dialog(
                operation_type,
                source_paths,
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
        proceeds to execution.
        
        Args:
            choice: User's choice ('overwrite', 'skip', or None for cancel)
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
        
        conflict_info = self.context.conflicts[self.context.current_conflict_index]
        conflict_path = conflict_info.path
        
        # Handle the choice
        if choice == 'overwrite':
            # Mark file for overwrite
            self.context.results['success'].append(conflict_path)
            display_name = conflict_info.archive_entry_name if conflict_info.archive_entry_name else conflict_path.name
            self.logger.info(f"Overwrite selected for: {display_name}")
            
            # Set apply-to-all option if requested
            if apply_to_all:
                self.context.options['overwrite_all'] = True
                self.logger.info("Overwrite will be applied to all remaining conflicts")
            
            # Move to next conflict
            self.context.current_conflict_index += 1
            self._resolve_next_conflict()
        
        elif choice == 'skip':
            # Mark file as skipped
            self.context.results['skipped'].append(conflict_path)
            display_name = conflict_info.archive_entry_name if conflict_info.archive_entry_name else conflict_path.name
            self.logger.info(f"Skip selected for: {display_name}")
            
            # Set apply-to-all option if requested
            if apply_to_all:
                self.context.options['skip_all'] = True
                self.logger.info("Skip will be applied to all remaining conflicts")
            
            # Move to next conflict
            self.context.current_conflict_index += 1
            self._resolve_next_conflict()
        
        else:
            self.logger.error(f"Invalid conflict resolution choice: {choice}")
            # Continue to next conflict to avoid getting stuck
            self.context.current_conflict_index += 1
            self._resolve_next_conflict()
    
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
        
        Detects conflicts for archive operations:
        - For create: checks if destination archive file already exists
        - For extract: checks if any files in archive would overwrite existing files
        
        After checking:
        - If conflicts found: transitions to RESOLVING_CONFLICT state
        - If no conflicts: transitions to EXECUTING state
        """
        if not self.context:
            self.logger.error("_check_conflicts called with no operation context")
            return
        
        operation_type = self.context.operation_type
        
        # Delegate conflict detection to executor
        conflict_infos = self.executor._check_conflicts(
            operation_type,
            self.context.source_paths,
            self.context.destination
        )
        
        # Store ConflictInfo objects in context
        self.context.conflicts = conflict_infos
        
        if conflict_infos:
            # Conflicts found, transition to resolution state
            self.logger.info(f"Found {len(conflict_infos)} conflict(s), transitioning to resolution")
            self._transition_to_state(State.RESOLVING_CONFLICT)
            self._resolve_next_conflict()
        else:
            # No conflicts, proceed to execution
            self.logger.info("No conflicts detected, proceeding to execution")
            self._transition_to_state(State.EXECUTING)
            self._execute_operation()
    
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
        
        # Check if apply-to-all options are set - use loop instead of recursion
        if self.context.options['overwrite_all']:
            # Process all remaining conflicts in a loop to avoid recursion
            remaining_conflicts = self.context.conflicts[self.context.current_conflict_index:]
            self.logger.info(f"Auto-overwrite (apply-to-all): processing {len(remaining_conflicts)} remaining conflicts")
            
            for conflict_info in remaining_conflicts:
                self.context.results['success'].append(conflict_info.path)
            
            # Update index to mark all conflicts as processed
            self.context.current_conflict_index = len(self.context.conflicts)
            
            # Proceed to execution
            self.logger.info("All conflicts resolved with overwrite-all, proceeding to execution")
            self._transition_to_state(State.EXECUTING)
            self._execute_operation()
            return
        
        if self.context.options['skip_all']:
            # Process all remaining conflicts in a loop to avoid recursion
            remaining_conflicts = self.context.conflicts[self.context.current_conflict_index:]
            self.logger.info(f"Auto-skip (apply-to-all): processing {len(remaining_conflicts)} remaining conflicts")
            
            for conflict_info in remaining_conflicts:
                self.context.results['skipped'].append(conflict_info.path)
            
            # Update index to mark all conflicts as processed
            self.context.current_conflict_index = len(self.context.conflicts)
            
            # Proceed to execution
            self.logger.info("All conflicts resolved with skip-all, proceeding to execution")
            self._transition_to_state(State.EXECUTING)
            self._execute_operation()
            return
        
        # Get current conflict
        conflict_info = self.context.conflicts[self.context.current_conflict_index]
        conflict_path = conflict_info.path
        
        # Calculate conflict numbers
        conflict_num = self.context.current_conflict_index + 1
        total_conflicts = len(self.context.conflicts)
        
        # Determine conflict type based on operation
        if self.context.operation_type == 'create':
            conflict_type = 'archive_exists'
        else:
            conflict_type = 'file_exists'
        
        # Build conflict info dictionary
        # For archive extraction, use archive_entry_name if available, otherwise use path
        display_name = conflict_info.archive_entry_name if conflict_info.archive_entry_name else conflict_path.name
        
        conflict_info_dict = {
            'path': conflict_path,
            'display_name': display_name,
            'size': conflict_path.stat().st_size if conflict_path.exists() else None,
            'is_directory': conflict_path.is_dir() if conflict_path.exists() else False
        }
        
        # Show conflict dialog via UI
        self.ui.show_conflict_dialog(
            conflict_type,
            conflict_info_dict,
            conflict_num,
            total_conflicts,
            lambda choice, apply_to_all=False: self.on_conflict_resolved(choice, apply_to_all)
        )
    
    def _execute_operation(self):
        """Execute the archive operation.
        
        Delegates to the executor to perform the actual archive operation
        in a background thread.
        """
        if not self.context:
            self.logger.error("_execute_operation called with no operation context")
            return
        
        # Set operation cancelled flag
        self.file_manager.operation_cancelled = False
        
        operation_type = self.context.operation_type
        self.logger.info(f"Executing {operation_type} operation")
        
        # Delegate to operation-specific execution method
        if operation_type == 'create':
            self._execute_create()
        elif operation_type == 'extract':
            self._execute_extract()
        else:
            self.logger.error(f"Unknown operation type: {operation_type}")
            self._transition_to_state(State.IDLE)
            self.context = None
            self.file_manager._clear_task()
    
    def _execute_create(self):
        """Execute archive creation operation.
        
        Delegates to ArchiveOperationExecutor to perform the actual creation
        operation in a background thread.
        """
        if not self.context:
            return
        
        self.logger.info(f"Starting archive creation with {len(self.context.source_paths)} file(s)")
        
        # Determine if we should overwrite based on conflict resolution
        overwrite = len(self.context.results['success']) > 0
        
        # Call executor to perform creation operation
        self.executor.perform_create_operation(
            self.context.source_paths,
            self.context.destination,
            self.context.format_type,
            completion_callback=self._on_operation_complete
        )
    
    def _execute_extract(self):
        """Execute archive extraction operation.
        
        Delegates to ArchiveOperationExecutor to perform the actual extraction
        operation in a background thread.
        """
        if not self.context:
            return
        
        self.logger.info(f"Starting archive extraction to {self.context.destination}")
        
        # Determine if we should overwrite based on conflict resolution
        # If overwrite_all is True, overwrite everything
        # If individual files were marked for overwrite, we need to pass them separately
        overwrite_all = self.context.options.get('overwrite_all', False)
        
        # Build list of files to skip (those marked as skipped during conflict resolution)
        # Convert full paths to relative paths from destination directory
        skip_files = []
        for path in self.context.results.get('skipped', []):
            try:
                # Get relative path from destination directory
                rel_path = path.relative_to(self.context.destination)
                skip_files.append(str(rel_path))
            except ValueError:
                # If relative_to fails, fall back to just the name
                skip_files.append(path.name)
        
        # Build list of files to overwrite (those marked for overwrite during conflict resolution)
        # Convert full paths to relative paths from destination directory
        overwrite_files = []
        for path in self.context.results.get('success', []):
            try:
                # Get relative path from destination directory
                rel_path = path.relative_to(self.context.destination)
                overwrite_files.append(str(rel_path))
            except ValueError:
                # If relative_to fails, fall back to just the name
                overwrite_files.append(path.name)
        
        # Call executor to perform extraction operation
        self.executor.perform_extract_operation(
            self.context.source_paths[0],  # Archive file is first (and only) source path
            self.context.destination,
            overwrite_all,
            skip_files=skip_files,
            overwrite_files=overwrite_files,
            completion_callback=self._on_operation_complete
        )
    
    def _on_operation_complete(self, success_count: int, error_count: int):
        """Callback when archive operation completes.
        
        Args:
            success_count: Number of files successfully processed
            error_count: Number of files that failed to process
        """
        # Store executor's counts for final summary
        # Note: We don't add to results lists here because conflict resolution
        # already populated them with the actual file paths
        if self.context:
            # Store the executor's counts separately for accurate reporting
            self.context.executor_success_count = success_count
            self.context.executor_error_count = error_count
        
        # Refresh file manager if operation was successful and not cancelled
        if success_count > 0 and not self.file_manager.operation_cancelled:
            # Refresh both panes since source and destination could be in the same directory
            # For 'create': archive file appears in destination, source files may have changed
            # For 'extract': extracted files appear in destination, archive may be in source
            if hasattr(self.file_manager, 'refresh_files'):
                self.file_manager.refresh_files()  # Refresh both panes
        
        # Mark UI as dirty to trigger redraw
        if hasattr(self.file_manager, 'mark_dirty'):
            self.file_manager.mark_dirty()
        
        # Transition to COMPLETED state
        self._transition_to_state(State.COMPLETED)
        self._complete_operation()
    
    def _complete_operation(self):
        """Complete the operation.
        
        Builds summary message, logs results, transitions to IDLE state,
        clears the operation context, and notifies FileManager that the task
        is complete.
        
        This method is called when the operation finishes (successfully or with
        errors) or when it's cancelled.
        """
        if not self.context:
            self.logger.warning("_complete_operation called with no operation context")
            # Still need to clean up and transition to IDLE
            self._transition_to_state(State.IDLE)
            self.file_manager._clear_task()
            return
        
        # Build summary message with counts
        # Use executor's counts if available (from actual operation), otherwise use results lists
        operation_type = self.context.operation_type
        success_count = getattr(self.context, 'executor_success_count', len(self.context.results['success']))
        skipped_count = len(self.context.results['skipped'])
        error_count = getattr(self.context, 'executor_error_count', len(self.context.results['errors']))
        
        # Check if operation was cancelled
        was_cancelled = self.file_manager.operation_cancelled
        
        # Build summary message
        if was_cancelled:
            summary = f"Archive {operation_type} operation cancelled"
            if success_count > 0:
                summary += f" ({success_count} completed before cancellation)"
        else:
            summary = f"Archive {operation_type} operation completed: "
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
