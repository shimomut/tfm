#!/bin/bash
#
# TFM macOS App Bundle Build Script
#
# This script compiles the Objective-C launcher and creates a complete
# macOS application bundle for TFM with embedded Python interpreter.
#

set -e  # Exit on error

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo "[INFO] $1"
}

log_warning() {
    echo "[WARNING] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

log_success() {
    echo "[SUCCESS] $1"
}

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

# Python configuration - detect from .venv
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python3"
if [ ! -f "${VENV_PYTHON}" ]; then
    log_error "Virtual environment not found at ${PROJECT_ROOT}/.venv"
    log_error "Please create a virtual environment: python3 -m venv .venv"
    exit 1
fi

# Get Python version and paths from venv
PYTHON_VERSION=$("${VENV_PYTHON}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_BASE_PREFIX=$("${VENV_PYTHON}" -c "import sys; print(sys.base_prefix)")
PYTHON_SITE_PACKAGES="${PROJECT_ROOT}/.venv/lib/python${PYTHON_VERSION}/site-packages"

log_info "Detected Python ${PYTHON_VERSION} from venv"
log_info "Python base: ${PYTHON_BASE_PREFIX}"
log_info "Site packages: ${PYTHON_SITE_PACKAGES}"

# Check if using Python.framework or standard Python installation
# Python.framework can be in /Library/Frameworks (python.org) or /opt/homebrew (Homebrew)
if [[ "${PYTHON_BASE_PREFIX}" == *"/Python.framework/Versions/"* ]]; then
    # Python.framework installation (python.org or Homebrew)
    # Extract framework root by removing /Versions/X.Y suffix
    PYTHON_FRAMEWORK="${PYTHON_BASE_PREFIX%/Versions/*}"
    USE_FRAMEWORK=true
    log_info "Using Python.framework installation"
    log_info "Framework root: ${PYTHON_FRAMEWORK}"
else
    # Standard Python installation (mise, pyenv, system Python)
    PYTHON_FRAMEWORK="${PYTHON_BASE_PREFIX}"
    USE_FRAMEWORK=false
    log_info "Using standard Python installation"
fi

# Compiler settings
CC="clang"
CFLAGS="-framework Cocoa"

# Configure compiler flags based on Python installation type
if [ "$USE_FRAMEWORK" = true ]; then
    # Python.framework style
    CFLAGS="${CFLAGS} -F${PYTHON_FRAMEWORK}/Versions/${PYTHON_VERSION}"
    CFLAGS="${CFLAGS} -I${PYTHON_FRAMEWORK}/Versions/${PYTHON_VERSION}/include/python${PYTHON_VERSION}"
    CFLAGS="${CFLAGS} -L${PYTHON_FRAMEWORK}/Versions/${PYTHON_VERSION}/lib"
else
    # Standard Python style
    CFLAGS="${CFLAGS} -I${PYTHON_BASE_PREFIX}/include/python${PYTHON_VERSION}"
    CFLAGS="${CFLAGS} -L${PYTHON_BASE_PREFIX}/lib"
fi

CFLAGS="${CFLAGS} -lpython${PYTHON_VERSION}"
LDFLAGS="-rpath @executable_path/../Frameworks"

# Code signing (optional - set to enable signing)
CODESIGN_IDENTITY="${CODESIGN_IDENTITY:-}"

# Version number (can be overridden by environment variable)
VERSION="${VERSION:-0.98}"

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

# Pre-compile TFM Python files
log_info "Pre-compiling TFM Python files..."
if "${VENV_PYTHON}" -m compileall -q "${TFM_DEST}"; then
    log_info "  Compiled TFM Python files"
else
    log_info "  Warning: Compilation failed"
fi

# Copy TTK library (runtime files only)
log_info "Copying TTK library..."
TTK_DEST="${RESOURCES_DIR_BUNDLE}/ttk"
TTK_SRC="${PROJECT_ROOT}/ttk"

if [ ! -d "${TTK_SRC}" ]; then
    log_error "TTK library not found at ${TTK_SRC}"
    exit 1
fi

# Create TTK destination directory
mkdir -p "${TTK_DEST}"

# Copy only runtime files (exclude docs, tests, demos, build artifacts)
log_info "  Copying TTK runtime files..."

# Copy essential Python files (exclude py.typed - only needed for type checkers)
cp "${TTK_SRC}/__init__.py" "${TTK_DEST}/" 2>/dev/null || true

# Copy top-level Python modules (exclude test/demo/setup files)
for file in "${TTK_SRC}"/*.py; do
    if [ -f "$file" ]; then
        basename=$(basename "$file")
        # Skip test, demo, and setup files
        if [[ ! "$basename" =~ ^test_ ]] && [[ ! "$basename" =~ ^demo_ ]] && [[ "$basename" != "setup.py" ]]; then
            cp "$file" "${TTK_DEST}/"
        fi
    fi
done

# Copy essential subdirectories (backends, serialization, utils)
for dir in backends serialization utils; do
    if [ -d "${TTK_SRC}/${dir}" ]; then
        cp -R "${TTK_SRC}/${dir}" "${TTK_DEST}/"
        log_info "    Copied ${dir}/"
    fi
done

# Remove C++ source files from backends (only compiled .so is needed)
if [ -d "${TTK_DEST}/backends" ]; then
    find "${TTK_DEST}/backends" -name "*.cpp" -delete 2>/dev/null || true
    log_info "    Removed C++ source files from backends/"
fi

log_info "  TTK runtime files copied (excluded: doc/, demo/, test/, build/, .coverage, etc.)"

# Copy C++ renderer extension module to Resources root
# This allows "import ttk_coregraphics_render" to work from anywhere
log_info "Copying C++ renderer extension module..."
if [ -f "${PROJECT_ROOT}/ttk_coregraphics_render.cpython-313-darwin.so" ]; then
    cp "${PROJECT_ROOT}/ttk_coregraphics_render.cpython-313-darwin.so" "${RESOURCES_DIR_BUNDLE}/"
    log_info "  Copied ttk_coregraphics_render.cpython-313-darwin.so to Resources/"
else
    log_warning "C++ renderer module not found at project root"
    log_warning "Application will fall back to PyObjC rendering"
fi

# Pre-compile TTK Python files
log_info "Pre-compiling TTK Python files..."
if "${VENV_PYTHON}" -m compileall -q "${TTK_DEST}"; then
    log_info "  Compiled TTK Python files"
else
    log_info "  Warning: Compilation failed"
fi

# Collect Python dependencies
log_info "Collecting Python dependencies..."
PACKAGES_DEST="${RESOURCES_DIR_BUNDLE}/python_packages"
mkdir -p "${PACKAGES_DEST}"

REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"
COLLECT_SCRIPT="${SCRIPT_DIR}/collect_dependencies.py"

if [ -f "${COLLECT_SCRIPT}" ]; then
    # Use venv's Python to run the collection script
    if "${VENV_PYTHON}" "${COLLECT_SCRIPT}" --requirements "${REQUIREMENTS_FILE}" --dest "${PACKAGES_DEST}"; then
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

# Copy LICENSE file
LICENSE_SOURCE="${PROJECT_ROOT}/LICENSE"
if [ -f "${LICENSE_SOURCE}" ]; then
    log_info "Copying LICENSE file..."
    cp "${LICENSE_SOURCE}" "${RESOURCES_DIR_BUNDLE}/"
else
    log_warning "LICENSE file not found at ${LICENSE_SOURCE}"
fi

log_success "Resources copied successfully"

# ============================================================================
# Step 4: Embed Python
# ============================================================================

log_info "Step 4: Embedding Python..."

# Clean up old Python versions from previous builds
if [ -d "${FRAMEWORKS_DIR}/Python.framework/Versions" ]; then
    log_info "Cleaning up old Python versions..."
    for old_version in "${FRAMEWORKS_DIR}/Python.framework/Versions"/*; do
        if [ -d "${old_version}" ] && [ "$(basename "${old_version}")" != "Current" ] && [ "$(basename "${old_version}")" != "${PYTHON_VERSION}" ]; then
            log_info "  Removing old version: $(basename "${old_version}")"
            rm -rf "${old_version}"
        fi
    done
fi

# Determine Python source based on installation type
if [ "$USE_FRAMEWORK" = true ]; then
    # Python.framework installation
    PYTHON_SOURCE="${PYTHON_FRAMEWORK}/Versions/${PYTHON_VERSION}"
    if [ ! -d "${PYTHON_SOURCE}" ]; then
        log_error "Python.framework not found at ${PYTHON_SOURCE}"
        exit 1
    fi
    
    # Copy Python.framework to bundle
    log_info "Copying Python.framework from ${PYTHON_SOURCE}..."
    PYTHON_DEST="${FRAMEWORKS_DIR}/Python.framework/Versions/${PYTHON_VERSION}"
    mkdir -p "${PYTHON_DEST}"
    
    # Copy essential framework components
    if command -v rsync > /dev/null 2>&1; then
        rsync -a --no-perms --chmod=u+rw "${PYTHON_SOURCE}/Python" "${PYTHON_DEST}/"
        rsync -a --no-perms --chmod=u+rw "${PYTHON_SOURCE}/Resources" "${PYTHON_DEST}/" 2>/dev/null || true
        rsync -a --no-perms --chmod=u+rw "${PYTHON_SOURCE}/lib" "${PYTHON_DEST}/"
        rsync -a --no-perms --chmod=u+rw "${PYTHON_SOURCE}/bin" "${PYTHON_DEST}/"
    else
        cp -R "${PYTHON_SOURCE}/Python" "${PYTHON_DEST}/" 2>/dev/null || true
        cp -R "${PYTHON_SOURCE}/Resources" "${PYTHON_DEST}/" 2>/dev/null || true
        cp -R "${PYTHON_SOURCE}/lib" "${PYTHON_DEST}/"
        cp -R "${PYTHON_SOURCE}/bin" "${PYTHON_DEST}/"
        chmod -R u+rw "${PYTHON_DEST}" 2>/dev/null || true
    fi
    
    # Create version symlinks
    cd "${FRAMEWORKS_DIR}/Python.framework/Versions"
    ln -sf "${PYTHON_VERSION}" Current
    cd "${FRAMEWORKS_DIR}/Python.framework"
    ln -sf "Versions/Current/Python" Python
    ln -sf "Versions/Current/bin" bin
    
    # Create python3 symlink in bin directory
    log_info "Creating python3 symlink in bin directory..."
    cd "${PYTHON_DEST}/bin"
    if [ -f "python${PYTHON_VERSION}" ]; then
        ln -sf "python${PYTHON_VERSION}" python3
        log_info "  Created python3 -> python${PYTHON_VERSION}"
    fi
    
    # Add sitecustomize.py to disable user site-packages
    log_info "Adding sitecustomize.py to disable user site-packages..."
    SITECUSTOMIZE_SOURCE="${SCRIPT_DIR}/resources/sitecustomize.py"
    SITECUSTOMIZE_DEST="${PYTHON_DEST}/lib/python${PYTHON_VERSION}/sitecustomize.py"
    if [ -f "${SITECUSTOMIZE_SOURCE}" ]; then
        cp "${SITECUSTOMIZE_SOURCE}" "${SITECUSTOMIZE_DEST}"
        log_info "  Installed sitecustomize.py"
    else
        log_error "sitecustomize.py not found at ${SITECUSTOMIZE_SOURCE}"
        exit 1
    fi
    
    log_success "Python.framework embedded successfully"
    
    # Remove unnecessary files from embedded Python
    log_info "Removing unnecessary files from embedded Python..."
    
    # Remove Python.app (GUI launcher)
    if [ -d "${PYTHON_DEST}/Resources/Python.app" ]; then
        rm -rf "${PYTHON_DEST}/Resources/Python.app"
        log_info "  Removed Python.app"
    fi
    
    # Remove Resources directory entirely (Info.plist not needed for embedded use)
    if [ -d "${PYTHON_DEST}/Resources" ]; then
        rm -rf "${PYTHON_DEST}/Resources"
        log_info "  Removed Resources/"
    fi
    
    # Remove development tools from bin/
    for tool in idle3.13 pip3 pip3.13 pydoc3.13 python3.13-config; do
        if [ -f "${PYTHON_DEST}/bin/${tool}" ]; then
            rm -f "${PYTHON_DEST}/bin/${tool}"
            log_info "  Removed bin/${tool}"
        fi
    done
    
    # Remove pkg-config files
    if [ -d "${PYTHON_DEST}/lib/pkgconfig" ]; then
        rm -rf "${PYTHON_DEST}/lib/pkgconfig"
        log_info "  Removed lib/pkgconfig/"
    fi
    
    # Remove Python test suite (saves ~68MB)
    if [ -d "${PYTHON_DEST}/lib/python${PYTHON_VERSION}/test" ]; then
        rm -rf "${PYTHON_DEST}/lib/python${PYTHON_VERSION}/test"
        log_info "  Removed lib/python${PYTHON_VERSION}/test/"
    fi
    
    log_success "Unnecessary files removed"
    
    # Pre-compile Python standard library
    log_info "Pre-compiling Python standard library..."
    STDLIB_PATH="${PYTHON_DEST}/lib/python${PYTHON_VERSION}"
    if [ -d "${STDLIB_PATH}" ]; then
        # Use the bundled Python to compile the standard library
        # This ensures compatibility and uses the correct Python version
        BUNDLE_PYTHON="${PYTHON_DEST}/bin/python3"
        if [ -f "${BUNDLE_PYTHON}" ]; then
            # Compile all .py files in the standard library
            # -q: quiet mode (only show errors)
            # -f: force recompilation even if .pyc files exist
            if "${BUNDLE_PYTHON}" -m compileall -q -f "${STDLIB_PATH}"; then
                log_info "  Compiled Python standard library"
                
                # Count compiled files for verification
                PYC_COUNT=$(find "${STDLIB_PATH}" -name "*.pyc" | wc -l | tr -d ' ')
                PY_COUNT=$(find "${STDLIB_PATH}" -name "*.py" | wc -l | tr -d ' ')
                log_info "  Created ${PYC_COUNT} .pyc files from ${PY_COUNT} .py files"
            else
                log_warning "Standard library compilation had errors (non-critical)"
            fi
        else
            log_warning "Bundled Python not found, skipping standard library pre-compilation"
        fi
    else
        log_warning "Standard library path not found: ${STDLIB_PATH}"
    fi
    
    # Update install names to use embedded framework
    log_info "Updating install names to use embedded framework..."
    install_name_tool -change \
        "${PYTHON_BASE_PREFIX}/Python" \
        "@executable_path/../Frameworks/Python.framework/Versions/${PYTHON_VERSION}/Python" \
        "${MACOS_DIR}/${APP_NAME}"
else
    # Standard Python installation (mise, pyenv, homebrew, etc.)
    log_info "Copying Python from ${PYTHON_BASE_PREFIX}..."
    PYTHON_DEST="${FRAMEWORKS_DIR}/Python.framework/Versions/${PYTHON_VERSION}"
    mkdir -p "${PYTHON_DEST}"
    
    # Copy Python components (excluding problematic symlinks from source)
    if command -v rsync > /dev/null 2>&1; then
        rsync -a --no-perms --chmod=u+rw "${PYTHON_BASE_PREFIX}/lib" "${PYTHON_DEST}/"
        rsync -a --no-perms --chmod=u+rw "${PYTHON_BASE_PREFIX}/bin" "${PYTHON_DEST}/"
        rsync -a --no-perms --chmod=u+rw "${PYTHON_BASE_PREFIX}/include" "${PYTHON_DEST}/" 2>/dev/null || true
    else
        cp -R "${PYTHON_BASE_PREFIX}/lib" "${PYTHON_DEST}/"
        cp -R "${PYTHON_BASE_PREFIX}/bin" "${PYTHON_DEST}/"
        cp -R "${PYTHON_BASE_PREFIX}/include" "${PYTHON_DEST}/" 2>/dev/null || true
        chmod -R u+rw "${PYTHON_DEST}" 2>/dev/null || true
    fi
    
    # Remove problematic symlinks that were copied from source Python
    # These are framework-level symlinks that don't belong in version-specific directory
    log_info "Removing broken symlinks from copied Python..."
    if [ -L "${PYTHON_DEST}/bin/bin" ]; then
        rm -f "${PYTHON_DEST}/bin/bin"
        log_info "  Removed ${PYTHON_DEST}/bin/bin"
    fi
    if [ -L "${PYTHON_DEST}/lib/lib" ]; then
        rm -f "${PYTHON_DEST}/lib/lib"
        log_info "  Removed ${PYTHON_DEST}/lib/lib"
    fi
    if [ -L "${PYTHON_DEST}/${PYTHON_VERSION}" ]; then
        rm -f "${PYTHON_DEST}/${PYTHON_VERSION}"
        log_info "  Removed ${PYTHON_DEST}/${PYTHON_VERSION}"
    fi
    
    # Add sitecustomize.py to disable user site-packages
    log_info "Adding sitecustomize.py to disable user site-packages..."
    SITECUSTOMIZE_SOURCE="${SCRIPT_DIR}/resources/sitecustomize.py"
    SITECUSTOMIZE_DEST="${PYTHON_DEST}/lib/python${PYTHON_VERSION}/sitecustomize.py"
    if [ -f "${SITECUSTOMIZE_SOURCE}" ]; then
        cp "${SITECUSTOMIZE_SOURCE}" "${SITECUSTOMIZE_DEST}"
        log_info "  Installed sitecustomize.py"
    else
        log_error "sitecustomize.py not found at ${SITECUSTOMIZE_SOURCE}"
        exit 1
    fi
    
    # Create python3 symlink in bin directory
    log_info "Creating python3 symlink in bin directory..."
    if [ -f "${PYTHON_DEST}/bin/python${PYTHON_VERSION}" ]; then
        (cd "${PYTHON_DEST}/bin" && ln -sf "python${PYTHON_VERSION}" python3)
        log_info "  Created python3 -> python${PYTHON_VERSION}"
    fi
    
    # Create version symlinks
    log_info "Creating framework-level symlinks..."
    VERSIONS_DIR="${FRAMEWORKS_DIR}/Python.framework/Versions"
    FRAMEWORK_DIR="${FRAMEWORKS_DIR}/Python.framework"
    
    # Create Current -> 3.12 symlink
    (cd "${VERSIONS_DIR}" && ln -sfn "${PYTHON_VERSION}" Current)
    log_info "  Created ${VERSIONS_DIR}/Current -> ${PYTHON_VERSION}"
    
    # Create framework-level bin and lib symlinks (use -n to avoid following symlinks)
    (cd "${FRAMEWORK_DIR}" && ln -sfn "Versions/Current/bin" bin)
    (cd "${FRAMEWORK_DIR}" && ln -sfn "Versions/Current/lib" lib)
    log_info "  Created ${FRAMEWORK_DIR}/bin -> Versions/Current/bin"
    log_info "  Created ${FRAMEWORK_DIR}/lib -> Versions/Current/lib"
    
    log_success "Python embedded successfully"
    
    # Remove unnecessary files from embedded Python
    log_info "Removing unnecessary files from embedded Python..."
    
    # Remove development tools from bin/
    for tool in idle3.13 pip3 pip3.13 pydoc3.13 python3.13-config; do
        if [ -f "${PYTHON_DEST}/bin/${tool}" ]; then
            rm -f "${PYTHON_DEST}/bin/${tool}"
            log_info "  Removed bin/${tool}"
        fi
    done
    
    # Remove pkg-config files
    if [ -d "${PYTHON_DEST}/lib/pkgconfig" ]; then
        rm -rf "${PYTHON_DEST}/lib/pkgconfig"
        log_info "  Removed lib/pkgconfig/"
    fi
    
    # Remove Python test suite (saves ~68MB)
    if [ -d "${PYTHON_DEST}/lib/python${PYTHON_VERSION}/test" ]; then
        rm -rf "${PYTHON_DEST}/lib/python${PYTHON_VERSION}/test"
        log_info "  Removed lib/python${PYTHON_VERSION}/test/"
    fi
    
    log_success "Unnecessary files removed"
    
    # Pre-compile Python standard library
    log_info "Pre-compiling Python standard library..."
    STDLIB_PATH="${PYTHON_DEST}/lib/python${PYTHON_VERSION}"
    if [ -d "${STDLIB_PATH}" ]; then
        # Use the bundled Python to compile the standard library
        # This ensures compatibility and uses the correct Python version
        BUNDLE_PYTHON="${PYTHON_DEST}/bin/python3"
        if [ -f "${BUNDLE_PYTHON}" ]; then
            # Compile all .py files in the standard library
            # -q: quiet mode (only show errors)
            # -f: force recompilation even if .pyc files exist
            if "${BUNDLE_PYTHON}" -m compileall -q -f "${STDLIB_PATH}"; then
                log_info "  Compiled Python standard library"
                
                # Count compiled files for verification
                PYC_COUNT=$(find "${STDLIB_PATH}" -name "*.pyc" | wc -l | tr -d ' ')
                PY_COUNT=$(find "${STDLIB_PATH}" -name "*.py" | wc -l | tr -d ' ')
                log_info "  Created ${PYC_COUNT} .pyc files from ${PY_COUNT} .py files"
            else
                log_warning "Standard library compilation had errors (non-critical)"
            fi
        else
            log_warning "Bundled Python not found, skipping standard library pre-compilation"
        fi
    else
        log_warning "Standard library path not found: ${STDLIB_PATH}"
    fi
    
    # Update install names for Python shared library
    log_info "Updating install names to use embedded Python..."
    # Find the Python shared library
    PYTHON_LIB=$(find "${PYTHON_DEST}/lib" -name "libpython${PYTHON_VERSION}*.dylib" -type f | head -1)
    if [ -n "${PYTHON_LIB}" ]; then
        PYTHON_LIB_NAME=$(basename "${PYTHON_LIB}")
        
        # Update the TFM executable to use bundled Python library
        install_name_tool -change \
            "${PYTHON_BASE_PREFIX}/lib/${PYTHON_LIB_NAME}" \
            "@executable_path/../Frameworks/Python.framework/Versions/${PYTHON_VERSION}/lib/${PYTHON_LIB_NAME}" \
            "${MACOS_DIR}/${APP_NAME}" 2>/dev/null || true
        
        # Update the Python library's own install name (id)
        install_name_tool -id \
            "@executable_path/../Frameworks/Python.framework/Versions/${PYTHON_VERSION}/lib/${PYTHON_LIB_NAME}" \
            "${PYTHON_LIB}"
        log_info "  Updated Python library install name"
        
        # Check for and update any external library dependencies
        EXTERNAL_LIBS=$(otool -L "${PYTHON_LIB}" | grep -E "/(opt|usr/local|Users)" | grep -v "/usr/lib" | grep -v "/System" | awk '{print $1}')
        if [ -n "${EXTERNAL_LIBS}" ]; then
            log_info "  Warning: Python library has external dependencies:"
            echo "${EXTERNAL_LIBS}" | while read -r lib; do
                log_info "    - ${lib}"
            done
            log_info "  These libraries must be available on the target system"
        fi
    fi
fi

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
