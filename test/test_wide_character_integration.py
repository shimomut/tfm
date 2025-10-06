#!/usr/bin/env python3
"""
Comprehensive integration tests for wide character support in TFM.

This test suite verifies that all components work together correctly
when handling directories containing wide character filenames.
"""

import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import tfm_wide_char_utils
import tfm_main
import tfm_text_viewer
import tfm_single_line_text_edit
import tfm_base_list_dialog


class WideCharacterIntegrationTest(unittest.TestCase):
    """Integration tests for wide character support across all TFM components."""
    
    def setUp(self):
        """Set up test environment with wide character test files."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
        
        # Create test files with various character types
        self.test_files = [
            "normal_file.txt",           # ASCII only
            "日本語ファイル.txt",          # Japanese characters
            "mixed_英語_file.txt",        # Mixed ASCII and Japanese
            "emoji_📁_folder",           # Emoji characters
            "combining_é_chars.txt",     # Combining characters
            "한국어_파일.txt",            # Korean characters
            "中文文件.txt",               # Chinese characters
            "русский_файл.txt",          # Cyrillic characters
            "العربية_ملف.txt",           # Arabic characters
            "very_long_filename_with_wide_characters_日本語ファイル名が長い場合のテスト.txt",
        ]
        
        # Create the test files
        for filename in self.test_files:
            file_path = os.path.join(self.test_dir, filename)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Test content for {filename}\n")
                    f.write("This file contains wide characters: こんにちは世界\n")
                    f.write("Mixed content: Hello 世界 World\n")
                    f.write("Emoji test: 📁📄🌍\n")
            except (OSError, UnicodeError) as e:
                # Skip files that can't be created on this system
                print(f"Warning: Could not create test file {filename}: {e}")
                continue
    
    def test_display_width_calculation_performance(self):
        """Test display width calculation performance with various character types."""
        import time
        
        # Test strings with different character types
        test_strings = [
            "simple_ascii_filename.txt",
            "日本語ファイル.txt",
            "mixed_英語_file.txt",
            "emoji_📁_folder",
            "very_long_filename_with_wide_characters_日本語ファイル名が長い場合のテスト.txt",
        ] * 100  # Repeat for performance testing
        
        # Measure performance
        start_time = time.time()
        for text in test_strings:
            width = tfm_wide_char_utils.get_display_width(text)
            self.assertIsInstance(width, int)
            self.assertGreaterEqual(width, 0)
        end_time = time.time()
        
        # Performance should be reasonable (less than 1 second for 500 calculations)
        elapsed = end_time - start_time
        self.assertLess(elapsed, 1.0, f"Display width calculation took too long: {elapsed:.3f}s")
        
        # Test cache effectiveness
        cache_info = tfm_wide_char_utils.get_cache_info()
        self.assertIsInstance(cache_info, dict)
        self.assertIn('display_width_cache', cache_info)
    
    def test_file_display_integration(self):
        """Test file display with wide character filenames."""
        # Create a mock TFM main instance
        class MockTFMMain:
            def __init__(self, test_dir):
                self.current_dir = test_dir
                self.files = []
                self.cursor_position = 0
                self.selected_files = set()
            
            def get_files_in_directory(self, directory):
                """Get files in directory, similar to TFM's file listing."""
                try:
                    files = []
                    for item in os.listdir(directory):
                        item_path = os.path.join(directory, item)
                        if os.path.isfile(item_path):
                            files.append({
                                'name': item,
                                'path': item_path,
                                'size': os.path.getsize(item_path),
                                'is_dir': False
                            })
                    return sorted(files, key=lambda x: x['name'])
                except (OSError, UnicodeError) as e:
                    print(f"Error listing directory: {e}")
                    return []
        
        # Test file listing with wide characters
        mock_tfm = MockTFMMain(self.test_dir)
        files = mock_tfm.get_files_in_directory(self.test_dir)
        
        # Verify files were found
        self.assertGreater(len(files), 0, "No test files found")
        
        # Test display width calculation for each filename
        for file_info in files:
            filename = file_info['name']
            
            # Test display width calculation
            width = tfm_wide_char_utils.safe_get_display_width(filename)
            self.assertIsInstance(width, int)
            self.assertGreaterEqual(width, 0)
            
            # Test truncation at various widths
            for max_width in [10, 20, 30, 50]:
                truncated = tfm_wide_char_utils.safe_truncate_to_width(filename, max_width)
                truncated_width = tfm_wide_char_utils.safe_get_display_width(truncated)
                self.assertLessEqual(truncated_width, max_width,
                                   f"Truncated filename '{truncated}' width {truncated_width} exceeds max {max_width}")
            
            # Test padding for column alignment
            original_width = tfm_wide_char_utils.safe_get_display_width(filename)
            for target_width in [20, 30, 40]:
                padded = tfm_wide_char_utils.safe_pad_to_width(filename, target_width)
                padded_width = tfm_wide_char_utils.safe_get_display_width(padded)
                expected_width = max(original_width, target_width)
                self.assertEqual(padded_width, expected_width,
                               f"Padded filename '{padded}' width {padded_width} != expected {expected_width}")
    
    def test_text_viewer_integration(self):
        """Test text viewer with wide character content."""
        # Create a test file with wide character content
        test_content = """Test file with wide characters
こんにちは世界 - Hello World in Japanese
Mixed content: Hello 世界 World
Emoji test: 📁📄🌍
Long line with wide characters: これは非常に長い行で、日本語の文字が含まれています。テキストビューアーでの表示をテストします。
Arabic: مرحبا بالعالم
Russian: Привет мир
Korean: 안녕하세요 세계
Chinese: 你好世界
"""
        
        test_file = os.path.join(self.test_dir, "wide_char_content.txt")
        try:
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
        except (OSError, UnicodeError) as e:
            self.skipTest(f"Could not create test file with wide characters: {e}")
        
        # Test text viewer functionality
        class MockTextViewer:
            def __init__(self, file_path):
                self.file_path = file_path
                self.lines = []
                self.load_file()
            
            def load_file(self):
                """Load file content, similar to TFM's text viewer."""
                try:
                    with open(self.file_path, 'r', encoding='utf-8') as f:
                        self.lines = f.readlines()
                except (OSError, UnicodeError) as e:
                    print(f"Error loading file: {e}")
                    self.lines = []
            
            def wrap_line(self, line, width):
                """Wrap line to specified width using wide character utilities."""
                if not line.strip():
                    return [line]
                
                wrapped_lines = []
                remaining = line.rstrip('\n\r')
                
                while remaining:
                    if tfm_wide_char_utils.safe_get_display_width(remaining) <= width:
                        wrapped_lines.append(remaining)
                        break
                    
                    # Split at width boundary
                    left, right = tfm_wide_char_utils.safe_split_at_width(remaining, width)
                    if not left:  # Prevent infinite loop
                        left = remaining[:1]
                        right = remaining[1:]
                    
                    wrapped_lines.append(left)
                    remaining = right
                
                return wrapped_lines
        
        # Test text viewer with wide character content
        viewer = MockTextViewer(test_file)
        self.assertGreater(len(viewer.lines), 0, "No lines loaded from test file")
        
        # Test line wrapping at various widths
        for width in [20, 40, 60, 80]:
            for line in viewer.lines:
                wrapped = viewer.wrap_line(line, width)
                self.assertIsInstance(wrapped, list)
                self.assertGreater(len(wrapped), 0)
                
                # Verify each wrapped line fits within width
                for wrapped_line in wrapped:
                    line_width = tfm_wide_char_utils.safe_get_display_width(wrapped_line)
                    self.assertLessEqual(line_width, width,
                                       f"Wrapped line '{wrapped_line}' width {line_width} exceeds {width}")
    
    def test_dialog_system_integration(self):
        """Test dialog system with wide character input."""
        # Test single line text edit with wide characters
        test_inputs = [
            "normal text",
            "日本語入力",
            "mixed 英語 input",
            "emoji 📁 input",
            "very long input with wide characters 非常に長い入力テキスト",
        ]
        
        class MockSingleLineTextEdit:
            def __init__(self):
                self.text = ""
                self.cursor_pos = 0
            
            def set_text(self, text):
                """Set text content."""
                self.text = text
                self.cursor_pos = len(text)
            
            def get_display_width(self):
                """Get display width of current text."""
                return tfm_wide_char_utils.safe_get_display_width(self.text)
            
            def truncate_for_display(self, max_width):
                """Truncate text for display within max width."""
                return tfm_wide_char_utils.safe_truncate_to_width(self.text, max_width)
        
        # Test text input with wide characters
        text_edit = MockSingleLineTextEdit()
        
        for test_input in test_inputs:
            text_edit.set_text(test_input)
            
            # Test display width calculation
            width = text_edit.get_display_width()
            self.assertIsInstance(width, int)
            self.assertGreaterEqual(width, 0)
            
            # Test truncation at various widths
            for max_width in [10, 20, 30]:
                truncated = text_edit.truncate_for_display(max_width)
                truncated_width = tfm_wide_char_utils.safe_get_display_width(truncated)
                self.assertLessEqual(truncated_width, max_width,
                                   f"Truncated text '{truncated}' width {truncated_width} exceeds {max_width}")
    
    def test_performance_with_large_directory(self):
        """Test performance with large directories containing mixed character types."""
        # Create a larger test directory
        large_test_dir = os.path.join(self.test_dir, "large_test")
        os.makedirs(large_test_dir, exist_ok=True)
        
        # Create many files with different character types
        file_patterns = [
            "file_{:03d}.txt",
            "ファイル_{:03d}.txt",
            "mixed_{:03d}_英語.txt",
            "emoji_{:03d}_📁.txt",
        ]
        
        created_files = []
        for i in range(50):  # Create 200 files total (50 * 4 patterns)
            for pattern in file_patterns:
                filename = pattern.format(i)
                file_path = os.path.join(large_test_dir, filename)
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"Content {i}\n")
                    created_files.append(filename)
                except (OSError, UnicodeError):
                    continue  # Skip files that can't be created
        
        self.assertGreater(len(created_files), 0, "No files created for performance test")
        
        # Test performance of display width calculations
        import time
        start_time = time.time()
        
        total_width = 0
        for filename in created_files:
            width = tfm_wide_char_utils.safe_get_display_width(filename)
            total_width += width
            
            # Test truncation
            truncated = tfm_wide_char_utils.safe_truncate_to_width(filename, 30)
            
            # Test padding
            padded = tfm_wide_char_utils.safe_pad_to_width(filename, 40)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Performance should be reasonable
        files_per_second = len(created_files) / elapsed if elapsed > 0 else float('inf')
        self.assertGreater(files_per_second, 100,
                          f"Performance too slow: {files_per_second:.1f} files/second")
        
        print(f"Processed {len(created_files)} files in {elapsed:.3f}s ({files_per_second:.1f} files/sec)")
    
    def test_error_handling_integration(self):
        """Test error handling across all components with problematic filenames."""
        # Test with various problematic inputs
        problematic_inputs = [
            "",  # Empty string
            None,  # None value
            123,  # Non-string type
            "\x00invalid\x00",  # Null bytes
            "invalid\udcff\udcfe",  # Invalid Unicode surrogates
        ]
        
        for problematic_input in problematic_inputs:
            # Test safe display width calculation
            try:
                width = tfm_wide_char_utils.safe_get_display_width(problematic_input)
                self.assertIsInstance(width, int)
                self.assertGreaterEqual(width, 0)
            except Exception as e:
                self.fail(f"safe_get_display_width failed with {problematic_input}: {e}")
            
            # Test safe truncation
            try:
                truncated = tfm_wide_char_utils.safe_truncate_to_width(problematic_input, 10)
                self.assertIsInstance(truncated, str)
            except Exception as e:
                self.fail(f"safe_truncate_to_width failed with {problematic_input}: {e}")
            
            # Test safe padding
            try:
                padded = tfm_wide_char_utils.safe_pad_to_width(problematic_input, 20)
                self.assertIsInstance(padded, str)
            except Exception as e:
                self.fail(f"safe_pad_to_width failed with {problematic_input}: {e}")
    
    def test_cache_effectiveness(self):
        """Test that caching improves performance for repeated operations."""
        # Clear cache to start fresh
        tfm_wide_char_utils.clear_display_width_cache()
        
        # Test strings that will be repeated
        test_strings = [
            "日本語ファイル.txt",
            "mixed_英語_file.txt",
            "emoji_📁_folder",
        ]
        
        # First pass - populate cache
        import time
        start_time = time.time()
        for _ in range(100):
            for text in test_strings:
                tfm_wide_char_utils.get_display_width(text)
        first_pass_time = time.time() - start_time
        
        # Second pass - should use cache
        start_time = time.time()
        for _ in range(100):
            for text in test_strings:
                tfm_wide_char_utils.get_display_width(text)
        second_pass_time = time.time() - start_time
        
        # Cache should improve performance (second pass should be faster)
        # Allow some tolerance for timing variations
        self.assertLess(second_pass_time, first_pass_time * 1.5,
                       f"Cache didn't improve performance: {first_pass_time:.3f}s vs {second_pass_time:.3f}s")
        
        # Verify cache has entries
        cache_info = tfm_wide_char_utils.get_cache_info()
        self.assertGreater(cache_info['display_width_cache']['hits'], 0)
        
        print(f"Cache performance: {first_pass_time:.3f}s -> {second_pass_time:.3f}s")
        print(f"Cache info: {cache_info}")


if __name__ == '__main__':
    # Run the integration tests
    unittest.main(verbosity=2)