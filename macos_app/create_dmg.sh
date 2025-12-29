#!/bin/bash
#
# TFM DMG Installer Creation Script
#
# This script creates a distributable DMG installer for TFM.app
#

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================

# Determine project root (parent of macos_app directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Build paths
BUILD_DIR="${SCRIPT_DIR}/build"
APP_NAME="TFM"
APP_BUNDLE="${BUILD_DIR}/${APP_NAME}.app"

# DMG configuration
DMG_TEMP_DIR="${BUILD_DIR}/dmg_temp"
DMG_NAME="TFM"
VOLUME_NAME="TFM Installer"

# Version number (can be overridden by environment variable)
VERSION="${VERSION:-0.99}"

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

check_app_exists() {
    if [ ! -d "${APP_BUNDLE}" ]; then
        log_error "TFM.app not found at ${APP_BUNDLE}"
        log_error "Please run build.sh first to create the app bundle"
        exit 1
    fi
}

extract_version_from_plist() {
    # Try to extract version from built Info.plist
    local plist="${APP_BUNDLE}/Contents/Info.plist"
    if [ -f "${plist}" ]; then
        local version=$(defaults read "${plist}" CFBundleShortVersionString 2>/dev/null || echo "")
        if [ -n "${version}" ]; then
            echo "${version}"
            return 0
        fi
    fi
    
    # Fallback to VERSION environment variable or default
    echo "${VERSION}"
}

create_install_doc() {
    local install_md="${DMG_TEMP_DIR}/INSTALL.md"
    
    # Check if INSTALL.md exists in project root
    if [ -f "${PROJECT_ROOT}/INSTALL.md" ]; then
        log_info "Copying existing INSTALL.md"
        cp "${PROJECT_ROOT}/INSTALL.md" "${install_md}"
    else
        log_info "Creating INSTALL.md"
        cat > "${install_md}" << 'EOF'
# TFM Installation Instructions

## Installation

1. Drag **TFM.app** to your **Applications** folder
2. Double-click TFM.app to launch
3. If you see a security warning, go to System Preferences > Security & Privacy and click "Open Anyway"

## Usage

- **New Window**: Right-click the Dock icon and select "New Window"
- **Quit**: Press Cmd+Q or right-click the Dock icon and select "Quit"

## Requirements

- macOS 10.13 (High Sierra) or later
- No additional software installation required

## Features

- Dual-pane file manager with native macOS interface
- Full keyboard and mouse support
- S3 bucket browsing support
- Archive file viewing (zip, tar, etc.)
- Syntax-highlighted text viewer
- Directory comparison tool

## Troubleshooting

If TFM fails to launch:

1. Check Console.app for error messages
2. Ensure you're running macOS 10.13 or later
3. Try reinstalling by dragging TFM.app to Trash and reinstalling

For more information, visit: https://github.com/shimomut/tfm

EOF
    fi
}

# ============================================================================
# Main Build Process
# ============================================================================

main() {
    log_info "Starting DMG creation for TFM"
    
    # Check prerequisites
    check_app_exists
    
    # Extract version
    VERSION=$(extract_version_from_plist)
    DMG_FILENAME="${DMG_NAME}-${VERSION}.dmg"
    DMG_PATH="${BUILD_DIR}/${DMG_FILENAME}"
    
    log_info "Creating DMG: ${DMG_FILENAME}"
    log_info "Version: ${VERSION}"
    
    # Clean up any existing DMG temp directory
    if [ -d "${DMG_TEMP_DIR}" ]; then
        log_info "Cleaning up existing DMG temp directory"
        rm -rf "${DMG_TEMP_DIR}"
    fi
    
    # Create temporary DMG directory
    log_info "Creating temporary DMG directory"
    mkdir -p "${DMG_TEMP_DIR}"
    
    # Copy TFM.app to DMG directory
    log_info "Copying TFM.app to DMG directory"
    cp -R "${APP_BUNDLE}" "${DMG_TEMP_DIR}/"
    
    # Create or copy INSTALL.md
    create_install_doc
    
    # Copy LICENSE file
    log_info "Copying LICENSE file"
    if [ -f "${PROJECT_ROOT}/LICENSE" ]; then
        cp "${PROJECT_ROOT}/LICENSE" "${DMG_TEMP_DIR}/"
    else
        log_warning "LICENSE file not found at ${PROJECT_ROOT}/LICENSE"
    fi
    
    # Remove any existing DMG with the same name
    if [ -f "${DMG_PATH}" ]; then
        log_info "Removing existing DMG"
        rm -f "${DMG_PATH}"
    fi
    
    # Create DMG using hdiutil
    log_info "Creating DMG with hdiutil"
    hdiutil create \
        -volname "${VOLUME_NAME}" \
        -srcfolder "${DMG_TEMP_DIR}" \
        -ov \
        -format UDZO \
        "${DMG_PATH}"
    
    # Clean up temporary directory
    log_info "Cleaning up temporary directory"
    rm -rf "${DMG_TEMP_DIR}"
    
    # Success
    log_info "DMG created successfully: ${DMG_PATH}"
    log_info "Size: $(du -h "${DMG_PATH}" | cut -f1)"
    
    echo ""
    echo "✓ DMG installer created: ${DMG_FILENAME}"
    echo "  Location: ${DMG_PATH}"
    echo ""
}

# Run main function
main "$@"
