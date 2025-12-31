#!/usr/bin/env python3
"""
Test batch rename emoji status indicators

Tests that BatchRenameDialog uses emoji status indicators to save space.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from tfm_batch_rename_dialog import BatchRenameDialog


class MockRenderer:
    """Mock renderer that captures draw_text calls"""
    def __init__(self):
        self.height = 40
        self.width = 120
        self.drawn_text = []
    
    def get_dimensions(self):
        return self.height, self.width
    
    def draw_text(self, y, x, text, color_pair=None, attributes=None):
        self.drawn_text.append({
            'y': y,
            'x': x,
            'text': text,
            'color_pair': color_pair,
            'attributes': attributes
        })
    
    def draw_hline(self, y, x, char, count, color_pair=None):
        pass
    
    def set_caret_position(self, x, y):
        pass


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def dialog():
    """Create a BatchRenameDialog instance for testing"""
    config = {}
    renderer = MockRenderer()
    return BatchRenameDialog(config, renderer)


def test_unchanged_files_use_circle_emoji(temp_dir, dialog):
    """Test that unchanged files show no status icon (just space)"""
    # Create test file
    file1 = temp_dir / "test.txt"
    file1.touch()
    
    # Show dialog
    dialog.show([file1])
    
    # No pattern - file unchanged
    dialog.regex_editor.set_text("")
    dialog.destination_editor.set_text("")
    dialog.update_preview()
    
    # Check preview data
    assert len(dialog.preview) == 1
    assert dialog.preview[0]['original'] == "test.txt"
    assert dialog.preview[0]['new'] == "test.txt"
    
    # Draw and verify no colored emoji for unchanged files
    dialog.renderer.drawn_text = []
    dialog.draw()
    
    # Verify no colored emojis (🟢 or 🔴) are present for unchanged files
    all_text = ' '.join([item['text'] for item in dialog.renderer.drawn_text])
    assert '🟢' not in all_text, "Green circle should not be present for unchanged files"
    assert '🔴' not in all_text, "Red circle should not be present for unchanged files"


def test_valid_rename_uses_checkmark_emoji(temp_dir, dialog):
    """Test that valid renames show green circle emoji (🟢)"""
    # Create test file
    file1 = temp_dir / "test.txt"
    file1.touch()
    
    # Show dialog
    dialog.show([file1])
    
    # Set pattern for valid rename
    dialog.regex_editor.set_text(r"test")
    dialog.destination_editor.set_text("result")
    dialog.update_preview()
    
    # Draw and check for green circle emoji
    dialog.renderer.drawn_text = []
    dialog.draw()
    
    # Find status text in drawn content
    status_texts = [item['text'] for item in dialog.renderer.drawn_text if '🟢' in item['text']]
    assert len(status_texts) > 0, "Green circle emoji (🟢) should be present for valid renames"


def test_conflict_uses_x_mark_emoji(temp_dir, dialog):
    """Test that conflicts show red circle emoji (🔴)"""
    # Create test files
    file1 = temp_dir / "test1.txt"
    file2 = temp_dir / "test2.txt"
    file1.touch()
    file2.touch()
    
    # Show dialog
    dialog.show([file1, file2])
    
    # Set pattern that creates conflict
    dialog.regex_editor.set_text(r"test\d")
    dialog.destination_editor.set_text("result")
    dialog.update_preview()
    
    # Draw and check for red circle emoji
    dialog.renderer.drawn_text = []
    dialog.draw()
    
    # Find status text in drawn content
    status_texts = [item['text'] for item in dialog.renderer.drawn_text if '🔴' in item['text']]
    assert len(status_texts) > 0, "Red circle emoji (🔴) should be present for conflicts"


def test_invalid_name_uses_x_mark_emoji(temp_dir, dialog):
    """Test that invalid names show red circle emoji (🔴)"""
    # Create test file
    file1 = temp_dir / "test.txt"
    file1.touch()
    
    # Show dialog
    dialog.show([file1])
    
    # Set pattern that creates invalid name (empty)
    dialog.regex_editor.set_text(r".*")
    dialog.destination_editor.set_text("")
    dialog.update_preview()
    
    # Draw and check for red circle emoji
    dialog.renderer.drawn_text = []
    dialog.draw()
    
    # Find status text in drawn content
    status_texts = [item['text'] for item in dialog.renderer.drawn_text if '🔴' in item['text']]
    assert len(status_texts) > 0, "Red circle emoji (🔴) should be present for invalid names"


def test_no_text_status_indicators(temp_dir, dialog):
    """Test that old text status indicators are not used"""
    # Create test files
    file1 = temp_dir / "test1.txt"
    file2 = temp_dir / "test2.txt"
    file1.touch()
    file2.touch()
    
    # Show dialog
    dialog.show([file1, file2])
    
    # Set pattern that creates conflict
    dialog.regex_editor.set_text(r"test\d")
    dialog.destination_editor.set_text("result")
    dialog.update_preview()
    
    # Draw and check that old text indicators are not present
    dialog.renderer.drawn_text = []
    dialog.draw()
    
    # Check that old text status indicators are not used
    all_text = ' '.join([item['text'] for item in dialog.renderer.drawn_text])
    assert 'UNCHANGED' not in all_text, "Old 'UNCHANGED' text should not be present"
    assert 'CONFLICT!' not in all_text, "Old 'CONFLICT!' text should not be present"
    assert 'INVALID!' not in all_text, "Old 'INVALID!' text should not be present"
    assert '[OK]' not in all_text, "Old '[OK]' text should not be present"


def test_emoji_status_saves_space(temp_dir, dialog):
    """Test that emoji status uses less space than text status"""
    # Create test file
    file1 = temp_dir / "test.txt"
    file1.touch()
    
    # Show dialog
    dialog.show([file1])
    
    # Set pattern for valid rename
    dialog.regex_editor.set_text(r"test")
    dialog.destination_editor.set_text("result")
    dialog.update_preview()
    
    # Draw and find status text
    dialog.renderer.drawn_text = []
    dialog.draw()
    
    # Find status indicators (only colored emojis, not spaces for unchanged)
    status_texts = [item for item in dialog.renderer.drawn_text 
                   if any(emoji in item['text'] for emoji in ['🟢', '🔴'])]
    
    # Verify status text is short (emoji + 2 spaces = 3-4 chars)
    for status_item in status_texts:
        # Status should be "🟢  " or "🔴  " (3-4 chars)
        assert len(status_item['text']) <= 4, f"Status text '{status_item['text']}' should be 4 chars or less"
