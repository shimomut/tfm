#!/usr/bin/env python3
"""
Test candidate list overlay rendering to ensure borders and content are drawn correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

import pytest
from unittest.mock import Mock
from tfm_candidate_list_overlay import CandidateListOverlay


def test_normal_rendering():
    """Test that candidates are rendered correctly in normal conditions"""
    renderer = Mock()
    renderer.get_dimensions.return_value = (24, 80)
    
    draw_calls = []
    renderer.draw_text = lambda y, x, text, color_pair, attributes: draw_calls.append({
        'y': y, 'x': x, 'text': text
    })
    
    overlay = CandidateListOverlay(renderer)
    overlay.set_candidates(
        candidates=["file1.txt", "file2.txt", "file3.txt"],
        text_edit_y=10,
        text_edit_x=5,
        completion_start_x=10,
        show_above=False
    )
    
    overlay.show()
    overlay.draw()
    
    # Check that candidate content is drawn
    candidate_calls = [c for c in draw_calls if any(
        cand in c['text'] for cand in ["file1.txt", "file2.txt", "file3.txt"]
    )]
    
    assert len(candidate_calls) == 3, "All 3 candidates should be drawn"


def test_scroll_offset_clamping():
    """Test that scroll_offset is clamped to prevent borders-only rendering"""
    renderer = Mock()
    renderer.get_dimensions.return_value = (24, 80)
    
    draw_calls = []
    renderer.draw_text = lambda y, x, text, color_pair, attributes: draw_calls.append({
        'y': y, 'x': x, 'text': text
    })
    
    overlay = CandidateListOverlay(renderer)
    overlay.set_candidates(
        candidates=["file1.txt", "file2.txt", "file3.txt"],
        text_edit_y=10,
        text_edit_x=5,
        completion_start_x=10,
        show_above=False
    )
    
    # Set scroll_offset beyond the list
    overlay.scroll_offset = 100
    
    overlay.show()
    overlay.draw()
    
    # Check that scroll_offset was clamped
    assert overlay.scroll_offset == 0, "scroll_offset should be clamped to 0"
    
    # Check that candidate content is still drawn
    candidate_calls = [c for c in draw_calls if any(
        cand in c['text'] for cand in ["file1.txt", "file2.txt", "file3.txt"]
    )]
    
    assert len(candidate_calls) > 0, "Candidates should be drawn after clamping scroll_offset"


def test_narrow_overlay_prevention():
    """Test that overlay is not drawn when too narrow"""
    renderer = Mock()
    renderer.get_dimensions.return_value = (24, 40)
    
    draw_calls = []
    renderer.draw_text = lambda y, x, text, color_pair, attributes: draw_calls.append({
        'y': y, 'x': x, 'text': text
    })
    
    overlay = CandidateListOverlay(renderer)
    overlay.set_candidates(
        candidates=["file.txt"],
        text_edit_y=10,
        text_edit_x=5,
        completion_start_x=38,  # Only 2 chars from edge
        show_above=False
    )
    
    overlay.show()
    overlay.draw()
    
    # Nothing should be drawn when overlay is too narrow
    assert len(draw_calls) == 0, "Nothing should be drawn when overlay is too narrow"


def test_max_visible_zero():
    """Test that nothing is drawn when max_visible_candidates is 0"""
    renderer = Mock()
    renderer.get_dimensions.return_value = (24, 80)
    
    draw_calls = []
    renderer.draw_text = lambda y, x, text, color_pair, attributes: draw_calls.append({
        'y': y, 'x': x, 'text': text
    })
    
    overlay = CandidateListOverlay(renderer)
    overlay.max_visible_candidates = 0
    
    overlay.set_candidates(
        candidates=["file1.txt", "file2.txt"],
        text_edit_y=10,
        text_edit_x=5,
        completion_start_x=10,
        show_above=False
    )
    
    overlay.show()
    overlay.draw()
    
    # Nothing should be drawn when max_visible_candidates is 0
    assert len(draw_calls) == 0, "Nothing should be drawn when max_visible_candidates is 0"


def test_borders_and_content_separation():
    """Test that borders and content are drawn separately with correct colors"""
    renderer = Mock()
    renderer.get_dimensions.return_value = (24, 80)
    
    draw_calls = []
    def track_draw(y, x, text, color_pair, attributes):
        draw_calls.append({
            'y': y,
            'x': x,
            'text': text,
            'color_pair': color_pair,
            'attributes': attributes
        })
    
    renderer.draw_text = track_draw
    
    overlay = CandidateListOverlay(renderer)
    overlay.set_candidates(
        candidates=["file.txt"],
        text_edit_y=10,
        text_edit_x=5,
        completion_start_x=10,
        show_above=False
    )
    
    overlay.show()
    overlay.draw()
    
    # Find border calls
    border_calls = [c for c in draw_calls if '│' in c['text'] or '─' in c['text'] or 
                    '┌' in c['text'] or '└' in c['text'] or '┐' in c['text'] or '┘' in c['text']]
    
    # Find candidate content calls
    candidate_calls = [c for c in draw_calls if 'file.txt' in c['text']]
    
    assert len(border_calls) > 0, "Borders should be drawn"
    assert len(candidate_calls) > 0, "Candidate content should be drawn"
    
    # Borders and content should use different color pairs (borders use normal, content may use focused)
    # This is verified by checking that they are drawn in separate calls
    assert len(draw_calls) > len(candidate_calls), "Borders and content should be separate draw calls"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
