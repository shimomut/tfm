#!/usr/bin/env python3
"""
Single line text editor component for TFM (Terminal File Manager)

This module provides a reusable SingleLineTextEdit class that handles:
- Text input and editing
- Cursor positioning and movement
- Text rendering with cursor highlighting
- Common editing operations (insert, delete, backspace)
- Navigation (home, end, left, right)
- Wide character support for proper display and editing
- TAB completion with pluggable completion strategies
"""

import os
import unicodedata
from typing import Protocol, List, Optional

# TTK imports
from ttk import TextAttribute, KeyCode, ModifierKey
from ttk.input_event import CharEvent, KeyEvent
from ttk.wide_char_utils import get_display_width, truncate_to_width, get_safe_functions

# TFM imports
from tfm_colors import get_status_color
from tfm_log_manager import getLogger
from tfm_candidate_list_overlay import CandidateListOverlay


def calculate_common_prefix(candidates: List[str]) -> str:
    """
    Calculate the longest common prefix shared by all candidates.
    
    This function determines the maximum unambiguous text that can be
    inserted during TAB completion. It uses case-sensitive comparison
    to match the behavior of most filesystem operations.
    
    Args:
        candidates: List of candidate strings
        
    Returns:
        str: The longest common prefix shared by all candidates.
             Returns empty string for empty list.
             Returns the complete candidate for single-element list.
    
    Examples:
        >>> calculate_common_prefix([])
        ''
        >>> calculate_common_prefix(['hello'])
        'hello'
        >>> calculate_common_prefix(['hello', 'help', 'hero'])
        'he'
        >>> calculate_common_prefix(['abc', 'def'])
        ''
    """
    # Handle empty list
    if not candidates:
        return ""
    
    # Handle single candidate
    if len(candidates) == 1:
        return candidates[0]
    
    # Find common prefix for multiple candidates
    # Start with the first candidate as the initial prefix
    prefix = candidates[0]
    
    # Compare with each subsequent candidate
    for candidate in candidates[1:]:
        # Find the common prefix between current prefix and this candidate
        # by comparing character by character
        common_len = 0
        min_len = min(len(prefix), len(candidate))
        
        for i in range(min_len):
            if prefix[i] == candidate[i]:
                common_len += 1
            else:
                break
        
        # Update prefix to the common portion
        prefix = prefix[:common_len]
        
        # Early exit if no common prefix remains
        if not prefix:
            return ""
    
    return prefix


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


class FilepathCompleter:
    """Completer for filesystem paths"""
    
    def __init__(self, base_directory: Optional[str] = None, directories_only: bool = False):
        """
        Initialize filepath completer.
        
        Args:
            base_directory: Base directory for relative path completion.
                          If None, uses current working directory.
            directories_only: If True, only show directories in completion candidates.
                            If False, show both files and directories.
        """
        self.base_directory = base_directory or os.getcwd()
        self.directories_only = directories_only
        self.logger = getLogger("FilepathComp")
    
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
        
        Args:
            text: Current text in the edit field
            cursor_pos: Current cursor position (character index)
            
        Returns:
            List of candidate strings (filenames/directory names with trailing
            separators for directories)
        """
        # Extract text up to cursor
        text_to_cursor = text[:cursor_pos]
        
        # Find the last directory separator
        last_sep_pos = text_to_cursor.rfind(os.sep)
        
        # Split into directory path and filename prefix
        if last_sep_pos == -1:
            # No separator - search in base directory
            directory = self.base_directory
            prefix = text_to_cursor
        else:
            # Has separator - split into directory and prefix
            directory = text_to_cursor[:last_sep_pos + 1]
            prefix = text_to_cursor[last_sep_pos + 1:]
            
            # Handle absolute vs relative paths
            if not os.path.isabs(directory):
                directory = os.path.join(self.base_directory, directory)
        
        # Normalize directory path
        directory = os.path.normpath(directory)
        
        # List entries in directory and filter by prefix
        candidates = []
        try:
            entries = os.listdir(directory)
            for entry in entries:
                # Check if entry starts with prefix (case-sensitive)
                if entry.startswith(prefix):
                    # Get full path to check if it's a directory
                    full_path = os.path.join(directory, entry)
                    
                    # Check if it's a directory
                    is_directory = os.path.isdir(full_path)
                    
                    # Skip files if directories_only mode is enabled
                    if self.directories_only and not is_directory:
                        continue
                    
                    # Add trailing separator for directories
                    if is_directory:
                        candidates.append(entry + os.sep)
                    else:
                        candidates.append(entry)
        except (PermissionError, FileNotFoundError, OSError) as e:
            # Log error but return empty list
            self.logger.error(f"Error listing directory {directory}: {e}")
            return []
        
        return sorted(candidates)
    
    def get_completion_start_pos(self, text: str, cursor_pos: int) -> int:
        """
        Find the position after the last directory separator.
        
        Returns the character position where the filename/directory name
        being completed begins.
        
        Args:
            text: Current text in the edit field
            cursor_pos: Current cursor position (character index)
            
        Returns:
            Character position where the completion portion begins
        """
        # Extract text up to cursor
        text_to_cursor = text[:cursor_pos]
        
        # Find the last directory separator
        last_sep_pos = text_to_cursor.rfind(os.sep)
        
        # Return position after separator (or 0 if no separator)
        return last_sep_pos + 1 if last_sep_pos != -1 else 0


class SingleLineTextEdit:
    """A single-line text editor with cursor control and visual feedback"""
    
    def __init__(self, initial_text="", max_length=None, renderer=None, completer: Optional[Completer] = None):
        """
        Initialize the text editor
        
        Args:
            initial_text (str): Initial text content (will be normalized to NFC)
            max_length (int, optional): Maximum allowed text length
            renderer: TTK Renderer instance for clipboard access (optional)
            completer (Completer, optional): Strategy for generating completions
        """
        # Store the original normalization form to convert back on retrieval
        self._original_was_nfd = self._is_nfd(initial_text)
        
        # Normalize to NFC for internal editing (consistent character representation)
        self.text = unicodedata.normalize('NFC', initial_text)
        self.cursor_pos = len(self.text)
        self.max_length = max_length
        self.renderer = renderer
        
        # TAB completion support
        self.completer = completer
        self.candidate_list = CandidateListOverlay(renderer) if completer else None
        self.completion_active = False
        self.completion_start_pos = 0
        
    def _is_nfd(self, text):
        """
        Check if text is in NFD (decomposed) form.
        
        Args:
            text (str): Text to check
            
        Returns:
            bool: True if text is in NFD form
        """
        if not text:
            return False
        # Text is NFD if normalizing to NFD doesn't change it, but normalizing to NFC does
        return text == unicodedata.normalize('NFD', text) and text != unicodedata.normalize('NFC', text)
    
    def get_text(self):
        """
        Get the current text content.
        
        If the initial text was in NFD form, converts back to NFD.
        This ensures that when editing filenames on macOS (which uses NFD),
        the returned text matches the original normalization form.
        
        Returns:
            str: Text in the same normalization form as the initial text
        """
        if self._original_was_nfd:
            return unicodedata.normalize('NFD', self.text)
        return self.text
        
    def set_text(self, text):
        """
        Set the text content and adjust cursor if needed.
        
        Args:
            text (str): New text content (will be normalized to NFC)
        """
        # Update original normalization form tracking
        self._original_was_nfd = self._is_nfd(text)
        
        # Normalize to NFC for internal editing
        self.text = unicodedata.normalize('NFC', text)
        self.cursor_pos = min(self.cursor_pos, len(self.text))
        
    def get_cursor_pos(self):
        """Get the current cursor position"""
        return self.cursor_pos
        
    def set_cursor_pos(self, pos):
        """Set the cursor position, ensuring it's within bounds"""
        self.cursor_pos = max(0, min(pos, len(self.text)))
        
    def clear(self):
        """Clear all text and reset cursor"""
        self.text = ""
        self.cursor_pos = 0
        
    def move_cursor_left(self):
        """Move cursor one character position to the left (handles wide characters properly)"""
        if self.cursor_pos > 0:
            self.cursor_pos -= 1
            return True
        return False
        
    def move_cursor_right(self):
        """Move cursor one character position to the right (handles wide characters properly)"""
        if self.cursor_pos < len(self.text):
            self.cursor_pos += 1
            return True
        return False
        
    def move_cursor_home(self):
        """Move cursor to the beginning of the text"""
        if self.cursor_pos > 0:
            self.cursor_pos = 0
            return True
        return False
        
    def move_cursor_end(self):
        """Move cursor to the end of the text"""
        if self.cursor_pos < len(self.text):
            self.cursor_pos = len(self.text)
            return True
        return False
    
    def _is_word_char(self, char):
        """
        Check if a character is a word character (alphanumeric or underscore).
        
        Word characters are letters, digits, and underscores.
        Everything else (whitespace, punctuation, symbols) is a word boundary.
        
        Args:
            char (str): Character to check
            
        Returns:
            bool: True if character is a word character
        """
        return char.isalnum() or char == '_'
    
    def _find_previous_word_boundary(self, pos):
        """
        Find the position of the previous word boundary from the given position.
        
        A word boundary is defined as:
        - The start of the text
        - A transition between word characters and non-word characters
        - Whitespace and punctuation (~`[]-=|\\ etc.) are treated as word boundaries
        
        Args:
            pos (int): Starting position
            
        Returns:
            int: Position of the previous word boundary
        """
        if pos <= 0:
            return 0
        
        # Move back one position to start
        pos -= 1
        
        # Skip any non-word characters (whitespace, punctuation, etc.)
        while pos > 0 and not self._is_word_char(self.text[pos]):
            pos -= 1
        
        # Skip word characters (letters, digits, underscores)
        while pos > 0 and self._is_word_char(self.text[pos]):
            pos -= 1
        
        # If we stopped on a non-word character, move forward one
        if pos > 0 or (pos == 0 and not self._is_word_char(self.text[0])):
            if not self._is_word_char(self.text[pos]):
                pos += 1
        
        return pos
    
    def _find_next_word_boundary(self, pos):
        """
        Find the position of the next word boundary from the given position.
        
        A word boundary is defined as:
        - The end of the text
        - A transition between word characters and non-word characters
        - Whitespace and punctuation (~`[]-=|\\ etc.) are treated as word boundaries
        
        Args:
            pos (int): Starting position
            
        Returns:
            int: Position of the next word boundary
        """
        text_len = len(self.text)
        if pos >= text_len:
            return text_len
        
        # Skip word characters (letters, digits, underscores)
        while pos < text_len and self._is_word_char(self.text[pos]):
            pos += 1
        
        # Skip any non-word characters (whitespace, punctuation, etc.)
        while pos < text_len and not self._is_word_char(self.text[pos]):
            pos += 1
        
        return pos
    
    def move_cursor_word_left(self):
        """Move cursor to the beginning of the previous word"""
        new_pos = self._find_previous_word_boundary(self.cursor_pos)
        if new_pos != self.cursor_pos:
            self.cursor_pos = new_pos
            return True
        return False
    
    def move_cursor_word_right(self):
        """Move cursor to the beginning of the next word"""
        new_pos = self._find_next_word_boundary(self.cursor_pos)
        if new_pos != self.cursor_pos:
            self.cursor_pos = new_pos
            return True
        return False
    
    def delete_word_backward(self):
        """
        Delete from cursor position to the beginning of the previous word.
        Similar to Alt+Backspace in many text editors.
        
        Returns:
            bool: True if text was deleted, False if nothing to delete
        """
        if self.cursor_pos <= 0:
            return False
        
        new_pos = self._find_previous_word_boundary(self.cursor_pos)
        if new_pos < self.cursor_pos:
            self.text = self.text[:new_pos] + self.text[self.cursor_pos:]
            self.cursor_pos = new_pos
            return True
        return False
    
    def delete_to_beginning(self):
        """
        Delete all text from the beginning to the cursor position.
        Similar to Command+Backspace on macOS.
        
        Returns:
            bool: True if text was deleted, False if nothing to delete
        """
        if self.cursor_pos <= 0:
            return False
        
        # Delete everything before cursor
        self.text = self.text[self.cursor_pos:]
        self.cursor_pos = 0
        return True
        
    def insert_char(self, char):
        """
        Insert a character at the cursor position, handling wide characters.
        
        Args:
            char (str): Character to insert (will be normalized to NFC)
            
        Returns:
            bool: True if character was inserted, False if max_length exceeded
        """
        # Normalize character to NFC for consistent internal representation
        char = unicodedata.normalize('NFC', char)
        
        # Check max_length constraint (by character count, not display width)
        if self.max_length and len(self.text) >= self.max_length:
            return False
            
        self.text = (self.text[:self.cursor_pos] + 
                    char + 
                    self.text[self.cursor_pos:])
        self.cursor_pos += 1
        return True
        
    def delete_char_at_cursor(self):
        """
        Delete the character at the cursor position
        
        Returns:
            bool: True if character was deleted, False if nothing to delete
        """
        if self.cursor_pos < len(self.text):
            self.text = (self.text[:self.cursor_pos] + 
                        self.text[self.cursor_pos + 1:])
            return True
        return False
        
    def backspace(self):
        """
        Delete the character before the cursor position
        
        Returns:
            bool: True if character was deleted, False if nothing to delete
        """
        if self.cursor_pos > 0:
            self.text = (self.text[:self.cursor_pos - 1] + 
                        self.text[self.cursor_pos:])
            self.cursor_pos -= 1
            return True
        return False
    
    def paste_from_clipboard(self):
        """
        Paste text from system clipboard at cursor position.
        
        Only works if renderer was provided during initialization and
        clipboard is supported by the backend.
        
        Returns:
            bool: True if text was pasted, False otherwise
        """
        if not self.renderer:
            return False
        
        if not hasattr(self.renderer, 'supports_clipboard') or not self.renderer.supports_clipboard():
            return False
        
        if not hasattr(self.renderer, 'get_clipboard_text'):
            return False
        
        # Get text from clipboard
        clipboard_text = self.renderer.get_clipboard_text()
        if not clipboard_text:
            return False
        
        # Only paste the first line (single-line editor)
        # Replace newlines with spaces
        paste_text = clipboard_text.replace('\n', ' ').replace('\r', ' ')
        
        # Normalize to NFC for consistent internal representation
        paste_text = unicodedata.normalize('NFC', paste_text)
        
        # Check max_length constraint
        if self.max_length:
            available_space = self.max_length - len(self.text)
            if available_space <= 0:
                return False
            # Truncate paste text if needed
            paste_text = paste_text[:available_space]
        
        # Insert text at cursor position
        self.text = (self.text[:self.cursor_pos] + 
                    paste_text + 
                    self.text[self.cursor_pos:])
        self.cursor_pos += len(paste_text)
        return True
    
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
        
        Returns:
            bool: True if completion occurred, False otherwise
        """
        # Check if completer is available
        if not self.completer:
            return False
        
        # Get candidates from completer
        candidates = self.completer.get_candidates(self.text, self.cursor_pos)
        
        # If no candidates, return False
        if not candidates:
            return False
        
        # Calculate common prefix of all candidates
        common_prefix = calculate_common_prefix(candidates)
        
        # Determine completion start position
        self.completion_start_pos = self.completer.get_completion_start_pos(
            self.text, self.cursor_pos
        )
        
        # Extract already-typed portion (from completion start to cursor)
        already_typed = self.text[self.completion_start_pos:self.cursor_pos]
        
        # Calculate text to insert (common prefix minus already typed)
        # Only insert if common prefix extends beyond what's already typed
        if common_prefix.startswith(already_typed) and len(common_prefix) > len(already_typed):
            text_to_insert = common_prefix[len(already_typed):]
            
            # Insert completion text at cursor
            self.text = (
                self.text[:self.cursor_pos] + 
                text_to_insert + 
                self.text[self.cursor_pos:]
            )
            
            # Update cursor position to end of inserted text
            self.cursor_pos += len(text_to_insert)
            
            # Mark completion as active
            self.completion_active = True
        
        # Show/update candidate list if multiple candidates exist
        if len(candidates) > 1 and self.candidate_list:
            # Mark completion as active so draw() will render the candidate list
            self.completion_active = True
            # Store candidates for later rendering in draw()
            # The actual positioning will be calculated in draw() method
            # where we have access to the current y, x coordinates
        
        # Return True if we had candidates (even if no text was inserted)
        return True
    
    def update_candidate_list(self):
        """
        Update candidate list based on current text.
        
        Called after text changes to refresh the candidate list.
        Hides the list if no candidates match.
        
        This method implements dynamic candidate filtering as the user types,
        ensuring the candidate list stays synchronized with the current input.
        
        When the user types characters, focus is cleared to prevent the focused
        candidate from unexpectedly changing as the list filters. This provides
        more predictable UX - typing refines the search, arrow keys navigate.
        
        Requirements:
        - 2.4: Update candidate list when user types additional characters
        - 2.5: Hide candidate list when reduced to zero matches
        - 2.6: Maintain visibility for single candidate
        - 5.1: Filter candidates when user types a character
        - 5.2: Expand candidates when user deletes a character
        """
        # Check if completer and candidate list are available
        if not self.completer or not self.candidate_list:
            return
        
        # Clear focus when candidate list is updated due to typing
        # This ensures the focused candidate doesn't unexpectedly change
        # User must press Up/Down again to re-activate focus after typing
        self.candidate_list.clear_focus()
        
        # Get current candidates from completer
        candidates = self.completer.get_candidates(self.text, self.cursor_pos)
        
        # Update completion start position
        self.completion_start_pos = self.completer.get_completion_start_pos(
            self.text, self.cursor_pos
        )
        
        # Hide candidate list if no candidates
        if not candidates:
            self.candidate_list.hide()
            self.completion_active = False
            return
        
        # Mark completion as active - candidates will be displayed in draw()
        # The candidate list will remain visible even for single candidate (Req 2.6)
        self.completion_active = len(candidates) > 0
    
    def apply_candidate(self, candidate: str):
        """
        Apply a selected candidate to the text edit field.
        
        This method replaces the completion portion of the text (from the
        completion start position to the cursor) with the selected candidate.
        The cursor is then moved to the end of the inserted text.
        
        This is called when the user presses Enter with a focused candidate,
        allowing them to quickly apply a specific completion without typing
        the full text.
        
        Args:
            candidate: The candidate text to apply
        
        Requirements:
        - 10.1: Replace completion portion with focused candidate text
        - 10.2: Hide candidate list after applying selection
        - 10.3: Move cursor to end of inserted text
        """
        # Replace the completion portion with the selected candidate
        # The completion portion is from completion_start_pos to cursor_pos
        self.text = (
            self.text[:self.completion_start_pos] +
            candidate +
            self.text[self.cursor_pos:]
        )
        
        # Update cursor position to end of inserted text
        self.cursor_pos = self.completion_start_pos + len(candidate)
        
    def handle_key(self, event, handle_vertical_nav=False):
        """
        Handle a key press and update the text/cursor accordingly
        
        Args:
            event: KeyEvent or CharEvent from TTK
            handle_vertical_nav (bool): Whether to handle Up/Down keys for cursor movement
            
        Returns:
            bool: True if the key was handled, False otherwise
        """
        if not event:
            return False
        
        # Handle CharEvent - text input
        if isinstance(event, CharEvent):
            result = self.insert_char(event.char)
            # Update candidate list after text modification
            if result and self.completion_active:
                self.update_candidate_list()
            return result
        
        # Handle KeyEvent - navigation and editing commands
        if isinstance(event, KeyEvent):
            # Check for TAB key press - trigger completion
            if event.key_code == KeyCode.TAB:
                return self.handle_tab_completion()
            
            # Check for ESC key press - hide candidate list and clear focus
            if event.key_code == KeyCode.ESCAPE:
                if self.candidate_list and self.completion_active:
                    self.candidate_list.hide()
                    self.candidate_list.clear_focus()
                    self.completion_active = False
                    return True
                return False
            
            # Check for Up/Down arrow keys when candidate list is visible
            # These keys navigate through the candidate list
            if self.candidate_list and self.completion_active and self.candidate_list.is_visible:
                if event.key_code == KeyCode.DOWN:
                    # Move focus to next candidate
                    self.candidate_list.move_focus_down()
                    # Mark dirty to trigger redraw with updated focus
                    # (The parent component will handle the actual redraw)
                    return True
                elif event.key_code == KeyCode.UP:
                    # Move focus to previous candidate
                    self.candidate_list.move_focus_up()
                    # Mark dirty to trigger redraw with updated focus
                    # (The parent component will handle the actual redraw)
                    return True
            
            # Check for Enter key when candidate list has focus
            # This applies the focused candidate to the text edit
            if event.key_code == KeyCode.ENTER:
                if self.candidate_list and self.candidate_list.has_focus():
                    # Get the focused candidate
                    focused_candidate = self.candidate_list.get_focused_candidate()
                    if focused_candidate:
                        # Apply the candidate to the text
                        self.apply_candidate(focused_candidate)
                        # Hide the candidate list
                        self.candidate_list.hide()
                        self.completion_active = False
                        # Clear focus state
                        self.candidate_list.clear_focus()
                        return True
                # If no focus or no candidate list, fall through to normal Enter handling
                return False
            
            # Check for Cmd+V / Ctrl+V paste (exact modifier match)
            if event.char == 'v' and event.modifiers == ModifierKey.COMMAND:
                result = self.paste_from_clipboard()
                # Update candidate list after text modification
                if result and self.completion_active:
                    self.update_candidate_list()
                return result
            
            # Track if this is a text-modifying operation
            text_modified = False
            
            # Command+Left/Right for home/end (macOS style)
            if event.key_code == KeyCode.LEFT and event.modifiers == ModifierKey.COMMAND:
                return self.move_cursor_home()
            elif event.key_code == KeyCode.RIGHT and event.modifiers == ModifierKey.COMMAND:
                return self.move_cursor_end()
            # Command+Backspace to delete to beginning
            elif event.key_code == KeyCode.BACKSPACE and event.modifiers == ModifierKey.COMMAND:
                result = self.delete_to_beginning()
                text_modified = result
            # Word-level navigation with Alt modifier
            elif event.key_code == KeyCode.LEFT and event.modifiers == ModifierKey.ALT:
                return self.move_cursor_word_left()
            elif event.key_code == KeyCode.RIGHT and event.modifiers == ModifierKey.ALT:
                return self.move_cursor_word_right()
            # Word-level deletion with Alt+Backspace
            elif event.key_code == KeyCode.BACKSPACE and event.modifiers == ModifierKey.ALT:
                result = self.delete_word_backward()
                text_modified = result
            # Character-level navigation (no modifiers)
            elif event.key_code == KeyCode.LEFT:
                return self.move_cursor_left()
            elif event.key_code == KeyCode.RIGHT:
                return self.move_cursor_right()
            elif event.key_code == KeyCode.HOME:
                return self.move_cursor_home()
            elif event.key_code == KeyCode.END:
                return self.move_cursor_end()
            elif handle_vertical_nav and event.key_code == KeyCode.UP:
                # Up arrow - move to beginning of line when vertical nav is enabled
                return self.move_cursor_home()
            elif handle_vertical_nav and event.key_code == KeyCode.DOWN:
                # Down arrow - move to end of line when vertical nav is enabled
                return self.move_cursor_end()
            elif event.key_code == KeyCode.BACKSPACE:
                result = self.backspace()
                text_modified = result
            elif event.key_code == KeyCode.DELETE:
                result = self.delete_char_at_cursor()
                text_modified = result
            else:
                return False
            
            # Update candidate list after text modifications
            if text_modified and self.completion_active:
                self.update_candidate_list()
            
            return text_modified if text_modified else False
        
        return False
        
    def draw(self, renderer, y, x, max_width, label="", is_active=True):
        """
        Draw the text field with cursor highlighting, supporting wide characters
        
        Args:
            renderer: TTK Renderer instance
            y (int): Y coordinate to draw at
            x (int): X coordinate to draw at
            max_width (int): Maximum width for the entire field
            label (str): Optional label to display before the text
            is_active (bool): Whether to show the cursor
        """
        # Get safe wide character functions for current terminal
        safe_funcs = get_safe_functions()
        get_width = safe_funcs['get_display_width']
        truncate_text = safe_funcs['truncate_to_width']
        
        # Calculate available space for text after label using display width
        label_width = get_width(label)
        text_start_x = x + label_width
        text_max_width = max_width - label_width
        
        if text_max_width <= 0:
            # Not enough space - return early
            return
        
        # Get color and attributes
        base_color, default_attributes = get_status_color()
        base_attributes = TextAttribute.BOLD if is_active else default_attributes
        
        # Draw the label
        self._safe_draw_text(renderer, y, x, label, base_color, base_attributes)
        
        # Handle empty text case
        if not self.text:
            if is_active:
                # Show cursor at beginning of empty field
                self._safe_draw_text(renderer, y, text_start_x, " ", base_color, 
                                   base_attributes | TextAttribute.REVERSE)
                # Set caret position at the beginning of the text field
                renderer.set_caret_position(text_start_x, y)
            
            # Draw candidate list if active and visible
            if self.completion_active and self.candidate_list and self.completer:
                self._render_candidate_list(y, text_start_x)
            
            return
        
        # Ensure cursor is within bounds
        cursor_pos = max(0, min(self.cursor_pos, len(self.text)))
        
        # Calculate display width of entire text
        text_display_width = get_width(self.text)
        
        # Calculate visible text window if text is too wide
        visible_start = 0
        visible_end = len(self.text)
        
        if text_display_width > text_max_width:
            # Need to scroll text to keep cursor visible
            # Calculate display position of cursor
            cursor_display_pos = get_width(self.text[:cursor_pos])
            
            # Reserve space for cursor if it's at the end of text
            effective_max_width = text_max_width
            if cursor_pos == len(self.text) and text_max_width > 1:
                effective_max_width = text_max_width - 1  # Reserve space for end cursor
            
            if cursor_display_pos < effective_max_width // 2:
                # Cursor near start, show from beginning
                visible_text = truncate_text(self.text, effective_max_width, "")
                visible_end = len(visible_text)
            elif cursor_display_pos >= text_display_width - effective_max_width // 2:
                # Cursor near end, show end portion
                # Find starting position that gives us the right width
                target_width = effective_max_width
                temp_start = 0
                for i in range(len(self.text)):
                    remaining_text = self.text[i:]
                    if get_width(remaining_text) <= target_width:
                        temp_start = i
                        break
                visible_start = temp_start
            else:
                # Cursor in middle, center the view around cursor
                # Find a good starting position that centers the cursor
                half_width = effective_max_width // 2
                
                # Start from cursor and work backwards to find start position
                temp_start = cursor_pos
                accumulated_width = 0
                for i in range(cursor_pos - 1, -1, -1):
                    char_width = get_width(self.text[i])
                    if accumulated_width + char_width > half_width:
                        break
                    accumulated_width += char_width
                    temp_start = i
                
                visible_start = temp_start
                # Truncate from this position
                remaining_text = self.text[visible_start:]
                visible_text = truncate_text(remaining_text, effective_max_width, "")
                visible_end = visible_start + len(visible_text)
        
        visible_text = self.text[visible_start:visible_end]
        cursor_in_visible = cursor_pos - visible_start
        
        # Draw text with cursor highlighting, accounting for wide characters
        current_x = text_start_x
        caret_x = text_start_x  # Track caret position
        
        for i, char in enumerate(visible_text):
            char_width = get_width(char)
            
            if i == cursor_in_visible and is_active:
                # Draw cursor character with reversed colors
                self._safe_draw_text(renderer, y, current_x, char, base_color, 
                                   base_attributes | TextAttribute.REVERSE)
                # Store caret position at cursor
                caret_x = current_x
            else:
                # Draw normal character
                self._safe_draw_text(renderer, y, current_x, char, base_color, base_attributes)
            
            # Advance cursor position by character's display width
            current_x += char_width
        
        # If cursor is at the end of text and field is active, show cursor after last character
        if cursor_in_visible >= len(visible_text) and is_active:
            # Make sure we have space to draw the cursor
            if current_x < x + max_width:
                self._safe_draw_text(renderer, y, current_x, " ", base_color, 
                                   base_attributes | TextAttribute.REVERSE)
                # Store caret position at end
                caret_x = current_x
            elif len(visible_text) > 0:
                # If we're at the edge, we need to be more careful with wide characters
                # Find the last character that we can highlight as cursor
                last_char_pos = len(visible_text) - 1
                if last_char_pos >= 0:
                    last_char = visible_text[last_char_pos]
                    last_char_width = get_width(last_char)
                    last_char_x = current_x - last_char_width
                    self._safe_draw_text(renderer, y, last_char_x, last_char, base_color, 
                                       base_attributes | TextAttribute.REVERSE)
                    # Store caret position at last character
                    caret_x = last_char_x
        
        # Set caret position for IME composition text positioning
        # TTK refresh() will automatically restore this position
        if is_active:
            renderer.set_caret_position(caret_x, y)
        
        # Draw candidate list if active and visible
        if self.completion_active and self.candidate_list and self.completer:
            self._render_candidate_list(y, text_start_x)
    
    def _render_candidate_list(self, text_edit_y: int, text_edit_x: int):
        """
        Render the candidate list overlay with proper positioning.
        
        This method calculates the correct position for the candidate list
        based on available screen space and the completion start position,
        then updates the candidate list and makes it visible.
        
        Args:
            text_edit_y: Y coordinate of the text edit field
            text_edit_x: X coordinate where the text starts (after label)
        """
        # Get current candidates from completer
        candidates = self.completer.get_candidates(self.text, self.cursor_pos)
        
        if not candidates:
            self.candidate_list.hide()
            return
        
        # Get screen dimensions
        height, width = self.renderer.get_dimensions()
        
        # Calculate completion start X position
        # This is where the filename/directory name being completed begins
        safe_funcs = get_safe_functions()
        get_width = safe_funcs['get_display_width']
        
        # Get completion start position from completer
        completion_start_pos = self.completer.get_completion_start_pos(self.text, self.cursor_pos)
        
        # Get the text up to completion start position
        text_before_completion = self.text[:completion_start_pos]
        completion_start_display_x = text_edit_x + get_width(text_before_completion)
        
        # Determine if we should show above or below the text edit field
        # Calculate approximate height needed for candidate list
        num_candidates = min(len(candidates), self.candidate_list.max_visible_candidates)
        overlay_height = num_candidates + 2  # +2 for borders
        
        # Check if there's enough space below
        space_below = height - text_edit_y - 1
        space_above = text_edit_y
        
        # Prefer showing below unless there's not enough space
        show_above = space_below < overlay_height and space_above >= overlay_height
        
        # Update candidate list with position information
        self.candidate_list.set_candidates(
            candidates,
            text_edit_y,
            text_edit_x,
            completion_start_display_x,
            show_above
        )
        
        # Make candidate list visible
        self.candidate_list.show()
        
        # Draw the candidate list
        self.candidate_list.draw()
    
    def on_focus_gained(self):
        """
        Handle focus gained event.
        
        When the text field gains focus, the candidate list should NOT
        automatically appear. The user must press TAB to trigger completion.
        
        This method is called by the parent component when focus is gained.
        
        Requirements:
        - 8.4: Candidate list doesn't auto-appear on focus gain
        """
        # Do nothing - candidate list should only appear when TAB is pressed
        # This ensures the candidate list doesn't automatically show up
        # when the text field receives focus
        pass
    
    def on_focus_lost(self):
        """
        Handle focus lost event.
        
        When the text field loses focus, hide the candidate list to ensure
        it doesn't remain visible when the user is no longer editing this field.
        
        This method is called by the parent component when focus is lost.
        
        Requirements:
        - 8.3: Hide candidate list when text field loses focus
        """
        # Hide candidate list when focus is lost
        if self.candidate_list and self.completion_active:
            self.candidate_list.hide()
            self.candidate_list.clear_focus()
            self.completion_active = False
    
    def _safe_draw_text(self, renderer, y, x, text, color_pair, attributes):
        """Safely draw text to screen, handling boundary conditions and wide characters"""
        try:
            height, width = renderer.get_dimensions()
            if 0 <= y < height and 0 <= x < width:
                # Get safe wide character functions
                safe_funcs = get_safe_functions()
                get_width = safe_funcs['get_display_width']
                truncate_text = safe_funcs['truncate_to_width']
                
                # Calculate available display width
                max_display_width = width - x
                
                # Truncate text if it would go beyond screen width (by display width)
                if get_width(text) > max_display_width:
                    text = truncate_text(text, max_display_width, "")
                
                renderer.draw_text(y, x, text, color_pair=color_pair, attributes=attributes)
        except Exception:
            # Ignore rendering errors (e.g., writing to bottom-right corner)
            pass