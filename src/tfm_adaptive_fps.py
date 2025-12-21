"""
Adaptive FPS Manager for TFM

Dynamically adjusts frame rate based on activity to reduce CPU usage during idle periods.
Transitions from 60 FPS (active) to 1 FPS (idle) with smooth degradation.
"""

import time


class AdaptiveFPSManager:
    """
    Manages adaptive frame rate to optimize CPU usage during idle periods.
    
    The manager tracks activity and gradually reduces FPS from 60 to 1 when idle,
    then immediately restores 60 FPS when activity resumes.
    
    FPS Levels:
    - 60 FPS: Active (events or rendering changes)
    - 30 FPS: Light idle (0.5s without activity)
    - 15 FPS: Moderate idle (2s without activity)
    - 5 FPS: Heavy idle (5s without activity)
    - 1 FPS: Deep idle (10s without activity)
    """
    
    # FPS levels and their corresponding timeouts in milliseconds
    FPS_LEVELS = [
        (60, 16),   # 60 FPS = ~16ms timeout
        (30, 33),   # 30 FPS = ~33ms timeout
        (15, 66),   # 15 FPS = ~66ms timeout
        (5, 200),   # 5 FPS = 200ms timeout
        (1, 1000),  # 1 FPS = 1000ms timeout
    ]
    
    # Time thresholds (in seconds) to transition to each FPS level
    IDLE_THRESHOLDS = [
        0.0,   # 60 FPS: immediate (active)
        0.5,   # 30 FPS: after 0.5s idle
        2.0,   # 15 FPS: after 2s idle
        5.0,   # 5 FPS: after 5s idle
        10.0,  # 1 FPS: after 10s idle
    ]
    
    def __init__(self):
        """Initialize the adaptive FPS manager."""
        self.last_activity_time = time.time()
        
    def mark_activity(self):
        """
        Mark that activity has occurred (event received or rendering needed).
        
        This resets the idle timer, which will result in highest FPS level
        on the next get_timeout_ms() call.
        """
        self.last_activity_time = time.time()
    
    def _calculate_fps_level(self) -> int:
        """
        Calculate the appropriate FPS level based on idle time.
        
        Returns:
            Index into FPS_LEVELS array (0 = highest FPS)
        """
        idle_time = time.time() - self.last_activity_time
        
        # Determine appropriate FPS level based on idle time
        fps_level = 0
        for i, threshold in enumerate(self.IDLE_THRESHOLDS):
            if idle_time >= threshold:
                fps_level = i
            else:
                break
        
        return fps_level
    
    def get_timeout_ms(self) -> int:
        """
        Get the appropriate timeout for the current activity level.
        
        Returns:
            Timeout in milliseconds for run_event_loop_iteration()
        """
        fps_level = self._calculate_fps_level()
        return self.FPS_LEVELS[fps_level][1]
    
    def get_current_fps(self) -> int:
        """
        Get the current FPS level.
        
        Returns:
            Current frames per second
        """
        fps_level = self._calculate_fps_level()
        return self.FPS_LEVELS[fps_level][0]
    
    def is_idle(self) -> bool:
        """
        Check if the system is currently in idle state (below 60 FPS).
        
        Returns:
            True if FPS has been reduced due to inactivity
        """
        return self._calculate_fps_level() > 0
