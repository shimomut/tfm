#!/usr/bin/env python3
"""
Demo: Dynamic Date Column Width Adjustment

This demo shows how the date column width automatically adjusts
when switching between date formats, ensuring optimal space usage
and proper column alignment.
"""

import sys
from pathlib import Path as StdPath

# Add src to path
sys.path.insert(0, str(StdPath(__file__).parent.parent / 'src'))

from tfm_const import DATE_FORMAT_FULL, DATE_FORMAT_SHORT


def draw_file_list_mockup(format_name, date_width, example_date):
    """Draw a mockup of the file list with the specified date column width"""
    
    # Simulate an 80-character wide pane
    pane_width = 80
    usable_width = pane_width - 2  # Account for borders
    
    # Fixed widths
    marker_width = 2
    size_width = 8
    
    # Calculate filename width
    # Formula: usable_width - (marker + space + size + space + date) = 78 - (2 + 1 + 8 + 1 + date_width)
    name_width = usable_width - (12 + date_width)
    
    print(f"\n{format_name}")
    print("=" * 80)
    print(f"Date column width: {date_width} characters")
    print(f"Filename column width: {name_width} characters")
    print("-" * 80)
    
    # Sample files
    files = [
        ("report.txt", "2.5K", example_date),
        ("presentation.pptx", "15M", example_date),
        ("data_analysis_results_final_v2.xlsx", "8.2M", example_date),
        ("meeting_notes.md", "1.2K", example_date),
        ("project_documentation.pdf", "45M", example_date),
    ]
    
    for filename, size, date in files:
        # Truncate filename if needed
        if len(filename) > name_width:
            display_name = filename[:name_width-1] + "…"
        else:
            display_name = filename.ljust(name_width)
        
        # Format line
        line = f"  {display_name} {size:>8} {date}"
        print(line)
    
    print("=" * 80)


def demo_column_width_adjustment():
    """Demonstrate how column width adjusts for each format"""
    
    print("=" * 80)
    print("Dynamic Date Column Width Adjustment Demo")
    print("=" * 80)
    print("\nThis demo shows how the file list layout adjusts when you")
    print("change the date format using the View Options menu (z key).")
    print()
    
    # Show each format with appropriate example dates
    formats = [
        ("Short Format (YY-MM-DD HH:mm) - Default", 14, "24-12-17 14:30"),
        ("Full Format (YYYY-MM-DD HH:mm:ss)", 19, "2024-12-17 14:30:45"),
    ]
    
    for format_name, date_width, example_date in formats:
        draw_file_list_mockup(format_name, date_width, example_date)
    
    print("\n" + "=" * 80)
    print("Column Width Comparison")
    print("=" * 80)
    print()
    print(f"{'Format':<35} {'Date Width':<12} {'Name Width':<12} {'Total':<10}")
    print("-" * 80)
    
    for format_name, date_width, _ in formats:
        name_width = 78 - (12 + date_width)
        total = name_width + date_width + 12
        print(f"{format_name:<35} {date_width:<12} {name_width:<12} {total:<10}")
    
    print("=" * 80)
    print("\nKey Benefits:")
    print("  • Each format uses exactly the space it needs")
    print("  • Filename column adjusts to maximize available space")
    print("  • Columns stay properly aligned regardless of format")
    print("  • Switching formats updates layout immediately")


def demo_space_savings():
    """Show how much space is saved/used by each format"""
    
    print("\n\n" + "=" * 80)
    print("Space Usage Analysis")
    print("=" * 80)
    print()
    
    formats = [
        ("Short", 14),
        ("Full", 19),
    ]
    
    base_format = formats[0]  # Short as baseline
    
    print(f"{'Format':<10} {'Date Width':<12} {'vs Short':<15} {'Impact':<30}")
    print("-" * 80)
    
    for format_name, date_width in formats:
        diff = date_width - base_format[1]
        
        if diff == 0:
            comparison = "baseline"
            impact = "Default, balanced space usage"
        elif diff > 0:
            comparison = f"+{diff} chars"
            impact = f"{diff} fewer chars for filenames"
        else:
            comparison = f"{diff} chars"
            impact = f"{abs(diff)} more chars for filenames"
        
        print(f"{format_name:<10} {date_width:<12} {comparison:<15} {impact:<30}")
    
    print("=" * 80)
    print("\nRecommendations:")
    print("  • Use Short format (default) for general browsing")
    print("  • Use Full format when you need precise timestamps with seconds")


def demo_visual_transition():
    """Show visual representation of format transitions"""
    
    print("\n\n" + "=" * 80)
    print("Visual Format Transition")
    print("=" * 80)
    print("\nWhen you press 'z' and toggle between formats, the layout changes:")
    print()
    
    # Show the same file with different formats
    filename = "important_document.pdf"
    size = "12M"
    
    formats = [
        ("Short", 14, "24-12-17 14:30", 52),
        ("Full", 19, "2024-12-17 14:30:45", 47),
    ]
    
    for format_name, date_width, date_str, name_width in formats:
        # Create visual representation
        marker = "●"
        padded_name = filename.ljust(name_width)
        
        print(f"{format_name:>6}: {marker} {padded_name} {size:>8} {date_str}")
        print(f"        {'↑':<3}{'↑' * name_width:<{name_width}} {'↑' * 8:<8} {'↑' * date_width}")
        print(f"        {'M':<3}{'Filename':<{name_width}} {'Size':<8} {'Date/Time'}")
        print()
    
    print("=" * 80)
    print("\nLegend:")
    print("  M = Selection marker")
    print("  ↑ = Column boundaries")
    print("\nNotice how the filename column width adjusts to accommodate")
    print("the different date column widths while maintaining alignment.")


if __name__ == '__main__':
    try:
        demo_column_width_adjustment()
        demo_space_savings()
        demo_visual_transition()
        
        print("\n\n" + "=" * 80)
        print("✓ Demo completed successfully!")
        print("=" * 80)
        print("\nTry it in TFM:")
        print("  1. Run: python tfm.py")
        print("  2. Press 'z' for View Options")
        print("  3. Select 'Cycle date format'")
        print("  4. Watch the columns adjust automatically!")
        print()
        
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
