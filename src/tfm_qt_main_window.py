"""
Qt Main Window for TFM

This module implements the main window for TFM's Qt GUI mode, providing
the top-level window with menu bar, toolbar, status bar, and dual-pane layout.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QMenuBar, 
    QToolBar, QStatusBar, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, QSettings, QSize, QPoint, Signal, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut

from tfm_key_bindings import KeyBindingManager
from tfm_config import get_config, config_manager
from _config import Config


class TFMMainWindow(QMainWindow):
    """
    Main window for TFM Qt GUI.
    
    This class provides the top-level window with:
    - Menu bar with File, Edit, View, Tools, Help menus
    - Toolbar with common actions
    - Status bar for messages
    - Central widget with splitter for dual panes
    - Window geometry save/restore
    - Keyboard shortcuts mapped from TUI key bindings
    """
    
    # Signal emitted when an action is triggered via keyboard shortcut
    action_triggered = Signal(str)  # action name
    
    # Signal emitted when Tab key is pressed for pane switching
    switch_pane_requested = Signal()
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Window settings
        self.setWindowTitle("TFM - File Manager")
        self.setMinimumSize(800, 600)
        
        # Store shortcuts for later reference
        self.shortcuts = {}
        
        # Timer for debouncing geometry saves
        self._geometry_save_timer = QTimer()
        self._geometry_save_timer.setSingleShot(True)
        self._geometry_save_timer.setInterval(500)  # 500ms delay
        self._geometry_save_timer.timeout.connect(self._save_geometry_now)
        
        # Create central widget with splitter
        self._setup_central_widget()
        
        # Create menu bar
        self._setup_menu_bar()
        
        # Create toolbar
        self._setup_toolbar()
        
        # Create status bar
        self._setup_status_bar()
        
        # Set up keyboard shortcuts from TUI key bindings
        self._setup_keyboard_shortcuts()
        
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
        """
        Restore window geometry from saved settings.
        
        This method:
        1. Loads geometry from user configuration file first
        2. Falls back to QSettings if not in config
        3. Uses default geometry if no saved config exists
        4. Handles off-screen positions gracefully by centering
        """
        # Get configuration
        config = get_config()
        
        # Try to get geometry from user config first
        width = getattr(config, 'GUI_WINDOW_WIDTH', 1200)
        height = getattr(config, 'GUI_WINDOW_HEIGHT', 800)
        x = getattr(config, 'GUI_WINDOW_X', None)
        y = getattr(config, 'GUI_WINDOW_Y', None)
        
        # Validate and apply window size
        if width < 400:
            width = 1200
        if height < 300:
            height = 800
        
        self.resize(width, height)
        
        # Apply window position
        if x is not None and y is not None:
            # Check if position is on screen
            screen_geometry = self.screen().availableGeometry()
            pos = QPoint(x, y)
            
            # Check if the window would be visible at this position
            # (at least part of the window should be on screen)
            window_rect = self.frameGeometry()
            window_rect.moveTo(pos)
            
            if screen_geometry.intersects(window_rect):
                self.move(pos)
            else:
                # Position is off-screen, center the window
                self._center_window()
        else:
            # No saved position, center the window
            self._center_window()
        
        # Restore splitter sizes from QSettings (not in config file)
        settings = QSettings("TFM", "FileManager")
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
        """
        Schedule a geometry save (debounced).
        
        This method is called on resize/move events and schedules a save
        after a short delay to avoid excessive writes during window dragging.
        """
        # Restart the timer - this debounces rapid resize/move events
        self._geometry_save_timer.start()
    
    def _save_geometry_now(self):
        """
        Save window geometry to configuration file and QSettings.
        
        This method:
        1. Saves window size and position to user config file
        2. Saves splitter sizes to QSettings (not in config file)
        3. Handles save errors gracefully
        """
        try:
            # Get current geometry
            width = self.width()
            height = self.height()
            x = self.x()
            y = self.y()
            
            # Save to configuration file
            config_manager.save_gui_geometry(width, height, x, y)
            
            # Save splitter sizes to QSettings (not in config file)
            settings = QSettings("TFM", "FileManager")
            settings.setValue("splitter/sizes", self.splitter.sizes())
            
        except Exception as e:
            print(f"Warning: Could not save window geometry: {e}")
    
    def _show_about(self):
        """Show the About dialog."""
        QMessageBox.about(
            self,
            "About TFM",
            "<h3>TFM - File Manager</h3>"
            "<p>A dual-pane file manager with both TUI and GUI modes.</p>"
            "<p>Version 1.0</p>"
        )
    
    def resizeEvent(self, event):
        """Handle window resize event to save geometry."""
        super().resizeEvent(event)
        self._save_geometry()
    
    def moveEvent(self, event):
        """Handle window move event to save geometry."""
        super().moveEvent(event)
        self._save_geometry()
    
    def closeEvent(self, event):
        """Handle window close event to save geometry immediately."""
        # Cancel any pending save and save immediately
        self._geometry_save_timer.stop()
        self._save_geometry_now()
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
    
    def _setup_keyboard_shortcuts(self):
        """
        Set up keyboard shortcuts from TUI key bindings.
        
        This method creates QShortcut objects for all configured key bindings
        in Config.KEY_BINDINGS, mapping them to action signals that the backend
        can handle.
        """
        # Map of special key names to Qt key codes
        special_key_map = {
            'HOME': Qt.Key_Home,
            'END': Qt.Key_End,
            'PPAGE': Qt.Key_PageUp,
            'NPAGE': Qt.Key_PageDown,
            'UP': Qt.Key_Up,
            'DOWN': Qt.Key_Down,
            'LEFT': Qt.Key_Left,
            'RIGHT': Qt.Key_Right,
            'BACKSPACE': Qt.Key_Backspace,
            'DELETE': Qt.Key_Delete,
            'INSERT': Qt.Key_Insert,
            'F1': Qt.Key_F1,
            'F2': Qt.Key_F2,
            'F3': Qt.Key_F3,
            'F4': Qt.Key_F4,
            'F5': Qt.Key_F5,
            'F6': Qt.Key_F6,
            'F7': Qt.Key_F7,
            'F8': Qt.Key_F8,
            'F9': Qt.Key_F9,
            'F10': Qt.Key_F10,
            'F11': Qt.Key_F11,
            'F12': Qt.Key_F12,
        }
        
        # Iterate through all key bindings
        for action, binding in Config.KEY_BINDINGS.items():
            # Get keys for this action
            keys = KeyBindingManager.get_keys_for_action(action)
            
            # Create shortcuts for each key
            for key in keys:
                try:
                    # Handle Tab key specially for pane switching
                    if action == 'switch_pane' or key.lower() == 'tab':
                        shortcut = QShortcut(QKeySequence(Qt.Key_Tab), self)
                        shortcut.activated.connect(self.switch_pane_requested.emit)
                        self.shortcuts[f"{action}_{key}"] = shortcut
                        continue
                    
                    # Convert key to Qt key sequence
                    if key in special_key_map:
                        # Special key (function key, navigation key, etc.)
                        qt_key = special_key_map[key]
                        key_sequence = QKeySequence(qt_key)
                    elif len(key) == 1:
                        # Single character key
                        key_sequence = QKeySequence(key)
                    else:
                        # Try to parse as key sequence string
                        key_sequence = QKeySequence(key)
                    
                    # Create shortcut
                    shortcut = QShortcut(key_sequence, self)
                    
                    # Connect to action signal
                    shortcut.activated.connect(
                        lambda a=action: self.action_triggered.emit(a)
                    )
                    
                    # Store shortcut reference
                    self.shortcuts[f"{action}_{key}"] = shortcut
                    
                except Exception as e:
                    print(f"Warning: Could not create shortcut for action '{action}' key '{key}': {e}")
        
        # Always create Tab shortcut for pane switching (not in KEY_BINDINGS)
        # Tab key is hardcoded in both TUI and GUI modes for pane switching
        tab_shortcut = QShortcut(QKeySequence(Qt.Key_Tab), self)
        tab_shortcut.activated.connect(self.switch_pane_requested.emit)
        self.shortcuts["switch_pane_Tab"] = tab_shortcut
    
    def get_shortcuts_for_action(self, action):
        """
        Get all shortcuts associated with an action.
        
        Args:
            action: Action name
        
        Returns:
            List of QShortcut objects for this action
        """
        return [shortcut for name, shortcut in self.shortcuts.items() 
                if name.startswith(f"{action}_")]
    
    def enable_action(self, action, enabled=True):
        """
        Enable or disable shortcuts for an action.
        
        Args:
            action: Action name
            enabled: Whether to enable (True) or disable (False) the shortcuts
        """
        for shortcut in self.get_shortcuts_for_action(action):
            shortcut.setEnabled(enabled)
    
    def update_shortcuts_for_selection(self, has_selection):
        """
        Update shortcut availability based on selection status.
        
        Some actions require files to be selected, others require no selection.
        This method enables/disables shortcuts based on current selection state.
        
        Args:
            has_selection: Whether there are currently selected files
        """
        # Get actions grouped by selection requirement
        for action in Config.KEY_BINDINGS.keys():
            is_available = KeyBindingManager.is_action_available(action, has_selection)
            self.enable_action(action, is_available)
