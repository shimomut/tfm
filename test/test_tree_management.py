"""
Unit tests for tree structure management in DirectoryDiffViewer.

Tests the expand_node, collapse_node, and visible node management functionality.

Run with: PYTHONPATH=.:src:ttk pytest test/test_tree_management.py -v
"""

import unittest
from src.tfm_directory_diff_viewer import TreeNode, DifferenceType


class TestTreeManagement(unittest.TestCase):
    """Test tree flattening and expand/collapse functionality."""
    
    def setUp(self):
        """Create a sample tree structure for testing."""
        # Create a simple tree:
        # root/
        #   dir1/
        #     file1.txt
        #     file2.txt
        #   dir2/
        #     subdir/
        #       file3.txt
        #   file4.txt
        
        self.root = TreeNode(
            name="root",
            left_path=None,
            right_path=None,
            is_directory=True,
            difference_type=DifferenceType.CONTAINS_DIFFERENCE,
            depth=0,
            is_expanded=True,
            children=[],
            parent=None
        )
        
        # dir1
        self.dir1 = TreeNode(
            name="dir1",
            left_path=None,
            right_path=None,
            is_directory=True,
            difference_type=DifferenceType.CONTAINS_DIFFERENCE,
            depth=1,
            is_expanded=False,
            children=[],
            parent=self.root
        )
        self.root.children.append(self.dir1)
        
        # dir1/file1.txt
        file1 = TreeNode(
            name="file1.txt",
            left_path=None,
            right_path=None,
            is_directory=False,
            difference_type=DifferenceType.IDENTICAL,
            depth=2,
            is_expanded=False,
            children=[],
            parent=self.dir1
        )
        self.dir1.children.append(file1)
        
        # dir1/file2.txt
        file2 = TreeNode(
            name="file2.txt",
            left_path=None,
            right_path=None,
            is_directory=False,
            difference_type=DifferenceType.CONTENT_DIFFERENT,
            depth=2,
            is_expanded=False,
            children=[],
            parent=self.dir1
        )
        self.dir1.children.append(file2)
        
        # dir2
        self.dir2 = TreeNode(
            name="dir2",
            left_path=None,
            right_path=None,
            is_directory=True,
            difference_type=DifferenceType.CONTAINS_DIFFERENCE,
            depth=1,
            is_expanded=False,
            children=[],
            parent=self.root
        )
        self.root.children.append(self.dir2)
        
        # dir2/subdir
        self.subdir = TreeNode(
            name="subdir",
            left_path=None,
            right_path=None,
            is_directory=True,
            difference_type=DifferenceType.CONTAINS_DIFFERENCE,
            depth=2,
            is_expanded=False,
            children=[],
            parent=self.dir2
        )
        self.dir2.children.append(self.subdir)
        
        # dir2/subdir/file3.txt
        file3 = TreeNode(
            name="file3.txt",
            left_path=None,
            right_path=None,
            is_directory=False,
            difference_type=DifferenceType.ONLY_LEFT,
            depth=3,
            is_expanded=False,
            children=[],
            parent=self.subdir
        )
        self.subdir.children.append(file3)
        
        # file4.txt
        file4 = TreeNode(
            name="file4.txt",
            left_path=None,
            right_path=None,
            is_directory=False,
            difference_type=DifferenceType.IDENTICAL,
            depth=1,
            is_expanded=False,
            children=[],
            parent=self.root
        )
        self.root.children.append(file4)
    
    def test_flatten_tree_root_expanded(self):
        """Test flattening tree with only root expanded."""
        from src.tfm_directory_diff_viewer import DirectoryDiffViewer
        from tfm_path import Path
        
        # Create a mock viewer (we won't actually scan)
        viewer = DirectoryDiffViewer.__new__(DirectoryDiffViewer)
        viewer.root_node = self.root
        viewer.visible_nodes = []
        viewer.node_index_map = {}
        viewer.show_identical = True  # Initialize filter state
        
        # Flatten the tree
        viewer._flatten_tree(self.root)
        
        # Should have 3 visible nodes: dir1, dir2, file4.txt
        self.assertEqual(len(viewer.visible_nodes), 3)
        self.assertEqual(viewer.visible_nodes[0].name, "dir1")
        self.assertEqual(viewer.visible_nodes[1].name, "dir2")
        self.assertEqual(viewer.visible_nodes[2].name, "file4.txt")
        
        # Check node_index_map
        self.assertEqual(viewer.node_index_map[id(self.dir1)], 0)
        self.assertEqual(viewer.node_index_map[id(self.dir2)], 1)
    
    def test_expand_node(self):
        """Test expanding a collapsed directory node."""
        from src.tfm_directory_diff_viewer import DirectoryDiffViewer
        
        # Create a mock viewer
        viewer = DirectoryDiffViewer.__new__(DirectoryDiffViewer)
        viewer.root_node = self.root
        viewer.visible_nodes = []
        viewer.node_index_map = {}
        viewer._dirty = False
        viewer.show_identical = True  # Initialize filter state
        
        # Initial flatten (root expanded, children collapsed)
        viewer._flatten_tree(self.root)
        initial_count = len(viewer.visible_nodes)
        
        # Expand dir1 (index 0)
        viewer.expand_node(0)
        
        # Should now have 5 visible nodes: dir1, file1.txt, file2.txt, dir2, file4.txt
        self.assertEqual(len(viewer.visible_nodes), 5)
        self.assertEqual(viewer.visible_nodes[0].name, "dir1")
        self.assertEqual(viewer.visible_nodes[1].name, "file1.txt")
        self.assertEqual(viewer.visible_nodes[2].name, "file2.txt")
        self.assertEqual(viewer.visible_nodes[3].name, "dir2")
        self.assertEqual(viewer.visible_nodes[4].name, "file4.txt")
        
        # Check that dir1 is marked as expanded
        self.assertTrue(self.dir1.is_expanded)
        
        # Check that viewer was marked dirty
        self.assertTrue(viewer._dirty)
    
    def test_collapse_node(self):
        """Test collapsing an expanded directory node."""
        from src.tfm_directory_diff_viewer import DirectoryDiffViewer
        
        # Create a mock viewer
        viewer = DirectoryDiffViewer.__new__(DirectoryDiffViewer)
        viewer.root_node = self.root
        viewer.visible_nodes = []
        viewer.node_index_map = {}
        viewer._dirty = False
        viewer.cursor_position = 0
        viewer.show_identical = True  # Initialize filter state
        
        # Initial flatten
        viewer._flatten_tree(self.root)
        
        # Expand dir1
        viewer.expand_node(0)
        expanded_count = len(viewer.visible_nodes)
        
        # Collapse dir1 (still at index 0)
        viewer.collapse_node(0)
        
        # Should be back to 3 visible nodes: dir1, dir2, file4.txt
        self.assertEqual(len(viewer.visible_nodes), 3)
        self.assertEqual(viewer.visible_nodes[0].name, "dir1")
        self.assertEqual(viewer.visible_nodes[1].name, "dir2")
        self.assertEqual(viewer.visible_nodes[2].name, "file4.txt")
        
        # Check that dir1 is marked as collapsed
        self.assertFalse(self.dir1.is_expanded)
        
        # Check that viewer was marked dirty
        self.assertTrue(viewer._dirty)
    
    def test_expand_nested_directories(self):
        """Test expanding nested directories."""
        from src.tfm_directory_diff_viewer import DirectoryDiffViewer
        
        # Create a mock viewer
        viewer = DirectoryDiffViewer.__new__(DirectoryDiffViewer)
        viewer.root_node = self.root
        viewer.visible_nodes = []
        viewer.node_index_map = {}
        viewer._dirty = False
        viewer.show_identical = True  # Initialize filter state
        
        # Initial flatten
        viewer._flatten_tree(self.root)
        
        # Expand dir2 (index 1)
        viewer.expand_node(1)
        
        # Should now have 4 visible nodes: dir1, dir2, subdir, file4
        self.assertEqual(len(viewer.visible_nodes), 4)
        self.assertEqual(viewer.visible_nodes[2].name, "subdir")
        
        # Expand subdir (now at index 2)
        viewer.expand_node(2)
        
        # Should now have 5 visible nodes: dir1, dir2, subdir, file3.txt, file4
        self.assertEqual(len(viewer.visible_nodes), 5)
        self.assertEqual(viewer.visible_nodes[3].name, "file3.txt")
    
    def test_collapse_nested_directories(self):
        """Test that collapsing removes all descendants."""
        from src.tfm_directory_diff_viewer import DirectoryDiffViewer
        
        # Create a mock viewer
        viewer = DirectoryDiffViewer.__new__(DirectoryDiffViewer)
        viewer.root_node = self.root
        viewer.visible_nodes = []
        viewer.node_index_map = {}
        viewer._dirty = False
        viewer.cursor_position = 0
        viewer.show_identical = True  # Initialize filter state
        
        # Initial flatten
        viewer._flatten_tree(self.root)
        
        # Expand dir2 and subdir
        viewer.expand_node(1)  # dir2
        viewer.expand_node(2)  # subdir
        
        # Should have 5 visible nodes
        self.assertEqual(len(viewer.visible_nodes), 5)
        
        # Collapse dir2 (still at index 1)
        viewer.collapse_node(1)
        
        # Should be back to 3 visible nodes (subdir and file3.txt removed)
        self.assertEqual(len(viewer.visible_nodes), 3)
        self.assertEqual(viewer.visible_nodes[0].name, "dir1")
        self.assertEqual(viewer.visible_nodes[1].name, "dir2")
        self.assertEqual(viewer.visible_nodes[2].name, "file4.txt")
    
    def test_node_index_map_consistency(self):
        """Test that node_index_map stays consistent after expand/collapse."""
        from src.tfm_directory_diff_viewer import DirectoryDiffViewer
        
        # Create a mock viewer
        viewer = DirectoryDiffViewer.__new__(DirectoryDiffViewer)
        viewer.root_node = self.root
        viewer.visible_nodes = []
        viewer.node_index_map = {}
        viewer.cursor_position = 0  # Initialize cursor_position
        viewer._dirty = False
        viewer.show_identical = True  # Initialize filter state
        
        # Initial flatten
        viewer._flatten_tree(self.root)
        
        # Verify initial map
        for node in viewer.visible_nodes:
            index = viewer.node_index_map[id(node)]
            self.assertEqual(viewer.visible_nodes[index], node)
        
        # Expand dir1
        viewer.expand_node(0)
        
        # Verify map after expand
        for node in viewer.visible_nodes:
            index = viewer.node_index_map[id(node)]
            self.assertEqual(viewer.visible_nodes[index], node)
        
        # Collapse dir1
        viewer.collapse_node(0)
        
        # Verify map after collapse
        for node in viewer.visible_nodes:
            index = viewer.node_index_map[id(node)]
            self.assertEqual(viewer.visible_nodes[index], node)
