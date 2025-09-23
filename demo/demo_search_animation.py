#!/usr/bin/env python3
"""
Demo script showing SearchDialog animation patterns
Demonstrates the three different animation patterns available for search progress
"""

import sys
import time
import tempfile
import shutil
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_search_dialog import SearchDialog
from tfm_progress_animator import ProgressAnimator
from tfm_config import DefaultConfig


class SpinnerConfig(DefaultConfig):
    """Configuration for spinner animation"""
    PROGRESS_ANIMATION_PATTERN = 'spinner'
    PROGRESS_ANIMATION_SPEED = 0.15
    MAX_SEARCH_RESULTS = 2000


class DotsConfig(DefaultConfig):
    """Configuration for dots animation"""
    PROGRESS_ANIMATION_PATTERN = 'dots'
    PROGRESS_ANIMATION_SPEED = 0.2
    MAX_SEARCH_RESULTS = 2000


class ProgressConfig(DefaultConfig):
    """Configuration for progress bar animation"""
    PROGRESS_ANIMATION_PATTERN = 'progress'
    PROGRESS_ANIMATION_SPEED = 0.25
    MAX_SEARCH_RESULTS = 2000


def create_demo_structure():
    """Create demo directory structure for testing animations"""
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Created demo directory: {temp_dir}")
    
    # Create many files to ensure search takes time for animation
    for i in range(1500):
        (temp_dir / f"demo_file_{i:04d}.txt").write_text(f"Demo content {i}\nSecond line {i}")
        
        if i % 200 == 0:
            subdir = temp_dir / f"subdir_{i}"
            subdir.mkdir()
            for j in range(30):
                (subdir / f"nested_{j}.py").write_text(f"def demo_{i}_{j}():\n    return {i + j}")
                (subdir / f"data_{j}.json").write_text(f'{{"id": {j}, "value": "demo_{i}_{j}"}}')
    
    return temp_dir


def demo_animation_pattern(pattern_name, config_class, demo_dir):
    """Demonstrate a specific animation pattern"""
    print(f"\n{'='*60}")
    print(f"DEMO: {pattern_name.upper()} ANIMATION PATTERN")
    print(f"{'='*60}")
    
    config = config_class()
    search_dialog = SearchDialog(config)
    
    try:
        # Show pattern details
        animator = ProgressAnimator(config)
        pattern_name = getattr(config, 'PROGRESS_ANIMATION_PATTERN', 'spinner')
        pattern_frames = animator.patterns[pattern_name]
        print(f"Pattern: {pattern_name}")
        print(f"Frames: {' '.join(pattern_frames)}")
        print(f"Speed: {getattr(config, 'PROGRESS_ANIMATION_SPEED', 0.2)}s per frame")
        
        # Test filename search
        print(f"\n1. Testing {pattern_name} with filename search...")
        search_dialog.show('filename')
        search_dialog.text_editor.text = "*.txt"
        search_dialog.perform_search(demo_dir)
        
        # Show animation frames while searching
        frames_shown = []
        start_time = time.time()
        while search_dialog.searching and time.time() - start_time < 3:
            with search_dialog.search_lock:
                result_count = len(search_dialog.results)
                is_searching = search_dialog.searching
            
            if is_searching:
                progress_indicator = search_dialog.progress_animator.get_progress_indicator(f"{result_count} found", is_searching)
                frame = search_dialog.progress_animator.get_current_frame()
                
                if frame not in frames_shown:
                    frames_shown.append(frame)
                    print(f"   Frame: {frame} | Progress: '{progress_indicator.strip()}' | Results: {result_count}")
            
            time.sleep(0.1)
        
        # Final results
        with search_dialog.search_lock:
            final_count = len(search_dialog.results)
        print(f"   Final results: {final_count}")
        print(f"   Animation frames shown: {' → '.join(frames_shown)}")
        
        # Test content search
        print(f"\n2. Testing {pattern_name} with content search...")
        search_dialog.show('content')
        search_dialog.text_editor.text = "demo"
        search_dialog.perform_search(demo_dir)
        
        # Show a few animation frames
        content_frames = []
        start_time = time.time()
        while search_dialog.searching and time.time() - start_time < 2:
            with search_dialog.search_lock:
                result_count = len(search_dialog.results)
                is_searching = search_dialog.searching
            
            if is_searching:
                frame = search_dialog.progress_animator.get_current_frame()
                if frame not in content_frames:
                    content_frames.append(frame)
                    print(f"   Content search frame: {frame} | Results: {result_count}")
            
            time.sleep(0.1)
        
        with search_dialog.search_lock:
            final_content_count = len(search_dialog.results)
        print(f"   Final content results: {final_content_count}")
        
        print(f"\n✓ {pattern_name.upper()} animation demo completed!")
        
    finally:
        search_dialog.exit()


def demo_animation_comparison():
    """Compare all animation patterns side by side"""
    print(f"\n{'='*60}")
    print("ANIMATION PATTERN COMPARISON")
    print(f"{'='*60}")
    
    configs = [
        ('Spinner', SpinnerConfig()),
        ('Dots', DotsConfig()),
        ('Progress', ProgressConfig())
    ]
    
    print("\nAnimation frame sequences:")
    for name, config in configs:
        pattern_name = getattr(config, 'PROGRESS_ANIMATION_PATTERN', 'spinner')
        animator = ProgressAnimator(config)
        pattern_frames = animator.patterns[pattern_name]
        print(f"{name:>8}: {' → '.join(pattern_frames)}")
    
    print("\nProgress indicator examples:")
    for name, config in configs:
        pattern_name = getattr(config, 'PROGRESS_ANIMATION_PATTERN', 'spinner')
        animator = ProgressAnimator(config)
        
        # Show a few frames of progress indicator
        examples = []
        for i in range(min(5, len(animator.patterns[pattern_name]))):
            progress_text = animator.get_progress_indicator("42 found", True)
            examples.append(progress_text.strip())
            animator.frame_index = (animator.frame_index + 1) % len(animator.patterns[pattern_name])
        
        print(f"{name:>8}: {' | '.join(examples)}")
    
    print("\nConfiguration options:")
    for name, config in configs:
        print(f"{name:>8}: PROGRESS_ANIMATION_PATTERN = '{getattr(config, 'PROGRESS_ANIMATION_PATTERN', 'spinner')}'")
        print(f"{'':>8}  PROGRESS_ANIMATION_SPEED = {getattr(config, 'PROGRESS_ANIMATION_SPEED', 0.2)}")


def main():
    """Run the animation demo"""
    print("SearchDialog Animation Patterns Demo")
    print("This demo showcases the three available animation patterns for search progress")
    
    demo_dir = create_demo_structure()
    
    try:
        # Demo each animation pattern
        demo_animation_pattern("spinner", SpinnerConfig, demo_dir)
        demo_animation_pattern("dots", DotsConfig, demo_dir)
        demo_animation_pattern("progress", ProgressConfig, demo_dir)
        
        # Show comparison
        demo_animation_comparison()
        
        print(f"\n{'='*60}")
        print("DEMO COMPLETED SUCCESSFULLY!")
        print(f"{'='*60}")
        print("\nKey features demonstrated:")
        print("• Three animation patterns: spinner, dots, progress")
        print("• Configurable animation speed")
        print("• Smooth frame transitions during search")
        print("• Works with both filename and content searches")
        print("• Animation resets on new searches")
        print("• Thread-safe animation updates")
        
        print(f"\nTo use in your config:")
        print("# Progress animation settings")
        print("PROGRESS_ANIMATION_PATTERN = 'spinner'  # or 'dots', 'progress', 'bounce', 'pulse', etc.")
        print("PROGRESS_ANIMATION_SPEED = 0.2          # seconds per frame")
        
    except Exception as e:
        print(f"\nDemo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        shutil.rmtree(demo_dir)
        print(f"\nCleaned up demo directory")


if __name__ == "__main__":
    main()