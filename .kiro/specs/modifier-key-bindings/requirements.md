# Requirements Document

## Introduction

This document specifies requirements for extending TFM's key binding configuration format to support modifier keys (Shift, Option/Alt, Control/Ctrl, Command/Cmd) in combination with main keys. Currently, the KEY_BINDINGS configuration only supports simple key expressions without explicit modifier key notation, limiting the ability to define complex keyboard shortcuts.

## Glossary

- **Config**: The user configuration system that stores KEY_BINDINGS settings
- **Key_Expression**: A string representation of a keyboard shortcut (e.g., "Shift-Space", "cmd-alt-left")
- **Modifier_Key**: A keyboard modifier key (Shift, Option/Alt, Control/Ctrl, Command/Cmd)
- **Main_Key**: The primary key in a keyboard shortcut (e.g., Space, HOME, left, a)
- **Key_Parser**: The component that parses key expression strings into structured key information
- **Key_Matcher**: The component that matches incoming keyboard events against configured key bindings

## Requirements

### Requirement 1: Key Expression Format

**User Story:** As a TFM user, I want to define key bindings using modifier keys, so that I can create more sophisticated keyboard shortcuts.

#### Acceptance Criteria

1. WHEN a key expression contains a single modifier, THE Key_Parser SHALL parse it in the format "{modifier}-{main-key}"
2. WHEN a key expression contains multiple modifiers, THE Key_Parser SHALL parse it in the format "{modifier}-{modifier}-{main-key}"
3. WHEN parsing modifier keys, THE Key_Parser SHALL treat modifier names as case-insensitive
4. WHEN parsing main keys, THE Key_Parser SHALL treat main key names as case-insensitive
5. THE Key_Parser SHALL support "Shift" as a valid modifier name
6. THE Key_Parser SHALL support both "Option" and "Alt" as valid modifier names for the same modifier
7. THE Key_Parser SHALL support both "Control" and "Ctrl" as valid modifier names for the same modifier
8. THE Key_Parser SHALL support both "Command" and "Cmd" as valid modifier names for the same modifier

### Requirement 2: Backward Compatibility

**User Story:** As a TFM user with existing key binding configurations, I want my current simple key bindings to continue working, so that I don't need to update my configuration.

#### Acceptance Criteria

1. WHEN a key expression contains no hyphen, THE Key_Parser SHALL treat it as a simple key without modifiers
2. WHEN processing existing KEY_BINDINGS entries, THE Config SHALL continue to support the current simple format
3. WHEN a key expression is a special key name without modifiers, THE Key_Parser SHALL parse it correctly
4. WHEN a key expression is a single character without modifiers, THE Key_Parser SHALL parse it correctly

**Note:** Case-insensitive parsing means that 'a' and 'A' will be treated as the same key. This is a breaking change from the current behavior where they are distinct, but it provides consistency with the new modifier key format.

### Requirement 3: Key Expression Validation

**User Story:** As a TFM developer, I want invalid key expressions to be detected early, so that configuration errors are caught before runtime.

#### Acceptance Criteria

1. WHEN a key expression contains an unrecognized modifier name, THE Key_Parser SHALL return an error
2. WHEN a key expression contains only modifiers without a main key, THE Key_Parser SHALL return an error
3. WHEN a key expression is an empty string, THE Key_Parser SHALL return an error
4. WHEN a key expression contains multiple consecutive hyphens, THE Key_Parser SHALL return an error

### Requirement 4: Key Matching

**User Story:** As a TFM user, I want keyboard events with modifiers to match my configured key bindings, so that my shortcuts work as expected.

#### Acceptance Criteria

1. WHEN a keyboard event has modifiers, THE Key_Matcher SHALL compare them against the parsed key expression modifiers
2. WHEN a keyboard event's main key matches the parsed main key, THE Key_Matcher SHALL consider it a potential match
3. WHEN all modifiers in the key expression are present in the keyboard event, THE Key_Matcher SHALL consider it a match
4. WHEN the keyboard event has extra modifiers not specified in the key expression, THE Key_Matcher SHALL NOT consider it a match
5. WHEN the keyboard event is missing modifiers specified in the key expression, THE Key_Matcher SHALL NOT consider it a match
6. WHEN comparing modifier keys, THE Key_Matcher SHALL treat the order of modifiers as irrelevant

### Requirement 5: Configuration Integration

**User Story:** As a TFM user, I want to use the new modifier key format in my KEY_BINDINGS configuration, so that I can define advanced shortcuts.

#### Acceptance Criteria

1. WHEN KEY_BINDINGS contains a key expression with modifiers, THE Config SHALL parse it using the Key_Parser
2. WHEN KEY_BINDINGS contains both simple and modifier key expressions, THE Config SHALL support both formats
3. WHEN an action has multiple key bindings with different modifier combinations, THE Config SHALL support all of them
4. WHEN loading KEY_BINDINGS, THE Config SHALL validate all key expressions

### Requirement 6: Documentation and Examples

**User Story:** As a TFM user, I want clear documentation on the modifier key format, so that I can configure my key bindings correctly.

#### Acceptance Criteria

1. WHEN viewing the configuration file, THE Config SHALL include comments explaining the modifier key format
2. WHEN viewing the configuration file, THE Config SHALL include examples of modifier key expressions
3. WHEN viewing the configuration file, THE Config SHALL list all supported modifier key names
4. WHEN viewing the configuration file, THE Config SHALL explain case-insensitivity rules

### Requirement 7: Help Dialog Integration

**User Story:** As a TFM user, I want the help dialog to display my key bindings with modifier keys correctly, so that I can see what shortcuts are available.

#### Acceptance Criteria

1. WHEN displaying key bindings in the help dialog, THE HelpDialog SHALL show modifier key expressions in their configured format
2. WHEN a key binding uses modifiers, THE HelpDialog SHALL display them in a readable format
3. WHEN generating help content, THE HelpDialog SHALL NOT use hardcoded key binding strings
4. WHEN KEY_BINDINGS configuration changes, THE HelpDialog SHALL reflect those changes dynamically
