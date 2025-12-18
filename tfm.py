#!/usr/bin/env python3
"""
TFM (Terminal File Manager) - Development Wrapper

This is a thin wrapper for development use only.
For installed package, use: tfm command (which calls tfm_main.cli_main())
"""

import sys
from pathlib import Path

# Setup module path for development environment
def setup_module_path():
    """Setup module path - add src directory to Python path"""
    current_dir = Path(__file__).parent
    src_dir = current_dir / 'src'
    
    # Add src directory to path for development
    sys.path.insert(0, str(src_dir))
    return str(src_dir)

# Setup the module path
module_path = setup_module_path()

def main():
    """Development entry point - delegates to tfm_main.cli_main()"""
    try:
        from tfm_main import cli_main
        cli_main()
    except ImportError as e:
        print(f"Error importing TFM modules: {e}", file=sys.stderr)
        print("Make sure you're running from the TFM root directory", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()