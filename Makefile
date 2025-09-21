# TFM Makefile

.PHONY: help run test clean install dev-install lint format

help:
	@echo "TFM - Terminal File Manager"
	@echo ""
	@echo "Available commands:"
	@echo "  run          - Run TFM"
	@echo "  test         - Run all tests"
	@echo "  test-quick   - Run quick verification tests"
	@echo "  clean        - Clean up temporary files"
	@echo "  install      - Install TFM"
	@echo "  dev-install  - Install in development mode"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code"

run:
	@python3 tfm.py

test:
	@echo "Running TFM tests..."
	@cd test && PYTHONPATH=../src python3 -m pytest . -v || echo "pytest not available, running individual tests..."
	@cd test && for test in test_*.py; do echo "Running $$test..."; PYTHONPATH=../src python3 "$$test" || exit 1; done

test-quick:
	@echo "Running quick verification tests..."
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
	@pip3 install .

dev-install:
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