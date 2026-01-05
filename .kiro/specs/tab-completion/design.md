# Design Document: TAB Completion

## Overview

This design document describes the implementation of TAB completion functionality for the SingleLineTextEdit component in TFM. The feature enables users to efficiently complete text input by pressing the TAB key, with an overlay candidate list that displays available completions. The design follows a strategy pattern to support multiple completion behaviors, with filepath completion as the initial implementation.

The system consists of three main components:
1. **Completer Strategy**: An interface and implementations for generating completion candidates
2. **Candidate List UI**: An overlay component that displays and manages completion candidates
3. **Enhanced SingleLineTextEdit**: Extended functionality to integrate TAB completion with existing text editing

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    SingleLineTextEdit                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Existing Text Editing Logic                           │ │
│  │  - Text input, cursor movement, editing operations     │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  TAB Completion Integration                            │ │
│  │  - Handle TAB key press                                │ │
│  │  - Manage candidate list visibility                    │ │
│  │  - Insert completion text                              │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          │ uses                              │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Completer (Strategy)                           │ │
│  │  - get_candidates(text, cursor_pos) -> List[str]      │ │
│  │  - get_completion_start_pos(text, cursor_pos) -> int  │ │
│  └────────────────────────────────────────────────────────┘ │
│                          △                                   │
│                          │ implements                        │
│                          │                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │      FilepathCompleter                                 │ │
│  │  - Parse directory and filename from input             │ │
│  │  - List matching files/directories                     │ │
│  │  - Format candidates with trailing separators          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ displays
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    CandidateListOverlay                      │
│  - Display candidates in overlay UI                          │
│  - Position above/below text edit field                      │
│  - Align horizontally with completion position               │
│  - Handle visibility and updates                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User presses TAB**:
   - SingleLineTextEdit receives TAB key event
   - Calls completion_behavior.get_candidates(text, cursor_pos)
   - Receives list of candidate strings

2. **Calculate common prefix**:
   - Extract common prefix from all candidates
   - Determine text to insert (common prefix minus already-typed text)

3. **Insert completion text**:
   - If common prefix extends beyond current input, insert additional characters
   - Update cursor position to end of inserted text

4. **Display candidate list**:
   - If multiple candidates exist, show CandidateListOverlay
   - Position overlay above or below based on available space
   - Align overlay horizontally with completion start position

5. **User types additional characters**:
   - Update text in SingleLineTextEdit
   - Regenerate candidates with new text
   - Update CandidateListOverlay with filtered candidates
   - Hide overlay if no candidates remain

## Components and Interfaces

### Completer (Protocol/Interface)

```python
class Completer(Protocol):
    """Strategy interface for generating completion candidates"""
    
    def get_candidates(self, text: str, cursor_pos: int) -> List[str]:
        """
        Generate completion candidates based on current text and cursor position.
        
        Args:
            text: Current text in the edit field
            cursor_pos: Current cursor position (character index)
            
        Returns:
            List of candidate strings that match the current input.
            For filepath completion, returns filenames/directory names with
            trailing separators for directories.
        """
        ...
    
    def get_completion_start_pos(self, text: str, cursor_pos: int) -> int:
        """
        Determine the character position where completion should start.
        
        For filepath completion, this is the position after the last
        directory separator (or 0 if no separator exists).
        
        Args:
            text: Current text in the edit field
            cursor_pos: Current cursor position (character index)
            
        Returns:
            Character position where the completion portion begins
        """
        ...
```

### FilepathCompleter

```python
class FilepathCompleter:
    """Completer for filesystem paths"""
    
    def __init__(self, base_directory: Optional[str] = None):
        """
        Initialize filepath completer.
        
        Args:
            base_directory: Base directory for relative path completion.
                          If None, uses current working directory.
        """
        self.base_directory = base_directory or os.getcwd()
    
    def get_candidates(self, text: str, cursor_pos: int) -> List[str]:
        """
        Generate filepath completion candidates.
        
        Algorithm:
        1. Extract the portion of text up to cursor position
        2. Find the last directory separator (/ or os.sep)
        3. Split into directory path and filename prefix
        4. List all entries in the directory
        5. Filter entries that start with the filename prefix
        6. Add trailing separator for directories
        7. Return list of matching filenames/directory names
        
        Example:
            text = "/aaaa/bbbb/ab"
            cursor_pos = 13
            directory = "/aaaa/bbbb/"
            prefix = "ab"
            matches = ["abcd1234/", "abc678/"]
        """
        ...
    
    def get_completion_start_pos(self, text: str, cursor_pos: int) -> int:
        """
        Find the position after the last directory separator.
        
        Returns the character position where the filename/directory name
        being completed begins.
        """
        ...
```

### CandidateListOverlay

```python
class CandidateListOverlay:
    """Overlay UI component for displaying completion candidates"""
    
    def __init__(self, renderer):
        """
        Initialize the candidate list overlay.
        
        Args:
            renderer: TTK Renderer instance for drawing
        """
        self.renderer = renderer
        self.candidates = []
        self.is_visible = False
        self.position_y = 0  # Y coordinate (above or below text edit)
        self.position_x = 0  # X coordinate (aligned with completion start)
        self.max_visible_candidates = 10  # Maximum candidates to display
    
    def set_candidates(self, candidates: List[str], position_y: int, 
                      position_x: int, show_above: bool):
        """
        Update the candidate list and position.
        
        Args:
            candidates: List of candidate strings to display
            position_y: Y coordinate of the text edit field
            position_x: X coordinate where completion starts
            show_above: True to show above text edit, False for below
        """
        ...
    
    def show(self):
        """Make the candidate list visible"""
        ...
    
    def hide(self):
        """Hide the candidate list"""
        ...
    
    def draw(self):
        """
        Draw the candidate list overlay.
        
        Rendering:
        1. Calculate overlay position (above or below text edit)
        2. Draw border/background
        3. Draw each candidate on a separate line
        4. Truncate candidates that exceed available width
        5. Show indicator if more candidates exist than can be displayed
        """
        ...
```

### Enhanced SingleLineTextEdit

```python
class SingleLineTextEdit:
    """Extended with TAB completion functionality"""
    
    def __init__(self, initial_text="", max_length=None, renderer=None,
                 completer: Optional[Completer] = None):
        """
        Initialize text editor with optional completer.
        
        Args:
            initial_text: Initial text content
            max_length: Maximum allowed text length
            renderer: TTK Renderer instance
            completer: Strategy for generating completions (optional)
        """
        # Existing initialization...
        self.completer = completer
        self.candidate_list = CandidateListOverlay(renderer) if completer else None
        self.completion_active = False
    
    def handle_tab_completion(self) -> bool:
        """
        Handle TAB key press for completion.
        
        Algorithm:
        1. Get candidates from completer
        2. If no candidates, return False
        3. Calculate common prefix of all candidates
        4. Determine completion start position
        5. Extract already-typed portion
        6. Calculate text to insert (common prefix - already typed)
        7. Insert completion text at cursor
        8. Update cursor position
        9. Show/update candidate list if multiple candidates
        10. Return True if completion occurred
        """
        ...
    
    def update_candidate_list(self):
        """
        Update candidate list based on current text.
        
        Called after text changes to refresh the candidate list.
        Hides the list if no candidates match.
        """
        ...
    
    def hide_candidate_list(self):
        """Hide the candidate list overlay"""
        ...
    
    def handle_key(self, event, handle_vertical_nav=False):
        """
        Extended to handle TAB key and update candidate list.
        
        Modifications:
        1. Check for TAB key press -> call handle_tab_completion()
        2. Check for ESC key press -> hide candidate list
        3. After any text modification -> update candidate list
        4. Preserve existing key handling logic
        """
        ...
    
    def draw(self, renderer, y, x, max_width, label="", is_active=True):
        """
        Extended to draw candidate list overlay.
        
        Modifications:
        1. Call existing draw logic for text field
        2. If candidate list is visible, call candidate_list.draw()
        """
        ...
```

## Data Models

### Candidate

Candidates are represented as simple strings. For filepath completion:
- Regular files: `"filename.txt"`
- Directories: `"dirname/"`
- The trailing separator distinguishes directories from files

### Completion State

```python
@dataclass
class CompletionState:
    """Internal state for managing completion"""
    candidates: List[str]           # Current list of candidates
    completion_start_pos: int       # Character position where completion begins
    common_prefix: str              # Common prefix of all candidates
    is_active: bool                 # Whether completion is currently active
```

### Keyboard Navigation State

The CandidateListOverlay maintains additional state for keyboard navigation:

```python
@dataclass
class NavigationState:
    """State for keyboard navigation in candidate list"""
    focused_index: Optional[int]    # Index of focused candidate (None if no focus)
    scroll_offset: int              # First visible candidate index
    visible_count: int              # Number of candidates that fit in visible area
```

## Keyboard Navigation Design

### Focus Management

The candidate list supports keyboard navigation with visual focus indication:

1. **Initial State**: When the candidate list first appears, no candidate is focused
2. **Focus Activation**: Pressing Up/Down arrow keys activates focus on a candidate
3. **Focus Movement**: Subsequent Up/Down presses move focus through the list
4. **Focus Wrapping**: Focus wraps from last to first (Down) and first to last (Up)
5. **Focus Clearing**: Pressing ESC or selecting a candidate clears focus

### Visual Feedback

The focused candidate is visually distinguished from other candidates:
- Background color change (highlighted)
- Different text attributes (bold or inverse video)
- Clear visual indication of which candidate will be selected on Enter

### Scrolling Behavior

When the candidate list has more items than fit in the visible area:

1. **Auto-scroll**: The list automatically scrolls to keep the focused candidate visible
2. **Scroll-up**: When focus moves above the visible area, scroll up to show it
3. **Scroll-down**: When focus moves below the visible area, scroll down to show it
4. **Scrollbar**: A visual scrollbar indicates scroll position and list size

### Scrollbar Design

The scrollbar uses the existing `draw_scrollbar()` utility from `tfm_scrollbar.py`:

```
┌─────────────────┐
│ candidate1      │
│ candidate2      │┃  ← Thumb (visible portion)
│ candidate3      │┃
│ candidate4      │   ← Track (non-visible portion)
│ candidate5      │
└─────────────────┘
```

- **Thumb (┃)**: Heavy vertical line indicates visible portion of list
- **Track (space)**: Background shows through for non-visible portion
- **Position**: Right edge of overlay, inside the border
- **Height**: Proportional to visible/total ratio
- **Implementation**: Use `draw_scrollbar(renderer, start_y, x_pos, display_height, total_items, scroll_offset, inverted=False)`

### Key Event Handling

The SingleLineTextEdit component handles these additional key events when the candidate list is visible:

```python
def handle_key(self, event):
    """Extended key handling for candidate list navigation"""
    
    if candidate_list_visible:
        if event.key == UP_ARROW:
            # Move focus to previous candidate (wrap to last if at first)
            candidate_list.move_focus_up()
            return True
        
        elif event.key == DOWN_ARROW:
            # Move focus to next candidate (wrap to first if at last)
            candidate_list.move_focus_down()
            return True
        
        elif event.key == ENTER and candidate_list.has_focus():
            # Apply focused candidate to text edit
            focused_candidate = candidate_list.get_focused_candidate()
            self.apply_candidate(focused_candidate)
            candidate_list.hide()
            return True
        
        elif event.key == ESC:
            # Hide candidate list without applying selection
            candidate_list.hide()
            return True
    
    # Fall through to existing key handling
    return existing_key_handling(event)
```

### Candidate Application

When a candidate is selected via Enter key:

1. **Extract completion portion**: Get the part of the candidate after the completion start position
2. **Replace text**: Replace from completion_start_pos to cursor_pos with the selected candidate
3. **Update cursor**: Move cursor to end of inserted text
4. **Hide list**: Close the candidate list
5. **Clear focus**: Reset focus state for next completion

Algorithm:
```python
def apply_candidate(self, candidate: str):
    """Apply selected candidate to text edit"""
    # Calculate what to insert
    already_typed = self.text[self.completion_start_pos:self.cursor_pos]
    
    # Replace the completion portion
    self.text = (
        self.text[:self.completion_start_pos] +
        candidate +
        self.text[self.cursor_pos:]
    )
    
    # Update cursor position
    self.cursor_pos = self.completion_start_pos + len(candidate)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Common Prefix Insertion

*For any* text input, cursor position, and non-empty list of candidates, pressing TAB should insert exactly the portion of the common prefix that extends beyond the already-typed text, and the cursor should move to the end of the inserted text.

**Validates: Requirements 1.1, 1.2, 8.1**

### Property 2: Candidate List Display

*For any* non-empty list of candidates, when TAB completion is triggered, all candidates should be displayed in the candidate list.

**Validates: Requirements 2.1**

### Property 3: Candidate List Positioning

*For any* text edit field position and window dimensions, the candidate list should appear below the text field when sufficient space exists below, and above the text field when insufficient space exists below.

**Validates: Requirements 2.2, 2.3**

### Property 4: Dynamic Candidate Filtering

*For any* visible candidate list and text modification (insertion or deletion), the candidate list should update to show only candidates that match the new input text.

**Validates: Requirements 2.4, 5.1, 5.2**

### Property 5: Single Candidate Persistence

*For any* candidate list that is filtered down to exactly one match, the candidate list should remain visible displaying that single match.

**Validates: Requirements 2.6**

### Property 6: Filepath Candidate Generation

*For any* filesystem directory and filename prefix, filepath completion should generate candidates for all files and directories in that directory whose names start with the prefix.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 7: Directory Separator Annotation

*For any* filepath completion candidate, directories should have a trailing directory separator and regular files should not have a trailing separator.

**Validates: Requirements 3.4, 3.5**

### Property 8: Candidate Format

*For any* filepath completion candidate, the candidate string should contain the complete filename or directory name after the last directory separator, including any characters already typed by the user.

**Validates: Requirements 3.6, 6.6**

### Property 9: Completion Behavior Integration

*For any* completer strategy provided to SingleLineTextEdit, pressing TAB should invoke that completer's get_candidates method to generate the candidate list.

**Validates: Requirements 4.3**

### Property 10: Cursor Movement Preservation

*For any* visible candidate list, moving the cursor left or right should keep the candidate list visible with the same candidates.

**Validates: Requirements 5.3**

### Property 11: Candidate Line Separation

*For any* candidate list with multiple candidates, each candidate should be rendered on a separate line in the overlay.

**Validates: Requirements 6.1**

### Property 12: Candidate Truncation

*For any* candidate that exceeds the available display width, the candidate should be truncated to fit within the available space.

**Validates: Requirements 6.3**

### Property 13: Candidate Overflow Indication

*For any* candidate list where the number of candidates exceeds the available vertical space, the overlay should display as many candidates as fit and indicate that more candidates exist.

**Validates: Requirements 6.4**

### Property 14: Candidate List Alignment

*For any* filepath completion, the candidate list should be horizontally aligned with the character position where the filename or directory name being completed begins (after the last directory separator).

**Validates: Requirements 6.7**

### Property 15: Common Prefix Calculation

*For any* non-empty list of candidate strings, the calculated common prefix should be the longest string that is a prefix of all candidates, using case-sensitive comparison.

**Validates: Requirements 7.1, 7.2**

### Property 16: Text Editing Preservation

*For any* active TAB completion session, all existing text editing operations (character insertion, deletion, cursor movement, etc.) should continue to function normally.

**Validates: Requirements 8.2**

### Property 17: Focus Movement with Down Arrow

*For any* visible candidate list, pressing the Down arrow key should move focus to the next candidate, wrapping to the first candidate when focus is on the last candidate.

**Validates: Requirements 9.1, 9.3, 9.5**

### Property 18: Focus Movement with Up Arrow

*For any* visible candidate list, pressing the Up arrow key should move focus to the previous candidate, wrapping to the last candidate when focus is on the first candidate.

**Validates: Requirements 9.2, 9.4, 9.6**

### Property 19: Focused Candidate Visual Distinction

*For any* candidate list with a focused candidate, the focused candidate should be visually highlighted to distinguish it from other candidates.

**Validates: Requirements 9.7**

### Property 20: Enter Key Selection

*For any* focused candidate, pressing Enter should replace the completion portion of the text with the focused candidate and hide the candidate list.

**Validates: Requirements 10.1, 10.2, 10.3**

### Property 21: ESC Key Dismissal

*For any* visible candidate list, pressing ESC should hide the candidate list without modifying the text.

**Validates: Requirements 11.1, 11.2, 11.3**

### Property 22: Scrollbar Visibility

*For any* candidate list where the number of candidates exceeds the visible area, a scrollbar should be displayed on the right edge of the overlay.

**Validates: Requirements 12.1**

### Property 23: Scrollbar Position Indication

*For any* candidate list with a scrollbar, the scrollbar should accurately indicate the current scroll position and the proportion of candidates currently visible.

**Validates: Requirements 12.2, 12.3**

### Property 24: Auto-scroll on Navigation

*For any* focused candidate that is outside the visible area, the candidate list should automatically scroll to make the focused candidate visible.

**Validates: Requirements 12.4, 12.5, 12.6**

## Error Handling

### Invalid Filesystem Paths

When filepath completion encounters invalid or inaccessible paths:
- Catch filesystem exceptions (PermissionError, FileNotFoundError, etc.)
- Return empty candidate list
- Log error for debugging purposes
- Do not crash or display error to user

### Empty Candidate Lists

When no candidates match the current input:
- Return empty list from get_candidates()
- Do not insert any text on TAB press
- Hide candidate list if currently visible
- Return False from handle_tab_completion() to indicate no action taken

### Cursor Position Edge Cases

When cursor is not at the end of text:
- Only consider text up to cursor position for completion
- Insert completion text at cursor position
- Do not modify text after cursor

### Wide Character Handling

When dealing with wide characters (CJK, emoji):
- Use existing wide character utilities (get_display_width, truncate_to_width)
- Calculate display positions correctly for candidate list alignment
- Ensure candidate truncation respects character boundaries

### Maximum Candidate List Size

When candidate list exceeds reasonable display limits:
- Limit display to max_visible_candidates (default 10)
- Show indicator that more candidates exist
- Consider implementing scrolling in future enhancement

## Testing Strategy

### Unit Tests

Unit tests will verify specific examples and edge cases:

1. **Common prefix calculation**:
   - Empty list returns empty string
   - Single candidate returns the candidate
   - Multiple candidates with common prefix
   - Multiple candidates with no common prefix
   - Case-sensitive prefix calculation

2. **Filepath completer**:
   - Absolute paths
   - Relative paths
   - Paths with no directory separator
   - Paths ending with directory separator
   - Non-existent directories
   - Permission errors

3. **Candidate list positioning**:
   - Sufficient space below
   - Insufficient space below
   - Edge of screen boundaries

4. **ESC key handling**: Pressing ESC hides candidate list
5. **Focus handling**: Losing focus hides candidate list
6. **No completer**: TAB does nothing when no completer set
7. **Visual styling**: Candidate list uses correct colors and borders

### Property-Based Tests

Property-based tests will verify universal properties across randomized inputs. Each test will run a minimum of 100 iterations.

1. **Property 1: Common Prefix Insertion**
   - Generate random text, cursor positions, and candidate lists
   - Verify TAB inserts correct portion of common prefix
   - Verify cursor moves to end of inserted text
   - **Feature: tab-completion, Property 1: Common prefix insertion**

2. **Property 2: Candidate List Display**
   - Generate random candidate lists
   - Verify all candidates appear in display
   - **Feature: tab-completion, Property 2: Candidate list display**

3. **Property 3: Candidate List Positioning**
   - Generate random window sizes and text field positions
   - Verify correct above/below positioning
   - **Feature: tab-completion, Property 3: Candidate list positioning**

4. **Property 4: Dynamic Candidate Filtering**
   - Generate random text modifications
   - Verify candidate list updates correctly
   - **Feature: tab-completion, Property 4: Dynamic candidate filtering**

5. **Property 5: Single Candidate Persistence**
   - Generate scenarios that filter to one candidate
   - Verify list remains visible
   - **Feature: tab-completion, Property 5: Single candidate persistence**

6. **Property 6: Filepath Candidate Generation**
   - Generate random directory structures and prefixes
   - Verify correct candidates are generated
   - **Feature: tab-completion, Property 6: Filepath candidate generation**

7. **Property 7: Directory Separator Annotation**
   - Generate random file/directory candidates
   - Verify correct trailing separator usage
   - **Feature: tab-completion, Property 7: Directory separator annotation**

8. **Property 8: Candidate Format**
   - Generate random filepath inputs
   - Verify candidates include complete filename
   - **Feature: tab-completion, Property 8: Candidate format**

9. **Property 9: Completion Behavior Integration**
   - Generate random completers
   - Verify TAB invokes get_candidates
   - **Feature: tab-completion, Property 9: Completion behavior integration**

10. **Property 10: Cursor Movement Preservation**
    - Generate random cursor movements with visible list
    - Verify list remains visible
    - **Feature: tab-completion, Property 10: Cursor movement preservation**

11. **Property 11: Candidate Line Separation**
    - Generate random candidate lists
    - Verify each candidate on separate line
    - **Feature: tab-completion, Property 11: Candidate line separation**

12. **Property 12: Candidate Truncation**
    - Generate candidates longer than display width
    - Verify truncation occurs correctly
    - **Feature: tab-completion, Property 12: Candidate truncation**

13. **Property 13: Candidate Overflow Indication**
    - Generate more candidates than fit vertically
    - Verify overflow indicator appears
    - **Feature: tab-completion, Property 13: Candidate overflow indication**

14. **Property 14: Candidate List Alignment**
    - Generate random filepath inputs
    - Verify horizontal alignment with completion start
    - **Feature: tab-completion, Property 14: Candidate list alignment**

15. **Property 15: Common Prefix Calculation**
    - Generate random candidate lists
    - Verify common prefix is longest shared prefix
    - Verify case-sensitive comparison
    - **Feature: tab-completion, Property 15: Common prefix calculation**

16. **Property 16: Text Editing Preservation**
    - Generate random text editing operations during completion
    - Verify all operations still work
    - **Feature: tab-completion, Property 16: Text editing preservation**

### Testing Framework

- **Unit tests**: Python's unittest or pytest framework
- **Property tests**: Hypothesis library for Python
- **Test location**: `test/test_tab_completion.py`
- **Minimum iterations**: 100 per property test
