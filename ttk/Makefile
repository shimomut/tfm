# TTK Library Makefile
# Provides convenient targets for running demo applications and tests

.PHONY: help demo-ttk demo-performance demo-standalone demo-test-interface demo-all test clean install install-dev uninstall build

# Backend selection (default: curses)
# Usage: make demo-ttk BACKEND=metal
# Valid options: auto, curses, metal
# Note: Metal backend is under development, use curses for now
BACKEND ?= curses

# Default target - show help
help:
	@echo "TTK Library - Available Make Targets"
	@echo "====================================="
	@echo ""
	@echo "Installation:"
	@echo "  make install               - Install TTK to Python (pip install .)"
	@echo "  make install-dev           - Install TTK in development mode (pip install -e .)"
	@echo "  make install-metal         - Install TTK with Metal backend support (macOS only)"
	@echo "  make uninstall             - Uninstall TTK from Python"
	@echo "  make build                 - Build distribution packages (wheel and sdist)"
	@echo ""
	@echo "Demo Applications:"
	@echo "  make demo-ttk              - Run the main TTK demo"
	@echo "  make demo-performance      - Run performance monitoring demo"
	@echo "  make demo-standalone       - Run standalone application demo"
	@echo "  make demo-test-interface   - Run test interface demo"
	@echo "  make demo-all              - Run all demos sequentially"
	@echo ""
	@echo "Backend Selection:"
	@echo "  BACKEND=curses             - Use curses (terminal) backend (default)"
	@echo "  BACKEND=auto               - Auto-detect best backend"
	@echo "  BACKEND=metal              - Use Metal (macOS desktop) backend (NOT YET FUNCTIONAL)"
	@echo ""
	@echo "Examples:"
	@echo "  make install-dev                 # Install for development"
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
	@echo "  make clean-all             - Remove cache files and build artifacts"
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

# Installation targets
install:
	@echo "Installing TTK to Python..."
	@pip3 install .
	@echo "TTK installed successfully!"

install-dev:
	@echo "Installing TTK in development mode..."
	@pip3 install -e .
	@echo "TTK installed in development mode!"
	@echo "Changes to source files will be reflected immediately."

install-metal:
	@echo "Installing TTK with Metal backend support (macOS only)..."
	@pip3 install ".[metal]"
	@echo "TTK installed with Metal backend support!"

uninstall:
	@echo "Uninstalling TTK from Python..."
	@pip3 uninstall -y ttk || echo "TTK not installed"
	@echo "TTK uninstalled!"

build:
	@echo "Building TTK distribution packages..."
	@python -m pip3 install --upgrade build
	@python -m build
	@echo "Build complete! Packages are in dist/"

# Cleanup
clean:
	@echo "Cleaning Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@echo "Cleanup complete!"

clean-all: clean
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage
	@echo "All artifacts cleaned!"
