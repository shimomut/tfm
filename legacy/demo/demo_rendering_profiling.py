#!/usr/bin/env python3
"""
Demo: Rendering Profiling

This demo demonstrates the rendering profiling feature in TFM.
It shows how rendering operations are profiled when profiling mode is enabled.

To run this demo:
    python demo/demo_rendering_profiling.py

Expected behavior:
1. TFM launches in profiling mode
2. Rendering operations are profiled
3. Profile files are written to profiling_output/ directory
4. Profile file locations are printed to stdout
5. FPS is printed every 5 seconds

Profile files can be analyzed with:
    python -m pstats profiling_output/render_profile_*.prof
    
Or visualized with snakeviz:
    pip install snakeviz
    snakeviz profiling_output/render_profile_*.prof
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def main():
    print("=" * 70)
    print("Demo: Rendering Profiling")
    print("=" * 70)
    print()
    print("This demo demonstrates rendering profiling in TFM.")
    print()
    print("What to expect:")
    print("1. TFM will launch in profiling mode")
    print("2. Rendering operations will be profiled")
    print("3. Profile files will be written to profiling_output/")
    print("4. Profile file locations will be printed")
    print("5. FPS will be printed every 5 seconds")
    print()
    print("Instructions:")
    print("- Navigate around the file manager")
    print("- Each frame render will be profiled")
    print("- Profile files will accumulate in profiling_output/")
    print("- Press 'q' to quit when done")
    print()
    print("After quitting, you can analyze the profile files:")
    print("  python -m pstats profiling_output/render_profile_*.prof")
    print()
    
    input("Press Enter to start TFM with profiling enabled...")
    print()
    
    # Clean up old profiling output for demo
    profiling_dir = Path("profiling_output")
    if profiling_dir.exists():
        print("Cleaning up old profiling output...")
        for file in profiling_dir.glob("render_profile_*.prof"):
            file.unlink()
        print()
    
    # Launch TFM with profiling enabled
    print("Launching TFM with --profile flag...")
    print("(Profile files will be written to profiling_output/)")
    print()
    
    try:
        # Run TFM with profiling
        result = subprocess.run(
            [sys.executable, "tfm.py", "--profile"],
            cwd=Path(__file__).parent.parent
        )
        
        print()
        print("=" * 70)
        print("Demo Complete")
        print("=" * 70)
        print()
        
        # Show generated profile files
        if profiling_dir.exists():
            render_profiles = list(profiling_dir.glob("render_profile_*.prof"))
            if render_profiles:
                print(f"Generated {len(render_profiles)} rendering profile files:")
                for profile in sorted(render_profiles)[:5]:  # Show first 5
                    print(f"  - {profile}")
                if len(render_profiles) > 5:
                    print(f"  ... and {len(render_profiles) - 5} more")
                print()
                print("To analyze a profile file:")
                print(f"  python -m pstats {render_profiles[0]}")
                print()
                print("Or visualize with snakeviz:")
                print(f"  snakeviz {render_profiles[0]}")
            else:
                print("No rendering profile files were generated.")
                print("(This is normal if you quit immediately)")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError running demo: {e}")

if __name__ == "__main__":
    main()
