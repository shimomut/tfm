"""
Integration test for SearchDialog animation with main TFM components
Tests that animation works correctly in the full application context

Run with: PYTHONPATH=.:src:ttk pytest test/test_search_animation_integration.py -v
"""

from pathlib import Path
import time
import tempfile
import shutil

from tfm_search_dialog import SearchDialog, SearchDialogHelpers
from tfm_progress_animator import ProgressAnimator
from tfm_config import DefaultConfig
from tfm_pane_manager import PaneManager
from tfm_file_operations import FileOperations


class IntegrationTestConfig(DefaultConfig):
    """Test configuration for integration testing"""
    MAX_SEARCH_RESULTS = 100
    PROGRESS_ANIMATION_PATTERN = 'spinner'
    PROGRESS_ANIMATION_SPEED = 0.1


def create_integration_test_structure():
    """Create test directory structure for integration testing"""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create test files
    (temp_dir / "test.txt").write_text("Test content for searching")
    (temp_dir / "script.py").write_text("def test(): pass\nprint('hello world')")
    (temp_dir / "data.json").write_text('{"key": "value", "test": true}')
    
    # Create subdirectory
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.log").write_text("Log entry with test data\nAnother line")
    (subdir / "config.ini").write_text("[section]\nkey=value\ntest=true")
    
    return temp_dir


def test_animation_with_full_integration():
    """Test animation works with full TFM component integration"""
    print("Testing animation with full TFM integration...")
    
    config = IntegrationTestConfig()
    test_dir = create_integration_test_structure()
    
    try:
        # Initialize all components like in real TFM
        search_dialog = SearchDialog(config)
        pane_manager = PaneManager(config, test_dir, test_dir, None)
        file_operations = FileOperations(config)
        
        # Verify animation system is properly initialized
        assert hasattr(search_dialog, 'progress_animator')
        assert isinstance(search_dialog.progress_animator, ProgressAnimator)
        assert search_dialog.progress_animator.animation_pattern == 'spinner'
        
        # Test filename search with animation
        search_dialog.show('filename')
        search_dialog.text_editor.text = "*.txt"
        
        # Verify animation resets on show
        assert search_dialog.progress_animator.frame_index == 0
        
        # Start search
        search_dialog.perform_search(test_dir)
        
        # Verify animation resets on new search
        assert search_dialog.progress_animator.frame_index == 0
        
        # Wait for search to complete or show some animation
        start_time = time.time()
        animation_frames_seen = []
        
        while search_dialog.searching and time.time() - start_time < 2:
            frame = search_dialog.progress_animator.get_current_frame()
            if frame not in animation_frames_seen:
                animation_frames_seen.append(frame)
            time.sleep(0.05)
        
        # Wait for search completion
        while search_dialog.searching and time.time() - start_time < 5:
            time.sleep(0.1)
        
        # Check results
        with search_dialog.search_lock:
            results = search_dialog.results.copy()
        
        assert len(results) > 0, "Should find .txt files"
        
        # Test that we can navigate to results (animation should not interfere)
        if results:
            result = results[0]
            
            messages = []
            def mock_print(msg):
                messages.append(msg)
            
            # Test navigation works with animation system present
            SearchDialogHelpers.navigate_to_result(
                result, pane_manager, file_operations, mock_print
            )
            
            assert len(messages) > 0, "Navigation should work with animation"
        
        print("✓ Full integration with animation test passed")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def test_animation_configuration_integration():
    """Test that animation configuration is properly integrated"""
    print("Testing animation configuration integration...")
    
    # Test different configurations
    configs_to_test = [
        ('spinner', 0.1),
        ('dots', 0.2),
        ('progress', 0.15)
    ]
    
    for pattern, speed in configs_to_test:
        class TestConfig(DefaultConfig):
            PROGRESS_ANIMATION_PATTERN = pattern
            PROGRESS_ANIMATION_SPEED = speed
        
        config = TestConfig()
        search_dialog = SearchDialog(config)
        
        # Verify configuration is applied
        assert search_dialog.progress_animator.animation_pattern == pattern
        assert search_dialog.progress_animator.animation_speed == speed
        
        # Verify pattern exists and is valid
        assert pattern in search_dialog.progress_animator.patterns
        pattern_frames = search_dialog.progress_animator.patterns[pattern]
        assert len(pattern_frames) > 0
        
        # Test frame generation
        frame = search_dialog.progress_animator.get_current_frame()
        assert frame in pattern_frames
        
        search_dialog.exit()
    
    print("✓ Animation configuration integration test passed")


def test_animation_thread_safety_integration():
    """Test animation thread safety in integration context"""
    print("Testing animation thread safety in integration...")
    
    config = IntegrationTestConfig()
    search_dialog = SearchDialog(config)
    test_dir = create_integration_test_structure()
    
    try:
        search_dialog.show('filename')
        search_dialog.text_editor.text = "*"
        
        # Start search
        search_dialog.perform_search(test_dir)
        
        # Simulate concurrent access to animation and search results
        import threading
        
        def access_animation():
            for _ in range(50):
                frame = search_dialog.progress_animator.get_current_frame()
                progress = search_dialog.progress_animator.get_progress_indicator(10, True)
                time.sleep(0.01)
        
        def access_results():
            for _ in range(50):
                with search_dialog.search_lock:
                    result_count = len(search_dialog.results)
                    is_searching = search_dialog.searching
                time.sleep(0.01)
        
        # Start multiple threads
        threads = []
        for _ in range(3):
            t1 = threading.Thread(target=access_animation)
            t2 = threading.Thread(target=access_results)
            threads.extend([t1, t2])
            t1.start()
            t2.start()
        
        # Wait for threads to complete
        for thread in threads:
            thread.join()
        
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and time.time() - start_time < 5:
            time.sleep(0.1)
        
        print("✓ Animation thread safety integration test passed")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def test_animation_with_search_cancellation():
    """Test animation behavior when search is cancelled"""
    print("Testing animation with search cancellation...")
    
    config = IntegrationTestConfig()
    search_dialog = SearchDialog(config)
    test_dir = create_integration_test_structure()
    
    try:
        search_dialog.show('filename')
        search_dialog.text_editor.text = "*"
        
        # Start search
        search_dialog.perform_search(test_dir)
        
        # Let animation run for a bit
        time.sleep(0.2)
        
        # Get current animation state
        frame_before_cancel = search_dialog.progress_animator.frame_index
        
        # Cancel search by clearing pattern
        search_dialog.text_editor.text = ""
        search_dialog.perform_search(test_dir)
        
        # Verify search is cancelled
        assert not search_dialog.searching
        
        # Verify animation state is maintained (not reset by cancellation)
        # Animation should continue from where it was
        
        # Test that animation still works after cancellation
        frame = search_dialog.progress_animator.get_current_frame()
        assert frame is not None
        
        # Start new search
        search_dialog.text_editor.text = "*.py"
        search_dialog.perform_search(test_dir)
        
        # Animation should reset for new search
        assert search_dialog.progress_animator.frame_index == 0
        
        print("✓ Animation with search cancellation test passed")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(test_dir)


def test_animation_performance_impact():
    """Test that animation doesn't significantly impact search performance"""
    print("Testing animation performance impact...")
    
    # Test with animation
    config_with_animation = IntegrationTestConfig()
    
    # Test without animation (simulate by using very slow speed)
    class NoAnimationConfig(DefaultConfig):
        PROGRESS_ANIMATION_PATTERN = 'spinner'
        PROGRESS_ANIMATION_SPEED = 999  # Very slow, effectively no animation
        MAX_SEARCH_RESULTS = 100
    
    test_dir = create_integration_test_structure()
    
    try:
        # Time search with animation
        search_dialog_animated = SearchDialog(config_with_animation)
        search_dialog_animated.show('filename')
        search_dialog_animated.text_editor.text = "*"
        
        start_time = time.time()
        search_dialog_animated.perform_search(test_dir)
        
        while search_dialog_animated.searching:
            time.sleep(0.01)
        
        animated_time = time.time() - start_time
        
        with search_dialog_animated.search_lock:
            animated_results = len(search_dialog_animated.results)
        
        search_dialog_animated.exit()
        
        # Time search without animation
        search_dialog_no_anim = SearchDialog(NoAnimationConfig())
        search_dialog_no_anim.show('filename')
        search_dialog_no_anim.text_editor.text = "*"
        
        start_time = time.time()
        search_dialog_no_anim.perform_search(test_dir)
        
        while search_dialog_no_anim.searching:
            time.sleep(0.01)
        
        no_anim_time = time.time() - start_time
        
        with search_dialog_no_anim.search_lock:
            no_anim_results = len(search_dialog_no_anim.results)
        
        search_dialog_no_anim.exit()
        
        # Verify results are the same
        assert animated_results == no_anim_results
        
        # Animation should not significantly slow down search
        # Allow up to 50% overhead (very generous)
        performance_ratio = animated_time / no_anim_time if no_anim_time > 0 else 1
        assert performance_ratio < 1.5, f"Animation overhead too high: {performance_ratio:.2f}x"
        
        print(f"   Animation time: {animated_time:.3f}s")
        print(f"   No animation time: {no_anim_time:.3f}s")
        print(f"   Performance ratio: {performance_ratio:.2f}x")
        print("✓ Animation performance impact test passed")
        
    finally:
        shutil.rmtree(test_dir)


def main():
    """Run all integration tests"""
    print("Running SearchDialog animation integration tests...")
    print("=" * 60)
    
    try:
        test_animation_with_full_integration()
        test_animation_configuration_integration()
        test_animation_thread_safety_integration()
        test_animation_with_search_cancellation()
        test_animation_performance_impact()
        
        print("=" * 60)
        print("✓ All animation integration tests passed!")
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
