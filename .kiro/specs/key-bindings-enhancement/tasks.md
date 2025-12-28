# Implementation Plan: Key Bindings Enhancement

## Overview

This plan implements the enhanced key bindings system for TFM, introducing the KeyBindings class and support for modifier key combinations. The implementation follows an incremental approach: first creating the KeyBindings class, then integrating it into the configuration system, updating the application to use the new API, and finally removing legacy code.

## Tasks

- [ ] 1. Implement KeyBindings class core functionality
  - [ ] 1.1 Create KeyBindings class in tfm_config.py
    - Add class with __init__ that accepts key_bindings_config dict
    - Add logger initialization
    - Store bindings in _bindings instance variable
    - Call _build_key_lookup to create reverse lookup table
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 1.2 Implement _parse_key_expression method
    - Handle single-character keys (return uppercase char, 0 modifiers)
    - Handle multi-character keys (split on hyphen)
    - Parse modifier names (Shift, Control/Ctrl, Alt/Option, Command/Cmd)
    - Parse main key (last part after splitting)
    - Return tuple of (main_key, modifier_flags)
    - Handle case-insensitivity for all parts
    - Log warnings for unknown modifiers
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7, 3.1, 3.2, 3.4_

  - [ ] 1.3 Implement _keycode_from_string method
    - Use getattr(KeyCode, key_str, None) to get KeyCode value
    - Handle AttributeError gracefully
    - Log warning for unknown KeyCode names
    - Return None for invalid names
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ] 1.4 Implement _build_key_lookup method
    - Iterate through all actions in _bindings
    - Extract keys and selection requirement (handle both list and dict formats)
    - For each key expression, parse it to get main_key and modifiers
    - Build dictionary mapping (main_key, modifiers) to list of (action, selection_req)
    - Return the lookup dictionary
    - _Requirements: 4.4, 4.6_

  - [ ]* 1.5 Write unit tests for KeyBindings class initialization
    - Test initialization with valid configuration
    - Test initialization with empty configuration
    - Test initialization with invalid configuration
    - _Requirements: 4.1_

  - [ ]* 1.6 Write unit tests for _parse_key_expression
    - Test single-character keys ('q', 'a', '?')
    - Test KeyCode names ('ENTER', 'DOWN', 'PAGE_UP')
    - Test single modifier ('Shift-Down', 'Command-Q')
    - Test multiple modifiers ('Command-Shift-X', 'Control-Alt-Delete')
    - Test case insensitivity ('shift-down', 'SHIFT-DOWN', 'Shift-Down')
    - Test modifier order independence ('Command-Shift-X' vs 'Shift-Command-X')
    - Test unknown modifiers (should log warning)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 1.7 Write property test for KeyCode name recognition
    - **Property 1: KeyCode Name Recognition**
    - **Validates: Requirements 1.1, 1.2, 1.3**
    - Generate random KeyCode names with random casing
    - Verify all are recognized and resolve correctly
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 1.8 Write property test for modifier key support
    - **Property 2: Modifier Key Support**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    - Generate random combinations of modifiers with random keys
    - Generate random permutations of modifier order
    - Generate random casing for modifiers
    - Verify all parse correctly
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 2. Implement KeyBindings matching and lookup methods
  - [ ] 2.1 Implement _match_key_event method
    - Check if event.modifiers matches expected modifiers
    - For single-character main_key, match against event.char (uppercase)
    - For multi-character main_key, convert to KeyCode and match against event.key_code
    - Return True if match, False otherwise
    - _Requirements: 2.6, 5.2, 5.3, 5.4_

  - [ ] 2.2 Implement _check_selection_requirement method
    - Handle 'required' (return has_selection)
    - Handle 'none' (return not has_selection)
    - Handle 'any' (return True)
    - _Requirements: 4.5, 5.6_

  - [ ] 2.3 Implement find_action_for_event method
    - Return None if event is None
    - Iterate through _key_to_actions lookup table
    - For each (main_key, modifiers), check if event matches using _match_key_event
    - If match found, check selection requirements for each action
    - Return first action that satisfies selection requirement
    - Return None if no match found
    - _Requirements: 5.1, 5.5, 5.7_

  - [ ] 2.4 Implement get_keys_for_action method
    - Return ([], 'any') if action not in _bindings
    - Extract keys and selection requirement from binding
    - Handle both list format and dict format
    - Return tuple of (keys, selection_requirement)
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ] 2.5 Implement format_key_for_display method
    - Return single-character keys as-is
    - For multi-character keys, split on hyphen
    - Capitalize modifiers (abbreviate Command to Cmd)
    - Uppercase main key
    - Join with hyphens
    - _Requirements: 6.5_

  - [ ]* 2.6 Write unit tests for _match_key_event
    - Test single-character matching against KeyEvent.char
    - Test KeyCode name matching against KeyEvent.key_code
    - Test modifier matching
    - Test non-matching cases
    - _Requirements: 5.2, 5.3, 5.4_

  - [ ]* 2.7 Write unit tests for find_action_for_event
    - Test finding action for single-character key
    - Test finding action for KeyCode name
    - Test finding action for modified key
    - Test returning None for no match
    - Test selection requirement enforcement
    - _Requirements: 5.1, 5.5, 5.6_

  - [ ]* 2.8 Write property test for single character backward compatibility
    - **Property 3: Single Character Backward Compatibility**
    - **Validates: Requirements 1.5, 2.6, 7.1**
    - Generate random single-character keys
    - Verify they match against KeyEvent.char
    - _Requirements: 1.5, 2.6_

  - [ ]* 2.9 Write property test for KeyEvent to action lookup
    - **Property 8: KeyEvent to Action Lookup**
    - **Validates: Requirements 5.1, 5.3, 5.4, 5.5**
    - Generate random KeyEvents
    - Verify correct action lookup or None
    - _Requirements: 5.1, 5.3, 5.4, 5.5_

  - [ ]* 2.10 Write property test for selection requirement enforcement
    - **Property 6: Selection Requirement Enforcement**
    - **Validates: Requirements 4.5, 5.6**
    - Generate random selection requirements and states
    - Verify requirements are enforced correctly
    - _Requirements: 4.5, 5.6_

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Integrate KeyBindings into ConfigManager
  - [ ] 4.1 Add _key_bindings instance variable to ConfigManager.__init__
    - Initialize to None
    - _Requirements: 4.1_

  - [ ] 4.2 Implement get_key_bindings method in ConfigManager
    - Get current config
    - If _key_bindings is None, create new KeyBindings instance
    - Use config.KEY_BINDINGS if available, else DefaultConfig.KEY_BINDINGS
    - Cache in _key_bindings
    - Return _key_bindings
    - _Requirements: 4.1_

  - [ ] 4.3 Update reload_config method to clear _key_bindings cache
    - Set self._key_bindings = None
    - _Requirements: 4.1_

  - [ ] 4.4 Add public API function find_action_for_event
    - Get key_bindings from config_manager
    - Call key_bindings.find_action_for_event(event, has_selection)
    - Return result
    - _Requirements: 5.1_

  - [ ] 4.5 Add public API function get_keys_for_action
    - Get key_bindings from config_manager
    - Call key_bindings.get_keys_for_action(action)
    - Return result
    - _Requirements: 6.1_

  - [ ] 4.6 Add public API function format_key_for_display
    - Get key_bindings from config_manager
    - Call key_bindings.format_key_for_display(key_expr)
    - Return result
    - _Requirements: 6.5_

  - [ ]* 4.7 Write unit tests for ConfigManager integration
    - Test get_key_bindings returns KeyBindings instance
    - Test caching works correctly
    - Test reload_config clears cache
    - Test public API functions work correctly
    - _Requirements: 4.1, 5.1, 6.1, 6.5_

  - [ ]* 4.8 Write property test for configuration format support
    - **Property 5: Configuration Format Support**
    - **Validates: Requirements 4.4, 7.2, 7.3**
    - Generate random configurations in both formats
    - Verify both are handled correctly
    - _Requirements: 4.4, 7.2, 7.3_

  - [ ]* 4.9 Write property test for action to keys reverse lookup
    - **Property 9: Action to Keys Reverse Lookup**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**
    - Generate random action names
    - Verify correct key expressions and requirements returned
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 5. Update DefaultConfig.KEY_BINDINGS to use new format
  - [ ] 5.1 Update KEY_BINDINGS to use KeyCode names directly
    - Replace SPECIAL_KEY_MAP references with KeyCode names
    - Use 'UP', 'DOWN', 'LEFT', 'RIGHT' instead of special key names
    - Use 'PAGE_UP', 'PAGE_DOWN', 'HOME', 'END' for navigation
    - Use 'ENTER', 'ESCAPE', 'TAB', 'BACKSPACE', 'DELETE' for editing
    - Use 'F1'-'F12' for function keys
    - _Requirements: 1.1, 1.2, 8.1, 8.2_

  - [ ] 5.2 Add modifier key bindings to KEY_BINDINGS
    - Add 'Shift-UP' and 'Shift-DOWN' for page navigation
    - Add 'Command-UP' and 'Command-DOWN' for jump to top/bottom
    - Add 'Command-Backspace' for delete
    - Add other useful modifier combinations
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 5.3 Write unit tests for updated KEY_BINDINGS
    - Test all default bindings still work
    - Test new modifier bindings work
    - Test backward compatibility maintained
    - _Requirements: 7.4_

  - [ ]* 5.4 Write property test for legacy key name compatibility
    - **Property 11: Legacy Key Name Compatibility**
    - **Validates: Requirements 7.5**
    - Generate key names from old SPECIAL_KEY_MAP
    - Verify they still work as KeyCode names
    - _Requirements: 7.5_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Update application code to use new API
  - [ ] 7.1 Update tfm_main.py to use find_action_for_event
    - Replace is_input_event_bound_to_with_selection calls
    - Use find_action_for_event instead
    - Update action handling logic to use returned action name
    - _Requirements: 5.1_

  - [ ] 7.2 Update tfm_pane_manager.py to use find_action_for_event
    - Replace is_input_event_bound_to_with_selection calls
    - Use find_action_for_event instead
    - Update action handling logic
    - _Requirements: 5.1_

  - [ ] 7.3 Update help dialog to use get_keys_for_action
    - Replace get_key_for_action calls
    - Use get_keys_for_action to get all keys for each action
    - Use format_key_for_display to format keys for display
    - _Requirements: 6.1, 6.5_

  - [ ] 7.4 Update other files that use key binding API
    - Search for is_key_bound_to, is_special_key_bound_to, etc.
    - Replace with find_action_for_event where appropriate
    - Update to use new API consistently
    - _Requirements: 5.1_

  - [ ]* 7.5 Write integration tests for application updates
    - Test key handling in tfm_main.py
    - Test key handling in tfm_pane_manager.py
    - Test help dialog displays keys correctly
    - _Requirements: 5.1, 6.1, 6.5_

- [ ] 8. Remove legacy code
  - [ ] 8.1 Remove SPECIAL_KEY_MAP from tfm_config.py
    - Delete SPECIAL_KEY_MAP dictionary
    - _Requirements: 8.1, 8.3_

  - [ ] 8.2 Remove SPECIAL_KEY_NAMES from tfm_config.py
    - Delete SPECIAL_KEY_NAMES dictionary
    - _Requirements: 8.4_

  - [ ] 8.3 Mark old API functions as deprecated
    - Add deprecation warnings to is_key_bound_to, is_special_key_bound_to, etc.
    - Add docstring notes recommending new API
    - Keep functions for backward compatibility but discourage use
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ] 8.4 Update documentation
    - Document new key expression format
    - Document modifier key support
    - Document KeyBindings class API
    - Provide migration examples
    - Update user guide with new key binding examples
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 8.5 Write property test for multiple keys per action
    - **Property 7: Multiple Keys Per Action**
    - **Validates: Requirements 4.6**
    - Generate random actions with multiple keys
    - Verify all keys trigger the action
    - _Requirements: 4.6_

  - [ ]* 8.6 Write property test for display formatting
    - **Property 10: Display Formatting**
    - **Validates: Requirements 6.5**
    - Generate random key expressions
    - Verify formatting is consistent and readable
    - _Requirements: 6.5_

- [ ] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Checkpoints ensure incremental validation
- The implementation maintains backward compatibility throughout
- Legacy code is marked deprecated but not removed to avoid breaking existing code
