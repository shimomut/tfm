# Design Document

## Overview

This design adds full Unicode input and IME (Input Method Editor) support to the CoreGraphics backend by implementing the NSTextInputClient protocol. The implementation leverages macOS's native text input system to automatically render composition text and candidate windows, while TFM provides positioning information and handles the final committed text through CharEvent generation.

### Key Design Decisions

1. **OS-Rendered Composition**: macOS handles all visual rendering of composition text and candidate windows
   - Simpler implementation - no custom rendering code needed
   - Consistent with native macOS applications
   - Automatic support for all IME features (underlining, highlighting, candidate selection)

2. **NSTextInputClient Protocol**: Full implementation of required protocol methods
   - `insertText:` - Handles committed text and generates CharEvent
   - `setMarkedText:selectedRange:replacementRange:` - Tracks composition state
   - `unmarkText` - Handles composition cancellation
   - `firstRectForCharacterRange:actualRange:` - Provides cursor position for IME overlay
   - `attributedSubstringForProposedRange:actualRange:` - Provides font information

3. **Font Size Synchronization**: IME uses same font as TFM
   - Font information provided via `attributedSubstringForProposedRange:`
   - Ensures composition text matches application text size
   - Updates automatically when application font changes

4. **Backend Isolation**: All IME code contained in CoreGraphics backend
   - No changes to curses backend
   - No changes to application code
   - CharEvent generation maintains compatibility with existing text widgets

5. **State Management**: Composition state tracked per text field
   - Marked text range stored in backend
   - Cleared on focus changes
   - Cancelled on Escape key

## Architecture

### NSTextInputClient Protocol Flow

```
User Types with IME Active
    ↓
macOS Input Method
    ↓
keyDown: (TTKView)
    ├── Generate KeyEvent
    ├── Deliver to application
    └── If not consumed → interpretKeyEvents:
        ↓
        macOS Text Input System
        ↓
        ┌─────────────────────────────────────┐
        │  NSTextInputClient Protocol Methods  │
        ├─────────────────────────────────────┤
        │  setMarkedText:... (composition)    │
        │  firstRectForCharacterRange:...     │
        │  attributedSubstringFor...          │
        │  insertText: (commit)               │
        │  unmarkText (cancel)                │
        └─────────────────────────────────────┘
        ↓
        macOS Renders Composition
        (underline, highlighting, candidates)
        ↓
        User Commits Text
        ↓
        insertText: (TTKView)
        ↓
        Generate CharEvent
        ↓
        Text Widget Handles CharEvent
```

### Component Interaction

```
┌─────────────────────────────────────────────────────────┐
│                    macOS Input System                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │  IME (Japanese, Chinese, Korean, etc.)           │   │
│  │  - Composition rendering                         │   │
│  │  - Candidate window                              │   │
│  │  - Font matching                                 │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                        ↕ NSTextInputClient Protocol
┌─────────────────────────────────────────────────────────┐
│              CoreGraphics Backend (TTKView)              │
│  ┌──────────────────────────────────────────────────┐   │
│  │  NSTextInputClient Implementation                │   │
│  │  - Track marked text range                       │   │
│  │  - Provide cursor position                       │   │
│  │  - Provide font information                      │   │
│  │  - Generate CharEvent on commit                  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                        ↓ CharEvent
┌─────────────────────────────────────────────────────────┐
│                  Application Layer (TFM)                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Text Input Widgets                              │   │
│  │  - Handle CharEvent identically                  │   │
│  │  - No IME-specific code needed                   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. TTKView NSTextInputClient Implementation

**Location:** `ttk/backends/coregraphics_backend.py` (TTKView class)

**Purpose:** Implement NSTextInputClient protocol to enable IME support

**New Instance Variables:**
```python
class TTKView(Cocoa.NSView):
    def initWithFrame_backend_(self, frame, backend):
        # ... existing initialization ...
        
        # IME state tracking
        self.marked_text = ""  # Current composition text
        self.marked_range = Cocoa.NSMakeRange(Cocoa.NSNotFound, 0)  # Composition range
        self.selected_range = Cocoa.NSMakeRange(0, 0)  # Selection within composition
```

**Protocol Methods:**

#### insertText:
```python
def insertText_(self, string):
    """
    Handle committed text from IME or direct keyboard input.
    
    This method is called by macOS when:
    1. User commits IME composition (presses Enter or selects candidate)
    2. User types a character without IME active
    3. User pastes text
    
    For each character in the string, we generate a CharEvent and deliver
    it to the application via the event callback system.
    
    Args:
        string: NSString or NSAttributedString containing committed text
    """
    # Clear marked text state
    self.marked_text = ""
    self.marked_range = Cocoa.NSMakeRange(Cocoa.NSNotFound, 0)
    
    # Extract plain text if NSAttributedString
    if hasattr(string, 'string'):
        text = str(string.string())
    else:
        text = str(string)
    
    # Generate CharEvent for each character
    if self.backend.event_callback:
        for char in text:
            char_event = CharEvent(char=char)
            self.backend.event_callback.on_char_event(char_event)
```

#### setMarkedText:selectedRange:replacementRange:
```python
def setMarkedText_selectedRange_replacementRange_(self, string, selected_range, replacement_range):
    """
    Handle composition text updates from IME.
    
    This method is called repeatedly as the user types with IME active.
    macOS handles all visual rendering - we just track the state for
    position queries.
    
    Args:
        string: NSString or NSAttributedString containing composition text
        selected_range: NSRange indicating selected portion within composition
        replacement_range: NSRange indicating text to replace (usually NSNotFound)
    """
    # Extract plain text if NSAttributedString
    if hasattr(string, 'string'):
        self.marked_text = str(string.string())
    else:
        self.marked_text = str(string)
    
    # Update marked range
    if len(self.marked_text) > 0:
        self.marked_range = Cocoa.NSMakeRange(0, len(self.marked_text))
    else:
        self.marked_range = Cocoa.NSMakeRange(Cocoa.NSNotFound, 0)
    
    # Store selected range within composition
    self.selected_range = selected_range
```

#### unmarkText
```python
def unmarkText(self):
    """
    Cancel composition without committing.
    
    This method is called when:
    1. User presses Escape during composition
    2. Focus changes while composition is active
    3. Dialog closes with active composition
    """
    self.marked_text = ""
    self.marked_range = Cocoa.NSMakeRange(Cocoa.NSNotFound, 0)
    self.selected_range = Cocoa.NSMakeRange(0, 0)
```

#### hasMarkedText
```python
def hasMarkedText(self) -> bool:
    """
    Check if composition is currently active.
    
    Returns:
        True if there is active composition text, False otherwise
    """
    return self.marked_range.location != Cocoa.NSNotFound
```

#### markedRange
```python
def markedRange(self):
    """
    Get the range of marked (composition) text.
    
    Returns:
        NSRange indicating the composition text range
    """
    return self.marked_range
```

#### selectedRange
```python
def selectedRange(self):
    """
    Get the selected range within the document.
    
    For TFM, we don't have text selection in the traditional sense,
    so we return the cursor position as a zero-length range.
    
    Returns:
        NSRange with cursor position
    """
    return self.selected_range
```

#### firstRectForCharacterRange:actualRange:
```python
def firstRectForCharacterRange_actualRange_(self, char_range, actual_range):
    """
    Provide screen rectangle for composition text positioning.
    
    This method tells macOS where to display the composition text and
    candidate window. We return the screen coordinates of the current
    cursor position.
    
    Args:
        char_range: NSRange indicating requested character range
        actual_range: Pointer to NSRange to fill with actual range (can be NULL)
    
    Returns:
        NSRect in screen coordinates where composition should appear
    """
    # Get cursor position from backend
    # The backend tracks the current text widget's cursor position
    cursor_row = self.backend.cursor_row
    cursor_col = self.backend.cursor_col
    
    # Convert to pixel coordinates (TTK to CoreGraphics)
    x_pixel = cursor_col * self.backend.char_width
    y_pixel = (self.backend.rows - cursor_row - 1) * self.backend.char_height
    
    # Create rect at cursor position with character dimensions
    rect = Cocoa.NSMakeRect(
        x_pixel,
        y_pixel,
        self.backend.char_width,
        self.backend.char_height
    )
    
    # Convert from view coordinates to screen coordinates
    window_rect = self.convertRect_toView_(rect, None)
    screen_rect = self.window().convertRectToScreen_(window_rect)
    
    # Fill actual_range if provided
    if actual_range is not None:
        actual_range[0] = char_range
    
    return screen_rect
```

#### attributedSubstringForProposedRange:actualRange:
```python
def attributedSubstringForProposedRange_actualRange_(self, proposed_range, actual_range):
    """
    Provide attributed string for font information.
    
    This method tells macOS what font to use for composition text.
    We return an attributed string with our application font so the
    IME composition matches our text size.
    
    Args:
        proposed_range: NSRange indicating requested range
        actual_range: Pointer to NSRange to fill with actual range (can be NULL)
    
    Returns:
        NSAttributedString with font information, or None
    """
    # Create attributed string with our font
    # Use a single space character as placeholder
    attrs = {
        Cocoa.NSFontAttributeName: self.backend.font
    }
    
    attr_string = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
        " ",
        attrs
    )
    
    # Fill actual_range if provided
    if actual_range is not None:
        actual_range[0] = Cocoa.NSMakeRange(0, 1)
    
    return attr_string
```

#### validAttributesForMarkedText
```python
def validAttributesForMarkedText(self):
    """
    Specify which text attributes are supported for marked text.
    
    Returns:
        Array of attribute names (empty for basic support)
    """
    # Return empty array - we support basic marked text without custom attributes
    return []
```

### 2. Cursor Position Tracking

**Location:** `ttk/backends/coregraphics_backend.py` (CoreGraphicsBackend class)

**Purpose:** Track current cursor position for IME positioning

**New Instance Variables:**
```python
class CoreGraphicsBackend(Renderer):
    def __init__(self, ...):
        # ... existing initialization ...
        
        # Cursor position tracking for IME
        self.cursor_row = 0
        self.cursor_col = 0
```

**New Method:**
```python
def set_cursor_position(self, row: int, col: int) -> None:
    """
    Update cursor position for IME positioning.
    
    This method should be called by text widgets when the cursor moves
    to ensure IME composition appears at the correct location.
    
    Args:
        row: Cursor row (0-based)
        col: Cursor column (0-based)
    """
    self.cursor_row = max(0, min(row, self.rows - 1))
    self.cursor_col = max(0, min(col, self.cols - 1))
```

### 3. KeyEvent Handling Updates

**Location:** `ttk/backends/coregraphics_backend.py` (TTKView class)

**Purpose:** Integrate IME with existing key event handling

**Modified Method:**
```python
def keyDown_(self, event):
    """
    Handle key down event with IME support.
    
    This method is called by macOS when a key is pressed. We:
    1. Generate KeyEvent and deliver to application
    2. If not consumed, pass to interpretKeyEvents: for IME processing
    3. IME calls insertText: or setMarkedText: as appropriate
    """
    # Generate KeyEvent from NSEvent
    key_event = self.backend._translate_event(event)
    
    # Deliver KeyEvent to application
    consumed = False
    if key_event and self.backend.event_callback:
        consumed = self.backend.event_callback.on_key_event(key_event)
    
    if consumed:
        # Application consumed the event - don't pass to IME
        return
    
    # Not consumed - pass to input system for IME processing
    # This will call setMarkedText: for composition or insertText: for commit
    self.interpretKeyEvents_([event])
```

### 4. CharEvent Integration

**Location:** Already implemented in `ttk/input_event.py`

**Purpose:** CharEvent class for text input (already exists from char-event-text-input spec)

**No changes needed** - IME generates CharEvent through `insertText:` method

## Data Models

### IME State

```python
@dataclass
class IMEState:
    """
    IME composition state (tracked in TTKView).
    
    Attributes:
        marked_text: Current composition text string
        marked_range: NSRange indicating composition range
        selected_range: NSRange indicating selection within composition
    """
    marked_text: str
    marked_range: Any  # NSRange
    selected_range: Any  # NSRange
```

### Cursor Position

```python
@dataclass
class CursorPosition:
    """
    Cursor position for IME positioning (tracked in CoreGraphicsBackend).
    
    Attributes:
        row: Cursor row (0-based)
        col: Cursor column (0-based)
    """
    row: int
    col: int
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: IME committed text generates CharEvent

*For any* text committed through IME `insertText:`, the system should generate a CharEvent for each character in the committed text.

**Validates: Requirements 1.5, 6.1, 6.2**

### Property 2: Cursor position determines IME overlay position

*For any* cursor position (row, col), the screen rectangle returned by `firstRectForCharacterRange:` should correspond to the pixel coordinates of that cursor position.

**Validates: Requirements 2.4, 2.5, 4.1, 4.2**

### Property 3: Font size matches application font

*For any* font configured in the backend, the attributed string returned by `attributedSubstringForProposedRange:` should use that same font.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 4: Composition state cleared on cancel

*For any* active composition, calling `unmarkText` should clear the marked text, marked range, and selected range.

**Validates: Requirements 5.4, 5.5**

### Property 5: Command keys work during composition

*For any* command key event (Cmd+C, Cmd+V, etc.) during active composition, the KeyEvent should be delivered to the application and consumed without affecting composition state.

**Validates: Requirements 7.1, 7.2**

### Property 6: CharEvent from IME identical to keyboard

*For any* character, a CharEvent generated from IME `insertText:` should be indistinguishable from a CharEvent generated from direct keyboard input.

**Validates: Requirements 6.2, 6.3, 8.3, 8.4, 8.5**

### Property 7: Marked text range reflects composition length

*For any* composition text of length N, the marked range should have location 0 and length N when N > 0, or location NSNotFound when N = 0.

**Validates: Requirements 3.2, 3.4**

## Error Handling

### Invalid Cursor Position

**Scenario:** Cursor position is out of bounds

**Handling:**
- Clamp cursor position to valid grid bounds in `set_cursor_position()`
- Return valid screen rectangle even with clamped position
- Log warning if position is significantly out of bounds

### Missing Event Callback

**Scenario:** `insertText:` called but no event callback registered

**Handling:**
- Check for callback existence before generating CharEvent
- Silently ignore if no callback (backward compatibility with polling mode)
- Log warning in debug mode

### Font Not Available

**Scenario:** Backend font is None or invalid

**Handling:**
- Return None from `attributedSubstringForProposedRange:`
- macOS will use default system font for composition
- Log warning about missing font

### Window Not Available

**Scenario:** `firstRectForCharacterRange:` called but view has no window

**Handling:**
- Return zero rect at origin
- IME will use default positioning
- Log warning about missing window

## Testing Strategy

### Unit Tests

**Test Coverage:**
1. `insertText:` generates correct CharEvent for single character
2. `insertText:` generates multiple CharEvent for multi-character string
3. `setMarkedText:` updates marked text and range correctly
4. `unmarkText` clears all composition state
5. `hasMarkedText` returns correct boolean based on marked range
6. `firstRectForCharacterRange:` returns correct screen coordinates
7. `attributedSubstringForProposedRange:` returns string with correct font
8. `set_cursor_position()` clamps to valid bounds
9. Command keys during composition don't affect marked text
10. Focus change clears composition state

### Integration Tests

**Test Scenarios:**
1. Type Japanese hiragana and convert to kanji
2. Type Chinese pinyin and select from candidates
3. Type Korean hangul composition
4. Type Vietnamese with tone marks
5. Switch between different IME languages
6. Use IME in dialog text fields
7. Use IME in main window text fields
8. Cancel composition with Escape
9. Commit composition with Enter
10. Use command keys (Cmd+C, Cmd+V) during composition

### Manual Testing

**Test Cases:**
1. Verify composition text appears at cursor position
2. Verify candidate window appears near composition
3. Verify font size matches application font
4. Verify composition underline is visible
5. Verify selected segment is highlighted
6. Verify composition follows cursor movement
7. Verify composition clears on focus change
8. Verify composition clears on dialog close
9. Verify committed text appears in text field
10. Verify IME works with different font sizes

## Implementation Notes

### PyObjC Method Naming

NSTextInputClient protocol methods follow PyObjC naming conventions:
- `insertText:` → `insertText_(string)`
- `setMarkedText:selectedRange:replacementRange:` → `setMarkedText_selectedRange_replacementRange_(string, selected, replacement)`
- `firstRectForCharacterRange:actualRange:` → `firstRectForCharacterRange_actualRange_(char_range, actual_range)`

### Coordinate System

TTK uses top-left origin, CoreGraphics uses bottom-left origin:
- Cursor position conversion: `y_pixel = (rows - row - 1) * char_height`
- View to screen conversion: Use `convertRect_toView:` and `convertRectToScreen:`

### Font Information

The `attributedSubstringForProposedRange:` method provides font information to macOS:
- Return NSAttributedString with NSFontAttributeName
- Use backend's configured font
- Single space character is sufficient as placeholder

### State Management

Composition state is tracked in TTKView instance variables:
- `marked_text`: Current composition string
- `marked_range`: NSRange with composition range
- `selected_range`: NSRange with selection within composition

Clear state on:
- `unmarkText` (explicit cancel)
- `insertText:` (commit)
- Focus change (implicit cancel)
- Dialog close (implicit cancel)

### Backward Compatibility

IME support is additive and doesn't break existing functionality:
- Polling mode (`get_event()`) continues to work
- Callback mode gains IME support automatically
- Text widgets handle CharEvent identically regardless of source
- No changes needed to curses backend or application code
