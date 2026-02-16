#!/usr/bin/env python3
"""Demo: Reveal in OS feature.

This demo demonstrates the reveal in OS action (Alt+Enter).
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src and ttk to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'ttk'))

from tfm_main import FileManager


def create_demo_structure():
    """Create a demo directory structure for testing."""
    temp_dir = Path(tempfile.mkdtemp(prefix='tfm_reveal_demo_'))
    
    # Create nested directory structure
    (temp_dir / 'documents').mkdir()
    (temp_dir / 'documents' / 'work').mkdir()
    (temp_dir / 'documents' / 'personal').mkdir()
    (temp_dir / 'images').mkdir()
    (temp_dir / 'images' / 'photos').mkdir()
    
    # Create various files
    (temp_dir / 'readme.txt').write_text('Demo file for reveal in file manager')
    (temp_dir / 'documents' / 'report.txt').write_text('Work report')
    (temp_dir / 'documents' / 'work' / 'project.txt').write_text('Project notes')
    (temp_dir / 'documents' / 'personal' / 'notes.txt').write_text('Personal notes')
    (temp_dir / 'images' / 'photo1.jpg').write_text('Image data')
    (temp_dir / 'images' / 'photos' / 'vacation.jpg').write_text('Vacation photo')
    
    return temp_dir


def main():
    """Run the demo."""
    print("Reveal in OS Demo")
    print("=" * 50)
    print()
    print("This demo shows the reveal in OS feature.")
    print()
    print("Instructions:")
    print("1. Navigate through the demo directory structure")
    print("2. Focus on any file or directory")
    print("3. Press Alt+Enter to reveal it in your file manager")
    print("4. Or use: File > Reveal in File Manager")
    print()
    print("Key Points:")
    print("- Always uses the FOCUSED item (not selection)")
    print("- Directories are revealed in their parent (not opened)")
    print("- Works on macOS (Finder), Windows (Explorer), Linux (various)")
    print()
    print("Press Enter to start...")
    input()
    
    # Create demo structure
    demo_dir = create_demo_structure()
    print(f"Created demo directory: {demo_dir}")
    print()
    
    # Launch TFM
    try:
        fm = FileManager()
        fm.left_pane['path'] = demo_dir
        fm.run()
    finally:
        # Cleanup
        import shutil
        if demo_dir.exists():
            shutil.rmtree(demo_dir)
            print(f"Cleaned up demo directory: {demo_dir}")


if __name__ == '__main__':
    main()
