#!/usr/bin/env python3
"""
Test file for SearchDialog animation functionality
Tests the progress indicator animation system
"""

import sys
import time
import tempfile
import shutil
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_search_dialog import SearchDialog
from tfm_progress_animator import ProgressAnimator, ProgressAnimatorFactory
from tfm_config import DefaultConfig


class AnimationTestConfig(DefaultConfig):
    """Test configuration for animation testing"""
    MAX_SEARCH_RESULTS = 100
    ANIMATION_PATTERN = 'spinner'
    ANIMATION_SPEED = 0.1  # Faster for testing


class SpinnerTestConfig(DefaultConfig):
    """Test configuration for spinner animation"""
    ANIMATION_PATTERN = 'spinner'
    ANIMATION_SPEED = 0.1


class DotsTestConfig(DefaultConfig):
    """Test configuration for dots animation"""
    ANIMATION_PATTERN = 'dots'
    ANIMATION_SPEED = 0.1


class ProgressTestConfig(DefaultConfig):
    """Test configuration for progress animation"""
    ANIMATION_PATTERN = 'progress'
    ANIMATION_SPEED = 0.1


def test_progress_animator_basic():
    """Test basic progress animator functionality"""
    print("Testing basic progress animator functionality...")
    
    config = AnimationTestConfig()
    animator = ProgressAnimator(config)
    
    # Test initial state
    assert animator.frame_index == 0
    assert animator.animation_pattern == 'spinner'
    assert animator.animation_speed == 0.1
    
    # Test frame progression
    first_frame = animator.get_current_frame()
    assert first_frame in animator.patterns['spinner']
    
    # Wait for animation speed and get next frame
    time.sleep(0.11)  # Slightly longer than animation speed
    second_frame = animator.get_current_frame()
    
    # Frame should have advanced
    assert animator.frame_index > 0
    
    # Test reset
    animator.reset()
    assert animator.frame_index == 0
    
    print("✓ Basic progress animator test passed")


def test_animation_patterns():
    """Test all animation patterns"""
    print("Testing all animation patterns...")
    
    patterns_to_test = [
        ('spinner', SpinnerTestConfig()),
        ('dots', DotsTestConfig()),
        ('progress', ProgressTestConfig())
    ]
    
    for pattern_name, config in patterns_to_test:
        print(f"  Testing {pattern_name} pattern...")
        
        animator = ProgressAnimatorFactory.create_search_animator(config)
        assert animator.animation_pattern == pattern_name
        
        # Test that we get valid frames
        frames_seen = set()
        for _ in range(20):  # Test multiple frames
            frame = animator.get_current_frame()
            assert frame in animator.patterns[pattern_name]
            frames_seen.add(frame)
            time.sleep(0.05)  # Small delay
        
        # Should have seen multiple different frames
        assert len(frames_seen) > 1, f"Should see multiple frames for {pattern_name}"
        
        # Test progress indicator formatting
        progress_text = animator.get_progress_indicator(context_info="5 found", is_active=True)
        assert isinstance(progress_text, str)
        assert len(progress_text) > 0
        
        # Test when not active
        no_progress_text = animator.get_progress_indicator(context_info="5 found", is_active=False)
        assert no_progress_text == ""
        
        print(f"    ✓ {pattern_name} pattern works correctly")
    
    print("✓ All animation patterns test passed")


def test_search_dialog_animation_integration():
    """Test animation integration with SearchDialog"""
    print("Testing SearchDialog animation integration...")
    
    config = AnimationTestConfig()
    search_dialog = SearchDialog(config)
    
    # Verify animator is created
    assert hasattr(search_dialog, 'progress_animator')
    assert isinstance(search_dialog.progress_animator, ProgressAnimator)
    
    # Test show resets animation
    search_dialog.show('filename')
    assert search_dialog.progress_animator.frame_index == 0
    
    # Test exit resets animation
    search_dialog.progress_animator.frame_index = 5  # Simulate some animation progress
    search_dialog.exit()
    assert search_dialog.progress_animator.frame_index == 0
    
    print("✓ SearchDialog animation integration test passed")


def test_animation_with_actual_search():
    """Test animation during actual search operation"""
    print("Testing animation during actual search...")
    
    config = AnimationTestConfig()
    search_dialog = SearchDialog(config)
    
    # Create test directory
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Create some files for searching
        for i in range(50):
            (temp_dir / f"test_file_{i:03d}.txt").write_text(f"Test content {i}")
        
        search_dialog.show('filename')
        search_dialog.pattern_editor.text = "*.txt"
        
        # Start search
        search_dialog.perform_search(temp_dir)
        
        # Verify animation resets on new search
        assert search_dialog.progress_animator.frame_index == 0
        
        # Wait a bit and check that animation progresses during search
        if search_dialog.searching:
            time.sleep(0.15)  # Wait longer than animation speed
            # Animation should have progressed if search is still running
            # (might complete quickly on fast systems)
            
        # Wait for search to complete
        start_time = time.time()
        while search_dialog.searching and time.time() - start_time < 3:
            time.sleep(0.05)
        
        # Verify we got results
        with search_dialog.search_lock:
            assert len(search_dialog.results) > 0
        
        print("✓ Animation during actual search test passed")
        
    finally:
        search_dialog.exit()
        shutil.rmtree(temp_dir)


def test_animation_frame_cycling():
    """Test that animation frames cycle correctly"""
    print("Testing animation frame cycling...")
    
    config = SpinnerTestConfig()
    animator = ProgressAnimatorFactory.create_search_animator(config)
    
    pattern = animator.patterns['spinner']
    pattern_length = len(pattern)
    
    # Collect frames over multiple cycles
    frames_collected = []
    for _ in range(pattern_length * 2 + 5):  # More than 2 full cycles
        frame = animator.get_current_frame()
        frames_collected.append(frame)
        time.sleep(0.11)  # Wait for frame update
    
    # Verify we see the pattern repeat
    assert len(frames_collected) > pattern_length
    
    # Check that we cycle through all frames in the pattern
    unique_frames = set(frames_collected)
    assert len(unique_frames) == pattern_length, f"Should see all {pattern_length} frames"
    
    # Verify all frames are from the correct pattern
    for frame in unique_frames:
        assert frame in pattern
    
    print("✓ Animation frame cycling test passed")


def test_animation_speed_configuration():
    """Test animation speed configuration"""
    print("Testing animation speed configuration...")
    
    # Test fast animation
    class FastConfig(DefaultConfig):
        ANIMATION_SPEED = 0.05
    
    # Test slow animation  
    class SlowConfig(DefaultConfig):
        ANIMATION_SPEED = 0.3
    
    fast_animator = ProgressAnimatorFactory.create_search_animator(FastConfig())
    slow_animator = ProgressAnimatorFactory.create_search_animator(SlowConfig())
    
    assert fast_animator.animation_speed == 0.05
    assert slow_animator.animation_speed == 0.3
    
    # Test that fast animation updates more frequently
    fast_animator.get_current_frame()
    slow_animator.get_current_frame()
    
    time.sleep(0.1)  # Wait between fast and slow speeds
    
    fast_frame_after = fast_animator.get_current_frame()
    slow_frame_after = slow_animator.get_current_frame()
    
    # Fast should have updated, slow might not have
    assert fast_animator.frame_index > 0
    # Slow animator might or might not have updated depending on timing
    
    print("✓ Animation speed configuration test passed")


def test_generalized_progress_animator():
    """Test the generalized ProgressAnimator features"""
    print("Testing generalized ProgressAnimator features...")
    
    config = AnimationTestConfig()
    animator = ProgressAnimator(config)
    
    # Test available patterns
    patterns = animator.get_available_patterns()
    assert 'spinner' in patterns
    assert 'dots' in patterns
    assert 'progress' in patterns
    assert 'bounce' in patterns
    assert 'pulse' in patterns
    
    # Test pattern switching
    animator.set_pattern('dots')
    assert animator.animation_pattern == 'dots'
    frame = animator.get_current_frame()
    assert frame in animator.patterns['dots']
    
    # Test speed changing
    animator.set_speed(0.05)
    assert animator.animation_speed == 0.05
    
    # Test pattern preview
    preview = animator.get_pattern_preview('pulse')
    assert len(preview) > 0
    assert all(frame in animator.patterns['pulse'] for frame in preview)
    
    # Test status text generation
    status = animator.get_status_text("Loading", "50%", True)
    assert "Loading" in status
    assert "50%" in status
    
    status_complete = animator.get_status_text("Loading", "100%", False)
    assert "complete" in status_complete
    
    print("✓ Generalized ProgressAnimator features test passed")


def test_progress_animator_factory():
    """Test the ProgressAnimatorFactory"""
    print("Testing ProgressAnimatorFactory...")
    
    config = AnimationTestConfig()
    
    # Test different factory methods
    search_animator = ProgressAnimatorFactory.create_search_animator(config)
    loading_animator = ProgressAnimatorFactory.create_loading_animator(config)
    processing_animator = ProgressAnimatorFactory.create_processing_animator(config)
    custom_animator = ProgressAnimatorFactory.create_custom_animator(config, 'pulse', 0.1)
    
    # Verify they're all ProgressAnimator instances
    assert isinstance(search_animator, ProgressAnimator)
    assert isinstance(loading_animator, ProgressAnimator)
    assert isinstance(processing_animator, ProgressAnimator)
    assert isinstance(custom_animator, ProgressAnimator)
    
    # Verify custom settings
    assert custom_animator.animation_pattern == 'pulse'
    assert custom_animator.animation_speed == 0.1
    
    # Verify loading animator defaults
    assert loading_animator.animation_pattern == 'spinner'
    assert loading_animator.animation_speed == 0.15
    
    # Verify processing animator defaults
    assert processing_animator.animation_pattern == 'progress'
    assert processing_animator.animation_speed == 0.25
    
    print("✓ ProgressAnimatorFactory test passed")


def main():
    """Run all animation tests"""
    print("Running SearchDialog animation tests...")
    print("=" * 50)
    
    try:
        test_progress_animator_basic()
        test_animation_patterns()
        test_search_dialog_animation_integration()
        test_animation_with_actual_search()
        test_animation_frame_cycling()
        test_animation_speed_configuration()
        test_generalized_progress_animator()
        test_progress_animator_factory()
        
        print("=" * 50)
        print("✓ All animation tests passed!")
        
    except Exception as e:
        print(f"✗ Animation test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()