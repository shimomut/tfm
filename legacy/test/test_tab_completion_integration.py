#!/usr/bin/env python3
"""
Integration tests for TAB completion keyboard navigation workflow

Tests complete workflows including:
- TAB → Down → Down → Enter
- TAB → Up → ESC
- Scrolling with long candidate lists
- Focus wrapping at boundaries
- Visual feedback at each step

Run with: PYTHONPATH=.:src:ttk pytest test/test_tab_completion_integration.py -v
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import os
import tempfile
import shutil

from tfm_single_line_text_edit import SingleLineTextEdit, FilepathCompleter
from tfm_candidate_list_overlay import CandidateListOverlay
from ttk import KeyEvent, KeyCode
from ttk.input_event import CharEvent


class TestTabCompletionIntegration(unittest.TestCase):
    """Integration tests for complete TAB completion workflows"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock renderer
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)
        
        # Create temporary directory with test files
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
        
        # Create test files and directories
        os.makedirs(os.path.join(self.test_dir, "dir1"))
        os.makedirs(os.path.join(self.test_dir, "dir2"))
        os.makedirs(os.path.join(self.test_dir, "directory_long_name"))
        
        for i in range(15):  # Create many files for scrolling tests
            with open(os.path.join(self.test_dir, f"file{i:02d}.txt"), 'w') as f:
                f.write("test")
        
        with open(os.path.join(self.test_dir, "abc.txt"), 'w') as f:
            f.write("test")
        with open(os.path.join(self.test_dir, "abcd.txt"), 'w') as f:
            f.write("test")
        with open(os.path.join(self.test_dir, "abcde.txt"), 'w') as f:
            f.write("test")
    
    def test_workflow_tab_down_down_enter(self):
        """
        Test complete workflow: TAB → Down → Down → Enter
        
        Validates:
        - TAB triggers completion and shows candidate list
        - Down arrow moves focus through candidates
        - Enter selects focused candidate
        - Requirements: 9.1, 9.7, 10.1, 10.2, 10.3
        """
        print("\n=== Testing TAB → Down → Down → Enter workflow ===")
        
        # Create editor with filepath completer
        completer = FilepathCompleter(self.test_dir)
        editor = SingleLineTextEdit(
            initial_text="ab",
            renderer=self.mock_renderer,
            completer=completer
        )
        editor.move_cursor_end()
        
        # Step 1: Press TAB to trigger completion
        print("Step 1: Pressing TAB...")
        tab_event = KeyEvent(key_code=KeyCode.TAB, modifiers=0)
        result = editor.handle_key(tab_event)
        
        # Verify TAB was handled
        assert result, "TAB key should be handled"
        
        # Trigger draw to render candidate list
        editor.draw(self.mock_renderer, 10, 0, 80, "", True)
        
        # Verify candidate list is visible
        assert editor.candidate_list is not None, "Candidate list should exist"
        assert editor.candidate_list.is_visible, "Candidate list should be visible"
        
        # Verify candidates are shown (abc.txt, abcd.txt, abcde.txt)
        candidates = editor.candidate_list.candidates
        print(f"  Candidates: {candidates}")
        assert len(candidates) >= 3, f"Should have at least 3 candidates, got {len(candidates)}"
        assert any("abc" in c for c in candidates), "Should have abc candidates"
        
        # Verify no focus initially
        assert editor.candidate_list.focused_index is None, "No candidate should be focused initially"
        
        # Step 2: Press Down arrow to focus first candidate
        print("Step 2: Pressing Down arrow (focus first)...")
        down_event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0)
        result = editor.handle_key(down_event)
        
        assert result, "Down arrow should be handled"
        assert editor.candidate_list.focused_index == 0, "First candidate should be focused"
        print(f"  Focused candidate: {editor.candidate_list.get_focused_candidate()}")
        
        # Step 3: Press Down arrow again to focus second candidate
        print("Step 3: Pressing Down arrow (focus second)...")
        result = editor.handle_key(down_event)
        
        assert result, "Down arrow should be handled"
        assert editor.candidate_list.focused_index == 1, "Second candidate should be focused"
        print(f"  Focused candidate: {editor.candidate_list.get_focused_candidate()}")
        
        # Step 4: Press Enter to select focused candidate
        print("Step 4: Pressing Enter to select...")
        focused_candidate = editor.candidate_list.get_focused_candidate()
        enter_event = KeyEvent(key_code=KeyCode.ENTER, modifiers=0)
        result = editor.handle_key(enter_event)
        
        assert result, "Enter should be handled"
        
        # Verify candidate was applied
        text = editor.get_text()
        print(f"  Final text: {text}")
        assert focused_candidate in text, f"Text should contain selected candidate: {focused_candidate}"
        
        # Verify focus is cleared (even though list may re-open)
        assert editor.candidate_list.focused_index is None, "Focus should be cleared"
        
        # Note: Candidate list may re-open with new candidates based on the selected text
        # This is the new behavior - the list automatically updates after selection
        
        print("✓ TAB → Down → Down → Enter workflow passed")
    
    def test_workflow_tab_up_esc(self):
        """
        Test complete workflow: TAB → Up → ESC
        
        Validates:
        - TAB triggers completion
        - Up arrow focuses last candidate (wrapping)
        - ESC dismisses without applying
        - Requirements: 9.2, 9.4, 9.6, 11.1, 11.2, 11.3
        """
        print("\n=== Testing TAB → Up → ESC workflow ===")
        
        # Create editor with filepath completer
        completer = FilepathCompleter(self.test_dir)
        editor = SingleLineTextEdit(
            initial_text="ab",
            renderer=self.mock_renderer,
            completer=completer
        )
        editor.move_cursor_end()
        
        # Step 1: Press TAB to trigger completion
        print("Step 1: Pressing TAB...")
        tab_event = KeyEvent(key_code=KeyCode.TAB, modifiers=0)
        result = editor.handle_key(tab_event)
        
        assert result, "TAB key should be handled"
        
        # Trigger draw to render candidate list
        editor.draw(self.mock_renderer, 10, 0, 80, "", True)
        
        assert editor.candidate_list.is_visible, "Candidate list should be visible"
        
        candidates = editor.candidate_list.candidates
        print(f"  Candidates: {candidates}")
        assert len(candidates) >= 3, "Should have multiple candidates"
        
        # Save text after TAB (may have inserted common prefix)
        text_after_tab = editor.get_text()
        
        # Step 2: Press Up arrow to focus last candidate (wrapping)
        print("Step 2: Pressing Up arrow (wrap to last)...")
        up_event = KeyEvent(key_code=KeyCode.UP, modifiers=0)
        result = editor.handle_key(up_event)
        
        assert result, "Up arrow should be handled"
        expected_index = len(candidates) - 1
        assert editor.candidate_list.focused_index == expected_index, \
            f"Last candidate should be focused (index {expected_index})"
        print(f"  Focused candidate: {editor.candidate_list.get_focused_candidate()}")
        
        # Step 3: Press ESC to dismiss without applying
        print("Step 3: Pressing ESC to dismiss...")
        esc_event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=0)
        result = editor.handle_key(esc_event)
        
        assert result, "ESC should be handled"
        
        # Verify text is unchanged from after TAB (ESC doesn't revert TAB completion)
        assert editor.get_text() == text_after_tab, \
            f"Text should be unchanged after ESC: expected '{text_after_tab}', got '{editor.get_text()}'"
        
        # Verify candidate list is hidden
        assert not editor.candidate_list.is_visible, "Candidate list should be hidden"
        
        # Verify focus is cleared
        assert editor.candidate_list.focused_index is None, "Focus should be cleared"
        
        print("✓ TAB → Up → ESC workflow passed")
    
    def test_scrolling_with_long_candidate_list(self):
        """
        Test scrolling behavior with many candidates
        
        Validates:
        - Scrollbar appears when candidates exceed visible area
        - Auto-scroll keeps focused candidate visible
        - Scrollbar position updates correctly
        - Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6
        """
        print("\n=== Testing scrolling with long candidate list ===")
        
        # Create editor with filepath completer
        completer = FilepathCompleter(self.test_dir)
        editor = SingleLineTextEdit(
            initial_text="file",
            renderer=self.mock_renderer,
            completer=completer
        )
        editor.move_cursor_end()
        
        # Trigger completion to show many candidates (file00.txt through file14.txt)
        print("Step 1: Triggering completion with many candidates...")
        tab_event = KeyEvent(key_code=KeyCode.TAB, modifiers=0)
        editor.handle_key(tab_event)
        
        # Trigger draw to render candidate list
        editor.draw(self.mock_renderer, 10, 0, 80, "", True)
        
        candidates = editor.candidate_list.candidates
        print(f"  Total candidates: {len(candidates)}")
        assert len(candidates) >= 10, "Should have many candidates for scrolling test"
        
        # Check if scrollbar should be visible
        visible_count = editor.candidate_list.max_visible_candidates
        print(f"  Visible candidates: {visible_count}")
        
        if len(candidates) > visible_count:
            print("  Scrollbar should be visible")
            # Note: We can't directly test scrollbar rendering without a real renderer,
            # but we can verify the scroll state
        
        # Step 2: Navigate down through candidates
        print("Step 2: Navigating down through candidates...")
        down_event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0)
        
        # Focus first candidate
        editor.handle_key(down_event)
        assert editor.candidate_list.focused_index == 0
        initial_scroll = editor.candidate_list.scroll_offset
        print(f"  Initial scroll offset: {initial_scroll}")
        
        # Navigate down multiple times to trigger scrolling
        for i in range(visible_count + 2):
            editor.handle_key(down_event)
        
        # Verify scroll offset has changed
        new_scroll = editor.candidate_list.scroll_offset
        print(f"  New scroll offset: {new_scroll}")
        
        if len(candidates) > visible_count:
            assert new_scroll > initial_scroll, "Scroll offset should increase when navigating down"
        
        # Verify focused candidate is still within valid range
        focused_idx = editor.candidate_list.focused_index
        assert 0 <= focused_idx < len(candidates), \
            f"Focused index {focused_idx} should be within range [0, {len(candidates)})"
        
        # Step 3: Navigate up to test upward scrolling
        print("Step 3: Navigating up to test upward scrolling...")
        up_event = KeyEvent(key_code=KeyCode.UP, modifiers=0)
        
        for i in range(visible_count + 2):
            editor.handle_key(up_event)
        
        # Verify scroll offset decreased
        final_scroll = editor.candidate_list.scroll_offset
        print(f"  Final scroll offset: {final_scroll}")
        
        if len(candidates) > visible_count:
            assert final_scroll < new_scroll, "Scroll offset should decrease when navigating up"
        
        print("✓ Scrolling with long candidate list passed")
    
    def test_focus_wrapping_at_boundaries(self):
        """
        Test focus wrapping at list boundaries
        
        Validates:
        - Down wraps from last to first
        - Up wraps from first to last
        - Wrapping works correctly with scrolling
        - Requirements: 9.3, 9.4, 9.5, 9.6
        """
        print("\n=== Testing focus wrapping at boundaries ===")
        
        # Create editor with filepath completer
        completer = FilepathCompleter(self.test_dir)
        editor = SingleLineTextEdit(
            initial_text="ab",
            renderer=self.mock_renderer,
            completer=completer
        )
        editor.move_cursor_end()
        
        # Trigger completion
        print("Step 1: Triggering completion...")
        tab_event = KeyEvent(key_code=KeyCode.TAB, modifiers=0)
        editor.handle_key(tab_event)
        
        # Trigger draw to render candidate list
        editor.draw(self.mock_renderer, 10, 0, 80, "", True)
        
        candidates = editor.candidate_list.candidates
        num_candidates = len(candidates)
        print(f"  Total candidates: {num_candidates}")
        assert num_candidates >= 3, "Need at least 3 candidates for wrapping test"
        
        # Test Down wrapping: no focus → first
        print("Step 2: Testing Down from no focus → first...")
        down_event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0)
        editor.handle_key(down_event)
        
        assert editor.candidate_list.focused_index == 0, "Down from no focus should focus first"
        print(f"  Focused: {editor.candidate_list.get_focused_candidate()}")
        
        # Test Up wrapping: first → last
        print("Step 3: Testing Up from first → last...")
        up_event = KeyEvent(key_code=KeyCode.UP, modifiers=0)
        editor.handle_key(up_event)
        
        expected_last = num_candidates - 1
        assert editor.candidate_list.focused_index == expected_last, \
            f"Up from first should wrap to last (index {expected_last})"
        print(f"  Focused: {editor.candidate_list.get_focused_candidate()}")
        
        # Test Down wrapping: last → first
        print("Step 4: Testing Down from last → first...")
        editor.handle_key(down_event)
        
        assert editor.candidate_list.focused_index == 0, "Down from last should wrap to first"
        print(f"  Focused: {editor.candidate_list.get_focused_candidate()}")
        
        # Test Up wrapping: no focus → last
        print("Step 5: Testing Up from no focus → last...")
        editor.candidate_list.clear_focus()
        assert editor.candidate_list.focused_index is None, "Focus should be cleared"
        
        editor.handle_key(up_event)
        assert editor.candidate_list.focused_index == expected_last, \
            f"Up from no focus should focus last (index {expected_last})"
        print(f"  Focused: {editor.candidate_list.get_focused_candidate()}")
        
        print("✓ Focus wrapping at boundaries passed")
    
    def test_visual_feedback_at_each_step(self):
        """
        Test that visual feedback is provided at each step
        
        Validates:
        - Candidate list appears after TAB
        - Focus highlighting changes with navigation
        - Candidate list disappears after selection/dismissal
        - Requirements: 2.1, 9.7, 10.2, 11.1
        """
        print("\n=== Testing visual feedback at each step ===")
        
        # Create editor with filepath completer
        completer = FilepathCompleter(self.test_dir)
        editor = SingleLineTextEdit(
            initial_text="ab",
            renderer=self.mock_renderer,
            completer=completer
        )
        editor.move_cursor_end()
        
        # Step 1: Verify no candidate list initially
        print("Step 1: Verifying initial state...")
        assert editor.candidate_list is not None, "Candidate list object should exist"
        assert not editor.candidate_list.is_visible, "Candidate list should not be visible initially"
        assert editor.candidate_list.focused_index is None, "No focus initially"
        print("  ✓ Initial state correct")
        
        # Step 2: Press TAB and verify candidate list appears
        print("Step 2: Pressing TAB and verifying candidate list appears...")
        tab_event = KeyEvent(key_code=KeyCode.TAB, modifiers=0)
        editor.handle_key(tab_event)
        
        # Trigger draw to render candidate list
        editor.draw(self.mock_renderer, 10, 0, 80, "", True)
        
        assert editor.candidate_list.is_visible, "Candidate list should be visible after TAB"
        assert len(editor.candidate_list.candidates) > 0, "Should have candidates"
        assert editor.candidate_list.focused_index is None, "No focus yet"
        print(f"  ✓ Candidate list visible with {len(editor.candidate_list.candidates)} candidates")
        
        # Step 3: Press Down and verify focus changes
        print("Step 3: Pressing Down and verifying focus...")
        down_event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0)
        editor.handle_key(down_event)
        
        assert editor.candidate_list.focused_index == 0, "First candidate should be focused"
        first_focused = editor.candidate_list.get_focused_candidate()
        print(f"  ✓ First candidate focused: {first_focused}")
        
        # Step 4: Press Down again and verify focus moves
        print("Step 4: Pressing Down again and verifying focus moves...")
        editor.handle_key(down_event)
        
        assert editor.candidate_list.focused_index == 1, "Second candidate should be focused"
        second_focused = editor.candidate_list.get_focused_candidate()
        assert second_focused != first_focused, "Focused candidate should change"
        print(f"  ✓ Second candidate focused: {second_focused}")
        
        # Step 5: Press ESC and verify candidate list disappears
        print("Step 5: Pressing ESC and verifying candidate list disappears...")
        esc_event = KeyEvent(key_code=KeyCode.ESCAPE, modifiers=0)
        editor.handle_key(esc_event)
        
        assert not editor.candidate_list.is_visible, "Candidate list should be hidden after ESC"
        assert editor.candidate_list.focused_index is None, "Focus should be cleared"
        print("  ✓ Candidate list hidden and focus cleared")
        
        # Step 6: Trigger again and test Enter selection
        print("Step 6: Testing Enter selection...")
        editor.handle_key(tab_event)
        
        # Trigger draw to render candidate list
        editor.draw(self.mock_renderer, 10, 0, 80, "", True)
        
        assert editor.candidate_list.is_visible, "Candidate list should reappear"
        
        editor.handle_key(down_event)
        assert editor.candidate_list.focused_index == 0, "First candidate focused"
        
        enter_event = KeyEvent(key_code=KeyCode.ENTER, modifiers=0)
        editor.handle_key(enter_event)
        
        # Note: Candidate list may re-open with new candidates based on the selected text
        # This is the new behavior - the list automatically updates after selection
        assert editor.candidate_list.focused_index is None, "Focus should be cleared"
        print("  ✓ Focus cleared after selection (list may re-open with new candidates)")
        
        print("✓ Visual feedback at each step passed")
    
    def test_complex_navigation_sequence(self):
        """
        Test a complex navigation sequence combining multiple operations
        
        Validates:
        - Multiple TAB presses
        - Mixed Up/Down navigation
        - Text editing during completion
        - Requirements: All keyboard navigation requirements
        """
        print("\n=== Testing complex navigation sequence ===")
        
        # Create editor with filepath completer
        completer = FilepathCompleter(self.test_dir)
        editor = SingleLineTextEdit(
            initial_text="",
            renderer=self.mock_renderer,
            completer=completer
        )
        
        # Step 1: Type partial text
        print("Step 1: Typing 'ab'...")
        editor.insert_char('a')
        editor.insert_char('b')
        assert editor.get_text() == "ab"
        
        # Step 2: Press TAB
        print("Step 2: Pressing TAB...")
        tab_event = KeyEvent(key_code=KeyCode.TAB, modifiers=0)
        editor.handle_key(tab_event)
        
        # Trigger draw to render candidate list
        editor.draw(self.mock_renderer, 10, 0, 80, "", True)
        
        assert editor.candidate_list.is_visible, "Candidate list should be visible after TAB"
        
        # Step 3: Navigate down twice
        print("Step 3: Navigating down twice...")
        down_event = KeyEvent(key_code=KeyCode.DOWN, modifiers=0)
        editor.handle_key(down_event)
        editor.handle_key(down_event)
        assert editor.candidate_list.focused_index == 1
        
        # Step 4: Navigate up once
        print("Step 4: Navigating up once...")
        up_event = KeyEvent(key_code=KeyCode.UP, modifiers=0)
        editor.handle_key(up_event)
        assert editor.candidate_list.focused_index == 0
        
        # Step 5: Type additional character (should update candidates)
        print("Step 5: Typing 'c' to filter...")
        char_event = CharEvent(char='c')
        editor.handle_key(char_event)
        
        print(f"  Text after typing 'c': '{editor.get_text()}'")
        print(f"  Cursor position: {editor.get_cursor_pos()}")
        
        # Trigger draw to update candidate list
        editor.draw(self.mock_renderer, 10, 0, 80, "", True)
        
        # Check if there are still matching candidates
        if editor.completer:
            candidates_after_typing = editor.completer.get_candidates(editor.get_text(), editor.get_cursor_pos())
            print(f"  Candidates after typing: {candidates_after_typing}")
        
        # Candidate list should still be visible if there are matching candidates
        # If no candidates match, the list will be hidden (which is correct behavior)
        if candidates_after_typing:
            assert editor.candidate_list.is_visible, "Candidate list should still be visible after typing"
        else:
            print("  No matching candidates after typing 'c' - list correctly hidden")
            assert not editor.candidate_list.is_visible, "Candidate list should be hidden when no matches"
        new_candidates = editor.candidate_list.candidates
        print(f"  New candidates after typing 'c': {new_candidates}")
        
        # Step 6: Navigate and select
        print("Step 6: Navigating and selecting...")
        editor.handle_key(down_event)
        
        enter_event = KeyEvent(key_code=KeyCode.ENTER, modifiers=0)
        editor.handle_key(enter_event)
        
        # Verify selection was applied
        final_text = editor.get_text()
        print(f"  Final text: {final_text}")
        assert len(final_text) > 3, "Text should be longer after selection"
        assert not editor.candidate_list.is_visible, "Candidate list should be hidden"
        
        print("✓ Complex navigation sequence passed")


if __name__ == '__main__':
    unittest.main()
