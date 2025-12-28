# Implementation Plan: Modifier Key Bindings

## Overview

This implementation plan breaks down the modifier key bindings feature into discrete coding tasks. The approach is to build the core parsing and matching infrastructure first, then integrate it with the existing key binding system, and finally update the configuration and help dialog.

## Tasks

- [ ] 1. Create ParsedKey data class and KeyExpressionParser
  - Create new module `src/tfm_key_expression_parser.py`
  - Implement `ParsedKey` dataclass with `main_key`, `modifiers`, and `original_expr` fields
  - Implement `KeyExpressionParser` class with modifier name mappings and special key name mappings
  - Implement `parse_key_expression()` method to parse key expression strings
  - Implement `normalize_modifier_name()` method for case-insensitive modifier lookup
  - Implement `normalize_main_key()` method for case-insensitive main key lookup
  - Implement `validate_expression()` method for validation without parsing
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 3.1, 3.2, 3.3, 3.4_

- [ ]* 1.1 Write property test for modifier-key format parsing
  - **Property 1: Modifier-Key Format Parsing**
  - **Validates: Requirements 1.1, 1.2**

- [ ]* 1.2 Write property test for case insensitivity
  - **Property 2: Case Insensitivity**
  - **Validates: Requirements 1.3, 1.4**

- [ ]* 1.3 Write property test for modifier alias equivalence
  - **Property 3: Modifier Alias Equivalence**
  - **Validates: Requirements 1.6, 1.7, 1.8**

- [ ]* 1.4 Write property test for modifier order independence
  - **Property 4: Modifier Order Independence**
  - **Validates: Requirements 4.6**

- [ ]* 1.5 Write property test for backward compatibility
  - **Property 5: Backward Compatibility**
  - **Validates: Requirements 2.1, 2.3, 2.4**

- [ ]* 1.6 Write property test for validation consistency
  - **Property 7: Validation Consistency**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

- [ ]* 1.7 Write unit tests for parser edge cases
  - Test empty string error
  - Test multiple consecutive hyphens error
  - Test specific modifier names (Shift, Option, Alt, Control, Ctrl, Command, Cmd)
  - _Requirements: 1.5, 3.3_

- [ ] 2. Implement KeyMatcher for event matching
  - Add `KeyMatcher` class to `src/tfm_key_expression_parser.py`
  - Implement `matches_event()` method to compare ParsedKey against KeyEvent
  - Implement `extract_event_modifiers()` method to extract modifiers from KeyEvent
  - Implement `extract_event_main_key()` method to extract main key from KeyEvent
  - Add `matches_event()` method to `ParsedKey` dataclass
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [ ]* 2.1 Write property test for event matching exactness
  - **Property 6: Event Matching Exactness**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

- [ ]* 2.2 Write unit tests for event matching edge cases
  - Test matching with no modifiers
  - Test matching with single modifier
  - Test matching with multiple modifiers
  - Test non-matching cases (wrong modifier, extra modifier, missing modifier)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Enhance KeyBindingManager with modifier support
  - Update `src/tfm_key_bindings.py` to import `KeyExpressionParser` and `ParsedKey`
  - Add `_parsed_keys_cache` class variable to `KeyBindingManager`
  - Implement `get_parsed_keys_for_action()` method to parse and cache key expressions
  - Implement `find_action_for_event()` method to find action matching a KeyEvent
  - Update `validate_key_bindings()` method to validate modifier key expressions
  - Update `get_key_to_action_mapping()` to work with ParsedKey objects
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 4.1 Write unit tests for KeyBindingManager integration
  - Test parsing key expressions from Config
  - Test caching of parsed keys
  - Test finding actions for events
  - Test validation of key bindings
  - Test mixed simple and modifier key expressions
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 5. Update input event handling
  - Update `src/tfm_input_utils.py` to import `KeyBindingManager` and `KeyMatcher`
  - Modify `input_event_to_key_char()` to handle modifier key expressions (or deprecate if no longer needed)
  - Update `is_input_event_for_action()` to use `KeyBindingManager.find_action_for_event()`
  - Update `is_input_event_for_action_with_selection()` to use new matching logic
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 5.1 Write integration tests for input event handling
  - Test event matching with simple keys
  - Test event matching with modifier keys
  - Test event matching with selection requirements
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 6. Update configuration file documentation
  - Update `src/_config.py` KEY_BINDINGS comments to explain modifier key format
  - Add examples of modifier key expressions in comments
  - List all supported modifier names and aliases
  - Explain case-insensitivity rules
  - Explain modifier order independence
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 7. Update help dialog to use dynamic key bindings
  - Locate help dialog implementation (likely in `src/tfm_info_dialog.py` or similar)
  - Update help dialog to read key bindings from `KeyBindingManager` instead of hardcoded strings
  - Format modifier key expressions in a readable way (e.g., "Shift-Space" or "Shift+Space")
  - Ensure help dialog reflects current KEY_BINDINGS configuration
  - _Requirements: 7.1, 7.3, 7.4_

- [ ]* 7.1 Write property test for configuration dynamic updates
  - **Property 8: Configuration Dynamic Updates**
  - **Validates: Requirements 7.4**

- [ ]* 7.2 Write unit tests for help dialog integration
  - Test help dialog displays modifier key expressions
  - Test help dialog updates when Config changes
  - Test help dialog doesn't use hardcoded strings
  - _Requirements: 7.1, 7.3_

- [ ] 8. Final integration and validation
  - Run all tests to ensure everything works together
  - Test with real keyboard events in the application
  - Verify backward compatibility with existing simple key bindings
  - Verify new modifier key bindings work as expected
  - _Requirements: All_

- [ ] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation follows a bottom-up approach: core parsing → matching → integration → UI
