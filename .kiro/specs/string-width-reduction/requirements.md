# Requirements Document

## Introduction

This document specifies requirements for a string width reduction utility module that intelligently shortens strings to fit within specified display widths while accounting for wide characters. The utility will be used across various UI components in TFM, such as QuickChoiceBar, to ensure text fits within available space.

## Glossary

- **String_Width_Reducer**: The utility module that reduces string display width
- **Wide_Character**: A character that occupies two display columns (e.g., CJK characters, emoji)
- **Display_Width**: The number of terminal columns a string occupies when rendered
- **Shortening_Strategy**: The method used to reduce string length (remove or abbreviate)
- **Shortening_Region**: A specific portion of the string designated for shortening with an associated priority
- **Abbreviation_Position**: The location where the ellipsis character appears (left, middle, right)
- **Filepath_Mode**: A specialized abbreviation mode that operates on directory and filename components separately
- **Text_Mode**: Standard abbreviation mode that treats the string as uniform text
- **Ellipsis**: The "…" character used to indicate abbreviated content

## Requirements

### Requirement 1

**User Story:** As a developer, I want to reduce a string's display width to fit within a specified column limit, so that UI elements display correctly without overflow.

#### Acceptance Criteria

1. WHEN a string and target width are provided, THE String_Width_Reducer SHALL return a string with display width less than or equal to the target width
2. WHEN calculating display width, THE String_Width_Reducer SHALL count wide characters as two columns and narrow characters as one column
3. WHEN the original string already fits within the target width, THE String_Width_Reducer SHALL return the original string unchanged
4. WHEN the target width is zero or negative, THE String_Width_Reducer SHALL return an empty string

### Requirement 2

**User Story:** As a developer, I want to choose between removal and abbreviation strategies, so that I can control how strings are shortened based on context.

#### Acceptance Criteria

1. WHEN the removal strategy is specified, THE String_Width_Reducer SHALL remove characters from designated regions without adding ellipsis
2. WHEN the abbreviation strategy is specified, THE String_Width_Reducer SHALL replace removed content with the ellipsis character "…"
3. WHEN abbreviation is used, THE String_Width_Reducer SHALL ensure the ellipsis character is counted in the display width calculation
4. THE String_Width_Reducer SHALL support specifying different strategies for different regions within the same string

### Requirement 3

**User Story:** As a developer, I want to specify one or more regions to shorten with priorities, so that less important parts are shortened first.

#### Acceptance Criteria

1. WHEN multiple shortening regions are specified, THE String_Width_Reducer SHALL process them in priority order from highest to lowest
2. WHEN a region is specified, THE String_Width_Reducer SHALL accept a start position, end position, priority value, and shortening strategy
3. WHEN shortening a region, THE String_Width_Reducer SHALL not modify characters outside the region boundaries
4. WHEN regions overlap, THE String_Width_Reducer SHALL handle them according to their priority order
5. WHEN no regions are specified, THE String_Width_Reducer SHALL apply shortening to the entire string

### Requirement 4

**User Story:** As a developer, I want to specify the abbreviation position (left, middle, right), so that the most important part of the text remains visible.

#### Acceptance Criteria

1. WHEN left abbreviation is specified, THE String_Width_Reducer SHALL place the ellipsis at the beginning and preserve the right portion
2. WHEN middle abbreviation is specified, THE String_Width_Reducer SHALL place the ellipsis in the center and preserve both ends
3. WHEN right abbreviation is specified, THE String_Width_Reducer SHALL place the ellipsis at the end and preserve the left portion
4. WHEN middle abbreviation is used, THE String_Width_Reducer SHALL distribute preserved characters approximately equally between left and right portions

### Requirement 5

**User Story:** As a developer, I want to use filepath mode for path strings, so that directory and filename components are abbreviated intelligently.

#### Acceptance Criteria

1. WHEN filepath mode is enabled, THE String_Width_Reducer SHALL parse the string as a filesystem path
2. WHEN abbreviating in filepath mode, THE String_Width_Reducer SHALL identify directory components and filename components separately
3. WHEN shortening in filepath mode, THE String_Width_Reducer SHALL abbreviate directory names before abbreviating the filename
4. WHEN a directory component is abbreviated in filepath mode, THE String_Width_Reducer SHALL preserve path separators
5. WHEN filepath mode is disabled, THE String_Width_Reducer SHALL treat the string as uniform text

### Requirement 6

**User Story:** As a developer, I want the utility to handle cases where the string cannot be shortened further within regions, so that the system gracefully falls back to shortening the entire string.

#### Acceptance Criteria

1. WHEN all specified regions have been fully shortened and the target width is not met, THE String_Width_Reducer SHALL apply shortening to the entire string
2. WHEN the entire string must be shortened, THE String_Width_Reducer SHALL use the abbreviation strategy with the specified position
3. WHEN the target width is smaller than the minimum displayable content (ellipsis plus one character), THE String_Width_Reducer SHALL return only the ellipsis character
4. WHEN falling back to entire string shortening, THE String_Width_Reducer SHALL preserve as much content as possible within the width constraint

### Requirement 7

**User Story:** As a developer, I want the utility to correctly handle Unicode normalization, so that strings with composed and decomposed characters are processed consistently.

#### Acceptance Criteria

1. WHEN processing strings, THE String_Width_Reducer SHALL normalize Unicode strings to NFC form before width calculation
2. WHEN shortening strings, THE String_Width_Reducer SHALL maintain Unicode normalization in the output
3. WHEN combining characters are present, THE String_Width_Reducer SHALL treat them as part of their base character for width calculation
4. WHEN emoji with variation selectors or modifiers are present, THE String_Width_Reducer SHALL calculate their display width correctly

### Requirement 8

**User Story:** As a developer, I want a simple API for common use cases, so that I can quickly integrate string shortening without complex configuration.

#### Acceptance Criteria

1. THE String_Width_Reducer SHALL provide a function that accepts a string and target width with sensible defaults
2. THE String_Width_Reducer SHALL provide convenience functions for common patterns (e.g., abbreviate_middle, abbreviate_path)
3. WHEN using convenience functions, THE String_Width_Reducer SHALL apply appropriate defaults for the use case
4. THE String_Width_Reducer SHALL provide clear documentation with usage examples for all public functions

### Requirement 9

**User Story:** As a developer, I want higher priority regions to be recalculated after lower priority regions are shortened, so that content is preserved optimally when filepath mode frees up significant space.

#### Acceptance Criteria

1. WHEN a lower priority region is shortened and frees up display width, THE String_Width_Reducer SHALL recalculate higher priority regions to potentially restore content
2. WHEN recalculating higher priority regions, THE String_Width_Reducer SHALL attempt to restore content that was previously shortened
3. WHEN filepath mode removes multiple directory levels, THE String_Width_Reducer SHALL use the freed space to preserve more content in higher priority regions
4. WHEN recalculation occurs, THE String_Width_Reducer SHALL maintain the priority order and not exceed the target width
5. WHEN all regions fit after recalculation, THE String_Width_Reducer SHALL return the result with maximum content preserved
