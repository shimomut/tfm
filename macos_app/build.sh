#!/bin/bash
#
# TFM macOS App Bundle Build Script
#
# This script compiles the Objective-C launcher and creates a complete
# macOS application bundle for TFM with embedded Python interpreter.
#

set -e  # Exit on error

# ============================================================================
# Build Configuration
# ============================================================================

# Determine project root (parent of macos_app directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Build paths
BUILD_DIR="${SCRIPT_DIR}/build"
APP_NAME="TFM"
APP_BUNDLE="${BUILD_DIR}/${APP_NAME}.app"

# Source paths
SRC_DIR="${SCRIPT_DIR}/src"
RESOURCES_DIR="${SCRIPT_DIR}/resources"

# Python configuration
PYTHON_VERSION="3.12"
PYTHON_FRAMEWORK="/Library/Frameworks/Python.framework"

# Compiler settings
CC="clang"
CFLAGS="-framework Cocoa"
CFLAGS="${CFLAGS} -F${PYTHON_FRAMEWORK}/Versions/${PYTHON_VERSION}"
CFLAGS="${CFLAGS} -I${PYTHON_FRAMEWORK}/Versions/${PYTHON_VERSION}/include/python${PYTHON_VERSION}"
CFLAGS="${CFLAGS} -L${PYTHON_FRAMEWORK}/Versions/${PYTHON_VERSION}/lib"
CFLAGS="${CFLAGS} -lpython${PYTHON_VERSION}"
LDFLAGS="-rpath @executable_path/../Frameworks"

# Code signing (optional - set to enable signing)
CODESIGN_IDENTITY="${CODESIGN_IDENTITY:-}"

# Version number (can be overridden by environment variable)
VERSION="${VERSION:-0.98}"

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

log_success() {
    echo "[SUCCESS] $1"
}

# ============================================================================
# Build Script Entry Point
# ============================================================================

log_info "Starting TFM macOS app bundle build..."
log_info "Project root: ${PROJECT_ROOT}"
log_info "Build directory: ${BUILD_DIR}"
log_info "Python version: ${PYTHON_VERSION}"

# ============================================================================
# Step 1: Compile Objective-C Source Files
# ============================================================================

log_info "Step 1: Compiling Objective-C source files..."

# Create build directory if it doesn't exist
mkdir -p "${BUILD_DIR}"

# Compile main.m and TFMAppDelegate.m
SOURCES="${SRC_DIR}/main.m ${SRC_DIR}/TFMAppDelegate.m"
OUTPUT_EXECUTABLE="${BUILD_DIR}/${APP_NAME}"

log_info "Compiling: ${SOURCES}"
log_info "Output: ${OUTPUT_EXECUTABLE}"

if ! ${CC} ${CFLAGS} ${LDFLAGS} -o "${OUTPUT_EXECUTABLE}" ${SOURCES}; then
    log_error "Compilation failed"
    exit 1
fi

log_success "Compilation completed successfully"

# ============================================================================
# Step 2: Create Bundle Structure
# ============================================================================

log_info "Step 2: Creating bundle structure..."

# Create bundle directories
CONTENTS_DIR="${APP_BUNDLE}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RESOURCES_DIR_BUNDLE="${CONTENTS_DIR}/Resources"
FRAMEWORKS_DIR="${CONTENTS_DIR}/Frameworks"

mkdir -p "${MACOS_DIR}"
mkdir -p "${RESOURCES_DIR_BUNDLE}"
mkdir -p "${FRAMEWORKS_DIR}"

log_success "Bundle directories created"

# Copy executable to MacOS directory
log_info "Copying executable to bundle..."
cp "${OUTPUT_EXECUTABLE}" "${MACOS_DIR}/${APP_NAME}"
chmod +x "${MACOS_DIR}/${APP_NAME}"

log_success "Executable copied and permissions set"

# ============================================================================
# Step 3: Copy Resources
# ============================================================================

log_info "Step 3: Copying resources..."

# Copy TFM Python source
log_info "Copying TFM Python source..."
TFM_DEST="${RESOURCES_DIR_BUNDLE}/tfm"
mkdir -p "${TFM_DEST}"
cp -R "${PROJECT_ROOT}/src/"* "${TFM_DEST}/"

# Copy TTK library
log_info "Copying TTK library..."
TTK_DEST="${RESOURCES_DIR_BUNDLE}/ttk"
if [ -d "${PROJECT_ROOT}/ttk" ]; then
    cp -R "${PROJECT_ROOT}/ttk" "${TTK_DEST}"
else
    log_error "TTK library not found at ${PROJECT_ROOT}/ttk"
    exit 1
fi

# Collect Python dependencies
log_info "Collecting Python dependencies..."
PACKAGES_DEST="${RESOURCES_DIR_BUNDLE}/python_packages"
mkdir -p "${PACKAGES_DEST}"

REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"
COLLECT_SCRIPT="${SCRIPT_DIR}/collect_dependencies.py"

if [ -f "${COLLECT_SCRIPT}" ]; then
    if python3 "${COLLECT_SCRIPT}" --requirements "${REQUIREMENTS_FILE}" --dest "${PACKAGES_DEST}"; then
        log_success "Dependencies collected successfully"
    else
        log_error "Failed to collect dependencies"
        log_error "Please ensure all dependencies are installed: pip install -r requirements.txt"
        exit 1
    fi
else
    log_warning "Dependency collection script not found at ${COLLECT_SCRIPT}"
    log_warning "Python packages will need to be added manually"
fi

# Copy application icon if it exists
ICON_SOURCE="${RESOURCES_DIR}/TFM.icns"
if [ -f "${ICON_SOURCE}" ]; then
    log_info "Copying application icon..."
    cp "${ICON_SOURCE}" "${RESOURCES_DIR_BUNDLE}/"
else
    log_info "Warning: Application icon not found at ${ICON_SOURCE}"
fi

log_success "Resources copied successfully"

# ============================================================================
# Step 4: Embed Python.framework
# ============================================================================

log_info "Step 4: Embedding Python.framework..."

# Locate system Python.framework
PYTHON_FW_SOURCE="${PYTHON_FRAMEWORK}/Versions/${PYTHON_VERSION}"
if [ ! -d "${PYTHON_FW_SOURCE}" ]; then
    log_error "Python.framework not found at ${PYTHON_FW_SOURCE}"
    log_error "Please install Python ${PYTHON_VERSION} framework"
    exit 1
fi

# Copy Python.framework to bundle
log_info "Copying Python.framework from ${PYTHON_FW_SOURCE}..."
PYTHON_FW_DEST="${FRAMEWORKS_DIR}/Python.framework/Versions/${PYTHON_VERSION}"
mkdir -p "${PYTHON_FW_DEST}"

# Copy essential framework components (use rsync to handle permissions better)
if command -v rsync > /dev/null 2>&1; then
    # Use rsync if available (better permission handling)
    rsync -a --no-perms --chmod=u+rw "${PYTHON_FW_SOURCE}/Python" "${PYTHON_FW_DEST}/"
    rsync -a --no-perms --chmod=u+rw "${PYTHON_FW_SOURCE}/Resources" "${PYTHON_FW_DEST}/"
    rsync -a --no-perms --chmod=u+rw "${PYTHON_FW_SOURCE}/lib" "${PYTHON_FW_DEST}/"
else
    # Fallback to cp with permission fixes
    cp -R "${PYTHON_FW_SOURCE}/Python" "${PYTHON_FW_DEST}/" 2>/dev/null || true
    cp -R "${PYTHON_FW_SOURCE}/Resources" "${PYTHON_FW_DEST}/" 2>/dev/null || true
    cp -R "${PYTHON_FW_SOURCE}/lib" "${PYTHON_FW_DEST}/" 2>/dev/null || true
    # Fix permissions on copied files
    chmod -R u+rw "${PYTHON_FW_DEST}" 2>/dev/null || true
fi

# Create version symlinks
cd "${FRAMEWORKS_DIR}/Python.framework/Versions"
ln -sf "${PYTHON_VERSION}" Current
cd "${FRAMEWORKS_DIR}/Python.framework"
ln -sf "Versions/Current/Python" Python
ln -sf "Versions/Current/Resources" Resources

log_success "Python.framework embedded successfully"

# Update install names to use embedded framework
log_info "Updating install names to use embedded framework..."
install_name_tool -change \
    "/Library/Frameworks/Python.framework/Versions/${PYTHON_VERSION}/Python" \
    "@executable_path/../Frameworks/Python.framework/Versions/${PYTHON_VERSION}/Python" \
    "${MACOS_DIR}/${APP_NAME}"

log_success "Install names updated"

# ============================================================================
# Step 5: Generate Info.plist
# ============================================================================

log_info "Step 5: Generating Info.plist..."

TEMPLATE_FILE="${RESOURCES_DIR}/Info.plist.template"
PLIST_FILE="${CONTENTS_DIR}/Info.plist"

if [ ! -f "${TEMPLATE_FILE}" ]; then
    log_error "Info.plist template not found at ${TEMPLATE_FILE}"
    exit 1
fi

# Substitute version number
log_info "Substituting version: ${VERSION}"
sed "s/{{VERSION}}/${VERSION}/g" "${TEMPLATE_FILE}" > "${PLIST_FILE}"

# Validate Info.plist is valid XML
if ! plutil -lint "${PLIST_FILE}" > /dev/null 2>&1; then
    log_error "Generated Info.plist is not valid XML"
    exit 1
fi

log_success "Info.plist generated and validated"

# ============================================================================
# Step 6: Code Signing (Optional)
# ============================================================================

if [ -n "${CODESIGN_IDENTITY}" ]; then
    log_info "Step 6: Code signing bundle..."
    
    # Sign frameworks
    log_info "Signing Python.framework..."
    codesign --force --sign "${CODESIGN_IDENTITY}" "${FRAMEWORKS_DIR}/Python.framework"
    
    # Sign executable
    log_info "Signing executable..."
    codesign --force --sign "${CODESIGN_IDENTITY}" "${MACOS_DIR}/${APP_NAME}"
    
    # Sign bundle
    log_info "Signing app bundle..."
    codesign --force --sign "${CODESIGN_IDENTITY}" "${APP_BUNDLE}"
    
    # Verify signature
    if codesign -v "${APP_BUNDLE}" 2>&1; then
        log_success "Code signing completed and verified"
    else
        log_error "Code signing verification failed"
        exit 1
    fi
else
    log_info "Step 6: Skipping code signing (no identity provided)"
fi

# ============================================================================
# Build Complete
# ============================================================================

log_success "Build completed successfully!"
log_info "Application bundle: ${APP_BUNDLE}"
log_info ""
log_info "To run the application:"
log_info "  open ${APP_BUNDLE}"
log_info ""
log_info "To install to Applications:"
log_info "  cp -R ${APP_BUNDLE} /Applications/"
