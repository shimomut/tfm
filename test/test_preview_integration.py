#!/usr/bin/env python3
"""
Integration test for preview_files.sh with TFM configuration
"""

import sys
import unittest
from pathlib import Path

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class TestPreviewIntegration(unittest.TestCase):
    """Test preview files integration with TFM"""
    
    def test_preview_program_in_default_config(self):
        """Test that preview program is in the default configuration"""
        # Import the default configuration module directly
        import importlib.util
        config_path = Path(__file__).parent.parent / 'src' / '_config.py'
        
        spec = importlib.util.spec_from_file_location("_config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        
        # Check the PROGRAMS list in the Config class
        programs = getattr(config_module.Config, 'PROGRAMS', [])
        preview_programs = [p for p in programs if 'preview' in p['name'].lower()]
        
        self.assertTrue(len(preview_programs) > 0, 
                       "Preview program should be in default configuration")
        
        preview_program = preview_programs[0]
        self.assertEqual(preview_program['name'], 'Preview Files (macOS)')
        self.assertEqual(preview_program['command'], ['./tools/preview_files.sh'])
        self.assertTrue(preview_program.get('options', {}).get('auto_return', False),
                       "Preview program should have auto_return option")
    
    def test_script_exists_and_executable(self):
        """Test that the preview script exists and is executable"""
        script_path = Path(__file__).parent.parent / 'tools' / 'preview_files.sh'
        
        self.assertTrue(script_path.exists(), 
                       "preview_files.sh should exist")
        self.assertTrue(script_path.is_file(), 
                       "preview_files.sh should be a file")
        
        import os
        self.assertTrue(os.access(script_path, os.X_OK), 
                       "preview_files.sh should be executable")
    
    def test_script_has_proper_shebang(self):
        """Test that the script has proper shebang"""
        script_path = Path(__file__).parent.parent / 'tools' / 'preview_files.sh'
        
        with open(script_path, 'r') as f:
            first_line = f.readline().strip()
        
        self.assertEqual(first_line, '#!/bin/bash', 
                        "Script should have proper bash shebang")

if __name__ == '__main__':
    unittest.main()