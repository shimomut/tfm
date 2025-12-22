# TFM Makefile

.PHONY: help run run-debug run-profile monitor-log test test-quick clean install uninstall dev-install lint format demo

# Backend selection (default: curses)
# Usage: make run BACKEND=coregraphics
# Valid options: curses, coregraphics
BACKEND ?= curses

help:
	@echo "TFM - Terminal File Manager"
	@echo ""
	@echo "Available commands:"
	@echo "  run          - Run TFM"
	@echo "  run-debug    - Run TFM with debug mode and remote log monitoring"
	@echo "  run-profile  - Run TFM with performance profiling enabled"
	@echo "  monitor-log  - Connect to remote log monitoring (port 8123)"
	@echo "  test         - Run all tests"
	@echo "  test-quick   - Run quick verification tests"
	@echo "  clean        - Clean up temporary files"
	@echo "  install      - Install TFM"
	@echo "  uninstall    - Uninstall TFM"
	@echo "  dev-install  - Install in development mode"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code"
	@echo ""
	@echo "Backend Selection:"
	@echo "  BACKEND=curses         - Use curses (terminal) backend (default)"
	@echo "  BACKEND=coregraphics   - Use CoreGraphics (macOS desktop) backend"
	@echo ""
	@echo "Examples:"
	@echo "  make run                        # Run with curses backend (default)"
	@echo "  make run BACKEND=coregraphics   # Run with CoreGraphics backend"
	@echo "  make test BACKEND=coregraphics  # Test with CoreGraphics backend"

run:
	@echo "Running TFM (backend: $(BACKEND))..."
	@python3 tfm.py --backend $(BACKEND)

run-debug:
	@echo "Running TFM with debug mode and remote log monitoring (backend: $(BACKEND))..."
	@python3 tfm.py --backend $(BACKEND) --debug --remote-log-port 8123

run-profile:
	@echo "Running TFM with performance profiling (backend: $(BACKEND))..."
	@python3 tfm.py --backend $(BACKEND) --profile

monitor-log:
	@python3 tools/tfm_log_client.py localhost 8123

test:
	@echo "Running TFM tests (backend: $(BACKEND))..."
	@cd test && PYTHONPATH=../src python3 -m pytest . -v || echo "pytest not available, running individual tests..."
	@cd test && for test in test_*.py; do echo "Running $$test..."; PYTHONPATH=../src python3 "$$test" || exit 1; done

test-quick:
	@echo "Running quick verification tests (backend: $(BACKEND))..."
	@cd test && PYTHONPATH=../src python3 test_cursor_movement.py
	@cd test && PYTHONPATH=../src python3 test_delete_feature.py
	@cd test && PYTHONPATH=../src python3 test_integration.py

clean:
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ 2>/dev/null || true

install:
	@echo "Installing TTK..."
	@cd ttk && pip3 install .
	@echo "Installing TFM..."
	@pip3 install .

uninstall:
	@echo "Uninstalling TFM..."
	@pip3 uninstall -y tfm
	@echo "Uninstalling TTK..."
	@pip3 uninstall -y ttk

dev-install:
	@echo "Installing TTK in development mode..."
	@cd ttk && pip3 install -e .
	@echo "Installing TFM in development mode..."
	@pip3 install -e .

lint:
	@echo "Running linting..."
	@python3 -m flake8 src/ --max-line-length=120 --ignore=E501,W503 || echo "flake8 not available"
	@python3 -m pylint src/ || echo "pylint not available"

format:
	@echo "Formatting code..."
	@python3 -m black src/ --line-length=120 || echo "black not available"
	@python3 -m isort src/ || echo "isort not available"

demo:
	@echo "Running TFM demo..."
	@cd test && python3 demo_delete_feature.py
