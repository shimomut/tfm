"""
Qt Header Widget for TFM

This module implements the header widget for displaying directory paths
in TFM's Qt GUI mode.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class HeaderWidget(QWidget):
    """
    Header widget for displaying directory paths.
    
    This widget displays the current directory path for each pane
    and highlights the active pane.
    """
    
    def __init__(self, parent=None):
        """Initialize the header widget."""
        super().__init__(parent)
        
        # State
        self.left_path = ""
        self.right_path = ""
        self.active_pane = "left"
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Left pane path label
        self.left_label = QLabel()
        self.left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        font = QFont()
        font.setBold(True)
        self.left_label.setFont(font)
        
        # Right pane path label
        self.right_label = QLabel()
        self.right_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.right_label.setFont(font)
        
        # Add labels to layout with equal stretch
        layout.addWidget(self.left_label, 1)
        layout.addWidget(self.right_label, 1)
        
        # Set initial styling
        self._update_styling()
    
    def set_paths(self, left_path: str, right_path: str):
        """
        Set the directory paths for both panes.
        
        Args:
            left_path: Path to display for left pane
            right_path: Path to display for right pane
        """
        self.left_path = left_path
        self.right_path = right_path
        
        # Update labels
        self.left_label.setText(left_path)
        self.right_label.setText(right_path)
    
    def set_active_pane(self, pane: str):
        """
        Set which pane is active.
        
        Args:
            pane: "left" or "right"
        """
        self.active_pane = pane
        self._update_styling()
    
    def _update_styling(self):
        """Update the styling to highlight the active pane."""
        # Active pane styling - blue background
        active_style = """
            QLabel {
                background-color: #4A90E2;
                color: white;
                padding: 5px;
                border-radius: 3px;
            }
        """
        
        # Inactive pane styling - light gray background
        inactive_style = """
            QLabel {
                background-color: #F0F0F0;
                color: #333333;
                padding: 5px;
                border-radius: 3px;
            }
        """
        
        # Apply styling based on active pane
        if self.active_pane == "left":
            self.left_label.setStyleSheet(active_style)
            self.right_label.setStyleSheet(inactive_style)
        else:
            self.left_label.setStyleSheet(inactive_style)
            self.right_label.setStyleSheet(active_style)
