#!/usr/bin/env python3
"""
Demo script showing generalized ProgressAnimator capabilities
Demonstrates how to use ProgressAnimator for various operations beyond search
"""

import sys
import time
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_progress_animator import ProgressAnimator, ProgressAnimatorFactory
from _config import Config


class DemoConfig(DefaultConfig):
    """Demo configuration"""
    PROGRESS_ANIMATION_PATTERN = 'pulse'
    PROGRESS_ANIMATION_SPEED = 0.2


def demo_all_patterns():
    """Demonstrate all available animation patterns"""
    print("\n" + "="*60)
    print("DEMO: ALL ANIMATION PATTERNS")
    print("="*60)
    
    config = DemoConfig()
    animator = ProgressAnimator(config)
    
    patterns = animator.get_available_patterns()
    print(f"Available patterns: {', '.join(patterns)}")
    
    for pattern in patterns:
        print(f"\n{pattern.upper()} Pattern:")
        animator.set_pattern(pattern)
        
        # Show pattern preview
        preview = animator.get_pattern_preview(pattern)
        print(f"  Frames: {' → '.join(preview)}")
        
        # Show animated sequence
        print("  Animation: ", end="", flush=True)
        for _ in range(len(preview)):
            frame = animator.get_current_frame()
            print(f"{frame} ", end="", flush=True)
            time.sleep(0.1)
        print()
        
        # Show different styles
        indicator_default = animator.get_progress_indicator("demo", True, 'default')
        indicator_brackets = animator.get_progress_indicator("demo", True, 'brackets')
        indicator_minimal = animator.get_progress_indicator("demo", True, 'minimal')
        
        print(f"  Styles: default='{indicator_default.strip()}', brackets='{indicator_brackets.strip()}', minimal='{indicator_minimal.strip()}'")


def demo_factory_methods():
    """Demonstrate factory methods for different use cases"""
    print("\n" + "="*60)
    print("DEMO: FACTORY METHODS FOR DIFFERENT USE CASES")
    print("="*60)
    
    config = DemoConfig()
    
    # Search operations
    print("\n1. SEARCH OPERATIONS")
    search_animator = ProgressAnimatorFactory.create_search_animator(config)
    print(f"   Pattern: {search_animator.animation_pattern}")
    print(f"   Speed: {search_animator.animation_speed}s")
    
    search_status = search_animator.get_status_text("Searching", "42 files found", True)
    print(f"   Status: {search_status}")
    
    # Loading operations
    print("\n2. LOADING OPERATIONS")
    loading_animator = ProgressAnimatorFactory.create_loading_animator(config)
    print(f"   Pattern: {loading_animator.animation_pattern}")
    print(f"   Speed: {loading_animator.animation_speed}s")
    
    loading_status = loading_animator.get_status_text("Loading", "75%", True)
    print(f"   Status: {loading_status}")
    
    # Processing operations
    print("\n3. PROCESSING OPERATIONS")
    processing_animator = ProgressAnimatorFactory.create_processing_animator(config)
    print(f"   Pattern: {processing_animator.animation_pattern}")
    print(f"   Speed: {processing_animator.animation_speed}s")
    
    processing_status = processing_animator.get_status_text("Processing", "1000 items", True)
    print(f"   Status: {processing_status}")
    
    # Custom operations
    print("\n4. CUSTOM OPERATIONS")
    custom_animator = ProgressAnimatorFactory.create_custom_animator(config, 'clock', 0.5)
    print(f"   Pattern: {custom_animator.animation_pattern}")
    print(f"   Speed: {custom_animator.animation_speed}s")
    
    custom_status = custom_animator.get_status_text("Synchronizing", "3 servers", True)
    print(f"   Status: {custom_status}")


def demo_real_world_scenarios():
    """Demonstrate real-world usage scenarios"""
    print("\n" + "="*60)
    print("DEMO: REAL-WORLD USAGE SCENARIOS")
    print("="*60)
    
    config = DemoConfig()
    
    scenarios = [
        {
            'name': 'File Copy Operation',
            'pattern': 'progress',
            'speed': 0.3,
            'operation': 'Copying',
            'contexts': ['1/10 files', '5/10 files', '10/10 files']
        },
        {
            'name': 'Network Download',
            'pattern': 'spinner',
            'speed': 0.15,
            'operation': 'Downloading',
            'contexts': ['0.5 MB', '2.1 MB', '5.0 MB']
        },
        {
            'name': 'Database Indexing',
            'pattern': 'wave',
            'speed': 0.25,
            'operation': 'Indexing',
            'contexts': ['100 records', '500 records', '1000 records']
        },
        {
            'name': 'System Backup',
            'pattern': 'pulse',
            'speed': 0.4,
            'operation': 'Backing up',
            'contexts': ['Documents', 'Pictures', 'Complete']
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name'].upper()}:")
        animator = ProgressAnimatorFactory.create_custom_animator(
            config, scenario['pattern'], scenario['speed']
        )
        
        print(f"  Using {scenario['pattern']} pattern at {scenario['speed']}s per frame")
        
        for i, context in enumerate(scenario['contexts']):
            is_active = i < len(scenario['contexts']) - 1
            status = animator.get_status_text(scenario['operation'], context, is_active)
            
            if is_active:
                # Show animated status
                print(f"  Step {i+1}: ", end="", flush=True)
                for _ in range(3):
                    frame = animator.get_current_frame()
                    print(f"\r  Step {i+1}: {scenario['operation']} {frame} ({context})", end="", flush=True)
                    time.sleep(scenario['speed'])
                print()
            else:
                print(f"  Final: {status}")


def demo_dynamic_configuration():
    """Demonstrate dynamic configuration changes"""
    print("\n" + "="*60)
    print("DEMO: DYNAMIC CONFIGURATION CHANGES")
    print("="*60)
    
    config = DemoConfig()
    animator = ProgressAnimator(config)
    
    print(f"Initial: {animator.animation_pattern} at {animator.animation_speed}s")
    
    # Demonstrate pattern switching
    patterns_to_try = ['spinner', 'dots', 'progress', 'bounce']
    
    for pattern in patterns_to_try:
        print(f"\nSwitching to {pattern}...")
        animator.set_pattern(pattern)
        
        print("  Animation: ", end="", flush=True)
        for _ in range(5):
            frame = animator.get_current_frame()
            print(f"{frame} ", end="", flush=True)
            time.sleep(0.1)
        print()
    
    # Demonstrate speed changes
    print(f"\nSpeed changes with {animator.animation_pattern} pattern:")
    speeds = [0.05, 0.2, 0.5]
    
    for speed in speeds:
        animator.set_speed(speed)
        print(f"  Speed {speed}s: ", end="", flush=True)
        
        for _ in range(5):
            frame = animator.get_current_frame()
            print(f"{frame}", end="", flush=True)
            time.sleep(speed)
        print()


def demo_status_text_variations():
    """Demonstrate different status text variations"""
    print("\n" + "="*60)
    print("DEMO: STATUS TEXT VARIATIONS")
    print("="*60)
    
    config = DemoConfig()
    animator = ProgressAnimator(config, 'spinner', 0.2)
    
    # Different operation types
    operations = [
        ("Loading", "configuration"),
        ("Scanning", "1,234 files"),
        ("Compressing", "archive.zip"),
        ("Uploading", "50% complete"),
        ("Validating", "checksums"),
    ]
    
    print("\nActive operations:")
    for operation, context in operations:
        status = animator.get_status_text(operation, context, True)
        print(f"  {status}")
        time.sleep(0.1)  # Let animation advance
    
    print("\nCompleted operations:")
    for operation, context in operations:
        status = animator.get_status_text(operation, context, False)
        print(f"  {status}")
    
    print("\nOperations without context:")
    simple_ops = ["Initializing", "Connecting", "Authenticating", "Finalizing"]
    
    for op in simple_ops:
        active_status = animator.get_status_text(op, None, True)
        complete_status = animator.get_status_text(op, None, False)
        print(f"  Active: {active_status}")
        print(f"  Complete: {complete_status}")
        print()


def demo_configuration_examples():
    """Show configuration examples"""
    print("\n" + "="*60)
    print("DEMO: CONFIGURATION EXAMPLES")
    print("="*60)
    
    print("\nBasic configuration in ~/.tfm/config.py:")
    print("""
class Config(DefaultConfig):
    # General animation settings (used by all components)
    ANIMATION_PATTERN = 'spinner'  # Default pattern for all animations
    ANIMATION_SPEED = 0.2          # Default speed for all animations
    
    # Progress animation settings
    PROGRESS_ANIMATION_PATTERN = 'spinner'  # Default pattern for all animations
    PROGRESS_ANIMATION_SPEED = 0.2          # Default speed for all animations
""")
    
    print("\nAdvanced usage in code:")
    print("""
# Use factory for common scenarios
search_animator = ProgressAnimatorFactory.create_search_animator(config)
loading_animator = ProgressAnimatorFactory.create_loading_animator(config)

# Create custom animators for specific needs
file_copy_animator = ProgressAnimatorFactory.create_custom_animator(
    config, 'progress', 0.3
)

# Dynamic configuration
animator = ProgressAnimator(config)
animator.set_pattern('wave')  # Change pattern at runtime
animator.set_speed(0.1)       # Change speed at runtime

# Generate status text
status = animator.get_status_text("Processing", "42 items", True)
# Output: "Processing ⠋ (42 items)"
""")


def main():
    """Run the generalized ProgressAnimator demo"""
    print("Generalized ProgressAnimator Demo")
    print("This demo showcases the versatile animation system for various operations")
    
    try:
        demo_all_patterns()
        demo_factory_methods()
        demo_real_world_scenarios()
        demo_dynamic_configuration()
        demo_status_text_variations()
        demo_configuration_examples()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nKey capabilities demonstrated:")
        print("• 8 different animation patterns (spinner, dots, progress, bounce, pulse, wave, clock, arrow)")
        print("• Factory methods for common use cases")
        print("• Dynamic pattern and speed changes")
        print("• Multiple indicator styles (default, brackets, minimal)")
        print("• Status text generation for any operation")
        print("• Real-world usage scenarios")
        print("• Flexible configuration system")
        
        print(f"\nThe ProgressAnimator is now generalized and can be used for:")
        print("• Search operations (existing)")
        print("• File operations (copy, move, delete)")
        print("• Network operations (download, upload)")
        print("• Processing operations (indexing, compression)")
        print("• Any long-running operation that needs visual feedback")
        
    except Exception as e:
        print(f"\nDemo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()