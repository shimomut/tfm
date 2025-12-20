# Requirements Document

## Introduction

This feature introduces a distinction between character input events (CharEvent) and command key events (KeyEvent) in the TFM file manager application. Currently, the system uses KeyEvent for all keyboard input, which makes it difficult to properly handle text input versus command shortcuts. By separating these concerns, we can improve text input handling while maintaining clear command key bindings.

## Glossary

- **CharEvent**: An event representing a character intended for text input (typing)
- **KeyEvent**: An event representing a keyboard key press intended as a command or shortcut (e.g., Q to quit, A to select all)
- **TTK**: The terminal toolkit library used by TFM for rendering and input handling
- **Backend**: The platform-specific implementation layer (curses or CoreGraphics) that interfaces with the operating system
- **TFM**: Terminal File Manager - the main application
- **Event Handler**: Code that processes keyboard input events and determines appropriate actions
- **UTF-8**: A variable-length character encoding for Unicode, where characters can be 1-4 bytes
- **Multi-byte Character**: A Unicode character that requires more than one byte in UTF-8 encoding (e.g., Japanese characters)
- **Caret**: The visible cursor indicator in the terminal that shows where text input will appear
- **Cursor Position**: The logical position within a text widget where the next character will be inserted

## Requirements

### Requirement 1

**User Story:** As a developer, I want a clear separation between character input and command input, so that text entry and keyboard shortcuts don't interfere with each other.

#### Acceptance Criteria

1. WHEN the system receives keyboard input intended for text entry THEN the system SHALL generate a CharEvent
2. WHEN the system receives keyboard input intended as a command THEN the system SHALL generate a KeyEvent
3. WHEN processing input events THEN the system SHALL distinguish between CharEvent and KeyEvent using type checking
4. WHEN a CharEvent is generated THEN the system SHALL include the character data for text insertion
5. WHEN a KeyEvent is generated THEN the system SHALL include the key identifier for command matching

### Requirement 2

**User Story:** As a user typing text in input fields, I want all printable characters to be correctly captured, so that I can enter text naturally.

#### Acceptance Criteria

1. WHEN a user types a printable ASCII character THEN the system SHALL generate a CharEvent with that character
2. WHEN a CharEvent is received by a text input widget THEN the widget SHALL insert the character at the cursor position
3. WHEN a CharEvent contains a character THEN the system SHALL preserve the exact Unicode representation

### Requirement 3

**User Story:** As a user executing file manager commands, I want keyboard shortcuts to work reliably, so that I can efficiently navigate and manage files.

#### Acceptance Criteria

1. WHEN a user presses Q without modifiers THEN the system SHALL generate a KeyEvent for the quit command
2. WHEN a user presses A without modifiers THEN the system SHALL generate a KeyEvent for the select-all command
3. WHEN a KeyEvent is received by the file manager THEN the system SHALL match it against command bindings
4. WHEN a command key is pressed in a text input context THEN the system SHALL generate a KeyEvent not a CharEvent
5. WHEN function keys are pressed THEN the system SHALL generate KeyEvent instances

### Requirement 4

**User Story:** As a developer maintaining event handling code, I want explicit type checking for event types, so that I can handle CharEvent and KeyEvent appropriately without confusion.

#### Acceptance Criteria

1. WHEN existing code assumes KeyEvent THEN the system SHALL use isinstance checks to verify event type
2. WHEN code handles both CharEvent and KeyEvent THEN the system SHALL check event type before processing
3. WHEN a CharEvent is passed to command handling code THEN the system SHALL ignore it or handle it separately
4. WHEN a KeyEvent is passed to text input code THEN the system SHALL process it as a command not as text

### Requirement 5

**User Story:** As a developer working with the TTK library, I want both backends (curses and CoreGraphics) to generate CharEvent and KeyEvent consistently, so that the application behaves the same across platforms.

#### Acceptance Criteria

1. WHEN the curses backend receives character input THEN the backend SHALL generate a CharEvent
2. WHEN the CoreGraphics backend receives character input THEN the backend SHALL generate a CharEvent
3. WHEN the curses backend receives command key input THEN the backend SHALL generate a KeyEvent
4. WHEN the CoreGraphics backend receives command key input THEN the backend SHALL generate a KeyEvent
5. WHEN comparing events from different backends THEN the CharEvent and KeyEvent structures SHALL be equivalent

### Requirement 6

**User Story:** As a developer, I want the CharEvent and KeyEvent classes to have clear, well-defined interfaces, so that I can use them correctly throughout the codebase.

#### Acceptance Criteria

1. WHEN defining CharEvent THEN the class SHALL include a character field containing the input character
2. WHEN defining KeyEvent THEN the class SHALL include a key identifier field for command matching
3. WHEN either event type is created THEN the system SHALL validate that required fields are present
4. WHEN accessing event data THEN the interface SHALL provide clear attribute names
5. WHEN serializing events for debugging THEN both event types SHALL provide readable string representations

### Requirement 7

**User Story:** As a user of text input widgets, I want modifier keys (Ctrl, Alt, Cmd) combined with characters to be treated as commands, so that keyboard shortcuts work in text fields.

#### Acceptance Criteria

1. WHEN a user presses Ctrl+C in a text field THEN the system SHALL generate a KeyEvent not a CharEvent
2. WHEN a user presses Alt+key in a text field THEN the system SHALL generate a KeyEvent not a CharEvent
3. WHEN a user presses Cmd+key on macOS in a text field THEN the system SHALL generate a KeyEvent not a CharEvent
4. WHEN a user presses a character without modifiers in a text field THEN the system SHALL generate a CharEvent
5. WHEN a user presses Shift+character for uppercase in a text field THEN the system SHALL generate a CharEvent with the uppercase character

### Requirement 8

**User Story:** As a user typing Unicode characters in curses backend mode, I want multi-byte UTF-8 characters to be handled correctly, so that I can input characters like Japanese hiragana without generating multiple events.

#### Acceptance Criteria

1. WHEN a user types a multi-byte UTF-8 character in curses mode THEN the system SHALL accumulate the bytes until a complete character is formed
2. WHEN a complete UTF-8 character is formed THEN the system SHALL generate a single CharEvent with the complete Unicode character
3. WHEN the system receives incomplete UTF-8 byte sequences THEN the system SHALL buffer them until the sequence is complete
4. WHEN the system receives an invalid UTF-8 byte sequence THEN the system SHALL discard the invalid bytes and continue processing
5. WHEN a multi-byte character is being accumulated THEN the system SHALL NOT generate KeyEvent instances for the individual bytes

### Requirement 9

**User Story:** As a user typing in text input fields, I want the terminal caret position to match the logical cursor position in the text widget, so that I can see where my input will appear.

#### Acceptance Criteria

1. WHEN a text input widget has focus THEN the system SHALL position the terminal caret at the widget's cursor position
2. WHEN the cursor position changes within a text widget THEN the system SHALL update the terminal caret position immediately
3. WHEN calculating caret position THEN the system SHALL account for the widget's screen coordinates and internal cursor offset
4. WHEN a text widget loses focus THEN the system SHALL hide the terminal caret or move it to an appropriate location
5. WHEN rendering a text widget THEN the system SHALL ensure the caret position is set after drawing the widget content

### Requirement 10

**User Story:** As a user typing with an IME (Input Method Editor) for languages like Japanese, I want the IME composition text to appear at the correct cursor position, so that I can see what I'm typing in the right location.

#### Acceptance Criteria

1. WHEN using IME to compose multi-byte characters THEN the IME composition text SHALL appear at the cursor position in the input field
2. WHEN the dialog contains help text THEN the IME composition text SHALL NOT appear after the help text
3. WHEN setting caret position for IME THEN the system SHALL call refresh() to apply the cursor position immediately
4. WHEN drawing dialog components THEN the system SHALL set caret position AFTER all text drawing is complete
5. WHEN calculating caret position THEN the system SHALL account for wide characters in the text before the cursor
