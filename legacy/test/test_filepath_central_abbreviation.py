"""
Test filepath abbreviation with central-first removal order.

This test verifies that FilepathSegment removes directory levels from the
center outward, keeping left and right un-abbreviated levels balanced.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_text_layout import FilepathSegment
from ttk.wide_char_utils import get_display_width


def test_central_first_abbreviation():
    """
    Test that directories are removed from center outward with RIGHT-LEFT alternation.
    
    Path structure (7 directories + filename):
    0: Users
    1: shimomut
    2: projects
    3: awsome-distributed-training (center, should be removed 1st)
    4: 1.architectures
    5: 7.sagemaker-hyperpod-eks
    6: LifecycleScripts
    7: base-config (filename)
    
    Expected removal order: 3 (center), 4 (right), 2 (left), 5 (right), 1 (left), 6 (right), 0 (left)
    This maintains balance because filename is always on the right side.
    """
    path = "/Users/shimomut/projects/awsome-distributed-training/1.architectures/7.sagemaker-hyperpod-eks/LifecycleScripts/base-config"
    
    # Test removal of first directory (awsome-distributed-training, the center)
    segment = FilepathSegment(path, priority=0, min_length=10)
    result = segment.shorten(115)
    assert "awsome-distributed-training" not in result, "First removal should remove 'awsome-distributed-training' (center)"
    assert "projects" in result, "Should still have 'projects'"
    assert "1.architectures" in result, "Should still have '1.architectures'"
    assert "Users" in result, "Should still have 'Users'"
    assert "shimomut" in result, "Should still have 'shimomut'"
    
    # Test removal of second directory (1.architectures, right of center)
    result = segment.shorten(87)
    assert "awsome-distributed-training" not in result, "Should not have 'awsome-distributed-training'"
    assert "1.architectures" not in result, "Second removal should remove '1.architectures' (right)"
    assert "projects" in result, "Should still have 'projects'"
    assert "Users" in result, "Should still have 'Users'"
    assert "shimomut" in result, "Should still have 'shimomut'"
    assert "7.sagemaker-hyperpod-eks" in result, "Should still have '7.sagemaker-hyperpod-eks'"
    
    # Test removal of third directory (projects, left of center)
    result = segment.shorten(71)
    assert "projects" not in result, "Third removal should remove 'projects' (left)"
    assert "shimomut" in result, "Should still have 'shimomut'"
    assert "7.sagemaker-hyperpod-eks" in result, "Should still have '7.sagemaker-hyperpod-eks'"
    
    # Test removal of fourth directory (7.sagemaker-hyperpod-eks, right)
    result = segment.shorten(62)
    assert "7.sagemaker-hyperpod-eks" not in result, "Fourth removal should remove '7.sagemaker-hyperpod-eks' (right)"
    assert "shimomut" in result, "Should still have 'shimomut'"
    assert "Users" in result, "Should still have 'Users'"
    assert "LifecycleScripts" in result, "Should still have 'LifecycleScripts'"
    
    # Test removal of fifth directory (shimomut, left)
    result = segment.shorten(37)
    assert "shimomut" not in result, "Fifth removal should remove 'shimomut' (left)"
    assert "Users" in result, "Should still have 'Users'"
    assert "LifecycleScripts" in result, "Should still have 'LifecycleScripts'"
    assert "base-config" in result, "Should always have filename"


def test_balanced_left_right():
    """
    Test that left and right un-abbreviated levels stay balanced.
    
    Rule: left_count <= right_count (where right includes the filename)
    This means: left <= (right_dirs + 1)
    """
    path = "/Users/shimomut/projects/awsome-distributed-training/1.architectures/7.sagemaker-hyperpod-eks/LifecycleScripts/base-config"
    
    segment = FilepathSegment(path, priority=0, min_length=10)
    
    # Test various widths and verify balance at each step
    test_cases = [
        (115, "After removing 1 directory (center)"),
        (87, "After removing 2 directories"),
        (71, "After removing 3 directories"),
        (62, "After removing 4 directories"),
    ]
    
    for width, description in test_cases:
        result = segment.shorten(width)
        parts = result.split('/')
        ellipsis_idx = parts.index('…') if '…' in parts else -1
        
        if ellipsis_idx > 0:
            left_count = ellipsis_idx - 1  # -1 for root
            right_dirs_count = len(parts) - ellipsis_idx - 2  # -2 for ellipsis and filename
            right_total_count = right_dirs_count + 1  # +1 for filename
            
            # Rule: left <= right_total (where right_total includes filename)
            assert left_count <= right_total_count, (
                f"{description}: Left ({left_count}) should be <= right total ({right_total_count} = {right_dirs_count} dirs + 1 file)"
            )
            assert right_total_count - left_count <= 1, (
                f"{description}: Right total ({right_total_count}) - left ({left_count}) = "
                f"{right_total_count - left_count}, should be 0 or 1"
            )


def test_ellipsis_placement():
    """Test that ellipsis is placed correctly in the middle."""
    path = "/Users/shimomut/projects/awsome-distributed-training/1.architectures/7.sagemaker-hyperpod-eks/LifecycleScripts/base-config"
    
    segment = FilepathSegment(path, priority=0, min_length=10)
    
    # When directories are removed, ellipsis should appear
    result = segment.shorten(100)
    assert '…' in result, "Should have ellipsis when directories are removed"
    
    # Ellipsis should be in the middle, not at the start or end
    parts = result.split('/')
    ellipsis_idx = parts.index('…')
    assert ellipsis_idx > 0, "Ellipsis should not be at the start"
    assert ellipsis_idx < len(parts) - 1, "Ellipsis should not be at the end"


if __name__ == '__main__':
    test_central_first_abbreviation()
    print("✓ Central-first abbreviation test passed")
    
    test_balanced_left_right()
    print("✓ Balanced left-right test passed")
    
    test_ellipsis_placement()
    print("✓ Ellipsis placement test passed")
    
    print("\nAll tests passed!")
