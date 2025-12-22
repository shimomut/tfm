# TTK Library Makefile
# Provides convenient targets for running demo applications and tests

.PHONY: help demo-ttk demo-performance demo-standalone demo-test-interface demo-all test clean install install-dev uninstall build build-cpp rebuild-cpp

# Backend selection (default: curses)
# Usage: make demo-ttk BACKEND=coregraphics
# Valid options: auto, curses, coregraphics
BACKEND ?= curses

# Default target - show help
help:
	@echo "TTK Library - Available Make Targets"
	@echo "====================================="
	@echo ""
	@echo "Installation:"
	@echo "  make install               - Install TTK to Python (pip install .)"
	@echo "  make install-dev           - Install TTK in development mode (pip install -e .)"
	@echo "  make uninstall             - Uninstall TTK from Python"
	@echo "  make build                 - Build distribution packages (wheel and sdist)"
	@echo "  make build-cpp             - Build C++ rendering extension (macOS only)"
	@echo "  make rebuild-cpp           - Clean and rebuild C++ rendering extension (macOS only)"
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
	@echo "  BACKEND=coregraphics       - Use CoreGraphics (macOS desktop) backend"
	@echo ""
	@echo "Examples:"
	@echo "  make install-dev                      # Install for development"
	@echo "  make demo-ttk                         # Auto-detect backend"
	@echo "  make demo-ttk BACKEND=curses          # Force curses backend"
	@echo "  make demo-ttk BACKEND=coregraphics    # Force CoreGraphics backend (macOS only)"
	@echo "  make demo-all BACKEND=coregraphics    # Run all demos with CoreGraphics"
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

# C++ extension building (macOS only)
build-cpp:
	@echo "Building C++ rendering extension..."
	@python3 setup.py build_ext --inplace
	@echo "Copying extension to project root for compatibility..."
	@cp -f ttk_coregraphics_render*.so ../ 2>/dev/null || true
	@echo "Build complete! Extension files:"
	@ls -lh ttk_coregraphics_render*.so 2>/dev/null || echo "Build failed - no .so file created"
	@ls -lh ../ttk_coregraphics_render*.so 2>/dev/null || true

rebuild-cpp:
	@echo "Cleaning previous C++ build..."
	@rm -f ttk_coregraphics_render*.so
	@rm -f ../ttk_coregraphics_render*.so
	@rm -rf build/temp.*
	@echo "Rebuilding C++ rendering extension..."
	@python3 setup.py build_ext --inplace --force
	@echo "Copying extension to project root for compatibility..."
	@cp -f ttk_coregraphics_render*.so ../ 2>/dev/null || true
	@echo "Rebuild complete! Extension files:"
	@ls -lh ttk_coregraphics_render*.so 2>/dev/null || echo "Build failed - no .so file created"
	@ls -lh ../ttk_coregraphics_render*.so 2>/dev/null || true
