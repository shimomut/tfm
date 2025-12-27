# Requirements Document

## Introduction

This document specifies the requirements for adding comprehensive mouse event support to the TFM (Terminal File Manager) application. The feature will enable mouse interaction in both terminal mode (via curses backend) and desktop mode (via CoreGraphics backend), with initial focus on pane switching and future extensibility for drag-and-drop operations.

## Glossary

- **TTK**: The Terminal ToolKit library that provides the backend abstraction layer for TFM
- **CoreGraphics_Backend**: The macOS-native rendering backend that supports desktop mode
- **Curses_Backend**: The terminal-based rendering backend using the curses library
- **UILayer**: A component in the UI layer stack that can receive and handle events
- **Mouse_Event**: An event object containing mouse interaction data (position, button state, event type)
- **Text_Grid**: The character-based coordinate system where position is measured in columns and rows
- **Sub_Cell_Position**: The fractional position within a text cell, expressed as percentages from the top-left corner
- **Event_Stack**: The ordered collection of UILayers where the topmost layer receives events first
- **File_Pane**: A UILayer component displaying a directory listing in TFM
- **TFM**: Terminal File Manager, the application using TTK
- **Quick_Edit_Bar**: A single-line text input component for editing filenames and paths
- **Quick_Choice_Bar**: A component displaying multiple choice options for user confirmation
- **I-search**: Incremental search mode in the text viewer where users type to search interactively
- **Text_Viewer**: A UILayer component for viewing file contents with search capabilities

## Requirements

### Requirement 1: TTK Mouse Event API

**User Story:** As a TTK library user, I want a unified mouse event API, so that I can handle mouse interactions consistently across different backends.

#### Acceptance Criteria

1. THE TTK SHALL provide a Mouse_Event class containing event type, button state, position, and timestamp
2. WHEN a mouse event occurs, THE TTK SHALL convert screen coordinates to Text_Grid coordinates (column and row)
3. WHEN a mouse event occurs, THE TTK SHALL calculate Sub_Cell_Position as percentages from the top-left of the grid cell
4. THE TTK SHALL support mouse event types including button down, button up, double click, move, and wheel
5. THE TTK SHALL provide an event callback mechanism for applications to register mouse event handlers

### Requirement 2: CoreGraphics Backend Mouse Support

**User Story:** As a desktop mode user, I want full mouse interaction support, so that I can use all mouse capabilities in the application.

#### Acceptance Criteria

1. WHEN running in desktop mode, THE CoreGraphics_Backend SHALL capture all mouse button events (down, up, double click)
2. WHEN running in desktop mode, THE CoreGraphics_Backend SHALL capture mouse movement events
3. WHEN running in desktop mode, THE CoreGraphics_Backend SHALL capture mouse wheel events
4. WHEN a mouse event is captured, THE CoreGraphics_Backend SHALL transform window coordinates to Text_Grid coordinates
5. WHEN a mouse event is captured, THE CoreGraphics_Backend SHALL calculate Sub_Cell_Position within the target grid cell

### Requirement 3: Curses Backend Mouse Support

**User Story:** As a terminal mode user, I want mouse support where available, so that I can use mouse interactions in terminal environments that support it.

#### Acceptance Criteria

1. WHEN running in terminal mode, THE Curses_Backend SHALL enable mouse event capture if supported by the terminal
2. WHEN mouse events are available, THE Curses_Backend SHALL capture button click events
3. WHEN mouse events are available, THE Curses_Backend SHALL provide Text_Grid coordinates for mouse events
4. IF the terminal does not support mouse events, THEN THE Curses_Backend SHALL gracefully degrade without errors
5. THE Curses_Backend SHALL document which mouse event types are supported versus unsupported

### Requirement 4: Event Routing to UI Layer Stack

**User Story:** As a UI framework developer, I want mouse events routed to the topmost UI layer only, so that the active component receives user input.

#### Acceptance Criteria

1. WHEN a mouse event occurs, THE Event_Stack SHALL deliver the event to the topmost UILayer only
2. THE Event_Stack SHALL not deliver mouse events to lower layers in the stack
3. THE Event_Stack SHALL maintain the same event routing behavior for mouse events as for keyboard events
4. THE UILayer SHALL provide a mouse event handler method
5. THE topmost UILayer SHALL receive all mouse events regardless of whether they are within its bounds

### Requirement 5: Pane Focus Switching

**User Story:** As a TFM user, I want to click on a file pane to switch focus, so that I can quickly navigate between left and right panes.

#### Acceptance Criteria

1. WHEN a user clicks on the left File_Pane, THEN THE TFM SHALL set focus to the left pane
2. WHEN a user clicks on the right File_Pane, THEN THE TFM SHALL set focus to the right pane
3. WHEN focus changes, THE TFM SHALL update the visual indicators to show which pane is active
4. WHEN a click occurs outside both panes, THEN THE TFM SHALL maintain the current focus state
5. THE TFM SHALL respond to mouse clicks in both terminal mode and desktop mode

### Requirement 6: Mouse Event Data Structure

**User Story:** As a developer, I want a well-defined mouse event data structure, so that I can access all relevant event information consistently.

#### Acceptance Criteria

1. THE Mouse_Event SHALL contain an event_type field indicating the type of mouse action
2. THE Mouse_Event SHALL contain a column field indicating the Text_Grid column position
3. THE Mouse_Event SHALL contain a row field indicating the Text_Grid row position
4. THE Mouse_Event SHALL contain sub_cell_x and sub_cell_y fields indicating fractional position within the cell
5. THE Mouse_Event SHALL contain a button field indicating which mouse button was involved
6. THE Mouse_Event SHALL contain a timestamp field for event ordering and timing analysis

### Requirement 7: Backend Capability Detection

**User Story:** As an application developer, I want to detect mouse support capabilities, so that I can adapt the UI based on available features.

#### Acceptance Criteria

1. THE TTK SHALL provide a method to query whether mouse events are supported by the current backend
2. THE TTK SHALL provide a method to query which specific mouse event types are supported
3. WHEN mouse support is unavailable, THE TTK SHALL return False for mouse capability queries
4. THE TTK SHALL document the mouse capabilities of each backend in the API documentation
5. THE TFM SHALL query mouse capabilities at startup and adapt its behavior accordingly

### Requirement 8: Future Extensibility for Drag and Drop

**User Story:** As a system architect, I want the mouse event system designed for extensibility, so that drag-and-drop can be added in the future without major refactoring.

#### Acceptance Criteria

1. THE Mouse_Event SHALL include fields that support tracking drag operations (button state during movement)
2. THE TTK SHALL maintain event ordering to support detecting drag gesture patterns
3. THE UILayer SHALL support a design pattern that allows adding drag-and-drop handlers in the future
4. THE Mouse_Event SHALL include modifier key state (shift, ctrl, alt) for future gesture support
5. THE architecture SHALL separate low-level event capture from high-level gesture recognition

### Requirement 9: Input Mode Mouse Event Filtering

**User Story:** As a TFM user, I want mouse events to be ignored during text input modes, so that accidental mouse clicks don't disrupt my keyboard-based workflow.

#### Acceptance Criteria

1. WHILE Quick_Edit_Bar is active, THE TFM SHALL ignore all mouse events
2. WHILE Quick_Choice_Bar is active, THE TFM SHALL ignore all mouse events
3. WHILE I-search mode is active in Text_Viewer, THE TFM SHALL ignore all mouse events
4. WHEN exiting any of these input modes, THE TFM SHALL resume normal mouse event processing
5. THE TFM SHALL check input mode state before processing any mouse event
