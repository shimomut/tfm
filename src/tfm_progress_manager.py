#!/usr/bin/env python3
"""
TFM Progress Manager - Handles progress tracking for file operations
"""

import time
from enum import Enum
from typing import Optional, Callable, Dict, Any
from tfm_progress_animator import ProgressAnimator
from tfm_str_format import format_size


class OperationType(Enum):
    """Types of operations that can show progress"""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    ARCHIVE_CREATE = "archive_create"
    ARCHIVE_EXTRACT = "archive_extract"


class ProgressManager:
    """Manages progress tracking for long-running file operations"""
    
    def __init__(self, config=None):
        self.current_operation: Optional[Dict[str, Any]] = None
        self.progress_callback: Optional[Callable] = None
        self.last_callback_time: float = 0
        self.callback_throttle_ms: float = 50  # Minimum 50ms between callbacks
        
        # Create animator with config or use minimal config
        if config:
            self.animator = ProgressAnimator(config, pattern_override='spinner', speed_override=0.08)
        else:
            # Create a minimal config object for standalone use
            class MinimalConfig:
                PROGRESS_ANIMATION_PATTERN = 'spinner'
                PROGRESS_ANIMATION_SPEED = 0.08
            self.animator = ProgressAnimator(MinimalConfig())
    

    
    def start_operation(self, operation_type: OperationType, total_items: int, 
                       description: str = "", progress_callback: Optional[Callable] = None):
        """Start tracking progress for an operation
        
        Args:
            operation_type: Type of operation being performed
            total_items: Total number of items to process
            description: Optional description of the operation
            progress_callback: Optional callback to call when progress updates
        """
        self.current_operation = {
            'type': operation_type,
            'total_items': total_items,
            'processed_items': 0,
            'current_item': '',
            'description': description,
            'errors': 0,
            'file_bytes_copied': 0,  # Bytes copied for current file
            'file_bytes_total': 0,   # Total bytes for current file
            'counting': True         # Flag to indicate we're still counting files
        }
        self.progress_callback = progress_callback
        self.animator.reset()
        
        # Call callback with initial state
        if self.progress_callback:
            self.progress_callback(self.current_operation)
    
    def update_operation_total(self, total_items: int, description: str = ""):
        """Update the total item count for current operation
        
        This is useful when the total count isn't known at operation start
        (e.g., during file counting phase).
        
        Args:
            total_items: New total number of items
            description: Optional updated description
        """
        if not self.current_operation:
            return
        
        self.current_operation['total_items'] = total_items
        if description:
            self.current_operation['description'] = description
        
        # Mark counting as complete
        self.current_operation['counting'] = False
        
        # Trigger callback to update display
        self._trigger_callback_if_needed(force=True)
    
    def update_progress(self, current_item: str, processed_items: Optional[int] = None):
        """Update progress with current item being processed
        
        Args:
            current_item: Name of the current item being processed
            processed_items: Optional override for processed count (auto-increments if None)
        """
        if not self.current_operation:
            return
        
        self.current_operation['current_item'] = current_item
        self.current_operation['file_bytes_copied'] = 0  # Reset byte progress for new file
        self.current_operation['file_bytes_total'] = 0
        
        # Mark counting as complete when we start processing items
        self.current_operation['counting'] = False
        
        if processed_items is not None:
            self.current_operation['processed_items'] = processed_items
        else:
            self.current_operation['processed_items'] += 1
        
        # Call callback with updated state (with throttling)
        self._trigger_callback_if_needed()
    
    def update_file_byte_progress(self, bytes_copied: int, bytes_total: int):
        """Update the byte-level progress for the current file being copied
        
        Args:
            bytes_copied: Number of bytes copied so far
            bytes_total: Total number of bytes in the file
        """
        if not self.current_operation:
            return
        
        self.current_operation['file_bytes_copied'] = bytes_copied
        self.current_operation['file_bytes_total'] = bytes_total
        
        # Call callback with updated state (with throttling)
        self._trigger_callback_if_needed()
    
    def _trigger_callback_if_needed(self, force: bool = False):
        """Trigger progress callback if enough time has passed or forced
        
        Args:
            force: If True, bypass throttling and always trigger callback
        """
        if not self.progress_callback:
            return
        
        current_time = time.time() * 1000  # Convert to milliseconds
        
        # Always call callback for the first update, if forced, or if enough time has passed
        if (force or 
            self.last_callback_time == 0 or 
            current_time - self.last_callback_time >= self.callback_throttle_ms or
            (self.current_operation and 
             self.current_operation['processed_items'] >= self.current_operation['total_items'])):
            
            self.progress_callback(self.current_operation)
            self.last_callback_time = current_time
    
    def refresh_animation(self):
        """Force a callback to refresh animation without changing progress data
        
        This should be called periodically to keep the animation smooth even when
        there are no progress updates (e.g., during large file copies).
        """
        if self.current_operation and self.progress_callback:
            # Force callback to update animation
            self._trigger_callback_if_needed(force=True)
    
    def increment_errors(self):
        """Increment the error count for the current operation"""
        if self.current_operation:
            self.current_operation['errors'] += 1
    
    def finish_operation(self):
        """Finish the current operation and clear progress state"""
        if self.progress_callback and self.current_operation:
            # Call callback one final time to clear progress display
            self.progress_callback(None)
        
        self.current_operation = None
        self.progress_callback = None
        self.last_callback_time = 0  # Reset throttling
        self.animator.reset()
    
    def is_operation_active(self) -> bool:
        """Check if an operation is currently being tracked"""
        return self.current_operation is not None
    
    def get_current_operation(self) -> Optional[Dict[str, Any]]:
        """Get the current operation state"""
        return self.current_operation
    
    def get_progress_percentage(self) -> int:
        """Get the current progress as a percentage (0-100)"""
        if not self.current_operation or self.current_operation['total_items'] == 0:
            return 0
        
        return int((self.current_operation['processed_items'] / self.current_operation['total_items']) * 100)
    
    def get_progress_text(self, max_width: int = 80) -> str:
        """Get formatted progress text for display
        
        Args:
            max_width: Maximum width for the progress text
            
        Returns:
            Formatted progress string
        """
        if not self.current_operation:
            return ""
        
        op = self.current_operation
        op_type = op['type']
        processed = op['processed_items']
        total = op['total_items']
        current_item = op['current_item']
        file_bytes_copied = op.get('file_bytes_copied', 0)
        file_bytes_total = op.get('file_bytes_total', 0)
        
        # Get operation verb
        operation_verbs = {
            OperationType.COPY: "Copying",
            OperationType.MOVE: "Moving", 
            OperationType.DELETE: "Deleting",
            OperationType.ARCHIVE_CREATE: "Creating archive",
            OperationType.ARCHIVE_EXTRACT: "Extracting archive"
        }
        
        verb = operation_verbs.get(op_type, "Processing")
        
        # Get animation frame using the existing animator
        animation_frame = self.animator.get_current_frame()
        
        # Build base progress text with animator (no percentage)
        # Hide count during counting phase
        is_counting = op.get('counting', False)
        
        if is_counting:
            # During counting, show "Preparing..." without count
            if op['description']:
                progress_text = f"{animation_frame} {verb} ({op['description']})... Preparing"
            else:
                progress_text = f"{animation_frame} {verb}... Preparing"
        else:
            # After counting, show actual progress count
            if op['description']:
                progress_text = f"{animation_frame} {verb} ({op['description']})... {processed}/{total}"
            else:
                progress_text = f"{animation_frame} {verb}... {processed}/{total}"
        
        # Add current item if there's space
        if current_item:
            # Calculate available space for filename
            base_len = len(progress_text)
            separator = " - "
            available_space = max_width - base_len - len(separator)
            
            # Reserve space for byte progress if applicable
            # Only show byte progress for large files (>1MB) that require multiple read/write operations
            byte_progress_text = ""
            if file_bytes_total > 1024 * 1024 and file_bytes_copied > 0:
                bytes_copied_str = format_size(file_bytes_copied, compact=True)
                bytes_total_str = format_size(file_bytes_total, compact=True)
                byte_progress_text = f" [{bytes_copied_str}/{bytes_total_str}]"
                available_space -= len(byte_progress_text)
            
            if available_space > 10:  # Only show filename if we have reasonable space
                # Truncate filename if too long
                if len(current_item) > available_space:
                    truncate_at = max(1, available_space - 1)
                    current_item = "…" + current_item[-truncate_at:]
                
                progress_text += separator + current_item + byte_progress_text
        
        return progress_text