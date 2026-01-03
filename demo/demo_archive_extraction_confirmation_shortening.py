#!/usr/bin/env python3
"""
Demo: Archive Extraction Confirmation Message Shortening

This demo shows how the archive extraction confirmation message intelligently
shortens to fit narrow terminals using two different strategies:

1. Archive name: AllOrNothing strategy - either shows full "'archive.tar.gz' " or removes it entirely
2. Destination path: Abbreviation with filepath mode - intelligently shortens the path

The archive name has higher priority (shortened first), while the destination
path has lower priority (more important, shortened last).
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_string_width import reduce_width, ShorteningRegion, calculate_display_width


def demo_extraction_confirmation_shortening():
    """Demonstrate archive extraction confirmation message shortening"""
    
    print("=" * 80)
    print("Archive Extraction Confirmation Message Shortening Demo")
    print("=" * 80)
    print()
    
    # Test cases with different archive names and destination paths
    test_cases = [
        {
            'archive': 'backup.tar.gz',
            'destination': '/home/user/documents/projects/2024/important_files',
            'description': 'Short archive name, long destination path'
        },
        {
            'archive': 'very_long_archive_name_with_timestamp_20240102.tar.gz',
            'destination': '/home/user/downloads',
            'description': 'Long archive name, short destination path'
        },
        {
            'archive': 'data.zip',
            'destination': '/mnt/external/backup/archives/2024/january/week1/monday',
            'description': 'Very short archive name, very long destination path'
        },
        {
            'archive': 'project_backup_final_v2_20240102_compressed.tar.gz',
            'destination': '/var/backups/system/critical/databases/production/daily',
            'description': 'Both archive name and destination are long'
        }
    ]
    
    # Test different terminal widths
    terminal_widths = [120, 80, 60, 40, 30]
    
    for i, test_case in enumerate(test_cases, 1):
        archive_name = test_case['archive']
        destination = test_case['destination']
        description = test_case['description']
        
        print(f"\nTest Case {i}: {description}")
        print(f"Archive: {archive_name}")
        print(f"Destination: {destination}")
        print("-" * 80)
        
        # Build the full message
        message = f"Extract '{archive_name}' to {destination}?"
        
        # Define shortening regions
        archive_part_start = len("Extract ")
        archive_part_end = archive_part_start + len(f"'{archive_name}' ")
        destination_start = archive_part_end + len("to ")
        destination_end = destination_start + len(destination)
        
        regions = [
            # Archive name region - remove entirely if space is tight
            ShorteningRegion(
                start=archive_part_start,
                end=archive_part_end,
                priority=1,  # Higher priority = shortened first
                strategy='all_or_nothing'
            ),
            # Destination path region - abbreviate intelligently
            ShorteningRegion(
                start=destination_start,
                end=destination_end,
                priority=0,  # Lower priority = more important, shortened last
                strategy='abbreviate',
                abbrev_position='middle',
                filepath_mode=True
            )
        ]
        
        print(f"\nOriginal message ({calculate_display_width(message)} cols):")
        print(f"  {message}")
        print()
        
        # Show how it looks at different widths
        for width in terminal_widths:
            shortened = reduce_width(message, width, regions=regions)
            actual_width = calculate_display_width(shortened)
            
            # Visual representation of the width constraint
            ruler = "+" + "-" * (width - 2) + "+"
            
            print(f"Width {width:3d}: {shortened}")
            print(f"          {ruler}")
            print(f"          (actual: {actual_width} cols)")
            print()
        
        if i < len(test_cases):
            print()
    
    print("=" * 80)
    print("Key Observations:")
    print("=" * 80)
    print()
    print("1. Archive name uses AllOrNothing strategy:")
    print("   - Either shows full \"'archive.tar.gz' \" or removes it entirely")
    print("   - No partial truncation like \"'very_long_arc...\"")
    print()
    print("2. Destination path uses Abbreviation with filepath mode:")
    print("   - Intelligently shortens directory paths")
    print("   - Preserves filename when possible")
    print("   - Example: /home/user/documents/file.txt → /home/…/file.txt")
    print()
    print("3. Priority order (higher = shortened first):")
    print("   - Priority 1: Archive name (shortened first)")
    print("   - Priority 0: Destination path (more important, shortened last)")
    print()
    print("4. At very narrow widths:")
    print("   - Archive name is removed first (AllOrNothing)")
    print("   - Then destination path is abbreviated (filepath mode)")
    print("   - Message becomes: \"Extract to /…/folder?\"")
    print()


def demo_strategy_comparison():
    """Compare AllOrNothing vs Truncation strategies"""
    
    print("=" * 80)
    print("Strategy Comparison: AllOrNothing vs Truncation")
    print("=" * 80)
    print()
    
    archive_name = "my_important_backup_file.tar.gz"
    message = f"Extract '{archive_name}' to /destination?"
    
    print(f"Original message: {message}")
    print(f"Original width: {calculate_display_width(message)} cols")
    print()
    
    # Define region for the archive name part
    archive_part_start = len("Extract ")
    archive_part_end = archive_part_start + len(f"'{archive_name}' ")
    
    print("Shortening the archive name part to fit in 40 columns:")
    print()
    
    # Test with AllOrNothing strategy
    regions_all_or_nothing = [
        ShorteningRegion(
            start=archive_part_start,
            end=archive_part_end,
            priority=1,
            strategy='all_or_nothing'
        )
    ]
    
    result_all_or_nothing = reduce_width(message, 40, regions=regions_all_or_nothing)
    
    print(f"AllOrNothing strategy:")
    print(f"  Result: {result_all_or_nothing}")
    print(f"  Width: {calculate_display_width(result_all_or_nothing)} cols")
    print(f"  Behavior: Removed entire archive name part")
    print()
    
    # Test with Truncation strategy
    regions_truncate = [
        ShorteningRegion(
            start=archive_part_start,
            end=archive_part_end,
            priority=1,
            strategy='truncate'
        )
    ]
    
    result_truncate = reduce_width(message, 40, regions=regions_truncate)
    
    print(f"Truncation strategy:")
    print(f"  Result: {result_truncate}")
    print(f"  Width: {calculate_display_width(result_truncate)} cols")
    print(f"  Behavior: Truncated from right, no ellipsis")
    print()
    
    # Test with Abbreviation strategy
    regions_abbreviate = [
        ShorteningRegion(
            start=archive_part_start,
            end=archive_part_end,
            priority=1,
            strategy='abbreviate',
            abbrev_position='middle'
        )
    ]
    
    result_abbreviate = reduce_width(message, 40, regions=regions_abbreviate)
    
    print(f"Abbreviation strategy (middle):")
    print(f"  Result: {result_abbreviate}")
    print(f"  Width: {calculate_display_width(result_abbreviate)} cols")
    print(f"  Behavior: Added ellipsis in middle")
    print()
    
    print("Why AllOrNothing for archive name?")
    print("  - Partial archive names can be confusing")
    print("  - \"'my_important_bac\" doesn't help identify the file")
    print("  - Better to show full name or remove it entirely")
    print("  - User can still see the full name in the file list")
    print()


if __name__ == '__main__':
    demo_extraction_confirmation_shortening()
    print()
    demo_strategy_comparison()
