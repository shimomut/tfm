#!/usr/bin/env python3
"""
TFM Archive Operation UI - Handles archive operation UI interactions
"""

from tfm_path import Path
from tfm_log_manager import getLogger
from typing import List, Dict, Callable, Optional


class ArchiveOperationUI:
    """Handles archive operation UI interactions.
    
    This class provides the user interface layer for archive operations,
    including confirmation dialogs and conflict resolution dialogs. It creates
    and starts ArchiveOperationTask instances.
    
    Architecture:
        ArchiveOperationUI is part of a clean four-layer architecture:
        - Layer 1: FileListManager - File list management
        - Layer 2: ArchiveOperationUI - UI interactions (this class)
        - Layer 3: ArchiveOperationTask - Orchestration (state machine)
        - Layer 4: ArchiveOperationExecutor - I/O operations
    
    Responsibilities:
        - Entry points for archive operations (create/extract)
        - UI dialog creation and display
        - Confirmation dialogs
        - Conflict resolution dialogs
        - Creating ArchiveOperationTask instances
        - NO I/O operations (delegated to ArchiveOperationExecutor)
    
    Task Usage:
        1. User initiates operation (create/extract)
        2. ArchiveOperationUI creates ArchiveOperationTask with ui=self and executor
        3. Task is started via file_manager.start_task()
        4. Task manages workflow and calls back to UI for dialogs
        5. Task delegates I/O to ArchiveOperationExecutor
        6. Task completes and cleans up
    
    Key Methods:
        - show_confirmation_dialog(): Show confirmation dialog
        - show_conflict_dialog(): Show conflict resolution dialog
    
    See Also:
        - tfm_archive_operation_task.py: ArchiveOperationTask implementation
        - tfm_archive_operation_executor.py: ArchiveOperationExecutor implementation
        - tfm_file_operation_ui.py: Similar pattern for file operations
    """
    
    def __init__(self, file_manager):
        """Initialize archive operations UI with file manager.
        
        Args:
            file_manager: FileManager instance for UI interactions and task management
        """
        self.file_manager = file_manager
        self.config = file_manager.config
        self.logger = getLogger("ArchiveUI")
    
    def show_confirmation_dialog(self, operation_type: str, source_paths: List[Path],
                                destination: Path, callback: Callable[[bool], None]):
        """Show confirmation dialog for archive operation.
        
        This method provides a centralized UI interaction for archive operation
        confirmations. It builds an appropriate confirmation message and
        delegates to file_manager.show_confirmation().
        
        Args:
            operation_type: Type of operation ('create' or 'extract')
            source_paths: List of Path objects to operate on
            destination: Destination Path (archive file for create, directory for extract)
            callback: Function to call with confirmation result (True/False)
        """
        # Build confirmation message
        if operation_type == 'create':
            if len(source_paths) == 1:
                # Single file archive creation
                file_name = source_paths[0].name
                message = f"Create archive '{destination.name}' from '{file_name}'?"
            else:
                # Multiple file archive creation
                file_count = len(source_paths)
                message = f"Create archive '{destination.name}' from {file_count} files?"
        
        elif operation_type == 'extract':
            # Archive extraction
            archive_name = source_paths[0].name if source_paths else 'archive'
            message = f"Extract '{archive_name}' to {destination}?"
        
        else:
            # Fallback for unknown operation types
            message = f"Confirm {operation_type} operation?"
        
        # Show confirmation dialog
        self.file_manager.show_confirmation(message, callback)
    
    def show_conflict_dialog(self, conflict_type: str, conflict_info: Dict,
                           conflict_num: int, total_conflicts: int,
                           callback: Callable[[Optional[str], bool], None]):
        """Show conflict resolution dialog.
        
        This method provides a centralized UI interaction for archive conflict
        resolution. It builds an appropriate conflict message and delegates
        to file_manager.show_dialog().
        
        Args:
            conflict_type: Type of conflict ('archive_exists' or 'file_exists')
            conflict_info: Dictionary with conflict details:
                - path: Path object for the conflicting file
                - size: File size in bytes (optional)
                - is_directory: Whether the conflict is a directory (optional)
            conflict_num: Current conflict number (1-based)
            total_conflicts: Total number of conflicts
            callback: Function to call with user's choice and apply_to_all flag
                     Signature: callback(choice: Optional[str], apply_to_all: bool)
                     choice can be 'overwrite', 'skip', or None (for cancel/ESC)
        """
        # Extract conflict information
        conflict_path = conflict_info.get('path')
        display_name = conflict_info.get('display_name', conflict_path.name if conflict_path else 'unknown')
        conflict_size = conflict_info.get('size')
        is_directory = conflict_info.get('is_directory', False)
        
        # Build conflict message based on conflict type
        if conflict_type == 'archive_exists':
            # Archive file already exists (for create operations)
            message = f"Archive exists: {display_name}"
            if conflict_size is not None:
                # Format size in human-readable format
                size_str = self._format_size(conflict_size)
                message += f" ({size_str})"
            
            if total_conflicts > 1:
                message += f" ({conflict_num}/{total_conflicts})"
            
            # For archive creation conflicts, only show Overwrite option
            # (Skip doesn't make sense for single archive file)
            choices = [
                {"text": "Overwrite", "key": "o", "value": "overwrite"}
            ]
        
        elif conflict_type == 'file_exists':
            # File exists in extraction destination (for extract operations)
            if is_directory:
                message = f"Directory exists: {display_name}"
            else:
                message = f"File exists: {display_name}"
            
            if conflict_size is not None and not is_directory:
                size_str = self._format_size(conflict_size)
                message += f" ({size_str})"
            
            if total_conflicts > 1:
                message += f" ({conflict_num}/{total_conflicts})"
            
            # For extraction conflicts, show both Overwrite and Skip options
            choices = [
                {"text": "Overwrite", "key": "o", "value": "overwrite"},
                {"text": "Skip", "key": "s", "value": "skip"}
            ]
        
        else:
            # Fallback for unknown conflict types
            message = f"Conflict: {display_name}"
            if total_conflicts > 1:
                message += f" ({conflict_num}/{total_conflicts})"
            
            choices = [
                {"text": "Overwrite", "key": "o", "value": "overwrite"},
                {"text": "Skip", "key": "s", "value": "skip"}
            ]
        
        # Wrapper callback to handle shift modifier detection
        def dialog_callback(choice, apply_to_all=False):
            """Wrapper callback that receives shift modifier flag and calls original callback.
            
            Args:
                choice: The user's choice value from the dialog
                apply_to_all: True if Shift modifier was pressed, False otherwise
            """
            # Call the original callback with choice and apply_to_all flag
            callback(choice, apply_to_all)
        
        # Show conflict dialog with shift modifier enabled for apply-to-all
        self.file_manager.show_dialog(
            message,
            choices,
            dialog_callback,
            enable_shift_modifier=True
        )
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
        
        Returns:
            Formatted size string (e.g., "1.5 MB", "234 KB")
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
