#!/usr/bin/env python3
"""
Integration test for archive file viewing in FileManager.

This test verifies that the complete flow of browsing archives and
viewing files works correctly.
"""

import unittest
import tempfile
import zipfile
import os
import sys
from pathlib import Path as PathlibPath
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock curses before importing tfm modules
sys.modules['curses'] = MagicMock()

from tfm_path import Path
from tfm_text_viewer import TextViewer, is_text_file, create_text_viewer


class TestArchiveViewerIntegration(unittest.TestCase):
    """Integration tests for archive file viewing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_stdscr = Mock()
        self.mock_stdscr.getmaxyx.return_value = (24, 80)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_archive(self):
        """Create a test archive with various files"""
        zip_path = PathlibPath(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add various test files
            zf.writestr("readme.txt", "This is a readme file")
            zf.writestr("docs/guide.txt", "This is a guide")
            zf.writestr("src/main.py", "#!/usr/bin/env python3\nprint('Hello')")
            zf.writestr("config.json", '{"key": "value"}')
        
        return zip_path
    
    def test_complete_viewing_flow(self):
        """Test the complete flow of viewing a file from an archive"""
        # Create test archive
        zip_path = self.create_test_archive()
        
        # Step 1: Create archive path for a file
        archive_uri = f"archive://{zip_path}#readme.txt"
        archive_path = Path(archive_uri)
        
        # Step 2: Verify the file exists
        self.assertTrue(archive_path.exists())
        self.assertTrue(archive_path.is_file())
        
        # Step 3: Verify it's detected as a text file
        self.assertTrue(is_text_file(archive_path))
        
        # Step 4: Create a TextViewer and verify content is loaded
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                viewer = TextViewer(self.mock_stdscr, archive_path)
                
                # Verify content was loaded
                self.assertEqual(len(viewer.lines), 1)
                self.assertEqual(viewer.lines[0], "This is a readme file")
        
        # Step 5: Verify view_text_file works
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                with patch.object(TextViewer, 'run'):
                    result = view_text_file(self.mock_stdscr, archive_path)
                    self.assertTrue(result)
    
    def test_viewing_nested_file(self):
        """Test viewing a file in a nested directory"""
        # Create test archive
        zip_path = self.create_test_archive()
        
        # Create archive path for nested file
        archive_uri = f"archive://{zip_path}#docs/guide.txt"
        archive_path = Path(archive_uri)
        
        # Verify the file exists
        self.assertTrue(archive_path.exists())
        
        # Create viewer and verify content
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                viewer = TextViewer(self.mock_stdscr, archive_path)
                
                self.assertEqual(len(viewer.lines), 1)
                self.assertEqual(viewer.lines[0], "This is a guide")
    
    def test_viewing_python_file_with_syntax_highlighting(self):
        """Test viewing a Python file with syntax highlighting"""
        # Create test archive
        zip_path = self.create_test_archive()
        
        # Create archive path for Python file
        archive_uri = f"archive://{zip_path}#src/main.py"
        archive_path = Path(archive_uri)
        
        # Create viewer
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                viewer = TextViewer(self.mock_stdscr, archive_path)
                
                # Verify content was loaded
                self.assertEqual(len(viewer.lines), 2)
                self.assertEqual(viewer.lines[0], "#!/usr/bin/env python3")
                self.assertEqual(viewer.lines[1], "print('Hello')")
                
                # Verify syntax highlighting was applied (if pygments available)
                if viewer.syntax_highlighting:
                    self.assertTrue(len(viewer.highlighted_lines) > 0)
    
    def test_header_shows_archive_path(self):
        """Test that the viewer header correctly shows the archive path using polymorphic methods"""
        # Create test archive
        zip_path = self.create_test_archive()
        
        # Create archive path
        archive_uri = f"archive://{zip_path}#docs/guide.txt"
        archive_path = Path(archive_uri)
        
        # Verify the polymorphic methods return correct values
        display_prefix = archive_path.get_display_prefix()
        display_title = archive_path.get_display_title()
        
        self.assertEqual(display_prefix, 'ARCHIVE: ', "Archive paths should have 'ARCHIVE: ' prefix")
        self.assertIn('test.zip', display_title, "Display title should contain archive name")
        self.assertIn('docs/guide.txt', display_title, "Display title should contain internal path")
        
        # Create viewer
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                viewer = TextViewer(self.mock_stdscr, archive_path)
                
                # Mock addstr to capture header content
                calls = []
                def capture_addstr(*args):
                    calls.append(args)
                
                self.mock_stdscr.addstr = capture_addstr
                
                # Draw header
                viewer.draw_header()
                
                # The full file info (before truncation) should contain ARCHIVE:
                full_file_info = f"{display_prefix}{display_title}"
                self.assertIn('ARCHIVE:', full_file_info, "Full file info should contain 'ARCHIVE:'")
                self.assertIn('test.zip', full_file_info, "Full file info should contain archive name")
                self.assertIn('docs/guide.txt', full_file_info, "Full file info should contain internal path")
                
                # Verify that header was drawn (at y=0, x=2)
                header_calls = [call for call in calls if len(call) >= 3 and call[0] == 0 and call[1] == 2 and isinstance(call[2], str)]
                self.assertTrue(len(header_calls) > 0, "Header should be drawn")
    
    def test_multiple_files_in_same_archive(self):
        """Test viewing multiple files from the same archive"""
        # Create test archive
        zip_path = self.create_test_archive()
        
        # View first file
        archive_uri1 = f"archive://{zip_path}#readme.txt"
        archive_path1 = Path(archive_uri1)
        
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                viewer1 = TextViewer(self.mock_stdscr, archive_path1)
                self.assertEqual(viewer1.lines[0], "This is a readme file")
        
        # View second file
        archive_uri2 = f"archive://{zip_path}#docs/guide.txt"
        archive_path2 = Path(archive_uri2)
        
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                viewer2 = TextViewer(self.mock_stdscr, archive_path2)
                self.assertEqual(viewer2.lines[0], "This is a guide")
    
    def test_error_handling_for_nonexistent_file(self):
        """Test error handling when trying to view a nonexistent file in archive"""
        # Create test archive
        zip_path = self.create_test_archive()
        
        # Create archive path for nonexistent file
        archive_uri = f"archive://{zip_path}#nonexistent.txt"
        archive_path = Path(archive_uri)
        
        # Verify the file doesn't exist
        self.assertFalse(archive_path.exists())
        
        # Try to create viewer - should handle error gracefully
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                viewer = TextViewer(self.mock_stdscr, archive_path)
                
                # Should have error message in lines
                self.assertTrue(len(viewer.lines) > 0)
                # Error message should be present
                error_found = any('not found' in line.lower() or 'error' in line.lower() 
                                for line in viewer.lines)
                self.assertTrue(error_found)


if __name__ == '__main__':
    unittest.main()
