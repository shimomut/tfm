#!/usr/bin/env python3
"""
Demo script showing the new confirmation options in TFM
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def demo_confirmation_options():
    """Demonstrate the new confirmation options"""
    print("TFM Confirmation Options Demo")
    print("=" * 40)
    
    from tfm_config import get_config
    
    config = get_config()
    
    print("\nCurrent confirmation settings:")
    print(f"  CONFIRM_DELETE: {getattr(config, 'CONFIRM_DELETE', True)}")
    print(f"  CONFIRM_QUIT: {getattr(config, 'CONFIRM_QUIT', True)}")
    print(f"  CONFIRM_COPY: {getattr(config, 'CONFIRM_COPY', True)}")
    print(f"  CONFIRM_MOVE: {getattr(config, 'CONFIRM_MOVE', True)}")
    print(f"  CONFIRM_EXTRACT_ARCHIVE: {getattr(config, 'CONFIRM_EXTRACT_ARCHIVE', True)}")
    
    print("\nNew confirmation options added:")
    print("  • CONFIRM_COPY - Shows confirmation before copying files")
    print("  • CONFIRM_MOVE - Shows confirmation before moving files")
    print("  • CONFIRM_EXTRACT_ARCHIVE - Shows confirmation before extracting archives")
    
    print("\nTo customize these settings, add them to your ~/.tfm/config.py:")
    print("""
    class Config:
        # Disable copy confirmation
        CONFIRM_COPY = False
        
        # Keep move confirmation enabled
        CONFIRM_MOVE = True
        
        # Disable extract confirmation
        CONFIRM_EXTRACT_ARCHIVE = False
    """)
    
    print("\nThese confirmations work just like the existing CONFIRM_DELETE and CONFIRM_QUIT options.")

if __name__ == '__main__':
    demo_confirmation_options()