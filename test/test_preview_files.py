#!/usr/bin/env python3
"""
Test preview_files.sh script functionality
"""

import sys
import subprocess
import unittest
import tempfile
import os
from pathlib import Path

class TestPreviewFiles(unittest.TestCase):
    """Test preview_files.sh script"""
    
    def setUp(self):
        """Set up test environment"""
        self.script_path = Path(__file__).parent.parent / 'tools' / 'preview_files.sh'
        self.assertTrue(self.script_path.exists(), "preview_files.sh script not found")
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.test_image = Path(self.temp_dir) / 'test.jpg'
        self.test_text = Path(self.temp_dir) / 'test.txt'
        
        # Create dummy files
        self.test_image.write_bytes(b'fake image content')
        self.test_text.write_text('fake text content')
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def run_script(self, env_vars=None):
        """Helper method to run the preview script with environment variables"""
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        
        result = subprocess.run(
            ['bash', str(self.script_path)],
            capture_output=True,
            text=True,
            env=env
        )
        return result
    
    def test_no_files_selected(self):
        """Test error when no files are selected"""
        result = self.run_script({
            'TFM_THIS_DIR': self.temp_dir
        })
        
        self.assertEqual(result.returncode, 1)
        self.assertIn('No files selected', result.stdout)
    
    def test_unsupported_file_type(self):
        """Test handling of unsupported file types"""
        result = self.run_script({
            'TFM_THIS_DIR': self.temp_dir,
            'TFM_THIS_SELECTED': f'"{self.test_text}"'
        })
        
        self.assertEqual(result.returncode, 1)
        self.assertIn('Skipping unsupported file type', result.stdout)
        self.assertIn('No supported files found', result.stdout)
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent files"""
        nonexistent = Path(self.temp_dir) / 'nonexistent.jpg'
        
        result = self.run_script({
            'TFM_THIS_DIR': self.temp_dir,
            'TFM_THIS_SELECTED': f'"{nonexistent}"'
        })
        
        self.assertEqual(result.returncode, 1)
        self.assertIn('File does not exist', result.stdout)
    
    def test_supported_extensions_list(self):
        """Test that supported extensions are properly listed"""
        result = self.run_script({
            'TFM_THIS_DIR': self.temp_dir,
            'TFM_THIS_SELECTED': f'"{self.test_text}"'
        })
        
        # Should list supported file types
        self.assertIn('jpg', result.stdout)
        self.assertIn('png', result.stdout)
        self.assertIn('pdf', result.stdout)
        self.assertIn('heic', result.stdout)
    
    def test_macos_check(self):
        """Test macOS detection (skip if not on macOS)"""
        # Test with fake Linux environment
        result = self.run_script({
            'TFM_THIS_DIR': self.temp_dir,
            'TFM_THIS_SELECTED': f'"{self.test_image}"'
        })
        
        # On macOS, should proceed (might fail at Preview.app check)
        # On other systems, should fail with OS error
        if result.returncode == 1 and 'only supports macOS' in result.stdout:
            # Running on non-macOS system
            self.assertIn('only supports macOS', result.stdout)
            self.assertIn('other operating systems will be supported', result.stdout)
    
    def test_script_is_executable(self):
        """Test that the script has executable permissions"""
        self.assertTrue(os.access(self.script_path, os.X_OK), 
                       "preview_files.sh should be executable")
    
    def test_multiple_files_mixed_types(self):
        """Test handling of multiple files with mixed types"""
        # Create another test file
        test_pdf = Path(self.temp_dir) / 'test.pdf'
        test_pdf.write_bytes(b'fake pdf content')
        
        result = self.run_script({
            'TFM_THIS_DIR': self.temp_dir,
            'TFM_THIS_SELECTED': f'"{self.test_image}" "{self.test_text}" "{test_pdf}"'
        })
        
        # Should process supported files and skip unsupported ones
        output = result.stdout
        self.assertIn('Adding to preview: test.jpg', output)
        self.assertIn('Adding to preview: test.pdf', output)
        self.assertIn('Skipping unsupported file type: test.txt', output)

if __name__ == '__main__':
    unittest.main()