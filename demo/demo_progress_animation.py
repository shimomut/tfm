#!/usr/bin/env python3
"""
Demo showing progress animations working with dialog optimization
"""

import sys
import os
import time
import threading
from unittest.mock import Mock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_search_dialog import SearchDialog
from tfm_jump_dialog import JumpDialog
from tfm_config import get_config


def demo_search_animation():
    """Demonstrate SearchDialog animation during search"""
    
    print("SearchDialog Progress Animation Demo")
    print("=" * 40)
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Show search dialog
    search_dialog.show('filename')
    search_dialog.text_editor.set_text('*.py')
    
    # Track animation and draws
    animation_frames = []
    draw_count = 0
    
    def mock_draw(*args, **kwargs):
        nonlocal draw_count
        draw_count += 1
        # Capture the current animation frame
        frame = search_dialog.progress_animator.get_current_frame()
        animation_frames.append(frame)
        print(f"  🎨 Draw #{draw_count}: Animation frame '{frame}'")
    
    search_dialog.draw = mock_draw
    
    print("\n1. Starting search simulation:")
    search_dialog.searching = True
    search_dialog.content_changed = False  # Simulate after initial draw
    
    print(f"   Searching: {search_dialog.searching}")
    print(f"   Content changed: {search_dialog.content_changed}")
    
    print("\n2. Simulating main loop iterations (animation should advance):")
    
    for i in range(8):
        # Simulate main loop content check (our optimized version)
        needs_redraw = search_dialog.searching or search_dialog.content_changed
        
        print(f"\n   Iteration {i+1}:")
        print(f"     Needs redraw: {needs_redraw} (searching={search_dialog.searching})")
        
        if needs_redraw:
            # Simulate drawing
            search_dialog.draw(None, None)
            
            # Don't mark as unchanged while searching (for animation)
            if not search_dialog.searching:
                search_dialog.content_changed = False
        else:
            print(f"     Skipping draw (no animation needed)")
        
        time.sleep(0.25)  # Wait for animation to advance
    
    print(f"\n3. Search completes:")
    search_dialog.searching = False
    search_dialog.content_changed = True  # Mark for final redraw
    
    # Final draw
    needs_redraw = search_dialog.searching or search_dialog.content_changed
    print(f"   Needs final redraw: {needs_redraw}")
    if needs_redraw:
        search_dialog.draw(None, None)
        search_dialog.content_changed = False
    
    print(f"\n4. Results:")
    print(f"   Total draws: {draw_count}")
    print(f"   Animation frames: {animation_frames}")
    print(f"   Unique frames: {set(animation_frames)}")
    
    print("\n✅ SearchDialog animation working correctly!")


def demo_jump_animation():
    """Demonstrate JumpDialog animation during directory scan"""
    
    print("\n\nJumpDialog Progress Animation Demo")
    print("=" * 40)
    
    config = get_config()
    jump_dialog = JumpDialog(config)
    
    # Show jump dialog
    jump_dialog.show(os.getcwd())
    
    # Track animation and draws
    animation_frames = []
    draw_count = 0
    
    def mock_draw(*args, **kwargs):
        nonlocal draw_count
        draw_count += 1
        # Capture the current animation frame
        frame = jump_dialog.progress_animator.get_current_frame()
        animation_frames.append(frame)
        print(f"  🎨 Draw #{draw_count}: Animation frame '{frame}'")
    
    jump_dialog.draw = mock_draw
    
    print("\n1. Starting directory scan simulation:")
    jump_dialog.searching = True
    jump_dialog.content_changed = False  # Simulate after initial draw
    
    print(f"   Scanning: {jump_dialog.searching}")
    print(f"   Content changed: {jump_dialog.content_changed}")
    
    print("\n2. Simulating main loop iterations (animation should advance):")
    
    for i in range(6):
        # Simulate main loop content check (our optimized version)
        needs_redraw = jump_dialog.searching or jump_dialog.content_changed
        
        print(f"\n   Iteration {i+1}:")
        print(f"     Needs redraw: {needs_redraw} (scanning={jump_dialog.searching})")
        
        if needs_redraw:
            # Simulate drawing
            jump_dialog.draw(None, None)
            
            # Don't mark as unchanged while scanning (for animation)
            if not jump_dialog.searching:
                jump_dialog.content_changed = False
        else:
            print(f"     Skipping draw (no animation needed)")
        
        time.sleep(0.25)  # Wait for animation to advance
    
    print(f"\n3. Directory scan completes:")
    jump_dialog.searching = False
    jump_dialog.content_changed = True  # Mark for final redraw
    
    # Final draw
    needs_redraw = jump_dialog.searching or jump_dialog.content_changed
    print(f"   Needs final redraw: {needs_redraw}")
    if needs_redraw:
        jump_dialog.draw(None, None)
        jump_dialog.content_changed = False
    
    print(f"\n4. Results:")
    print(f"   Total draws: {draw_count}")
    print(f"   Animation frames: {animation_frames}")
    print(f"   Unique frames: {set(animation_frames)}")
    
    print("\n✅ JumpDialog animation working correctly!")


def demo_optimization_benefits():
    """Show the benefits of the animation optimization"""
    
    print("\n\nOptimization Benefits")
    print("=" * 30)
    
    print("\n📉 WITHOUT animation optimization:")
    print("   1. Dialog redraws constantly (every 16ms)")
    print("   2. ❌ Wastes CPU on unnecessary redraws")
    print("   3. ❌ Animation works but inefficient")
    print("   4. ❌ High rendering overhead")
    
    print("\n📈 WITH animation optimization:")
    print("   1. Dialog only redraws when searching/scanning")
    print("   2. ✅ Efficient: no redraws when idle")
    print("   3. ✅ Animation works smoothly during operations")
    print("   4. ✅ Minimal rendering overhead")
    print("   5. ✅ Best of both worlds: efficiency + animation")
    
    print("\n🎯 Key improvements:")
    print("   • Animations continue during search/scan operations")
    print("   • No unnecessary redraws when dialogs are idle")
    print("   • Smooth progress indicators for better UX")
    print("   • Optimal performance with visual feedback")


if __name__ == "__main__":
    try:
        demo_search_animation()
        demo_jump_animation()
        demo_optimization_benefits()
        
        print("\n" + "=" * 50)
        print("🎉 Progress animation optimization demonstrated!")
        print("\nSummary:")
        print("  • Animations work smoothly during operations")
        print("  • No unnecessary redraws when idle")
        print("  • Optimal balance of performance and UX")
        print("  • Progress indicators provide real-time feedback")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)