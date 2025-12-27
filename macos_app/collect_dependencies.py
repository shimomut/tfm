#!/usr/bin/env python3
"""
TFM Dependency Collection Script

This script collects Python dependencies from requirements.txt and copies them
to the app bundle's python_packages directory with proper structure.

It handles:
- Reading requirements.txt
- Locating site-packages for each dependency
- Copying packages with proper structure
- Handling package metadata (.dist-info directories)
- Verifying PyObjC frameworks are included
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


def log_info(message):
    """Print info message."""
    print(f"[INFO] {message}")


def log_error(message):
    """Print error message."""
    print(f"[ERROR] {message}", file=sys.stderr)


def log_success(message):
    """Print success message."""
    print(f"[SUCCESS] {message}")


def log_warning(message):
    """Print warning message."""
    print(f"[WARNING] {message}")


def get_site_packages_dir():
    """
    Get the site-packages directory for the current Python environment.
    
    Returns:
        Path: Path to site-packages directory
    """
    # Try to get from sys.path
    for path in sys.path:
        if 'site-packages' in path and os.path.isdir(path):
            return Path(path)
    
    # Fallback: use sysconfig
    import sysconfig
    return Path(sysconfig.get_path('purelib'))


def read_requirements(requirements_file):
    """
    Read requirements.txt and extract package names.
    
    Args:
        requirements_file: Path to requirements.txt
        
    Returns:
        list: List of package names
    """
    packages = []
    
    if not os.path.exists(requirements_file):
        log_error(f"Requirements file not found: {requirements_file}")
        return packages
    
    log_info(f"Reading requirements from: {requirements_file}")
    
    with open(requirements_file, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Extract package name (handle version specifiers)
            package_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
            
            if package_name:
                packages.append(package_name)
    
    log_info(f"Found {len(packages)} packages in requirements.txt")
    return packages


def normalize_package_name(name):
    """
    Normalize package name for filesystem lookup.
    PyPI package names can use hyphens, but installed packages use underscores.
    
    Args:
        name: Package name from requirements.txt
        
    Returns:
        str: Normalized package name
    """
    return name.replace('-', '_').lower()


def find_package_in_site_packages(package_name, site_packages_dir):
    """
    Find a package in site-packages directory.
    
    Args:
        package_name: Name of the package
        site_packages_dir: Path to site-packages
        
    Returns:
        tuple: (package_path, dist_info_path) or (None, None) if not found
    """
    site_packages = Path(site_packages_dir)
    
    # Try exact match first
    package_path = site_packages / package_name
    if package_path.exists():
        # Find corresponding .dist-info directory
        dist_info_pattern = f"{package_name}-*.dist-info"
        dist_info_dirs = list(site_packages.glob(dist_info_pattern))
        dist_info_path = dist_info_dirs[0] if dist_info_dirs else None
        return package_path, dist_info_path
    
    # Try normalized name (replace hyphens with underscores)
    normalized = normalize_package_name(package_name)
    package_path = site_packages / normalized
    if package_path.exists():
        # Try to find dist-info with original name or normalized name
        dist_info_pattern = f"{package_name}-*.dist-info"
        dist_info_dirs = list(site_packages.glob(dist_info_pattern))
        if not dist_info_dirs:
            dist_info_pattern = f"{normalized}-*.dist-info"
            dist_info_dirs = list(site_packages.glob(dist_info_pattern))
        dist_info_path = dist_info_dirs[0] if dist_info_dirs else None
        return package_path, dist_info_path
    
    # Special case: python-dateutil is installed as dateutil
    if package_name == 'python-dateutil':
        package_path = site_packages / 'dateutil'
        if package_path.exists():
            dist_info_pattern = f"python_dateutil-*.dist-info"
            dist_info_dirs = list(site_packages.glob(dist_info_pattern))
            dist_info_path = dist_info_dirs[0] if dist_info_dirs else None
            return package_path, dist_info_path
    
    # Try as a single-file module
    module_file = site_packages / f"{package_name}.py"
    if module_file.exists():
        dist_info_pattern = f"{package_name}-*.dist-info"
        dist_info_dirs = list(site_packages.glob(dist_info_pattern))
        dist_info_path = dist_info_dirs[0] if dist_info_dirs else None
        return module_file, dist_info_path
    
    # Try single-file module with normalized name
    module_file = site_packages / f"{normalized}.py"
    if module_file.exists():
        dist_info_pattern = f"{normalized}-*.dist-info"
        dist_info_dirs = list(site_packages.glob(dist_info_pattern))
        dist_info_path = dist_info_dirs[0] if dist_info_dirs else None
        return module_file, dist_info_path
    
    return None, None


def copy_package(package_name, site_packages_dir, dest_dir):
    """
    Copy a package and its metadata to the destination directory.
    
    Args:
        package_name: Name of the package
        site_packages_dir: Path to site-packages
        dest_dir: Destination directory
        
    Returns:
        bool: True if successful, False otherwise
    """
    package_path, dist_info_path = find_package_in_site_packages(package_name, site_packages_dir)
    
    if not package_path:
        log_error(f"Package not found: {package_name}")
        return False
    
    dest_dir = Path(dest_dir)
    
    # Copy package
    dest_package = dest_dir / package_path.name
    if package_path.is_dir():
        log_info(f"Copying package directory: {package_path.name}")
        if dest_package.exists():
            shutil.rmtree(dest_package)
        shutil.copytree(package_path, dest_package)
    else:
        log_info(f"Copying package file: {package_path.name}")
        shutil.copy2(package_path, dest_package)
    
    # Copy .dist-info if it exists
    if dist_info_path and dist_info_path.exists():
        dest_dist_info = dest_dir / dist_info_path.name
        log_info(f"Copying metadata: {dist_info_path.name}")
        if dest_dist_info.exists():
            shutil.rmtree(dest_dist_info)
        shutil.copytree(dist_info_path, dest_dist_info)
    
    return True


def verify_pyobjc_frameworks(site_packages_dir, dest_dir):
    """
    Verify that PyObjC frameworks are included.
    
    Args:
        site_packages_dir: Path to site-packages
        dest_dir: Destination directory
        
    Returns:
        bool: True if all required frameworks are present
    """
    log_info("Verifying PyObjC frameworks...")
    
    required_modules = ['objc', 'Cocoa', 'AppKit']
    missing_modules = []
    
    for module_name in required_modules:
        # Check if module exists in destination
        dest_path = Path(dest_dir) / module_name
        dest_file = Path(dest_dir) / f"{module_name}.py"
        
        if not dest_path.exists() and not dest_file.exists():
            log_warning(f"PyObjC module not found in destination: {module_name}")
            
            # Try to copy from site-packages
            package_path, dist_info_path = find_package_in_site_packages(module_name, site_packages_dir)
            
            if package_path:
                log_info(f"Adding missing PyObjC module: {module_name}")
                if not copy_package(module_name, site_packages_dir, dest_dir):
                    missing_modules.append(module_name)
            else:
                missing_modules.append(module_name)
    
    if missing_modules:
        log_error(f"Missing PyObjC modules: {', '.join(missing_modules)}")
        log_error("Please install PyObjC: pip install pyobjc-framework-Cocoa")
        return False
    
    log_success("All required PyObjC frameworks are present")
    return True


def get_package_dependencies(package_name):
    """
    Get dependencies for a package using pip show.
    
    Args:
        package_name: Name of the package
        
    Returns:
        list: List of dependency package names
    """
    try:
        result = subprocess.run(
            ['pip', 'show', package_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        for line in result.stdout.split('\n'):
            if line.startswith('Requires:'):
                deps_str = line.split(':', 1)[1].strip()
                if deps_str:
                    return [dep.strip() for dep in deps_str.split(',')]
                return []
        
        return []
    except subprocess.CalledProcessError:
        return []


def collect_all_dependencies(packages, site_packages_dir, dest_dir):
    """
    Recursively collect all dependencies for the given packages.
    
    Args:
        packages: List of package names
        site_packages_dir: Path to site-packages
        dest_dir: Destination directory
        
    Returns:
        tuple: (success_count, failed_packages)
    """
    processed = set()
    to_process = list(packages)
    success_count = 0
    failed_packages = []
    
    while to_process:
        package_name = to_process.pop(0)
        
        # Skip if already processed
        if package_name in processed:
            continue
        
        processed.add(package_name)
        
        log_info(f"Processing package: {package_name}")
        
        # Copy the package
        if copy_package(package_name, site_packages_dir, dest_dir):
            success_count += 1
            
            # Get dependencies and add to queue
            deps = get_package_dependencies(package_name)
            if deps:
                log_info(f"  Found dependencies: {', '.join(deps)}")
                for dep in deps:
                    if dep not in processed:
                        to_process.append(dep)
        else:
            failed_packages.append(package_name)
    
    return success_count, failed_packages


def collect_dependencies(requirements_file, dest_dir):
    """
    Main function to collect all dependencies.
    
    Args:
        requirements_file: Path to requirements.txt
        dest_dir: Destination directory for packages
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get site-packages directory
    site_packages_dir = get_site_packages_dir()
    log_info(f"Using site-packages: {site_packages_dir}")
    
    # Create destination directory
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Read requirements
    packages = read_requirements(requirements_file)
    
    if not packages:
        log_warning("No packages found in requirements.txt")
        return True
    
    # Collect packages and their dependencies
    log_info(f"Collecting {len(packages)} packages and their dependencies...")
    success_count, failed_packages = collect_all_dependencies(
        packages, site_packages_dir, dest_dir
    )
    
    # Report results
    log_info(f"Successfully copied {success_count} packages (including dependencies)")
    
    if failed_packages:
        log_error(f"Failed to copy packages: {', '.join(failed_packages)}")
        log_error("Please ensure all dependencies are installed: pip install -r requirements.txt")
        return False
    
    # Verify PyObjC frameworks
    if not verify_pyobjc_frameworks(site_packages_dir, dest_dir):
        return False
    
    log_success("All dependencies collected successfully")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Collect Python dependencies for TFM macOS app bundle'
    )
    parser.add_argument(
        '--requirements',
        default='requirements.txt',
        help='Path to requirements.txt file'
    )
    parser.add_argument(
        '--dest',
        required=True,
        help='Destination directory for packages'
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    requirements_file = os.path.abspath(args.requirements)
    dest_dir = os.path.abspath(args.dest)
    
    log_info("TFM Dependency Collection Script")
    log_info(f"Requirements file: {requirements_file}")
    log_info(f"Destination directory: {dest_dir}")
    log_info("")
    
    # Collect dependencies
    if collect_dependencies(requirements_file, dest_dir):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
