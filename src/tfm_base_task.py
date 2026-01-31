"""Abstract base class for long-running tasks with UI interaction.

This module provides the BaseTask abstract class, which serves as a framework
for implementing complex workflows that involve user interaction, background
processing, and state management.

Tasks are used to coordinate operations that require:
- Multiple user interactions (confirmations, choices, input)
- Background thread execution
- State management across multiple steps
- Cancellation support
"""

from abc import ABC, abstractmethod
from tfm_log_manager import getLogger


class BaseTask(ABC):
    """Abstract base class for long-running tasks with UI interaction.
    
    This class provides a framework for implementing complex workflows that
    involve user interaction, background processing, and state management.
    
    Subclasses must implement:
    - start(): Begin the task execution
    - cancel(): Cancel the task if possible
    - is_active(): Check if task is currently active
    - get_state(): Get current task state as string
    
    Subclasses may override:
    - on_state_enter(state): Called when entering a new state
    - on_state_exit(state): Called when exiting a state
    
    Example usage:
        class MyTask(BaseTask):
            def __init__(self, file_manager):
                super().__init__(file_manager)
                self.state = "idle"
            
            def start(self):
                self.state = "running"
                # Begin task execution
            
            def cancel(self):
                if self.is_active():
                    self.state = "idle"
            
            def is_active(self):
                return self.state != "idle"
            
            def get_state(self):
                return self.state
    """
    
    def __init__(self, file_manager, logger_name=None):
        """Initialize base task.
        
        Args:
            file_manager: Reference to FileManager for UI interactions
            logger_name: Optional custom logger name (defaults to class name if not provided)
        """
        self.file_manager = file_manager
        self.logger = getLogger(logger_name if logger_name else self.__class__.__name__)
        self._cancelled = False
    
    @abstractmethod
    def start(self):
        """Start the task execution.
        
        This method should initiate the task workflow. It will be called
        by FileManager when the task is started.
        
        Subclasses must implement this method to define how the task begins.
        """
        pass
    
    @abstractmethod
    def cancel(self):
        """Cancel the task if possible.
        
        This method should attempt to cancel the task gracefully. It may
        not be possible to cancel immediately if the task is in the middle
        of a critical operation.
        
        Subclasses must implement this method to define cancellation behavior.
        """
        pass
    
    @abstractmethod
    def is_active(self) -> bool:
        """Check if the task is currently active.
        
        Returns:
            True if task is active (not IDLE or COMPLETED), False otherwise
        
        Subclasses must implement this method to report task activity status.
        """
        pass
    
    @abstractmethod
    def get_state(self) -> str:
        """Get the current state of the task.
        
        Returns:
            String representation of current state
        
        Subclasses must implement this method to report current task state.
        """
        pass
    
    def is_cancelled(self) -> bool:
        """Check if the task has been cancelled.
        
        Returns:
            True if task has been cancelled, False otherwise
        """
        return self._cancelled
    
    def request_cancellation(self):
        """Request task cancellation.
        
        Sets the internal cancellation flag. Subclasses should check
        this flag periodically during execution and stop processing
        when cancellation is requested.
        """
        self._cancelled = True
    
    def on_state_enter(self, state):
        """Hook called when entering a new state.
        
        Subclasses can override this to perform actions when entering states.
        The default implementation does nothing.
        
        Args:
            state: The state being entered
        """
        pass
    
    def on_state_exit(self, state):
        """Hook called when exiting a state.
        
        Subclasses can override this to perform cleanup when exiting states.
        The default implementation does nothing.
        
        Args:
            state: The state being exited
        """
        pass
