# TFM Makefile

.PHONY: help run run-debug run-profile monitor-log test test-quick clean install uninstall dev-install lint format demo macos-app macos-app-clean macos-app-install macos-refresh-icon macos-dmg install-config

# Backend selection (default: curses)
# Usage: make run BACKEND=coregraphics
# Valid options: curses, coregraphics
BACKEND ?= curses

help:
	@echo "TFM - Terminal File Manager"
	@echo ""
	@echo "Available commands:"
	@echo "  run            - Run TFM"
	@echo "  run-debug      - Run TFM with debug mode and remote log monitoring"
	@echo "  run-profile    - Run TFM with performance profiling enabled"
	@echo "  monitor-log    - Connect to remote log monitoring (port 8123)"
	@echo "  test           - Run all tests"
	@echo "  test-quick     - Run quick verification tests"
	@echo "  clean          - Clean up temporary files"
	@echo "  install        - Install TFM"
	@echo "  uninstall      - Uninstall TFM"
	@echo "  dev-install    - Install in development mode"
	@echo "  install-config - Copy default config to ~/.tfm/config.py (overwrites existing)"
	@echo "  lint           - Run code linting"
	@echo "  format         - Format code"
	@echo ""
	@echo "macOS App Bundle:"
	@echo "  macos-app         - Build native macOS application bundle"
	@echo "  macos-app-clean   - Clean macOS app build artifacts"
	@echo "  macos-app-install - Install TFM.app to Applications folder"
	@echo "  macos-refresh-icon - Refresh macOS icon cache (after icon changes)"
	@echo "  macos-dmg         - Create DMG installer for distribution"
	@echo ""
	@echo "Backend Selection:"
	@echo "  BACKEND=curses         - Use curses (terminal) backend (default)"
	@echo "  BACKEND=coregraphics   - Use CoreGraphics (macOS desktop) backend"
	@echo ""
	@echo "Examples:"
	@echo "  make run                        # Run with curses backend (default)"
	@echo "  make run BACKEND=coregraphics   # Run with CoreGraphics backend"
	@echo "  make test BACKEND=coregraphics  # Test with CoreGraphics backend"
	@echo "  make install-config             # Install/update user config file"
	@echo "  make macos-app                  # Build macOS app bundle"
	@echo "  make macos-app-install          # Install to /Applications"
	@echo "  make macos-dmg                  # Create DMG installer"

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
	@python3 src/tools/tfm_log_client.py localhost 8123

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

install-config:
	@echo "Installing default configuration to ~/.tfm/config.py..."
	@mkdir -p ~/.tfm
	@if [ -f ~/.tfm/config.py ]; then \
		echo "Warning: ~/.tfm/config.py already exists"; \
		echo "This will overwrite your existing configuration!"; \
		read -p "Continue? [y/N] " confirm; \
		if [ "$${confirm}" = "y" ] || [ "$${confirm}" = "Y" ]; then \
			cp src/_config.py ~/.tfm/config.py; \
			echo "Configuration installed successfully"; \
			echo "Your old config has been overwritten"; \
		else \
			echo "Installation cancelled"; \
			exit 1; \
		fi; \
	else \
		cp src/_config.py ~/.tfm/config.py; \
		echo "Configuration installed successfully"; \
	fi

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

# ============================================================================
# macOS App Bundle Targets
# ============================================================================

macos-app:
	@echo "Building macOS application bundle..."
	@cd macos_app && ./build.sh

macos-app-clean:
	@echo "Cleaning macOS app build artifacts..."
	@rm -rf macos_app/build/
	@echo "Build artifacts removed"

macos-app-install:
	@echo "Installing TFM.app to Applications..."
	@if [ ! -d "macos_app/build/TFM.app" ]; then \
		echo "Error: TFM.app not found. Run 'make macos-app' first."; \
		exit 1; \
	fi
	@echo "Choose installation location:"
	@echo "  1) /Applications (system-wide, requires sudo)"
	@echo "  2) ~/Applications (user-only)"
	@read -p "Enter choice [1-2]: " choice; \
	case $$choice in \
		1) \
			echo "Installing to /Applications..."; \
			sudo cp -R macos_app/build/TFM.app /Applications/; \
			echo "TFM.app installed to /Applications"; \
			;; \
		2) \
			echo "Installing to ~/Applications..."; \
			mkdir -p ~/Applications; \
			cp -R macos_app/build/TFM.app ~/Applications/; \
			echo "TFM.app installed to ~/Applications"; \
			;; \
		*) \
			echo "Invalid choice. Installation cancelled."; \
			exit 1; \
			;; \
	esac

macos-refresh-icon:
	@echo "Refreshing macOS icon cache..."
	@if [ ! -d "macos_app/build/TFM.app" ]; then \
		echo "Warning: TFM.app not found at macos_app/build/TFM.app"; \
	else \
		touch macos_app/build/TFM.app; \
		echo "Touched app bundle to invalidate cache"; \
	fi
	@echo "Clearing system icon cache (may require password)..."
	@sudo rm -rf /Library/Caches/com.apple.iconservices.store 2>/dev/null || echo "Skipped system cache (no sudo access)"
	@rm -rf ~/Library/Caches/com.apple.iconservices 2>/dev/null || true
	@echo "Restarting Dock and Finder..."
	@killall Dock 2>/dev/null || true
	@killall Finder 2>/dev/null || true
	@echo "Icon cache cleared successfully"
	@echo "The new icon should appear now. If the app is running, quit and relaunch it."

macos-dmg: macos-app
	@echo "Creating DMG installer..."
	@cd macos_app && ./create_dmg.sh
	@echo "DMG installer created successfully"
