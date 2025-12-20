# Requirements Document

## Introduction

This feature adds full Unicode input and Input Method Editor (IME) support to the CoreGraphics backend of TFM. While the curses backend already supports Unicode input through UTF-8 byte accumulation, the CoreGraphics backend needs to implement macOS-specific IME protocols to enable proper input of complex scripts like Japanese, Chinese, and Korean. The implementation uses macOS's native text input system to automatically render composition text and candidate windows, while TFM provides positioning information and handles the final committed text through CharEvent generation.

## Glossary

- **IME**: Input Method Editor - a system component that enables users to input complex characters and symbols not directly available on their keyboard
- **CoreGraphics Backend**: The macOS-specific rendering backend for TFM that uses native macOS APIs
- **NSTextInputClient**: A macOS protocol that enables IME support by allowing the system to communicate with the application about text input and render composition text
- **Composition Text**: Temporary text displayed during IME input before the user commits the final characters (rendered by macOS)
- **Marked Text**: The text currently being composed in the IME (synonymous with composition text)
- **Candidate Window**: A popup window showing possible character choices during IME input (rendered by macOS)
- **Hiragana**: A Japanese syllabary used for native Japanese words
- **Kanji**: Chinese characters used in Japanese writing
- **Font Size**: The point size of the font used for rendering text and IME composition
- **TFM**: Terminal File Manager - the main application
- **TTK**: The terminal toolkit library used by TFM for rendering and input handling
- **CharEvent**: An event representing a character intended for text input
- **KeyEvent**: An event representing a keyboard key press intended as a command
- **First Rect**: The screen rectangle where composition text begins, used by macOS to position the candidate window

## Requirements

### Requirement 1

**User Story:** As a user typing Japanese text, I want to use the macOS IME to input hiragana and convert it to kanji, so that I can enter Japanese text naturally.

#### Acceptance Criteria

1. WHEN a user activates the Japanese IME and types romaji THEN the macOS system SHALL display the hiragana composition text at the cursor position
2. WHEN composition text is being entered THEN the macOS system SHALL underline the composition text to indicate it is not yet committed
3. WHEN a user presses Space during composition THEN the macOS system SHALL show the candidate window with kanji conversion options
4. WHEN a user selects a candidate THEN the macOS system SHALL replace the composition text with the selected kanji
5. WHEN a user presses Enter during composition THEN the system SHALL commit the current composition text as final input via CharEvent

### Requirement 2

**User Story:** As a user typing with IME, I want the composition text to appear at the correct location with the correct font size, so that I can see what I'm typing clearly.

#### Acceptance Criteria

1. WHEN composition text is displayed THEN the system SHALL use the same font size as the application's main text
2. WHEN the application uses a 12-point font THEN the IME composition SHALL use a 12-point font
3. WHEN the application changes font size THEN the IME composition font size SHALL update accordingly
4. WHEN composition text is displayed THEN the system SHALL position it at the current cursor location in the text field
5. WHEN the cursor moves THEN the IME composition position SHALL update to follow the cursor

### Requirement 3

**User Story:** As a developer implementing IME support, I want to implement the NSTextInputClient protocol correctly, so that macOS can communicate with the application about text input and render composition text automatically.

#### Acceptance Criteria

1. WHEN the CoreGraphics backend initializes THEN the system SHALL register the view as conforming to NSTextInputClient protocol
2. WHEN macOS queries for marked text THEN the system SHALL return the current composition text range
3. WHEN macOS queries for selected text THEN the system SHALL return the current text selection range
4. WHEN macOS requests to set marked text THEN the system SHALL store the composition text for position tracking
5. WHEN macOS requests to insert text THEN the system SHALL commit the text and generate a CharEvent

### Requirement 4

**User Story:** As a user typing with IME, I want the candidate window to appear near my cursor, so that I can easily see and select conversion options.

#### Acceptance Criteria

1. WHEN the IME shows candidates THEN the candidate window SHALL appear below the composition text
2. WHEN macOS queries for the first rectangle of marked text THEN the system SHALL return the screen coordinates of the composition text
3. WHEN the composition text is near the bottom of the window THEN the candidate window SHALL appear above the composition text instead
4. WHEN the cursor moves during composition THEN the candidate window position SHALL update accordingly
5. WHEN composition is committed or cancelled THEN the candidate window SHALL disappear

### Requirement 5

**User Story:** As a user typing with IME in different text fields, I want each field to maintain its own composition state, so that switching between fields doesn't lose my input.

#### Acceptance Criteria

1. WHEN a text field has active composition THEN the system SHALL store the composition text associated with that field
2. WHEN focus moves to a different text field THEN the system SHALL clear the previous field's composition
3. WHEN focus returns to a field with uncommitted composition THEN the system SHALL restore the composition state
4. WHEN a dialog closes with active composition THEN the system SHALL discard the composition text
5. WHEN composition is active and the user presses Escape THEN the system SHALL cancel the composition and clear the marked text

### Requirement 6

**User Story:** As a developer, I want the IME implementation to work consistently with the existing CharEvent system, so that text input behaves the same whether using IME or direct keyboard input.

#### Acceptance Criteria

1. WHEN IME commits text THEN the system SHALL generate a CharEvent for each committed character
2. WHEN a CharEvent is generated from IME THEN the text widget SHALL handle it identically to keyboard CharEvent
3. WHEN composition is active THEN the system SHALL NOT generate CharEvent for composition text
4. WHEN composition is cancelled THEN the system SHALL NOT generate any CharEvent
5. WHEN IME inserts multiple characters THEN the system SHALL generate CharEvent for each character in sequence

### Requirement 7

**User Story:** As a user typing with IME, I want command keys to work normally even when IME is active, so that I can use keyboard shortcuts without committing composition.

#### Acceptance Criteria

1. WHEN IME composition is active and user presses Cmd+C THEN the system SHALL execute the copy command without committing composition
2. WHEN IME composition is active and user presses Cmd+V THEN the system SHALL execute the paste command and cancel composition
3. WHEN IME composition is active and user presses Escape THEN the system SHALL cancel the composition without executing other commands
4. WHEN IME composition is active and user presses arrow keys THEN the system SHALL move the cursor within composition text
5. WHEN IME composition is not active and user presses command keys THEN the system SHALL generate KeyEvent as normal

### Requirement 8

**User Story:** As a developer maintaining the codebase, I want IME support to be isolated in the CoreGraphics backend, so that the curses backend and application code remain unchanged.

#### Acceptance Criteria

1. WHEN implementing IME support THEN the system SHALL contain all IME-specific code in the CoreGraphics backend
2. WHEN the curses backend is used THEN the system SHALL NOT load or execute any IME-specific code
3. WHEN the application receives CharEvent THEN the application SHALL NOT need to know whether it came from IME or keyboard
4. WHEN text widgets handle input THEN the widgets SHALL work identically with both backends
5. WHEN IME generates CharEvent THEN the event SHALL be indistinguishable from keyboard-generated CharEvent

### Requirement 9

**User Story:** As a user typing with IME, I want visual feedback during composition, so that I can see what text is being composed before committing it.

#### Acceptance Criteria

1. WHEN composition text is displayed THEN the macOS system SHALL render it with an underline to distinguish it from committed text
2. WHEN composition text contains multiple segments THEN the macOS system SHALL highlight the currently selected segment
3. WHEN the user navigates within composition text THEN the macOS system SHALL update the visual highlighting
4. WHEN composition is committed THEN the macOS system SHALL remove the underline and render the text normally
5. WHEN composition is cancelled THEN the macOS system SHALL remove the composition text from the display

### Requirement 10

**User Story:** As a developer testing IME support, I want to verify that IME works correctly with various input methods, so that I can ensure compatibility across different languages.

#### Acceptance Criteria

1. WHEN testing with Japanese IME THEN the system SHALL correctly handle hiragana input and kanji conversion
2. WHEN testing with Chinese IME THEN the system SHALL correctly handle pinyin input and character selection
3. WHEN testing with Korean IME THEN the system SHALL correctly handle hangul composition
4. WHEN testing with Vietnamese IME THEN the system SHALL correctly handle tone mark composition
5. WHEN switching between different IME languages THEN the system SHALL handle each IME's specific behavior correctly
