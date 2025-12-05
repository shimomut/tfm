"""
Qt Log Pane Widget for TFM

This module implements the log pane widget for displaying log messages
in TFM's Qt GUI mode.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor, QColor
from typing import List, Tuple


class LogPaneWidget(QWidget):
    """
    Log pane widget for displaying log messages.
    
    This widget displays log messages with:
    - Automatic scrolling
    - Message formatting with timestamps and sources
    - Color coding based on message source
    """
    
    def __init__(self, parent=None):
        """Initialize the log pane widget."""
        super().__init__(parent)
        
        # State
        self.messages = []  # List of (timestamp, source, message) tuples
        self.max_messages = 1000  # Maximum number of messages to keep
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create text edit for log display
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        
        # Use monospace font for better alignment
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        font.setPointSize(9)
        self.text_edit.setFont(font)
        
        # Set background color
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: none;
            }
        """)
        
        layout.addWidget(self.text_edit)
    
    def add_message(self, timestamp: str, source: str, message: str):
        """
        Add a log message.
        
        Args:
            timestamp: Message timestamp
            source: Message source (e.g., "COPY", "MOVE", "ERROR")
            message: Message text
        """
        # Add to messages list
        self.messages.append((timestamp, source, message))
        
        # Trim old messages if needed
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        # Format and append message
        formatted_message = self._format_message(timestamp, source, message)
        
        # Get color for source
        color = self._get_source_color(source)
        
        # Append to text edit
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Set text color
        format = cursor.charFormat()
        format.setForeground(color)
        cursor.setCharFormat(format)
        
        # Insert text
        cursor.insertText(formatted_message + "\n")
        
        # Auto-scroll to bottom
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()
    
    def update_messages(self, messages: List[Tuple[str, str, str]]):
        """
        Update the entire message list.
        
        Args:
            messages: List of (timestamp, source, message) tuples
        """
        self.messages = list(messages)
        
        # Clear text edit
        self.text_edit.clear()
        
        # Add all messages
        for timestamp, source, message in messages:
            formatted_message = self._format_message(timestamp, source, message)
            color = self._get_source_color(source)
            
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            
            format = cursor.charFormat()
            format.setForeground(color)
            cursor.setCharFormat(format)
            
            cursor.insertText(formatted_message + "\n")
        
        # Scroll to bottom
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
    
    def clear(self):
        """Clear all log messages."""
        self.messages.clear()
        self.text_edit.clear()
    
    def _format_message(self, timestamp: str, source: str, message: str) -> str:
        """
        Format a log message for display.
        
        Args:
            timestamp: Message timestamp
            source: Message source
            message: Message text
        
        Returns:
            Formatted message string
        """
        return f"{timestamp} [{source:>6}] {message}"
    
    def _get_source_color(self, source: str) -> QColor:
        """
        Get color for a message source.
        
        Args:
            source: Message source
        
        Returns:
            QColor for the source
        """
        # Color mapping for different sources
        color_map = {
            "ERROR": QColor(255, 100, 100),  # Red
            "WARN": QColor(255, 200, 100),   # Orange
            "INFO": QColor(100, 200, 255),   # Light blue
            "COPY": QColor(100, 255, 100),   # Green
            "MOVE": QColor(100, 255, 100),   # Green
            "DELETE": QColor(255, 150, 150), # Light red
            "SEARCH": QColor(200, 150, 255), # Purple
            "S3": QColor(255, 200, 50),      # Yellow
        }
        
        # Return color for source, or default gray
        return color_map.get(source, QColor(180, 180, 180))
