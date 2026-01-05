# Requirements Document

## Introduction

This document specifies requirements for a new text layout system for TFM (Terminal File Manager). The system will provide a comprehensive API for rendering text segments with intelligent width management, color attributes, and flexible shortening strategies. Unlike the existing `tfm_string_width.py` which focuses solely on width reduction, this new system will handle the complete text layout and rendering pipeline, including drawing text to the screen with proper positioning, colors, and attributes.

## Glossary

- **Text_Layout_System**: The new module that handles text segment layout, shortening, and rendering
- **Text_Segment**: An object containing a string, shortening configuration, color, and text attributes
- **Shortening_Strategy**: A method for reducing text width (abbreviation, filepath-abbreviation, truncate, all-or-nothing, as-is)
- **Abbreviation_Position**: Location where ellipsis appears when abbreviating (left, middle, right)
- **Spacer**: A special text segment that expands with whitespace when text doesn't need shortening
- **Priority**: Numeric value determining which segments are shortened first (higher values shortened first)
- **Minimum_Length**: The minimum number of characters a segment must retain after shortening
- **Rendering_Width**: The target display width in terminal columns for the entire text layout
- **Drawing_Position**: The (row, column) coordinates where text should be rendered on screen
- **Text_Attribute**: Terminal text styling (bold, underline, reverse, etc.)
- **Color_Pair**: Terminal color pair number for foreground/background colors
- **Display_Width**: The width of text in terminal columns, accounting for wide characters

## Requirements

### Requirement 1: Text Segment Definition

**User Story:** As a developer, I want to define text segments with comprehensive configuration, so that I can specify exactly how each portion of text should be rendered and shortened.

#### Acceptance Criteria

1. THE Text_Segment SHALL contain a string value
2. THE Text_Segment SHALL contain a shortening strategy specification
3. THE Text_Segment SHALL contain an abbreviation position specification
4. THE Text_Segment SHALL contain a minimum length value
5. THE Text_Segment SHALL contain a priority value
6. THE Text_Segment SHALL contain a color pair value
7. THE Text_Segment SHALL contain a text attribute value
8. WHEN a Text_Segment is created with default values THEN the system SHALL use sensible defaults for all optional fields

### Requirement 2: Shortening Strategy Support

**User Story:** As a developer, I want multiple shortening strategies available, so that I can choose the most appropriate method for each text segment.

#### Acceptance Criteria

1. WHEN the shortening strategy is "abbreviation" THEN the system SHALL replace removed content with an ellipsis character
2. WHEN the shortening strategy is "filepath-abbreviation" THEN the system SHALL intelligently abbreviate filesystem paths by removing directory levels
3. WHEN the shortening strategy is "truncate" THEN the system SHALL remove characters from the end without adding ellipsis
4. WHEN the shortening strategy is "all-or-nothing" THEN the system SHALL either keep the segment entirely or remove it completely
5. WHEN the shortening strategy is "as-is" THEN the system SHALL never shorten the segment regardless of width constraints
6. WHEN an invalid shortening strategy is specified THEN the system SHALL log a warning and fall back to "abbreviation"

### Requirement 3: Abbreviation Position Control

**User Story:** As a developer, I want to control where the ellipsis appears when abbreviating, so that I can preserve the most important parts of the text.

#### Acceptance Criteria

1. WHEN abbreviation position is "left" THEN the system SHALL place ellipsis at the start and preserve the right portion
2. WHEN abbreviation position is "middle" THEN the system SHALL place ellipsis in the center and preserve both ends
3. WHEN abbreviation position is "right" THEN the system SHALL place ellipsis at the end and preserve the left portion
4. WHEN an invalid abbreviation position is specified THEN the system SHALL log a warning and fall back to "right"

### Requirement 4: Priority-Based Shortening

**User Story:** As a developer, I want to assign priorities to text segments, so that less important segments are shortened before more important ones.

#### Acceptance Criteria

1. WHEN multiple segments need shortening THEN the system SHALL shorten segments with higher priority values first
2. WHEN segments have equal priority THEN the system SHALL shorten them in their definition order
3. WHEN a segment has priority 0 THEN the system SHALL treat it as lowest priority
4. WHEN shortening is complete and space remains THEN the system SHALL attempt to restore segments in reverse priority order

### Requirement 5: Minimum Length Enforcement

**User Story:** As a developer, I want to specify minimum lengths for segments, so that critical information is never shortened below a readable threshold.

#### Acceptance Criteria

1. WHEN a segment has a minimum length specified THEN the system SHALL never shorten it below that length
2. WHEN a segment cannot meet its minimum length within width constraints THEN the system SHALL preserve as much as possible up to the minimum
3. WHEN minimum length is 0 THEN the system SHALL allow the segment to be completely removed if necessary
4. WHEN minimum length exceeds the segment's actual length THEN the system SHALL treat the actual length as the minimum

### Requirement 6: Spacer Support

**User Story:** As a developer, I want to add spacers between text segments, so that text can expand to fill available width when shortening is not needed.

#### Acceptance Criteria

1. WHEN a segment is marked as a spacer THEN the system SHALL treat it as expandable whitespace
2. WHEN the total text width is less than rendering width THEN the system SHALL distribute extra space among all spacers
3. WHEN multiple spacers exist THEN the system SHALL distribute extra space equally among them
4. WHEN no spacers exist and text is shorter than rendering width THEN the system SHALL not add any padding
5. WHEN spacers exist but text must be shortened THEN the system SHALL collapse all spacers to zero width before shortening other segments

### Requirement 7: Text Layout and Rendering

**User Story:** As a developer, I want the system to handle both layout calculation and rendering, so that I can display formatted text with a single API call.

#### Acceptance Criteria

1. WHEN the layout API is called THEN the system SHALL calculate the final shortened text for all segments
2. WHEN the layout API is called THEN the system SHALL render each segment at the specified drawing position
3. WHEN rendering a segment THEN the system SHALL apply the segment's color pair
4. WHEN rendering a segment THEN the system SHALL apply the segment's text attributes
5. WHEN rendering multiple segments THEN the system SHALL position them consecutively without gaps
6. WHEN the total width exceeds rendering width THEN the system SHALL shorten segments according to their priorities and strategies

### Requirement 8: Wide Character Support

**User Story:** As a developer, I want the system to correctly handle wide characters, so that CJK text and emoji are properly measured and rendered.

#### Acceptance Criteria

1. WHEN calculating display width THEN the system SHALL use TTK's wide character utilities
2. WHEN shortening text with wide characters THEN the system SHALL account for their 2-column width
3. WHEN a wide character would be split at a boundary THEN the system SHALL exclude it entirely rather than splitting
4. WHEN normalizing text THEN the system SHALL use NFC normalization for consistent character representation

### Requirement 9: Color and Attribute Management

**User Story:** As a developer, I want to specify colors and attributes per segment, so that I can create visually distinct text layouts.

#### Acceptance Criteria

1. WHEN a segment specifies a color pair THEN the system SHALL apply that color when rendering
2. WHEN a segment specifies text attributes THEN the system SHALL apply those attributes when rendering
3. WHEN a segment has no color specified THEN the system SHALL use the default color provided to the layout API
4. WHEN a segment has no attributes specified THEN the system SHALL use the default attributes provided to the layout API
5. WHEN rendering completes THEN the system SHALL restore the previous color and attribute state

### Requirement 10: API Design

**User Story:** As a developer, I want a clean and intuitive API, so that I can easily integrate the text layout system into TFM components.

#### Acceptance Criteria

1. THE system SHALL provide a primary function named draw_text_segments that accepts drawing position, segment list, rendering width, default color, and default attributes
2. THE system SHALL provide classes for each segment type (AbbreviationSegment, FilepathSegment, TruncateSegment, AllOrNothingSegment, AsIsSegment, SpacerSegment)
3. THE system SHALL provide a SpacerSegment class for expandable whitespace
4. THE system SHALL provide helper functions for common layout patterns
5. WHEN the API is called with invalid parameters THEN the system SHALL log errors and handle gracefully without crashing

### Requirement 11: Logging and Debugging

**User Story:** As a developer, I want comprehensive logging, so that I can debug layout issues and understand shortening decisions.

#### Acceptance Criteria

1. WHEN segments are shortened THEN the system SHALL log which segments were affected and by how much
2. WHEN priorities are processed THEN the system SHALL log the priority order
3. WHEN spacers are expanded THEN the system SHALL log the distribution of extra space
4. WHEN errors occur THEN the system SHALL log detailed error messages with context
5. THE system SHALL use TFM's unified logging system with an appropriate logger name

### Requirement 12: Independence from Legacy System

**User Story:** As a developer, I want the new system to be independent from tfm_string_width.py, so that it can eventually replace the legacy system without dependencies.

#### Acceptance Criteria

1. THE Text_Layout_System SHALL NOT import or depend on tfm_string_width.py
2. THE Text_Layout_System SHALL implement its own shortening strategies
3. THE Text_Layout_System SHALL use TTK's wide_char_utils directly for width calculations
4. THE Text_Layout_System SHALL be usable as a standalone module
5. WHEN the legacy system is removed THEN the Text_Layout_System SHALL continue functioning without modification
