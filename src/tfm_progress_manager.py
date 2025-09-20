#!/usr/bin/env python3
"""
TFM Progress Manager - Handles progress tracking for file operations
"""

from enum import Enum
from typing import Optional, Callable, Dict, Any


class OperationType(Enum):
    """Types of operations that can show progress"""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    ARCHIVE_CREATE = "archive_create"
    ARCHIVE_EXTRACT = "archive_extract"


class ProgressManager:
    """Manages progress tracking for long-running file operations"""
    
    def __init__(self):
        self.current_operation: Optional[Dict[str, Any]] = None
        self.progress_callback: Optional[Callable] = None
        self.last_callback_time: float = 0
        self.callback_throttle_ms: float = 50  # Minimum 50ms between callbacks
    
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
            'errors': 0
        }
        self.progress_callback = progress_callback
        
        # Call callback with initial state
        if self.progress_callback:
            self.progress_callback(self.current_operation)
    
    def update_progress(self, current_item: str, processed_items: Optional[int] = None):
        """Update progress with current item being processed
        
        Args:
            current_item: Name of the current item being processed
            processed_items: Optional override for processed count (auto-increments if None)
        """
        if not self.current_operation:
            return
        
        self.current_operation['current_item'] = current_item
        
        if processed_items is not None:
            self.current_operation['processed_items'] = processed_items
        else:
            self.current_operation['processed_items'] += 1
        
        # Call callback with updated state (with throttling)
        if self.progress_callback:
            import time
            current_time = time.time() * 1000  # Convert to milliseconds
            
            # Always call callback for the first update or if enough time has passed
            if (self.last_callback_time == 0 or 
                current_time - self.last_callback_time >= self.callback_throttle_ms or
                self.current_operation['processed_items'] >= self.current_operation['total_items']):
                
                self.progress_callback(self.current_operation)
                self.last_callback_time = current_time
    
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
        percentage = self.get_progress_percentage()
        
        # Get operation verb
        operation_verbs = {
            OperationType.COPY: "Copying",
            OperationType.MOVE: "Moving", 
            OperationType.DELETE: "Deleting",
            OperationType.ARCHIVE_CREATE: "Creating archive",
            OperationType.ARCHIVE_EXTRACT: "Extracting archive"
        }
        
        verb = operation_verbs.get(op_type, "Processing")
        
        # Build base progress text
        if op['description']:
            progress_text = f"{verb} ({op['description']})... {processed}/{total} ({percentage}%)"
        else:
            progress_text = f"{verb}... {processed}/{total} ({percentage}%)"
        
        # Add current item if there's space
        if current_item:
            # Calculate available space for filename
            base_len = len(progress_text)
            separator = " - "
            available_space = max_width - base_len - len(separator)
            
            if available_space > 10:  # Only show filename if we have reasonable space
                # Truncate filename if too long
                if len(current_item) > available_space:
                    truncate_at = max(1, available_space - 3)
                    current_item = "..." + current_item[-truncate_at:]
                
                progress_text += separator + current_item
        
        return progress_text