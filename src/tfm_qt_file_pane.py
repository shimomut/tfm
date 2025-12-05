"""
Qt File Pane Widget for TFM

This module implements the file pane widget for displaying file listings
in TFM's Qt GUI mode.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QHeaderView, QAbstractItemView, QMenu
)
from PySide6.QtCore import Qt, Signal, QMimeData, QUrl, QPoint
from PySide6.QtGui import QFont, QColor, QDrag, QAction
from typing import List, Dict, Any
from pathlib import Path

from src.tfm_qt_colors import get_file_color, get_qt_colors


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
    files_dropped = Signal(list, str)  # Emitted when files are dropped (file_paths, target_dir)
    context_action_triggered = Signal(str)  # Emitted when a context menu action is triggered
    
    def __init__(self, parent=None):
        """Initialize the file pane widget."""
        super().__init__(parent)
        
        # State
        self.files = []  # List of Path objects
        self.selected_files = set()  # Set of selected file paths (strings)
        self.current_index = 0  # Current cursor position
        self.is_active = False  # Whether this pane is active
        self.color_scheme = 'dark'  # Default color scheme
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
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
        
        # Enable drag from table
        self.table.setDragEnabled(True)
        self.table.setDragDropMode(QAbstractItemView.DragDrop)
        self.table.setDefaultDropAction(Qt.CopyAction)
        
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
    
    def update_files(self, files: List[Path], force_full_update: bool = False):
        """
        Update the file listing with incremental updates.
        
        Uses incremental updates when possible to avoid full table rebuilds,
        which improves performance for large directories.
        
        Args:
            files: List of Path objects to display
            force_full_update: If True, force a full table rebuild
        """
        old_files = self.files
        self.files = files
        
        # Check if we can do an incremental update
        can_incremental = (
            not force_full_update and
            len(old_files) == len(files) and
            self.table.rowCount() == len(files)
        )
        
        if can_incremental:
            # Incremental update - only update changed rows
            self._incremental_update(old_files, files)
        else:
            # Full update - rebuild entire table
            self._full_update(files)
        
        # Restore selection
        self._restore_selection()
        
        # Set current row
        if 0 <= self.current_index < len(files):
            self.table.setCurrentCell(self.current_index, 0)
    
    def _incremental_update(self, old_files: List[Path], new_files: List[Path]):
        """
        Perform incremental update of file listing.
        
        Only updates rows where the file has changed.
        
        Args:
            old_files: Previous file list
            new_files: New file list
        """
        for row, (old_path, new_path) in enumerate(zip(old_files, new_files)):
            # Check if this row needs updating
            if old_path != new_path or self._file_needs_update(old_path, new_path):
                self._update_row(row, new_path)
    
    def _file_needs_update(self, old_path: Path, new_path: Path) -> bool:
        """
        Check if a file row needs updating.
        
        Compares file metadata to determine if the row should be updated.
        
        Args:
            old_path: Previous file path
            new_path: New file path
        
        Returns:
            True if the row needs updating
        """
        # If paths are different, definitely needs update
        if old_path != new_path:
            return True
        
        # Check if metadata has changed
        try:
            old_stat = old_path.stat()
            new_stat = new_path.stat()
            
            # Compare size and modification time
            return (old_stat.st_size != new_stat.st_size or
                    old_stat.st_mtime != new_stat.st_mtime)
        except (OSError, Exception):
            # If we can't stat, assume it needs update
            return True
    
    def _full_update(self, files: List[Path]):
        """
        Perform full update of file listing.
        
        Clears and rebuilds the entire table.
        
        Args:
            files: List of files to display
        """
        # Disable updates during bulk changes for better performance
        self.table.setUpdatesEnabled(False)
        
        try:
            # Clear table
            self.table.setRowCount(0)
            
            # Populate table
            self.table.setRowCount(len(files))
            
            for row, file_path in enumerate(files):
                self._update_row(row, file_path)
        finally:
            # Re-enable updates
            self.table.setUpdatesEnabled(True)
    
    def _update_row(self, row: int, file_path: Path):
        """
        Update a single row in the table.
        
        Args:
            row: Row index
            file_path: File path to display
        """
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
    
    def _format_size(self, file_path: Path) -> str:
        """
        Format file size for display.
        
        Handles both local and S3 paths.
        
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
        except (OSError, PermissionError, Exception):
            # Catch all exceptions including S3-specific errors
            return "???"
    
    def _format_date(self, file_path: Path) -> str:
        """
        Format modification date for display.
        
        Handles both local and S3 paths.
        
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
        except (OSError, PermissionError, Exception):
            # Catch all exceptions including S3-specific errors
            return "???"
    
    def _format_permissions(self, file_path: Path) -> str:
        """
        Format file permissions for display.
        
        For S3 paths, returns a simplified representation since S3 doesn't
        have traditional Unix permissions.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Formatted permissions string (e.g., "rwxr-xr-x" for local, "rw-rw-rw-" for S3)
        """
        try:
            import stat
            
            # Check if this is an S3 path
            if hasattr(file_path, '_impl') and hasattr(file_path._impl, 'get_scheme'):
                if file_path._impl.get_scheme() == 's3':
                    # S3 objects don't have traditional permissions
                    # Show simplified representation
                    if file_path.is_dir():
                        return "rwxrwxrwx"  # Directories are accessible
                    else:
                        return "rw-rw-rw-"  # Files are readable/writable
            
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
        except (OSError, PermissionError, Exception):
            # Catch all exceptions including S3-specific errors
            return "?????????"
    
    def _apply_file_coloring(self, row: int, file_path: Path):
        """
        Apply coloring to a file row based on file type.
        
        Handles both local and S3 paths.
        
        Args:
            row: Row index in the table
            file_path: Path to the file
        """
        # Determine file type
        file_type = 'regular'
        
        if file_path.is_dir():
            file_type = 'directory'
        elif file_path.is_symlink():
            file_type = 'symlink'
        else:
            # Check if executable (only for local files)
            try:
                # S3 paths don't support os.access, so check if it's a local path
                is_s3 = hasattr(file_path, '_impl') and hasattr(file_path._impl, 'get_scheme') and file_path._impl.get_scheme() == 's3'
                
                if not is_s3 and file_path.is_file() and os.access(file_path, os.X_OK):
                    file_type = 'executable'
            except (OSError, Exception):
                # Ignore errors when checking executability
                pass
        
        # Get color for file type using current color scheme
        color = get_file_color(file_type, self.color_scheme)
        
        # Apply color to all cells in the row
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
    
    def set_color_scheme(self, scheme: str):
        """
        Set the color scheme for this pane.
        
        Args:
            scheme: Color scheme name ('dark' or 'light')
        """
        self.color_scheme = scheme
        
        # Reapply colors to all files
        for row, file_path in enumerate(self.files):
            self._apply_file_coloring(row, file_path)
    
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
    
    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        # Accept drags with file URLs
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move event."""
        # Accept drags with file URLs
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop event."""
        # Get dropped file URLs
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            # Extract file paths from URLs
            file_paths = []
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_paths.append(url.toLocalFile())
            
            if file_paths:
                # Get target directory (current directory of this pane)
                target_dir = str(self.files[0].parent) if self.files else ""
                
                # Emit signal with dropped files and target directory
                self.files_dropped.emit(file_paths, target_dir)
                event.acceptProposedAction()
                return
        
        event.ignore()
    
    def mousePressEvent(self, event):
        """Handle mouse press event for drag initiation."""
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move event for drag initiation."""
        # Check if we should start a drag
        if not (event.buttons() & Qt.LeftButton):
            super().mouseMoveEvent(event)
            return
        
        if not hasattr(self, '_drag_start_position'):
            super().mouseMoveEvent(event)
            return
        
        # Check if we've moved far enough to start a drag
        from PySide6.QtWidgets import QApplication
        if (event.pos() - self._drag_start_position).manhattanLength() < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return
        
        # Start drag operation
        selected = self.get_selected_files()
        if not selected:
            super().mouseMoveEvent(event)
            return
        
        # Create mime data with file URLs
        mime_data = QMimeData()
        urls = []
        for file_path in selected:
            # Only add local files to drag (not S3 or remote)
            if not file_path.is_remote():
                urls.append(QUrl.fromLocalFile(str(file_path)))
        
        if urls:
            mime_data.setUrls(urls)
            
            # Create drag object
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # Execute drag
            drag.exec_(Qt.CopyAction | Qt.MoveAction)
        
        super().mouseMoveEvent(event)
    
    def _show_context_menu(self, position: QPoint):
        """
        Show context menu for files.
        
        Args:
            position: Position where the context menu was requested
        """
        # Create context menu
        menu = QMenu(self)
        
        # Get selected files
        selected = self.get_selected_files()
        has_selection = len(selected) > 0
        
        # File operations
        if has_selection:
            # Copy action
            copy_action = QAction("Copy (F5)", self)
            copy_action.triggered.connect(lambda: self.context_action_triggered.emit('copy'))
            menu.addAction(copy_action)
            
            # Move action
            move_action = QAction("Move (F6)", self)
            move_action.triggered.connect(lambda: self.context_action_triggered.emit('move'))
            menu.addAction(move_action)
            
            # Delete action
            delete_action = QAction("Delete (F8)", self)
            delete_action.triggered.connect(lambda: self.context_action_triggered.emit('delete'))
            menu.addAction(delete_action)
            
            menu.addSeparator()
            
            # Rename action (only for single selection)
            if len(selected) == 1:
                rename_action = QAction("Rename (F2)", self)
                rename_action.triggered.connect(lambda: self.context_action_triggered.emit('rename'))
                menu.addAction(rename_action)
            
            menu.addSeparator()
        
        # View operations
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(lambda: self.context_action_triggered.emit('refresh'))
        menu.addAction(refresh_action)
        
        menu.addSeparator()
        
        # Selection operations
        select_all_action = QAction("Select All", self)
        select_all_action.triggered.connect(lambda: self.context_action_triggered.emit('select_all'))
        menu.addAction(select_all_action)
        
        if has_selection:
            clear_selection_action = QAction("Clear Selection", self)
            clear_selection_action.triggered.connect(lambda: self.context_action_triggered.emit('clear_selection'))
            menu.addAction(clear_selection_action)
        
        menu.addSeparator()
        
        # New operations
        new_file_action = QAction("New File", self)
        new_file_action.triggered.connect(lambda: self.context_action_triggered.emit('new_file'))
        menu.addAction(new_file_action)
        
        new_dir_action = QAction("New Directory (F7)", self)
        new_dir_action.triggered.connect(lambda: self.context_action_triggered.emit('new_directory'))
        menu.addAction(new_dir_action)
        
        # Show the menu at the cursor position
        menu.exec_(self.mapToGlobal(position))
