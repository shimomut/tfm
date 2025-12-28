# Design Document

## Overview

This design enhances TTK's KeyCode enum to include all printable characters (letters, numbers, symbols) and establishes comprehensive key mapping systems for both macOS (CoreGraphics) and curses backends. The design maintains backward compatibility while providing a foundation for future keyboard layout support (JIS, ISO).

The key insight is that uppercase and lowercase letters share the same KeyCode value - the distinction is made through the Shift modifier flag. This aligns with how physical keyboards work: pressing 'A' with or without Shift is the same physical key.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     TTK Application                          │
└────────────────────────┬────────────────────────────────────┘
                         │ Uses KeyCode enum
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  KeyCode Enum (Enhanced)                     │
│  - Letters (A-Z): 2000-2025                                 │
│  - Digits (0-9): 2100-2109                                  │
│  - Space: 32 (Unicode)                                      │
│  - Symbols: 2200+ range                                     │
│  - Special keys: 1000+ range (existing)                     │
└────────────────────────┬────────────────────────────────────┘
                         │ Translated by backends
                         ↓
┌──────────────────────────────┬──────────────────────────────┐
│   CoreGraphics Backend       │      Curses Backend          │
│   (macOS)                    │      (Terminal)              │
│                              │                              │
│  ┌────────────────────────┐ │  ┌────────────────────────┐  │
│  │  macOS Virtual Key     │ │  │  Curses Key Code       │  │
│  │  Code Mapper           │ │  │  Mapper                │  │
│  │  - ANSI layout (default)│ │  │  - ANSI layout (default)│ │
│  │  - Extensible for      │ │  │  - Extensible for      │  │
│  │    JIS/ISO             │ │  │    other layouts       │  │
│  └────────────────────────┘ │  └────────────────────────┘  │
└──────────────────────────────┴──────────────────────────────┘
```

### Design Principles

1. **Physical Key Representation**: KeyCode values represent physical keys, not characters
2. **Modifier Independence**: Case and symbols are handled through modifier flags
3. **Backward Compatibility**: Existing KeyCode values remain unchanged
4. **Layout Extensibility**: Architecture supports multiple keyboard layouts
5. **Consistent Numbering**: Clear separation between printable and special keys

## Components and Interfaces

### 1. Enhanced KeyCode Enum

**Location**: `ttk/input_event.py`

**Design**:
```python
class KeyCode(IntEnum):
    """Standard key codes for keyboard keys."""
    
    # Special keys (existing - unchanged)
    ENTER = 10
    ESCAPE = 27
    BACKSPACE = 127
    TAB = 9
    
    # Arrow keys (existing - unchanged)
    UP = 1000
    DOWN = 1001
    LEFT = 1002
    RIGHT = 1003
    
    # Function keys (existing - unchanged)
    F1 = 1100
    F2 = 1101
    # ... F3-F12 ...
    
    # Editing keys (existing - unchanged)
    INSERT = 1200
    DELETE = 1201
    HOME = 1202
    END = 1203
    PAGE_UP = 1204
    PAGE_DOWN = 1205
    
    # Letter keys (NEW - physical keys, case handled by Shift modifier)
    # Range: 2000-2025
    KEY_A = 2000
    KEY_B = 2001
    KEY_C = 2002
    KEY_D = 2003
    KEY_E = 2004
    KEY_F = 2005
    KEY_G = 2006
    KEY_H = 2007
    KEY_I = 2008
    KEY_J = 2009
    KEY_K = 2010
    KEY_L = 2011
    KEY_M = 2012
    KEY_N = 2013
    KEY_O = 2014
    KEY_P = 2015
    KEY_Q = 2016
    KEY_R = 2017
    KEY_S = 2018
    KEY_T = 2019
    KEY_U = 2020
    KEY_V = 2021
    KEY_W = 2022
    KEY_X = 2023
    KEY_Y = 2024
    KEY_Z = 2025
    
    # Digit keys (NEW - physical keys, symbols handled by Shift modifier)
    # Range: 2100-2109
    KEY_0 = 2100
    KEY_1 = 2101
    KEY_2 = 2102
    KEY_3 = 2103
    KEY_4 = 2104
    KEY_5 = 2105
    KEY_6 = 2106
    KEY_7 = 2107
    KEY_8 = 2108
    KEY_9 = 2109
    
    # Space key (NEW - using Unicode code point for consistency)
    SPACE = 32
    
    # Symbol/Punctuation keys (NEW)
    # Range: 2200-2299
    KEY_MINUS = 2200          # - and _
    KEY_EQUAL = 2201          # = and +
    KEY_LEFT_BRACKET = 2202   # [ and {
    KEY_RIGHT_BRACKET = 2203  # ] and }
    KEY_BACKSLASH = 2204      # \ and |
    KEY_SEMICOLON = 2205      # ; and :
    KEY_QUOTE = 2206          # ' and "
    KEY_COMMA = 2207          # , and <
    KEY_PERIOD = 2208         # . and >
    KEY_SLASH = 2209          # / and ?
    KEY_GRAVE = 2210          # ` and ~
```

**Rationale**:
- Letter keys use KEY_A format to clearly indicate physical keys
- Separate ranges (2000s, 2100s, 2200s) for easy categorization
- Space uses Unicode 32 for consistency with existing character handling
- Symbol keys represent physical keys; Shift produces alternate symbols

### 2. macOS Key Mapper

**Location**: `ttk/backends/coregraphics_backend.py`

**Design**:

```python
# macOS Virtual Key Code to TTK KeyCode mapping (ANSI layout)
# Reference: https://gist.github.com/eegrok/949034
# Reference: keyhac-mac project (https://github.com/crftwr/keyhac-mac)

MACOS_ANSI_KEY_MAP = {
    # Letter keys (ANSI positions)
    0x00: KeyCode.KEY_A,
    0x01: KeyCode.KEY_S,
    0x02: KeyCode.KEY_D,
    0x03: KeyCode.KEY_F,
    0x04: KeyCode.KEY_H,
    0x05: KeyCode.KEY_G,
    0x06: KeyCode.KEY_Z,
    0x07: KeyCode.KEY_X,
    0x08: KeyCode.KEY_C,
    0x09: KeyCode.KEY_V,
    0x0B: KeyCode.KEY_B,
    0x0C: KeyCode.KEY_Q,
    0x0D: KeyCode.KEY_W,
    0x0E: KeyCode.KEY_E,
    0x0F: KeyCode.KEY_R,
    0x10: KeyCode.KEY_Y,
    0x11: KeyCode.KEY_T,
    0x1F: KeyCode.KEY_O,
    0x20: KeyCode.KEY_U,
    0x22: KeyCode.KEY_I,
    0x23: KeyCode.KEY_P,
    0x25: KeyCode.KEY_L,
    0x26: KeyCode.KEY_J,
    0x28: KeyCode.KEY_K,
    0x2D: KeyCode.KEY_N,
    0x2E: KeyCode.KEY_M,
    
    # Digit keys
    0x12: KeyCode.KEY_1,
    0x13: KeyCode.KEY_2,
    0x14: KeyCode.KEY_3,
    0x15: KeyCode.KEY_4,
    0x16: KeyCode.KEY_6,
    0x17: KeyCode.KEY_5,
    0x1C: KeyCode.KEY_8,
    0x1D: KeyCode.KEY_0,
    0x19: KeyCode.KEY_9,
    0x1A: KeyCode.KEY_7,
    
    # Symbol/Punctuation keys
    0x1B: KeyCode.KEY_MINUS,        # - and _
    0x18: KeyCode.KEY_EQUAL,        # = and +
    0x21: KeyCode.KEY_LEFT_BRACKET, # [ and {
    0x1E: KeyCode.KEY_RIGHT_BRACKET,# ] and }
    0x2A: KeyCode.KEY_BACKSLASH,    # \ and |
    0x29: KeyCode.KEY_SEMICOLON,    # ; and :
    0x27: KeyCode.KEY_QUOTE,        # ' and "
    0x2B: KeyCode.KEY_COMMA,        # , and <
    0x2F: KeyCode.KEY_PERIOD,       # . and >
    0x2C: KeyCode.KEY_SLASH,        # / and ?
    0x32: KeyCode.KEY_GRAVE,        # ` and ~
    
    # Space
    0x31: KeyCode.SPACE,
    
    # Special keys (existing mappings - unchanged)
    123: KeyCode.LEFT,
    124: KeyCode.RIGHT,
    125: KeyCode.DOWN,
    126: KeyCode.UP,
    122: KeyCode.F1,
    120: KeyCode.F2,
    # ... rest of existing mappings ...
}

# Future: MACOS_JIS_KEY_MAP for Japanese keyboards
# Future: MACOS_ISO_KEY_MAP for European keyboards

class CoreGraphicsBackend(Renderer):
    def __init__(self, keyboard_layout='ANSI', **kwargs):
        """
        Initialize CoreGraphics backend.
        
        Args:
            keyboard_layout: Keyboard layout type ('ANSI', 'JIS', 'ISO')
                           Default: 'ANSI'
        """
        self.keyboard_layout = keyboard_layout
        self._key_map = self._get_key_map(keyboard_layout)
        # ... rest of initialization ...
    
    def _get_key_map(self, layout: str) -> dict:
        """Get the appropriate key map for the keyboard layout."""
        if layout == 'ANSI':
            return MACOS_ANSI_KEY_MAP
        elif layout == 'JIS':
            # Future implementation
            raise NotImplementedError("JIS layout not yet supported")
        elif layout == 'ISO':
            # Future implementation
            raise NotImplementedError("ISO layout not yet supported")
        else:
            raise ValueError(f"Unknown keyboard layout: {layout}")
    
    def _convert_key_event(self, event) -> Optional[KeyEvent]:
        """Convert macOS NSEvent to TTK KeyEvent."""
        key_code = event.keyCode()
        modifiers = self._extract_modifiers(event)
        chars = event.characters()
        char = chars[0] if chars and len(chars) > 0 else None
        
        # Look up in key map
        if key_code in self._key_map:
            ttk_key_code = self._key_map[key_code]
            return KeyEvent(
                key_code=ttk_key_code,
                modifiers=modifiers,
                char=char  # Include character for convenience
            )
        
        # Fallback for unmapped keys
        if char and len(char) == 1:
            code_point = ord(char)
            return KeyEvent(
                key_code=code_point,
                modifiers=modifiers,
                char=char
            )
        
        return None
```

### 3. Curses Key Mapper

**Location**: `ttk/backends/curses_backend.py`

**Design**:

```python
# Curses key code to TTK KeyCode mapping (ANSI layout)
CURSES_ANSI_KEY_MAP = {
    # Letter keys (lowercase ASCII codes)
    ord('a'): KeyCode.KEY_A,
    ord('b'): KeyCode.KEY_B,
    ord('c'): KeyCode.KEY_C,
    ord('d'): KeyCode.KEY_D,
    ord('e'): KeyCode.KEY_E,
    ord('f'): KeyCode.KEY_F,
    ord('g'): KeyCode.KEY_G,
    ord('h'): KeyCode.KEY_H,
    ord('i'): KeyCode.KEY_I,
    ord('j'): KeyCode.KEY_J,
    ord('k'): KeyCode.KEY_K,
    ord('l'): KeyCode.KEY_L,
    ord('m'): KeyCode.KEY_M,
    ord('n'): KeyCode.KEY_N,
    ord('o'): KeyCode.KEY_O,
    ord('p'): KeyCode.KEY_P,
    ord('q'): KeyCode.KEY_Q,
    ord('r'): KeyCode.KEY_R,
    ord('s'): KeyCode.KEY_S,
    ord('t'): KeyCode.KEY_T,
    ord('u'): KeyCode.KEY_U,
    ord('v'): KeyCode.KEY_V,
    ord('w'): KeyCode.KEY_W,
    ord('x'): KeyCode.KEY_X,
    ord('y'): KeyCode.KEY_Y,
    ord('z'): KeyCode.KEY_Z,
    
    # Uppercase letters (map to same KeyCode, Shift handled separately)
    ord('A'): KeyCode.KEY_A,
    ord('B'): KeyCode.KEY_B,
    ord('C'): KeyCode.KEY_C,
    ord('D'): KeyCode.KEY_D,
    ord('E'): KeyCode.KEY_E,
    ord('F'): KeyCode.KEY_F,
    ord('G'): KeyCode.KEY_G,
    ord('H'): KeyCode.KEY_H,
    ord('I'): KeyCode.KEY_I,
    ord('J'): KeyCode.KEY_J,
    ord('K'): KeyCode.KEY_K,
    ord('L'): KeyCode.KEY_L,
    ord('M'): KeyCode.KEY_M,
    ord('N'): KeyCode.KEY_N,
    ord('O'): KeyCode.KEY_O,
    ord('P'): KeyCode.KEY_P,
    ord('Q'): KeyCode.KEY_Q,
    ord('R'): KeyCode.KEY_R,
    ord('S'): KeyCode.KEY_S,
    ord('T'): KeyCode.KEY_T,
    ord('U'): KeyCode.KEY_U,
    ord('V'): KeyCode.KEY_V,
    ord('W'): KeyCode.KEY_W,
    ord('X'): KeyCode.KEY_X,
    ord('Y'): KeyCode.KEY_Y,
    ord('Z'): KeyCode.KEY_Z,
    
    # Digit keys
    ord('0'): KeyCode.KEY_0,
    ord('1'): KeyCode.KEY_1,
    ord('2'): KeyCode.KEY_2,
    ord('3'): KeyCode.KEY_3,
    ord('4'): KeyCode.KEY_4,
    ord('5'): KeyCode.KEY_5,
    ord('6'): KeyCode.KEY_6,
    ord('7'): KeyCode.KEY_7,
    ord('8'): KeyCode.KEY_8,
    ord('9'): KeyCode.KEY_9,
    
    # Symbol keys (unshifted)
    ord('-'): KeyCode.KEY_MINUS,
    ord('='): KeyCode.KEY_EQUAL,
    ord('['): KeyCode.KEY_LEFT_BRACKET,
    ord(']'): KeyCode.KEY_RIGHT_BRACKET,
    ord('\\'): KeyCode.KEY_BACKSLASH,
    ord(';'): KeyCode.KEY_SEMICOLON,
    ord("'"): KeyCode.KEY_QUOTE,
    ord(','): KeyCode.KEY_COMMA,
    ord('.'): KeyCode.KEY_PERIOD,
    ord('/'): KeyCode.KEY_SLASH,
    ord('`'): KeyCode.KEY_GRAVE,
    
    # Symbol keys (shifted - map to same physical key)
    ord('_'): KeyCode.KEY_MINUS,
    ord('+'): KeyCode.KEY_EQUAL,
    ord('{'): KeyCode.KEY_LEFT_BRACKET,
    ord('}'): KeyCode.KEY_RIGHT_BRACKET,
    ord('|'): KeyCode.KEY_BACKSLASH,
    ord(':'): KeyCode.KEY_SEMICOLON,
    ord('"'): KeyCode.KEY_QUOTE,
    ord('<'): KeyCode.KEY_COMMA,
    ord('>'): KeyCode.KEY_PERIOD,
    ord('?'): KeyCode.KEY_SLASH,
    ord('~'): KeyCode.KEY_GRAVE,
    
    # Shifted digit symbols
    ord('!'): KeyCode.KEY_1,
    ord('@'): KeyCode.KEY_2,
    ord('#'): KeyCode.KEY_3,
    ord('$'): KeyCode.KEY_4,
    ord('%'): KeyCode.KEY_5,
    ord('^'): KeyCode.KEY_6,
    ord('&'): KeyCode.KEY_7,
    ord('*'): KeyCode.KEY_8,
    ord('('): KeyCode.KEY_9,
    ord(')'): KeyCode.KEY_0,
    
    # Space
    ord(' '): KeyCode.SPACE,
    
    # Special keys (existing mappings - unchanged)
    curses.KEY_UP: KeyCode.UP,
    curses.KEY_DOWN: KeyCode.DOWN,
    curses.KEY_LEFT: KeyCode.LEFT,
    curses.KEY_RIGHT: KeyCode.RIGHT,
    # ... rest of existing mappings ...
}

class CursesBackend(Renderer):
    def __init__(self, keyboard_layout='ANSI', **kwargs):
        """
        Initialize Curses backend.
        
        Args:
            keyboard_layout: Keyboard layout type ('ANSI', etc.)
                           Default: 'ANSI'
        """
        self.keyboard_layout = keyboard_layout
        self._key_map = self._get_key_map(keyboard_layout)
        # ... rest of initialization ...
    
    def _get_key_map(self, layout: str) -> dict:
        """Get the appropriate key map for the keyboard layout."""
        if layout == 'ANSI':
            return CURSES_ANSI_KEY_MAP
        else:
            raise ValueError(f"Unknown keyboard layout: {layout}")
    
    def _convert_key_event(self, key: int) -> Optional[KeyEvent]:
        """Convert curses key code to TTK KeyEvent."""
        modifiers = ModifierKey.NONE
        
        # Handle shift detection for uppercase letters
        if ord('A') <= key <= ord('Z'):
            modifiers = ModifierKey.SHIFT
        
        # Look up in key map
        if key in self._key_map:
            ttk_key_code = self._key_map[key]
            
            # Determine character representation
            char = chr(key) if 32 <= key <= 126 else None
            
            return KeyEvent(
                key_code=ttk_key_code,
                modifiers=modifiers,
                char=char
            )
        
        # Fallback for unmapped printable characters
        if 32 <= key <= 126:
            return KeyEvent(
                key_code=key,
                modifiers=modifiers,
                char=chr(key)
            )
        
        return None
```

## Data Models

### KeyEvent Enhancement

The existing `KeyEvent` class requires no structural changes but will now receive enhanced KeyCode values:

```python
@dataclass
class KeyEvent(Event):
    """Represents a keyboard command event."""
    key_code: int  # Now includes printable character KeyCodes
    modifiers: int  # Bitwise OR of ModifierKey values
    char: Optional[str] = None  # Character for convenience
```

**Usage Examples**:

```python
# Letter 'a' pressed (no modifiers)
KeyEvent(key_code=KeyCode.KEY_A, modifiers=ModifierKey.NONE, char='a')

# Letter 'A' pressed (with Shift)
KeyEvent(key_code=KeyCode.KEY_A, modifiers=ModifierKey.SHIFT, char='A')

# Digit '5' pressed
KeyEvent(key_code=KeyCode.KEY_5, modifiers=ModifierKey.NONE, char='5')

# Symbol '%' pressed (Shift+5)
KeyEvent(key_code=KeyCode.KEY_5, modifiers=ModifierKey.SHIFT, char='%')

# Space pressed
KeyEvent(key_code=KeyCode.SPACE, modifiers=ModifierKey.NONE, char=' ')

# Ctrl+A pressed
KeyEvent(key_code=KeyCode.KEY_A, modifiers=ModifierKey.CONTROL, char='\x01')
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: KeyCode Value Uniqueness

*For any* two distinct KeyCode enum entries, their integer values must be different.

**Validates: Requirements 1.6**

**Rationale**: This ensures that each key has a unique identifier and prevents ambiguity in key event handling. No two keys should map to the same KeyCode value.

### Property 2: Shift Modifier Consistency for Letters

*For any* letter key (KEY_A through KEY_Z), when pressed with the Shift modifier, the KeyEvent must have the same key_code value but with ModifierKey.SHIFT set in the modifiers field.

**Validates: Requirements 1.7**

**Rationale**: Uppercase and lowercase letters are the same physical key with different modifier states. This property ensures consistent handling across all letter keys.

### Property 3: Backward Compatibility of Existing KeyCodes

*For all* existing KeyCode entries (UP, DOWN, LEFT, RIGHT, F1-F12, ENTER, ESCAPE, BACKSPACE, TAB, INSERT, DELETE, HOME, END, PAGE_UP, PAGE_DOWN), their integer values must remain unchanged from the pre-enhancement implementation.

**Validates: Requirements 1.5, 6.1, 6.2, 6.4**

**Rationale**: Existing TTK applications depend on specific KeyCode values. Changing these values would break backward compatibility and require modifications to all existing code.

### Property 4: CoreGraphics Mapping Correctness

*For any* macOS virtual key code that exists in the MACOS_ANSI_KEY_MAP, the CoreGraphics backend's _convert_key_event method must return a KeyEvent with the corresponding TTK KeyCode value.

**Validates: Requirements 2.1**

**Rationale**: The mapping table defines the contract between macOS key codes and TTK KeyCodes. Every mapped key must translate correctly to ensure accurate keyboard input handling.

### Property 5: CoreGraphics Graceful Error Handling

*For any* macOS virtual key code that does not exist in the MACOS_ANSI_KEY_MAP, the CoreGraphics backend's _convert_key_event method must either return None or a valid KeyEvent without raising an exception.

**Validates: Requirements 2.6**

**Rationale**: Unmapped keys should not crash the application. The backend must handle unknown keys gracefully, either by ignoring them or providing a fallback mapping.

### Property 6: Curses Mapping Correctness

*For any* curses key code that exists in the CURSES_ANSI_KEY_MAP, the Curses backend's _convert_key_event method must return a KeyEvent with the corresponding TTK KeyCode value.

**Validates: Requirements 3.1**

**Rationale**: Similar to CoreGraphics, the curses mapping table defines the contract for terminal-based keyboard input. Every mapped key must translate correctly.

### Property 7: Curses Graceful Error Handling

*For any* curses key code that does not exist in the CURSES_ANSI_KEY_MAP, the Curses backend's _convert_key_event method must either return None or a valid KeyEvent without raising an exception.

**Validates: Requirements 3.6**

**Rationale**: Similar to CoreGraphics, unmapped keys in terminal environments should not crash the application. The backend must handle unknown keys gracefully.

## Error Handling

### Unmapped Key Codes

**Strategy**: When a backend receives a key code that is not in its mapping table:

1. **Primary**: Return `None` to indicate the key is not recognized
2. **Fallback**: For printable ASCII characters (32-126), create a KeyEvent with the character's code point
3. **Never**: Raise an exception or crash the application

**Implementation**:
```python
def _convert_key_event(self, key_code: int) -> Optional[KeyEvent]:
    # Try mapping table first
    if key_code in self._key_map:
        return KeyEvent(key_code=self._key_map[key_code], ...)
    
    # Fallback for printable ASCII
    if 32 <= key_code <= 126:
        return KeyEvent(key_code=key_code, char=chr(key_code), ...)
    
    # Unknown key - return None
    return None
```

### Invalid Keyboard Layout

**Strategy**: When an unsupported keyboard layout is requested:

1. Raise `ValueError` with a clear message during initialization
2. Document supported layouts in the error message
3. Suggest using the default ANSI layout

**Implementation**:
```python
def _get_key_map(self, layout: str) -> dict:
    if layout == 'ANSI':
        return ANSI_KEY_MAP
    elif layout == 'JIS':
        raise NotImplementedError(
            "JIS keyboard layout not yet supported. "
            "Use 'ANSI' layout or contribute JIS support."
        )
    else:
        raise ValueError(
            f"Unknown keyboard layout: {layout}. "
            f"Supported layouts: ANSI"
        )
```

### Modifier Key Detection Failures

**Strategy**: If modifier key state cannot be determined:

1. Default to `ModifierKey.NONE`
2. Log a warning for debugging purposes
3. Continue processing the key event

This ensures the application remains functional even if modifier detection fails.

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests:

- **Unit tests**: Verify specific examples, edge cases, and structural requirements
- **Property tests**: Verify universal properties across all keys and mappings

### Unit Testing Focus

1. **Enum Structure Tests**:
   - Verify all letter keys (KEY_A through KEY_Z) exist
   - Verify all digit keys (KEY_0 through KEY_9) exist
   - Verify all symbol keys exist
   - Verify SPACE key exists
   - Verify existing special keys still exist

2. **Mapping Table Completeness**:
   - Verify CoreGraphics ANSI map includes all printable characters
   - Verify Curses ANSI map includes all printable characters
   - Verify both maps include all special keys

3. **Architecture Tests**:
   - Verify backends accept keyboard_layout parameter
   - Verify default layout is ANSI
   - Verify unsupported layouts raise appropriate errors

4. **Edge Cases**:
   - Unmapped key codes return None or fallback
   - Invalid keyboard layouts raise ValueError
   - KeyEvent works with both old and new KeyCodes

### Property-Based Testing Focus

**Testing Framework**: Use Python's `hypothesis` library for property-based testing.

**Test Configuration**: Each property test must run minimum 100 iterations.

**Property Tests**:

1. **KeyCode Uniqueness** (Property 1):
   - Generate all KeyCode enum values
   - Verify no duplicates exist
   - Tag: **Feature: keycode-enum-enhancement, Property 1: KeyCode Value Uniqueness**

2. **Shift Modifier Consistency** (Property 2):
   - Generate random letter keys (KEY_A through KEY_Z)
   - Create KeyEvents with and without Shift
   - Verify key_code is same, only modifiers differ
   - Tag: **Feature: keycode-enum-enhancement, Property 2: Shift Modifier Consistency for Letters**

3. **Backward Compatibility** (Property 3):
   - Generate all existing special KeyCodes
   - Verify their integer values match expected constants
   - Tag: **Feature: keycode-enum-enhancement, Property 3: Backward Compatibility of Existing KeyCodes**

4. **CoreGraphics Mapping** (Property 4):
   - Generate random macOS virtual key codes from mapping table
   - Verify _convert_key_event returns correct TTK KeyCode
   - Tag: **Feature: keycode-enum-enhancement, Property 4: CoreGraphics Mapping Correctness**

5. **CoreGraphics Error Handling** (Property 5):
   - Generate random unmapped macOS key codes
   - Verify _convert_key_event doesn't crash
   - Tag: **Feature: keycode-enum-enhancement, Property 5: CoreGraphics Graceful Error Handling**

6. **Curses Mapping** (Property 6):
   - Generate random curses key codes from mapping table
   - Verify _convert_key_event returns correct TTK KeyCode
   - Tag: **Feature: keycode-enum-enhancement, Property 6: Curses Mapping Correctness**

7. **Curses Error Handling** (Property 7):
   - Generate random unmapped curses key codes
   - Verify _convert_key_event doesn't crash
   - Tag: **Feature: keycode-enum-enhancement, Property 7: Curses Graceful Error Handling**

### Test Organization

- Unit tests: `ttk/test/test_keycode_enum.py`
- Property tests: `ttk/test/test_keycode_properties.py`
- CoreGraphics integration: `ttk/test/test_coregraphics_keycode_mapping.py`
- Curses integration: `ttk/test/test_curses_keycode_mapping.py`

### Testing Best Practices

- Use descriptive test names that explain what is being tested
- Include comments referencing design properties
- Test both backends independently and together
- Verify backward compatibility with existing test suites
- Use property-based testing for comprehensive coverage
- Keep unit tests focused on specific examples and edge cases
