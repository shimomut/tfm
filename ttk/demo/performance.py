#!/usr/bin/env python3
"""
TTK Performance Monitoring

This module provides performance monitoring capabilities for TTK applications,
tracking frame rate (FPS) and rendering time per frame.

The performance monitor can be integrated into any TTK application to provide
real-time performance metrics and help identify rendering bottlenecks.
"""

import time
from collections import deque
from typing import Optional


class PerformanceMonitor:
    """
    Performance monitoring for TTK applications.
    
    Tracks frame rate (FPS) and rendering time to help identify performance
    issues and verify that rendering backends meet performance requirements.
    """
    
    def __init__(self, history_size: int = 60):
        """
        Initialize the performance monitor.
        
        Args:
            history_size: Number of frames to keep in history for averaging
        """
        self.history_size = history_size
        self.frame_times = deque(maxlen=history_size)
        self.render_times = deque(maxlen=history_size)
        
        self.last_frame_time = None
        self.current_render_start = None
        
        self.total_frames = 0
        self.start_time = time.time()
    
    def start_frame(self):
        """Mark the start of a new frame."""
        current_time = time.time()
        
        # Calculate time since last frame
        if self.last_frame_time is not None:
            frame_time = current_time - self.last_frame_time
            self.frame_times.append(frame_time)
        
        self.last_frame_time = current_time
        self.total_frames += 1
    
    def start_render(self):
        """Mark the start of rendering operations."""
        self.current_render_start = time.time()
    
    def end_render(self):
        """Mark the end of rendering operations."""
        if self.current_render_start is not None:
            render_time = time.time() - self.current_render_start
            self.render_times.append(render_time)
            self.current_render_start = None
    
    def get_fps(self) -> float:
        """
        Get current frames per second.
        
        Returns:
            Current FPS based on recent frame times, or 0.0 if no data
        """
        if not self.frame_times:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        if avg_frame_time > 0:
            return 1.0 / avg_frame_time
        return 0.0
    
    def get_average_fps(self) -> float:
        """
        Get average FPS since monitoring started.
        
        Returns:
            Average FPS over entire monitoring period
        """
        elapsed = time.time() - self.start_time
        if elapsed > 0 and self.total_frames > 0:
            return self.total_frames / elapsed
        return 0.0
    
    def get_render_time_ms(self) -> float:
        """
        Get average rendering time in milliseconds.
        
        Returns:
            Average render time in milliseconds, or 0.0 if no data
        """
        if not self.render_times:
            return 0.0
        
        avg_render_time = sum(self.render_times) / len(self.render_times)
        return avg_render_time * 1000.0  # Convert to milliseconds
    
    def get_min_render_time_ms(self) -> float:
        """
        Get minimum rendering time in milliseconds.
        
        Returns:
            Minimum render time in milliseconds, or 0.0 if no data
        """
        if not self.render_times:
            return 0.0
        return min(self.render_times) * 1000.0
    
    def get_max_render_time_ms(self) -> float:
        """
        Get maximum rendering time in milliseconds.
        
        Returns:
            Maximum render time in milliseconds, or 0.0 if no data
        """
        if not self.render_times:
            return 0.0
        return max(self.render_times) * 1000.0
    
    def get_frame_time_ms(self) -> float:
        """
        Get average frame time in milliseconds.
        
        Returns:
            Average frame time in milliseconds, or 0.0 if no data
        """
        if not self.frame_times:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return avg_frame_time * 1000.0
    
    def get_total_frames(self) -> int:
        """
        Get total number of frames processed.
        
        Returns:
            Total frame count since monitoring started
        """
        return self.total_frames
    
    def get_uptime(self) -> float:
        """
        Get monitoring uptime in seconds.
        
        Returns:
            Time in seconds since monitoring started
        """
        return time.time() - self.start_time
    
    def reset(self):
        """Reset all performance statistics."""
        self.frame_times.clear()
        self.render_times.clear()
        self.last_frame_time = None
        self.current_render_start = None
        self.total_frames = 0
        self.start_time = time.time()
    
    def get_summary(self) -> dict:
        """
        Get a summary of all performance metrics.
        
        Returns:
            Dictionary containing all performance metrics
        """
        return {
            'fps': self.get_fps(),
            'average_fps': self.get_average_fps(),
            'render_time_ms': self.get_render_time_ms(),
            'min_render_time_ms': self.get_min_render_time_ms(),
            'max_render_time_ms': self.get_max_render_time_ms(),
            'frame_time_ms': self.get_frame_time_ms(),
            'total_frames': self.get_total_frames(),
            'uptime': self.get_uptime()
        }
