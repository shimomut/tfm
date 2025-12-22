#!/usr/bin/env python3
"""
TFM External Programs Module - Handles external program execution and subshell features
"""

import os
import subprocess
import sys
import shlex
import time
from tfm_path import Path
from tfm_backend_detector import is_desktop_mode


def tfm_tool(tool_name):
    """
    Find and return the path to a TFM tool.
    
    This function searches for tools in the TFM tool directories:
    1. ~/.tfm/tools/ (user-specific tools, highest priority)
    2. {parent of src}/tools/ (system tools - works for both development and installed package)
    
    Args:
        tool_name: Name of the tool to search for
        
    Returns:
        Path to the tool if found, otherwise the original tool_name
        
    Example:
        {'name': 'My Tool', 'command': [sys.executable, tfm_tool('my_script.py')]}
    """
    
    # Candidate directories in priority order
    candidates = []
    
    # 1. User-specific tools directory: ~/.tfm/tools/
    home_dir = Path.home()
    user_tools_dir = home_dir / '.tfm' / 'tools'
    candidates.append(user_tools_dir / tool_name)
    
    # 2. System tools directory
    # This works for both development and installed package:
    # - Development: project_root/src/tfm_external_programs.py -> project_root/src/tools/
    # - Installed: site-packages/tfm/tfm_external_programs.py -> site-packages/tfm/tools/
    current_file = Path(__file__)  # This is tfm_external_programs.py
    tools_dir = current_file.parent / 'tools'  # tools/ is in the same directory as this file
    candidates.append(tools_dir / tool_name)
    
    # Check each candidate
    for candidate_path in candidates:
        if candidate_path.exists() and os.access(candidate_path, os.X_OK):
            return str(candidate_path)
    
    # Tool not found, return original name (will likely fail later with clear error)
    return tool_name


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
    if not selected and pane_data['files'] and pane_data['focused_index'] < len(pane_data['files']):
        # No files selected, use focused file
        focused_file = pane_data['files'][pane_data['focused_index']]
        selected = [focused_file.name]
    return selected

class ExternalProgramManager:
    """Manages external program execution and subshell functionality"""
    
    def __init__(self, config, log_manager, renderer=None):
        self.config = config
        self.log_manager = log_manager
        self.renderer = renderer
    



    
    def execute_external_program(self, pane_manager, program):
        """Execute an external program with environment variables set"""
        # Detect if running in desktop mode
        desktop_mode = is_desktop_mode()
        
        # In terminal mode, restore stdout/stderr to allow subprocess to use terminal
        # In desktop mode, keep LogCapture active so subprocess output goes to log pane
        if not desktop_mode:
            self.log_manager.restore_stdio()
        
        # Clear the screen and reset cursor
        self.renderer.clear()
        self.renderer.refresh()
        
        # Suspend the renderer to allow external program to run
        self.renderer.suspend()
        
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
            
            # Use the command as-is (users should use tfm_tool() for TFM tools)
            command = program['command']
            
            # Determine working directory for external program
            # If current pane is browsing a remote directory (like S3), 
            # fallback to TFM's working directory
            working_dir = None
            if current_pane['path'].is_remote():
                working_dir = os.getcwd()
            else:
                working_dir = str(current_pane['path'])
            
            # Print information about the program execution
            print(f"TFM External Program: {program['name']}")
            print("=" * 50)
            print(f"Command: {' '.join(command)}")
            print(f"Working Directory: {working_dir}")
            if current_pane['path'].is_remote():
                print(f"Note: Current pane is browsing remote directory: {current_pane['path']}")
                print(f"Working directory set to TFM's directory: {working_dir}")
            print(f"TFM_THIS_DIR: {env['TFM_THIS_DIR']}")
            print(f"TFM_THIS_SELECTED: {env['TFM_THIS_SELECTED']}")
            print("=" * 50)
            print()
            
            # Change to the working directory
            os.chdir(working_dir)
            
            # Execute the program with the modified environment
            # In desktop mode, capture output to redirect to log pane
            if desktop_mode:
                result = subprocess.run(command, env=env, capture_output=True, text=True)
                
                # Redirect stdout to log pane (LogCapture is still active)
                if result.stdout:
                    for line in result.stdout.splitlines():
                        print(line)
                
                # Redirect stderr to log pane (LogCapture is still active)
                if result.stderr:
                    for line in result.stderr.splitlines():
                        print(line, file=sys.stderr)
            else:
                # Terminal mode - let subprocess use terminal directly
                result = subprocess.run(command, env=env)
            
            # Check if auto_return option is enabled
            auto_return = program.get('options', {}).get('auto_return', False)
            
            # Show exit status
            print()
            print("=" * 50)
            if result.returncode == 0:
                print(f"Program '{program['name']}' completed successfully")
                
                if auto_return or desktop_mode:
                    # In desktop mode, no sleep needed - just return immediately
                    if not desktop_mode:
                        time.sleep(1)  # Brief pause in terminal mode only
                else:
                    print("Press Enter to return to TFM...")
                    input()
            else:
                print(f"Program '{program['name']}' exited with code {result.returncode}")
                # In desktop mode, auto-return even on error (user can check log pane)
                # In terminal mode, wait for user input when there's an error
                if desktop_mode:
                    print("Check log pane for error details.")
                    # No sleep in desktop mode - return immediately
                else:
                    print("Press Enter to return to TFM...")
                    input()
            
        except FileNotFoundError:
            print(f"Error: Command not found: {program['command'][0]}")
            print("Tip: Use tfm_tool() function for TFM tools in your configuration")
            
            # In desktop mode, auto-return (user can check log pane)
            # In terminal mode, wait for user input
            if desktop_mode:
                print("Check log pane for error details.")
                # No sleep in desktop mode - return immediately
            else:
                print("Press Enter to continue...")
                input()
        except Exception as e:
            print(f"Error executing program '{program['name']}': {e}")
            
            # In desktop mode, auto-return (user can check log pane)
            # In terminal mode, wait for user input
            if desktop_mode:
                print("Check log pane for error details.")
                # No sleep in desktop mode - return immediately
            else:
                print("Press Enter to continue...")
                input()
        
        finally:
            # Resume the renderer
            self.renderer.resume()
            
            # Reinitialize colors with configured scheme
            from tfm_colors import init_colors
            color_scheme = getattr(self.config, 'COLOR_SCHEME', 'dark')
            init_colors(self.renderer, color_scheme)
            
            # Restore stdout/stderr capture (only needed in terminal mode)
            # In desktop mode, LogCapture was never disconnected
            if not desktop_mode:
                from tfm_log_manager import LogCapture
                sys.stdout = LogCapture(self.log_manager.log_messages, "STDOUT")
                sys.stderr = LogCapture(self.log_manager.log_messages, "STDERR")
            
            # Log return from program execution
            print(f"Returned from external program: {program['name']}")
    
    def enter_subshell_mode(self, pane_manager):
        """Enter sub-shell mode with environment variables set"""
        # Restore stdout/stderr temporarily
        self.log_manager.restore_stdio()
        
        # Clear the screen and reset cursor
        self.renderer.clear()
        self.renderer.refresh()
        
        # Suspend the renderer to allow subshell to run
        self.renderer.suspend()
        
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
            
            # Determine working directory for subshell
            # If current pane is browsing a remote directory (like S3), 
            # fallback to TFM's working directory
            working_dir = None
            if current_pane['path'].is_remote():
                working_dir = os.getcwd()
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
                print(f"Note: Current pane is browsing remote directory: {current_pane['path']}")
                print(f"Subshell working directory set to TFM's directory: {working_dir}")
            else:
                working_dir = str(current_pane['path'])
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
            
            # Change to the working directory
            os.chdir(working_dir)
            
            # Start the shell with the modified environment
            shell = env.get('SHELL', '/bin/bash')
            subprocess.run([shell], env=env)
            
        except Exception as e:
            print(f"Error starting sub-shell: {e}")
            input("Press Enter to continue...")
        
        finally:
            # Resume the renderer
            self.renderer.resume()
            
            # Reinitialize colors with configured scheme
            from tfm_colors import init_colors
            color_scheme = getattr(self.config, 'COLOR_SCHEME', 'dark')
            init_colors(self.renderer, color_scheme)
            
            # Restore stdout/stderr capture  
            from tfm_log_manager import LogCapture
            sys.stdout = LogCapture(self.log_manager.log_messages, "STDOUT")
            sys.stderr = LogCapture(self.log_manager.log_messages, "STDERR")
            
            # Log return from sub-shell
            print("Returned from sub-shell mode")
    
    def suspend_curses(self):
        """Suspend the renderer to allow external programs to run"""
        # Check if the renderer has a suspend method (CursesBackend does)
        if hasattr(self.renderer, 'suspend'):
            self.renderer.suspend()
        
    def resume_curses(self):
        """Resume the renderer after external program execution"""
        # Check if the renderer has a resume method (CursesBackend does)
        if hasattr(self.renderer, 'resume'):
            self.renderer.resume()