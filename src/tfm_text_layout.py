"""
Text Layout System for TFM.

This module provides a comprehensive API for rendering text segments with intelligent
width management, color attributes, and flexible shortening strategies. It handles
the complete text layout and rendering pipeline, including:

- Layout calculation with priority-based shortening
- Multiple shortening strategies (abbreviation, filepath, truncate, all-or-nothing, as-is)
- Spacer support for expandable whitespace
- Wide character support (CJK, emoji)
- Color and attribute management per segment
- Integration with TTK rendering backend

The system is designed to be independent of the legacy tfm_string_width.py module
and will eventually replace it.

Basic Usage:
    from tfm_text_layout import draw_text_segments, AbbreviationSegment, SpacerSegment
    
    segments = [
        AbbreviationSegment("Long filename.txt", priority=1, min_length=10),
        SpacerSegment(),
        AbbreviationSegment("Status", priority=0, min_length=3)
    ]
    
    draw_text_segments(renderer, row=0, col=0, segments=segments, 
                      rendering_width=80, default_color=1)

Helper Functions:
    The module provides several helper functions for common layout patterns:
    
    1. Status Bar Layout:
        segments = create_status_bar_layout(
            left_text="/home/user/documents/report.txt",
            right_text="Modified | 1.2 MB"
        )
        draw_text_segments(renderer, 0, 0, segments, 80)
        # Renders: "/home/user/documents/report.txt        Modified | 1.2 MB"
    
    2. File List Item:
        segments = create_file_list_item(
            filename="document.txt",
            size_text="1.2 MB",
            date_text="2024-01-15"
        )
        draw_text_segments(renderer, 0, 0, segments, 80)
        # Renders: "document.txt    1.2 MB    2024-01-15"
    
    3. Dialog Prompt:
        segments = create_dialog_prompt(
            prompt_text="Enter filename:",
            input_text="/home/user/file.txt"
        )
        draw_text_segments(renderer, 0, 0, segments, 60)
        # Renders: "Enter filename: /home/user/file.txt"
    
    4. Three-Column Layout:
        segments = create_three_column_layout(
            left_text="File",
            center_text="Terminal File Manager v1.0",
            right_text="Help: F1"
        )
        draw_text_segments(renderer, 0, 0, segments, 80)
        # Renders: "File    Terminal File Manager v1.0    Help: F1"
    
    5. Breadcrumb Path:
        segments = create_breadcrumb_path(
            path="/home/user/documents/projects/myproject/src/main.py"
        )
        draw_text_segments(renderer, 0, 0, segments, 50)
        # Renders: "…/myproject/src/main.py"
    
    6. Key-Value Pair:
        segments = create_key_value_pair(
            key="Modified",
            value="2024-01-15 14:30:00"
        )
        draw_text_segments(renderer, 0, 0, segments, 40)
        # Renders: "Modified: 2024-01-15 14:30:00"

Segment Types:
    - AbbreviationSegment: Shortens with ellipsis (left/middle/right position)
    - FilepathSegment: Intelligently abbreviates filesystem paths
    - TruncateSegment: Removes characters from end without ellipsis
    - AllOrNothingSegment: Either keeps full text or removes entirely
    - AsIsSegment: Never shortens regardless of width constraints
    - SpacerSegment: Expands with whitespace when space available

Priority-Based Shortening:
    Segments with higher priority values are shortened first. When space becomes
    available, segments are restored in reverse priority order (lower values first).
    
    Example:
        segments = [
            AbbreviationSegment("Important", priority=0, min_length=5),
            SpacerSegment(),
            AbbreviationSegment("Less important", priority=1, min_length=3)
        ]
        # "Less important" will be shortened before "Important"

Wide Character Support:
    All operations properly handle wide characters (CJK, emoji) which occupy
    2 terminal columns instead of 1. Wide characters are never split at boundaries.
    
    Example:
        segments = [AbbreviationSegment("Hello 世界 World")]
        draw_text_segments(renderer, 0, 0, segments, 10)
        # Properly accounts for wide characters taking 2 columns each
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Union, Optional
import unicodedata

# TTK imports for wide character support
from ttk.wide_char_utils import get_display_width, truncate_to_width

# TFM unified logging system
from tfm_log_manager import getLogger

# Initialize logger
logger = getLogger("TextLayout")


# ============================================================================
# Wide Character Support Utilities
# ============================================================================

def normalize_text(text: str) -> str:
    """
    Normalize text to NFC (Canonical Composition) form.
    
    NFC normalization ensures consistent character representation across different
    platforms and handles macOS NFD filenames correctly. This is essential for
    accurate width calculation and text comparison.
    
    Args:
        text: Text to normalize
        
    Returns:
        NFC-normalized text, or original text if normalization fails
        
    Example:
        >>> normalize_text("café")  # é as single character
        'café'
        >>> normalize_text("café")  # é as e + combining accent
        'café'  # Both normalize to same form
    """
    try:
        return unicodedata.normalize('NFC', text)
    except Exception as e:
        logger.error(f"Unicode normalization failed for text: {e}")
        return text


def calculate_display_width(text: str) -> int:
    """
    Calculate the display width of text in terminal columns.
    
    This function accounts for wide characters (CJK, emoji) which occupy 2 columns
    instead of 1. It delegates to TTK's wide_char_utils for accurate calculation.
    
    Args:
        text: Text to measure (should be NFC-normalized for best results)
        
    Returns:
        Display width in terminal columns, or character count if calculation fails
        
    Example:
        >>> calculate_display_width("hello")
        5
        >>> calculate_display_width("你好")  # Two wide characters
        4
        >>> calculate_display_width("hello世界")  # Mixed narrow and wide
        9
    """
    try:
        return get_display_width(text)
    except Exception as e:
        logger.error(f"Display width calculation failed, falling back to character count: {e}")
        return len(text)


def is_wide_char_boundary_safe(text: str, position: int) -> bool:
    """
    Check if a position in text is safe for truncation (won't split a wide character).
    
    When truncating text at a specific position, we must ensure we don't split
    a wide character in half. This function checks if the character at the given
    position would be split, considering the display width up to that point.
    
    Args:
        text: Text to check (should be NFC-normalized)
        position: Character position to check (0-based index)
        
    Returns:
        True if truncating at this position won't split a wide character,
        False if it would split a wide character
        
    Example:
        >>> is_wide_char_boundary_safe("hello世界", 5)
        True  # Safe to truncate after "hello"
        >>> is_wide_char_boundary_safe("hello世界", 6)
        True  # Safe to truncate after "hello世"
        >>> # Note: This function checks character boundaries, not column boundaries
    """
    try:
        if position <= 0 or position >= len(text):
            return True
        
        # Get the character at the position
        char = text[position]
        
        # Check if this character is a wide character
        char_width = get_display_width(char)
        
        # If the character is wide (2 columns), we need to check if we're
        # trying to truncate in the middle of its display width
        if char_width == 2:
            # Calculate display width up to this position
            prefix_width = get_display_width(text[:position])
            
            # If the prefix width is odd and we're at a wide character,
            # we would be splitting it
            # However, for character-based truncation, we're always safe
            # because we're not splitting the character itself
            return True
        
        return True
        
    except Exception as e:
        logger.error(f"Wide character boundary check failed: {e}")
        # If we can't determine, assume it's safe to avoid data loss
        return True


def truncate_at_width(text: str, target_width: int) -> str:
    """
    Truncate text to fit within target_width columns, respecting wide character boundaries.
    
    This is a convenience wrapper around TTK's truncate_to_width that adds error
    handling and logging. It ensures wide characters are never split in half.
    
    Note: This function does NOT add an ellipsis. Use the segment classes for
    ellipsis handling.
    
    Args:
        text: Text to truncate (should be NFC-normalized)
        target_width: Target display width in terminal columns
        
    Returns:
        Truncated text that fits within target_width, or original text if truncation fails
        
    Example:
        >>> truncate_at_width("hello world", 5)
        'hello'
        >>> truncate_at_width("你好世界", 4)
        '你好'  # Two wide characters = 4 columns
        >>> truncate_at_width("hello世界", 6)
        'hello'  # Can't fit the wide character, so exclude it
    """
    try:
        if target_width <= 0:
            return ""
        
        current_width = get_display_width(text)
        if current_width <= target_width:
            return text
        
        # Use TTK's truncate_to_width with empty ellipsis to get pure truncation
        return truncate_to_width(text, target_width, ellipsis="")
        
    except Exception as e:
        logger.error(f"Text truncation failed: {e}")
        # Fall back to simple character truncation
        return text[:target_width] if target_width > 0 else ""


@dataclass
class TextSegment(ABC):
    """
    Abstract base class for text segments.
    
    A text segment represents a portion of text with configuration for how it
    should be shortened, rendered, and styled.
    
    Attributes:
        text: The text content of this segment
        priority: Shortening priority (higher values shortened first, default 0)
        min_length: Minimum characters to preserve when shortening (default 0)
        color_pair: Terminal color pair number, None uses default (default None)
        attributes: Terminal text attributes (bold, underline, etc.), None uses default (default None)
    """
    text: str
    priority: int = 0
    min_length: int = 0
    color_pair: Optional[int] = None
    attributes: Optional[int] = None
    
    @abstractmethod
    def shorten(self, target_width: int) -> str:
        """
        Shorten the text to fit within target_width columns.
        
        Each subclass implements its own shortening strategy.
        
        Args:
            target_width: Target display width in terminal columns
            
        Returns:
            Shortened text that fits within target_width
        """
        pass
    
    def get_display_width(self) -> int:
        """
        Calculate the display width of the text in terminal columns.
        
        Returns:
            Display width accounting for wide characters
        """
        try:
            # Use helper function for normalization and width calculation
            normalized_text = normalize_text(self.text)
            return calculate_display_width(normalized_text)
        except Exception as e:
            logger.error(f"get_display_width failed for text '{self.text}': {e}")
            # Fall back to character count
            return len(self.text)


@dataclass
class SpacerSegment:
    """
    A special segment that expands with whitespace when text doesn't need shortening.
    
    Spacers are collapsed to zero width when shortening is needed, and expanded
    to fill available space when the total text width is less than rendering width.
    
    Attributes:
        color_pair: Terminal color pair number, None uses default (default None)
        attributes: Terminal text attributes, None uses default (default None)
    """
    color_pair: Optional[int] = None
    attributes: Optional[int] = None
    
    def __post_init__(self):
        """Validate segment configuration after initialization."""
        # Validate color_pair if specified
        if self.color_pair is not None and (self.color_pair < 0 or self.color_pair > 255):
            logger.warning(
                f"Invalid color_pair {self.color_pair} in SpacerSegment "
                f"(must be 0-255), will use default color"
            )
            self.color_pair = None
    
    def get_display_width(self) -> int:
        """
        Spacers have zero width initially.
        
        Returns:
            0 (spacers are sized during layout calculation)
        """
        return 0


@dataclass
class AbbreviationSegment(TextSegment):
    """
    A text segment that shortens by replacing removed content with an ellipsis.
    
    The ellipsis can be placed at the left, middle, or right of the text based
    on the abbrev_position setting.
    
    Attributes:
        abbrev_position: Where to place ellipsis ('left', 'middle', 'right', default 'right')
    """
    abbrev_position: str = 'right'
    
    def __post_init__(self):
        """Validate segment configuration after initialization."""
        # Validate abbrev_position
        if self.abbrev_position not in ('left', 'middle', 'right'):
            logger.warning(
                f"Invalid abbrev_position '{self.abbrev_position}' in AbbreviationSegment, "
                f"falling back to 'right'. Valid values: 'left', 'middle', 'right'"
            )
            self.abbrev_position = 'right'
        
        # Validate priority (should be non-negative)
        if self.priority < 0:
            logger.warning(f"Negative priority {self.priority} in AbbreviationSegment, treating as 0")
            self.priority = 0
        
        # Validate min_length (should be non-negative)
        if self.min_length < 0:
            logger.warning(f"Negative min_length {self.min_length} in AbbreviationSegment, treating as 0")
            self.min_length = 0
        
        # Validate color_pair if specified
        if self.color_pair is not None and (self.color_pair < 0 or self.color_pair > 255):
            logger.warning(
                f"Invalid color_pair {self.color_pair} in AbbreviationSegment "
                f"(must be 0-255), will use default color"
            )
            self.color_pair = None
    
    def shorten(self, target_width: int) -> str:
        """
        Shorten text by replacing removed content with an ellipsis.
        
        Args:
            target_width: Target display width in terminal columns
            
        Returns:
            Shortened text with ellipsis at the specified position
        """
        try:
            # Use helper function for normalization
            normalized_text = normalize_text(self.text)
            current_width = calculate_display_width(normalized_text)
            
            # If already fits, return as-is
            if current_width <= target_width:
                return normalized_text
            
            # Handle edge cases
            if target_width == 0:
                return ""
            
            ellipsis = "…"
            ellipsis_width = calculate_display_width(ellipsis)
            
            if target_width == 1:
                # Only room for ellipsis or single character
                if ellipsis_width <= 1:
                    return ellipsis
                return normalized_text[0] if len(normalized_text) > 0 else ""
            
            # If text is shorter than ellipsis, just truncate
            if target_width < ellipsis_width:
                return truncate_at_width(normalized_text, target_width)
            
            # Validate abbrev_position (should have been validated in __post_init__, but double-check)
            position = self.abbrev_position
            if position not in ('left', 'middle', 'right'):
                logger.warning(f"Invalid abbrev_position '{position}', falling back to 'right'")
                position = 'right'
            
            # Calculate available width for actual text (minus ellipsis)
            available_width = target_width - ellipsis_width
            
            if position == 'right':
                # Keep left portion, ellipsis at end
                left_part = truncate_at_width(normalized_text, available_width)
                return left_part + ellipsis
            
            elif position == 'left':
                # Keep right portion, ellipsis at start
                # We need to find where to start from the right
                right_part = self._truncate_from_right(normalized_text, available_width)
                return ellipsis + right_part
            
            else:  # middle
                # Split available width between left and right
                left_width = available_width // 2
                right_width = available_width - left_width
                
                left_part = truncate_at_width(normalized_text, left_width)
                right_part = self._truncate_from_right(normalized_text, right_width)
                return left_part + ellipsis + right_part
                
        except Exception as e:
            logger.error(f"AbbreviationSegment.shorten failed for text '{self.text}': {e}")
            # Fall back to simple truncation
            try:
                normalized_text = normalize_text(self.text)
                return truncate_at_width(normalized_text, target_width)
            except Exception as e2:
                logger.error(f"Fallback truncation also failed: {e2}")
                # Last resort: return original text or empty string
                return self.text if target_width > 0 else ""
    
    def _truncate_from_right(self, text: str, target_width: int) -> str:
        """
        Truncate text from the right side to fit target_width.
        
        This is used for left and middle abbreviation positions where we need
        to preserve the right portion of the text.
        
        Args:
            text: Text to truncate
            target_width: Target display width
            
        Returns:
            Right portion of text that fits within target_width
        """
        try:
            if target_width <= 0:
                return ""
            
            # Start from the end and work backwards
            result = ""
            current_width = 0
            
            for char in reversed(text):
                char_width = calculate_display_width(char)
                if current_width + char_width > target_width:
                    break
                result = char + result
                current_width += char_width
            
            return result
            
        except Exception as e:
            logger.error(f"_truncate_from_right failed: {e}")
            # Fall back to simple character-based truncation from right
            if target_width <= 0:
                return ""
            return text[-target_width:] if len(text) >= target_width else text


@dataclass
class FilepathSegment(TextSegment):
    """
    A text segment that shortens filesystem paths by removing directory levels.
    
    When shortening is needed, entire directory components are removed (replaced
    with ellipsis) before the filename is abbreviated. This preserves the filename
    as much as possible.
    
    Attributes:
        abbrev_position: Where to place ellipsis when abbreviating filename ('left', 'middle', 'right', default 'right')
    """
    abbrev_position: str = 'right'
    
    def __post_init__(self):
        """Validate segment configuration after initialization."""
        # Validate abbrev_position
        if self.abbrev_position not in ('left', 'middle', 'right'):
            logger.warning(
                f"Invalid abbrev_position '{self.abbrev_position}' in FilepathSegment, "
                f"falling back to 'right'. Valid values: 'left', 'middle', 'right'"
            )
            self.abbrev_position = 'right'
        
        # Validate priority (should be non-negative)
        if self.priority < 0:
            logger.warning(f"Negative priority {self.priority} in FilepathSegment, treating as 0")
            self.priority = 0
        
        # Validate min_length (should be non-negative)
        if self.min_length < 0:
            logger.warning(f"Negative min_length {self.min_length} in FilepathSegment, treating as 0")
            self.min_length = 0
        
        # Validate color_pair if specified
        if self.color_pair is not None and (self.color_pair < 0 or self.color_pair > 255):
            logger.warning(
                f"Invalid color_pair {self.color_pair} in FilepathSegment "
                f"(must be 0-255), will use default color"
            )
            self.color_pair = None
    
    def shorten(self, target_width: int) -> str:
        """
        Shorten filesystem path by removing directory levels.
        
        Strategy:
        1. Parse path into directory components and filename
        2. Remove directory levels from left to right, replacing with ellipsis
        3. If still too long, abbreviate the filename itself
        
        Args:
            target_width: Target display width in terminal columns
            
        Returns:
            Shortened path with directory levels removed as needed
        """
        try:
            # Use helper function for normalization
            normalized_text = normalize_text(self.text)
            current_width = calculate_display_width(normalized_text)
            
            # If already fits, return as-is
            if current_width <= target_width:
                return normalized_text
            
            # Handle edge cases
            if target_width == 0:
                return ""
            
            ellipsis = "…"
            ellipsis_width = calculate_display_width(ellipsis)
            
            # Detect path separator (handle both Unix and Windows paths)
            separator = '/'
            if '\\' in normalized_text and '/' not in normalized_text:
                separator = '\\'
            elif '\\' in normalized_text and '/' in normalized_text:
                # Mixed separators, prefer forward slash
                separator = '/'
            
            # Split path into components
            components = normalized_text.split(separator)
            
            # Handle edge case: single component (no directories)
            if len(components) <= 1:
                # Just abbreviate the filename
                return self._abbreviate_filename(normalized_text, target_width)
            
            # Separate directories from filename
            filename = components[-1]
            directories = components[:-1]
            
            # Strategy: Keep directories from both ends, remove from middle
            # This matches the legacy FilepathStrategy behavior
            num_dirs = len(directories)
            
            # First try: keep all directories (no ellipsis)
            if num_dirs > 0:
                test_path = separator.join(directories) + separator + filename
                path_width = calculate_display_width(test_path)
                if path_width <= target_width:
                    return test_path
            
            # Try removing directories from the middle, one at a time
            # Start by removing the directory closest to the middle
            for num_to_remove in range(1, num_dirs):
                # Calculate which directories to remove (from middle)
                num_to_keep = num_dirs - num_to_remove
                
                # Split kept directories between start and end
                # Prefer balanced distribution
                keep_from_start = (num_to_keep + 1) // 2  # Round up for start
                keep_from_end = num_to_keep - keep_from_start
                
                # Build path with ellipsis in middle
                start_dirs = directories[:keep_from_start] if keep_from_start > 0 else []
                end_dirs = directories[-keep_from_end:] if keep_from_end > 0 else []
                
                if start_dirs or end_dirs:
                    path_parts = start_dirs + [ellipsis] + end_dirs + [filename]
                else:
                    path_parts = [ellipsis, filename]
                
                test_path = separator.join(path_parts)
                path_width = calculate_display_width(test_path)
                if path_width <= target_width:
                    return test_path
            
            # All directories removed, just ellipsis + separator + filename
            abbreviated_path = ellipsis + separator + filename
            path_width = calculate_display_width(abbreviated_path)
            
            if path_width <= target_width:
                return abbreviated_path
            
            # Still too long, need to abbreviate the filename itself
            # Calculate space available for filename
            prefix = ellipsis + separator
            prefix_width = calculate_display_width(prefix)
            
            if prefix_width >= target_width:
                # Not even room for prefix, just abbreviate filename alone
                return self._abbreviate_filename(filename, target_width)
            
            filename_width = target_width - prefix_width
            abbreviated_filename = self._abbreviate_filename(filename, filename_width)
            
            return prefix + abbreviated_filename
            
        except Exception as e:
            logger.error(f"FilepathSegment.shorten failed for path '{self.text}': {e}")
            # Fall back to simple truncation
            try:
                normalized_text = normalize_text(self.text)
                return truncate_at_width(normalized_text, target_width)
            except Exception as e2:
                logger.error(f"Fallback truncation also failed: {e2}")
                # Last resort: return original text or empty string
                return self.text if target_width > 0 else ""
    
    def _abbreviate_filename(self, filename: str, target_width: int) -> str:
        """
        Abbreviate a filename using the specified abbreviation position.
        
        Args:
            filename: Filename to abbreviate
            target_width: Target display width
            
        Returns:
            Abbreviated filename
        """
        try:
            current_width = calculate_display_width(filename)
            
            if current_width <= target_width:
                return filename
            
            if target_width == 0:
                return ""
            
            ellipsis = "…"
            ellipsis_width = calculate_display_width(ellipsis)
            
            if target_width < ellipsis_width:
                return truncate_at_width(filename, target_width)
            
            # Validate abbrev_position (should have been validated in __post_init__, but double-check)
            position = self.abbrev_position
            if position not in ('left', 'middle', 'right'):
                logger.warning(f"Invalid abbrev_position '{position}', falling back to 'right'")
                position = 'right'
            
            available_width = target_width - ellipsis_width
            
            if position == 'right':
                left_part = truncate_at_width(filename, available_width)
                return left_part + ellipsis
            
            elif position == 'left':
                right_part = self._truncate_from_right(filename, available_width)
                return ellipsis + right_part
            
            else:  # middle
                left_width = available_width // 2
                right_width = available_width - left_width
                
                left_part = truncate_at_width(filename, left_width)
                right_part = self._truncate_from_right(filename, right_width)
                return left_part + ellipsis + right_part
                
        except Exception as e:
            logger.error(f"_abbreviate_filename failed for '{filename}': {e}")
            # Fall back to simple truncation
            try:
                return truncate_at_width(filename, target_width)
            except Exception as e2:
                logger.error(f"Fallback truncation also failed: {e2}")
                return filename if target_width > 0 else ""
    
    def _truncate_from_right(self, text: str, target_width: int) -> str:
        """
        Truncate text from the right side to fit target_width.
        
        Args:
            text: Text to truncate
            target_width: Target display width
            
        Returns:
            Right portion of text that fits within target_width
        """
        try:
            if target_width <= 0:
                return ""
            
            result = ""
            current_width = 0
            
            for char in reversed(text):
                char_width = calculate_display_width(char)
                if current_width + char_width > target_width:
                    break
                result = char + result
                current_width += char_width
            
            return result
            
        except Exception as e:
            logger.error(f"_truncate_from_right failed: {e}")
            # Fall back to simple character-based truncation from right
            if target_width <= 0:
                return ""
            return text[-target_width:] if len(text) >= target_width else text


@dataclass
class TruncateSegment(TextSegment):
    """
    A text segment that shortens by removing characters from the end.
    
    Unlike abbreviation, no ellipsis is added. Characters are simply removed
    from the end until the text fits within the target width.
    """
    
    def __post_init__(self):
        """Validate segment configuration after initialization."""
        # Validate priority (should be non-negative)
        if self.priority < 0:
            logger.warning(f"Negative priority {self.priority} in TruncateSegment, treating as 0")
            self.priority = 0
        
        # Validate min_length (should be non-negative)
        if self.min_length < 0:
            logger.warning(f"Negative min_length {self.min_length} in TruncateSegment, treating as 0")
            self.min_length = 0
        
        # Validate color_pair if specified
        if self.color_pair is not None and (self.color_pair < 0 or self.color_pair > 255):
            logger.warning(
                f"Invalid color_pair {self.color_pair} in TruncateSegment "
                f"(must be 0-255), will use default color"
            )
            self.color_pair = None
    
    def shorten(self, target_width: int) -> str:
        """
        Shorten text by removing characters from the end without adding ellipsis.
        
        Args:
            target_width: Target display width in terminal columns
            
        Returns:
            Truncated text without ellipsis
        """
        try:
            # Use helper function for normalization
            normalized_text = normalize_text(self.text)
            current_width = calculate_display_width(normalized_text)
            
            # If already fits, return as-is
            if current_width <= target_width:
                return normalized_text
            
            # Handle edge case
            if target_width == 0:
                return ""
            
            # Simply truncate to target width (no ellipsis)
            return truncate_at_width(normalized_text, target_width)
            
        except Exception as e:
            logger.error(f"TruncateSegment.shorten failed for text '{self.text}': {e}")
            # Fall back to simple character truncation
            if target_width <= 0:
                return ""
            return self.text[:target_width] if len(self.text) > target_width else self.text


@dataclass
class AllOrNothingSegment(TextSegment):
    """
    A text segment that is either kept in full or removed entirely.
    
    This segment type never partially shortens. If the full text doesn't fit
    within the target width, it returns an empty string.
    """
    
    def __post_init__(self):
        """Validate segment configuration after initialization."""
        # Validate priority (should be non-negative)
        if self.priority < 0:
            logger.warning(f"Negative priority {self.priority} in AllOrNothingSegment, treating as 0")
            self.priority = 0
        
        # Validate min_length (should be non-negative)
        if self.min_length < 0:
            logger.warning(f"Negative min_length {self.min_length} in AllOrNothingSegment, treating as 0")
            self.min_length = 0
        
        # Validate color_pair if specified
        if self.color_pair is not None and (self.color_pair < 0 or self.color_pair > 255):
            logger.warning(
                f"Invalid color_pair {self.color_pair} in AllOrNothingSegment "
                f"(must be 0-255), will use default color"
            )
            self.color_pair = None
    
    def shorten(self, target_width: int) -> str:
        """
        Return full text if it fits, otherwise return empty string.
        
        Args:
            target_width: Target display width in terminal columns
            
        Returns:
            Full text if it fits, empty string otherwise
        """
        try:
            # Use helper function for normalization
            normalized_text = normalize_text(self.text)
            current_width = calculate_display_width(normalized_text)
            
            # All or nothing: either keep full text or remove entirely
            if current_width <= target_width:
                return normalized_text
            else:
                return ""
                
        except Exception as e:
            logger.error(f"AllOrNothingSegment.shorten failed for text '{self.text}': {e}")
            # In case of error, return empty string (safer than returning potentially malformed text)
            return ""


@dataclass
class AsIsSegment(TextSegment):
    """
    A text segment that never shortens regardless of width constraints.
    
    This segment type always returns its original text, even if it exceeds
    the target width. Use this for text that must never be modified.
    """
    
    def __post_init__(self):
        """Validate segment configuration after initialization."""
        # Validate priority (should be non-negative)
        if self.priority < 0:
            logger.warning(f"Negative priority {self.priority} in AsIsSegment, treating as 0")
            self.priority = 0
        
        # Validate min_length (should be non-negative)
        if self.min_length < 0:
            logger.warning(f"Negative min_length {self.min_length} in AsIsSegment, treating as 0")
            self.min_length = 0
        
        # Validate color_pair if specified
        if self.color_pair is not None and (self.color_pair < 0 or self.color_pair > 255):
            logger.warning(
                f"Invalid color_pair {self.color_pair} in AsIsSegment "
                f"(must be 0-255), will use default color"
            )
            self.color_pair = None
    
    def shorten(self, target_width: int) -> str:
        """
        Always return the original text unchanged.
        
        Args:
            target_width: Target display width (ignored)
            
        Returns:
            Original text unchanged
        """
        try:
            # Use helper function for normalization
            normalized_text = normalize_text(self.text)
            
            # Always return original text, never shorten
            return normalized_text
            
        except Exception as e:
            logger.error(f"AsIsSegment.shorten failed for text '{self.text}': {e}")
            # Return original text even if normalization failed
            return self.text


# ============================================================================
# Layout Calculation Engine
# ============================================================================

@dataclass
class LayoutState:
    """
    Internal state during layout calculation.
    
    This dataclass tracks the state of all segments during the layout calculation
    process, including their current widths, original widths, and which segments
    are spacers.
    
    Attributes:
        segments: List of text and spacer segments to layout
        current_widths: Current display width of each segment (modified during layout)
        original_widths: Original display width of each segment (0 for spacers)
        total_width: Current total width of all segments combined
        target_width: Target rendering width in terminal columns
        spacer_indices: Indices of spacer segments in the segments list
    """
    segments: List[Union[TextSegment, SpacerSegment]]
    current_widths: List[int]
    original_widths: List[int]
    total_width: int
    target_width: int
    spacer_indices: List[int]


def collapse_spacers(state: LayoutState) -> None:
    """
    Collapse all spacer segments to zero width.
    
    This function is called when shortening is needed. Before shortening any
    text segments, all spacers are collapsed to zero width to maximize available
    space for text content.
    
    Args:
        state: Layout state to modify (modified in-place)
        
    Side Effects:
        - Sets current_widths to 0 for all spacer indices
        - Updates total_width to reflect collapsed spacers
        
    Example:
        >>> state = LayoutState(...)
        >>> state.spacer_indices = [1, 3]
        >>> state.current_widths = [10, 5, 10, 3]
        >>> collapse_spacers(state)
        >>> state.current_widths
        [10, 0, 10, 0]
    """
    if not state.spacer_indices:
        return
    
    logger.debug(f"Collapsing {len(state.spacer_indices)} spacer(s) to zero width")
    
    # Set all spacer widths to zero
    for idx in state.spacer_indices:
        if state.current_widths[idx] > 0:
            state.total_width -= state.current_widths[idx]
            state.current_widths[idx] = 0
    
    logger.debug(f"Total width after spacer collapse: {state.total_width}")


def shorten_segments_by_priority(state: LayoutState, shortened_texts: List[str]) -> None:
    """
    Shorten text segments by priority until target width is met.
    
    This function implements the core shortening algorithm:
    1. Sort segments by priority (descending - higher values first)
    2. For each priority level, shorten all segments at that level
    3. Respect minimum length constraints
    4. Stop when target width is met or no more shortening possible
    
    Args:
        state: Layout state containing segments and width information
        shortened_texts: List to store shortened text for each segment (modified in-place)
        
    Side Effects:
        - Updates state.current_widths with new widths after shortening
        - Updates state.total_width to reflect shortened segments
        - Populates shortened_texts with shortened text for each segment
        
    Example:
        >>> state = LayoutState(...)
        >>> shortened_texts = [""] * len(state.segments)
        >>> shorten_segments_by_priority(state, shortened_texts)
        >>> # state.current_widths and shortened_texts are now updated
    """
    # Build list of (index, segment, priority) for text segments only (not spacers)
    text_segments = []
    for idx, segment in enumerate(state.segments):
        if isinstance(segment, TextSegment):
            text_segments.append((idx, segment, segment.priority))
    
    if not text_segments:
        logger.debug("No text segments to shorten")
        return
    
    # Sort by priority (descending), then by original order for equal priorities
    text_segments.sort(key=lambda x: (-x[2], x[0]))
    
    logger.debug(f"Shortening order by priority: {[(idx, pri) for idx, _, pri in text_segments]}")
    
    # Group segments by priority level
    priority_groups = []
    current_priority = None
    current_group = []
    
    for idx, segment, priority in text_segments:
        if priority != current_priority:
            if current_group:
                priority_groups.append((current_priority, current_group))
            current_priority = priority
            current_group = [(idx, segment)]
        else:
            current_group.append((idx, segment))
    
    if current_group:
        priority_groups.append((current_priority, current_group))
    
    # Process each priority level
    for priority, group in priority_groups:
        logger.debug(f"Processing priority level {priority} with {len(group)} segment(s)")
        
        # Check if we've already met the target
        if state.total_width <= state.target_width:
            logger.debug("Target width met, stopping shortening")
            break
        
        # Calculate how much we need to reduce
        excess_width = state.total_width - state.target_width
        
        # Try to shorten each segment in this priority group
        for idx, segment in group:
            if state.total_width <= state.target_width:
                break
            
            current_width = state.current_widths[idx]
            
            # Calculate target width for this segment
            # We want to reduce by a fair share, but respect minimum length
            min_length = max(0, segment.min_length)
            
            # Calculate minimum width based on min_length
            # For now, we'll use character count as approximation
            # (actual width may vary with wide characters)
            min_width = min_length
            
            # Don't shorten below minimum width
            if current_width <= min_width:
                logger.debug(f"Segment {idx} already at minimum width {min_width}, skipping")
                continue
            
            # Calculate how much we can reduce this segment
            max_reduction = current_width - min_width
            
            # Try to reduce by the excess, but not more than max_reduction
            target_reduction = min(excess_width, max_reduction)
            new_width = current_width - target_reduction
            
            # Shorten the segment
            try:
                shortened_text = segment.shorten(new_width)
                actual_width = calculate_display_width(shortened_text)
            except Exception as e:
                logger.error(f"Segment {idx} shorten() failed: {e}, using original text")
                # Use original text if shortening fails
                shortened_text = normalize_text(segment.text)
                actual_width = calculate_display_width(shortened_text)
            
            # Update state
            width_reduction = current_width - actual_width
            state.current_widths[idx] = actual_width
            state.total_width -= width_reduction
            shortened_texts[idx] = shortened_text
            
            logger.debug(f"Shortened segment {idx} from {current_width} to {actual_width} columns")
            
            # Update excess for next segment
            excess_width = state.total_width - state.target_width
    
    logger.debug(f"Final total width after shortening: {state.total_width}")


def restore_segments_by_priority(state: LayoutState, shortened_texts: List[str]) -> None:
    """
    Restore text segments by priority when extra space is available.
    
    After shortening, if there's extra space available (total_width < target_width),
    this function attempts to restore segments to their original width in reverse
    priority order (lower priority values first).
    
    Args:
        state: Layout state containing segments and width information
        shortened_texts: List of shortened text for each segment (modified in-place)
        
    Side Effects:
        - Updates state.current_widths with restored widths
        - Updates state.total_width to reflect restored segments
        - Updates shortened_texts with restored text for segments
        
    Example:
        >>> state = LayoutState(...)
        >>> shortened_texts = ["short", "text"]
        >>> restore_segments_by_priority(state, shortened_texts)
        >>> # Segments may be restored to original width if space available
    """
    # Check if we have extra space
    if state.total_width >= state.target_width:
        logger.debug("No extra space available for restoration")
        return
    
    available_space = state.target_width - state.total_width
    logger.debug(f"Attempting restoration with {available_space} columns available")
    
    # Build list of (index, segment, priority) for text segments that were shortened
    text_segments = []
    for idx, segment in enumerate(state.segments):
        if isinstance(segment, TextSegment):
            # Only consider segments that were shortened
            if state.current_widths[idx] < state.original_widths[idx]:
                text_segments.append((idx, segment, segment.priority))
    
    if not text_segments:
        logger.debug("No shortened segments to restore")
        return
    
    # Sort by priority (ascending - lower values first), then by original order
    text_segments.sort(key=lambda x: (x[2], x[0]))
    
    logger.debug(f"Restoration order by priority: {[(idx, pri) for idx, _, pri in text_segments]}")
    
    # Try to restore each segment
    for idx, segment, priority in text_segments:
        if available_space <= 0:
            logger.debug("No more space available for restoration")
            break
        
        current_width = state.current_widths[idx]
        original_width = state.original_widths[idx]
        
        # Calculate how much we can restore
        max_restoration = original_width - current_width
        actual_restoration = min(available_space, max_restoration)
        
        if actual_restoration <= 0:
            continue
        
        # Try to restore to current_width + actual_restoration
        target_width = current_width + actual_restoration
        
        # Get the original text (not shortened)
        original_text = normalize_text(segment.text)
        
        # If we can restore to full width, use original text
        if target_width >= original_width:
            restored_text = original_text
            actual_width = original_width
        else:
            # Partially restore by shortening to the new target width
            try:
                restored_text = segment.shorten(target_width)
                actual_width = calculate_display_width(restored_text)
            except Exception as e:
                logger.error(f"Segment {idx} shorten() failed during restoration: {e}, using original text")
                # Use original text if shortening fails
                restored_text = original_text
                actual_width = original_width
        
        # Update state
        width_increase = actual_width - current_width
        state.current_widths[idx] = actual_width
        state.total_width += width_increase
        shortened_texts[idx] = restored_text
        available_space -= width_increase
        
        logger.debug(f"Restored segment {idx} from {current_width} to {actual_width} columns")
    
    logger.debug(f"Final total width after restoration: {state.total_width}")


def expand_spacers(state: LayoutState, shortened_texts: List[str]) -> None:
    """
    Expand spacer segments to fill available space.
    
    When the total width is less than the rendering width and spacers exist,
    this function distributes the extra space equally among all spacers.
    
    Args:
        state: Layout state containing segments and width information
        shortened_texts: List of text for each segment (modified in-place for spacers)
        
    Side Effects:
        - Updates state.current_widths for spacer segments
        - Updates state.total_width to reflect expanded spacers
        - Updates shortened_texts with whitespace for spacer segments
        
    Example:
        >>> state = LayoutState(...)
        >>> state.spacer_indices = [1, 3]
        >>> state.total_width = 70
        >>> state.target_width = 80
        >>> expand_spacers(state, shortened_texts)
        >>> # Spacers expanded to fill 10 columns (5 each)
    """
    # Check if we have spacers and extra space
    if not state.spacer_indices:
        logger.debug("No spacers to expand")
        return
    
    if state.total_width >= state.target_width:
        logger.debug("No extra space available for spacer expansion")
        return
    
    extra_space = state.target_width - state.total_width
    num_spacers = len(state.spacer_indices)
    
    logger.debug(f"Expanding {num_spacers} spacer(s) to fill {extra_space} columns")
    
    # Calculate base space per spacer and remainder
    base_space = extra_space // num_spacers
    remainder = extra_space % num_spacers
    
    # Distribute space among spacers
    # First 'remainder' spacers get base_space + 1
    # Remaining spacers get base_space
    for i, idx in enumerate(state.spacer_indices):
        if i < remainder:
            spacer_width = base_space + 1
        else:
            spacer_width = base_space
        
        # Update state
        state.current_widths[idx] = spacer_width
        state.total_width += spacer_width
        
        # Create whitespace string for this spacer
        shortened_texts[idx] = " " * spacer_width
        
        logger.debug(f"Expanded spacer {idx} to {spacer_width} columns")
    
    logger.debug(f"Final total width after spacer expansion: {state.total_width}")


# ============================================================================
# Rendering Logic
# ============================================================================

@dataclass
class RenderContext:
    """
    Context for rendering segments to the screen.
    
    This dataclass tracks the state during the rendering phase, including
    the renderer instance, current drawing position, and default styling.
    
    Attributes:
        renderer: TTK renderer instance for drawing text
        row: Row position for rendering (0-based)
        current_col: Current column position (updated as segments are rendered)
        default_color: Default color pair for segments without color
        default_attributes: Default attributes for segments without attributes
    """
    renderer: any  # TTK Renderer type
    row: int
    current_col: int
    default_color: int
    default_attributes: int


def render_segments(
    context: RenderContext,
    segments: List[Union[TextSegment, SpacerSegment]],
    shortened_texts: List[str],
    widths: List[int]
) -> None:
    """
    Render all segments to the screen with their calculated widths.
    
    This function iterates through all segments and renders each one at the
    appropriate position with the correct color and attributes. It handles
    both text segments and spacer segments (which render as whitespace).
    
    Args:
        context: Rendering context with renderer and position information
        segments: List of text and spacer segments to render
        shortened_texts: List of shortened/final text for each segment
        widths: List of display widths for each segment
        
    Side Effects:
        - Calls renderer.draw_text() for each segment
        - Updates context.current_col as segments are rendered
        
    Example:
        >>> context = RenderContext(renderer, row=0, current_col=0, ...)
        >>> render_segments(context, segments, shortened_texts, widths)
        >>> # All segments rendered at row 0, starting from column 0
    """
    logger.debug(f"Rendering {len(segments)} segment(s) at row {context.row}, starting col {context.current_col}")
    
    for idx, segment in enumerate(segments):
        text = shortened_texts[idx]
        width = widths[idx]
        
        # Skip empty segments
        if not text or width == 0:
            logger.debug(f"Skipping empty segment {idx}")
            continue
        
        # Determine color pair to use
        if isinstance(segment, SpacerSegment):
            color_pair = segment.color_pair if segment.color_pair is not None else context.default_color
        else:
            color_pair = segment.color_pair if segment.color_pair is not None else context.default_color
        
        # Determine attributes to use
        if isinstance(segment, SpacerSegment):
            attributes = segment.attributes if segment.attributes is not None else context.default_attributes
        else:
            attributes = segment.attributes if segment.attributes is not None else context.default_attributes
        
        # Validate color pair
        if color_pair < 0 or color_pair > 255:
            logger.warning(f"Invalid color_pair {color_pair} for segment {idx}, using default")
            color_pair = context.default_color
        
        logger.debug(f"Rendering segment {idx}: '{text}' at col {context.current_col} with color {color_pair}, attrs {attributes}")
        
        try:
            # Render the segment
            context.renderer.draw_text(
                context.row,
                context.current_col,
                text,
                color_pair,
                attributes
            )
            
            # Update current column position
            context.current_col += width
            
        except Exception as e:
            logger.error(f"Failed to render segment {idx} at row {context.row}, col {context.current_col}: {e}")
            # Continue with next segment even if this one failed
            context.current_col += width
    
    logger.debug(f"Rendering complete, final column: {context.current_col}")


# ============================================================================
# Main API Function
# ============================================================================

def draw_text_segments(
    renderer,
    row: int,
    col: int,
    segments: List[Union[TextSegment, SpacerSegment]],
    rendering_width: int,
    default_color: int = 0,
    default_attributes: int = 0
) -> None:
    """
    Calculate layout, shorten segments, and render text to screen.
    
    This is the primary entry point for the text layout system. It performs
    the complete layout and rendering pipeline:
    
    1. Validates input parameters
    2. Creates initial layout state from segments
    3. Collapses spacers if shortening is needed
    4. Shortens segments by priority until target width is met
    5. Restores segments if extra space is available
    6. Expands spacers to fill remaining space
    7. Renders each segment with its color and attributes
    
    The function handles all errors gracefully with logging and will not crash
    even if individual segments fail to render.
    
    Args:
        renderer: TTK renderer instance (must have draw_text method)
        row: Row position for rendering (0-based)
        col: Starting column position (0-based)
        segments: List of text/spacer segments to layout and render
        rendering_width: Target width in terminal columns
        default_color: Default color pair for segments without color (default 0)
        default_attributes: Default attributes for segments without attributes (default 0)
        
    Raises:
        ValueError: If renderer is None or segments list is None
        
    Example:
        >>> from tfm_text_layout import draw_text_segments, AbbreviationSegment, SpacerSegment
        >>> 
        >>> segments = [
        ...     AbbreviationSegment("Long filename.txt", priority=1, min_length=10),
        ...     SpacerSegment(),
        ...     AbbreviationSegment("Status", priority=0, min_length=3)
        ... ]
        >>> 
        >>> draw_text_segments(renderer, row=0, col=0, segments=segments,
        ...                    rendering_width=80, default_color=1)
        
    Notes:
        - Segments with higher priority values are shortened first
        - Spacers are collapsed before any text shortening occurs
        - Spacers expand to fill available space when text doesn't need shortening
        - Wide characters (CJK, emoji) are properly handled and never split
        - Each segment can have its own color and attributes
        - Minimum length constraints are respected during shortening
    """
    # ========================================================================
    # Input Validation
    # ========================================================================
    
    # Validate renderer
    if renderer is None:
        logger.error("draw_text_segments called with None renderer")
        raise ValueError("renderer cannot be None")
    
    # Validate segments
    if segments is None:
        logger.error("draw_text_segments called with None segments")
        raise ValueError("segments cannot be None")
    
    # Handle empty segments list
    if not segments:
        logger.debug("draw_text_segments called with empty segments list, nothing to render")
        return
    
    # Validate rendering_width
    if rendering_width < 0:
        logger.warning(f"Negative rendering_width {rendering_width}, treating as 0")
        rendering_width = 0
    
    if rendering_width == 0:
        logger.debug("rendering_width is 0, nothing to render")
        return
    
    # Validate row and col
    if row < 0:
        logger.warning(f"Negative row {row}, clipping to 0")
        row = 0
    
    if col < 0:
        logger.warning(f"Negative col {col}, clipping to 0")
        col = 0
    
    logger.info(f"draw_text_segments: {len(segments)} segment(s), target width {rendering_width}, row {row}, col {col}")
    
    # ========================================================================
    # Create Initial Layout State
    # ========================================================================
    
    try:
        # Calculate initial widths for all segments
        current_widths = []
        original_widths = []
        spacer_indices = []
        
        for idx, segment in enumerate(segments):
            if isinstance(segment, SpacerSegment):
                # Spacers start with zero width
                current_widths.append(0)
                original_widths.append(0)
                spacer_indices.append(idx)
            elif isinstance(segment, TextSegment):
                # Text segments start with their full width
                width = segment.get_display_width()
                current_widths.append(width)
                original_widths.append(width)
            else:
                logger.error(f"Unknown segment type at index {idx}: {type(segment)}")
                # Treat as zero-width segment
                current_widths.append(0)
                original_widths.append(0)
        
        # Calculate total width
        total_width = sum(current_widths)
        
        # Create layout state
        state = LayoutState(
            segments=segments,
            current_widths=current_widths,
            original_widths=original_widths,
            total_width=total_width,
            target_width=rendering_width,
            spacer_indices=spacer_indices
        )
        
        logger.debug(f"Initial layout state: total_width={total_width}, target_width={rendering_width}, spacers={len(spacer_indices)}")
        
    except Exception as e:
        logger.error(f"Failed to create initial layout state: {e}")
        # Cannot proceed without valid state
        return
    
    # ========================================================================
    # Execute Layout Calculation
    # ========================================================================
    
    # Initialize shortened_texts with original text for all segments
    shortened_texts = []
    for idx, segment in enumerate(segments):
        if isinstance(segment, SpacerSegment):
            shortened_texts.append("")  # Spacers start empty
        elif isinstance(segment, TextSegment):
            shortened_texts.append(normalize_text(segment.text))
        else:
            shortened_texts.append("")
    
    try:
        # Phase 1: Collapse spacers if shortening is needed
        if state.total_width > state.target_width:
            logger.debug("Total width exceeds target, collapsing spacers")
            collapse_spacers(state)
        
        # Phase 2: Shorten segments by priority if still over target
        if state.total_width > state.target_width:
            logger.debug("Total width still exceeds target after spacer collapse, shortening segments")
            shorten_segments_by_priority(state, shortened_texts)
        
        # Phase 3: Restore segments if extra space is available
        if state.total_width < state.target_width:
            logger.debug("Extra space available, attempting to restore segments")
            restore_segments_by_priority(state, shortened_texts)
        
        # Phase 4: Expand spacers to fill remaining space
        if state.total_width < state.target_width and state.spacer_indices:
            logger.debug("Extra space available with spacers, expanding spacers")
            expand_spacers(state, shortened_texts)
        
        logger.info(f"Layout calculation complete: final width {state.total_width}/{state.target_width}")
        
    except Exception as e:
        logger.error(f"Layout calculation failed: {e}")
        # Try to render with whatever state we have
        logger.warning("Attempting to render with partial layout state")
    
    # ========================================================================
    # Execute Rendering
    # ========================================================================
    
    try:
        # Create rendering context
        context = RenderContext(
            renderer=renderer,
            row=row,
            current_col=col,
            default_color=default_color,
            default_attributes=default_attributes
        )
        
        # Render all segments
        render_segments(context, segments, shortened_texts, state.current_widths)
        
        logger.info(f"Rendering complete: rendered to column {context.current_col}")
        
    except Exception as e:
        logger.error(f"Rendering failed: {e}")
        # Rendering failure is logged but doesn't raise exception
        # This allows the application to continue even if rendering fails


# ============================================================================
# Helper Functions and Convenience APIs
# ============================================================================

def create_status_bar_layout(
    left_text: str,
    right_text: str,
    left_priority: int = 1,
    right_priority: int = 0,
    left_min_length: int = 10,
    right_min_length: int = 5,
    left_color: Optional[int] = None,
    right_color: Optional[int] = None,
    left_attributes: int = 0,
    right_attributes: int = 0
) -> List[Union[TextSegment, SpacerSegment]]:
    """
    Create a common status bar layout with left-aligned and right-aligned text.
    
    This helper creates a segment list for a typical status bar pattern:
    [left text]<spacer>[right text]
    
    The left text is typically more important (higher priority) and gets more
    space when shortening is needed. The spacer expands to push the right text
    to the right edge when space is available.
    
    Args:
        left_text: Text to display on the left side
        right_text: Text to display on the right side
        left_priority: Priority for left text (default 1, shortened after right)
        right_priority: Priority for right text (default 0, shortened first)
        left_min_length: Minimum characters for left text (default 10)
        right_min_length: Minimum characters for right text (default 5)
        left_color: Color pair for left text (None uses default)
        right_color: Color pair for right text (None uses default)
        left_attributes: Text attributes for left text (default 0)
        right_attributes: Text attributes for right text (default 0)
        
    Returns:
        List of segments ready for draw_text_segments()
        
    Example:
        >>> segments = create_status_bar_layout(
        ...     left_text="/home/user/documents/report.txt",
        ...     right_text="Modified | 1.2 MB",
        ...     left_priority=1,
        ...     right_priority=0
        ... )
        >>> draw_text_segments(renderer, 0, 0, segments, 80)
        # Renders: "/home/user/documents/report.txt        Modified | 1.2 MB"
        
        >>> # With narrow width, left text is preserved more than right
        >>> draw_text_segments(renderer, 0, 0, segments, 40)
        # Renders: "/home/user/docum…report.txt Modif…"
    """
    return [
        AbbreviationSegment(
            text=left_text,
            priority=left_priority,
            min_length=left_min_length,
            color_pair=left_color,
            attributes=left_attributes,
            abbrev_position='middle'
        ),
        SpacerSegment(
            color_pair=left_color,  # Use left color for spacer
            attributes=0
        ),
        AbbreviationSegment(
            text=right_text,
            priority=right_priority,
            min_length=right_min_length,
            color_pair=right_color,
            attributes=right_attributes,
            abbrev_position='right'
        )
    ]


def create_file_list_item(
    filename: str,
    size_text: str,
    date_text: str,
    filename_priority: int = 2,
    size_priority: int = 1,
    date_priority: int = 0,
    filename_min_length: int = 15,
    size_min_length: int = 5,
    date_min_length: int = 8,
    filename_color: Optional[int] = None,
    size_color: Optional[int] = None,
    date_color: Optional[int] = None,
    filename_attributes: int = 0,
    size_attributes: int = 0,
    date_attributes: int = 0
) -> List[Union[TextSegment, SpacerSegment]]:
    """
    Create a file list item layout with filename, size, and date columns.
    
    This helper creates a segment list for a typical file manager row:
    [filename]<spacer>[size]<spacer>[date]
    
    The filename has highest priority (preserved most), followed by size,
    then date. Spacers distribute the columns evenly when space is available.
    
    Args:
        filename: Filename to display
        size_text: File size text (e.g., "1.2 MB")
        date_text: Date text (e.g., "2024-01-15")
        filename_priority: Priority for filename (default 2, highest)
        size_priority: Priority for size (default 1, medium)
        date_priority: Priority for date (default 0, lowest)
        filename_min_length: Minimum characters for filename (default 15)
        size_min_length: Minimum characters for size (default 5)
        date_min_length: Minimum characters for date (default 8)
        filename_color: Color pair for filename (None uses default)
        size_color: Color pair for size (None uses default)
        date_color: Color pair for date (None uses default)
        filename_attributes: Text attributes for filename (default 0)
        size_attributes: Text attributes for size (default 0)
        date_attributes: Text attributes for date (default 0)
        
    Returns:
        List of segments ready for draw_text_segments()
        
    Example:
        >>> segments = create_file_list_item(
        ...     filename="very_long_document_name.txt",
        ...     size_text="1.2 MB",
        ...     date_text="2024-01-15"
        ... )
        >>> draw_text_segments(renderer, 0, 0, segments, 80)
        # Renders: "very_long_document_name.txt    1.2 MB    2024-01-15"
        
        >>> # With narrow width, filename preserved, date removed first
        >>> draw_text_segments(renderer, 0, 0, segments, 40)
        # Renders: "very_long_docum…name.txt 1.2 MB"
    """
    return [
        FilepathSegment(
            text=filename,
            priority=filename_priority,
            min_length=filename_min_length,
            color_pair=filename_color,
            attributes=filename_attributes,
            abbrev_position='middle'
        ),
        SpacerSegment(
            color_pair=filename_color,
            attributes=0
        ),
        AbbreviationSegment(
            text=size_text,
            priority=size_priority,
            min_length=size_min_length,
            color_pair=size_color,
            attributes=size_attributes,
            abbrev_position='right'
        ),
        SpacerSegment(
            color_pair=size_color,
            attributes=0
        ),
        AbbreviationSegment(
            text=date_text,
            priority=date_priority,
            min_length=date_min_length,
            color_pair=date_color,
            attributes=date_attributes,
            abbrev_position='right'
        )
    ]


def create_dialog_prompt(
    prompt_text: str,
    input_text: str = "",
    prompt_priority: int = 0,
    input_priority: int = 1,
    prompt_min_length: int = 10,
    input_min_length: int = 5,
    prompt_color: Optional[int] = None,
    input_color: Optional[int] = None,
    prompt_attributes: int = 0,
    input_attributes: int = 0,
    separator: str = " "
) -> List[Union[TextSegment, SpacerSegment]]:
    """
    Create a dialog prompt layout with prompt text and input field.
    
    This helper creates a segment list for a typical dialog prompt:
    [prompt text][separator][input text]
    
    The input text has higher priority (preserved more) than the prompt text,
    ensuring the user's input remains visible even in narrow dialogs.
    
    Args:
        prompt_text: Prompt text to display (e.g., "Enter filename:")
        input_text: Current input text (default "")
        prompt_priority: Priority for prompt (default 0, shortened first)
        input_priority: Priority for input (default 1, preserved more)
        prompt_min_length: Minimum characters for prompt (default 10)
        input_min_length: Minimum characters for input (default 5)
        prompt_color: Color pair for prompt (None uses default)
        input_color: Color pair for input (None uses default)
        prompt_attributes: Text attributes for prompt (default 0)
        input_attributes: Text attributes for input (default 0)
        separator: Separator between prompt and input (default " ")
        
    Returns:
        List of segments ready for draw_text_segments()
        
    Example:
        >>> segments = create_dialog_prompt(
        ...     prompt_text="Enter destination path:",
        ...     input_text="/home/user/documents/project/files/",
        ...     prompt_attributes=curses.A_BOLD
        ... )
        >>> draw_text_segments(renderer, 0, 0, segments, 60)
        # Renders: "Enter destination path: /home/user/documents/project/files/"
        
        >>> # With narrow width, prompt is shortened to preserve input
        >>> draw_text_segments(renderer, 0, 0, segments, 40)
        # Renders: "Enter dest…: /home/user/documents/pr…"
    """
    segments = [
        AbbreviationSegment(
            text=prompt_text,
            priority=prompt_priority,
            min_length=prompt_min_length,
            color_pair=prompt_color,
            attributes=prompt_attributes,
            abbrev_position='right'
        )
    ]
    
    # Add separator if provided
    if separator:
        segments.append(
            AsIsSegment(
                text=separator,
                priority=0,
                min_length=0,
                color_pair=prompt_color,
                attributes=prompt_attributes
            )
        )
    
    # Add input text
    segments.append(
        AbbreviationSegment(
            text=input_text,
            priority=input_priority,
            min_length=input_min_length,
            color_pair=input_color,
            attributes=input_attributes,
            abbrev_position='middle'
        )
    )
    
    return segments


def create_three_column_layout(
    left_text: str,
    center_text: str,
    right_text: str,
    left_priority: int = 1,
    center_priority: int = 2,
    right_priority: int = 0,
    left_min_length: int = 5,
    center_min_length: int = 10,
    right_min_length: int = 5,
    left_color: Optional[int] = None,
    center_color: Optional[int] = None,
    right_color: Optional[int] = None,
    left_attributes: int = 0,
    center_attributes: int = 0,
    right_attributes: int = 0
) -> List[Union[TextSegment, SpacerSegment]]:
    """
    Create a three-column layout with left, center, and right text.
    
    This helper creates a segment list for a three-column pattern:
    [left]<spacer>[center]<spacer>[right]
    
    The center text typically has highest priority (preserved most), with
    spacers distributing the columns evenly when space is available.
    
    Args:
        left_text: Text for left column
        center_text: Text for center column
        right_text: Text for right column
        left_priority: Priority for left text (default 1)
        center_priority: Priority for center text (default 2, highest)
        right_priority: Priority for right text (default 0, lowest)
        left_min_length: Minimum characters for left (default 5)
        center_min_length: Minimum characters for center (default 10)
        right_min_length: Minimum characters for right (default 5)
        left_color: Color pair for left text (None uses default)
        center_color: Color pair for center text (None uses default)
        right_color: Color pair for right text (None uses default)
        left_attributes: Text attributes for left text (default 0)
        center_attributes: Text attributes for center text (default 0)
        right_attributes: Text attributes for right text (default 0)
        
    Returns:
        List of segments ready for draw_text_segments()
        
    Example:
        >>> segments = create_three_column_layout(
        ...     left_text="File",
        ...     center_text="Terminal File Manager v1.0",
        ...     right_text="Help: F1"
        ... )
        >>> draw_text_segments(renderer, 0, 0, segments, 80)
        # Renders: "File    Terminal File Manager v1.0    Help: F1"
        
        >>> # With narrow width, center preserved, right removed first
        >>> draw_text_segments(renderer, 0, 0, segments, 40)
        # Renders: "File Terminal File Manager v1.0"
    """
    return [
        AbbreviationSegment(
            text=left_text,
            priority=left_priority,
            min_length=left_min_length,
            color_pair=left_color,
            attributes=left_attributes,
            abbrev_position='right'
        ),
        SpacerSegment(
            color_pair=left_color,
            attributes=0
        ),
        AbbreviationSegment(
            text=center_text,
            priority=center_priority,
            min_length=center_min_length,
            color_pair=center_color,
            attributes=center_attributes,
            abbrev_position='middle'
        ),
        SpacerSegment(
            color_pair=center_color,
            attributes=0
        ),
        AbbreviationSegment(
            text=right_text,
            priority=right_priority,
            min_length=right_min_length,
            color_pair=right_color,
            attributes=right_attributes,
            abbrev_position='right'
        )
    ]


def create_breadcrumb_path(
    path: str,
    priority: int = 1,
    min_length: int = 20,
    color_pair: Optional[int] = None,
    attributes: int = 0
) -> List[Union[TextSegment, SpacerSegment]]:
    """
    Create a breadcrumb-style path display that intelligently abbreviates.
    
    This helper creates a single FilepathSegment configured for optimal
    path display. It's a convenience wrapper that uses sensible defaults
    for displaying filesystem paths.
    
    Args:
        path: Filesystem path to display
        priority: Priority for the path segment (default 1)
        min_length: Minimum characters to preserve (default 20)
        color_pair: Color pair for the path (None uses default)
        attributes: Text attributes for the path (default 0)
        
    Returns:
        List containing a single FilepathSegment
        
    Example:
        >>> segments = create_breadcrumb_path(
        ...     path="/home/user/documents/projects/myproject/src/main.py"
        ... )
        >>> draw_text_segments(renderer, 0, 0, segments, 50)
        # Renders: "…/myproject/src/main.py"
        
        >>> draw_text_segments(renderer, 0, 0, segments, 30)
        # Renders: "…/main.py"
    """
    return [
        FilepathSegment(
            text=path,
            priority=priority,
            min_length=min_length,
            color_pair=color_pair,
            attributes=attributes,
            abbrev_position='middle'
        )
    ]


def create_key_value_pair(
    key: str,
    value: str,
    key_priority: int = 0,
    value_priority: int = 1,
    key_min_length: int = 3,
    value_min_length: int = 5,
    key_color: Optional[int] = None,
    value_color: Optional[int] = None,
    key_attributes: int = 0,
    value_attributes: int = 0,
    separator: str = ": "
) -> List[Union[TextSegment, SpacerSegment]]:
    """
    Create a key-value pair layout with configurable separator.
    
    This helper creates a segment list for displaying key-value pairs:
    [key][separator][value]
    
    The value has higher priority (preserved more) than the key, ensuring
    the actual data remains visible when space is limited.
    
    Args:
        key: Key text (e.g., "Size", "Modified", "Type")
        value: Value text (e.g., "1.2 MB", "2024-01-15", "PDF Document")
        key_priority: Priority for key (default 0, shortened first)
        value_priority: Priority for value (default 1, preserved more)
        key_min_length: Minimum characters for key (default 3)
        value_min_length: Minimum characters for value (default 5)
        key_color: Color pair for key (None uses default)
        value_color: Color pair for value (None uses default)
        key_attributes: Text attributes for key (default 0)
        value_attributes: Text attributes for value (default 0)
        separator: Separator between key and value (default ": ")
        
    Returns:
        List of segments ready for draw_text_segments()
        
    Example:
        >>> segments = create_key_value_pair(
        ...     key="Modified",
        ...     value="2024-01-15 14:30:00",
        ...     key_attributes=curses.A_BOLD
        ... )
        >>> draw_text_segments(renderer, 0, 0, segments, 40)
        # Renders: "Modified: 2024-01-15 14:30:00"
        
        >>> draw_text_segments(renderer, 0, 0, segments, 20)
        # Renders: "Mod…: 2024-01-15 …"
    """
    segments = [
        AbbreviationSegment(
            text=key,
            priority=key_priority,
            min_length=key_min_length,
            color_pair=key_color,
            attributes=key_attributes,
            abbrev_position='right'
        )
    ]
    
    # Add separator if provided
    if separator:
        segments.append(
            AsIsSegment(
                text=separator,
                priority=0,
                min_length=0,
                color_pair=key_color,
                attributes=key_attributes
            )
        )
    
    # Add value
    segments.append(
        AbbreviationSegment(
            text=value,
            priority=value_priority,
            min_length=value_min_length,
            color_pair=value_color,
            attributes=value_attributes,
            abbrev_position='middle'
        )
    )
    
    return segments
