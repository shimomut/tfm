# Requirements Document

## Introduction

This document specifies the requirements for adding TAB completion functionality to the SingleLineTextEdit component in TFM (Terminal File Manager). TAB completion will allow users to efficiently complete text input by pressing the TAB key, with support for multiple completion behaviors starting with filepath completion. The feature includes an overlay candidate list UI that displays available completions and automatically updates as the user types.

## Glossary

- **SingleLineTextEdit**: The existing single-line text editor component in TFM that handles text input, cursor positioning, and editing operations
- **TAB_Completion**: The feature that completes partial text input when the TAB key is pressed
- **Candidate_List**: An overlay UI component that displays available completion options above or below the text edit field
- **Common_Prefix**: The longest string that is shared by all completion candidates starting from the current input
- **Completion_Behavior**: A strategy for generating completion candidates (e.g., filepath completion, command completion)
- **Filepath_Completion**: A completion behavior that suggests file and directory paths based on the current input
- **Overlay_UI**: A UI component that appears temporarily above or below another component without permanently occupying screen space

## Requirements

### Requirement 1: TAB Key Completion

**User Story:** As a user, I want to press TAB to complete my partial input, so that I can quickly enter text without typing the full content.

#### Acceptance Criteria

1. WHEN the user presses the TAB key, THE SingleLineTextEdit SHALL insert text up to the common prefix of all matching candidates
2. WHEN there is only one matching candidate, THE SingleLineTextEdit SHALL insert the complete candidate text
3. WHEN there are no matching candidates, THE SingleLineTextEdit SHALL not modify the text
4. WHEN the common prefix equals the current input, THE SingleLineTextEdit SHALL not insert any additional text

### Requirement 2: Candidate List Display

**User Story:** As a user, I want to see available completion options in a list, so that I know what completions are available and can choose among them.

#### Acceptance Criteria

1. WHEN TAB completion is triggered and multiple candidates exist, THE Candidate_List SHALL display all matching candidates
2. WHEN the text edit field has sufficient space below it, THE Candidate_List SHALL appear below the text edit field
3. WHEN the text edit field does not have sufficient space below it, THE Candidate_List SHALL appear above the text edit field
4. WHEN the user types additional characters, THE Candidate_List SHALL automatically update to show only candidates matching the new input
5. WHEN the candidate list is reduced to zero matches, THE Candidate_List SHALL hide itself
6. WHEN the candidate list is reduced to one match, THE Candidate_List SHALL continue displaying that single match

### Requirement 3: Filepath Completion Behavior

**User Story:** As a user, I want TAB completion to suggest file and directory paths, so that I can quickly navigate and select files without typing full paths.

#### Acceptance Criteria

1. WHEN filepath completion is active and the user presses TAB, THE System SHALL generate candidates based on filesystem paths matching the current input
2. WHEN the input contains a directory separator, THE System SHALL search for matches within that directory
3. WHEN the input does not contain a directory separator, THE System SHALL search for matches in the current working directory
4. WHEN a completion candidate is a directory, THE System SHALL include a trailing directory separator in the candidate
5. WHEN a completion candidate is a regular file, THE System SHALL not include a trailing directory separator
6. THE System SHALL generate candidates that represent the complete filename or directory name after the last directory separator, including any characters already typed by the user

### Requirement 4: Multiple Completion Behaviors

**User Story:** As a developer, I want the completion system to support multiple completion behaviors, so that different contexts can provide different types of completions.

#### Acceptance Criteria

1. THE SingleLineTextEdit SHALL accept a completion behavior strategy as a configuration parameter
2. WHEN no completion behavior is specified, THE SingleLineTextEdit SHALL not provide TAB completion functionality
3. WHEN a completion behavior is specified, THE SingleLineTextEdit SHALL use that behavior to generate candidates
4. THE completion behavior interface SHALL define a method for generating candidates based on current input

### Requirement 5: Candidate List Interaction

**User Story:** As a user, I want the candidate list to respond to my typing, so that I can narrow down options as I type more characters.

#### Acceptance Criteria

1. WHEN the user types a character while the candidate list is visible, THE Candidate_List SHALL filter candidates to match the updated input
2. WHEN the user deletes a character while the candidate list is visible, THE Candidate_List SHALL expand candidates to match the updated input
3. WHEN the user moves the cursor while the candidate list is visible, THE Candidate_List SHALL remain visible with the same candidates
4. WHEN the user presses ESC while the candidate list is visible, THE Candidate_List SHALL hide itself

### Requirement 6: Visual Presentation

**User Story:** As a user, I want the candidate list to be clearly visible and well-formatted, so that I can easily read and understand the available options.

#### Acceptance Criteria

1. THE Candidate_List SHALL display each candidate on a separate line
2. THE Candidate_List SHALL use appropriate colors and attributes to distinguish itself from the main UI
3. THE Candidate_List SHALL truncate candidates that exceed the available display width
4. WHEN the number of candidates exceeds the available vertical space, THE Candidate_List SHALL display as many candidates as fit and indicate that more exist
5. THE Candidate_List SHALL display a visual border or separator to distinguish it from surrounding UI elements
6. THE Candidate_List SHALL display the complete filename or directory name for each candidate, including any prefix already typed by the user
7. THE Candidate_List SHALL align its horizontal position with the start of the filename or directory name being completed

### Requirement 7: Common Prefix Calculation

**User Story:** As a developer, I want the system to correctly calculate the common prefix of all candidates, so that TAB completion inserts the maximum unambiguous text.

#### Acceptance Criteria

1. WHEN multiple candidates exist, THE System SHALL calculate the longest common prefix shared by all candidates
2. THE common prefix calculation SHALL be case-sensitive
3. THE common prefix calculation SHALL handle empty candidate lists by returning an empty string
4. THE common prefix calculation SHALL handle single-candidate lists by returning the complete candidate

### Requirement 8: Integration with Existing Text Editing

**User Story:** As a user, I want TAB completion to work seamlessly with existing text editing features, so that my editing workflow is not disrupted.

#### Acceptance Criteria

1. WHEN TAB completion inserts text, THE cursor position SHALL move to the end of the inserted text
2. WHEN TAB completion is active, THE existing text editing operations SHALL continue to function normally
3. WHEN the text field loses focus, THE Candidate_List SHALL hide itself
4. WHEN the text field gains focus, THE Candidate_List SHALL not automatically appear until TAB is pressed
