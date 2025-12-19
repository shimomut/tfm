# Design Document

## Overview

This design introduces a new `CharEvent` class to represent character input events, distinct from the existing `KeyEvent` class which represents command key events. The separation allows the system to properly distinguish between text input (typing characters) and command execution (keyboard shortcuts), improving text input handling and preventing conflicts between text entry and command bindings.

### Key Architectural Decisions

1. **Dual Event Delivery:** The system delivers both KeyEvent and CharEvent separately
   - KeyEvent: For command handling (Q to quit, arrows for navigation)
   - CharEvent: For text input (typing characters)

2. **Callback-Based Event System (Both Modes):**
   - Replace polling (`get_event()`) with callback system for consistency
   - Backend delivers KeyEvent first via `on_key_event()` callback
   - If not consumed, backend delivers CharEvent via `on_char_event()` callback
   - Enables proper IME support in the future

3. **Backend-Specific Translation:**
   - **Terminal Mode (curses):** Backend translates unconsumed KeyEvent to CharEvent
   - **Desktop Mode (CoreGraphics):** OS translates via NSTextInputClient protocol

4. **Backward Compatibility:**
   - `get_event()` polling maintained for backward compatibility
   - New callback system is opt-in via `set_event_callback()`
   - Existing TFM key bindings continue to work
   - Gradual migration path from polling to callbacks

### Why Keep get_event() for Backward Compatibility?

The `get_event()` polling method must be maintained because:

1. **Existing Code Dependency:**
   - All current TFM code uses `get_event()` in the main loop
   - Removing it would break the entire application immediately
   - No gradual migration path without it

2. **Testing and Development:**
   - Unit tests use `get_event()` to simulate input
   - Demo scripts rely on polling for controlled event delivery
   - Removing it would break hundreds of tests

3. **Simpler Mental Model:**
   - Polling is easier to understand and debug
   - Callbacks require understanding event-driven programming
   - Some developers prefer explicit control flow

4. **Gradual Migration Strategy:**
   - Phase 1: Add callback system alongside polling
   - Phase 2: Migrate main application to callbacks
   - Phase 3: Migrate tests and demos
   - Phase 4: Deprecate (but not remove) `get_event()`

5. **Fallback Mechanism:**
   - If callbacks have issues, polling provides a fallback
   - Useful for debugging callback-related problems
   - Allows running in "compatibility mode"

**Implementation Strategy:**
```python
class Renderer:
    def get_event(self, timeout_ms: int = -1) -> Optional[Event]:
        """
        Get event (polling mode - for backward compatibility).
        
        This method is maintained for:
        - Backward compatibility with existing code
        - Unit testing and demo scripts
        - Gradual migration to callback-based system
        
        When callbacks are enabled, this method may return None
        as events are delivered via callbacks instead.
        """
        if self.event_callback:
            # Callbacks enabled - process events but don't return them
            # (they're delivered via callbacks)
            self._process_events(timeout_ms)
            return None
        else:
            # Callbacks disabled - use traditional polling
            return self._poll_event(timeout_ms)
```

Existing code that handles events will be updated to check event types explicitly using `isinstance()` checks.

## Architecture

### Event Type Hierarchy

```
Event (base class)
├── KeyEvent (command keys, shortcuts)
├── CharEvent (text input) [NEW]
├── MouseEvent (mouse input)
├── SystemEvent (resize, close)
└── MenuEvent (menu selections)
```

### Event Generation Flow

#### Terminal Mode (Curses Backend)

```
User Input
    ↓
Curses Backend Event Loop
    ├── Poll via getch()
    ├── Generate KeyEvent
    └── Deliver via on_key_event() callback
    ↓
Application Event Handler (TFM)
    ├── Command matched? → Return True (consumed)
    └── Not matched? → Return False (not consumed)
    ↓
Curses Backend
    ├── KeyEvent consumed? → Done
    └── Not consumed? → Translate to CharEvent
        ↓
        Deliver via on_char_event() callback
        ↓
        Text Input Widget
        └── Handle CharEvent (insert character)
```

#### Desktop Mode (CoreGraphics Backend)

```
User Input
    ↓
macOS Event System
    ↓
CoreGraphics Backend (NSTextInputClient)
    ├── keyDown: → Generate KeyEvent
    └── Deliver via on_key_event() callback
    ↓
Application Event Handler (TFM)
    ├── Command matched? → Return True (consumed) → Done
    └── Not matched? → Return False (not consumed)
    ↓
macOS Text Input System
    ├── interpretKeyEvents:
    └── insertText: → Generate CharEvent
        ↓
        Deliver via on_char_event() callback
        ↓
        Text Input Widget
        └── Handle CharEvent (insert character)
```

### Component Interaction

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer (TFM)               │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Command Handler (FileManager)            │   │
│  │  - Receives KeyEvent                             │   │
│  │  - Returns True if consumed, False if not        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                        ↓ KeyEvent
┌─────────────────────────────────────────────────────────┐
│              Event Handling Layer (TFM Main Loop)        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  KeyEvent → CharEvent Translation                │   │
│  │  - If KeyEvent not consumed                      │   │
│  │  - And is printable character                    │   │
│  │  - Translate to CharEvent                        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                        ↓ CharEvent
┌─────────────────────────────────────────────────────────┐
│                  Text Input Widget Layer                 │
│  ┌──────────────────┐                                    │
│  │ SingleLineEdit   │                                    │
│  │ Handles CharEvent│                                    │
│  └──────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
                        ↑ KeyEvent (always)
┌─────────────────────────────────────────────────────────┐
│                      TTK Event System                    │
│  ┌──────────────────┐         ┌────────────────────┐   │
│  │   CharEvent      │         │    KeyEvent        │   │
│  │  - char: str     │         │  - key_code: int   │   │
│  └──────────────────┘         │  - modifiers: int  │   │
│                                │  - char: Optional  │   │
│                                └────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                        ↑ KeyEvent (always)
┌─────────────────────────────────────────────────────────┐
│                    Backend Layer                         │
│  ┌──────────────────┐         ┌────────────────────┐   │
│  │ Curses Backend   │         │ CoreGraphics       │   │
│  │ _translate_key() │         │ _translate_event() │   │
│  │ Always KeyEvent  │         │ Always KeyEvent    │   │
│  └──────────────────┘         └────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Event Callback Interface (New)

**Location:** `ttk/renderer.py` (base class)

**Purpose:** Define callback interface for event delivery

**Interface:**
```python
class EventCallback:
    """
    Callback interface for event delivery.
    
    Backends call these methods to deliver events to the application.
    The application implements these methods to handle events.
    """
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """
        Handle a key event.
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed (handled), False otherwise
        """
        return False
    
    def on_char_event(self, event: CharEvent) -> bool:
        """
        Handle a character event.
        
        Args:
            event: CharEvent to handle
        
        Returns:
            True if the event was consumed (handled), False otherwise
        """
        return False
    
    def on_system_event(self, event: SystemEvent) -> bool:
        """
        Handle a system event (resize, close, etc.).
        
        Args:
            event: SystemEvent to handle
        
        Returns:
            True if the event was consumed (handled), False otherwise
        """
        return False
```

**Backend Integration:**
```python
class Renderer:
    """Base renderer class."""
    
    def set_event_callback(self, callback: Optional[EventCallback]) -> None:
        """
        Set the event callback for event delivery.
        
        Args:
            callback: EventCallback instance or None to disable callbacks
        """
        self.event_callback = callback
    
    def get_event(self, timeout_ms: int = -1) -> Optional[Event]:
        """
        Get event (polling mode - for backward compatibility).
        
        This method is maintained for terminal mode and backward compatibility.
        Desktop mode should use callbacks via set_event_callback().
        """
        pass
```

### 2. CharEvent Class (New)

**Location:** `ttk/input_event.py`

**Purpose:** Represents a character intended for text input.

**Interface:**
```python
@dataclass
class CharEvent(Event):
    """
    Represents a character input event for text entry.
    
    CharEvent is generated when the user types a printable character
    without command modifiers (Ctrl, Alt, Cmd). It is used by text
    input widgets to insert characters into text fields.
    """
    char: str  # The character to insert (single Unicode character)
    
    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"CharEvent(char={repr(self.char)})"
```

**Attributes:**
- `char`: A single Unicode character string representing the character to insert

**Methods:**
- `__repr__()`: Returns a readable string representation for debugging

### 2. KeyEvent Class (Modified)

**Location:** `ttk/input_event.py`

**Purpose:** Represents a keyboard command or shortcut.

**Changes:**
- No structural changes to the class
- Usage context changes: Now explicitly for commands, not text input
- Documentation updated to clarify distinction from CharEvent

**Existing Interface:**
```python
@dataclass
class KeyEvent(Event):
    """
    Represents a keyboard command event.
    
    KeyEvent is generated for:
    - Special keys (arrows, function keys, etc.)
    - Printable keys with command modifiers (Ctrl, Alt, Cmd)
    - Command shortcuts (Q to quit, A to select all, etc.)
    """
    key_code: int  # KeyCode value or Unicode code point
    modifiers: int  # Bitwise OR of ModifierKey values
    char: Optional[str] = None  # Character for printable keys (legacy)
```

### 3. Backend Event Translation

#### Curses Backend (Terminal Mode)

**Location:** `ttk/backends/curses_backend.py`

**Changes:**
- **No changes to event generation** - continues to generate KeyEvent for all inputs via `get_event()`
- Maintains polling-based event delivery
- TFM application layer handles KeyEvent → CharEvent translation

**Existing Logic (unchanged):**
```python
def get_event(self, timeout_ms: int = -1) -> Optional[Event]:
    # Poll for keyboard input
    key = self.stdscr.getch()
    if key == -1:
        return None
    return self._translate_curses_key(key)

def _translate_curses_key(self, key: int) -> Event:
    # Special keys → KeyEvent
    if key in key_map:
        return KeyEvent(key_code=key_map[key], modifiers=modifiers)
    
    # Printable ASCII → KeyEvent with char field
    if 32 <= key <= 126:
        return KeyEvent(key_code=key, modifiers=modifiers, char=chr(key))
    
    # Control characters → KeyEvent
    if key in [10, 13, 27, 9, 127]:
        return KeyEvent(key_code=KeyCode.XXX, modifiers=modifiers)
    
    # Default → KeyEvent
    return KeyEvent(key_code=key, modifiers=modifiers)
```

#### CoreGraphics Backend (Desktop Mode)

**Location:** `ttk/backends/coregraphics_backend.py`

**Changes:**
- **Add callback-based event delivery** using NSTextInputClient protocol
- Implement `keyDown:` to deliver KeyEvent via callback
- Implement `insertText:` to deliver CharEvent via callback
- Maintain `get_event()` for backward compatibility (polling mode)

**New Callback-Based Logic:**
```python
class TTKView(Cocoa.NSView):
    """Custom NSView that implements NSTextInputClient protocol."""
    
    def keyDown_(self, event):
        """
        Handle key down event from macOS.
        
        This is called by macOS when a key is pressed. We translate it to
        KeyEvent and deliver via callback. If not consumed, macOS will call
        insertText: with the character.
        """
        # Translate NSEvent to KeyEvent
        key_event = self.backend._translate_event(event)
        
        if key_event and self.backend.event_callback:
            # Deliver KeyEvent via callback
            consumed = self.backend.event_callback.on_key_event(key_event)
            
            if consumed:
                # Application consumed the event - don't pass to input system
                return
        
        # Not consumed - pass to input system for character translation
        # macOS will call insertText: if this produces a character
        self.interpretKeyEvents_([event])
    
    def insertText_(self, string):
        """
        Handle character input from macOS text input system.
        
        This is called by macOS when a key event produces a character
        (after keyDown: was not consumed). We translate it to CharEvent
        and deliver via callback.
        """
        if not string or len(string) == 0:
            return
        
        # Create CharEvent for each character
        for char in string:
            char_event = CharEvent(char=char)
            
            if self.backend.event_callback:
                self.backend.event_callback.on_char_event(char_event)
    
    def hasMarkedText(self) -> bool:
        """Required by NSTextInputClient - for IME support (future)."""
        return False
    
    def markedRange(self):
        """Required by NSTextInputClient - for IME support (future)."""
        return Cocoa.NSMakeRange(Cocoa.NSNotFound, 0)
    
    # ... other NSTextInputClient methods for IME support (future)
```

**Backward Compatible Polling:**
```python
def get_event(self, timeout_ms: int = -1) -> Optional[Event]:
    """
    Get event (polling mode - for backward compatibility).
    
    In desktop mode with callbacks enabled, this method processes the
    event loop but events are delivered via callbacks. Without callbacks,
    events are queued and returned via polling.
    """
    # Process macOS event loop
    app = Cocoa.NSApplication.sharedApplication()
    event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(...)
    
    if event and not self.event_callback:
        # No callback - queue event for polling
        return self._translate_event(event)
    
    return None
```

### 4. Event Translation Layer (Terminal Mode Only)

**Location:** `src/tfm_main.py` (or new module `src/tfm_event_translator.py`)

**Purpose:** Translates unconsumed KeyEvent to CharEvent for text input (terminal mode only)

**Interface:**
```python
def translate_key_to_char(event: KeyEvent) -> Optional[CharEvent]:
    """
    Translate a KeyEvent to CharEvent if it represents a printable character.
    
    This is only used in terminal mode. Desktop mode uses OS-provided translation.
    
    Args:
        event: KeyEvent that was not consumed by the application
    
    Returns:
        CharEvent if the KeyEvent represents a printable character,
        None otherwise
    """
    # Only translate if no command modifiers
    if event.modifiers & (ModifierKey.CONTROL | ModifierKey.ALT | ModifierKey.COMMAND):
        return None
    
    # Only translate if has printable character
    if event.char and len(event.char) == 1 and event.char.isprintable():
        return CharEvent(char=event.char)
    
    return None
```

**Integration in Main Loop (Both Modes - Unified):**
```python
class TFMEventCallback(EventCallback):
    """Event callback implementation for TFM (used by both terminal and desktop modes)."""
    
    def __init__(self, app):
        self.app = app
    
    def on_key_event(self, event: KeyEvent) -> bool:
        """Handle KeyEvent - return True if consumed."""
        return self.app.handle_command(event)
    
    def on_char_event(self, event: CharEvent) -> bool:
        """Handle CharEvent - pass to active text widget."""
        if self.app.active_text_widget:
            return self.app.active_text_widget.handle_key(event)
        return False
    
    def on_system_event(self, event: SystemEvent) -> bool:
        """Handle SystemEvent (resize, close, etc.)."""
        if event.is_resize():
            self.app.handle_resize()
            return True
        elif event.is_close():
            self.app.quit()
            return True
        return False

def main_loop(self):
    """Main loop for both terminal and desktop modes (callback-based)."""
    # Set up event callback
    callback = TFMEventCallback(self)
    self.backend.set_event_callback(callback)
    
    # Run backend event loop
    # Terminal mode: runs curses event loop
    # Desktop mode: runs macOS NSApplication event loop
    self.backend.run_event_loop()
```

### 5. Application Event Handlers

#### SingleLineTextEdit

**Location:** `src/tfm_single_line_text_edit.py`

**Method:** `handle_key(event, handle_vertical_nav=False) -> bool`

**Changes:**
- Add `isinstance()` check to distinguish `CharEvent` from `KeyEvent`
- Handle `CharEvent` by inserting the character
- Handle `KeyEvent` for navigation and editing commands

**Updated Logic:**
```python
def handle_key(self, event, handle_vertical_nav=False) -> bool:
    if not event:
        return False
    
    # Handle CharEvent - text input (new)
    if isinstance(event, CharEvent):
        return self.insert_char(event.char)
    
    # Handle KeyEvent - navigation and editing commands
    if isinstance(event, KeyEvent):
        if event.key_code == KeyCode.LEFT:
            return self.move_cursor_left()
        elif event.key_code == KeyCode.RIGHT:
            return self.move_cursor_right()
        elif event.key_code == KeyCode.HOME:
            return self.move_cursor_home()
        elif event.key_code == KeyCode.END:
            return self.move_cursor_end()
        elif event.key_code == KeyCode.BACKSPACE:
            return self.backspace()
        elif event.key_code == KeyCode.DELETE:
            return self.delete_char_at_cursor()
        # Note: Printable characters are NOT handled here anymore
        # They come as CharEvent after translation
    
    return False
```

#### File Manager Command Handler

**Location:** `src/tfm_main.py` (and other command handling code)

**Changes:**
- Add `isinstance()` check to verify event is `KeyEvent`
- Ignore `CharEvent` in command handling code
- Maintain existing command key bindings

**Updated Logic:**
```python
def handle_input(self, event):
    # Only handle KeyEvent in command context
    # CharEvent should never reach here (handled by text widgets)
    if not isinstance(event, KeyEvent):
        return False
    
    # Handle KeyEvent commands
    if event.char == 'q' or event.char == 'Q':
        self.quit()
        return True  # Consumed
    elif event.char == 'a' or event.char == 'A':
        self.select_all()
        return True  # Consumed
    elif event.key_code == KeyCode.UP:
        self.move_cursor_up()
        return True  # Consumed
    # ... other commands
    
    return False  # Not consumed - can be translated to CharEvent
```

## Data Models

### Event Type Enumeration

No new enumeration needed. Event types are distinguished by class type using `isinstance()`.

### Event Classification Rules

**Backend Generation (Always KeyEvent):**
1. All keyboard input generates KeyEvent at the backend level
2. Printable characters include `char` field in KeyEvent
3. Special keys have KeyCode and no `char` field
4. Modifiers are captured in `modifiers` field

**Translation to CharEvent (Application Layer):**
1. KeyEvent was not consumed by application (returned False)
2. KeyEvent has no command modifiers (Ctrl, Alt, Cmd)
3. KeyEvent has printable `char` field
4. Shift modifier is allowed (for uppercase letters)

**Event Consumption:**
1. Application returns True if KeyEvent is consumed (command executed)
2. Application returns False if KeyEvent is not consumed
3. Unconsumed KeyEvent with printable char → translated to CharEvent
4. CharEvent is passed to active text input widget

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Backends always generate KeyEvent

*For any* keyboard input, both backends (curses and CoreGraphics) should generate a KeyEvent.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

### Property 2: Printable KeyEvent includes char field

*For any* printable character input, the generated KeyEvent should include the character in the `char` field.

**Validates: Requirements 2.1, 1.4**

### Property 3: Unconsumed printable KeyEvent translates to CharEvent

*For any* KeyEvent with a printable `char` field and no command modifiers, if the application does not consume it, the system should translate it to a CharEvent.

**Validates: Requirements 1.1, 2.1, 7.4**

### Property 4: Command modifiers prevent CharEvent translation

*For any* KeyEvent with Ctrl, Alt, or Cmd modifiers, the system should not translate it to CharEvent even if unconsumed.

**Validates: Requirements 7.1, 7.2, 7.3**

### Property 5: CharEvent contains only printable characters

*For any* CharEvent generated by translation, the `char` field should contain exactly one printable Unicode character.

**Validates: Requirements 2.3**

### Property 6: Text input widgets accept CharEvent

*For any* CharEvent received by a text input widget, the widget should insert the character at the cursor position.

**Validates: Requirements 2.2**

### Property 7: Consumed KeyEvent prevents translation

*For any* KeyEvent that is consumed by the application (returns True), the system should not translate it to CharEvent.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 8: Special keys remain as KeyEvent

*For any* special key input (arrows, function keys, Home, End, etc.), the KeyEvent should not be translated to CharEvent.

**Validates: Requirements 3.5, 1.2**

### Property 9: Type checking prevents confusion

*For any* code that handles both CharEvent and KeyEvent, using `isinstance()` checks should correctly distinguish between the two types.

**Validates: Requirements 4.1, 4.2, 4.4**

### Property 10: Shift+character translates to CharEvent

*For any* printable character typed with only the Shift modifier, if unconsumed, the system should translate the KeyEvent to a CharEvent with the shifted character.

**Validates: Requirements 7.5**

## Error Handling

### Invalid CharEvent Creation

**Scenario:** Attempt to create CharEvent with non-printable or multi-character string

**Handling:**
- Backend validation ensures only single printable characters create CharEvent
- Invalid inputs generate KeyEvent instead
- No exceptions thrown; graceful fallback to KeyEvent

### Missing isinstance() Checks

**Scenario:** Code assumes KeyEvent without type checking

**Handling:**
- Gradual migration: existing code continues to work with KeyEvent
- CharEvent has no `key_code` attribute, causing AttributeError if accessed
- AttributeError indicates missing type check; add `isinstance()` check

### Backend Inconsistency

**Scenario:** Backends generate different event types for same input

**Handling:**
- Unit tests verify backend consistency
- Integration tests compare backend behavior
- Bugs fixed in backend translation logic

## Testing Strategy

### Unit Tests

**Test Coverage:**
1. CharEvent creation and attributes
2. KeyEvent creation with modifiers
3. Backend event translation logic
4. SingleLineTextEdit CharEvent handling
5. Command handler KeyEvent handling
6. Type checking with isinstance()

**Example Tests:**
```python
def test_char_event_creation():
    """Test CharEvent with printable character."""
    event = CharEvent(char='a')
    assert event.char == 'a'
    assert isinstance(event, CharEvent)
    assert isinstance(event, Event)

def test_key_event_with_modifier():
    """Test KeyEvent with Ctrl modifier."""
    event = KeyEvent(key_code=ord('c'), modifiers=ModifierKey.CONTROL, char='c')
    assert event.key_code == ord('c')
    assert event.has_modifier(ModifierKey.CONTROL)
    assert isinstance(event, KeyEvent)

def test_backend_generates_char_event():
    """Test backend generates CharEvent for printable character."""
    backend = CursesBackend()
    event = backend._translate_curses_key(ord('a'))
    assert isinstance(event, CharEvent)
    assert event.char == 'a'

def test_backend_generates_key_event_for_special():
    """Test backend generates KeyEvent for arrow key."""
    backend = CursesBackend()
    event = backend._translate_curses_key(curses.KEY_UP)
    assert isinstance(event, KeyEvent)
    assert event.key_code == KeyCode.UP

def test_text_edit_handles_char_event():
    """Test SingleLineTextEdit inserts character from CharEvent."""
    editor = SingleLineTextEdit()
    event = CharEvent(char='x')
    result = editor.handle_key(event)
    assert result == True
    assert editor.get_text() == 'x'

def test_text_edit_handles_key_event():
    """Test SingleLineTextEdit handles navigation KeyEvent."""
    editor = SingleLineTextEdit(initial_text='hello')
    editor.set_cursor_pos(5)
    event = KeyEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.NONE)
    result = editor.handle_key(event)
    assert result == True
    assert editor.get_cursor_pos() == 4

def test_command_handler_ignores_char_event():
    """Test command handler ignores CharEvent."""
    # Simulate command handler receiving CharEvent
    event = CharEvent(char='q')
    # Command handler should not quit on CharEvent
    assert not should_handle_as_command(event)

def test_isinstance_distinguishes_events():
    """Test isinstance() correctly distinguishes event types."""
    char_event = CharEvent(char='a')
    key_event = KeyEvent(key_code=KeyCode.UP, modifiers=ModifierKey.NONE)
    
    assert isinstance(char_event, CharEvent)
    assert not isinstance(char_event, KeyEvent)
    assert isinstance(key_event, KeyEvent)
    assert not isinstance(key_event, CharEvent)
```

### Integration Tests

**Test Scenarios:**
1. End-to-end text input in SingleLineTextEdit
2. Command execution with keyboard shortcuts
3. Mixed text input and command usage
4. Backend consistency across curses and CoreGraphics
5. Modifier key combinations

**Example Integration Tests:**
```python
def test_text_input_workflow():
    """Test complete text input workflow."""
    backend = CoreGraphicsBackend()
    editor = SingleLineTextEdit()
    
    # Simulate typing "hello"
    for char in "hello":
        event = CharEvent(char=char)
        editor.handle_key(event)
    
    assert editor.get_text() == "hello"

def test_command_workflow():
    """Test command execution workflow."""
    backend = CoreGraphicsBackend()
    file_manager = FileManager()
    
    # Simulate pressing 'q' to quit
    event = KeyEvent(key_code=ord('q'), modifiers=ModifierKey.NONE, char='q')
    file_manager.handle_input(event)
    
    assert file_manager.should_quit == True

def test_mixed_input_workflow():
    """Test mixing text input and commands."""
    editor = SingleLineTextEdit()
    
    # Type some text
    editor.handle_key(CharEvent(char='t'))
    editor.handle_key(CharEvent(char='e'))
    editor.handle_key(CharEvent(char='s'))
    editor.handle_key(CharEvent(char='t'))
    
    # Use arrow key to move cursor
    editor.handle_key(KeyEvent(key_code=KeyCode.LEFT, modifiers=ModifierKey.NONE))
    
    # Type more text
    editor.handle_key(CharEvent(char='x'))
    
    assert editor.get_text() == "tesxt"
```

### Property-Based Tests

Property-based tests will be implemented using Python's `hypothesis` library to verify the correctness properties across many randomly generated inputs.

**Test Configuration:**
- Minimum 100 iterations per property test
- Random generation of characters, key codes, and modifier combinations
- Each test tagged with property number from design document

**Property Test Examples:**
```python
from hypothesis import given, strategies as st

@given(st.characters(min_codepoint=32, max_codepoint=126))
def test_property_1_char_event_printable(char):
    """
    Property 1: CharEvent contains only printable characters
    Feature: char-event-text-input, Property 1
    """
    event = CharEvent(char=char)
    assert len(event.char) == 1
    assert event.char.isprintable()

@given(
    st.integers(min_value=32, max_value=126),
    st.sampled_from([ModifierKey.CONTROL, ModifierKey.ALT, ModifierKey.COMMAND])
)
def test_property_2_modifiers_generate_key_event(key_code, modifier):
    """
    Property 2: KeyEvent generated for command modifiers
    Feature: char-event-text-input, Property 2
    """
    backend = CursesBackend()
    # Simulate input with modifier
    # (Implementation depends on backend mock)
    event = KeyEvent(key_code=key_code, modifiers=modifier)
    assert isinstance(event, KeyEvent)
    assert not isinstance(event, CharEvent)

@given(st.sampled_from([KeyCode.UP, KeyCode.DOWN, KeyCode.LEFT, KeyCode.RIGHT,
                        KeyCode.F1, KeyCode.F2, KeyCode.HOME, KeyCode.END]))
def test_property_3_special_keys_generate_key_event(key_code):
    """
    Property 3: Special keys generate KeyEvent
    Feature: char-event-text-input, Property 3
    """
    event = KeyEvent(key_code=key_code, modifiers=ModifierKey.NONE)
    assert isinstance(event, KeyEvent)
    assert event.key_code == key_code

@given(st.characters(min_codepoint=32, max_codepoint=126))
def test_property_4_text_widget_accepts_char_event(char):
    """
    Property 4: Text input widgets accept CharEvent
    Feature: char-event-text-input, Property 4
    """
    editor = SingleLineTextEdit()
    event = CharEvent(char=char)
    result = editor.handle_key(event)
    assert result == True
    assert char in editor.get_text()

@given(st.characters(min_codepoint=32, max_codepoint=126))
def test_property_7_shift_character_generates_char_event(char):
    """
    Property 7: Shift+character generates CharEvent
    Feature: char-event-text-input, Property 7
    """
    # Simulate Shift+character input
    shifted_char = char.upper() if char.isalpha() else char
    event = CharEvent(char=shifted_char)
    assert isinstance(event, CharEvent)
    assert event.char == shifted_char
```

## OS Compatibility and IME Support

### macOS Text Input Architecture

macOS uses NSTextInputClient protocol for text input:

1. **keyDown: (NSEvent):**
   - Called for all keyboard input
   - Application can consume for commands
   - If not consumed, passed to `interpretKeyEvents:`

2. **interpretKeyEvents: → insertText:**
   - macOS translates key event to character
   - Calls `insertText:` with the character
   - Application inserts character into text

3. **IME Support (Future):**
   - `setMarkedText:selectedRange:replacementRange:` - Show composition
   - `insertText:replacementRange:` - Insert finalized text

**Our Design Implementation:**
- ✅ `keyDown:` → Generate KeyEvent → Deliver via `on_key_event()` callback
- ✅ If not consumed → `interpretKeyEvents:` → `insertText:`
- ✅ `insertText:` → Generate CharEvent → Deliver via `on_char_event()` callback
- ✅ Future: `setMarkedText:` → Generate CompositionEvent

**Code Mapping:**
```objc
// macOS NSTextInputClient
- (void)keyDown:(NSEvent *)event {
    // → on_key_event(KeyEvent)
    if (!consumed) {
        [self interpretKeyEvents:@[event]];
    }
}

- (void)insertText:(id)string {
    // → on_char_event(CharEvent)
}
```

### Windows Text Input Architecture (Future)

Windows uses message-based text input:

1. **WM_KEYDOWN:**
   - Raw key press event
   - Application can handle for commands
   - If not handled, system translates to WM_CHAR

2. **WM_CHAR:**
   - Translated character message
   - Application inserts character

3. **IME Support:**
   - WM_IME_COMPOSITION: Composition in progress
   - WM_IME_CHAR: Finalized character

**Future Design Implementation:**
- WM_KEYDOWN → Generate KeyEvent → Deliver via `on_key_event()` callback
- If not consumed → WM_CHAR → Generate CharEvent → Deliver via `on_char_event()` callback
- WM_IME_COMPOSITION → Generate CompositionEvent

### Terminal Mode (Curses)

Terminal mode uses callbacks with backend-level translation (consistent with desktop mode):

1. **Backend Event Loop:**
   - Poll for keyboard input via `getch()`
   - Generate KeyEvent for all input
   - Deliver KeyEvent via `on_key_event()` callback

2. **Backend Translation:**
   - If KeyEvent not consumed by callback
   - Backend translates to CharEvent (if printable)
   - Deliver CharEvent via `on_char_event()` callback

**Implementation:**
```python
class CursesBackend(Renderer):
    def run_event_loop(self):
        """Run event loop with callback delivery."""
        while True:
            # Poll for input
            key = self.stdscr.getch()
            if key == -1:
                continue
            
            # Generate KeyEvent
            key_event = self._translate_curses_key(key)
            
            # Deliver KeyEvent via callback
            consumed = False
            if self.event_callback:
                consumed = self.event_callback.on_key_event(key_event)
            
            # If not consumed, translate to CharEvent
            if not consumed:
                char_event = self._translate_key_to_char(key_event)
                if char_event and self.event_callback:
                    self.event_callback.on_char_event(char_event)
    
    def _translate_key_to_char(self, event: KeyEvent) -> Optional[CharEvent]:
        """Translate KeyEvent to CharEvent if printable."""
        # Only translate if no command modifiers
        if event.modifiers & (ModifierKey.CONTROL | ModifierKey.ALT | ModifierKey.COMMAND):
            return None
        
        # Only translate if has printable character
        if event.char and len(event.char) == 1 and event.char.isprintable():
            return CharEvent(char=event.char)
        
        return None
```

### IME Integration Path

**Current Design (Phase 1):**

Both Modes (Unified Callback Interface):
```
Backend Event Loop
    ↓
KeyEvent → on_key_event() → [consumed?]
                                ↓ not consumed
                         Backend Translation
                                ↓
                         CharEvent → on_char_event()
```

Desktop Mode (OS-Level Translation):
```
keyDown: → KeyEvent → on_key_event() → [consumed?]
                                           ↓ not consumed
                                    interpretKeyEvents:
                                           ↓
                                    insertText: → CharEvent → on_char_event()
```

Terminal Mode (Backend-Level Translation):
```
getch() → KeyEvent → on_key_event() → [consumed?]
                                          ↓ not consumed
                                   _translate_key_to_char()
                                          ↓
                                   CharEvent → on_char_event()
```

**Future IME Support (Phase 2):**

Desktop Mode:
```
keyDown: → KeyEvent → on_key_event() → [consumed?]
                                           ↓ not consumed
                                    interpretKeyEvents:
                                           ↓
                                    setMarkedText: → CompositionEvent → on_composition_event()
                                           ↓
                                    insertText: → CharEvent → on_char_event()
```

This design provides native OS text input handling in desktop mode while maintaining backward compatibility in terminal mode.

## Implementation Notes

### Migration Strategy

1. **Phase 1:** Add CharEvent class to `ttk/input_event.py`
2. **Phase 2:** Add KeyEvent to CharEvent translation function
3. **Phase 3:** Update main event loop to translate unconsumed KeyEvents
4. **Phase 4:** Update SingleLineTextEdit to handle CharEvent
5. **Phase 5:** Update command handlers to return True/False for consumption
6. **Phase 6:** Update tests and verify behavior

### Backward Compatibility

- **No changes to backends** - they continue generating KeyEvent
- Existing TFM key bindings continue to work unchanged
- KeyEvent retains `char` field for legacy compatibility
- Gradual migration: code can handle both CharEvent and KeyEvent
- No breaking changes to public APIs
- Translation layer is additive, not replacing existing behavior

### Performance Considerations

- `isinstance()` checks are fast (O(1) operation)
- No performance impact on event generation
- Minimal memory overhead (CharEvent is smaller than KeyEvent)

### Future Enhancements

- IME support: CharEvent can be extended for multi-byte character composition
- Composition events: Add CompositionEvent for IME input in progress
- Dead key support: Handle dead key combinations for accented characters
