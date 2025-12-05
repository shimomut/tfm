"""
Qt File Pane Widget for TFM

This module implements the file pane widget for displaying file listings
in TFM's Qt GUI mode.
"""

from PySide6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from typing import List, Dict, Any
from pathlib import Path


class FilePaneWidget(QWidget):
    """
    File pane widget for displaying file listings.
    
    This widget displays files in a table with columns for:
    - Filename
    - Size
    - Date modified
    - Permissions
    
    Supports:
    - Single selection
    - Multi-selection (Ctrl+click)
    - Range selection (Shift+click)
    - Keyboard navigation
    """
    
    # Signals
    file_selected = Signal(int)  # Emitted when a file is selected (index)
    file_activated = Signal(int)  # Emitted when a file is double-clicked or Enter pressed
    selection_changed = Signal()  # Emitted when selection changes
    
    def __init__(self, parent=None):
        """Initialize the file pane widget."""
        super().__init__(parent)
        
        # State
        self.files = []  # List of Path objects
        self.selected_files = set()  # Set of selected file paths (strings)
        self.current_index = 0  # Current cursor position
        self.is_active = False  # Whether this pane is active
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Size", "Date", "Permissions"])
        
        # Configure table
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        # Set column resize modes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Name column stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Size
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Permissions
        
        # Use monospace font for better alignment
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        self.table.setFont(font)
        
        # Connect signals
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table.currentCellChanged.connect(self._on_current_cell_changed)
        
        layout.addWidget(self.table)
    
    def update_files(self, files: List[Path]):
        """
        Update the file listing.
        
        Args:
            files: List of Path objects to display
        """
        self.files = files
        
        # Clear table
        self.table.setRowCount(0)
        
        # Populate table
        self.table.setRowCount(len(files))
        
        for row, file_path in enumerate(files):
            # Name column
            name_item = QTableWidgetItem(file_path.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # Read-only
            
            # Add directory indicator
            if file_path.is_dir():
                name_item.setText(f"📁 {file_path.name}")
            
            self.table.setItem(row, 0, name_item)
            
            # Size column
            size_str = self._format_size(file_path)
            size_item = QTableWidgetItem(size_str)
            size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 1, size_item)
            
            # Date column
            date_str = self._format_date(file_path)
            date_item = QTableWidgetItem(date_str)
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, date_item)
            
            # Permissions column
            perms_str = self._format_permissions(file_path)
            perms_item = QTableWidgetItem(perms_str)
            perms_item.setFlags(perms_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, perms_item)
            
            # Apply coloring based on file type
            self._apply_file_coloring(row, file_path)
        
        # Restore selection
        self._restore_selection()
        
        # Set current row
        if 0 <= self.current_index < len(files):
            self.table.setCurrentCell(self.current_index, 0)
    
    def _format_size(self, file_path: Path) -> str:
        """
        Format file size for display.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Formatted size string
        """
        try:
            if file_path.is_dir():
                return "<DIR>"
            
            size = file_path.stat().st_size
            
            # Format with appropriate units
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size / (1024 * 1024):.1f} MB"
            else:
                return f"{size / (1024 * 1024 * 1024):.1f} GB"
        except (OSError, PermissionError):
            return "???"
    
    def _format_date(self, file_path: Path) -> str:
        """
        Format modification date for display.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Formatted date string
        """
        try:
            import datetime
            mtime = file_path.stat().st_mtime
            dt = datetime.datetime.fromtimestamp(mtime)
            return dt.strftime("%Y-%m-%d %H:%M")
        except (OSError, PermissionError):
            return "???"
    
    def _format_permissions(self, file_path: Path) -> str:
        """
        Format file permissions for display.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Formatted permissions string (e.g., "rwxr-xr-x")
        """
        try:
            import stat
            st = file_path.stat()
            mode = st.st_mode
            
            # Build permission string
            perms = []
            
            # Owner permissions
            perms.append('r' if mode & stat.S_IRUSR else '-')
            perms.append('w' if mode & stat.S_IWUSR else '-')
            perms.append('x' if mode & stat.S_IXUSR else '-')
            
            # Group permissions
            perms.append('r' if mode & stat.S_IRGRP else '-')
            perms.append('w' if mode & stat.S_IWGRP else '-')
            perms.append('x' if mode & stat.S_IXGRP else '-')
            
            # Other permissions
            perms.append('r' if mode & stat.S_IROTH else '-')
            perms.append('w' if mode & stat.S_IWOTH else '-')
            perms.append('x' if mode & stat.S_IXOTH else '-')
            
            return ''.join(perms)
        except (OSError, PermissionError):
            return "?????????"
    
    def _apply_file_coloring(self, row: int, file_path: Path):
        """
        Apply coloring to a file row based on file type.
        
        Args:
            row: Row index in the table
            file_path: Path to the file
        """
        import os
        
        # Determine color based on file type
        color = None
        
        if file_path.is_dir():
            # Directories - blue
            color = QColor(100, 149, 237)  # Cornflower blue
        elif file_path.is_symlink():
            # Symlinks - cyan
            color = QColor(0, 255, 255)
        elif file_path.is_file() and os.access(file_path, os.X_OK):
            # Executable files - green
            color = QColor(50, 205, 50)  # Lime green
        
        # Apply color to all cells in the row
        if color:
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setForeground(color)
    
    def _restore_selection(self):
        """Restore multi-selection state after updating files."""
        for row, file_path in enumerate(self.files):
            if str(file_path) in self.selected_files:
                self.table.selectRow(row)
    
    def _on_selection_changed(self):
        """Handle selection change in the table."""
        # Update selected_files set
        self.selected_files.clear()
        for item in self.table.selectedItems():
            row = item.row()
            if 0 <= row < len(self.files):
                self.selected_files.add(str(self.files[row]))
        
        # Emit signal
        self.selection_changed.emit()
    
    def _on_cell_double_clicked(self, row: int, column: int):
        """Handle double-click on a cell."""
        if 0 <= row < len(self.files):
            self.file_activated.emit(row)
    
    def _on_current_cell_changed(self, current_row: int, current_col: int, 
                                 previous_row: int, previous_col: int):
        """Handle current cell change (cursor movement)."""
        if 0 <= current_row < len(self.files):
            self.current_index = current_row
            self.file_selected.emit(current_row)
    
    def set_active(self, active: bool):
        """
        Set whether this pane is active.
        
        Args:
            active: True if this pane should be highlighted as active
        """
        self.is_active = active
        
        # Update visual appearance
        if active:
            # Highlight active pane with border
            self.setStyleSheet("FilePaneWidget { border: 2px solid #4A90E2; }")
        else:
            # Remove border for inactive pane
            self.setStyleSheet("FilePaneWidget { border: 1px solid #CCCCCC; }")
    
    def get_selected_files(self) -> List[Path]:
        """
        Get list of selected files.
        
        Returns:
            List of Path objects for selected files
        """
        selected = []
        for file_path in self.files:
            if str(file_path) in self.selected_files:
                selected.append(file_path)
        return selected
    
    def get_current_file(self) -> Path:
        """
        Get the file at the current cursor position.
        
        Returns:
            Path object for the current file, or None if no files
        """
        if 0 <= self.current_index < len(self.files):
            return self.files[self.current_index]
        return None
    
    def clear_selection(self):
        """Clear all file selections."""
        self.table.clearSelection()
        self.selected_files.clear()
    
    def select_all(self):
        """Select all files."""
        self.table.selectAll()
    
    def keyPressEvent(self, event):
        """Handle key press events for keyboard navigation."""
        key = event.key()
        
        # Handle Enter/Return - activate current file
        if key in (Qt.Key_Return, Qt.Key_Enter):
            if 0 <= self.current_index < len(self.files):
                self.file_activated.emit(self.current_index)
            event.accept()
            return
        
        # Let table handle other keys (arrow keys, etc.)
        super().keyPressEvent(event)
