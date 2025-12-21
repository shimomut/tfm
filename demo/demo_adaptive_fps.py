#!/usr/bin/env python3
"""
Demo: Adaptive FPS CPU Optimization

This demo demonstrates the adaptive FPS system that reduces CPU usage during
idle periods by automatically lowering the frame rate from 60 FPS to 1 FPS.

Features demonstrated:
- Automatic FPS reduction during idle periods
- Immediate FPS restoration on activity
- Smooth FPS degradation based on idle time
- CPU usage optimization

Test scenarios:
1. Launch TFM and observe initial 60 FPS
2. Stop interacting and watch FPS gradually reduce:
   - 0.5s idle: 30 FPS
   - 2s idle: 15 FPS
   - 5s idle: 5 FPS
   - 10s idle: 1 FPS
3. Press any key and observe immediate return to 60 FPS
4. Monitor CPU usage with Activity Monitor/top to see reduction

Expected behavior:
- Active use: 60 FPS, normal CPU usage
- Idle periods: 1 FPS, minimal CPU usage
- Instant response: Any input immediately restores 60 FPS

To monitor FPS in real-time, you can enable profiling mode:
    python tfm.py --profile

The adaptive FPS manager is always active and requires no configuration.
"""

import sys
import os

# Add parent directory to path to import TFM modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tfm_adaptive_fps import AdaptiveFPSManager
import time


def demo_fps_transitions():
    """Demonstrate FPS transitions during idle periods."""
    print("Adaptive FPS Demo")
    print("=" * 60)
    print()
    print("This demo shows how FPS adapts based on activity:")
    print()
    
    fps_manager = AdaptiveFPSManager()
    
    # Simulate active period
    print("1. Active period (events occurring):")
    for i in range(5):
        fps_manager.mark_activity()
        timeout = fps_manager.get_timeout_ms()
        current_fps = fps_manager.get_current_fps()
        print(f"   Event {i+1}: FPS={current_fps}, timeout={timeout}ms")
        time.sleep(0.1)
    
    print()
    print("2. Idle period (no events, watching FPS degrade):")
    
    # Simulate idle period with periodic checks
    idle_checkpoints = [0, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 12.0]
    start_time = time.time()
    
    for checkpoint in idle_checkpoints:
        # Wait until checkpoint
        while time.time() - start_time < checkpoint:
            time.sleep(0.1)
        
        timeout = fps_manager.get_timeout_ms()
        current_fps = fps_manager.get_current_fps()
        idle_time = time.time() - start_time
        print(f"   {idle_time:.1f}s idle: FPS={current_fps}, timeout={timeout}ms")
    
    print()
    print("3. Activity resumes (immediate FPS restoration):")
    fps_manager.mark_activity()
    timeout = fps_manager.get_timeout_ms()
    current_fps = fps_manager.get_current_fps()
    print(f"   Event received: FPS={current_fps}, timeout={timeout}ms")
    
    print()
    print("4. Rendering occurs (marks activity via UILayerStack):")
    fps_manager.mark_activity()
    timeout = fps_manager.get_timeout_ms()
    current_fps = fps_manager.get_current_fps()
    print(f"   Render triggered: FPS={current_fps}, timeout={timeout}ms")
    
    print()
    print("=" * 60)
    print("Demo complete!")
    print()
    print("In TFM, this happens automatically:")
    print("- Any key press, mouse event, or UI change triggers 60 FPS")
    print("- UILayerStack marks activity when rendering occurs")
    print("- During idle periods, FPS gradually reduces to save CPU")
    print("- No configuration needed - it just works!")


if __name__ == '__main__':
    demo_fps_transitions()
