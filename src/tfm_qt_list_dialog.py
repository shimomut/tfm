"""
Qt List Selection Dialog for TFM

This module provides a custom list selection dialog with search/filter support
for the Qt GUI backend.
"""

from typing import List, Dict, Optional, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QLabel, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal


class ListSelectionDialog(QDialog):
    """
    Custom list selection dialog with search/filter support.
    
    Supports both single and multi-selection modes with real-time filtering.
    """
    
    def __init__(self, parent=None, title: str = "Select Item", 
                 message: str = "", items: List[Dict] = None,
                 multi_select: bool = False):
        """
        Initialize the list selection dialog.
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Message to display above the list
            items: List of items (dicts with 'label' and optional 'value' keys)
            multi_select: Whether to allow multiple selection
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)
        
        self.items = items or []
        self.multi_select = multi_select
        self.selected_items = []
        
        self._setup_ui(message)
        self._populate_list()
    
    def _setup_ui(self, message: str):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Message label
        if message:
            message_label = QLabel(message)
            message_label.setWordWrap(True)
            layout.addWidget(message_label)
        
        # Search/filter input
        search_layout = QHBoxLayout()
        search_label = QLabel("Filter:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter items...")
        self.search_input.textChanged.connect(self._filter_items)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # List widget
        self.list_widget = QListWidget()
        if self.multi_select:
            self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        else:
            self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Double-click to accept (for single selection)
        if not self.multi_select:
            self.list_widget.itemDoubleClicked.connect(self.accept)
        
        layout.addWidget(self.list_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _populate_list(self):
        """Populate the list widget with items."""
        self.list_widget.clear()
        
        for item in self.items:
            label = item.get('label', str(item))
            list_item = QListWidgetItem(label)
            list_item.setData(Qt.UserRole, item)
            self.list_widget.addItem(list_item)
    
    def _filter_items(self, filter_text: str):
        """
        Filter items based on search text.
        
        Args:
            filter_text: Text to filter by
        """
        filter_text = filter_text.lower()
        
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item_text = item.text().lower()
            
            # Show item if filter text is in item text
            item.setHidden(filter_text not in item_text)
    
    def get_selected_items(self) -> List[Dict]:
        """
        Get the selected items.
        
        Returns:
            List of selected item dictionaries
        """
        selected = []
        for item in self.list_widget.selectedItems():
            item_data = item.data(Qt.UserRole)
            if item_data:
                selected.append(item_data)
        
        return selected
    
    def accept(self):
        """Handle dialog acceptance."""
        self.selected_items = self.get_selected_items()
        super().accept()
    
    @staticmethod
    def get_selection(parent=None, title: str = "Select Item",
                     message: str = "", items: List[Dict] = None,
                     multi_select: bool = False) -> Optional[List[Dict]]:
        """
        Show the dialog and return selected items.
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Message to display
            items: List of items to choose from
            multi_select: Whether to allow multiple selection
        
        Returns:
            List of selected items, or None if cancelled
        """
        dialog = ListSelectionDialog(parent, title, message, items, multi_select)
        
        if dialog.exec() == QDialog.Accepted:
            return dialog.selected_items
        
        return None
