"""
Recursive content (grep) search for the PuiKit TfmApp.

Covers the pane-independent search core behind ``show_content_search`` — the
bounded tree walk (``_walk_grep``), the binary-file filter (``_looks_textual``),
and result navigation (``_go_to_content_hit``). The input/results dialogs are
``show_input`` + ``show_filter_list`` modals, exercised via a smoke construction.
"""

import os
import re
import sys
import tempfile
import shutil
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))
sys.path.insert(0, os.path.join(_HERE, ".."))

import tfm  # noqa: E402
from tfm_path import Path  # noqa: E402


def _bare_app(show_hidden=False):
    app = tfm.TfmApp.__new__(tfm.TfmApp)
    app.flm = type("_FLM", (), {"show_hidden": show_hidden})()
    return app


class WalkGrep(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, relpath, content, mode="w"):
        p = os.path.join(self.tmp, relpath)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, mode) as f:
            f.write(content)
        return p

    def _grep(self, pattern, **kw):
        app = _bare_app(**kw)
        return app._walk_grep(Path(self.tmp), re.compile(pattern, re.IGNORECASE))

    def test_finds_matching_line_with_number(self):
        self._write("a.txt", "alpha\nneedle here\ngamma\n")
        hits = self._grep("needle")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["line"], 2)
        self.assertEqual(hits[0]["text"], "needle here")
        self.assertEqual(hits[0]["path"].name, "a.txt")

    def test_recurses_into_subdirectories(self):
        self._write("sub/deep/b.txt", "TODO: fix this\n")
        hits = self._grep("todo")  # case-insensitive
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["path"].name, "b.txt")

    def test_skips_binary_files(self):
        self._write("bin.dat", "match\x00more match\n", mode="w")
        hits = self._grep("match")
        self.assertEqual(hits, [])

    def test_skips_hidden_unless_shown(self):
        self._write(".secret.txt", "password\n")
        self.assertEqual(self._grep("password"), [])
        self.assertEqual(len(self._grep("password", show_hidden=True)), 1)

    def test_result_cap_is_honored(self):
        self._write("big.txt", "hit\n" * 50)
        app = _bare_app()
        hits = app._walk_grep(Path(self.tmp), re.compile("hit"), cap=10)
        self.assertEqual(len(hits), 10)

    def test_no_matches_returns_empty(self):
        self._write("a.txt", "nothing interesting\n")
        self.assertEqual(self._grep("zzz"), [])


class LooksTextual(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _file(self, data):
        p = os.path.join(self.tmp, "f")
        with open(p, "wb") as fh:
            fh.write(data)
        return Path(p)

    def test_text_is_textual(self):
        self.assertTrue(tfm.TfmApp._looks_textual(self._file(b"hello world")))

    def test_nul_byte_is_binary(self):
        self.assertFalse(tfm.TfmApp._looks_textual(self._file(b"hello\x00world")))

    def test_empty_is_not_textual(self):
        self.assertFalse(tfm.TfmApp._looks_textual(self._file(b"")))


class Navigation(unittest.TestCase):
    def test_go_to_hit_moves_pane_and_cursor(self):
        tmp = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp, "sub"))
            target = os.path.join(tmp, "sub", "hit.txt")
            open(target, "w").close()
            open(os.path.join(tmp, "sub", "other.txt"), "w").close()

            from puikit.backends import create_backend
            b = create_backend("memory"); b.open()
            app = tfm.TfmApp(b, tmp, tmp, left_provided=True, right_provided=True)
            try:
                app._go_to_content_hit({"path": Path(target), "line": 1, "text": "x"})
                pane = app.active_pane()
                self.assertEqual(str(pane["path"]), os.path.join(tmp, "sub"))
                self.assertEqual(pane["files"][pane["focused_index"]].name, "hit.txt")
            finally:
                app.file_monitor.stop_monitoring()
                b.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
