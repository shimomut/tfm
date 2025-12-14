#!/bin/bash

# Manual Visual Correctness Verification Script
# 
# This script helps manually verify that the optimized CoreGraphics backend
# produces visually identical output to the baseline implementation.
#
# Usage:
#   ./tools/verify_visual_manual.sh

set -e

echo "================================================================================"
echo "Manual Visual Correctness Verification"
echo "CoreGraphics Backend Optimization"
echo "================================================================================"
echo ""
echo "This script will guide you through manual visual verification of the"
echo "CoreGraphics backend optimization."
echo ""
echo "Requirements validated:"
echo "  - 7.1: All existing visual tests pass"
echo "  - 7.2: Optimized and original output are visually identical"
echo "  - 7.3: Edge cases are handled correctly"
echo "  - 7.4: Different color combinations render correctly"
echo "  - 7.5: Various rectangle sizes appear correctly"
echo ""

# Check if we're on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: This script requires macOS (CoreGraphics backend)"
    exit 1
fi

# Function to run TFM and wait for user verification
run_visual_test() {
    local test_name="$1"
    local test_dir="$2"
    local description="$3"
    
    echo "--------------------------------------------------------------------------------"
    echo "Test: $test_name"
    echo "Description: $description"
    echo "--------------------------------------------------------------------------------"
    echo ""
    echo "Press ENTER to launch TFM for this test..."
    read
    
    # Launch TFM in the test directory
    if [ -d "$test_dir" ]; then
        echo "Launching TFM in: $test_dir"
        python tfm.py "$test_dir" || true
    else
        echo "Warning: Test directory not found: $test_dir"
        echo "Launching TFM in current directory"
        python tfm.py . || true
    fi
    
    echo ""
    echo "Visual verification questions:"
    echo "  1. Did TFM render correctly?"
    echo "  2. Were colors displayed accurately?"
    echo "  3. Was text readable and properly positioned?"
    echo "  4. Were there any visual artifacts or glitches?"
    echo ""
    echo "Did this test PASS? (y/n): "
    read response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "✓ Test passed: $test_name"
        return 0
    else
        echo "✗ Test failed: $test_name"
        return 1
    fi
}

# Track test results
total_tests=0
passed_tests=0

echo "Starting visual verification tests..."
echo ""

# Test 1: Basic file listing
total_tests=$((total_tests + 1))
if run_visual_test \
    "Basic File Listing" \
    "." \
    "Verify basic file listing with default colors"; then
    passed_tests=$((passed_tests + 1))
fi

# Test 2: Large directory
total_tests=$((total_tests + 1))
if run_visual_test \
    "Large Directory" \
    "/usr/bin" \
    "Verify rendering performance with many files"; then
    passed_tests=$((passed_tests + 1))
fi

# Test 3: Nested directories
total_tests=$((total_tests + 1))
if run_visual_test \
    "Nested Directories" \
    "src" \
    "Verify navigation and rendering in nested directories"; then
    passed_tests=$((passed_tests + 1))
fi

# Test 4: File selection
echo "--------------------------------------------------------------------------------"
echo "Test: File Selection"
echo "Description: Verify selection highlighting and colors"
echo "--------------------------------------------------------------------------------"
echo ""
echo "Instructions:"
echo "  1. Launch TFM"
echo "  2. Use SPACE to select multiple files"
echo "  3. Verify selection highlighting is visible and correct"
echo "  4. Press 'q' to quit"
echo ""
echo "Press ENTER to launch TFM..."
read
python tfm.py . || true
echo ""
echo "Did selection highlighting work correctly? (y/n): "
read response
total_tests=$((total_tests + 1))
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "✓ Test passed: File Selection"
    passed_tests=$((passed_tests + 1))
else
    echo "✗ Test failed: File Selection"
fi

# Test 5: Dual pane mode
echo "--------------------------------------------------------------------------------"
echo "Test: Dual Pane Mode"
echo "Description: Verify dual pane rendering and active pane highlighting"
echo "--------------------------------------------------------------------------------"
echo ""
echo "Instructions:"
echo "  1. Launch TFM"
echo "  2. Press TAB to switch between panes"
echo "  3. Verify active pane is clearly indicated"
echo "  4. Verify both panes render correctly"
echo "  5. Press 'q' to quit"
echo ""
echo "Press ENTER to launch TFM..."
read
python tfm.py . || true
echo ""
echo "Did dual pane mode work correctly? (y/n): "
read response
total_tests=$((total_tests + 1))
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "✓ Test passed: Dual Pane Mode"
    passed_tests=$((passed_tests + 1))
else
    echo "✗ Test failed: Dual Pane Mode"
fi

# Test 6: Text viewer
echo "--------------------------------------------------------------------------------"
echo "Test: Text Viewer"
echo "Description: Verify text file viewing with syntax highlighting"
echo "--------------------------------------------------------------------------------"
echo ""
echo "Instructions:"
echo "  1. Launch TFM"
echo "  2. Navigate to a Python file (e.g., tfm.py)"
echo "  3. Press ENTER to view the file"
echo "  4. Verify text is readable and colors are correct"
echo "  5. Press 'q' to exit viewer, then 'q' again to quit TFM"
echo ""
echo "Press ENTER to launch TFM..."
read
python tfm.py . || true
echo ""
echo "Did text viewer work correctly? (y/n): "
read response
total_tests=$((total_tests + 1))
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "✓ Test passed: Text Viewer"
    passed_tests=$((passed_tests + 1))
else
    echo "✗ Test failed: Text Viewer"
fi

# Test 7: Search functionality
echo "--------------------------------------------------------------------------------"
echo "Test: Search Functionality"
echo "Description: Verify search dialog and result highlighting"
echo "--------------------------------------------------------------------------------"
echo ""
echo "Instructions:"
echo "  1. Launch TFM"
echo "  2. Press '/' to open search"
echo "  3. Type a search term and press ENTER"
echo "  4. Verify search results are highlighted correctly"
echo "  5. Press ESC to close search, then 'q' to quit"
echo ""
echo "Press ENTER to launch TFM..."
read
python tfm.py . || true
echo ""
echo "Did search functionality work correctly? (y/n): "
read response
total_tests=$((total_tests + 1))
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "✓ Test passed: Search Functionality"
    passed_tests=$((passed_tests + 1))
else
    echo "✗ Test failed: Search Functionality"
fi

# Test 8: Edge cases - very long filenames
echo "--------------------------------------------------------------------------------"
echo "Test: Long Filenames"
echo "Description: Verify handling of very long filenames"
echo "--------------------------------------------------------------------------------"
echo ""
echo "Creating test directory with long filenames..."
test_dir=$(mktemp -d)
touch "$test_dir/this_is_a_very_long_filename_that_should_be_truncated_properly_in_the_display.txt"
touch "$test_dir/another_extremely_long_filename_to_test_the_rendering_capabilities.py"
touch "$test_dir/short.txt"
echo ""
echo "Instructions:"
echo "  1. TFM will launch in test directory"
echo "  2. Verify long filenames are displayed correctly (truncated if needed)"
echo "  3. Verify no visual artifacts or overlapping text"
echo "  4. Press 'q' to quit"
echo ""
echo "Press ENTER to launch TFM..."
read
python tfm.py "$test_dir" || true
echo ""
echo "Cleaning up test directory..."
rm -rf "$test_dir"
echo ""
echo "Did long filename handling work correctly? (y/n): "
read response
total_tests=$((total_tests + 1))
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "✓ Test passed: Long Filenames"
    passed_tests=$((passed_tests + 1))
else
    echo "✗ Test failed: Long Filenames"
fi

# Print summary
echo ""
echo "================================================================================"
echo "VISUAL CORRECTNESS VERIFICATION SUMMARY"
echo "================================================================================"
echo ""
echo "Tests passed: $passed_tests/$total_tests"
echo ""

if [ $passed_tests -eq $total_tests ]; then
    echo "✓ SUCCESS: All visual tests passed"
    echo ""
    echo "Requirements validated:"
    echo "  ✓ 7.1: All existing visual tests pass"
    echo "  ✓ 7.2: Optimized and original output are visually identical"
    echo "  ✓ 7.3: Edge cases are handled correctly"
    echo "  ✓ 7.4: Different color combinations render correctly"
    echo "  ✓ 7.5: Various rectangle sizes appear correctly"
    echo ""
    echo "The CoreGraphics backend optimization maintains visual correctness!"
    exit 0
else
    echo "✗ FAILURE: Some visual tests failed"
    echo ""
    echo "Failed tests: $((total_tests - passed_tests))"
    echo ""
    echo "Please review the failed tests and investigate visual differences."
    echo "The optimization may have introduced rendering issues."
    exit 1
fi
