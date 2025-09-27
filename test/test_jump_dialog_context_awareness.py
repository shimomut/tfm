#!/usr/bin/env python3
"""
Test JumpDialog context-aware hidden files behavior
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_jump_dialog import JumpDialog
from tfm_file_operations import FileOperations


class TestJumpDialogContextAwareness(unittest.TestCase):
    """Test JumpDialog context-aware hidden files behavior"""
    
    def setUp(self):
        """Set up test environment with realistic directory structure"""
        # Create mock config
        self.config = Mock()
        self.config.MAX_JUMP_DIRECTORIES = 1000
        
        # Create temporary directory structure similar to a real project
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create a realistic project structure
        project_dir = self.temp_dir / "my-project"
        project_dir.mkdir()
        
        # Visible directories
        (project_dir / "src").mkdir()
        (project_dir / "docs").mkdir()
        (project_dir / "tests").mkdir()
        (project_dir / "src" / "components").mkdir()
        (project_dir / "src" / "utils").mkdir()
        
        # Hidden directories (common in projects)
        git_dir = project_dir / ".git"
        git_dir.mkdir()
        (git_dir / "hooks").mkdir()
        (git_dir / "info").mkdir()
        (git_dir / "objects").mkdir()
        (git_dir / "refs").mkdir()
        (git_dir / "refs" / "heads").mkdir()
        (git_dir / "refs" / "tags").mkdir()
        
        vscode_dir = project_dir / ".vscode"
        vscode_dir.mkdir()
        
        config_dir = project_dir / ".config"
        config_dir.mkdir()
        (config_dir / "settings").mkdir()
        
        # Node modules (common hidden-ish directory)
        node_modules = project_dir / "node_modules"
        node_modules.mkdir()
        (node_modules / "package1").mkdir()
        (node_modules / "package2").mkdir()
        
        self.project_dir = project_dir
        self.git_dir = git_dir
        self.config_dir = config_dir
        
        # Create jump dialog
        self.jump_dialog = JumpDialog(self.config)
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def wait_for_scan_completion(self, timeout=5.0):
        """Wait for directory scanning to complete"""
        import time
        start_time = time.time()
        while self.jump_dialog.searching and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        return not self.jump_dialog.searching
    
    def test_visible_root_filters_hidden_directories(self):
        """Test that scanning from visible root filters out hidden directories"""
        # Create file operations with show_hidden = False
        file_ops = FileOperations(self.config)
        file_ops.show_hidden = False
        
        # Scan from project root (visible directory)
        self.jump_dialog.show(self.project_dir, file_ops)
        self.assertTrue(self.wait_for_scan_completion())
        
        # Get found directories as strings for easier checking
        found_paths = [str(d) for d in self.jump_dialog.directories]
        
        # Should include visible directories
        self.assertTrue(any("src" in path for path in found_paths))
        self.assertTrue(any("docs" in path for path in found_paths))
        self.assertTrue(any("tests" in path for path in found_paths))
        self.assertTrue(any("components" in path for path in found_paths))
        self.assertTrue(any("node_modules" in path for path in found_paths))  # Not hidden
        
        # Should NOT include hidden directories
        self.assertFalse(any(".git" in path for path in found_paths))
        self.assertFalse(any(".vscode" in path for path in found_paths))
        self.assertFalse(any(".config" in path for path in found_paths))
        
        self.jump_dialog.exit()
    
    def test_hidden_root_allows_subdirectories(self):
        """Test that scanning from hidden root allows access to subdirectories"""
        # Create file operations with show_hidden = False
        file_ops = FileOperations(self.config)
        file_ops.show_hidden = False
        
        # Scan from .git directory (hidden root)
        self.jump_dialog.show(self.git_dir, file_ops)
        self.assertTrue(self.wait_for_scan_completion())
        
        # Get found directories as strings for easier checking
        found_paths = [str(d) for d in self.jump_dialog.directories]
        
        # Should include .git subdirectories
        self.assertTrue(any("hooks" in path for path in found_paths))
        self.assertTrue(any("info" in path for path in found_paths))
        self.assertTrue(any("objects" in path for path in found_paths))
        self.assertTrue(any("refs" in path for path in found_paths))
        self.assertTrue(any("heads" in path for path in found_paths))
        self.assertTrue(any("tags" in path for path in found_paths))
        
        # Should include the root .git directory itself
        self.assertTrue(any(str(self.git_dir) in path for path in found_paths))
        
        self.jump_dialog.exit()
    
    def test_nested_hidden_directory_access(self):
        """Test access to nested directories within hidden context"""
        # Create file operations with show_hidden = False
        file_ops = FileOperations(self.config)
        file_ops.show_hidden = False
        
        # Scan from .git/refs directory (nested within hidden)
        refs_dir = self.git_dir / "refs"
        self.jump_dialog.show(refs_dir, file_ops)
        self.assertTrue(self.wait_for_scan_completion())
        
        # Get found directories as strings for easier checking
        found_paths = [str(d) for d in self.jump_dialog.directories]
        
        # Should include subdirectories within refs
        self.assertTrue(any("heads" in path for path in found_paths))
        self.assertTrue(any("tags" in path for path in found_paths))
        
        # Should include the refs directory itself
        self.assertTrue(any(str(refs_dir) in path for path in found_paths))
        
        self.jump_dialog.exit()
    
    def test_show_hidden_true_includes_everything(self):
        """Test that show_hidden=True includes all directories regardless of context"""
        # Create file operations with show_hidden = True
        file_ops = FileOperations(self.config)
        file_ops.show_hidden = True
        
        # Scan from project root
        self.jump_dialog.show(self.project_dir, file_ops)
        self.assertTrue(self.wait_for_scan_completion())
        
        # Get found directories as strings for easier checking
        found_paths = [str(d) for d in self.jump_dialog.directories]
        
        # Should include visible directories
        self.assertTrue(any("src" in path for path in found_paths))
        self.assertTrue(any("docs" in path for path in found_paths))
        self.assertTrue(any("components" in path for path in found_paths))
        
        # Should ALSO include hidden directories
        self.assertTrue(any(".git" in path for path in found_paths))
        self.assertTrue(any(".vscode" in path for path in found_paths))
        self.assertTrue(any(".config" in path for path in found_paths))
        self.assertTrue(any("hooks" in path for path in found_paths))
        self.assertTrue(any("settings" in path for path in found_paths))
        
        self.jump_dialog.exit()
    
    def test_real_world_git_workflow(self):
        """Test a realistic Git workflow scenario"""
        # Create file operations with show_hidden = False
        file_ops = FileOperations(self.config)
        file_ops.show_hidden = False
        
        # Scenario 1: User is in project root, should not see .git
        self.jump_dialog.show(self.project_dir, file_ops)
        self.assertTrue(self.wait_for_scan_completion())
        
        found_paths = [str(d) for d in self.jump_dialog.directories]
        self.assertFalse(any(".git" in path for path in found_paths))
        self.jump_dialog.exit()
        
        # Scenario 2: User navigates to .git/info, should see subdirectories
        git_info_dir = self.git_dir / "info"
        self.jump_dialog.show(git_info_dir, file_ops)
        self.assertTrue(self.wait_for_scan_completion())
        
        # Should at least include the info directory itself
        found_paths = [str(d) for d in self.jump_dialog.directories]
        self.assertTrue(any(str(git_info_dir) in path for path in found_paths))
        self.jump_dialog.exit()
    
    def test_config_directory_workflow(self):
        """Test working within .config directory"""
        # Create file operations with show_hidden = False
        file_ops = FileOperations(self.config)
        file_ops.show_hidden = False
        
        # User navigates to .config directory
        self.jump_dialog.show(self.config_dir, file_ops)
        self.assertTrue(self.wait_for_scan_completion())
        
        found_paths = [str(d) for d in self.jump_dialog.directories]
        
        # Should include .config directory itself and its subdirectories
        self.assertTrue(any(str(self.config_dir) in path for path in found_paths))
        self.assertTrue(any("settings" in path for path in found_paths))
        
        self.jump_dialog.exit()


if __name__ == '__main__':
    unittest.main()