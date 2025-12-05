"""
Qt Main Window for TFM

This module implements the main window for TFM's Qt GUI mode, providing
the top-level window with menu bar, toolbar, status bar, and dual-pane layout.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QMenuBar, 
    QToolBar, QStatusBar, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, QSettings, QSize, QPoint
from PySide6.QtGui import QAction, QKeySequence


class TFMMainWindow(QMainWindow):
    """
    Main window for TFM Qt GUI.
    
    This class provides the top-level window with:
    - Menu bar with File, Edit, View, Tools, Help menus
    - Toolbar with common actions
    - Status bar for messages
    - Central widget with splitter for dual panes
    - Window geometry save/restore
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Window settings
        self.setWindowTitle("TFM - File Manager")
        self.setMinimumSize(800, 600)
        
        # Create central widget with splitter
        self._setup_central_widget()
        
        # Create menu bar
        self._setup_menu_bar()
        
        # Create toolbar
        self._setup_toolbar()
        
        # Create status bar
        self._setup_status_bar()
        
        # Restore window geometry from saved settings
        self._restore_geometry()
    
    def _setup_central_widget(self):
        """Set up the central widget with splitter for dual panes."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create splitter for dual panes
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)  # Prevent panes from collapsing
        
        # Placeholder widgets for panes (will be replaced by actual pane widgets)
        self.left_pane_container = QWidget()
        self.right_pane_container = QWidget()
        
        self.splitter.addWidget(self.left_pane_container)
        self.splitter.addWidget(self.right_pane_container)
        
        # Set equal sizes for both panes
        self.splitter.setSizes([400, 400])
        
        layout.addWidget(self.splitter)
    
    def _setup_menu_bar(self):
        """Set up the menu bar with File, Edit, View, Tools, Help menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New file action
        new_file_action = QAction("&New File", self)
        new_file_action.setShortcut(QKeySequence.New)
        new_file_action.setStatusTip("Create a new file")
        file_menu.addAction(new_file_action)
        
        # New directory action
        new_dir_action = QAction("New &Directory", self)
        new_dir_action.setShortcut(QKeySequence("F7"))
        new_dir_action.setStatusTip("Create a new directory")
        file_menu.addAction(new_dir_action)
        
        file_menu.addSeparator()
        
        # Quit action
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.setStatusTip("Exit the application")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Copy action
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence("F5"))
        copy_action.setStatusTip("Copy selected files")
        edit_menu.addAction(copy_action)
        
        # Move action
        move_action = QAction("&Move", self)
        move_action.setShortcut(QKeySequence("F6"))
        move_action.setStatusTip("Move selected files")
        edit_menu.addAction(move_action)
        
        # Delete action
        delete_action = QAction("&Delete", self)
        delete_action.setShortcut(QKeySequence("F8"))
        delete_action.setStatusTip("Delete selected files")
        edit_menu.addAction(delete_action)
        
        edit_menu.addSeparator()
        
        # Rename action
        rename_action = QAction("&Rename", self)
        rename_action.setShortcut(QKeySequence("F2"))
        rename_action.setStatusTip("Rename selected file")
        edit_menu.addAction(rename_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Refresh action
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.setStatusTip("Refresh file listings")
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        # Show hidden files action
        show_hidden_action = QAction("Show &Hidden Files", self)
        show_hidden_action.setCheckable(True)
        show_hidden_action.setStatusTip("Toggle display of hidden files")
        view_menu.addAction(show_hidden_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Search action
        search_action = QAction("&Search", self)
        search_action.setShortcut(QKeySequence.Find)
        search_action.setStatusTip("Search for files")
        tools_menu.addAction(search_action)
        
        # Preferences action
        prefs_action = QAction("&Preferences", self)
        prefs_action.setShortcut(QKeySequence.Preferences)
        prefs_action.setStatusTip("Configure application settings")
        tools_menu.addAction(prefs_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("About TFM")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Set up the toolbar with common actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Add common actions to toolbar
        # Copy
        copy_action = QAction("Copy", self)
        copy_action.setStatusTip("Copy selected files (F5)")
        toolbar.addAction(copy_action)
        
        # Move
        move_action = QAction("Move", self)
        move_action.setStatusTip("Move selected files (F6)")
        toolbar.addAction(move_action)
        
        # Delete
        delete_action = QAction("Delete", self)
        delete_action.setStatusTip("Delete selected files (F8)")
        toolbar.addAction(delete_action)
        
        toolbar.addSeparator()
        
        # Refresh
        refresh_action = QAction("Refresh", self)
        refresh_action.setStatusTip("Refresh file listings")
        toolbar.addAction(refresh_action)
        
        # Search
        search_action = QAction("Search", self)
        search_action.setStatusTip("Search for files")
        toolbar.addAction(search_action)
    
    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _restore_geometry(self):
        """Restore window geometry from saved settings."""
        settings = QSettings("TFM", "FileManager")
        
        # Restore window size
        size = settings.value("window/size", QSize(1200, 800))
        self.resize(size)
        
        # Restore window position
        pos = settings.value("window/position")
        if pos is not None:
            # Check if position is on screen
            screen_geometry = self.screen().availableGeometry()
            if screen_geometry.contains(pos):
                self.move(pos)
            else:
                # Position is off-screen, center the window
                self._center_window()
        else:
            # No saved position, center the window
            self._center_window()
        
        # Restore splitter sizes
        splitter_sizes = settings.value("splitter/sizes")
        if splitter_sizes:
            self.splitter.setSizes(splitter_sizes)
    
    def _center_window(self):
        """Center the window on the screen."""
        screen_geometry = self.screen().availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
    
    def _save_geometry(self):
        """Save window geometry to settings."""
        settings = QSettings("TFM", "FileManager")
        
        # Save window size
        settings.setValue("window/size", self.size())
        
        # Save window position
        settings.setValue("window/position", self.pos())
        
        # Save splitter sizes
        settings.setValue("splitter/sizes", self.splitter.sizes())
    
    def _show_about(self):
        """Show the About dialog."""
        QMessageBox.about(
            self,
            "About TFM",
            "<h3>TFM - File Manager</h3>"
            "<p>A dual-pane file manager with both TUI and GUI modes.</p>"
            "<p>Version 1.0</p>"
        )
    
    def closeEvent(self, event):
        """Handle window close event to save geometry."""
        self._save_geometry()
        event.accept()
    
    def set_left_pane_widget(self, widget):
        """
        Set the left pane widget.
        
        Args:
            widget: The widget to use for the left pane
        """
        # Remove old widget
        old_widget = self.splitter.widget(0)
        if old_widget:
            old_widget.setParent(None)
        
        # Add new widget
        self.splitter.insertWidget(0, widget)
        self.left_pane_container = widget
    
    def set_right_pane_widget(self, widget):
        """
        Set the right pane widget.
        
        Args:
            widget: The widget to use for the right pane
        """
        # Remove old widget
        old_widget = self.splitter.widget(1)
        if old_widget:
            old_widget.setParent(None)
        
        # Add new widget
        self.splitter.insertWidget(1, widget)
        self.right_pane_container = widget
