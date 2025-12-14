# Requirements Document

## Introduction

This document specifies the requirements for implementing window geometry persistence in TFM's CoreGraphics backend mode. Window geometry persistence allows the application to remember and restore the window's size and position across application sessions, providing a consistent user experience.

## Glossary

- **Window Geometry**: The size (width and height) and position (x and y coordinates) of the application window on the screen
- **CoreGraphics Backend**: TFM's macOS-native rendering backend that uses NSWindow and CoreGraphics APIs
- **NSWindow**: macOS Cocoa framework class representing an application window
- **Frame Autosave**: macOS native feature that automatically saves and restores window frame (geometry) using NSUserDefaults
- **NSUserDefaults**: macOS system for storing user preferences and application state
- **TFM**: Two-File Manager, the terminal-based file manager application
- **TTK**: Terminal Toolkit, the abstraction layer providing cross-platform terminal UI capabilities

## Requirements

### Requirement 1

**User Story:** As a TFM user running in CoreGraphics backend mode, I want the application window to remember its size and position, so that I don't have to resize and reposition it every time I launch the application.

#### Acceptance Criteria

1. WHEN a user launches TFM in CoreGraphics backend mode for the first time THEN the system SHALL display the window at the default size and position specified in configuration
2. WHEN a user resizes the TFM window THEN the system SHALL persist the new window size to storage
3. WHEN a user moves the TFM window to a different screen position THEN the system SHALL persist the new window position to storage
4. WHEN a user quits TFM and relaunches it THEN the system SHALL restore the window to its previous size and position
5. WHEN window geometry data is corrupted or invalid THEN the system SHALL fall back to default window size and position

### Requirement 2

**User Story:** As a TFM developer, I want to use macOS native window persistence features, so that the implementation is simple, reliable, and follows platform conventions.

#### Acceptance Criteria

1. WHEN implementing window geometry persistence THEN the system SHALL use NSWindow's setFrameAutosaveName method for automatic persistence
2. WHEN storing window geometry THEN the system SHALL use macOS NSUserDefaults system for storage
3. WHEN the CoreGraphics backend initializes THEN the system SHALL configure the window with a unique frame autosave name
4. WHEN the window frame changes THEN the system SHALL automatically persist changes without manual intervention
5. WHEN restoring window geometry THEN the system SHALL automatically restore from NSUserDefaults without manual loading

### Requirement 3

**User Story:** As a TFM user with multiple monitors, I want the window to restore to the correct monitor, so that my multi-monitor workflow is preserved.

#### Acceptance Criteria

1. WHEN a user moves the TFM window to a secondary monitor THEN the system SHALL persist the monitor-specific position
2. WHEN a user relaunches TFM with the same monitor configuration THEN the system SHALL restore the window to the correct monitor
3. WHEN a user relaunches TFM with a different monitor configuration THEN the system SHALL restore the window to a valid visible position
4. WHEN the saved window position is off-screen THEN the system SHALL automatically adjust the position to be visible
5. WHEN multiple monitors are disconnected THEN the system SHALL ensure the window appears on the primary monitor

### Requirement 4

**User Story:** As a TFM user, I want window geometry persistence to work seamlessly without configuration, so that I can focus on file management tasks.

#### Acceptance Criteria

1. WHEN TFM launches in CoreGraphics backend mode THEN the system SHALL enable window geometry persistence automatically
2. WHEN window geometry persistence is active THEN the system SHALL not require user configuration or manual save actions
3. WHEN the user resizes or moves the window THEN the system SHALL persist changes immediately without delay
4. WHEN the user quits the application THEN the system SHALL ensure all geometry changes are saved
5. WHEN window geometry persistence fails THEN the system SHALL log a warning but continue normal operation

### Requirement 5

**User Story:** As a TFM developer, I want window geometry persistence to integrate cleanly with existing code, so that it doesn't disrupt other features or introduce bugs.

#### Acceptance Criteria

1. WHEN adding window geometry persistence THEN the system SHALL not modify the existing window creation logic beyond adding the autosave name
2. WHEN window geometry persistence is enabled THEN the system SHALL not interfere with programmatic window resizing
3. WHEN the window delegate handles resize events THEN the system SHALL continue to update the character grid correctly
4. WHEN window geometry is restored THEN the system SHALL recalculate grid dimensions based on the restored size
5. WHEN running in curses backend mode THEN the system SHALL not attempt to use window geometry persistence

### Requirement 6

**User Story:** As a TFM user, I want to be able to reset the window geometry to defaults if needed, so that I can recover from undesirable window states.

#### Acceptance Criteria

1. WHEN window geometry becomes problematic THEN the system SHALL provide a mechanism to reset to defaults
2. WHEN resetting window geometry THEN the system SHALL clear the saved frame from NSUserDefaults
3. WHEN resetting window geometry THEN the system SHALL apply the default size and position from configuration
4. WHEN the user manually deletes NSUserDefaults data THEN the system SHALL handle missing data gracefully
5. WHEN window geometry is reset THEN the system SHALL log the action for debugging purposes

### Requirement 7

**User Story:** As a TTK library developer, I want the window frame autosave name to be configurable from the application layer, so that TTK remains independent from TFM and can be used by other applications.

#### Acceptance Criteria

1. WHEN initializing the CoreGraphics backend THEN the system SHALL accept an optional frame autosave name parameter
2. WHEN no frame autosave name is provided THEN the system SHALL use a sensible default value
3. WHEN the frame autosave name is provided THEN the system SHALL use that value for NSWindow frame persistence
4. WHEN TFM initializes the CoreGraphics backend THEN TFM SHALL provide "TFMMainWindow" as the frame autosave name
5. WHEN other applications use TTK THEN they SHALL be able to provide their own unique frame autosave names
