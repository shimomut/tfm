#!/usr/bin/env python3
"""
Property-based tests for external program integration

**Feature: qt-gui-port, Property 21: External program integration**
**Feature: qt-gui-port, Property 22: Post-operation refresh**
**Feature: qt-gui-port, Property 23: External program error handling**
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path as StdPath
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings
import pytest

# Add src directory to path
src_dir = StdPath(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

from tfm_external_programs import ExternalProgramManager
from tfm_path import Path


# Strategies for generating test data
@st.composite
def pane_data_strategy(draw):
    """Generate pane data with selected files"""
    # Generate a list of filenames
    num_files = draw(st.integers(min_value=0, max_value=10))
    filenames = [f"file_{i}.txt" for i in range(num_files)]
    
    # Generate selected files (subset of filenames)
    num_selected = draw(st.integers(min_value=0, max_value=num_files))
    selected_indices = draw(st.lists(
        st.integers(min_value=0, max_value=max(0, num_files - 1)),
        min_size=num_selected,
        max_size=num_selected,
        unique=True
    )) if num_files > 0 else []
    
    selected_files = [filenames[i] for i in selected_indices] if num_files > 0 else []
    
    # Create mock Path objects for files
    mock_files = []
    for filename in filenames:
        mock_file = Mock(spec=Path)
        mock_file.name = filename
        mock_file.is_remote.return_value = False
        mock_files.append(mock_file)
    
    # Create pane data
    pane = {
        'path': Path('/test/directory'),
        'files': mock_files,
        'selected_files': selected_files,
        'selected_index': draw(st.integers(min_value=0, max_value=max(0, num_files - 1))) if num_files > 0 else 0
    }
    
    return pane


@st.composite
def program_config_strategy(draw):
    """Generate external program configuration"""
    program_name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    command = draw(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3))
    auto_return = draw(st.booleans())
    
    return {
        'name': program_name,
        'command': command,
        'options': {'auto_return': auto_return}
    }


class TestExternalProgramIntegration:
    """Property-based tests for external program integration"""
    
    @given(
        left_pane=pane_data_strategy(),
        right_pane=pane_data_strategy(),
        program=program_config_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_21_external_program_environment_variables(self, left_pane, right_pane, program):
        """
        **Feature: qt-gui-port, Property 21: External program integration**
        
        For any configured external program, it should receive selected files through 
        environment variables with consistent naming (TFM_THIS_DIR, TFM_THIS_SELECTED, etc.)
        
        **Validates: Requirements 8.1, 8.2, 8.3**
        """
        # Setup
        config = Mock()
        log_manager = Mock()
        log_manager.restore_stdio = Mock()
        
        external_program_manager = ExternalProgramManager(config, log_manager)
        
        # Create mock pane manager
        pane_manager = Mock()
        pane_manager.left_pane = left_pane
        pane_manager.right_pane = right_pane
        pane_manager.active_pane = 'left'
        pane_manager.get_current_pane.return_value = left_pane
        pane_manager.get_inactive_pane.return_value = right_pane
        
        # Create mock stdscr
        stdscr = Mock()
        stdscr.clear = Mock()
        stdscr.refresh = Mock()
        
        # Track environment variables passed to subprocess
        captured_env = {}
        
        def capture_subprocess_run(command, env=None):
            nonlocal captured_env
            if env:
                captured_env = env.copy()
            return Mock(returncode=0)
        
        # Mock all the necessary functions
        with patch('curses.endwin'), \
             patch('curses.initscr', return_value=stdscr), \
             patch('curses.curs_set'), \
             patch('subprocess.run', side_effect=capture_subprocess_run), \
             patch('os.chdir'), \
             patch('tfm_colors.init_colors'), \
             patch('builtins.print'), \
             patch('builtins.input'):
            
            # Execute external program
            external_program_manager.execute_external_program(stdscr, pane_manager, program)
        
        # Verify environment variables are set correctly
        assert 'TFM_LEFT_DIR' in captured_env, "TFM_LEFT_DIR should be set"
        assert 'TFM_RIGHT_DIR' in captured_env, "TFM_RIGHT_DIR should be set"
        assert 'TFM_THIS_DIR' in captured_env, "TFM_THIS_DIR should be set"
        assert 'TFM_OTHER_DIR' in captured_env, "TFM_OTHER_DIR should be set"
        assert 'TFM_LEFT_SELECTED' in captured_env, "TFM_LEFT_SELECTED should be set"
        assert 'TFM_RIGHT_SELECTED' in captured_env, "TFM_RIGHT_SELECTED should be set"
        assert 'TFM_THIS_SELECTED' in captured_env, "TFM_THIS_SELECTED should be set"
        assert 'TFM_OTHER_SELECTED' in captured_env, "TFM_OTHER_SELECTED should be set"
        assert 'TFM_ACTIVE' in captured_env, "TFM_ACTIVE should be set"
        
        # Verify directory paths are correct
        assert captured_env['TFM_LEFT_DIR'] == str(left_pane['path'])
        assert captured_env['TFM_RIGHT_DIR'] == str(right_pane['path'])
        assert captured_env['TFM_THIS_DIR'] == str(left_pane['path'])
        assert captured_env['TFM_OTHER_DIR'] == str(right_pane['path'])
        assert captured_env['TFM_ACTIVE'] == '1'
        
        # Verify selected files are passed (should be space-separated quoted filenames)
        # The format should be: "file1.txt" "file2.txt" etc.
        if left_pane['selected_files']:
            assert captured_env['TFM_LEFT_SELECTED'] != '', "TFM_LEFT_SELECTED should not be empty when files are selected"
            # Check that selected files are quoted
            for filename in left_pane['selected_files']:
                assert f'"{filename}"' in captured_env['TFM_LEFT_SELECTED'], f"Selected file {filename} should be quoted in TFM_LEFT_SELECTED"
    
    @given(
        pane=pane_data_strategy(),
        program=program_config_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_22_post_operation_refresh_needed(self, pane, program):
        """
        **Feature: qt-gui-port, Property 22: Post-operation refresh**
        
        For any external program that completes, the system should be ready to refresh 
        the file listing to show any changes made by the external program.
        
        **Validates: Requirements 8.4**
        """
        # Setup
        config = Mock()
        log_manager = Mock()
        log_manager.restore_stdio = Mock()
        
        external_program_manager = ExternalProgramManager(config, log_manager)
        
        # Create mock pane manager
        pane_manager = Mock()
        pane_manager.left_pane = pane
        pane_manager.right_pane = pane
        pane_manager.active_pane = 'left'
        pane_manager.get_current_pane.return_value = pane
        pane_manager.get_inactive_pane.return_value = pane
        
        # Create mock stdscr
        stdscr = Mock()
        stdscr.clear = Mock()
        stdscr.refresh = Mock()
        
        # Mock all the necessary functions
        with patch('curses.endwin'), \
             patch('curses.initscr', return_value=stdscr), \
             patch('curses.curs_set'), \
             patch('subprocess.run', return_value=Mock(returncode=0)), \
             patch('os.chdir'), \
             patch('tfm_colors.init_colors'), \
             patch('builtins.print'), \
             patch('builtins.input'):
            
            # Execute external program
            result_stdscr = external_program_manager.execute_external_program(stdscr, pane_manager, program)
        
        # Verify that curses is reinitialized after program execution
        # This allows the UI to refresh and show any file changes
        assert result_stdscr is not None, "Should return reinitialized stdscr for UI refresh"
        
        # Verify that the log manager captured the return message
        # This indicates the system is ready for refresh
        log_manager.restore_stdio.assert_called()
    
    @given(
        pane=pane_data_strategy(),
        program=program_config_strategy(),
        exit_code=st.integers(min_value=1, max_value=255)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_23_external_program_error_handling(self, pane, program, exit_code):
        """
        **Feature: qt-gui-port, Property 23: External program error handling**
        
        For any external program that fails (non-zero exit code), an error message 
        should be displayed to the user.
        
        **Validates: Requirements 8.5**
        """
        # Setup
        config = Mock()
        log_manager = Mock()
        log_manager.restore_stdio = Mock()
        
        external_program_manager = ExternalProgramManager(config, log_manager)
        
        # Create mock pane manager
        pane_manager = Mock()
        pane_manager.left_pane = pane
        pane_manager.right_pane = pane
        pane_manager.active_pane = 'left'
        pane_manager.get_current_pane.return_value = pane
        pane_manager.get_inactive_pane.return_value = pane
        
        # Create mock stdscr
        stdscr = Mock()
        stdscr.clear = Mock()
        stdscr.refresh = Mock()
        
        # Track print calls to verify error message
        print_calls = []
        
        def capture_print(*args, **kwargs):
            print_calls.append(' '.join(str(arg) for arg in args))
        
        # Mock all the necessary functions
        with patch('curses.endwin'), \
             patch('curses.initscr', return_value=stdscr), \
             patch('curses.curs_set'), \
             patch('subprocess.run', return_value=Mock(returncode=exit_code)), \
             patch('os.chdir'), \
             patch('tfm_colors.init_colors'), \
             patch('builtins.print', side_effect=capture_print), \
             patch('builtins.input'):
            
            # Execute external program (should fail)
            external_program_manager.execute_external_program(stdscr, pane_manager, program)
        
        # Verify that an error message was printed
        error_messages = [msg for msg in print_calls if 'exited with code' in msg.lower() or str(exit_code) in msg]
        assert len(error_messages) > 0, f"Should display error message for non-zero exit code {exit_code}"
        
        # Verify that the error message includes the program name
        program_name_mentioned = any(program['name'] in msg for msg in print_calls)
        assert program_name_mentioned, "Error message should mention the program name"
    
    @given(
        pane=pane_data_strategy(),
        program=program_config_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_23_file_not_found_error_handling(self, pane, program):
        """
        **Feature: qt-gui-port, Property 23: External program error handling**
        
        For any external program that cannot be found, an error message should be 
        displayed to the user.
        
        **Validates: Requirements 8.5**
        """
        # Setup
        config = Mock()
        log_manager = Mock()
        log_manager.restore_stdio = Mock()
        
        external_program_manager = ExternalProgramManager(config, log_manager)
        
        # Create mock pane manager
        pane_manager = Mock()
        pane_manager.left_pane = pane
        pane_manager.right_pane = pane
        pane_manager.active_pane = 'left'
        pane_manager.get_current_pane.return_value = pane
        pane_manager.get_inactive_pane.return_value = pane
        
        # Create mock stdscr
        stdscr = Mock()
        stdscr.clear = Mock()
        stdscr.refresh = Mock()
        
        # Track print calls to verify error message
        print_calls = []
        
        def capture_print(*args, **kwargs):
            print_calls.append(' '.join(str(arg) for arg in args))
        
        # Mock all the necessary functions
        with patch('curses.endwin'), \
             patch('curses.initscr', return_value=stdscr), \
             patch('curses.curs_set'), \
             patch('subprocess.run', side_effect=FileNotFoundError("Command not found")), \
             patch('os.chdir'), \
             patch('tfm_colors.init_colors'), \
             patch('builtins.print', side_effect=capture_print), \
             patch('builtins.input'):
            
            # Execute external program (should fail with FileNotFoundError)
            external_program_manager.execute_external_program(stdscr, pane_manager, program)
        
        # Verify that an error message was printed
        error_messages = [msg for msg in print_calls if 'error' in msg.lower() or 'not found' in msg.lower()]
        assert len(error_messages) > 0, "Should display error message for FileNotFoundError"
        
        # Verify that the error message mentions the command
        command_mentioned = any(program['command'][0] in msg for msg in print_calls)
        assert command_mentioned, "Error message should mention the command that was not found"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
