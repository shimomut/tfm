#!/bin/bash
# Profile C++ rendering backend with Instruments
#
# Usage:
#   ./tools/profile_cpp_renderer.sh [template] [output]
#
# Templates:
#   time      - Time Profiler (default)
#   alloc     - Allocations
#   leaks     - Leaks
#   system    - System Trace
#
# Examples:
#   ./tools/profile_cpp_renderer.sh time profile_time.trace
#   ./tools/profile_cpp_renderer.sh alloc profile_alloc.trace

set -e

# Default values
TEMPLATE="time"
OUTPUT="profile.trace"

# Parse arguments
if [ $# -ge 1 ]; then
    TEMPLATE="$1"
fi

if [ $# -ge 2 ]; then
    OUTPUT="$2"
fi

# Map template names to Instruments templates
case "$TEMPLATE" in
    time)
        INSTRUMENTS_TEMPLATE="Time Profiler"
        ;;
    alloc)
        INSTRUMENTS_TEMPLATE="Allocations"
        ;;
    leaks)
        INSTRUMENTS_TEMPLATE="Leaks"
        ;;
    system)
        INSTRUMENTS_TEMPLATE="System Trace"
        ;;
    *)
        echo "Error: Unknown template '$TEMPLATE'"
        echo "Valid templates: time, alloc, leaks, system"
        exit 1
        ;;
esac

# Check if Instruments is available
if ! command -v instruments &> /dev/null; then
    echo "Error: Instruments not found"
    echo "Please install Xcode Command Line Tools:"
    echo "  xcode-select --install"
    exit 1
fi

# Check if benchmark script exists
if [ ! -f "test/benchmark_rendering.py" ]; then
    echo "Error: Benchmark script not found"
    echo "Please run from project root directory"
    exit 1
fi

# Check if C++ renderer is built
if [ ! -f "cpp_renderer.cpython-*.so" ]; then
    echo "Error: C++ renderer not built"
    echo "Please build the C++ extension first:"
    echo "  python setup.py build_ext --inplace"
    exit 1
fi

echo "============================================================"
echo "Profiling C++ Rendering Backend"
echo "============================================================"
echo "Template: $INSTRUMENTS_TEMPLATE"
echo "Output:   $OUTPUT"
echo ""
echo "Starting profiling..."
echo ""

# Run profiling
instruments -t "$INSTRUMENTS_TEMPLATE" -D "$OUTPUT" python test/benchmark_rendering.py

echo ""
echo "============================================================"
echo "Profiling Complete"
echo "============================================================"
echo "Results saved to: $OUTPUT"
echo ""
echo "To view results:"
echo "  open $OUTPUT"
echo ""
