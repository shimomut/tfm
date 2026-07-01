#!/usr/bin/env python3
"""
Tests for CandidateListOverlay class

Run with: PYTHONPATH=.:src:ttk pytest test/test_candidate_list_overlay.py -v
"""

import unittest
from unittest.mock import Mock, MagicMock
from tfm_candidate_list_overlay import CandidateListOverlay


class TestCandidateListOverlay(unittest.TestCase):
    """Test CandidateListOverlay functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_renderer = Mock()
        self.mock_renderer.get_dimensions.return_value = (24, 80)  # Standard terminal size
        self.overlay = CandidateListOverlay(self.mock_renderer)
    
    def test_initialization(self):
        """Test that overlay initializes with correct default state"""
        self.assertEqual(self.overlay.candidates, [])
        self.assertFalse(self.overlay.is_visible)
        self.assertEqual(self.overlay.text_edit_y, 0)
        self.assertEqual(self.overlay.text_edit_x, 0)
        self.assertEqual(self.overlay.completion_start_x, 0)
        self.assertFalse(self.overlay.show_above)
        self.assertEqual(self.overlay.max_visible_candidates, 10)
    
    def test_set_candidates(self):
        """Test setting candidates and position"""
        candidates = ["file1.txt", "file2.txt", "folder/"]
        self.overlay.set_candidates(candidates, text_edit_y=10, text_edit_x=5, 
                                    completion_start_x=15, show_above=False)
        
        self.assertEqual(self.overlay.candidates, candidates)
        self.assertEqual(self.overlay.text_edit_y, 10)
        self.assertEqual(self.overlay.text_edit_x, 5)
        self.assertEqual(self.overlay.completion_start_x, 15)
        self.assertFalse(self.overlay.show_above)
    
    def test_show_hide(self):
        """Test show and hide methods"""
        self.assertFalse(self.overlay.is_visible)
        
        self.overlay.show()
        self.assertTrue(self.overlay.is_visible)
        
        self.overlay.hide()
        self.assertFalse(self.overlay.is_visible)
    
    def test_draw_when_not_visible(self):
        """Test that draw does nothing when overlay is not visible"""
        self.overlay.set_candidates(["test"], 10, 5, 15, False)
        self.overlay.hide()
        
        self.overlay.draw()
        
        # Should not call draw_text when not visible
        self.mock_renderer.draw_text.assert_not_called()
    
    def test_draw_when_no_candidates(self):
        """Test that draw does nothing when there are no candidates"""
        self.overlay.set_candidates([], 10, 5, 15, False)
        self.overlay.show()
        
        self.overlay.draw()
        
        # Should not call draw_text when no candidates
        self.mock_renderer.draw_text.assert_not_called()
    
    def test_draw_with_candidates_below(self):
        """Test drawing candidates below text edit field"""
        candidates = ["file1.txt", "file2.txt", "folder/"]
        self.overlay.set_candidates(candidates, text_edit_y=10, text_edit_x=5, 
                                    completion_start_x=15, show_above=False)
        self.overlay.show()
        
        self.overlay.draw()
        
        # Should call draw_text multiple times (borders + candidates)
        self.assertGreater(self.mock_renderer.draw_text.call_count, 0)
    
    def test_draw_with_candidates_above(self):
        """Test drawing candidates above text edit field"""
        candidates = ["file1.txt", "file2.txt", "folder/"]
        self.overlay.set_candidates(candidates, text_edit_y=20, text_edit_x=5, 
                                    completion_start_x=15, show_above=True)
        self.overlay.show()
        
        self.overlay.draw()
        
        # Should call draw_text multiple times (borders + candidates)
        self.assertGreater(self.mock_renderer.draw_text.call_count, 0)
    
    def test_draw_with_many_candidates(self):
        """Test drawing with more candidates than max_visible_candidates"""
        # Create 15 candidates (more than default max of 10)
        candidates = [f"file{i}.txt" for i in range(15)]
        self.overlay.set_candidates(candidates, text_edit_y=10, text_edit_x=5, 
                                    completion_start_x=15, show_above=False)
        self.overlay.show()
        
        self.overlay.draw()
        
        # Should call draw_text multiple times
        # Should show overflow indicator in bottom border
        self.assertGreater(self.mock_renderer.draw_text.call_count, 0)
    
    def test_draw_respects_screen_boundaries(self):
        """Test that overlay respects screen boundaries"""
        # Set up overlay near bottom of screen
        candidates = ["file1.txt", "file2.txt", "folder/"]
        self.overlay.set_candidates(candidates, text_edit_y=22, text_edit_x=5, 
                                    completion_start_x=15, show_above=False)
        self.overlay.show()
        
        # Should not crash when drawing near screen edge
        self.overlay.draw()
        
        self.assertGreater(self.mock_renderer.draw_text.call_count, 0)
    
    def test_draw_respects_right_edge(self):
        """Test that overlay respects right edge of screen"""
        # Set up overlay near right edge
        candidates = ["very_long_filename_that_might_exceed_screen_width.txt"]
        self.overlay.set_candidates(candidates, text_edit_y=10, text_edit_x=5, 
                                    completion_start_x=70, show_above=False)
        self.overlay.show()
        
        # Should not crash when drawing near right edge
        self.overlay.draw()
        
        self.assertGreater(self.mock_renderer.draw_text.call_count, 0)


if __name__ == '__main__':
    unittest.main()
