"""
TFM (Terminal File Manager) - Source Package

This package contains all the core modules for the TFM file manager.
"""

import sys
import os

# Version information
__version__ = "0.98"
__author__ = "Tomonori Shimomura"

# Add the package directory to sys.path to support relative imports
# This allows modules to import each other without the 'tfm.' prefix
_package_dir = os.path.dirname(__file__)
if _package_dir not in sys.path:
    sys.path.insert(0, _package_dir)