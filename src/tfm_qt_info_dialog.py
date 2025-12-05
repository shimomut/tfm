"""
Qt Info Dialog for TFM

This module provides a custom information dialog with scrolling support
for displaying formatted information.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
)
from PySide6.QtCore import Qt


class InfoDialog(QDialog):
    """
    Custom information dialog with scrolling support.
    
    Displays formatted information with support for long content.
    """
    
    def __init__(self, parent=None, title: str = "Information",
                 message: str = "", content: str = ""):
        """
        Initialize the info dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Brief message to display above content
            content: Main content to display (supports HTML/plain text)
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self._setup_ui(message, content)
    
    def _setup_ui(self, message: str, content: str):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Message label (optional)
        if message:
            message_label = QLabel(message)
            message_label.setWordWrap(True)
            layout.addWidget(message_label)
        
        # Text edit for content (read-only with scrolling)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        
        # Check if content looks like HTML
        if content.strip().startswith('<'):
            self.text_edit.setHtml(content)
        else:
            self.text_edit.setPlainText(content)
        
        layout.addWidget(self.text_edit)
        
        # OK button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    @staticmethod
    def show_info(parent=None, title: str = "Information",
                  message: str = "", content: str = ""):
        """
        Show the info dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Brief message
            content: Main content to display
        """
        dialog = InfoDialog(parent, title, message, content)
        dialog.exec()
