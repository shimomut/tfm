# Design Document: Modifier Key Bindings

## Overview

This design extends TFM's key binding configuration format to support explicit modifier key notation (Shift, Option/Alt, Control/Ctrl, Command/Cmd) in combination with main keys. The current system only supports simple key expressions and hardcoded modifier combinations (like CTRL_A). This enhancement allows users to configure complex keyboard shortcuts using an intuitive string format like "Shift-Space", "Command-Option-HOME", or "ctrl-alt-left".

The design introduces a key expression parser that converts string representations into structured key information, and a key matcher that compares keyboard events against parsed expressions. The system maintains backward compatibility with existing simple key bindings while adding support for the new modifier key format.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      User Configuration                      │
│                     (_config.py)                            │
│  KEY_BINDINGS = {                                           │
│    'action': ['Shift-Space', 'cmd-alt-left', 'a']          │
│  }                                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   KeyExpressionParser                        │
│  - parse_key_expression(expr: str) -> ParsedKey             │
│  - normalize_modifier_name(name: str) -> ModifierKey        │
│  - normalize_main_key(name: str) -> str                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      ParsedKey                               │
│  - main_key: str                                            │
│  - modifiers: Set[ModifierKey]                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   KeyBindingManager                          │
│  - get_keys_for_action(action) -> List[ParsedKey]          │
│  - Enhanced with modifier support                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      KeyMatcher                              │
│  - matches_event(parsed_key, event) -> bool                │
│  - extract_event_modifiers(event) -> Set[ModifierKey]      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Input Event Handler                        │
│                  (tfm_input_utils.py)                       │
│  - input_event_to_key_char() enhanced                       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Configuration Loading**: User defines key bindings in `_config.py` using the new format
2. **Parsing**: `KeyExpressionParser` converts string expressions to `ParsedKey` objects
3. **Storage**: `KeyBindingManager` stores parsed keys for each action
4. **Event Matching**: When a keyboard event occurs, `KeyMatcher` compares it against parsed keys
5. **Action Dispatch**: Matching events trigger their associated actions

## Components and Interfaces

### ParsedKey Data Class

```python
@dataclass
class ParsedKey:
    """
    Represents a parsed key expression with modifiers.
    
    Attributes:
        main_key: The primary key (e.g., 'space', 'home', 'a')
        modifiers: Set of modifier keys that must be pressed
        original_expr: Original expression string for debugging
    """
    main_key: str
    modifiers: Set[ModifierKey]
    original_expr: str
    
    def matches_event(self, event: KeyEvent) -> bool:
        """Check if this parsed key matches a keyboard event."""
        pass
```

### KeyExpressionParser

```python
class KeyExpressionParser:
    """
    Parser for key expression strings with modifier support.
    
    Handles formats like:
    - Simple: 'a', 'HOME', 'F1'
    - Single modifier: 'Shift-Space', 'ctrl-a'
    - Multiple modifiers: 'Command-Option-HOME', 'ctrl-alt-left'
    """
    
    # Modifier name mappings (case-insensitive)
    MODIFIER_ALIASES = {
        'shift': ModifierKey.SHIFT,
        'option': ModifierKey.ALT,
        'alt': ModifierKey.ALT,
        'control': ModifierKey.CONTROL,
        'ctrl': ModifierKey.CONTROL,
        'command': ModifierKey.COMMAND,
        'cmd': ModifierKey.COMMAND,
    }
    
    # Special key name mappings (case-insensitive)
    SPECIAL_KEY_NAMES = {
        'space': ' ',
        'home': 'HOME',
        'end': 'END',
        'up': 'KEY_UP',
        'down': 'KEY_DOWN',
        'left': 'KEY_LEFT',
        'right': 'KEY_RIGHT',
        'pageup': 'KEY_PPAGE',
        'pagedown': 'KEY_NPAGE',
        'ppage': 'KEY_PPAGE',
        'npage': 'KEY_NPAGE',
        'backspace': 'KEY_BACKSPACE',
        'delete': 'KEY_DC',
        'insert': 'KEY_IC',
        'enter': 'KEY_ENTER',
        'return': 'KEY_ENTER',
        'escape': 'KEY_ESCAPE',
        'esc': 'KEY_ESCAPE',
        'tab': 'KEY_TAB',
        'f1': 'KEY_F1',
        'f2': 'KEY_F2',
        # ... F3-F12
    }
    
    @classmethod
    def parse_key_expression(cls, expr: str) -> ParsedKey:
        """
        Parse a key expression string into a ParsedKey object.
        
        Args:
            expr: Key expression string (e.g., 'Shift-Space', 'a', 'cmd-alt-left')
            
        Returns:
            ParsedKey object with main_key and modifiers
            
        Raises:
            ValueError: If expression is invalid
        """
        pass
    
    @classmethod
    def normalize_modifier_name(cls, name: str) -> ModifierKey:
        """
        Convert a modifier name string to ModifierKey enum.
        
        Args:
            name: Modifier name (case-insensitive)
            
        Returns:
            ModifierKey enum value
            
        Raises:
            ValueError: If modifier name is not recognized
        """
        pass
    
    @classmethod
    def normalize_main_key(cls, name: str) -> str:
        """
        Normalize a main key name to internal representation.
        
        Args:
            name: Main key name (case-insensitive)
            
        Returns:
            Normalized key string
        """
        pass
    
    @classmethod
    def validate_expression(cls, expr: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a key expression without parsing.
        
        Args:
            expr: Key expression string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
```

### KeyMatcher

```python
class KeyMatcher:
    """
    Matches keyboard events against parsed key expressions.
    """
    
    @staticmethod
    def matches_event(parsed_key: ParsedKey, event: KeyEvent) -> bool:
        """
        Check if a parsed key matches a keyboard event.
        
        Args:
            parsed_key: Parsed key expression
            event: Keyboard event from TTK
            
        Returns:
            True if event matches the parsed key
        """
        pass
    
    @staticmethod
    def extract_event_modifiers(event: KeyEvent) -> Set[ModifierKey]:
        """
        Extract modifier keys from a keyboard event.
        
        Args:
            event: Keyboard event from TTK
            
        Returns:
            Set of ModifierKey values
        """
        pass
    
    @staticmethod
    def extract_event_main_key(event: KeyEvent) -> Optional[str]:
        """
        Extract the main key from a keyboard event.
        
        Args:
            event: Keyboard event from TTK
            
        Returns:
            Main key string, or None if cannot be determined
        """
        pass
```

### Enhanced KeyBindingManager

```python
class KeyBindingManager:
    """
    Enhanced manager with modifier key support.
    """
    
    # Cache of parsed keys for performance
    _parsed_keys_cache: Dict[str, ParsedKey] = {}
    
    @staticmethod
    def get_parsed_keys_for_action(action: str) -> List[ParsedKey]:
        """
        Get parsed keys for an action.
        
        Args:
            action: Action name
            
        Returns:
            List of ParsedKey objects
        """
        pass
    
    @staticmethod
    def find_action_for_event(event: KeyEvent, has_selection: bool) -> Optional[str]:
        """
        Find the action that matches a keyboard event.
        
        Args:
            event: Keyboard event
            has_selection: Whether files are selected
            
        Returns:
            Action name, or None if no match
        """
        pass
    
    @staticmethod
    def validate_key_bindings() -> Tuple[bool, List[str]]:
        """
        Validate all key bindings including modifier expressions.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass
```

## Data Models

### Key Expression Format

**Grammar:**
```
key_expression := simple_key | modified_key
simple_key := main_key
modified_key := modifier_list "-" main_key
modifier_list := modifier | modifier "-" modifier_list
modifier := "Shift" | "Option" | "Alt" | "Control" | "Ctrl" | "Command" | "Cmd"
main_key := character | special_key_name
```

**Examples:**
- Simple: `'a'`, `'Q'`, `'HOME'`, `'F1'`, `'space'`
- Single modifier: `'Shift-Space'`, `'ctrl-a'`, `'Command-Q'`
- Multiple modifiers: `'Command-Option-HOME'`, `'ctrl-alt-left'`, `'shift-ctrl-f1'`

**Normalization Rules:**
1. All modifier names are case-insensitive
2. All main key names are case-insensitive
3. Modifier order in the expression doesn't matter for matching
4. Whitespace around hyphens is not allowed

### ParsedKey Structure

```python
ParsedKey(
    main_key='space',
    modifiers={ModifierKey.SHIFT},
    original_expr='Shift-Space'
)

ParsedKey(
    main_key='KEY_LEFT',
    modifiers={ModifierKey.COMMAND, ModifierKey.ALT},
    original_expr='cmd-alt-left'
)

ParsedKey(
    main_key='a',
    modifiers=set(),
    original_expr='a'
)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Modifier-Key Format Parsing

*For any* valid modifier name and main key, formatting them as "{modifier}-{main-key}" or "{modifier}-{modifier}-{main-key}" and parsing should produce a ParsedKey with the correct modifiers and main key.

**Validates: Requirements 1.1, 1.2**

### Property 2: Case Insensitivity

*For any* key expression, changing the case of any modifier name or main key name should produce a ParsedKey with the same modifiers and main key.

**Validates: Requirements 1.3, 1.4**

### Property 3: Modifier Alias Equivalence

*For any* key expression using a modifier alias ("Alt"/"Option", "Ctrl"/"Control", "Cmd"/"Command"), replacing the modifier with its alias should produce a ParsedKey with the same modifier.

**Validates: Requirements 1.6, 1.7, 1.8**

### Property 4: Modifier Order Independence

*For any* key expression with multiple modifiers, permuting the order of modifiers should produce a ParsedKey with the same modifiers set.

**Validates: Requirements 4.6**

### Property 5: Backward Compatibility

*For any* key expression without hyphens (simple key), parsing it should produce a ParsedKey with an empty modifiers set and the correct main key.

**Validates: Requirements 2.1, 2.3, 2.4**

### Property 6: Event Matching Exactness

*For any* ParsedKey and KeyEvent, the event matches the parsed key if and only if the event's modifiers exactly equal the parsed key's modifiers AND the event's main key matches the parsed key's main key.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 7: Validation Consistency

*For any* key expression, if validation succeeds, then parsing must succeed; if validation fails, then parsing must raise an exception.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 8: Configuration Dynamic Updates

*For any* change to KEY_BINDINGS configuration, the help dialog content should reflect the new bindings without requiring a restart.

**Validates: Requirements 7.4**

## Error Handling

### Parser Errors

1. **Empty Expression**: Return error "Key expression cannot be empty"
2. **Invalid Modifier**: Return error "Unknown modifier: {name}"
3. **Missing Main Key**: Return error "Key expression must end with a main key"
4. **Multiple Consecutive Hyphens**: Return error "Invalid format: multiple consecutive hyphens"
5. **Invalid Main Key**: Return error "Unknown key name: {name}"

### Runtime Errors

1. **Configuration Validation**: On startup, validate all KEY_BINDINGS and log errors
2. **Duplicate Bindings**: Warn if the same key expression is bound to multiple actions
3. **Conflicting Bindings**: Warn if a key with modifiers conflicts with a simple key

### Error Recovery

- Invalid key expressions are skipped with a warning logged
- The system continues to function with remaining valid bindings
- Help dialog shows only valid bindings

## Testing Strategy

### Unit Tests

1. **Parser Tests**:
   - Test parsing of simple keys
   - Test parsing of single modifier keys
   - Test parsing of multiple modifier keys
   - Test case insensitivity
   - Test modifier aliases
   - Test error cases (empty, invalid modifier, missing main key)

2. **Matcher Tests**:
   - Test matching events with no modifiers
   - Test matching events with single modifiers
   - Test matching events with multiple modifiers
   - Test non-matching cases (wrong modifier, extra modifier, missing modifier)

3. **Integration Tests**:
   - Test KeyBindingManager with new format
   - Test backward compatibility with existing bindings
   - Test help dialog generation
   - Test configuration validation

### Property-Based Tests

Property-based tests will use Python's `hypothesis` library to generate random inputs and verify the correctness properties defined above. Each test will run a minimum of 100 iterations.

**Test Configuration**:
- Library: `hypothesis`
- Minimum iterations: 100 per property
- Tag format: `# Feature: modifier-key-bindings, Property {N}: {property_text}`

**Property Test Examples**:

1. **Property 1 Test**: Generate random valid key expressions, parse them, format them, parse again, and verify equivalence
2. **Property 2 Test**: Generate random key expressions with multiple modifiers, permute the modifier order, and verify same ParsedKey
3. **Property 3 Test**: Generate random key expressions, vary the case, and verify same ParsedKey
4. **Property 5 Test**: Generate random ParsedKey and matching KeyEvent pairs, verify matching logic
5. **Property 6 Test**: Generate random simple key expressions, verify empty modifiers set

## Implementation Notes

### Performance Considerations

1. **Caching**: Parse key expressions once and cache ParsedKey objects
2. **Set Operations**: Use set operations for fast modifier comparison
3. **Early Exit**: Check main key match before checking modifiers

### Backward Compatibility

The system maintains backward compatibility by:
1. Supporting simple key expressions without hyphens
2. Preserving existing KeyBindingManager API
3. Extending rather than replacing the current format

### Migration Path

Users can migrate gradually:
1. Existing simple bindings continue to work
2. New modifier bindings can be added alongside simple bindings
3. No configuration changes required for existing users

### Configuration Documentation

The `_config.py` file will be updated with:
1. Explanation of the new modifier key format
2. Examples of modifier key expressions
3. List of supported modifier names and aliases
4. List of supported special key names
5. Notes on case-insensitivity and modifier order independence
