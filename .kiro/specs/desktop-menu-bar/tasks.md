# Implementation Plan

- [ ] 1. Set up TTK abstract menu interface
  - Add MenuEvent class to TTK renderer abstract base class
  - Add set_menu_bar() abstract method to RendererABC
  - Add update_menu_item_state() abstract method to RendererABC
  - Update get_event() to support MenuEvent objects
  - _Requirements: 2.1, 3.1, 3.2, 3.3_

- [ ]* 1.1 Write property test for MenuEvent creation
  - **Property 2: Menu event delivery**
  - **Validates: Requirements 3.1, 3.2, 3.3**

- [ ] 2. Implement CoreGraphics backend menu support
  - Add menu bar creation using NSMenu and NSMenuItem APIs
  - Implement menu item callback mechanism for selections
  - Add menu event queue for MenuEvent objects
  - Implement shortcut parsing for macOS key equivalents
  - _Requirements: 8.2, 10.3_

- [ ]* 2.1 Write property test for menu structure consistency
  - **Property 1: Menu structure consistency**
  - **Validates: Requirements 2.3**

- [ ]* 2.2 Write property test for disabled menu items
  - **Property 3: Disabled menu items prevent events**
  - **Validates: Requirements 1.4**

- [ ] 3. Create MenuManager class in TFM
  - Implement menu structure builder with File, Edit, View, and Go menus
  - Add menu item ID constants and definitions
  - Implement menu state calculation logic
  - Add enable/disable logic for selection-dependent items
  - Add enable/disable logic for clipboard-dependent items
  - Add enable/disable logic for navigation items (parent directory at root)
  - _Requirements: 2.2, 2.3, 2.5, 4.2, 5.2, 6.2, 7.2_

- [ ]* 3.1 Write property test for menu structure completeness
  - **Property 5: Menu structure completeness**
  - **Validates: Requirements 4.2, 5.2, 6.2, 7.2**

- [ ]* 3.2 Write property test for keyboard shortcut uniqueness
  - **Property 6: Keyboard shortcuts are unique**
  - **Validates: Requirements 10.3**

- [ ]* 3.3 Write property test for parent directory menu state
  - **Property 8: Parent directory menu state**
  - **Validates: Requirements 7.4**

- [ ]* 3.4 Write property test for selection-dependent menu states
  - **Property 9: Selection-dependent menu states**
  - **Validates: Requirements 4.4, 5.4**

- [ ]* 3.5 Write property test for clipboard-dependent menu state
  - **Property 10: Clipboard-dependent menu state**
  - **Validates: Requirements 5.5**

- [ ] 4. Integrate menu system into TFM main application
  - Add desktop mode detection in TFM initialization
  - Initialize MenuManager for desktop mode
  - Call set_menu_bar() with menu structure during initialization
  - Add menu state update calls in main loop
  - _Requirements: 1.1, 2.1, 9.1_

- [ ]* 4.1 Write property test for menu state updates
  - **Property 4: Menu state updates are reflected**
  - **Validates: Requirements 9.3**

- [ ] 5. Implement menu event handling in TFM
  - Add MenuEvent handling to main event loop
  - Create menu event dispatcher that maps item IDs to actions
  - Implement File menu action handlers (new_file, new_folder, open, delete, rename, quit)
  - Implement Edit menu action handlers (copy, cut, paste, select_all)
  - Implement View menu action handlers (show_hidden, sort_by_*, refresh)
  - Implement Go menu action handlers (parent, home, favorites, recent)
  - _Requirements: 1.3, 3.4, 4.3, 5.3, 6.3, 6.5, 7.3, 7.5_

- [ ]* 5.1 Write property test for menu action execution
  - **Property 7: Menu action execution**
  - **Validates: Requirements 1.3**

- [ ] 6. Add keyboard shortcut support
  - Implement shortcut parsing in MenuManager
  - Add platform-specific shortcut formatting (Cmd for macOS, Ctrl for Windows)
  - Ensure shortcuts are included in menu structure
  - Test that shortcuts execute actions without opening menus
  - _Requirements: 10.1, 10.2, 10.3, 10.5_

- [ ]* 6.1 Write property test for keyboard shortcut execution
  - **Property 2: Menu event delivery** (for shortcuts)
  - **Validates: Requirements 10.2**

- [ ] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Create demo script for menu bar feature
  - Create demo that shows menu bar in desktop mode
  - Demonstrate menu selection and action execution
  - Show menu state updates based on selection
  - Show keyboard shortcut functionality
  - _Requirements: All_

- [ ]* 8.1 Write integration test for end-to-end menu flow
  - Test complete flow: create menu, select item, verify action executes
  - Test menu state updates when application state changes
  - Test keyboard shortcuts execute actions
  - _Requirements: All_

- [ ] 9. Create end-user documentation
  - Document menu bar feature for users
  - Explain available menus and menu items
  - Document keyboard shortcuts
  - Provide usage examples
  - _Requirements: All_

- [ ] 10. Create developer documentation
  - Document menu system architecture
  - Explain how to add new menu items
  - Document MenuEvent handling
  - Provide implementation examples
  - _Requirements: All_

- [ ] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
