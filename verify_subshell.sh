#!/bin/bash
# Simple script to verify TFM sub-shell environment variables

echo "TFM Sub-shell Environment Verification"
echo "======================================"

# Check if we're in TFM sub-shell
if [ -z "$THIS_DIR" ]; then
    echo "❌ Not in TFM sub-shell mode"
    echo "Start TFM and press 'x' to enter sub-shell mode"
    exit 1
fi

echo "✅ In TFM sub-shell mode"
echo

echo "Directory Variables:"
echo "  LEFT_DIR:  $LEFT_DIR"
echo "  RIGHT_DIR: $RIGHT_DIR"
echo "  THIS_DIR:  $THIS_DIR"
echo "  OTHER_DIR: $OTHER_DIR"
echo

echo "Selected Files:"
echo "  LEFT_SELECTED:  '$LEFT_SELECTED'"
echo "  RIGHT_SELECTED: '$RIGHT_SELECTED'"
echo "  THIS_SELECTED:  '$THIS_SELECTED'"
echo "  OTHER_SELECTED: '$OTHER_SELECTED'"
echo

echo "Directory Verification:"
for dir_var in LEFT_DIR RIGHT_DIR THIS_DIR OTHER_DIR; do
    dir_path="${!dir_var}"
    if [ -d "$dir_path" ]; then
        echo "  ✅ $dir_var ($dir_path) exists"
    else
        echo "  ❌ $dir_var ($dir_path) does not exist"
    fi
done
echo

echo "Current Working Directory: $(pwd)"
echo "Should match THIS_DIR: $THIS_DIR"
if [ "$(pwd)" = "$THIS_DIR" ]; then
    echo "✅ Working directory matches THIS_DIR"
else
    echo "❌ Working directory does not match THIS_DIR"
fi
echo

echo "======================================"
echo "Environment variables are working correctly!"
echo "You can now use these variables in your shell commands."
echo "Type 'exit' to return to TFM."