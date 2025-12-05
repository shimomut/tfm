"""
Qt Progress Dialog for TFM

This module provides a custom progress dialog for long-running operations
with support for progress updates, current file display, and cancellation.
"""

import time
from typing import Optional, Callable
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal


class ProgressDialog(QDialog):
    """
    Custom progress dialog for long operations.
    
    Supports progress bar updates, current file name display, and cancellation.
    """
    
    # Signal emitted when user cancels the operation
    cancelled = Signal()
    
    def __init__(self, parent=None, title: str = "Progress",
                 operation: str = "Processing", cancelable: bool = True,
                 throttle_ms: int = 100):
        """
        Initialize the progress dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            operation: Operation name (e.g., "Copying files")
            cancelable: Whether the operation can be cancelled
            throttle_ms: Minimum milliseconds between UI updates (default: 100ms)
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        
        # Prevent closing with X button if not cancelable
        if not cancelable:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        
        self.operation = operation
        self.cancelable = cancelable
        self.is_cancelled = False
        
        # Throttling state
        self.throttle_ms = throttle_ms
        self._last_update_time = 0
        self._pending_update = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Operation label
        self.operation_label = QLabel(self.operation)
        self.operation_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.operation_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Current file/message label
        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        # Cancel button (if cancelable)
        if self.cancelable:
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.clicked.connect(self._on_cancel)
            button_layout.addWidget(self.cancel_button)
            
            layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def update_progress(self, current: int, total: int, message: str = "", force: bool = False):
        """
        Update the progress dialog with throttling.
        
        Updates are throttled to avoid excessive UI updates that can cause lag.
        The last update is always applied to ensure the final state is shown.
        
        Args:
            current: Current progress value
            total: Total progress value
            message: Current status message (e.g., current file name)
            force: If True, bypass throttling and update immediately
        """
        current_time = time.time() * 1000  # Convert to milliseconds
        time_since_last = current_time - self._last_update_time
        
        # Check if we should throttle this update
        should_update = (
            force or
            time_since_last >= self.throttle_ms or
            current == total  # Always update on completion
        )
        
        if should_update:
            self._apply_update(current, total, message)
            self._last_update_time = current_time
            self._pending_update = None
        else:
            # Store pending update to apply later
            self._pending_update = (current, total, message)
    
    def _apply_update(self, current: int, total: int, message: str):
        """
        Apply a progress update to the UI.
        
        Args:
            current: Current progress value
            total: Total progress value
            message: Current status message
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            
            # Update progress bar text
            self.progress_bar.setFormat(f"{current}/{total} ({percentage}%)")
        else:
            # Indeterminate progress
            self.progress_bar.setMaximum(0)
            self.progress_bar.setFormat("")
        
        # Update message
        if message:
            self.message_label.setText(message)
        
        # Process events to keep UI responsive
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
    
    def flush_pending_update(self):
        """
        Flush any pending throttled update.
        
        Call this when an operation completes to ensure the final
        progress state is displayed.
        """
        if self._pending_update:
            current, total, message = self._pending_update
            self._apply_update(current, total, message)
            self._pending_update = None
    
    def set_operation(self, operation: str):
        """
        Set the operation name.
        
        Args:
            operation: Operation name
        """
        self.operation = operation
        self.operation_label.setText(operation)
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.is_cancelled = True
        self.cancelled.emit()
        
        # Disable cancel button to prevent multiple clicks
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Cancelling...")
    
    def was_cancelled(self) -> bool:
        """
        Check if the operation was cancelled.
        
        Returns:
            True if cancelled, False otherwise
        """
        return self.is_cancelled
    
    def auto_close(self):
        """Automatically close the dialog when operation completes."""
        # Flush any pending updates before closing
        self.flush_pending_update()
        self.accept()
    
    @staticmethod
    def create_progress(parent=None, title: str = "Progress",
                       operation: str = "Processing",
                       cancelable: bool = True) -> 'ProgressDialog':
        """
        Create and show a progress dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            operation: Operation name
            cancelable: Whether the operation can be cancelled
        
        Returns:
            ProgressDialog instance
        """
        dialog = ProgressDialog(parent, title, operation, cancelable)
        dialog.show()
        return dialog
