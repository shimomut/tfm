"""
Test key event profiling functionality

Run with: PYTHONPATH=.:src:ttk pytest test/test_key_event_profiling.py -v
"""

import unittest
import tempfile
import shutil
import time
from pathlib import Path

from tfm_profiling import ProfilingManager


class TestKeyEventProfiling(unittest.TestCase):
    """Test key event profiling"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for profiling output
        self.temp_dir = tempfile.mkdtemp()
        self.profiling_manager = ProfilingManager(enabled=True, output_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Wait a bit to ensure all async operations complete
        time.sleep(0.2)
        # Remove temporary directory
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_profile_key_handling_creates_file(self):
        """Test that profiling key handling creates a profile file"""
        # Define a simple function to profile
        def mock_key_handler(event):
            # Simulate some work
            total = 0
            for i in range(1000):
                total += i
            return total
        
        # Create a mock event
        class MockEvent:
            def __init__(self):
                self.key_code = 'a'
        
        event = MockEvent()
        
        # Profile the key handling
        result = self.profiling_manager.profile_key_handling(mock_key_handler, event)
        
        # Verify the function executed correctly
        self.assertEqual(result, sum(range(1000)))
        
        # Wait for async file write to complete
        time.sleep(0.1)
        
        # Verify a profile file was created
        profile_files = list(Path(self.temp_dir).glob("key_profile_*.prof"))
        self.assertEqual(len(profile_files), 1, "Expected exactly one key profile file")
        
        # Verify the profile file has content
        profile_file = profile_files[0]
        self.assertGreater(profile_file.stat().st_size, 0, "Profile file should not be empty")
    
    def test_profile_key_handling_filename_format(self):
        """Test that profile filenames follow the expected format"""
        def mock_key_handler(event):
            return None
        
        class MockEvent:
            def __init__(self):
                self.key_code = 'b'
        
        event = MockEvent()
        
        # Profile the key handling
        self.profiling_manager.profile_key_handling(mock_key_handler, event)
        
        # Wait for async file write to complete
        time.sleep(0.1)
        
        # Check filename format
        profile_files = list(Path(self.temp_dir).glob("key_profile_*.prof"))
        self.assertEqual(len(profile_files), 1)
        
        filename = profile_files[0].name
        # Verify format: key_profile_YYYYMMDD_HHMMSS_microseconds.prof
        self.assertTrue(filename.startswith("key_profile_"))
        self.assertTrue(filename.endswith(".prof"))
        
        # Extract timestamp part
        timestamp_part = filename[len("key_profile_"):-len(".prof")]
        parts = timestamp_part.split("_")
        self.assertEqual(len(parts), 3, "Expected date, time, and microseconds")
    
    def test_multiple_key_profiles_unique_filenames(self):
        """Test that multiple key profiles generate unique filenames"""
        def mock_key_handler(event):
            return None
        
        class MockEvent:
            def __init__(self):
                self.key_code = 'c'
        
        event = MockEvent()
        
        # Profile multiple times
        for _ in range(3):
            self.profiling_manager.profile_key_handling(mock_key_handler, event)
            time.sleep(0.001)  # Small delay to ensure different timestamps
        
        # Verify we have 3 unique profile files
        profile_files = list(Path(self.temp_dir).glob("key_profile_*.prof"))
        self.assertEqual(len(profile_files), 3, "Expected three unique profile files")
        
        # Verify all filenames are unique
        filenames = [f.name for f in profile_files]
        self.assertEqual(len(filenames), len(set(filenames)), "All filenames should be unique")
    
    def test_profile_key_handling_disabled(self):
        """Test that profiling does nothing when disabled"""
        # Create a disabled profiling manager
        disabled_manager = ProfilingManager(enabled=False, output_dir=self.temp_dir)
        
        def mock_key_handler(event):
            return "result"
        
        class MockEvent:
            def __init__(self):
                self.key_code = 'd'
        
        event = MockEvent()
        
        # Profile with disabled manager
        result = disabled_manager.profile_key_handling(mock_key_handler, event)
        
        # Verify function still executes
        self.assertEqual(result, "result")
        
        # Verify no profile files were created
        profile_files = list(Path(self.temp_dir).glob("key_profile_*.prof"))
        self.assertEqual(len(profile_files), 0, "No profile files should be created when disabled")
    
    def test_profile_key_handling_with_exception(self):
        """Test that profiling handles exceptions in the profiled function"""
        def mock_key_handler_with_error(event):
            raise ValueError("Test error")
        
        class MockEvent:
            def __init__(self):
                self.key_code = 'e'
        
        event = MockEvent()
        
        # Profile should propagate the exception
        with self.assertRaises(ValueError):
            self.profiling_manager.profile_key_handling(mock_key_handler_with_error, event)
        
        # Wait for async file write to complete
        time.sleep(0.1)
        
        # But it should still write the profile file
        profile_files = list(Path(self.temp_dir).glob("key_profile_*.prof"))
        self.assertEqual(len(profile_files), 1, "Profile file should be created even on exception")
    
    def test_readme_created_in_output_directory(self):
        """Test that README.txt is created in the output directory"""
        # Trigger profile writing which should create the directory and README
        def mock_key_handler(event):
            return None
        
        class MockEvent:
            def __init__(self):
                self.key_code = 'f'
        
        event = MockEvent()
        
        self.profiling_manager.profile_key_handling(mock_key_handler, event)
        
        # Wait for async file write to complete
        time.sleep(0.1)
        
        # Verify README exists
        readme_path = Path(self.temp_dir) / "README.txt"
        self.assertTrue(readme_path.exists(), "README.txt should be created")
        
        # Verify README has content
        readme_content = readme_path.read_text()
        self.assertIn("TFM Profiling Output", readme_content)
        self.assertIn("pstats", readme_content)
        self.assertIn("snakeviz", readme_content)
