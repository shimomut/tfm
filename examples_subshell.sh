#!/bin/bash
# Examples of using TFM sub-shell environment variables
# Run this script from within TFM sub-shell mode (press 'x' in TFM)

echo "TFM Sub-shell Examples"
echo "======================"

# Check if we're in TFM sub-shell
if [ -z "$THIS_DIR" ]; then
    echo "Error: This script should be run from TFM sub-shell mode"
    echo "1. Start TFM: python3 tfm.py"
    echo "2. Press 'x' to enter sub-shell mode"
    echo "3. Run this script: bash examples_subshell.sh"
    exit 1
fi

echo "Current TFM state:"
echo "  Left pane:  $LEFT_DIR"
echo "  Right pane: $RIGHT_DIR"
echo "  Active:     $THIS_DIR"
echo "  Other:      $OTHER_DIR"
echo

# Example 1: List files in both panes
echo "Example 1: Listing files in both panes"
echo "---------------------------------------"
echo "Left pane contents:"
ls -la "$LEFT_DIR" | head -5
echo "..."
echo
echo "Right pane contents:"
ls -la "$RIGHT_DIR" | head -5
echo "..."
echo

# Example 2: Show selected files
echo "Example 2: Selected files information"
echo "------------------------------------"
if [ -n "$THIS_SELECTED" ]; then
    echo "Selected files in active pane:"
    for file in $THIS_SELECTED; do
        if [ -f "$THIS_DIR/$file" ]; then
            echo "  📄 $file ($(stat -f%z "$THIS_DIR/$file" 2>/dev/null || stat -c%s "$THIS_DIR/$file" 2>/dev/null || echo "unknown") bytes)"
        elif [ -d "$THIS_DIR/$file" ]; then
            echo "  📁 $file (directory)"
        fi
    done
else
    echo "No files selected in active pane"
fi
echo

# Example 3: Compare directory sizes
echo "Example 3: Directory size comparison"
echo "-----------------------------------"
echo "Left pane size:  $(du -sh "$LEFT_DIR" 2>/dev/null | cut -f1)"
echo "Right pane size: $(du -sh "$RIGHT_DIR" 2>/dev/null | cut -f1)"
echo

# Example 4: Find Python files
echo "Example 4: Finding Python files"
echo "-------------------------------"
python_files=$(find "$LEFT_DIR" "$RIGHT_DIR" -name "*.py" 2>/dev/null | wc -l)
echo "Total Python files in both panes: $python_files"
if [ $python_files -gt 0 ]; then
    echo "First few Python files:"
    find "$LEFT_DIR" "$RIGHT_DIR" -name "*.py" 2>/dev/null | head -3
fi
echo

# Example 5: Demonstrate file operations (safe, read-only)
echo "Example 5: Safe file operations"
echo "------------------------------"
if [ -n "$THIS_SELECTED" ]; then
    echo "Commands you could run on selected files:"
    for file in $THIS_SELECTED; do
        echo "  # Copy to other pane:"
        echo "  cp '$THIS_DIR/$file' '$OTHER_DIR/'"
        echo "  # Show file info:"
        echo "  file '$THIS_DIR/$file'"
        echo "  # Calculate checksum:"
        echo "  md5sum '$THIS_DIR/$file'"
        echo
    done
else
    echo "No files selected - select some files in TFM and try again"
fi

echo "======================"
echo "Type 'exit' to return to TFM"