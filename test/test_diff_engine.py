"""
Unit tests for DiffEngine class.

Tests the core functionality of building tree structures and classifying differences.

Run with: PYTHONPATH=.:src:ttk pytest test/test_diff_engine.py -v
"""

import unittest
import tempfile
from pathlib import Path as StdPath

# Add src to path for imports
from tfm_directory_diff_viewer import DiffEngine, FileInfo, DifferenceType, TreeNode
from tfm_path import Path


class TestDiffEngine(unittest.TestCase):
    """Test cases for DiffEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.left_dir = StdPath(self.temp_dir) / "left"
        self.right_dir = StdPath(self.temp_dir) / "right"
        self.left_dir.mkdir()
        self.right_dir.mkdir()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_build_tree_with_identical_files(self):
        """Test building tree with identical files on both sides."""
        # Create identical files
        (self.left_dir / "file1.txt").write_text("content")
        (self.right_dir / "file1.txt").write_text("content")
        
        # Create file info dictionaries
        left_files = {
            "file1.txt": FileInfo(
                path=Path(str(self.left_dir / "file1.txt")),
                relative_path="file1.txt",
                is_directory=False,
                size=7,
                mtime=0.0,
                is_accessible=True
            )
        }
        right_files = {
            "file1.txt": FileInfo(
                path=Path(str(self.right_dir / "file1.txt")),
                relative_path="file1.txt",
                is_directory=False,
                size=7,
                mtime=0.0,
                is_accessible=True
            )
        }
        
        # Build tree
        engine = DiffEngine(left_files, right_files)
        root = engine.build_tree()
        
        # Verify tree structure
        self.assertEqual(len(root.children), 1)
        self.assertEqual(root.children[0].name, "file1.txt")
        self.assertEqual(root.children[0].difference_type, DifferenceType.IDENTICAL)
    
    def test_classify_only_left(self):
        """Test classification of files that exist only on left side."""
        left_files = {
            "only_left.txt": FileInfo(
                path=Path(str(self.left_dir / "only_left.txt")),
                relative_path="only_left.txt",
                is_directory=False,
                size=0,
                mtime=0.0,
                is_accessible=True
            )
        }
        right_files = {}
        
        engine = DiffEngine(left_files, right_files)
        root = engine.build_tree()
        
        self.assertEqual(len(root.children), 1)
        self.assertEqual(root.children[0].difference_type, DifferenceType.ONLY_LEFT)
    
    def test_classify_only_right(self):
        """Test classification of files that exist only on right side."""
        left_files = {}
        right_files = {
            "only_right.txt": FileInfo(
                path=Path(str(self.right_dir / "only_right.txt")),
                relative_path="only_right.txt",
                is_directory=False,
                size=0,
                mtime=0.0,
                is_accessible=True
            )
        }
        
        engine = DiffEngine(left_files, right_files)
        root = engine.build_tree()
        
        self.assertEqual(len(root.children), 1)
        self.assertEqual(root.children[0].difference_type, DifferenceType.ONLY_RIGHT)
    
    def test_classify_content_different(self):
        """Test classification of files with different content."""
        # Create files with different content
        (self.left_dir / "diff.txt").write_text("left content")
        (self.right_dir / "diff.txt").write_text("right content")
        
        left_files = {
            "diff.txt": FileInfo(
                path=Path(str(self.left_dir / "diff.txt")),
                relative_path="diff.txt",
                is_directory=False,
                size=12,
                mtime=0.0,
                is_accessible=True
            )
        }
        right_files = {
            "diff.txt": FileInfo(
                path=Path(str(self.right_dir / "diff.txt")),
                relative_path="diff.txt",
                is_directory=False,
                size=13,
                mtime=0.0,
                is_accessible=True
            )
        }
        
        engine = DiffEngine(left_files, right_files)
        root = engine.build_tree()
        
        self.assertEqual(len(root.children), 1)
        self.assertEqual(root.children[0].difference_type, DifferenceType.CONTENT_DIFFERENT)
    
    def test_directory_contains_difference(self):
        """Test that directories are marked as containing differences when children differ."""
        # Create directory structure with differences
        (self.left_dir / "subdir").mkdir()
        (self.right_dir / "subdir").mkdir()
        (self.left_dir / "subdir" / "file.txt").write_text("left")
        (self.right_dir / "subdir" / "file.txt").write_text("right")
        
        left_files = {
            "subdir": FileInfo(
                path=Path(str(self.left_dir / "subdir")),
                relative_path="subdir",
                is_directory=True,
                size=0,
                mtime=0.0,
                is_accessible=True
            ),
            "subdir/file.txt": FileInfo(
                path=Path(str(self.left_dir / "subdir" / "file.txt")),
                relative_path="subdir/file.txt",
                is_directory=False,
                size=4,
                mtime=0.0,
                is_accessible=True
            )
        }
        right_files = {
            "subdir": FileInfo(
                path=Path(str(self.right_dir / "subdir")),
                relative_path="subdir",
                is_directory=True,
                size=0,
                mtime=0.0,
                is_accessible=True
            ),
            "subdir/file.txt": FileInfo(
                path=Path(str(self.right_dir / "subdir" / "file.txt")),
                relative_path="subdir/file.txt",
                is_directory=False,
                size=5,
                mtime=0.0,
                is_accessible=True
            )
        }
        
        engine = DiffEngine(left_files, right_files)
        root = engine.build_tree()
        
        # Find the subdir node
        subdir_node = root.children[0]
        self.assertEqual(subdir_node.name, "subdir")
        self.assertEqual(subdir_node.difference_type, DifferenceType.CONTAINS_DIFFERENCE)
        
        # Verify the file is marked as different
        file_node = subdir_node.children[0]
        self.assertEqual(file_node.difference_type, DifferenceType.CONTENT_DIFFERENT)
    
    def test_compare_file_content_identical(self):
        """Test file content comparison for identical files."""
        # Create identical files
        (self.left_dir / "same.txt").write_text("identical content")
        (self.right_dir / "same.txt").write_text("identical content")
        
        engine = DiffEngine({}, {})
        result = engine.compare_file_content(
            Path(str(self.left_dir / "same.txt")),
            Path(str(self.right_dir / "same.txt"))
        )
        
        self.assertTrue(result)
    
    def test_compare_file_content_different(self):
        """Test file content comparison for different files."""
        # Create different files
        (self.left_dir / "diff.txt").write_text("left content")
        (self.right_dir / "diff.txt").write_text("right content")
        
        engine = DiffEngine({}, {})
        result = engine.compare_file_content(
            Path(str(self.left_dir / "diff.txt")),
            Path(str(self.right_dir / "diff.txt"))
        )
        
        self.assertFalse(result)
    
    def test_compare_file_content_different_sizes(self):
        """Test file content comparison with different file sizes."""
        # Create files with different sizes
        (self.left_dir / "size1.txt").write_text("short")
        (self.right_dir / "size1.txt").write_text("much longer content")
        
        engine = DiffEngine({}, {})
        result = engine.compare_file_content(
            Path(str(self.left_dir / "size1.txt")),
            Path(str(self.right_dir / "size1.txt"))
        )
        
        self.assertFalse(result)
