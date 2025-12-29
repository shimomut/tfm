"""
Test entry point functionality for TFM

Run with: PYTHONPATH=.:src:ttk pytest test/test_entry_point.py -v
"""

import unittest

class TestEntryPoint(unittest.TestCase):
    """Test entry point functionality"""
    
    def test_import_main_function(self):
        """Test that we can import the main function from tfm.py"""
        try:
            from tfm import main
            self.assertTrue(callable(main), "main should be callable")
        except ImportError as e:
            self.fail(f"Failed to import main function: {e}")
    
    def test_import_parser_function(self):
        """Test that we can import the create_parser function"""
        try:
            from tfm import create_parser
            parser = create_parser()
            self.assertIsNotNone(parser, "Parser should not be None")
            
            # Test that parser has the expected arguments
            help_text = parser.format_help()
            self.assertIn('--version', help_text)
            self.assertIn('--help', help_text)
            
        except ImportError as e:
            self.fail(f"Failed to import create_parser function: {e}")
