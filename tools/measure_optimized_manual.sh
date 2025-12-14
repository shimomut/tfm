#!/bin/bash
#
# Manual Optimized Performance Measurement Script
#
# This script measures the performance of the optimized CoreGraphics backend
# and compares it with baseline measurements.
#
# Usage:
#   ./tools/measure_optimized_manual.sh [duration_seconds]
#
# The script will:
# 1. Launch TFM with CoreGraphics backend and profiling enabled
# 2. You manually interact with TFM (navigate, scroll, etc.)
# 3. After the specified duration, quit TFM (press 'q')
# 4. Analyze the profiling data and compare with baseline
# 5. Generate a comprehensive comparison report
#
# Default duration: 30 seconds

set -e

# Configuration
DURATION=${1:-30}
OUTPUT_DIR="profiling_output/optimized"
BASELINE_DIR="profiling_output/baseline"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================================================"
echo "Optimized CoreGraphics Performance Measurement"
echo "========================================================================"
echo ""
echo "Duration: ${DURATION} seconds"
echo "Output directory: ${OUTPUT_DIR}"
echo "Baseline directory: ${BASELINE_DIR}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Check if baseline exists
if [ -f "${BASELINE_DIR}/baseline_report.txt" ]; then
    echo -e "${GREEN}✓ Baseline data found - comparison will be generated${NC}"
else
    echo -e "${YELLOW}⚠ No baseline data found - run baseline benchmark first for comparison${NC}"
    echo "  Run: ./tools/manual_baseline_benchmark.sh"
fi
echo ""

echo -e "${GREEN}Step 1: Preparing measurement environment${NC}"
echo "Output directory created: ${OUTPUT_DIR}"
echo ""

echo -e "${GREEN}Step 2: Launching TFM with profiling enabled${NC}"
echo ""
echo -e "${YELLOW}Instructions:${NC}"
echo "  1. TFM will launch with the optimized CoreGraphics backend"
echo "  2. Profiling is enabled and will track FPS and performance"
echo "  3. Navigate around, scroll through files, switch panes, etc."
echo "  4. Try to use TFM normally to get realistic performance data"
echo "  5. After ${DURATION} seconds, press 'q' to quit TFM"
echo ""
echo "Press Enter to start the measurement..."
read

# Set environment variables for profiling
export TFM_PROFILING=1
export TFM_PROFILING_OUTPUT="${OUTPUT_DIR}"

# Record start time
START_TIME=$(date +%s)

echo -e "${GREEN}Starting TFM...${NC}"
echo ""

# Run TFM with CoreGraphics backend
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

# Create a Python script to analyze and compare
cat > /tmp/analyze_optimized_$.py << 'PYTHON_SCRIPT'
import sys
import pstats
from pathlib import Path

def load_baseline_metrics(baseline_dir):
    """Load baseline metrics from report file"""
    baseline_report = Path(baseline_dir) / 'baseline_report.txt'
    
    if not baseline_report.exists():
        return None
    
    metrics = {}
    
    try:
        with open(baseline_report, 'r') as f:
            content = f.read()
        
        for line in content.split('\n'):
            if 'Average FPS:' in line:
                metrics['avg_fps'] = float(line.split(':')[1].strip())
            elif 'Total calls:' in line and 'drawRect_' in content[max(0, content.find(line)-200):content.find(line)]:
                metrics['drawrect_calls'] = int(line.split(':')[1].strip())
            elif 'Cumulative time:' in line and 'seconds' in line:
                metrics['drawrect_time'] = float(line.split(':')[1].replace('seconds', '').strip())
            elif 'Total API calls:' in line:
                metrics['api_calls'] = int(line.split(':')[1].strip())
        
        return metrics
    except Exception as e:
        print(f"Warning: Could not load baseline metrics: {e}", file=sys.stderr)
        return None

def analyze_profile(profile_path, baseline_dir):
    """Analyze cProfile data and compare with baseline"""
    try:
        stats = pstats.Stats(profile_path)
        
        print("=" * 70)
        print("OPTIMIZED PERFORMANCE ANALYSIS")
        print("=" * 70)
        print("")
        
        # Find drawRect_ statistics
        drawrect_calls = 0
        drawrect_time = 0.0
        
        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            func_name = func[2]
            if 'drawRect_' in func_name:
                drawrect_calls = nc
                drawrect_time = ct
                print(f"drawRect_ Method:")
                print(f"  Total calls: {nc}")
                print(f"  Cumulative time: {ct:.4f} seconds")
                if nc > 0:
                    print(f"  Average time per call: {(ct/nc)*1000:.4f} ms")
                break
        
        # Count API calls
        api_patterns = ['NSRectFill', 'NSColor', 'NSAttributedString', 'drawAtPoint', 'setFill']
        api_count = 0
        
        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            func_name = func[2]
            for pattern in api_patterns:
                if pattern in func_name:
                    api_count += nc
        
        print(f"\nCoreGraphics API Calls:")
        print(f"  Total API calls: {api_count}")
        
        if drawrect_calls > 0:
            print(f"  API calls per frame: {api_count / drawrect_calls:.2f}")
        
        # Load and compare with baseline
        baseline = load_baseline_metrics(baseline_dir)
        
        if baseline:
            print("\n" + "=" * 70)
            print("COMPARISON WITH BASELINE")
            print("=" * 70)
            print("")
            
            print("Baseline Metrics:")
            if 'avg_fps' in baseline:
                print(f"  Average FPS: {baseline['avg_fps']:.2f}")
            if 'drawrect_calls' in baseline and 'drawrect_time' in baseline:
                if baseline['drawrect_calls'] > 0:
                    baseline_avg_time = baseline['drawrect_time'] / baseline['drawrect_calls']
                    print(f"  drawRect_ avg time: {baseline_avg_time*1000:.4f} ms")
            if 'api_calls' in baseline:
                print(f"  Total API calls: {baseline['api_calls']}")
                if 'drawrect_calls' in baseline and baseline['drawrect_calls'] > 0:
                    print(f"  API calls per frame: {baseline['api_calls'] / baseline['drawrect_calls']:.2f}")
            
            print("\nImprovements:")
            
            # Calculate improvements
            if 'drawrect_calls' in baseline and baseline['drawrect_calls'] > 0 and drawrect_calls > 0:
                baseline_avg_time = baseline['drawrect_time'] / baseline['drawrect_calls']
                optimized_avg_time = drawrect_time / drawrect_calls
                time_improvement = ((baseline_avg_time - optimized_avg_time) / baseline_avg_time) * 100
                print(f"  drawRect_ time reduction: {time_improvement:+.2f}%")
            
            if 'api_calls' in baseline and baseline['api_calls'] > 0:
                api_reduction = ((baseline['api_calls'] - api_count) / baseline['api_calls']) * 100
                print(f"  API call reduction: {api_reduction:+.2f}%")
                
                if api_reduction >= 75:
                    print(f"  ✓ Excellent reduction (target: 75-85%)")
                elif api_reduction >= 50:
                    print(f"  ✓ Good reduction")
                else:
                    print(f"  ⚠ Moderate reduction (target: 75-85%)")
            
            if 'drawrect_calls' in baseline and baseline['drawrect_calls'] > 0 and drawrect_calls > 0:
                baseline_api_per_frame = baseline['api_calls'] / baseline['drawrect_calls']
                optimized_api_per_frame = api_count / drawrect_calls
                api_per_frame_reduction = ((baseline_api_per_frame - optimized_api_per_frame) / baseline_api_per_frame) * 100
                print(f"  API calls per frame reduction: {api_per_frame_reduction:+.2f}%")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"Error analyzing profile: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python analyze_optimized.py <profile_file> <baseline_dir>", file=sys.stderr)
        sys.exit(1)
    
    analyze_profile(sys.argv[1], sys.argv[2])
PYTHON_SCRIPT

# Run the analysis
python3 /tmp/analyze_optimized_$.py "${LATEST_PROFILE}" "${BASELINE_DIR}"

# Clean up
rm /tmp/analyze_optimized_$.py

echo ""
echo "========================================================================"
echo -e "${GREEN}Measurement Complete!${NC}"
echo "========================================================================"
echo ""
echo "Duration: ${ACTUAL_DURATION} seconds"
echo "Profile data: ${LATEST_PROFILE}"
echo "Output directory: ${OUTPUT_DIR}"
echo ""
echo "Next steps:"
echo "  1. Review the performance analysis above"
echo "  2. Check if the 20% FPS improvement target was met"
echo "  3. Verify the 75-85% API call reduction target"
echo "  4. Document the results in the optimization spec"
echo ""
echo "To view detailed profile data:"
echo "  python3 -m pstats ${LATEST_PROFILE}"
echo ""
echo "Or install snakeviz for visual analysis:"
echo "  pip install snakeviz"
echo "  snakeviz ${LATEST_PROFILE}"
echo ""
