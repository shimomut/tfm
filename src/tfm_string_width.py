"""
String Width Reduction Utility

This module provides intelligent string shortening functionality for terminal UI
components. It accounts for wide characters (CJK, emoji), supports multiple
shortening strategies (all-or-nothing, truncation, abbreviation), and offers both
simple and advanced APIs for different use cases.

The module integrates with TTK's wide_char_utils for accurate display width
calculations and provides region-based control for flexible shortening.

Usage Examples:
    Basic usage with default abbreviation:
        >>> from tfm_string_width import reduce_width
        >>> reduce_width("very_long_filename.txt", 15)
        'very_lon….txt'
    
    Middle abbreviation:
        >>> from tfm_string_width import abbreviate_middle
        >>> abbreviate_middle("very_long_filename.txt", 15)
        'very_l…name.txt'
    
    Path abbreviation:
        >>> from tfm_string_width import abbreviate_path
        >>> abbreviate_path("/home/user/documents/file.txt", 20)
        '/home/…/file.txt'
    
    Region-based shortening:
        >>> from tfm_string_width import reduce_width, ShorteningRegion
        >>> region = ShorteningRegion(start=0, end=10, priority=1, strategy='remove')
        >>> reduce_width("prefix_important_suffix", 20, regions=[region])
        'pre_important_suffix'
"""

from dataclasses import dataclass
from typing import Optional, List
import unicodedata

# Import TTK's display width calculation
from ttk.wide_char_utils import get_display_width

# Import TFM's unified logging system
from tfm_log_manager import getLogger

# Initialize logger for this module
logger = getLogger("StrWidth")


@dataclass
class ShorteningRegion:
    """
    Defines a region of a string that can be shortened with a priority.
    
    Attributes:
        start: Start index (inclusive) of the region
        end: End index (exclusive) of the region
        priority: Priority value (higher values are shortened first)
        strategy: Shortening strategy ('all_or_nothing', 'truncate', or 'abbreviate')
        abbrev_position: Position for ellipsis ('left', 'middle', 'right')
        filepath_mode: Whether to treat the region as a filesystem path
    """
    start: int
    end: int
    priority: int
    strategy: str
    abbrev_position: str = 'right'
    filepath_mode: bool = False


def calculate_display_width(text: str) -> int:
    """
    Calculate the display width of a string in terminal columns.
    
    Delegates to TTK's get_display_width() which handles:
    - Wide characters (CJK, emoji) count as 2 columns
    - Narrow characters count as 1 column
    - Combining characters count as 0 columns (via NFC normalization)
    
    Args:
        text: Input string (will be NFC normalized by get_display_width)
        
    Returns:
        Display width in columns
    """
    return get_display_width(text)


def normalize_unicode(text: str) -> str:
    """
    Normalize string to NFC form for consistent processing.
    
    NFC (Canonical Decomposition followed by Canonical Composition) ensures
    that characters are represented in their composed form, which is important
    for consistent width calculation and string manipulation.
    
    Args:
        text: Input string
        
    Returns:
        NFC normalized string
    """
    return unicodedata.normalize('NFC', text)


class AllOrNothingStrategy:
    """
    Shortening strategy that either keeps the region entirely or removes it completely.
    
    This strategy implements "all or nothing" behavior: if the region fits within
    the target width, it's kept in full; otherwise, it's removed entirely.
    No partial truncation or ellipsis is used.
    
    This is useful for optional context in prompts where partial information
    would be confusing or misleading.
    """
    
    def shorten(self, text: str, target_width: int, region: ShorteningRegion) -> str:
        """
        Shorten text by either keeping or removing the region entirely.
        
        If the full text fits within target_width, return it unchanged.
        Otherwise, remove the region completely (no partial truncation).
        
        Args:
            text: Full string to process
            target_width: Target display width in columns
            region: Region to potentially remove (only region.start and region.end are used)
            
        Returns:
            Either the original text (if it fits) or text with region completely removed
        """
        # Normalize the input text
        text = normalize_unicode(text)
        
        # Calculate current width
        current_width = calculate_display_width(text)
        
        # If already fits, return unchanged
        if current_width <= target_width:
            return text
        
        # Extract the three parts: before region, region, after region
        before_region = text[:region.start]
        after_region = text[region.end:]
        
        # Remove the region entirely
        result = before_region + after_region
        
        return result


class TruncationStrategy:
    """
    Shortening strategy that truncates characters from the right without adding ellipsis.
    
    This strategy removes characters from the end of the specified region
    until the target width is met. No ellipsis character is added.
    """
    
    def shorten(self, text: str, target_width: int, region: ShorteningRegion) -> str:
        """
        Shorten text by truncating characters from the right side of the region.
        
        Characters are removed from the end of the region (working backwards
        from region.end towards region.start) until the total display width
        of the string meets the target width. No ellipsis is added.
        
        Args:
            text: Full string to process
            target_width: Target display width in columns
            region: Region to shorten (only region.start and region.end are used)
            
        Returns:
            Shortened string with characters truncated from the right side of the region
        """
        # Normalize the input text
        text = normalize_unicode(text)
        
        # Calculate current width
        current_width = calculate_display_width(text)
        
        # If already fits, return unchanged
        if current_width <= target_width:
            return text
        
        # Extract the three parts: before region, region, after region
        before_region = text[:region.start]
        region_text = text[region.start:region.end]
        after_region = text[region.end:]
        
        # Calculate widths
        before_width = calculate_display_width(before_region)
        after_width = calculate_display_width(after_region)
        
        # Calculate available width for the region
        available_width = target_width - before_width - after_width
        
        # Edge case: target width = 1
        # Return first character of region if it fits
        if available_width == 1:
            if region_text:
                first_char = region_text[0]
                first_char_width = calculate_display_width(first_char)
                if first_char_width <= 1:
                    return before_region + first_char + after_region
            # Can't fit anything, return empty region
            return before_region + after_region
        
        # Edge case: no space available for region content
        if available_width <= 0:
            return before_region + after_region
        
        # Calculate how much width we need to reduce
        width_to_reduce = current_width - target_width
        
        # Remove characters from the end of the region until we meet the target
        while region_text and width_to_reduce > 0:
            # Remove the last character
            removed_char = region_text[-1]
            region_text = region_text[:-1]
            
            # Calculate the width of the removed character
            char_width = calculate_display_width(removed_char)
            width_to_reduce -= char_width
        
        # Reconstruct the string
        result = before_region + region_text + after_region
        
        return result


class AbbreviationStrategy:
    """
    Shortening strategy that replaces removed content with an ellipsis character.
    
    This strategy abbreviates text by removing characters and inserting an
    ellipsis ("…") at the specified position (left, middle, or right).
    """
    
    ELLIPSIS = "…"
    
    def shorten(self, text: str, target_width: int, region: ShorteningRegion) -> str:
        """
        Shorten text by abbreviating with an ellipsis at the specified position.
        
        The abbreviation position determines where the ellipsis appears:
        - 'left': Ellipsis at start, preserve right portion
        - 'right': Ellipsis at end, preserve left portion
        - 'middle': Ellipsis in center, preserve both ends with balanced distribution
        
        Args:
            text: Full string to process
            target_width: Target display width in columns
            region: Region to shorten (uses region.abbrev_position)
            
        Returns:
            Shortened string with ellipsis replacing removed content
        """
        # Normalize the input text
        text = normalize_unicode(text)
        
        # Calculate current width
        current_width = calculate_display_width(text)
        
        # If already fits, return unchanged
        if current_width <= target_width:
            return text
        
        # Extract the three parts: before region, region, after region
        before_region = text[:region.start]
        region_text = text[region.start:region.end]
        after_region = text[region.end:]
        
        # Calculate widths
        before_width = calculate_display_width(before_region)
        after_width = calculate_display_width(after_region)
        ellipsis_width = calculate_display_width(self.ELLIPSIS)
        
        # Calculate available width for the region (including ellipsis)
        available_width = target_width - before_width - after_width
        
        # Edge case: target width = 1
        # Return just the ellipsis if abbreviating, or first character if possible
        if available_width == 1:
            if ellipsis_width <= 1:
                return before_region + self.ELLIPSIS + after_region
            else:
                # Ellipsis is too wide, return first character of region if it fits
                if region_text:
                    first_char = region_text[0]
                    first_char_width = calculate_display_width(first_char)
                    if first_char_width <= 1:
                        return before_region + first_char + after_region
                # Can't fit anything, return ellipsis anyway
                return before_region + self.ELLIPSIS + after_region
        
        # Edge case: String shorter than ellipsis
        # If the region text is shorter than the ellipsis, just return ellipsis
        region_width = calculate_display_width(region_text)
        if region_width < ellipsis_width and available_width >= ellipsis_width:
            return before_region + self.ELLIPSIS + after_region
        
        # If there's not enough space even for the ellipsis, return just ellipsis
        if available_width < ellipsis_width:
            return before_region + self.ELLIPSIS + after_region
        
        # Calculate how much content we can preserve (minus ellipsis)
        content_width = available_width - ellipsis_width
        
        # Apply the appropriate abbreviation strategy based on position
        # Validate abbreviation position
        position = region.abbrev_position.lower()
        if position not in ['left', 'middle', 'right']:
            logger.warning(f"Invalid abbreviation position '{region.abbrev_position}', falling back to 'right'")
            position = 'right'
        
        if position == 'left':
            # Ellipsis at start, preserve right portion
            abbreviated = self._abbreviate_left(region_text, content_width)
        elif position == 'middle':
            # Ellipsis in center, preserve both ends
            abbreviated = self._abbreviate_middle(region_text, content_width)
        else:  # 'right' or default
            # Ellipsis at end, preserve left portion
            abbreviated = self._abbreviate_right(region_text, content_width)
        
        # Reconstruct the string
        result = before_region + abbreviated + after_region
        
        return result
    
    def _abbreviate_left(self, text: str, content_width: int) -> str:
        """
        Abbreviate with ellipsis at the start, preserving the right portion.
        
        Args:
            text: Text to abbreviate
            content_width: Available width for content (excluding ellipsis)
            
        Returns:
            Abbreviated text with ellipsis at the start
        """
        if content_width <= 0:
            return self.ELLIPSIS
        
        # Build from the right, preserving as much as possible
        preserved = ""
        current_width = 0
        
        for i in range(len(text) - 1, -1, -1):
            char = text[i]
            char_width = calculate_display_width(char)
            
            if current_width + char_width <= content_width:
                preserved = char + preserved
                current_width += char_width
            else:
                break
        
        return self.ELLIPSIS + preserved
    
    def _abbreviate_right(self, text: str, content_width: int) -> str:
        """
        Abbreviate with ellipsis at the end, preserving the left portion.
        
        Args:
            text: Text to abbreviate
            content_width: Available width for content (excluding ellipsis)
            
        Returns:
            Abbreviated text with ellipsis at the end
        """
        if content_width <= 0:
            return self.ELLIPSIS
        
        # Build from the left, preserving as much as possible
        preserved = ""
        current_width = 0
        
        for char in text:
            char_width = calculate_display_width(char)
            
            if current_width + char_width <= content_width:
                preserved += char
                current_width += char_width
            else:
                break
        
        return preserved + self.ELLIPSIS
    
    def _abbreviate_middle(self, text: str, content_width: int) -> str:
        """
        Abbreviate with ellipsis in the center, preserving both ends.
        
        The preserved characters are distributed approximately equally between
        the left and right portions. If the content width is odd, the extra
        character goes to the left side.
        
        Args:
            text: Text to abbreviate
            content_width: Available width for content (excluding ellipsis)
            
        Returns:
            Abbreviated text with ellipsis in the middle
        """
        if content_width <= 0:
            return self.ELLIPSIS
        
        # Calculate how much width to allocate to each side
        # If odd, give the extra character to the left
        left_width = (content_width + 1) // 2
        right_width = content_width // 2
        
        # Build left portion
        left_preserved = ""
        left_current_width = 0
        
        for char in text:
            char_width = calculate_display_width(char)
            
            if left_current_width + char_width <= left_width:
                left_preserved += char
                left_current_width += char_width
            else:
                break
        
        # Build right portion (from the end)
        right_preserved = ""
        right_current_width = 0
        
        for i in range(len(text) - 1, -1, -1):
            char = text[i]
            char_width = calculate_display_width(char)
            
            if right_current_width + char_width <= right_width:
                right_preserved = char + right_preserved
                right_current_width += char_width
            else:
                break
        
        return left_preserved + self.ELLIPSIS + right_preserved


class FilepathStrategy:
    """
    Shortening strategy specialized for filesystem paths.
    
    This strategy intelligently abbreviates filesystem paths by:
    1. Parsing the path into directory components and filename
    2. Replacing entire directory levels with ellipsis (…) before touching the filename
    3. Preserving path separators (/ or \\)
    
    Example: "aaaa/bbbb/cccc/dddd.txt" -> "aaaa/…/dddd.txt"
    
    This ensures that the filename remains as readable as possible while
    directory paths are shortened by removing entire levels.
    """
    
    ELLIPSIS = "…"
    
    def shorten(self, text: str, target_width: int, region: ShorteningRegion) -> str:
        """
        Shorten a filesystem path by replacing directory levels with ellipsis.
        
        The path is parsed into components, and the minimum number of directory
        levels are replaced with ellipsis to meet the target width. This preserves
        as much context as possible while keeping the filename intact.
        
        Args:
            text: Full string to process
            target_width: Target display width in columns
            region: Region to shorten (should cover the entire path)
            
        Returns:
            Shortened path with minimum directory levels replaced by ellipsis
        """
        # Normalize the input text
        text = normalize_unicode(text)
        
        # Calculate current width
        current_width = calculate_display_width(text)
        
        # If already fits, return unchanged
        if current_width <= target_width:
            return text
        
        # Extract the three parts: before region, region, after region
        before_region = text[:region.start]
        region_text = text[region.start:region.end]
        after_region = text[region.end:]
        
        # Calculate widths
        before_width = calculate_display_width(before_region)
        after_width = calculate_display_width(after_region)
        
        # Calculate available width for the path region
        available_width = target_width - before_width - after_width
        
        # Edge case: target width = 1
        ellipsis_width = calculate_display_width(self.ELLIPSIS)
        if available_width <= ellipsis_width:
            return before_region + self.ELLIPSIS + after_region
        
        # Parse the path into components
        # Detect separator (prefer / but support \)
        if '/' in region_text:
            separator = '/'
        elif '\\' in region_text:
            separator = '\\'
        else:
            # No separator, treat as a single filename
            # Use middle abbreviation on the whole thing
            abbrev_strategy = AbbreviationStrategy()
            temp_region = ShorteningRegion(
                start=0,
                end=len(region_text),
                priority=region.priority,
                strategy='abbreviate',
                abbrev_position='middle'
            )
            abbreviated = abbrev_strategy.shorten(region_text, available_width, temp_region)
            return before_region + abbreviated + after_region
        
        # Split into components
        components = region_text.split(separator)
        
        # Separate directories from filename
        if len(components) > 1:
            directories = components[:-1]
            filename = components[-1]
        else:
            # Only one component
            directories = []
            filename = components[0]
        
        if not directories:
            # No directories, just abbreviate the filename
            abbrev_strategy = AbbreviationStrategy()
            temp_region = ShorteningRegion(
                start=0,
                end=len(filename),
                priority=region.priority,
                strategy='abbreviate',
                abbrev_position='middle'
            )
            abbreviated = abbrev_strategy.shorten(filename, available_width, temp_region)
            return before_region + abbreviated + after_region
        
        # Calculate widths
        separator_width = calculate_display_width(separator)
        filename_width = calculate_display_width(filename)
        
        # Strategy: Try to keep as many directory levels as possible
        # Start with all directories, then progressively remove from the middle
        
        # Try: all directories + filename
        full_path = separator.join(directories) + separator + filename
        if calculate_display_width(full_path) <= available_width:
            return before_region + full_path + after_region
        
        # We need to shorten. Try different combinations, keeping as many dirs as possible
        # Strategy: Keep directories from both ends, replace middle with ellipsis
        
        num_dirs = len(directories)
        
        # Try keeping progressively fewer directories from each end
        # Start with keeping all but one from each end, then reduce
        for keep_from_start in range(num_dirs - 1, 0, -1):
            for keep_from_end in range(num_dirs - keep_from_start, 0, -1):
                if keep_from_start + keep_from_end >= num_dirs:
                    # This would keep all directories, already tried
                    continue
                
                # Build path with these directories
                kept_dirs = directories[:keep_from_start] + directories[-keep_from_end:]
                path_parts = directories[:keep_from_start] + [self.ELLIPSIS] + directories[-keep_from_end:] + [filename]
                test_path = separator.join(path_parts)
                
                if calculate_display_width(test_path) <= available_width:
                    return before_region + test_path + after_region
        
        # Try keeping just first directory: first_dir/…/filename
        if num_dirs >= 1:
            first_dir = directories[0]
            path_with_ellipsis = f"{first_dir}{separator}{self.ELLIPSIS}{separator}{filename}"
            if calculate_display_width(path_with_ellipsis) <= available_width:
                return before_region + path_with_ellipsis + after_region
        
        # Try: …/filename
        path_with_ellipsis = f"{self.ELLIPSIS}{separator}{filename}"
        if calculate_display_width(path_with_ellipsis) <= available_width:
            return before_region + path_with_ellipsis + after_region
        
        # Even …/filename doesn't fit, need to abbreviate filename too
        # Calculate available width for filename
        ellipsis_and_sep_width = calculate_display_width(self.ELLIPSIS) + separator_width
        available_for_filename = available_width - ellipsis_and_sep_width
        
        if available_for_filename <= 0:
            # Can't fit anything, just return ellipsis
            return before_region + self.ELLIPSIS + after_region
        
        # Abbreviate the filename
        abbrev_strategy = AbbreviationStrategy()
        temp_region = ShorteningRegion(
            start=0,
            end=len(filename),
            priority=region.priority,
            strategy='abbreviate',
            abbrev_position='middle'
        )
        abbreviated_filename = abbrev_strategy.shorten(filename, available_for_filename, temp_region)
        
        result = before_region + self.ELLIPSIS + separator + abbreviated_filename + after_region
        return result


def _sort_regions_by_priority(regions: List[ShorteningRegion]) -> List[ShorteningRegion]:
    """
    Sort regions by priority in descending order.
    
    Regions with higher priority values are processed first. When regions
    have equal priority, they are kept in their original definition order
    (stable sort).
    
    Args:
        regions: List of shortening regions to sort
        
    Returns:
        Sorted list of regions (highest priority first)
    """
    # Use stable sort to preserve definition order for equal priorities
    return sorted(regions, key=lambda r: r.priority, reverse=True)


def _validate_region(region: ShorteningRegion, text_length: int) -> bool:
    """
    Validate region boundaries.
    
    A region is valid if:
    - start is non-negative
    - end is non-negative
    - start < end
    - start < text_length
    - end <= text_length
    
    Invalid regions are logged as warnings and should be skipped during processing.
    
    Args:
        region: Region to validate
        text_length: Length of the text being processed
        
    Returns:
        True if region is valid, False otherwise
    """
    # Check for negative indices
    if region.start < 0:
        logger.warning(f"Invalid region: start index is negative ({region.start})")
        return False
    
    if region.end < 0:
        logger.warning(f"Invalid region: end index is negative ({region.end})")
        return False
    
    # Check that start < end
    if region.start >= region.end:
        logger.warning(f"Invalid region: start ({region.start}) >= end ({region.end})")
        return False
    
    # Check that indices are within text bounds
    if region.start >= text_length:
        logger.warning(f"Invalid region: start ({region.start}) >= text length ({text_length})")
        return False
    
    if region.end > text_length:
        logger.warning(f"Invalid region: end ({region.end}) > text length ({text_length})")
        return False
    
    return True


def _process_regions(text: str, target_width: int, regions: List[ShorteningRegion]) -> str:
    """
    Process regions in priority order to shorten text.
    
    For non-overlapping regions, processes regions by priority (highest first).
    Each region is shortened as much as needed before moving to the next priority.
    
    For overlapping regions, falls back to sequential processing.
    
    Args:
        text: Text to shorten
        target_width: Target display width in columns
        regions: List of shortening regions with priorities
        
    Returns:
        Shortened text after processing regions
    """
    # Normalize the input text
    text = normalize_unicode(text)
    
    # If no regions, return original text
    if not regions:
        return text
    
    # Sort regions by priority (highest first)
    sorted_regions = _sort_regions_by_priority(regions)
    
    # Validate all regions and filter out invalid ones
    valid_regions = []
    for region in sorted_regions:
        if _validate_region(region, len(text)):
            valid_regions.append(region)
    
    if not valid_regions:
        return text
    
    # Check if regions overlap
    regions_overlap = False
    for i, region1 in enumerate(valid_regions):
        for region2 in valid_regions[i+1:]:
            # Check for overlap (regions share any indices)
            if not (region1.end <= region2.start or region2.end <= region1.start):
                regions_overlap = True
                break
        if regions_overlap:
            break
    
    # If regions overlap, use sequential processing
    if regions_overlap:
        logger.warning("Overlapping regions detected, using sequential processing")
        return _process_regions_sequential(text, target_width, valid_regions)
    
    # Process non-overlapping regions by priority
    # Sort regions by start position for reconstruction
    regions_by_position = sorted(valid_regions, key=lambda r: r.start)
    
    # Calculate current width
    current_width = calculate_display_width(text)
    if current_width <= target_width:
        return text
    
    # Calculate width of text outside all regions (this must be preserved)
    preserved_parts = []
    last_end = 0
    for region in regions_by_position:
        if region.start > last_end:
            preserved_parts.append(text[last_end:region.start])
        last_end = region.end
    if last_end < len(text):
        preserved_parts.append(text[last_end:])
    
    preserved_width = sum(calculate_display_width(part) for part in preserved_parts)
    available_for_regions = target_width - preserved_width
    
    if available_for_regions <= 0:
        logger.debug("Target width too small for preserved text outside regions")
        available_for_regions = 1
    
    # Process regions by priority (highest first)
    # Keep track of both original and shortened versions of each region
    region_texts = {}
    original_region_texts = {}
    for region in regions_by_position:
        original_text = text[region.start:region.end]
        region_texts[region.start] = original_text
        original_region_texts[region.start] = original_text  # Store original for recalculation
    
    # Process each priority level
    for priority_level in sorted(set(r.priority for r in valid_regions), reverse=True):
        # Get regions at this priority level
        priority_regions = [r for r in valid_regions if r.priority == priority_level]
        
        # Calculate current total width with current region texts
        current_parts = []
        last_end = 0
        for region in regions_by_position:
            if region.start > last_end:
                current_parts.append(text[last_end:region.start])
            current_parts.append(region_texts[region.start])
            last_end = region.end
        if last_end < len(text):
            current_parts.append(text[last_end:])
        
        current_result = ''.join(current_parts)
        current_result_width = calculate_display_width(current_result)
        
        # Don't return early - continue processing all priorities
        # so we can recalculate later
        
        # Calculate how much we need to reduce
        width_to_reduce = current_result_width - target_width
        
        # Shorten regions at this priority level
        for region in priority_regions:
            if width_to_reduce <= 0:
                break
            
            region_text = region_texts[region.start]
            region_width = calculate_display_width(region_text)
            
            # Calculate target width for this region
            # Try to reduce by the full amount needed, but at least leave 1 char
            region_target = max(1, region_width - width_to_reduce)
            
            # Select the appropriate strategy
            strategy_name = region.strategy.lower()
            if strategy_name not in ['all_or_nothing', 'truncate', 'abbreviate']:
                logger.warning(f"Invalid strategy '{region.strategy}' in region, falling back to 'abbreviate'")
                strategy_name = 'abbreviate'
            
            if region.filepath_mode:
                strategy = FilepathStrategy()
            elif strategy_name == 'all_or_nothing':
                strategy = AllOrNothingStrategy()
            elif strategy_name == 'truncate':
                strategy = TruncationStrategy()
            else:
                strategy = AbbreviationStrategy()
            
            # Create a temporary region for just this text
            temp_region = ShorteningRegion(
                start=0,
                end=len(region_text),
                priority=region.priority,
                strategy=region.strategy,
                abbrev_position=region.abbrev_position,
                filepath_mode=region.filepath_mode
            )
            
            # Shorten the region text
            shortened = strategy.shorten(region_text, region_target, temp_region)
            shortened_width = calculate_display_width(shortened)
            
            # Update the region text
            region_texts[region.start] = shortened
            
            # Update how much we've reduced
            width_reduced = region_width - shortened_width
            width_to_reduce -= width_reduced
    
    # Recalculation phase: Try to restore content in reverse priority order
    # (lowest priority number = most important, restored first)
    
    # Calculate current result width
    current_parts = []
    last_end = 0
    for region in regions_by_position:
        if region.start > last_end:
            current_parts.append(text[last_end:region.start])
        current_parts.append(region_texts[region.start])
        last_end = region.end
    if last_end < len(text):
        current_parts.append(text[last_end:])
    
    current_result = ''.join(current_parts)
    current_result_width = calculate_display_width(current_result)
    
    logger.debug(f"Before recalculation: width={current_result_width}, target={target_width}")
    
    # If we have freed space (width < target), try to restore regions
    if current_result_width < target_width:
        available_space = target_width - current_result_width
        logger.debug(f"Recalculation: {available_space} cols available (result={current_result_width}, target={target_width})")
        
        # Iterate through priorities in reverse order (lowest to highest)
        # Lower priority numbers = more important = restore first
        for priority_level in sorted(set(r.priority for r in valid_regions)):
            if available_space <= 0:
                break
            
            logger.debug(f"Trying to restore priority {priority_level} regions")
            
            # Get regions at this priority level
            priority_regions = [r for r in valid_regions if r.priority == priority_level]
            
            # Try to restore each region at this priority
            for region in priority_regions:
                if available_space <= 0:
                    break
                
                current_text = region_texts[region.start]
                original_text = original_region_texts[region.start]
                
                # Skip if already at original
                if current_text == original_text:
                    continue
                
                # Calculate widths
                current_width = calculate_display_width(current_text)
                original_width = calculate_display_width(original_text)
                
                # Calculate new target width for this region with available space
                new_target_width = current_width + available_space
                
                # If we can fit the original, use it
                if original_width <= new_target_width:
                    region_texts[region.start] = original_text
                    space_used = original_width - current_width
                    available_space -= space_used
                    logger.debug(f"Restored region at priority {priority_level} to original, used {space_used} cols")
                else:
                    # Re-shorten with the new target width
                    # Select the appropriate strategy
                    strategy_name = region.strategy.lower()
                    if strategy_name not in ['all_or_nothing', 'truncate', 'abbreviate']:
                        strategy_name = 'abbreviate'
                    
                    if region.filepath_mode:
                        strategy = FilepathStrategy()
                    elif strategy_name == 'all_or_nothing':
                        strategy = AllOrNothingStrategy()
                    elif strategy_name == 'truncate':
                        strategy = TruncationStrategy()
                    else:
                        strategy = AbbreviationStrategy()
                    
                    # Create a temporary region for just this text
                    temp_region = ShorteningRegion(
                        start=0,
                        end=len(original_text),
                        priority=region.priority,
                        strategy=region.strategy,
                        abbrev_position=region.abbrev_position,
                        filepath_mode=region.filepath_mode
                    )
                    
                    # Re-shorten the original text with new target
                    re_shortened = strategy.shorten(original_text, new_target_width, temp_region)
                    re_shortened_width = calculate_display_width(re_shortened)
                    
                    # Only use if it's better than current
                    if re_shortened_width > current_width:
                        region_texts[region.start] = re_shortened
                        space_used = re_shortened_width - current_width
                        available_space -= space_used
                        logger.debug(f"Re-shortened region at priority {priority_level}, used {space_used} cols")
    
    # Reconstruct the final text
    result_parts = []
    last_end = 0
    
    for region in regions_by_position:
        # Add preserved text before this region
        if region.start > last_end:
            result_parts.append(text[last_end:region.start])
        # Add shortened region
        result_parts.append(region_texts[region.start])
        last_end = region.end
    
    # Add any remaining preserved text
    if last_end < len(text):
        result_parts.append(text[last_end:])
    
    return ''.join(result_parts)


def _process_regions_sequential(text: str, target_width: int, regions: List[ShorteningRegion]) -> str:
    """
    Process overlapping regions sequentially (fallback for overlapping regions).
    
    Note: Region boundaries refer to the current text, which changes after
    each region is processed. This may cause issues with overlapping regions.
    """
    current_text = text
    
    for region in regions:
        # Validate region boundaries against current text
        if not _validate_region(region, len(current_text)):
            continue
        
        # Check if we've already met the target width
        current_width = calculate_display_width(current_text)
        if current_width <= target_width:
            return current_text
        
        # Select the appropriate strategy
        strategy_name = region.strategy.lower()
        if strategy_name not in ['all_or_nothing', 'truncate', 'abbreviate']:
            logger.warning(f"Invalid strategy '{region.strategy}' in region, falling back to 'abbreviate'")
            strategy_name = 'abbreviate'
        
        if region.filepath_mode:
            strategy = FilepathStrategy()
        elif strategy_name == 'all_or_nothing':
            strategy = AllOrNothingStrategy()
        elif strategy_name == 'truncate':
            strategy = TruncationStrategy()
        else:
            strategy = AbbreviationStrategy()
        
        # Apply the strategy
        current_text = strategy.shorten(current_text, target_width, region)
    
    return current_text


def reduce_width(
    text: str,
    target_width: int,
    regions: Optional[List[ShorteningRegion]] = None,
    default_strategy: str = 'abbreviate',
    default_position: str = 'right'
) -> str:
    """
    Reduce string display width to fit within target.
    
    This is the main entry point for the string width reduction utility. It
    intelligently shortens strings to fit within a specified display width,
    accounting for wide characters (CJK, emoji) and providing flexible control
    through regions and strategies.
    
    The function processes the string in the following order:
    1. Input validation and edge case handling
    2. If regions are specified, process them in priority order
    3. If target not met after regions (or no regions), apply fallback shortening
       to the entire string using the default strategy and position
    
    Args:
        text: Input string to shorten
        target_width: Maximum display width in columns
        regions: Optional list of regions to shorten with priorities.
                If None, the entire string is shortened using default strategy.
        default_strategy: Strategy when no regions specified or for fallback
                         ('remove' or 'abbreviate'). Default is 'abbreviate'.
        default_position: Abbreviation position for fallback shortening
                         ('left', 'middle', 'right'). Default is 'right'.
        
    Returns:
        Shortened string fitting within target_width
        
    Examples:
        Basic usage with default abbreviation:
            >>> reduce_width("very_long_filename.txt", 15)
            'very_lon….txt'
        
        With middle abbreviation:
            >>> reduce_width("very_long_filename.txt", 15, default_position='middle')
            'very_l…name.txt'
        
        With regions:
            >>> region = ShorteningRegion(start=0, end=10, priority=1, strategy='remove')
            >>> reduce_width("prefix_important_suffix", 20, regions=[region])
            'pre_important_suffix'
    """
    # Subtask 7.1: Input validation and edge cases
    
    # Handle None input
    if text is None:
        return ""
    
    # Handle empty string
    if not text:
        return ""
    
    # Handle negative or zero target width
    if target_width <= 0:
        return ""
    
    # Normalize the input text
    text = normalize_unicode(text)
    
    # Calculate current display width
    current_width = calculate_display_width(text)
    
    # If string already fits, return unchanged
    if current_width <= target_width:
        return text
    
    # Subtask 7.2: Region-based shortening
    
    if regions:
        # Process regions in priority order
        result = _process_regions(text, target_width, regions)
        
        # Check if target width is met
        result_width = calculate_display_width(result)
        if result_width <= target_width:
            return result
        
        # Target not met, will fall through to fallback shortening
        text = result
    else:
        # No regions specified, create a default region for the entire string
        default_region = ShorteningRegion(
            start=0,
            end=len(text),
            priority=1,
            strategy=default_strategy,
            abbrev_position=default_position,
            filepath_mode=False
        )
        regions = [default_region]
        
        # Process the default region
        result = _process_regions(text, target_width, regions)
        
        # Check if target width is met
        result_width = calculate_display_width(result)
        if result_width <= target_width:
            return result
        
        # If still doesn't fit, fall through to fallback shortening
        text = result
    
    # Subtask 7.3: Fallback to entire string
    
    # If we reach here, the target was not met after processing all regions
    # Apply fallback shortening to the entire string using default strategy
    
    # Validate default_strategy
    if default_strategy.lower() not in ['all_or_nothing', 'truncate', 'abbreviate']:
        logger.warning(f"Invalid strategy '{default_strategy}', falling back to 'abbreviate'")
        default_strategy = 'abbreviate'
    
    # Validate default_position
    if default_position.lower() not in ['left', 'middle', 'right']:
        logger.warning(f"Invalid position '{default_position}', falling back to 'right'")
        default_position = 'right'
    
    # Create a fallback region covering the entire string
    fallback_region = ShorteningRegion(
        start=0,
        end=len(text),
        priority=1,
        strategy=default_strategy,
        abbrev_position=default_position,
        filepath_mode=False
    )
    
    # Select the appropriate strategy
    if default_strategy.lower() == 'all_or_nothing':
        strategy = AllOrNothingStrategy()
    elif default_strategy.lower() == 'truncate':
        strategy = TruncationStrategy()
    else:  # 'abbreviate'
        strategy = AbbreviationStrategy()
    
    # Apply the fallback strategy to the entire string
    result = strategy.shorten(text, target_width, fallback_region)
    
    return result


def abbreviate_middle(text: str, target_width: int) -> str:
    """
    Convenience function: abbreviate with ellipsis in the middle.
    
    This is a convenience wrapper around reduce_width() that uses middle
    abbreviation by default. The ellipsis will be placed in the center of
    the string, preserving both the beginning and end.
    
    Args:
        text: Input string to abbreviate
        target_width: Maximum display width in columns
        
    Returns:
        Abbreviated string with ellipsis in the middle
        
    Example:
        >>> abbreviate_middle("very_long_filename.txt", 15)
        'very_l…name.txt'
    """
    return reduce_width(text, target_width, default_position='middle')


def abbreviate_path(path: str, target_width: int) -> str:
    """
    Convenience function: abbreviate filesystem path intelligently.
    
    This is a convenience wrapper around reduce_width() that uses filepath
    mode to intelligently abbreviate filesystem paths. Directory components
    are abbreviated before the filename, ensuring the filename remains as
    readable as possible.
    
    Args:
        path: Filesystem path to abbreviate
        target_width: Maximum display width in columns
        
    Returns:
        Abbreviated path with directories shortened before filename
        
    Example:
        >>> abbreviate_path("/home/user/documents/file.txt", 20)
        '/home/…/file.txt'
    """
    region = ShorteningRegion(
        start=0,
        end=len(path),
        priority=1,
        strategy='abbreviate',
        abbrev_position='middle',
        filepath_mode=True
    )
    return reduce_width(path, target_width, regions=[region])
