# External Programs System

## Overview

The External Programs System manages the execution of external programs and subshell features in TFM. It provides a safe and configurable way to launch external editors, viewers, and shell commands from within the file manager.

## Architecture

### Core Class: ExternalProgramManager

The `ExternalProgramManager` class handles:

- **Program Execution**: Launching external programs with proper arguments
- **Subshell Management**: Opening shell sessions in current directory
- **Terminal Handling**: Managing terminal state during external execution
- **Error Handling**: Gracefully handling program failures

### Key Responsibilities

1. **Configuration**: Read external program settings from config
2. **Execution**: Launch programs with proper environment
3. **Terminal Management**: Save/restore terminal state
4. **Error Reporting**: Report execution errors to user

## Implementation Details

### Program Execution Flow

```python
# Pseudo-code for program execution
def execute_program(program, args, path):
    # Save terminal state
    save_terminal_state()
    
    try:
        # Build command
        cmd = [program] + args
        
        # Execute in subprocess
        result = subprocess.run(cmd, cwd=path)
        
        # Check result
        if result.returncode != 0:
            report_error(result)
    finally:
        # Restore terminal state
        restore_terminal_state()
```

### Terminal State Management

The system must carefully manage terminal state:

1. **Save State**: Save current terminal settings
2. **Reset Terminal**: Reset to cooked mode for external program
3. **Execute**: Run external program
4. **Restore State**: Restore TFM's raw mode settings

### Subshell Feature

The subshell feature allows users to open a shell:

- **Current Directory**: Opens in current pane's directory
- **Environment**: Inherits TFM's environment
- **Return**: Returns to TFM on shell exit
- **State Preservation**: TFM state preserved during shell session

## Configuration

External programs are configured in the config file:

```python
# Example configuration
external_programs = {
    'editor': 'vim',
    'viewer': 'less',
    'shell': '/bin/bash',
    'diff': 'vimdiff',
}
```

### Program Types

The system supports several program types:

- **Editor**: Text editor for file editing
- **Viewer**: File viewer (alternative to built-in)
- **Shell**: Shell for subshell feature
- **Diff**: Diff tool for file comparison
- **Custom**: User-defined programs

## Key Methods

### ExternalProgramManager Methods

```python
class ExternalProgramManager:
    def execute_editor(self, filepath):
        """Launch external editor for file."""
        
    def execute_viewer(self, filepath):
        """Launch external viewer for file."""
        
    def open_subshell(self, directory):
        """Open shell in specified directory."""
        
    def execute_custom(self, program, args):
        """Execute custom external program."""
        
    def get_program_path(self, program_type):
        """Get configured program path for type."""
```

### Terminal Management Methods

```python
def save_terminal_state():
    """Save current terminal settings."""
    
def restore_terminal_state():
    """Restore saved terminal settings."""
    
def reset_terminal():
    """Reset terminal to cooked mode."""
```

## Integration Points

### File Manager Integration

The external programs system integrates with file manager:

- **Edit File**: Launch editor for selected file
- **View File**: Launch viewer for selected file
- **Subshell**: Open shell in current directory
- **Custom Actions**: Execute user-defined programs

### Configuration System

Integrates with configuration system:

- **Program Paths**: Read program paths from config
- **Arguments**: Read default arguments from config
- **Environment**: Read environment variables from config

### Menu System

Integrated into menu system:

- **File Menu**: Edit, View options
- **Tools Menu**: Subshell, custom programs
- **Key Bindings**: Keyboard shortcuts for common actions

## Error Handling

The system handles various error conditions:

- **Program Not Found**: Report missing program
- **Execution Failure**: Report execution errors
- **Permission Denied**: Report permission errors
- **Terminal Errors**: Handle terminal state errors

### Error Recovery

On error, the system:

1. **Log Error**: Log error details
2. **Restore Terminal**: Ensure terminal state restored
3. **Report to User**: Show error message
4. **Continue**: Allow TFM to continue running

## Security Considerations

### Command Injection Prevention

The system prevents command injection:

- **No Shell Expansion**: Use subprocess without shell
- **Argument Escaping**: Properly escape arguments
- **Path Validation**: Validate file paths

### Program Validation

Before execution:

- **Existence Check**: Verify program exists
- **Permission Check**: Verify program is executable
- **Path Sanitization**: Sanitize file paths

## Platform Considerations

### Unix/Linux/macOS

- **Terminal Control**: Use termios for terminal control
- **Signal Handling**: Handle SIGTSTP, SIGCONT
- **Process Groups**: Manage process groups properly

### Windows

- **Console API**: Use Windows Console API
- **Process Creation**: Use Windows process creation
- **Path Handling**: Handle Windows path conventions

## Performance Considerations

### Startup Time

- **Lazy Loading**: Load external program config on demand
- **Caching**: Cache program paths after first lookup
- **Validation**: Validate programs only when needed

### Resource Management

- **Process Cleanup**: Ensure child processes cleaned up
- **File Descriptors**: Close unused file descriptors
- **Memory**: Release resources after execution

## Testing Considerations

Key areas for testing:

- **Program Execution**: Test launching various programs
- **Terminal State**: Verify terminal state preserved
- **Error Handling**: Test error conditions
- **Subshell**: Test subshell feature
- **Configuration**: Test config reading
- **Platform Support**: Test on different platforms

## Related Documentation

- [External Programs Feature](../EXTERNAL_PROGRAMS_FEATURE.md) - User documentation
- [Configuration System](CONFIGURATION_SYSTEM.md) - Configuration management
- [Subshell System](SUBSHELL_SYSTEM.md) - Subshell implementation details

## Future Enhancements

Potential improvements:

- **Program Templates**: Configurable program templates
- **Argument Substitution**: Variable substitution in arguments
- **Multiple Programs**: Support multiple programs per type
- **Program Discovery**: Auto-discover installed programs
- **Async Execution**: Non-blocking program execution
- **Output Capture**: Capture and display program output
