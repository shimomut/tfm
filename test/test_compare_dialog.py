"""App-integration tests for Compare & Select: drives the real dialog through a
MemoryBackend + TfmApp so the handler wiring (guards, dialog → criteria → applied
selection, replace/add, the content task path) and the dialog's draw are covered.

Complements test_compare_selection.py, which unit-tests the pure engine."""

import os
import sys
import shutil
import tempfile
import time
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))
sys.path.insert(0, os.path.join(_HERE, ".."))

import tfm  # noqa: E402
from tfm_compare_dialog import CompareSelectDialog  # noqa: E402
from puikit.backends import create_backend  # noqa: E402
from puikit.event import Event, EventType  # noqa: E402


def _write(d, rel, data=b"x", mtime=None):
    p = os.path.join(d, rel)
    with open(p, "wb") as f:
        f.write(data)
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return p


class CompareDialogApp(unittest.TestCase):
    def setUp(self):
        self.left = tempfile.mkdtemp()
        self.right = tempfile.mkdtemp()
        _write(self.left, "same.txt", b"hello", mtime=1000.0)
        _write(self.right, "same.txt", b"hello", mtime=1000.0)         # identical
        _write(self.left, "newer.txt", b"AAAA", mtime=5000.0)
        _write(self.right, "newer.txt", b"BBBB", mtime=1000.0)         # same size, newer, diff bytes
        _write(self.left, "orphan.txt", b"z")                          # only on the left
        _write(self.right, "only_right.txt", b"y")

        self.b = create_backend("memory")
        self.b.open()
        self.app = tfm.TfmApp(self.b, self.left, self.right,
                              left_provided=True, right_provided=True)
        self.app._settle_listings()

    def tearDown(self):
        try:
            self.app.file_monitor.stop_monitoring()
        except Exception:
            pass
        self.b.close()
        shutil.rmtree(self.left, ignore_errors=True)
        shutil.rmtree(self.right, ignore_errors=True)

    def _open(self):
        self.app.compare_selection()
        dlg = self.app.panel._layers[-1].widget
        self.assertIsInstance(dlg, CompareSelectDialog)
        return dlg

    def _selected_names(self):
        return {os.path.basename(p) for p in self.app.active_pane()["selected_files"]}

    def test_dialog_draws_all_radio_options(self):
        # Regression: option rows must land on distinct integer grid rows (a
        # fractional origin rounded x.5 pairs onto one cell, dropping options).
        self._open()
        self.app.panel.render()
        screen = "\n".join(self.b.snapshot())
        for label in ("any", "equal", "differs", "same", "newer", "older",
                      "Replace", "Add"):
            self.assertIn(label, screen, f"missing radio option {label!r}")

    def test_mtime_newer_replace(self):
        dlg = self._open()
        dlg._mtime.selected = 2   # newer
        dlg._mode.selected = 0    # replace
        dlg._accept()
        self.assertEqual(self._selected_names(), {"newer.txt"})

    def test_include_missing_add_mode_unions(self):
        pane = self.app.active_pane()
        pane["selected_files"].add(os.path.join(self.left, "seed.marker"))  # pre-existing
        dlg = self._open()
        dlg._missing.checked = True   # also orphans
        dlg._mode.selected = 1        # add (union, don't clear)
        dlg._accept()
        names = self._selected_names()
        self.assertIn("same.txt", names)     # filename match
        self.assertIn("newer.txt", names)
        self.assertIn("orphan.txt", names)   # orphan via include_missing
        self.assertIn("seed.marker", names)  # prior selection preserved (add mode)

    def test_replace_mode_clears_prior_selection(self):
        pane = self.app.active_pane()
        pane["selected_files"].add(os.path.join(self.left, "seed.marker"))
        dlg = self._open()
        dlg._mode.selected = 0        # replace
        dlg._accept()                 # filename-only: all common names
        names = self._selected_names()
        self.assertNotIn("seed.marker", names)
        self.assertEqual(names, {"same.txt", "newer.txt"})

    def test_cancel_leaves_selection_untouched(self):
        pane = self.app.active_pane()
        pane["selected_files"].add(os.path.join(self.left, "keep.marker"))
        dlg = self._open()
        dlg._finish(None)             # cancel
        self.assertEqual(self._selected_names(), {"keep.marker"})

    def test_content_differs_runs_on_worker(self):
        dlg = self._open()
        dlg._content.selected = 2     # differs -> content path -> task worker
        dlg._mode.selected = 0        # replace
        dlg._accept()
        deadline = time.time() + 5
        while self.app.tasks.has_active() and time.time() < deadline:
            self.b.run_animation_ticks()
            time.sleep(0.01)
        self.b.run_animation_ticks()
        # same.txt has identical bytes; newer.txt differs at equal size.
        self.assertEqual(self._selected_names(), {"newer.txt"})

    def test_tab_and_arrow_change_focus_and_selection(self):
        dlg = self._open()
        self.assertIs(dlg._focused, dlg._size)
        dlg.handle_event(Event(EventType.KEY, key="tab"))    # -> mtime
        self.assertIs(dlg._focused, dlg._mtime)
        dlg.handle_event(Event(EventType.KEY, key="down"))   # mtime: any -> same
        self.assertEqual(dlg._mtime.selected, 1)


class CompareDialogFlow(unittest.TestCase):
    """The vertical flow must never overlap, at any radio pitch. The memory backend
    is a 1:1 grid, so it can't reproduce the taller vector pitch that caused the
    real GUI overlap — assert the pure geometry (_flow) directly with grid- and
    vector-scale measured heights."""

    def _regions(self, f, band_h, cb_h, mode_h, btn_h):
        return [
            ("band", f["band_top"], f["band_top"] + band_h),
            ("checkbox", f["cb_y"], f["cb_y"] + cb_h),
            ("sel_header", f["sel_head_y"], f["sel_head_y"] + 1.0),
            ("mode", f["mode_y"], f["mode_y"] + mode_h),
            ("buttons", f["btn_y"], f["btn_y"] + btn_h),
        ]

    def _assert_no_overlap(self, band_h, cb_h, mode_h, btn_h, title_bottom):
        dlg = CompareSelectDialog(on_result=lambda c: None)
        f = dlg._flow(title_bottom, band_h, cb_h, mode_h, btn_h)
        stacked = self._regions(f, band_h, cb_h, mode_h, btn_h)[:-1]  # single column
        prev_bottom = title_bottom
        for name, top, bottom in stacked:
            self.assertGreaterEqual(top + 1e-6, prev_bottom,
                                    f"{name} overlaps the element above it")
            prev_bottom = bottom
        # buttons share the bottom band with the mode group and must fit inside it
        self.assertGreaterEqual(f["btn_y"] + 1e-6, f["mode_y"])
        self.assertLessEqual(f["btn_y"] + btn_h, f["bottom"] + 1e-6)
        # the reported box bottom encloses everything
        self.assertGreaterEqual(f["bottom"] + 1e-6, f["mode_y"] + max(mode_h, btn_h))

    def test_grid_pitch_no_overlap(self):
        self._assert_no_overlap(4.0, 1.0, 2.0, 1.0, title_bottom=3.0)

    def test_vector_pitch_no_overlap(self):
        # radio pitch ~1.4/row (4-option band ~5.6), checkbox ~1.4, buttons ~1.6
        self._assert_no_overlap(5.6, 1.4, 2.8, 1.6, title_bottom=2.3)

    def test_taller_pitch_still_no_overlap(self):
        self._assert_no_overlap(8.0, 2.0, 4.0, 2.4, title_bottom=2.0)


if __name__ == "__main__":
    unittest.main()
