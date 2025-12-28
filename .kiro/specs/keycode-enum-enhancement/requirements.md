# Requirements Document

## Introduction

This document specifies the requirements for enhancing TTK's KeyCode enum to include printable characters (alphabet, numbers, space, etc.) and establishing a comprehensive key mapping system for both macOS (CoreGraphics) and curses backends. The enhancement will support multiple keyboard layouts (ANSI, JIS, ISO) with initial focus on ANSI keyboards.

## Glossary

- **KeyCode**: An enumeration in TTK that represents keyboard keys with unique integer values
- **TTK**: Terminal Toolkit - a Python library for building terminal user interfaces
- **CoreGraphics_Backend**: The macOS-specific rendering backend using Apple's CoreGraphics framework
- **Curses_Backend**: The cross-platform terminal rendering backend using the curses library
- **ANSI_Keyboard**: American National Standards Institute keyboard layout (standard US layout)
- **JIS_Keyboard**: Japanese Industrial Standards keyboard layout
- **ISO_Keyboard**: International Organization for Standardization keyboard layout (European)
- **Virtual_Key_Code**: Platform-specific integer code representing a physical key press
- **Printable_Character**: A character that produces visible output when typed (letters, numbers, symbols)
- **Key_Mapper**: A component that translates platform-specific key codes to TTK KeyCode values
- **Keyboard_Layout**: The physical arrangement and mapping of keys on a keyboard

## Requirements

### Requirement 1: KeyCode Enum Extension

**User Story:** As a TTK developer, I want the KeyCode enum to include all printable characters, so that I can handle keyboard input consistently across all key types.

#### Acceptance Criteria

1. THE KeyCode enum SHALL include entries for all letter keys (A-Z, representing the physical keys)
2. THE KeyCode enum SHALL include entries for all digit keys (0-9)
3. THE KeyCode enum SHALL include an entry for the space character
4. THE KeyCode enum SHALL include entries for common punctuation and symbol keys
5. THE KeyCode enum SHALL maintain backward compatibility with existing special key codes (arrows, function keys, etc.)
6. THE KeyCode enum SHALL use a consistent numbering scheme that avoids conflicts between printable and special keys
7. WHEN a letter key is pressed with Shift, THE system SHALL use the same KeyCode with the Shift modifier flag set

### Requirement 2: macOS Key Code Mapping

**User Story:** As a TTK application running on macOS, I want accurate key code translation from macOS virtual key codes to TTK KeyCode values, so that all keyboard input is correctly interpreted.

#### Acceptance Criteria

1. WHEN a macOS virtual key code is received, THE CoreGraphics_Backend SHALL translate it to the corresponding TTK KeyCode value
2. THE CoreGraphics_Backend SHALL support mapping for all printable character keys
3. THE CoreGraphics_Backend SHALL support mapping for all special keys (arrows, function keys, editing keys)
4. THE CoreGraphics_Backend SHALL assume ANSI keyboard layout for initial implementation
5. THE CoreGraphics_Backend SHALL provide a mapping table that can be extended for other keyboard layouts (JIS, ISO)
6. WHEN an unmapped key code is received, THE CoreGraphics_Backend SHALL handle it gracefully without crashing

### Requirement 3: Curses Key Code Mapping

**User Story:** As a TTK application running in a terminal, I want accurate key code translation from curses key codes to TTK KeyCode values, so that keyboard input works consistently across terminal emulators.

#### Acceptance Criteria

1. WHEN a curses key code is received, THE Curses_Backend SHALL translate it to the corresponding TTK KeyCode value
2. THE Curses_Backend SHALL support mapping for all printable character keys
3. THE Curses_Backend SHALL support mapping for all special keys (arrows, function keys, editing keys)
4. THE Curses_Backend SHALL assume ANSI keyboard layout for initial implementation
5. THE Curses_Backend SHALL provide a mapping table that can be extended for other keyboard layouts
6. WHEN an unmapped key code is received, THE Curses_Backend SHALL handle it gracefully without crashing

### Requirement 4: Keyboard Layout Extensibility

**User Story:** As a TTK maintainer, I want the key mapping system to support multiple keyboard layouts, so that future enhancements can add JIS and ISO keyboard support without major refactoring.

#### Acceptance Criteria

1. THE Key_Mapper SHALL be designed with a structure that allows multiple keyboard layout configurations
2. THE Key_Mapper SHALL provide a mechanism to select the active keyboard layout
3. THE Key_Mapper SHALL default to ANSI keyboard layout when no layout is explicitly specified
4. THE Key_Mapper SHALL document the structure needed to add new keyboard layouts (JIS, ISO)
5. WHEN adding a new keyboard layout, THE Key_Mapper SHALL require only adding a new mapping table without modifying core logic

### Requirement 5: Reference Implementation Compatibility

**User Story:** As a TTK developer, I want the key mapping implementation to follow established patterns from reference implementations, so that the system is reliable and maintainable.

#### Acceptance Criteria

1. THE macOS key mapping SHALL reference the keyhac-mac project's key code constants for accuracy
2. THE macOS key mapping SHALL follow the conversion patterns demonstrated in keyhac-mac's keyhac_key.py
3. THE implementation SHALL document any deviations from the reference implementations with clear rationale
4. THE implementation SHALL include comments referencing the source of key code values for maintainability

### Requirement 6: Backward Compatibility

**User Story:** As an existing TTK application, I want the KeyCode enum enhancement to maintain backward compatibility, so that my application continues to work without modifications.

#### Acceptance Criteria

1. WHEN existing code uses current KeyCode values, THE enhanced KeyCode enum SHALL return the same values
2. THE enhanced KeyCode enum SHALL not change the integer values of existing special keys
3. THE enhanced KeyCode enum SHALL not remove any existing KeyCode entries
4. WHEN existing code checks for special keys, THE behavior SHALL remain unchanged
5. THE KeyEvent class SHALL continue to work with both old and new KeyCode values

### Requirement 7: Testing and Validation

**User Story:** As a TTK maintainer, I want comprehensive tests for the key mapping system, so that I can verify correctness across all supported keys and backends.

#### Acceptance Criteria

1. THE test suite SHALL verify that all printable characters map correctly in the CoreGraphics backend
2. THE test suite SHALL verify that all printable characters map correctly in the curses backend
3. THE test suite SHALL verify that all special keys continue to map correctly in both backends
4. THE test suite SHALL verify that modifier keys (Shift, Control, Alt, Command) work correctly with all key types
5. THE test suite SHALL verify backward compatibility with existing KeyCode usage patterns
6. THE test suite SHALL include tests for edge cases (unmapped keys, invalid key codes)
