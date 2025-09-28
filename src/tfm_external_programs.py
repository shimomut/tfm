#!/usr/bin/env python3
"""
TFM External Programs Module - Handles external program execution and subshell features
"""

import curses
import os
import subprocess
import sys
import shlex
import time
from tfm_path import Path


def quote_filenames_with_double_quotes(filenames):
    """
    Quote filenames for safe shell usage using double quotes.
    
    This function replaces the previous use of shlex.quote() which used single quotes.
    Double quotes are preferred for TFM_*_SELECTED environment variables to provide
    consistent quoting behavior across different shell environments.
    
    Args:
        filenames: List of filename strings to quote
        
    Returns:
        List of quoted filename strings using double quotes
    """
    quoted = []
    for filename in filenames:
        # Use double quotes and escape any double quotes or backslashes in the filename
        escaped = filename.replace('\\', '\\\\').replace('"', '\\"')
        quoted.append(f'"{escaped}"')
    return quoted


def get_selected_or_cursor_files(pane_data):
    """Get selected files, or current cursor position if no files selected"""
    selected = [Path(f).name for f in pane_data['selected_files']]
    if not selected and pane_data['files'] and pane_data['selected_index'] < len(pane_data['files']):
        # No files selected, use cursor position
        cursor_file = pane_data['files'][pane_data['selected_index']]
        selected = [cursor_file.name]
    return selected

class ExternalProgramManager:
    """Manages external program execution and subshell functionality"""
    
    def __init__(self, config, log_manager):
        self.config = config
        self.log_manager = log_manager
    
    def resolve_command_path(self, command):
        """
        Resolve the command path, converting relative paths to absolute paths
        based on the TFM main script location.
        
        This function handles the following cases:
        - Absolute paths: Returned unchanged (e.g., '/usr/bin/git')
        - Relative paths with separators: Resolved relative to tfm.py location (e.g., './tools/script.sh')
        - Command names only: Returned unchanged to be found in PATH (e.g., 'git')
        
        Args:
            command: List where first element is the command/program path
            
        Returns:
            List with resolved command path (first element may be modified)
            
        Examples:
            ['./tools/script.sh'] -> ['/path/to/tfm/tools/script.sh']
            ['git', 'status'] -> ['git', 'status'] (unchanged)
            ['/usr/bin/python3'] -> ['/usr/bin/python3'] (unchanged)
        """
        if not command or not command[0]:
            return command
        
        command_path = Path(command[0])
        
        # If it's already an absolute path, return as-is
        if command_path.is_absolute():
            return command
        
        # If it's a relative path, resolve it relative to tfm.py location
        if '/' in command[0] or '\\' in command[0]:  # Contains path separators
            # Find the TFM main script directory
            # We need to go up from src/ to the root where tfm.py is located
            current_file = Path(__file__)  # This is tfm_external_programs.py in src/
            tfm_root = current_file.parent.parent  # Go up from src/ to root
            
            # Resolve the relative path
            resolved_path = (tfm_root / command_path).resolve()
            
            # Create new command list with resolved path
            resolved_command = [str(resolved_path)] + command[1:]
            return resolved_command
        
        # If it's just a command name without path separators, return as-is
        # (let the system find it in PATH)
        return command
    
    def execute_external_program(self, stdscr, pane_manager, program):
        """Execute an external program with environment variables set"""
        # Restore stdout/stderr temporarily
        self.log_manager.restore_stdio()
        
        # Clear the screen and reset cursor
        stdscr.clear()
        stdscr.refresh()
        
        # Reset terminal to normal mode
        curses.endwin()
        
        try:
            # Get current pane information
            left_pane = pane_manager.left_pane
            right_pane = pane_manager.right_pane
            current_pane = pane_manager.get_current_pane()
            other_pane = pane_manager.get_inactive_pane()
            
            # Set environment variables with TFM_ prefix
            env = os.environ.copy()
            env['TFM_LEFT_DIR'] = str(left_pane['path'])
            env['TFM_RIGHT_DIR'] = str(right_pane['path'])
            env['TFM_THIS_DIR'] = str(current_pane['path'])
            env['TFM_OTHER_DIR'] = str(other_pane['path'])
            
            # Get selected files for each pane, or cursor position if no selection
            left_selected = quote_filenames_with_double_quotes(get_selected_or_cursor_files(left_pane))
            right_selected = quote_filenames_with_double_quotes(get_selected_or_cursor_files(right_pane))
            current_selected = quote_filenames_with_double_quotes(get_selected_or_cursor_files(current_pane))
            other_selected = quote_filenames_with_double_quotes(get_selected_or_cursor_files(other_pane))
            
            # Set selected files environment variables (space-separated) with TFM_ prefix
            env['TFM_LEFT_SELECTED'] = ' '.join(left_selected)
            env['TFM_RIGHT_SELECTED'] = ' '.join(right_selected)
            env['TFM_THIS_SELECTED'] = ' '.join(current_selected)
            env['TFM_OTHER_SELECTED'] = ' '.join(other_selected)
            
            # Set TFM indicator environment variable
            env['TFM_ACTIVE'] = '1'
            
            # Resolve relative paths in the command
            resolved_command = self.resolve_command_path(program['command'])
            
            # Print information about the program execution
            print(f"TFM External Program: {program['name']}")
            print("=" * 50)
            print(f"Original Command: {' '.join(program['command'])}")
            if resolved_command != program['command']:
                print(f"Resolved Command: {' '.join(resolved_command)}")
            print(f"Working Directory: {current_pane['path']}")
            print(f"TFM_THIS_DIR: {env['TFM_THIS_DIR']}")
            print(f"TFM_THIS_SELECTED: {env['TFM_THIS_SELECTED']}")
            print("=" * 50)
            print()
            
            # Change to the current directory
            os.chdir(current_pane['path'])
            
            # Execute the program with the modified environment
            result = subprocess.run(resolved_command, env=env)
            
            # Check if auto_return option is enabled
            auto_return = program.get('options', {}).get('auto_return', False)
            
            # Show exit status
            print()
            print("=" * 50)
            if result.returncode == 0:
                print(f"Program '{program['name']}' completed successfully")
            else:
                print(f"Program '{program['name']}' exited with code {result.returncode}")
            
            if auto_return:
                print("Auto-returning to TFM...")
                time.sleep(1)  # Brief pause to show the message
            else:
                print("Press Enter to return to TFM...")
                input()
            
        except FileNotFoundError:
            resolved_command = self.resolve_command_path(program['command'])
            print(f"Error: Command not found: {resolved_command[0]}")
            if resolved_command != program['command']:
                print(f"(Resolved from: {program['command'][0]})")
            print("Press Enter to continue...")
            input()
        except Exception as e:
            print(f"Error executing program '{program['name']}': {e}")
            print("Press Enter to continue...")
            input()
        
        finally:
            # Reinitialize curses
            stdscr = curses.initscr()
            curses.curs_set(0)  # Hide cursor
            stdscr.keypad(True)
            
            # Reinitialize colors with configured scheme
            from tfm_colors import init_colors
            color_scheme = getattr(self.config, 'COLOR_SCHEME', 'dark')
            init_colors(color_scheme)
            
            # Restore stdout/stderr capture
            from tfm_log_manager import LogCapture
            sys.stdout = LogCapture(self.log_manager.log_messages, "STDOUT")
            sys.stderr = LogCapture(self.log_manager.log_messages, "STDERR")
            
            # Log return from program execution
            print(f"Returned from external program: {program['name']}")
            
            return stdscr  # Return the reinitialized screen
    
    def enter_subshell_mode(self, stdscr, pane_manager):
        """Enter sub-shell mode with environment variables set"""
        # Restore stdout/stderr temporarily
        self.log_manager.restore_stdio()
        
        # Clear the screen and reset cursor
        stdscr.clear()
        stdscr.refresh()
        
        # Reset terminal to normal mode
        curses.endwin()
        
        try:
            # Get current pane information
            left_pane = pane_manager.left_pane
            right_pane = pane_manager.right_pane
            current_pane = pane_manager.get_current_pane()
            other_pane = pane_manager.get_inactive_pane()
            
            # Set environment variables with TFM_ prefix
            env = os.environ.copy()
            env['TFM_LEFT_DIR'] = str(left_pane['path'])
            env['TFM_RIGHT_DIR'] = str(right_pane['path'])
            env['TFM_THIS_DIR'] = str(current_pane['path'])
            env['TFM_OTHER_DIR'] = str(other_pane['path'])
            
            # Get selected files for each pane, or cursor position if no selection
            left_selected = quote_filenames_with_double_quotes(get_selected_or_cursor_files(left_pane))
            right_selected = quote_filenames_with_double_quotes(get_selected_or_cursor_files(right_pane))
            current_selected = quote_filenames_with_double_quotes(get_selected_or_cursor_files(current_pane))
            other_selected = quote_filenames_with_double_quotes(get_selected_or_cursor_files(other_pane))
            
            # Set selected files environment variables (space-separated) with TFM_ prefix
            # Filenames are properly quoted with double quotes for shell safety
            env['TFM_LEFT_SELECTED'] = ' '.join(left_selected)
            env['TFM_RIGHT_SELECTED'] = ' '.join(right_selected)
            env['TFM_THIS_SELECTED'] = ' '.join(current_selected)
            env['TFM_OTHER_SELECTED'] = ' '.join(other_selected)
            
            # Set TFM indicator environment variable
            env['TFM_ACTIVE'] = '1'
            
            # Modify shell prompt to include [TFM] label
            # Handle both bash (PS1) and zsh (PROMPT) prompts
            current_ps1 = env.get('PS1', '')
            current_prompt = env.get('PROMPT', '')
            
            # Modify PS1 for bash and other shells
            if current_ps1:
                env['PS1'] = f'[TFM] {current_ps1}'
            else:
                env['PS1'] = '[TFM] \\u@\\h:\\w\\$ '
            
            # Modify PROMPT for zsh
            if current_prompt:
                env['PROMPT'] = f'[TFM] {current_prompt}'
            else:
                env['PROMPT'] = '[TFM] %n@%m:%~%# '
            
            # Print information about the sub-shell environment
            print("TFM Sub-shell Mode")
            print("=" * 50)
            print(f"TFM_LEFT_DIR:      {env['TFM_LEFT_DIR']}")
            print(f"TFM_RIGHT_DIR:     {env['TFM_RIGHT_DIR']}")
            print(f"TFM_THIS_DIR:      {env['TFM_THIS_DIR']}")
            print(f"TFM_OTHER_DIR:     {env['TFM_OTHER_DIR']}")
            print(f"TFM_LEFT_SELECTED: {env['TFM_LEFT_SELECTED']}")
            print(f"TFM_RIGHT_SELECTED: {env['TFM_RIGHT_SELECTED']}")
            print(f"TFM_THIS_SELECTED: {env['TFM_THIS_SELECTED']}")
            print(f"TFM_OTHER_SELECTED: {env['TFM_OTHER_SELECTED']}")
            print("=" * 50)
            print("TFM_ACTIVE environment variable is set for shell customization")
            print("To show [TFM] in your prompt, add this to your shell config:")
            print("  Zsh (~/.zshrc): if [[ -n \"$TFM_ACTIVE\" ]]; then PROMPT=\"[TFM] $PROMPT\"; fi")
            print("  Bash (~/.bashrc): if [[ -n \"$TFM_ACTIVE\" ]]; then PS1=\"[TFM] $PS1\"; fi")
            print("Type 'exit' to return to TFM")
            print()
            
            # Change to the current directory
            os.chdir(current_pane['path'])
            
            # Start the shell with the modified environment
            shell = env.get('SHELL', '/bin/bash')
            subprocess.run([shell], env=env)
            
        except Exception as e:
            print(f"Error starting sub-shell: {e}")
            input("Press Enter to continue...")
        
        finally:
            # Reinitialize curses
            stdscr = curses.initscr()
            curses.curs_set(0)  # Hide cursor
            stdscr.keypad(True)
            
            # Reinitialize colors with configured scheme
            from tfm_colors import init_colors
            color_scheme = getattr(self.config, 'COLOR_SCHEME', 'dark')
            init_colors(color_scheme)
            
            # Restore stdout/stderr capture  
            from tfm_log_manager import LogCapture
            sys.stdout = LogCapture(self.log_manager.log_messages, "STDOUT")
            sys.stderr = LogCapture(self.log_manager.log_messages, "STDERR")
            
            # Log return from sub-shell
            print("Returned from sub-shell mode")
            
            return stdscr  # Return the reinitialized screen
    
    def suspend_curses(self, stdscr):
        """Suspend the curses system to allow external programs to run"""
        curses.endwin()
        
    def resume_curses(self, stdscr):
        """Resume the curses system after external program execution"""
        stdscr.refresh()
        curses.curs_set(0)  # Hide cursor