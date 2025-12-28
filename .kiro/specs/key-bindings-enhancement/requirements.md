# Requirements Document

## Introduction

This document specifies the requirements for enhancing TFM's key bindings configuration system to support all KeyCode names from TTK and modifier key combinations. The enhancement will replace the legacy SPECIAL_KEY_MAP with direct KeyCode string values and introduce a new KeyBindings class for centralized key binding management.

## Glossary

- **KeyCode**: An enumeration in TTK that represents keyboard keys with unique string values (StrEnum)
- **KeyEvent**: A TTK event object representing a keyboard input with key_code, modifiers, and char fields
- **ModifierKey**: Flags representing modifier keys (Shift, Control, Alt, Command) in TTK
- **Key_Expression**: A string representation of a key binding that may include modifier information
- **KeyBindings_Class**: A new class that manages key bindings and provides lookup functionality
- **Config**: TFM's configuration system that stores user preferences including key bindings
- **SPECIAL_KEY_MAP**: Legacy mapping dictionary from key names to KeyCode values (to be removed)
- **Selection_Requirement**: A constraint on whether an action requires files to be selected ('required', 'none', 'any')

## Requirements

### Requirement 1: Direct KeyCode String Support

**User Story:** As a TFM user, I want to use KeyCode names directly in my configuration, so that I can bind any key supported by TTK without needing a special mapping table.

#### Acceptance Criteria

1. WHEN a key binding uses a KeyCode name string (e.g., "ENTER", "ESCAPE", "TAB"), THE system SHALL recognize it as a valid key binding
2. THE system SHALL support all KeyCode names defined in TTK's KeyCode enum
3. THE system SHALL treat KeyCode name strings as case-insensitive (e.g., "ENTER", "enter", "Enter" are equivalent)
4. THE system SHALL NOT require SPECIAL_KEY_MAP for KeyCode name resolution
5. WHEN a single-character key binding is specified, THE system SHALL maintain backward compatibility with existing character-based bindings

### Requirement 2: Modifier Key Support

**User Story:** As a TFM user, I want to bind actions to key combinations with modifier keys (Shift, Control, Alt, Command), so that I can create more sophisticated key bindings.

#### Acceptance Criteria

1. WHEN a key expression contains a modifier prefix (e.g., "Shift-Down"), THE system SHALL recognize it as a modified key binding
2. THE system SHALL support all modifier keys: Shift, Control, Alt, Command
3. THE system SHALL support multiple modifiers in a single expression (e.g., "Command-Shift-X")
4. THE system SHALL treat modifier names as case-insensitive (e.g., "Shift", "SHIFT", "shift" are equivalent)
5. THE system SHALL treat modifier order as insignificant (e.g., "Command-Shift-X" equals "Shift-Command-X")
6. WHEN a key expression is a single alphabet character (a-z, A-Z), THE system SHALL treat it as case-insensitive (e.g., 'a' and 'A' are the same)
7. WHEN a key expression is a single non-alphabet character (?, /, ., etc.), THE system SHALL treat it as case-sensitive (e.g., '?' and '/' are different)
8. WHEN users want to bind uppercase letters separately, THEY SHALL use "Shift-A" instead of just "A"
9. WHEN a key expression length is greater than 1, THE system SHALL parse it as a key expression with potential modifiers

### Requirement 3: Key Expression Format

**User Story:** As a TFM user, I want a clear and consistent format for specifying key bindings, so that I can easily configure my key mappings.

#### Acceptance Criteria

1. THE key expression format SHALL be "{main-key}" for keys without modifiers
2. THE key expression format SHALL be "{modifier-key}-{main-key}" for keys with one modifier
3. THE key expression format SHALL support multiple modifiers as "{modifier1}-{modifier2}-{main-key}"
4. THE system SHALL use hyphen (-) as the separator between modifier and main key
5. THE main key SHALL be a KeyCode name string (e.g., "DOWN", "ENTER", "A")
6. THE modifier keys SHALL be one of: "Shift", "Control", "Alt", "Command"
7. THE system SHALL parse key expressions case-insensitively

### Requirement 4: KeyBindings Class

**User Story:** As a TFM developer, I want a centralized KeyBindings class to manage key bindings, so that key binding logic is encapsulated and maintainable.

#### Acceptance Criteria

1. THE KeyBindings class SHALL maintain the KEY_BINDINGS configuration from Config
2. THE KeyBindings class SHALL provide a method to lookup an action name from KeyEvent and selection status
3. THE KeyBindings class SHALL provide a method to lookup key expression and selection requirement from an action name
4. THE KeyBindings class SHALL handle both simple key bindings (list of keys) and extended format (dict with 'keys' and 'selection')
5. THE KeyBindings class SHALL respect selection requirements ('required', 'none', 'any') when matching actions
6. THE KeyBindings class SHALL support multiple key bindings per action

### Requirement 5: Action Lookup from KeyEvent

**User Story:** As a TFM developer, I want to find which action corresponds to a KeyEvent, so that I can handle user input correctly.

#### Acceptance Criteria

1. WHEN given a KeyEvent and selection status, THE KeyBindings class SHALL return the matching action name
2. THE lookup SHALL match single-character keys against KeyEvent.char
3. THE lookup SHALL match KeyCode names against KeyEvent.key_code
4. THE lookup SHALL match modifier combinations against KeyEvent.modifiers
5. THE lookup SHALL return None when no matching action is found
6. THE lookup SHALL respect selection requirements when determining matches
7. WHEN multiple actions match, THE lookup SHALL return the first matching action

### Requirement 6: Key Expression Lookup from Action

**User Story:** As a TFM developer, I want to retrieve the key expression for an action, so that I can display it in help dialogs and UI.

#### Acceptance Criteria

1. WHEN given an action name, THE KeyBindings class SHALL return the list of key expressions bound to that action
2. THE KeyBindings class SHALL return the selection requirement for the action
3. WHEN an action has multiple key bindings, THE KeyBindings class SHALL return all of them
4. WHEN an action is not found, THE KeyBindings class SHALL return an empty list
5. THE returned key expressions SHALL be in a format suitable for display to users

### Requirement 7: Backward Compatibility

**User Story:** As an existing TFM user, I want my current key bindings configuration to continue working, so that I don't need to update my config file.

#### Acceptance Criteria

1. WHEN a key binding uses a single character, THE system SHALL continue to match against KeyEvent.char
2. THE system SHALL support existing KEY_BINDINGS format with lists of keys
3. THE system SHALL support existing extended format with 'keys' and 'selection' fields
4. THE system SHALL maintain compatibility with all existing default key bindings
5. WHEN SPECIAL_KEY_MAP names are used in configuration, THE system SHALL still recognize them as KeyCode names

### Requirement 8: SPECIAL_KEY_MAP Removal

**User Story:** As a TFM maintainer, I want to remove the SPECIAL_KEY_MAP dictionary, so that the codebase is simpler and uses KeyCode directly.

#### Acceptance Criteria

1. THE system SHALL NOT use SPECIAL_KEY_MAP for key binding resolution
2. THE system SHALL use KeyCode enum values directly for all key lookups
3. THE system SHALL remove SPECIAL_KEY_MAP from tfm_config.py after migration
4. THE system SHALL remove SPECIAL_KEY_NAMES reverse mapping after migration
5. THE system SHALL update all code that references SPECIAL_KEY_MAP to use the new KeyBindings class

### Requirement 9: Configuration Migration

**User Story:** As a TFM user, I want clear guidance on updating my configuration, so that I can take advantage of new key binding features.

#### Acceptance Criteria

1. THE system SHALL provide documentation on the new key expression format
2. THE system SHALL provide examples of modifier key bindings
3. THE system SHALL document all supported KeyCode names
4. THE system SHALL provide migration examples for common use cases
5. THE system SHALL explain the difference between character keys and KeyCode name keys

### Requirement 10: Testing and Validation

**User Story:** As a TFM maintainer, I want comprehensive tests for the key bindings system, so that I can verify correctness across all key types and modifiers.

#### Acceptance Criteria

1. THE test suite SHALL verify that single-character keys match correctly
2. THE test suite SHALL verify that KeyCode name keys match correctly
3. THE test suite SHALL verify that modifier combinations match correctly
4. THE test suite SHALL verify that selection requirements are respected
5. THE test suite SHALL verify that action lookup returns correct results
6. THE test suite SHALL verify that key expression lookup returns correct results
7. THE test suite SHALL verify backward compatibility with existing configurations
