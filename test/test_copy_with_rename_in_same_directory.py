"""Regression test for copy/move with rename-on-conflict in the same directory.

Bug: when the user resolved a conflict by choosing "Rename" and entering a new
name, the FileOperationTask passed only the source path to the executor, which
recomputed the destination as `destination_dir / source.name` — i.e. the
original (already-existing) name. With overwrite=False the file was silently
skipped, but the success summary still reported "1 successful" because the
count came from results['success'] populated at rename-resolution time.

Run with: PYTHONPATH=.:src:ttk python test/test_copy_with_rename_in_same_directory.py
"""

import tempfile
import time
import unittest
from pathlib import Path as StdPath
from unittest.mock import Mock

from tfm_cache_manager import CacheManager
from tfm_file_operation_executor import FileOperationExecutor
from tfm_file_operation_task import FileOperationTask
from tfm_path import Path as TFMPath
from tfm_progress_manager import ProgressManager


class FakeFileManager:
    """Minimal FileManager stub the executor/task can talk to."""

    def __init__(self):
        self.dirty = False
        self.pane = {'selected_files': set()}
        self.progress_manager = ProgressManager()
        self.cache_manager = CacheManager()

    def mark_dirty(self):
        self.dirty = True

    def refresh_files(self):
        pass

    def get_current_pane(self):
        return self.pane

    def _clear_task(self):
        pass


def _wait_until(predicate, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


class TestCopyWithRenameInSameDirectory(unittest.TestCase):
    def test_copy_with_rename_in_same_dir_creates_renamed_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            work = StdPath(temp_dir)
            source = work / "original.txt"
            source.write_text("hello")

            file_manager = FakeFileManager()
            executor = FileOperationExecutor(file_manager)

            ui = Mock()
            ui.config = Mock()
            ui.config.CONFIRM_COPY = False

            task = FileOperationTask(file_manager, ui, executor)

            src = TFMPath(str(source))
            dest_dir = TFMPath(str(work))

            # Start the copy. Confirmation is disabled, so it goes straight to
            # conflict checking — and the source name conflicts with itself
            # because we're copying into the same directory.
            task.start_operation('copy', [src], dest_dir)

            # The conflict-resolution callback was registered on the UI; pull it.
            self.assertTrue(_wait_until(lambda: ui.show_conflict_dialog.called))
            conflict_callback = ui.show_conflict_dialog.call_args[0][4]

            # User picks "Rename".
            conflict_callback('rename', False)

            # The rename dialog callback was registered on the UI; pull it.
            self.assertTrue(_wait_until(lambda: ui.show_rename_dialog.called))
            rename_callback = ui.show_rename_dialog.call_args[0][2]

            # User enters the new name.
            rename_callback(src, "original-2.txt")

            # Wait for the executor's worker thread to finish.
            renamed = work / "original-2.txt"
            self.assertTrue(
                _wait_until(lambda: renamed.exists()),
                f"Renamed copy was not created at {renamed}",
            )
            self.assertEqual(renamed.read_text(), "hello")
            self.assertTrue(source.exists(), "Source file should still exist after copy")


if __name__ == '__main__':
    unittest.main()
