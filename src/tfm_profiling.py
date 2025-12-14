#!/usr/bin/env python3
"""
TFM Profiling Module - Performance profiling infrastructure for TFM

This module provides profiling capabilities for measuring and analyzing
TFM performance, including FPS tracking and cProfile integration.
"""

import os
import sys
import time
import cProfile
import pstats
import threading
import tempfile
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Callable, Any, Optional


class FPSTracker:
    """Track frame timing and calculate frames per second"""
    
    def __init__(self, window_size: int = 60, print_interval: float = 5.0):
        """
        Initialize FPS tracker
        
        Args:
            window_size: Number of recent frames to track for FPS calculation
            print_interval: Interval in seconds between FPS prints
        """
        self.frame_times = deque(maxlen=window_size)
        self.last_print_time = time.time()
        self.print_interval = print_interval
    
    def record_frame(self) -> None:
        """Record current frame timestamp"""
        self.frame_times.append(time.time())
    
    def calculate_fps(self) -> float:
        """
        Calculate FPS from recent frame times
        
        Returns:
            Current FPS, or 0.0 if insufficient data
        """
        if len(self.frame_times) < 2:
            return 0.0
        
        # Calculate time span of recent frames
        time_span = self.frame_times[-1] - self.frame_times[0]
        
        # FPS = number of frames / time span
        if time_span > 0:
            return (len(self.frame_times) - 1) / time_span
        return 0.0
    
    def should_print(self) -> bool:
        """Check if print interval has elapsed"""
        current_time = time.time()
        if current_time - self.last_print_time >= self.print_interval:
            self.last_print_time = current_time
            return True
        return False
    
    def format_output(self) -> str:
        """
        Format FPS output with timestamp
        
        Returns:
            Formatted string with timestamp and FPS
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fps = self.calculate_fps()
        return f"[{timestamp}] FPS: {fps:.2f}"


class ProfileWriter:
    """Write cProfile data to files with proper naming"""
    
    def __init__(self, output_dir: str = "profiling_output"):
        """
        Initialize profile writer
        
        Args:
            output_dir: Directory for profile output files
        """
        self.output_dir = output_dir
        self.fallback_dir = None
        self.using_fallback = False
    
    def ensure_output_dir(self) -> bool:
        """
        Create output directory if it doesn't exist
        
        Returns:
            True if directory is ready, False if fallback is needed
        """
        # If already using fallback, skip primary directory check
        if self.using_fallback and self.fallback_dir:
            return True
        
        try:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            
            # Test write permissions by creating README
            readme_path = Path(self.output_dir) / "README.txt"
            if not readme_path.exists():
                self._write_readme(readme_path)
            
            return True
            
        except PermissionError as e:
            print(f"Error: Permission denied creating profiling directory '{self.output_dir}': {e}", 
                  file=sys.stderr)
            return self._setup_fallback_dir()
            
        except OSError as e:
            # Handle disk full, invalid path, etc.
            print(f"Error: Could not create profiling output directory '{self.output_dir}': {e}", 
                  file=sys.stderr)
            return self._setup_fallback_dir()
    
    def _setup_fallback_dir(self) -> bool:
        """
        Set up fallback directory in temp location
        
        Returns:
            True if fallback directory is ready, False if all attempts failed
        """
        if self.using_fallback:
            # Already tried fallback, don't retry
            return False
        
        try:
            # Create fallback directory in system temp
            self.fallback_dir = tempfile.mkdtemp(prefix="tfm_profiling_")
            self.using_fallback = True
            
            print(f"Warning: Using fallback profiling directory: {self.fallback_dir}", 
                  file=sys.stderr)
            
            # Try to create README in fallback location
            readme_path = Path(self.fallback_dir) / "README.txt"
            self._write_readme(readme_path)
            
            return True
            
        except (PermissionError, OSError) as e:
            print(f"Error: Could not create fallback profiling directory: {e}", 
                  file=sys.stderr)
            print("Warning: Profiling will continue but profile files cannot be saved", 
                  file=sys.stderr)
            return False
    
    def _write_readme(self, readme_path: Path) -> None:
        """
        Write README file to profiling directory
        
        Args:
            readme_path: Path where README should be written
        """
        try:
            with open(readme_path, 'w') as f:
                f.write("TFM Profiling Output\n")
                f.write("=" * 50 + "\n\n")
                f.write("This directory contains profiling data from TFM.\n\n")
                f.write("Analyzing Profile Files:\n")
                f.write("-" * 50 + "\n\n")
                f.write("Using pstats (built-in):\n")
                f.write("  python -m pstats <profile_file>.prof\n")
                f.write("  Then use commands like:\n")
                f.write("    sort cumulative\n")
                f.write("    stats 20\n")
                f.write("    callers function_name\n\n")
                f.write("Using snakeviz (visual):\n")
                f.write("  pip install snakeviz\n")
                f.write("  snakeviz <profile_file>.prof\n\n")
                f.write("Profile File Naming:\n")
                f.write("-" * 50 + "\n")
                f.write("  key_profile_YYYYMMDD_HHMMSS_microseconds.prof\n")
                f.write("  render_profile_YYYYMMDD_HHMMSS_microseconds.prof\n\n")
        except (PermissionError, OSError) as e:
            # README creation is not critical, just log and continue
            print(f"Warning: Could not create README file: {e}", file=sys.stderr)
    
    def generate_filename(self, operation_type: str) -> str:
        """
        Generate timestamped filename for profile
        
        Args:
            operation_type: Type of operation (e.g., 'key', 'render')
            
        Returns:
            Generated filename with timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"{operation_type}_profile_{timestamp}.prof"
    
    def write_profile(self, profile_data: cProfile.Profile, operation_type: str) -> str:
        """
        Write profile data to file with error handling and fallback
        
        Args:
            profile_data: cProfile.Profile object with collected data
            operation_type: Type of operation being profiled
            
        Returns:
            Path to written profile file, or empty string if write failed
        """
        # Ensure output directory exists (may switch to fallback)
        if not self.ensure_output_dir():
            # Both primary and fallback failed
            return ""
        
        # Determine which directory to use
        target_dir = self.fallback_dir if self.using_fallback else self.output_dir
        filename = self.generate_filename(operation_type)
        filepath = Path(target_dir) / filename
        
        try:
            profile_data.dump_stats(str(filepath))
            return str(filepath)
            
        except PermissionError as e:
            print(f"Error: Permission denied writing profile file '{filepath}': {e}", 
                  file=sys.stderr)
            
            # Try fallback if not already using it
            if not self.using_fallback:
                if self._setup_fallback_dir():
                    # Retry with fallback directory
                    return self._write_to_fallback(profile_data, operation_type)
            return ""
            
        except OSError as e:
            # Handle disk full, I/O errors, etc.
            error_msg = str(e).lower()
            if "no space" in error_msg or "disk full" in error_msg:
                print(f"Error: Disk full - cannot write profile file: {e}", 
                      file=sys.stderr)
            else:
                print(f"Error: Could not write profile file '{filepath}': {e}", 
                      file=sys.stderr)
            
            # Try fallback if not already using it
            if not self.using_fallback:
                if self._setup_fallback_dir():
                    # Retry with fallback directory
                    return self._write_to_fallback(profile_data, operation_type)
            return ""
    
    def _write_to_fallback(self, profile_data: cProfile.Profile, operation_type: str) -> str:
        """
        Write profile to fallback directory
        
        Args:
            profile_data: cProfile.Profile object with collected data
            operation_type: Type of operation being profiled
            
        Returns:
            Path to written profile file, or empty string if write failed
        """
        if not self.fallback_dir:
            return ""
        
        filename = self.generate_filename(operation_type)
        filepath = Path(self.fallback_dir) / filename
        
        try:
            profile_data.dump_stats(str(filepath))
            return str(filepath)
        except (PermissionError, OSError) as e:
            print(f"Error: Could not write to fallback directory: {e}", 
                  file=sys.stderr)
            return ""


class ProfilingManager:
    """Central coordinator for all profiling activities"""
    
    def __init__(self, enabled: bool = False, output_dir: str = "profiling_output",
                 render_profile_interval: int = 100):
        """
        Initialize profiling manager
        
        Args:
            enabled: Whether profiling is active
            output_dir: Directory for profiling output
            render_profile_interval: Profile every Nth render call (0 = profile all)
        """
        self.enabled = enabled
        self.output_dir = output_dir
        self.render_profile_interval = render_profile_interval
        
        if self.enabled:
            self.fps_tracker = FPSTracker()
            self.profile_writer = ProfileWriter(output_dir)
            self.key_profile_count = 0
            self.render_profile_count = 0
            self.render_call_count = 0
        else:
            self.fps_tracker = None
            self.profile_writer = None
            self.key_profile_count = 0
            self.render_profile_count = 0
            self.render_call_count = 0
    
    def start_frame(self) -> None:
        """Mark the start of a new frame for FPS tracking"""
        # Optimization: Single check for enabled state
        if not self.enabled:
            return
        self.fps_tracker.record_frame()
    
    def end_frame(self) -> None:
        """Mark the end of a frame and update FPS"""
        # Currently no action needed at frame end
        # FPS is calculated from frame start times
        pass
    
    def should_print_fps(self) -> bool:
        """Check if 5 seconds have elapsed since last FPS print"""
        # Optimization: Early return for disabled state
        if not self.enabled:
            return False
        return self.fps_tracker.should_print()
    
    def print_fps(self) -> None:
        """Print current FPS to stdout with timestamp"""
        # Optimization: Early return for disabled state
        if not self.enabled:
            return
        try:
            output = self.fps_tracker.format_output()
            print(output)
        except Exception as e:
            # Handle any unexpected errors in FPS calculation/formatting
            print(f"Warning: Error printing FPS: {e}", file=sys.stderr)
    
    def profile_key_handling(self, func: Callable, *args, **kwargs) -> Any:
        """
        Profile a key handling function and save results
        
        Args:
            func: Function to profile
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Result of function call
        """
        # Optimization: Early return for disabled state (zero overhead)
        if not self.enabled:
            return func(*args, **kwargs)
        
        try:
            profiler = cProfile.Profile()
            profiler.enable()
            
            try:
                result = func(*args, **kwargs)
            finally:
                profiler.disable()
                
                # Optimization: Write profile asynchronously to avoid blocking
                self._write_profile_async(profiler, "key")
            
            return result
        except Exception as e:
            # If profiling fails, still execute the function without profiling
            print(f"Warning: Key profiling failed, continuing without profiling: {e}", 
                  file=sys.stderr)
            return func(*args, **kwargs)
    
    def profile_rendering(self, func: Callable, *args, **kwargs) -> Any:
        """
        Profile a rendering function and save results
        
        Optimization: Only profiles every Nth render call to reduce overhead
        
        Args:
            func: Function to profile
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Result of function call
        """
        # Optimization: Early return for disabled state (zero overhead)
        if not self.enabled:
            return func(*args, **kwargs)
        
        # Optimization: Conditional profiling - only profile every Nth frame
        self.render_call_count += 1
        should_profile = (self.render_profile_interval == 0 or 
                         self.render_call_count % self.render_profile_interval == 0)
        
        if not should_profile:
            return func(*args, **kwargs)
        
        try:
            profiler = cProfile.Profile()
            profiler.enable()
            
            try:
                result = func(*args, **kwargs)
            finally:
                profiler.disable()
                
                # Optimization: Write profile asynchronously to avoid blocking
                self._write_profile_async(profiler, "render")
            
            return result
        except Exception as e:
            # If profiling fails, still execute the function without profiling
            print(f"Warning: Render profiling failed, continuing without profiling: {e}", 
                  file=sys.stderr)
            return func(*args, **kwargs)
    
    def get_output_dir(self) -> str:
        """Get the profiling output directory path"""
        return self.output_dir
    
    def _write_profile_async(self, profiler: cProfile.Profile, operation_type: str) -> None:
        """
        Write profile data asynchronously to avoid blocking main loop
        
        Optimization: Uses background thread for file I/O
        
        Args:
            profiler: cProfile.Profile object with collected data
            operation_type: Type of operation being profiled
        """
        def write_in_background():
            try:
                filepath = self.profile_writer.write_profile(profiler, operation_type)
                if filepath:
                    if operation_type == "key":
                        self.key_profile_count += 1
                    else:
                        self.render_profile_count += 1
                    print(f"{operation_type.capitalize()} profile written to: {filepath}")
                else:
                    # write_profile returns empty string on failure
                    # Error message already printed by write_profile
                    pass
            except Exception as e:
                # Catch any unexpected exceptions to prevent thread crashes
                print(f"Error: Unexpected error writing {operation_type} profile: {e}", 
                      file=sys.stderr)
        
        try:
            # Start background thread for file writing
            thread = threading.Thread(target=write_in_background, daemon=True)
            thread.start()
        except Exception as e:
            # Handle thread creation failures
            print(f"Error: Could not create background thread for profiling: {e}", 
                  file=sys.stderr)
