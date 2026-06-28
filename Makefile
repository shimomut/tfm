# TFM Makefile

.PHONY: help run run-gui test test-quick clean install uninstall dev-install lint format demo macos-app macos-app-clean macos-app-install macos-refresh-icon macos-dmg install-config venv venv-clean check-venv install-puikit

# Python interpreter selection
# All Python is run through the project virtual environment (.venv). There is no
# fallback to a system python3 - run 'make venv' first to create the environment.
# An absolute path is used so targets that change directories (e.g. "cd ttk && ...")
# still resolve the same interpreter.
PYTHON := $(abspath .venv/bin/python)
PIP := $(PYTHON) -m pip

# PuiKit source checkout (sibling repo). Installed editable into .venv so edits
# to PuiKit are picked up live with no reinstall. Override if it lives elsewhere:
#   make venv PUIKIT_DIR=/path/to/puikit
PUIKIT_DIR ?= ../puikit

help:
	@echo "TFM - Terminal File Manager"
	@echo ""
	@echo "Using Python: $(PYTHON)"
	@echo "(run 'make venv' first if .venv does not exist)"
	@echo ""
	@echo "Available commands:"
	@echo "  venv           - Create .venv using the latest python3 in PATH and install deps"
	@echo "  venv-clean     - Remove the .venv directory"
	@echo "  install-puikit - Install PuiKit (editable) from PUIKIT_DIR into .venv"
	@echo "  run            - Run TFM (terminal); LEFT=/RIGHT= set startup dirs"
	@echo "  run-gui        - Run TFM in a native macOS GUI window"
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
	@echo "Examples:"
	@echo "  make run                        # Run TFM in the terminal"
	@echo "  make run-gui                    # Run TFM in a macOS GUI window"
	@echo "  make run LEFT=./src RIGHT=./doc # Run with custom startup directories"
	@echo "  make install-config             # Install/update user config file"
	@echo "  make macos-app                  # Build macOS app bundle"
	@echo "  make macos-app-install          # Install to /Applications"
	@echo "  make macos-dmg                  # Create DMG installer"

venv:
	@if [ -d .venv ]; then \
		echo ".venv already exists. Run 'make venv-clean' first to recreate it."; \
		exit 1; \
	fi
	@echo "Searching for the latest python3 in PATH..."
	@best=""; best_key=0; \
	for dir in $$(echo "$$PATH" | tr ':' '\n'); do \
		for py in "$$dir"/python3.[0-9] "$$dir"/python3.[0-9][0-9]; do \
			[ -x "$$py" ] || continue; \
			key=$$("$$py" -c 'import sys; print(sys.version_info[0]*100 + sys.version_info[1])' 2>/dev/null) || continue; \
			if [ -n "$$key" ] && [ "$$key" -gt "$$best_key" ]; then \
				best_key=$$key; best="$$py"; \
			fi; \
		done; \
	done; \
	if [ -z "$$best" ]; then \
		if command -v python3 >/dev/null 2>&1; then \
			best=$$(command -v python3); \
			echo "No versioned python3.x found; falling back to python3"; \
		else \
			echo "Error: no python3 interpreter found in PATH"; \
			exit 1; \
		fi; \
	fi; \
	echo "Using $$best ($$($$best --version 2>&1)) to create .venv..."; \
	"$$best" -m venv .venv
	@echo "Upgrading pip..."
	@.venv/bin/python -m pip install --upgrade pip
	@echo "Installing dependencies from requirements.txt..."
	@.venv/bin/python -m pip install -r requirements.txt
	@$(MAKE) install-puikit
	@echo ""
	@echo ".venv created successfully with $$(.venv/bin/python --version 2>&1)"
	@echo "Run 'make run' to launch TFM using the new environment."

# Install PuiKit editable from its sibling checkout (PUIKIT_DIR). Run standalone
# to (re)link PuiKit into an existing .venv without recreating it.
install-puikit: check-venv
	@if [ ! -d "$(PUIKIT_DIR)" ]; then \
		echo "Error: PuiKit not found at $(PUIKIT_DIR). Set PUIKIT_DIR=/path/to/puikit."; \
		exit 1; \
	fi
	@echo "Installing PuiKit (editable) from $(PUIKIT_DIR)..."
	@$(PIP) install -e "$(PUIKIT_DIR)"

venv-clean:
	@echo "Removing .venv..."
	@rm -rf .venv
	@echo ".venv removed"

# Guard target: ensure the virtual environment exists before running any
# Python-based target. Fails with a clear message instead of falling back to
# system python.
check-venv:
	@if [ ! -x .venv/bin/python ]; then \
		echo "Error: .venv not found. Run 'make venv' to create it first."; \
		exit 1; \
	fi

# Run TFM (PuiKit). Optional startup directories: make run LEFT=./src RIGHT=./doc
PUIKIT_DIRS := $(if $(LEFT),--left $(LEFT)) $(if $(RIGHT),--right $(RIGHT))

run: check-venv
	@echo "Running TFM on PuiKit (terminal)..."
	@$(PYTHON) tfm_puikit.py $(PUIKIT_DIRS)

run-gui: check-venv
	@echo "Running TFM on PuiKit (macOS GUI)..."
	@$(PYTHON) tfm_puikit.py --backend gui $(PUIKIT_DIRS)

test: check-venv
	@echo "Running TFM tests..."
	@cd test && PYTHONPATH=../src $(PYTHON) -m pytest . -v || echo "pytest not available, running individual tests..."
	@cd test && for test in test_*.py; do echo "Running $$test..."; PYTHONPATH=../src $(PYTHON) "$$test" || exit 1; done

test-quick: check-venv
	@echo "Running quick verification tests..."
	@cd test && PYTHONPATH=../src $(PYTHON) test_cursor_movement.py
	@cd test && PYTHONPATH=../src $(PYTHON) test_delete_feature.py
	@cd test && PYTHONPATH=../src $(PYTHON) test_integration.py

clean:
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ 2>/dev/null || true

install: check-venv
	@echo "Installing TTK..."
	@cd ttk && $(PIP) install .
	@echo "Installing TFM..."
	@$(PIP) install .

uninstall: check-venv
	@echo "Uninstalling TFM..."
	@$(PIP) uninstall -y tfm
	@echo "Uninstalling TTK..."
	@$(PIP) uninstall -y ttk

dev-install: check-venv
	@echo "Installing TTK in development mode..."
	@cd ttk && $(PIP) install -e .
	@echo "Installing TFM in development mode..."
	@$(PIP) install -e .

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

lint: check-venv
	@echo "Running linting..."
	@$(PYTHON) -m flake8 src/ --max-line-length=120 --ignore=E501,W503 || echo "flake8 not available"
	@$(PYTHON) -m pylint src/ || echo "pylint not available"

format: check-venv
	@echo "Formatting code..."
	@$(PYTHON) -m black src/ --line-length=120 || echo "black not available"
	@$(PYTHON) -m isort src/ || echo "isort not available"

demo: check-venv
	@echo "Running TFM demo..."
	@cd test && $(PYTHON) demo_delete_feature.py

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
