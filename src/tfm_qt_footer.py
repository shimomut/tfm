"""
Qt Footer Widget for TFM

This module implements the footer widget for displaying file counts and
sort information in TFM's Qt GUI mode.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class FooterWidget(QWidget):
    """
    Footer widget for displaying file counts and sort info.
    
    This widget displays:
    - Directory/file counts for each pane
    - Sort mode and filter info
    - Highlights the active pane
    """
    
    def __init__(self, parent=None):
        """Initialize the footer widget."""
        super().__init__(parent)
        
        # State
        self.left_info = ""
        self.right_info = ""
        self.active_pane = "left"
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Left pane info label
        self.left_label = QLabel()
        self.left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        font = QFont()
        font.setPointSize(9)
        self.left_label.setFont(font)
        
        # Right pane info label
        self.right_label = QLabel()
        self.right_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.right_label.setFont(font)
        
        # Add labels to layout with equal stretch
        layout.addWidget(self.left_label, 1)
        layout.addWidget(self.right_label, 1)
        
        # Set initial styling
        self._update_styling()
    
    def set_info(self, left_info: str, right_info: str):
        """
        Set the information text for both panes.
        
        Args:
            left_info: Information text for left pane (e.g., "5 dirs, 12 files")
            right_info: Information text for right pane
        """
        self.left_info = left_info
        self.right_info = right_info
        
        # Update labels
        self.left_label.setText(left_info)
        self.right_label.setText(right_info)
    
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
        # Active pane styling - darker background
        active_style = """
            QLabel {
                background-color: #E8F4F8;
                color: #2C5F7F;
                padding: 5px;
                border-radius: 3px;
                font-weight: bold;
            }
        """
        
        # Inactive pane styling - lighter background
        inactive_style = """
            QLabel {
                background-color: #F8F8F8;
                color: #666666;
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
