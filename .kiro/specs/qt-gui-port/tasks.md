# Implementation Plan: Qt GUI Port for TFM

## Phase 1: Abstraction Layer Foundation

- [x] 1. Define core abstraction interfaces
- [x] 1.1 Create IUIBackend interface with all required methods
  - Define initialize(), cleanup(), get_screen_size() methods
  - Define rendering methods: render_panes(), render_header(), render_footer(), render_status_bar(), render_log_pane()
  - Define interaction methods: show_dialog(), show_progress(), get_input_event(), refresh()
  - Define configuration method: set_color_scheme()
  - _Requirements: 2.3_

- [x] 1.2 Create InputEvent class for unified input representation
  - Define dataclass with type, key, key_name, mouse coordinates, button, and modifiers
  - Implement conversion methods for curses key codes
  - Implement conversion methods for Qt key events
  - _Requirements: 2.1, 2.3_

- [x] 1.3 Create LayoutInfo dataclass for UI layout dimensions
  - Define fields for screen dimensions, pane widths/heights, and component positions
  - Implement calculation method that works for any screen size
  - _Requirements: 2.1_

- [x] 1.4 Create DialogConfig dataclass for dialog configuration
  - Define fields for dialog type, title, message, choices, dimensions
  - Support all dialog types: confirmation, input, list, info, progress
  - _Requirements: 2.3_

- [x] 1.5 Write property test for abstraction layer interfaces
  - **Property 30: Backend interface compliance**
  - **Validates: Requirements 11.3**

## Phase 2: Extract Business Logic

- [ ] 2. Refactor FileManager into TFMApplication controller
- [ ] 2.1 Create TFMApplication class that accepts IUIBackend
  - Move all business logic from FileManager to TFMApplication
  - Remove all direct curses calls from business logic
  - Accept ui_backend parameter in constructor
  - _Requirements: 2.1, 2.2, 2.5_

- [ ] 2.2 Implement main application loop in TFMApplication
  - Create run() method with initialize, event loop, and cleanup
  - Implement render() method that calls UI backend methods
  - Implement handle_input() method for event processing
  - _Requirements: 2.1, 2.2_

- [ ] 2.3 Refactor PaneManager to remove UI dependencies
  - Ensure PaneManager only manages pane state, not rendering
  - Remove any curses-specific code
  - _Requirements: 2.1, 2.5_

- [ ] 2.4 Refactor FileOperations to remove UI dependencies
  - Ensure FileOperations only performs file operations, not UI updates
  - Remove any curses-specific code
  - _Requirements: 2.1, 2.5_

- [ ] 2.5 Refactor all dialog classes to work with abstraction layer
  - Update ListDialog, InfoDialog, SearchDialog, etc. to use IUIBackend
  - Remove direct curses calls from dialog classes
  - _Requirements: 2.1, 2.3, 2.5_

- [ ] 2.6 Write property test for business logic isolation
  - **Property 4: Business logic isolation**
  - **Validates: Requirements 2.1, 2.5**

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 3: Implement Curses Backend

- [ ] 4. Create CursesBackend implementation
- [ ] 4.1 Implement CursesBackend class inheriting from IUIBackend
  - Implement initialize() and cleanup() methods
  - Implement get_screen_size() method
  - _Requirements: 1.1, 2.3_

- [ ] 4.2 Implement curses rendering methods
  - Implement render_panes() wrapping existing draw_pane logic
  - Implement render_header() wrapping existing draw_header logic
  - Implement render_footer() wrapping existing draw_file_footers logic
  - Implement render_status_bar() for status messages
  - Implement render_log_pane() wrapping existing log rendering
  - _Requirements: 1.1, 2.1_

- [ ] 4.3 Implement curses dialog methods
  - Implement show_dialog() delegating to existing dialog classes
  - Support all dialog types: confirmation, input, list, info, progress
  - _Requirements: 1.1, 2.3_

- [ ] 4.4 Implement curses input handling
  - Implement get_input_event() converting curses keys to InputEvent
  - Handle keyboard events, special keys, and resize events
  - _Requirements: 1.1, 2.3_

- [ ] 4.5 Implement curses color scheme support
  - Implement set_color_scheme() using existing color system
  - _Requirements: 1.1, 12.1_

- [ ] 4.6 Write property test for curses backend
  - **Property 30: Backend interface compliance**
  - **Validates: Requirements 11.3**

- [ ] 5. Update tfm.py entry point
- [ ] 5.1 Refactor tfm.py to use TFMApplication with CursesBackend
  - Initialize curses environment
  - Create CursesBackend instance
  - Create TFMApplication with CursesBackend
  - Call TFMApplication.run()
  - _Requirements: 1.1, 1.2_

- [ ] 5.2 Write integration test for TUI mode launch
  - Verify tfm.py launches in TUI mode
  - Verify curses is initialized
  - Verify dual-pane layout is displayed
  - _Requirements: 1.1, 1.3_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 4: Implement Qt Backend Foundation

- [ ] 7. Create Qt main window and pane widgets
- [ ] 7.1 Create TFMMainWindow class (QMainWindow)
  - Set up main window with menu bar, toolbar, status bar
  - Create central widget with splitter for dual panes
  - Implement window geometry save/restore
  - _Requirements: 1.2, 1.3, 10.1, 10.2, 10.3_

- [ ] 7.2 Create FilePaneWidget class (QWidget)
  - Create QTableWidget or QListWidget for file listing
  - Implement columns for filename, size, date, permissions
  - Implement selection handling (single, multi, range)
  - Implement keyboard navigation
  - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4_

- [ ] 7.3 Create HeaderWidget for directory paths
  - Display current directory path for each pane
  - Highlight active pane
  - _Requirements: 3.2_

- [ ] 7.4 Create FooterWidget for file counts and sort info
  - Display directory/file counts
  - Display sort mode and filter info
  - Highlight active pane
  - _Requirements: 3.2_

- [ ] 7.5 Create LogPaneWidget for log messages
  - Create QTextEdit or QListWidget for log display
  - Implement scrolling and message formatting
  - _Requirements: 1.3_

- [ ] 7.6 Write integration test for Qt window creation
  - Verify TFMMainWindow creates all required widgets
  - Verify dual-pane layout is established
  - _Requirements: 1.3, 3.1_

- [ ] 8. Create QtBackend implementation
- [ ] 8.1 Implement QtBackend class inheriting from IUIBackend
  - Implement initialize() and cleanup() methods
  - Store reference to TFMMainWindow
  - Set up event queue for input events
  - _Requirements: 1.2, 2.3_

- [ ] 8.2 Implement Qt rendering methods
  - Implement render_panes() updating FilePaneWidget contents
  - Implement render_header() updating HeaderWidget
  - Implement render_footer() updating FooterWidget
  - Implement render_status_bar() updating status bar
  - Implement render_log_pane() updating LogPaneWidget
  - _Requirements: 1.2, 2.1, 3.1, 3.2, 3.3_

- [ ] 8.3 Implement Qt input handling
  - Implement get_input_event() reading from event queue
  - Connect Qt signals to event queue (key press, mouse click, resize)
  - Convert Qt events to InputEvent objects
  - _Requirements: 1.2, 2.3, 4.1, 4.2, 4.3, 5.1_

- [ ] 8.4 Implement get_screen_size() for Qt
  - Return main window dimensions
  - _Requirements: 1.2_

- [ ] 8.5 Write property test for Qt backend
  - **Property 30: Backend interface compliance**
  - **Validates: Requirements 11.3**

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 5: Implement Qt Dialogs

- [ ] 10. Create Qt dialog implementations
- [ ] 10.1 Implement confirmation dialog
  - Create QMessageBox-based confirmation dialog
  - Support Yes/No/Cancel options
  - Return user choice
  - _Requirements: 6.1, 6.5_

- [ ] 10.2 Implement input dialog
  - Create QInputDialog-based text input dialog
  - Support default values and validation
  - Return user input or None if cancelled
  - _Requirements: 6.2, 6.5_

- [ ] 10.3 Implement list selection dialog
  - Create custom QDialog with QListWidget
  - Support single and multi-selection
  - Support search/filter
  - Return selected items
  - _Requirements: 6.5_

- [ ] 10.4 Implement info dialog
  - Create custom QDialog with QTextEdit
  - Display formatted information
  - Support scrolling for long content
  - _Requirements: 6.5_

- [ ] 10.5 Implement progress dialog
  - Create QProgressDialog for long operations
  - Support progress bar updates
  - Support current file name display
  - Support cancellation
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 10.6 Implement show_dialog() in QtBackend
  - Route dialog requests to appropriate Qt dialog implementation
  - Ensure dialogs are modal (block main window)
  - _Requirements: 6.5_

- [ ] 10.7 Write property test for dialog modality
  - **Property 16: Dialog modality**
  - **Validates: Requirements 6.5**

- [ ] 10.8 Write property test for progress dialog behavior
  - **Property 17: Progress bar updates**
  - **Property 18: Current file display in progress**
  - **Property 19: Progress dialog auto-close**
  - **Property 20: Operation cancellation**
  - **Validates: Requirements 7.2, 7.3, 7.4, 7.5**

- [ ] 11. Create tfm_qt.py entry point
- [ ] 11.1 Create tfm_qt.py entry point script
  - Initialize Qt application (QApplication)
  - Create QtBackend instance
  - Create TFMApplication with QtBackend
  - Call TFMApplication.run()
  - Start Qt event loop
  - _Requirements: 1.2_

- [ ] 11.2 Write integration test for GUI mode launch
  - Verify tfm_qt.py launches in GUI mode
  - Verify Qt window is displayed
  - Verify dual-pane layout is visible
  - _Requirements: 1.2, 1.3_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 6: Implement File Operations in GUI

- [ ] 13. Implement file operation support in Qt
- [ ] 13.1 Connect file operations to Qt UI
  - Wire up copy, move, delete, rename operations
  - Ensure operations work with selected files
  - Display confirmation dialogs before destructive operations
  - _Requirements: 4.5, 6.1_

- [ ] 13.2 Implement progress tracking for file operations
  - Show progress dialog during copy/move operations
  - Update progress bar as files are processed
  - Display current file name
  - Support cancellation
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 13.3 Write property test for file operation consistency
  - **Property 5: File operation consistency**
  - **Validates: Requirements 2.2**

- [ ] 13.4 Write property test for batch operations
  - **Property 13: Batch operation on selection**
  - **Validates: Requirements 4.5**

- [ ] 14. Implement keyboard shortcuts in Qt
- [ ] 14.1 Map all TUI key bindings to Qt shortcuts
  - Create QShortcut objects for all configured key bindings
  - Connect shortcuts to appropriate actions
  - Support function keys, navigation keys, and character keys
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 14.2 Implement Tab key for pane switching
  - Connect Tab key to switch_pane action
  - Update active pane highlighting
  - _Requirements: 5.2_

- [ ] 14.3 Write property test for key binding consistency
  - **Property 14: Key binding consistency**
  - **Validates: Requirements 5.1, 5.3, 5.4**

- [ ] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 7: Implement External Programs and S3 Support

- [ ] 16. Implement external program support in Qt
- [ ] 16.1 Wire external program execution to Qt UI
  - Ensure external programs can be launched from GUI
  - Pass selected files through environment variables
  - Use same environment variable names as TUI mode
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 16.2 Implement post-execution refresh
  - Refresh file listings after external program completes
  - _Requirements: 8.4_

- [ ] 16.3 Implement error handling for external programs
  - Display error dialogs when external programs fail
  - _Requirements: 8.5_

- [ ] 16.4 Write property test for external program integration
  - **Property 21: External program integration**
  - **Property 22: Post-operation refresh**
  - **Property 23: External program error handling**
  - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

- [ ] 17. Implement S3 support in Qt
- [ ] 17.1 Ensure S3 paths work in Qt file panes
  - Display S3 objects in file listings
  - Show object names, sizes, and modification dates
  - _Requirements: 9.1, 9.2_

- [ ] 17.2 Implement S3 file operations in Qt
  - Ensure copy, move, delete work with S3 objects
  - Use same S3 backend as TUI mode
  - _Requirements: 9.3_

- [ ] 17.3 Implement S3 progress indicators
  - Show progress dialogs for S3 operations
  - _Requirements: 9.4_

- [ ] 17.4 Implement S3 error handling
  - Display error dialogs for S3 errors
  - _Requirements: 9.5_

- [ ] 17.5 Write property test for S3 backend consistency
  - **Property 25: S3 backend consistency**
  - **Validates: Requirements 9.3**

- [ ] 18. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 8: Implement Configuration and Themes

- [ ] 19. Implement configuration persistence for Qt
- [ ] 19.1 Implement window geometry save/restore
  - Save window size and position on resize/move
  - Restore saved geometry on launch
  - Use default geometry if no saved config exists
  - Handle off-screen positions gracefully
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 19.2 Write property test for window geometry persistence
  - **Property 28: Window geometry persistence**
  - **Property 29: Window geometry restoration**
  - **Validates: Requirements 10.1, 10.2, 10.3**

- [ ] 19.3 Add GUI-specific configuration options
  - Add GUI_WINDOW_WIDTH, GUI_WINDOW_HEIGHT, GUI_WINDOW_X, GUI_WINDOW_Y
  - Add GUI_FONT_FAMILY, GUI_FONT_SIZE
  - Add GUI_ENABLE_DRAG_DROP, GUI_SHOW_TOOLBAR, GUI_SHOW_MENUBAR
  - _Requirements: 10.1, 10.2, 10.3_

- [ ] 20. Implement theme support in Qt
- [ ] 20.1 Implement color scheme application in Qt
  - Apply configured color scheme on launch
  - Use same color definitions as TUI mode where applicable
  - _Requirements: 12.1, 12.2_

- [ ] 20.2 Implement file type coloring in Qt
  - Apply colors based on file types and attributes
  - Use consistent coloring rules
  - _Requirements: 12.3_

- [ ] 20.3 Implement consistent dialog styling
  - Ensure all dialogs use same styling approach
  - _Requirements: 12.4_

- [ ] 20.4 Implement dynamic theme switching
  - Allow theme changes without restart
  - Update GUI appearance immediately
  - _Requirements: 12.5_

- [ ] 20.5 Write property test for color scheme consistency
  - **Property 32: Color scheme consistency**
  - **Validates: Requirements 12.2**

- [ ] 20.6 Write property test for dynamic theme switching
  - **Property 35: Dynamic theme switching**
  - **Validates: Requirements 12.5**

- [ ] 21. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 9: Polish and Enhancements

- [ ] 22. Add GUI-specific enhancements
- [ ] 22.1 Implement drag-and-drop support
  - Allow dragging files between panes
  - Allow dragging files to/from external applications
  - _Requirements: 1.5_

- [ ] 22.2 Implement context menus
  - Right-click context menu for files
  - Context menu for panes
  - _Requirements: 1.5_

- [ ] 22.3 Implement toolbar with common actions
  - Add toolbar buttons for common operations
  - Make toolbar configurable
  - _Requirements: 1.5_

- [ ] 22.4 Implement menu bar
  - Add File, Edit, View, Tools, Help menus
  - Populate with all available actions
  - _Requirements: 1.5_

- [ ] 23. Performance optimization
- [ ] 23.1 Optimize file list rendering
  - Use incremental updates when possible
  - Implement virtual scrolling for large directories
  - _Requirements: 1.5_

- [ ] 23.2 Optimize progress updates
  - Throttle progress bar updates to avoid UI lag
  - Use background threads for file operations
  - _Requirements: 7.2_

- [ ] 24. Final integration testing
- [ ] 24.1 Write comprehensive integration tests
  - Test all file operations in both modes
  - Test all dialogs in both modes
  - Test external programs in both modes
  - Test S3 operations in both modes
  - _Requirements: 11.4_

- [ ] 24.2 Write property test for configuration consistency
  - **Property 2: Configuration consistency across modes**
  - **Validates: Requirements 1.4**

- [ ] 24.3 Write property test for feature parity
  - **Property 3: Feature parity between backends**
  - **Validates: Requirements 1.5**

- [ ] 25. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 10: Documentation and Deployment

- [ ] 26. Create documentation
- [ ] 26.1 Create end-user documentation for GUI mode
  - Document how to launch GUI mode
  - Document GUI-specific features (mouse, drag-drop, menus)
  - Document keyboard shortcuts in GUI mode
  - Document configuration options
  - Place in doc/QT_GUI_MODE_FEATURE.md
  - _Requirements: 1.2, 1.5_

- [ ] 26.2 Create developer documentation for abstraction layer
  - Document IUIBackend interface
  - Document how to implement new backends
  - Document InputEvent system
  - Document testing strategy
  - Place in doc/dev/UI_ABSTRACTION_LAYER_SYSTEM.md
  - _Requirements: 2.1, 2.3_

- [ ] 26.3 Update README with Qt GUI information
  - Add section about dual-mode support
  - Add installation instructions for Qt dependencies
  - Add screenshots of GUI mode
  - _Requirements: 1.2_

- [ ] 27. Update build and installation
- [ ] 27.1 Update setup.py with Qt dependencies
  - Add PySide6 or PyQt6 to requirements
  - Add optional dependencies for Qt themes
  - Create separate entry point for tfm_qt.py
  - _Requirements: 1.2_

- [ ] 27.2 Update requirements.txt
  - Add Qt dependencies
  - Document optional dependencies
  - _Requirements: 1.2_

- [ ] 28. Final verification
- [ ] 28.1 Verify all requirements are met
  - Review all 12 requirements
  - Verify all acceptance criteria are satisfied
  - Run all tests and ensure they pass
  - _Requirements: 1.1-12.5_

- [ ] 28.2 Verify backward compatibility
  - Ensure existing TUI mode works unchanged
  - Ensure existing configuration files work
  - Ensure no breaking changes for TUI users
  - _Requirements: 1.1_
