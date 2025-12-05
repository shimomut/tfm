# Requirements Document

## Introduction

This document specifies the requirements for porting TFM (TUI File Manager) to support both Terminal User Interface (TUI) and Graphical User Interface (GUI) modes using Qt for Python (PySide6/PyQt6). The goal is to maintain a single codebase that can run in either mode through separate entry points, preserving all existing TUI functionality while adding a modern GUI alternative.

## Glossary

- **TFM**: TUI File Manager - the existing terminal-based file manager application
- **TUI**: Terminal User Interface - text-based interface using curses library
- **GUI**: Graphical User Interface - window-based interface using Qt framework
- **Qt for Python**: Python bindings for Qt framework (PySide6 or PyQt6)
- **Abstraction Layer**: Interface that separates UI-specific code from business logic
- **Entry Point**: Main executable script that launches the application
- **Dual-Mode Application**: Application that supports both TUI and GUI interfaces
- **Business Logic**: Core functionality independent of UI implementation
- **UI Backend**: Specific implementation (curses or Qt) of the abstraction layer
- **Pane**: File listing panel showing directory contents
- **Dialog**: Modal window for user input or information display
- **File Operations**: Copy, move, delete, rename operations on files and directories
- **Selection System**: Mechanism for selecting multiple files for batch operations
- **Key Binding**: Keyboard shortcut mapped to an action
- **Configuration System**: User preferences and settings management

## Requirements

### Requirement 1

**User Story:** As a user, I want to launch TFM in either TUI or GUI mode, so that I can choose the interface that best suits my environment and preferences.

#### Acceptance Criteria

1. WHEN a user executes `tfm.py`, THE System SHALL launch the application in TUI mode using the curses library
2. WHEN a user executes `tfm_qt.py`, THE System SHALL launch the application in GUI mode using Qt for Python
3. WHEN the GUI mode is launched, THE System SHALL display a window with the same dual-pane layout as TUI mode
4. WHEN either mode is launched, THE System SHALL load the same configuration files and user preferences
5. WHEN either mode is launched, THE System SHALL provide access to all core file management features

### Requirement 2

**User Story:** As a developer, I want a clear abstraction layer between UI and business logic, so that both TUI and GUI can share the same core functionality without code duplication.

#### Acceptance Criteria

1. WHEN business logic is implemented, THE System SHALL separate it from UI-specific rendering code
2. WHEN a file operation is performed, THE System SHALL execute the same logic regardless of UI mode
3. WHEN the abstraction layer is defined, THE System SHALL provide interfaces for all UI operations including rendering, input handling, and dialogs
4. WHEN a new feature is added, THE System SHALL require implementation only in the abstraction layer and both UI backends
5. WHEN the codebase is analyzed, THE System SHALL show no direct curses or Qt calls in business logic modules

### Requirement 3

**User Story:** As a user, I want the GUI version to display the dual-pane file browser, so that I can navigate and manage files with the same workflow as the TUI version.

#### Acceptance Criteria

1. WHEN the GUI launches, THE System SHALL display two file listing panes side by side
2. WHEN a pane is active, THE System SHALL highlight it to indicate focus
3. WHEN files are displayed in a pane, THE System SHALL show filename, size, date, and permissions
4. WHEN a directory is selected, THE System SHALL navigate into that directory
5. WHEN the parent directory is selected, THE System SHALL navigate up one level

### Requirement 4

**User Story:** As a user, I want to select files in GUI mode using mouse clicks, so that I can perform batch operations on multiple files.

#### Acceptance Criteria

1. WHEN a user clicks on a file, THE System SHALL toggle its selection state
2. WHEN a user holds Ctrl and clicks files, THE System SHALL add files to the selection
3. WHEN a user holds Shift and clicks a file, THE System SHALL select all files between the last selected file and the clicked file
4. WHEN files are selected, THE System SHALL visually highlight them
5. WHEN a file operation is invoked, THE System SHALL operate on all selected files

### Requirement 5

**User Story:** As a user, I want keyboard shortcuts to work in GUI mode, so that I can use the same efficient keyboard-driven workflow as in TUI mode.

#### Acceptance Criteria

1. WHEN a user presses a key binding in GUI mode, THE System SHALL execute the same action as in TUI mode
2. WHEN the user presses Tab, THE System SHALL switch focus between panes
3. WHEN the user presses function keys, THE System SHALL trigger the corresponding file operations
4. WHEN the user presses navigation keys, THE System SHALL move the cursor in the file list
5. WHEN the user presses Ctrl+C or Cmd+Q, THE System SHALL exit the application

### Requirement 6

**User Story:** As a user, I want dialogs to appear in GUI mode for operations requiring input, so that I can provide information in a familiar graphical interface.

#### Acceptance Criteria

1. WHEN a file operation requires confirmation, THE System SHALL display a dialog with Yes/No options
2. WHEN a rename operation is initiated, THE System SHALL display a text input dialog
3. WHEN a search is performed, THE System SHALL display a search dialog with results
4. WHEN an error occurs, THE System SHALL display an error dialog with the error message
5. WHEN a dialog is displayed, THE System SHALL block interaction with the main window until dismissed

### Requirement 7

**User Story:** As a user, I want file operations to show progress in GUI mode, so that I can monitor long-running operations like copying large files.

#### Acceptance Criteria

1. WHEN a file copy operation starts, THE System SHALL display a progress dialog
2. WHEN files are being copied, THE System SHALL update the progress bar to reflect completion percentage
3. WHEN multiple files are being processed, THE System SHALL show the current file name
4. WHEN an operation completes, THE System SHALL close the progress dialog automatically
5. WHEN a user clicks Cancel in a progress dialog, THE System SHALL abort the operation

### Requirement 8

**User Story:** As a user, I want the GUI to support the same external programs integration as TUI mode, so that I can launch external tools from the file manager.

#### Acceptance Criteria

1. WHEN external programs are configured, THE System SHALL make them available in both TUI and GUI modes
2. WHEN a user invokes an external program in GUI mode, THE System SHALL launch it with the same environment variables as TUI mode
3. WHEN an external program is launched, THE System SHALL pass selected files through environment variables
4. WHEN an external program completes, THE System SHALL refresh the file listing if needed
5. WHEN an external program fails, THE System SHALL display an error message

### Requirement 9

**User Story:** As a user, I want the GUI to support S3 browsing, so that I can manage cloud storage with the same interface as local files.

#### Acceptance Criteria

1. WHEN a user navigates to an S3 path in GUI mode, THE System SHALL display S3 objects in the file listing
2. WHEN S3 objects are displayed, THE System SHALL show object names, sizes, and modification dates
3. WHEN a user performs file operations on S3 objects, THE System SHALL execute them using the same S3 backend as TUI mode
4. WHEN S3 operations are in progress, THE System SHALL display appropriate progress indicators
5. WHEN S3 errors occur, THE System SHALL display error messages in GUI dialogs

### Requirement 10

**User Story:** As a user, I want the GUI to remember window size and position, so that my preferred layout is restored when I restart the application.

#### Acceptance Criteria

1. WHEN the GUI window is resized, THE System SHALL save the new dimensions to the configuration
2. WHEN the GUI window is moved, THE System SHALL save the new position to the configuration
3. WHEN the GUI is launched, THE System SHALL restore the saved window size and position
4. WHEN no saved configuration exists, THE System SHALL use default window dimensions
5. WHEN the saved position is off-screen, THE System SHALL use default positioning

### Requirement 11

**User Story:** As a developer, I want comprehensive tests for the abstraction layer, so that I can ensure both UI backends work correctly.

#### Acceptance Criteria

1. WHEN the abstraction layer is implemented, THE System SHALL include unit tests for all interface methods
2. WHEN business logic is tested, THE System SHALL use mock UI backends to verify behavior
3. WHEN UI backends are tested, THE System SHALL verify they correctly implement the abstraction interface
4. WHEN file operations are tested, THE System SHALL verify they work identically in both modes
5. WHEN tests are run, THE System SHALL achieve at least 80% code coverage for shared business logic

### Requirement 12

**User Story:** As a user, I want the GUI to support themes and styling, so that I can customize the appearance to match my preferences.

#### Acceptance Criteria

1. WHEN the GUI launches, THE System SHALL apply the configured color scheme
2. WHEN color schemes are defined, THE System SHALL use the same color definitions as TUI mode where applicable
3. WHEN the GUI renders file listings, THE System SHALL apply colors based on file types and attributes
4. WHEN dialogs are displayed, THE System SHALL use consistent styling throughout the application
5. WHEN the user changes themes, THE System SHALL update the GUI appearance without requiring a restart
