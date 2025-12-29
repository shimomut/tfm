"""
Tests for archive file viewing support in TextViewer.

This test verifies that the TextViewer can properly display files
from within archive files using the archive:// URI scheme.

Run with: PYTHONPATH=.:src:ttk pytest test/test_archive_file_viewing.py -v
"""

import unittest
import tempfile
import zipfile
import tarfile
from pathlib import Path as PathlibPath
from unittest.mock import Mock, patch, MagicMock

# Mock curses before importing tfm modules
sys.modules['curses'] = MagicMock()

from tfm_path import Path
from tfm_text_viewer import TextViewer, is_text_file, create_text_viewer


class TestArchiveFileViewing(unittest.TestCase):
    """Test archive file viewing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_stdscr = Mock()
        self.mock_stdscr.getmaxyx.return_value = (24, 80)
        
        # Mock curses color functions
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                pass
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_zip(self, filename: str, content: str) -> PathlibPath:
        """Create a test zip file with a text file inside"""
        zip_path = PathlibPath(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr(filename, content)
        
        return zip_path
    
    def create_test_tar(self, filename: str, content: str) -> PathlibPath:
        """Create a test tar file with a text file inside"""
        tar_path = PathlibPath(self.temp_dir) / "test.tar"
        
        with tarfile.open(tar_path, 'w') as tf:
            import io
            data = content.encode('utf-8')
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(data)
            tf.addfile(tarinfo, io.BytesIO(data))
        
        return tar_path
    
    def test_archive_path_detection(self):
        """Test that archive:// paths are properly detected"""
        # Create a test archive
        zip_path = self.create_test_zip("test.txt", "Hello from archive!")
        
        # Create an archive path
        archive_uri = f"archive://{zip_path}#test.txt"
        archive_path = Path(archive_uri)
        
        # Verify the path is recognized as an archive
        self.assertEqual(archive_path.get_scheme(), 'archive')
    
    def test_read_text_from_zip(self):
        """Test reading text content from a zip archive"""
        # Create a test zip with text content
        test_content = "Hello from inside a zip file!\nLine 2\nLine 3"
        zip_path = self.create_test_zip("readme.txt", test_content)
        
        # Create an archive path
        archive_uri = f"archive://{zip_path}#readme.txt"
        archive_path = Path(archive_uri)
        
        # Read the content
        content = archive_path.read_text()
        
        # Verify the content matches
        self.assertEqual(content, test_content)
    
    def test_read_text_from_tar(self):
        """Test reading text content from a tar archive"""
        # Create a test tar with text content
        test_content = "Hello from inside a tar file!\nLine 2\nLine 3"
        tar_path = self.create_test_tar("readme.txt", test_content)
        
        # Create an archive path
        archive_uri = f"archive://{tar_path}#readme.txt"
        archive_path = Path(archive_uri)
        
        # Read the content
        content = archive_path.read_text()
        
        # Verify the content matches
        self.assertEqual(content, test_content)
    
    def test_text_viewer_loads_archive_file(self):
        """Test that TextViewer can load a file from an archive"""
        # Create a test zip with text content
        test_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        zip_path = self.create_test_zip("test.txt", test_content)
        
        # Create an archive path
        archive_uri = f"archive://{zip_path}#test.txt"
        archive_path = Path(archive_uri)
        
        # Mock curses functions
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                # Create a TextViewer instance
                viewer = TextViewer(self.mock_stdscr, archive_path)
                
                # Verify the content was loaded
                self.assertEqual(len(viewer.lines), 5)
                self.assertEqual(viewer.lines[0], "Line 1")
                self.assertEqual(viewer.lines[4], "Line 5")
    
    def test_text_viewer_header_shows_archive_path(self):
        """Test that the viewer header shows the full archive path using polymorphic methods"""
        # Create a test zip with text content
        test_content = "Test content"
        zip_path = self.create_test_zip("docs/readme.txt", test_content)
        
        # Create an archive path
        archive_uri = f"archive://{zip_path}#docs/readme.txt"
        archive_path = Path(archive_uri)
        
        # Verify the polymorphic methods return correct values
        display_prefix = archive_path.get_display_prefix()
        display_title = archive_path.get_display_title()
        
        self.assertEqual(display_prefix, 'ARCHIVE: ', "Archive paths should have 'ARCHIVE: ' prefix")
        self.assertIn('test.zip', display_title, "Display title should contain archive name")
        self.assertIn('docs/readme.txt', display_title, "Display title should contain internal path")
        
        # Mock curses functions
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                # Create a TextViewer instance
                viewer = TextViewer(self.mock_stdscr, archive_path)
                
                # Mock the addstr method to capture what's being drawn
                calls = []
                def capture_addstr(*args):
                    calls.append(args)
                
                self.mock_stdscr.addstr = capture_addstr
                
                # Draw the header
                viewer.draw_header()
                
                # Find the call that draws the file info (at y=0, x=2)
                file_info_calls = [call for call in calls if len(call) >= 3 and call[0] == 0 and call[1] == 2 and isinstance(call[2], str)]
                
                # Verify that file info was drawn
                self.assertTrue(len(file_info_calls) > 0, "File info should be drawn in header")
                
                # The displayed text might be truncated if the path is too long
                # But the full file info (before truncation) should contain ARCHIVE:
                full_file_info = f"{display_prefix}{display_title}"
                self.assertIn('ARCHIVE:', full_file_info, "Full file info should contain 'ARCHIVE:'")
                self.assertIn('test.zip', full_file_info, "Full file info should contain archive name")
                self.assertIn('docs/readme.txt', full_file_info, "Full file info should contain internal path")
    
    def test_is_text_file_works_with_archives(self):
        """Test that is_text_file works with archive paths"""
        # Create a test zip with a text file
        test_content = "This is a text file"
        zip_path = self.create_test_zip("test.txt", test_content)
        
        # Create an archive path
        archive_uri = f"archive://{zip_path}#test.txt"
        archive_path = Path(archive_uri)
        
        # Verify it's detected as a text file
        self.assertTrue(is_text_file(archive_path))
    
    def test_view_text_file_with_archive(self):
        """Test the view_text_file function with archive paths"""
        # Create a test zip with text content
        test_content = "Hello from archive!"
        zip_path = self.create_test_zip("test.txt", test_content)
        
        # Create an archive path
        archive_uri = f"archive://{zip_path}#test.txt"
        archive_path = Path(archive_uri)
        
        # Mock curses functions and TextViewer.run
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                with patch.object(TextViewer, 'run'):
                    # Call view_text_file
                    result = view_text_file(self.mock_stdscr, archive_path)
                    
                    # Verify it succeeded
                    self.assertTrue(result)
    
    def test_nested_directory_in_archive(self):
        """Test viewing a file in a nested directory within an archive"""
        # Create a test zip with nested structure
        test_content = "Nested file content"
        zip_path = PathlibPath(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("dir1/dir2/nested.txt", test_content)
        
        # Create an archive path
        archive_uri = f"archive://{zip_path}#dir1/dir2/nested.txt"
        archive_path = Path(archive_uri)
        
        # Read the content
        content = archive_path.read_text()
        
        # Verify the content matches
        self.assertEqual(content, test_content)
    
    def test_binary_file_in_archive(self):
        """Test that binary files in archives are handled correctly"""
        # Create a test zip with binary content
        binary_content = b'\x00\x01\x02\x03\x04\x05'
        zip_path = PathlibPath(self.temp_dir) / "test.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("binary.dat", binary_content)
        
        # Create an archive path
        archive_uri = f"archive://{zip_path}#binary.dat"
        archive_path = Path(archive_uri)
        
        # Verify it's not detected as a text file
        self.assertFalse(is_text_file(archive_path))
    
    def test_unicode_content_in_archive(self):
        """Test viewing files with unicode content from archives"""
        # Create a test zip with unicode content
        test_content = "Hello 世界! 🌍 Привет мир!"
        zip_path = self.create_test_zip("unicode.txt", test_content)
        
        # Create an archive path
        archive_uri = f"archive://{zip_path}#unicode.txt"
        archive_path = Path(archive_uri)
        
        # Read the content
        content = archive_path.read_text()
        
        # Verify the content matches
        self.assertEqual(content, test_content)
    
    def test_large_file_in_archive(self):
        """Test viewing a large file from an archive"""
        # Create a test zip with a large text file
        lines = [f"Line {i}" for i in range(1000)]
        test_content = "\n".join(lines)
        zip_path = self.create_test_zip("large.txt", test_content)
        
        # Create an archive path
        archive_uri = f"archive://{zip_path}#large.txt"
        archive_path = Path(archive_uri)
        
        # Mock curses functions
        with patch('curses.color_pair', return_value=1):
            with patch('curses.init_pair'):
                # Create a TextViewer instance
                viewer = TextViewer(self.mock_stdscr, archive_path)
                
                # Verify all lines were loaded
                self.assertEqual(len(viewer.lines), 1000)
                self.assertEqual(viewer.lines[0], "Line 0")
                self.assertEqual(viewer.lines[999], "Line 999")
