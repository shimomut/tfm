"""
Test Search Dialog Configuration Access
Verifies that search dialog can access MAX_SEARCH_RESULTS configuration

Run with: PYTHONPATH=.:src:ttk pytest test/test_search_dialog_config.py -v
"""

import unittest

from tfm_config import DefaultConfig
from _config import Config
from tfm_search_dialog import SearchDialog


class TestSearchDialogConfig(unittest.TestCase):
    """Test that search dialog can access its configuration parameters"""
    
    def setUp(self):
        """Set up test environment"""
        self.default_config = DefaultConfig()
        self.user_config = Config()
    
    def test_search_dialog_max_results_access(self):
        """Test that search dialog can access MAX_SEARCH_RESULTS"""
        # Test with default config
        search_dialog_default = SearchDialog(self.default_config)
        self.assertEqual(search_dialog_default.max_search_results, 
                        self.default_config.MAX_SEARCH_RESULTS)
        
        # Test with user config
        search_dialog_user = SearchDialog(self.user_config)
        self.assertEqual(search_dialog_user.max_search_results, 
                        self.user_config.MAX_SEARCH_RESULTS)
    
    def test_max_search_results_value(self):
        """Test that MAX_SEARCH_RESULTS has a reasonable value"""
        # Check default config
        self.assertIsInstance(self.default_config.MAX_SEARCH_RESULTS, int)
        self.assertGreater(self.default_config.MAX_SEARCH_RESULTS, 0)
        self.assertGreaterEqual(self.default_config.MAX_SEARCH_RESULTS, 1000)
        
        # Check user config
        self.assertIsInstance(self.user_config.MAX_SEARCH_RESULTS, int)
        self.assertGreater(self.user_config.MAX_SEARCH_RESULTS, 0)
        self.assertGreaterEqual(self.user_config.MAX_SEARCH_RESULTS, 1000)
    
    def test_config_consistency(self):
        """Test that both configs have the same MAX_SEARCH_RESULTS value"""
        self.assertEqual(self.default_config.MAX_SEARCH_RESULTS, 
                        self.user_config.MAX_SEARCH_RESULTS)


def run_search_config_tests():
    """Run all search dialog configuration tests"""
    print("Running Search Dialog Configuration Tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchDialogConfig)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} search dialog config tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests")
        
        for test, traceback in result.failures:
            print(f"\nFAILURE: {test}")
            print(traceback)
            
        for test, traceback in result.errors:
            print(f"\nERROR: {test}")
            print(traceback)
    
    return result.wasSuccessful()
