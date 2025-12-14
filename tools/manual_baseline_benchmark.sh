#!/bin/bash
#
# Manual Baseline Benchmark Script
#
# This script provides a simple way to establish a performance baseline
# for the CoreGraphics backend by running TFM with profiling enabled.
#
# Usage:
#   ./tools/manual_baseline_benchmark.sh [duration_seconds]
#
# The script will:
# 1. Create the profiling output directory
# 2. Launch TFM with CoreGraphics backend and profiling enabled
# 3. You manually interact with TFM (navigate, scroll, etc.)
# 4. After the specified duration, quit TFM (press 'q')
# 5. The script will analyze the profiling data and generate a report
#
# Default duration: 30 seconds

set -e

# Configuration
DURATION=${1:-30}
OUTPUT_DIR="profiling_output/baseline"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================================================"
echo "CoreGraphics Performance Baseline - Manual Benchmark"
echo "========================================================================"
echo ""
echo "Duration: ${DURATION} seconds"
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

echo -e "${GREEN}Step 1: Preparing benchmark environment${NC}"
echo "Output directory created: ${OUTPUT_DIR}"
echo ""

echo -e "${GREEN}Step 2: Launching TFM with profiling enabled${NC}"
echo ""
echo -e "${YELLOW}Instructions:${NC}"
echo "  1. TFM will launch with the CoreGraphics backend"
echo "  2. Profiling is enabled and will track FPS and performance"
echo "  3. Navigate around, scroll through files, switch panes, etc."
echo "  4. Try to use TFM normally to get realistic performance data"
echo "  5. After ${DURATION} seconds, press 'q' to quit TFM"
echo ""
echo "Press Enter to start the benchmark..."
read

# Set environment variables for profiling
export TFM_PROFILING=1
export TFM_PROFILING_OUTPUT="${OUTPUT_DIR}"

# Record start time
START_TIME=$(date +%s)

echo -e "${GREEN}Starting TFM...${NC}"
echo ""

# Run TFM with CoreGraphics backend
# Note: User will interact manually
python3 tfm.py --backend coregraphics || true

# Record end time
END_TIME=$(date +%s)
ACTUAL_DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${GREEN}Step 3: Analyzing profiling data${NC}"
echo ""

# Find the most recent profile file
LATEST_PROFILE=$(ls -t "${OUTPUT_DIR}"/*_profile_*.prof 2>/dev/null | head -1)

if [ -z "${LATEST_PROFILE}" ]; then
    echo -e "${RED}Error: No profile data found${NC}"
    echo "Make sure TFM ran for at least a few seconds"
    exit 1
fi

echo "Found profile: $(basename ${LATEST_PROFILE})"
echo ""

# Create a Python script to analyze the profile
cat > /tmp/analyze_profile_$$.py << 'PYTHON_SCRIPT'
import sys
import pstats
from pathlib import Path

def analyze_profile(profile_path):
    """Analyze cProfile data and extract key metrics"""
    try:
        stats = pstats.Stats(profile_path)
        
        print("Top 20 functions by cumulative time:")
        print("-" * 70)
        stats.sort_stats('cumulative')
        stats.print_stats(20)
        
        print("\n" + "=" * 70)
        print("drawRect_ Method Analysis:")
        print("=" * 70)
        
        # Find drawRect_ statistics
        found_drawrect = False
        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            func_name = func[2]
            if 'drawRect_' in func_name:
                found_drawrect = True
                print(f"\nFunction: {func_name}")
                print(f"  Primitive calls: {cc}")
                print(f"  Total calls: {nc}")
                print(f"  Total time: {tt:.4f} seconds")
                print(f"  Cumulative time: {ct:.4f} seconds")
                print(f"  Time per call: {(ct/nc)*1000:.4f} ms")
        
        if not found_drawrect:
            print("\nWarning: drawRect_ method not found in profile data")
            print("This may indicate the method wasn't called during profiling")
        
        print("\n" + "=" * 70)
        print("CoreGraphics API Calls:")
        print("=" * 70)
        
        # Count API calls
        api_patterns = ['NSRectFill', 'NSColor', 'NSAttributedString', 'drawAtPoint', 'setFill']
        api_counts = {pattern: 0 for pattern in api_patterns}
        
        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            func_name = func[2]
            for pattern in api_patterns:
                if pattern in func_name:
                    api_counts[pattern] += nc
        
        total_api_calls = sum(api_counts.values())
        print(f"\nTotal CoreGraphics API calls: {total_api_calls}")
        for pattern, count in sorted(api_counts.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                print(f"  {pattern}: {count}")
        
    except Exception as e:
        print(f"Error analyzing profile: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python analyze_profile.py <profile_file>", file=sys.stderr)
        sys.exit(1)
    
    analyze_profile(sys.argv[1])
PYTHON_SCRIPT

# Run the analysis
python3 /tmp/analyze_profile_$$.py "${LATEST_PROFILE}"

# Clean up
rm /tmp/analyze_profile_$$.py

echo ""
echo "========================================================================"
echo -e "${GREEN}Benchmark Complete!${NC}"
echo "========================================================================"
echo ""
echo "Duration: ${ACTUAL_DURATION} seconds"
echo "Profile data: ${LATEST_PROFILE}"
echo "Output directory: ${OUTPUT_DIR}"
echo ""
echo "Next steps:"
echo "  1. Review the profile analysis above"
echo "  2. Note the FPS values that were printed during execution"
echo "  3. Use this data as the baseline for optimization"
echo "  4. After implementing optimizations, run this script again to compare"
echo ""
echo "To view detailed profile data:"
echo "  python3 -m pstats ${LATEST_PROFILE}"
echo ""
echo "Or install snakeviz for visual analysis:"
echo "  pip install snakeviz"
echo "  snakeviz ${LATEST_PROFILE}"
echo ""
