# TTK Library Makefile
# Provides convenient targets for running demo applications and tests

.PHONY: help demo-ttk demo-performance demo-standalone demo-test-interface demo-all test clean

# Backend selection (default: auto)
# Usage: make demo-ttk BACKEND=metal
# Valid options: auto, curses, metal
BACKEND ?= auto

# Default target - show help
help:
	@echo "TTK Library - Available Make Targets"
	@echo "====================================="
	@echo ""
	@echo "Demo Applications:"
	@echo "  make demo-ttk              - Run the main TTK demo"
	@echo "  make demo-performance      - Run performance monitoring demo"
	@echo "  make demo-standalone       - Run standalone application demo"
	@echo "  make demo-test-interface   - Run test interface demo"
	@echo "  make demo-all              - Run all demos sequentially"
	@echo ""
	@echo "Backend Selection:"
	@echo "  BACKEND=auto               - Auto-detect best backend (default)"
	@echo "  BACKEND=curses             - Use curses (terminal) backend"
	@echo "  BACKEND=metal              - Use Metal (macOS desktop) backend"
	@echo ""
	@echo "Examples:"
	@echo "  make demo-ttk                    # Auto-detect backend"
	@echo "  make demo-ttk BACKEND=curses     # Force curses backend"
	@echo "  make demo-ttk BACKEND=metal      # Force Metal backend (macOS only)"
	@echo "  make demo-all BACKEND=metal      # Run all demos with Metal"
	@echo ""
	@echo "Testing:"
	@echo "  make test                  - Run all TTK tests"
	@echo "  make test-unit             - Run unit tests only"
	@echo "  make test-integration      - Run integration tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                 - Remove Python cache files"
	@echo ""

# Demo targets
demo-ttk:
	@echo "Running TTK Demo (backend: $(BACKEND))..."
	@cd .. && python -m ttk.demo.demo_ttk --backend $(BACKEND)

demo-performance:
	@echo "Running Performance Monitoring Demo (backend: $(BACKEND))..."
	@cd .. && python -m ttk.demo.performance --backend $(BACKEND)

demo-standalone:
	@echo "Running Standalone Application Demo (backend: $(BACKEND))..."
	@cd .. && python -m ttk.demo.standalone_app --backend $(BACKEND)

demo-test-interface:
	@echo "Running Test Interface Demo (backend: $(BACKEND))..."
	@cd .. && python -m ttk.demo.test_interface --backend $(BACKEND)

demo-all: demo-ttk demo-performance demo-standalone demo-test-interface
	@echo "All demos completed with $(BACKEND) backend!"

# Testing targets
test:
	@echo "Running all TTK tests..."
	@cd .. && python -m pytest ttk/test/ -v

test-unit:
	@echo "Running unit tests..."
	@cd .. && python -m pytest ttk/test/test_*.py -v

test-integration:
	@echo "Running integration tests..."
	@cd .. && python -m pytest ttk/test/test_*_integration.py -v

# Cleanup
clean:
	@echo "Cleaning Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@echo "Cleanup complete!"
