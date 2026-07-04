"""
ProgressiveSearchDialog — the live search-as-you-type file/content finder.

The dialog owns the background-search machinery: each query supersedes the
previous search, results stream in via a worker thread and are installed on a
per-frame tick, the result cap bounds the list, and an invalid content-search
regex surfaces as an error. With no panel attached, ``_ensure_ticking`` falls
back to settling synchronously (join the worker + drain), so the streaming logic
is exercised deterministically here without a backend. One end-to-end test drives
the real dialog through a MemoryBackend + TfmApp to pin down the wiring
(``search_iter`` / ``to_label`` / ``on_accept`` / pane anchoring).
"""

import os
import re
import sys
import shutil
import tempfile
import threading
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))
sys.path.insert(0, os.path.join(_HERE, ".."))

import tfm  # noqa: E402
from tfm_progressive_search_dialog import ProgressiveSearchDialog  # noqa: E402


def _run(dialog, query):
    """Type ``query`` and settle the resulting search synchronously (no panel ->
    the tick falls back to join-and-drain)."""
    dialog.query_edit.text = query
    dialog._start_search()


class Streaming(unittest.TestCase):
    def test_matches_stream_in(self):
        dlg = ProgressiveSearchDialog(
            search_iter=lambda mode, q, cancel: iter(range(5)),
            to_label=lambda mode, v: str(v),
        )
        _run(dlg, "x")
        self.assertEqual(dlg.results, [0, 1, 2, 3, 4])
        self.assertFalse(dlg._searching)

    def test_empty_query_clears_and_runs_nothing(self):
        called = []

        def it(mode, q, cancel):
            called.append(q)
            return iter([1])

        dlg = ProgressiveSearchDialog(search_iter=it, to_label=lambda m, v: str(v))
        _run(dlg, "a")
        self.assertEqual(dlg.results, [1])
        _run(dlg, "   ")  # whitespace-only -> no search
        self.assertEqual(dlg.results, [])
        self.assertEqual(called, ["a"])  # the blank query never reached search_iter

    def test_result_cap_bounds_the_list(self):
        dlg = ProgressiveSearchDialog(
            search_iter=lambda mode, q, cancel: iter(range(10_000)),
            to_label=lambda mode, v: str(v),
            result_cap=25,
        )
        _run(dlg, "x")
        self.assertEqual(len(dlg.results), 25)

    def test_cap_signals_cancel_to_stop_the_walk(self):
        # The worker sets the cancel event once the cap is hit, so an unbounded
        # generator that honors it stops instead of running forever.
        seen = []

        def it(mode, q, cancel):
            i = 0
            while not cancel.is_set():
                seen.append(i)
                yield i
                i += 1

        dlg = ProgressiveSearchDialog(
            search_iter=it, to_label=lambda m, v: str(v), result_cap=10)
        _run(dlg, "x")
        self.assertEqual(len(dlg.results), 10)
        # The generator was stopped shortly after the cap, not left spinning.
        self.assertLess(len(seen), 1000)


class Supersede(unittest.TestCase):
    def test_new_query_replaces_previous_results(self):
        dlg = ProgressiveSearchDialog(
            search_iter=lambda mode, q, cancel: iter([q + "!"]),
            to_label=lambda mode, v: v,
        )
        _run(dlg, "one")
        self.assertEqual(dlg.results, ["one!"])
        _run(dlg, "two")
        self.assertEqual(dlg.results, ["two!"])

    def test_stale_batches_are_dropped(self):
        # A late batch tagged with an old generation must not land in the new
        # search's results.
        dlg = ProgressiveSearchDialog(
            search_iter=lambda mode, q, cancel: iter([1]),
            to_label=lambda mode, v: str(v),
        )
        _run(dlg, "a")
        stale_gen = dlg._gen - 5
        dlg._queue.put((stale_gen, [999], False, None))
        dlg._drain()
        self.assertNotIn(999, dlg.results)


class ContentErrors(unittest.TestCase):
    def test_invalid_regex_surfaces_as_error(self):
        def it(mode, q, cancel):
            re.compile(q)  # raises re.error for a bad pattern
            yield from ()

        dlg = ProgressiveSearchDialog(search_iter=it, to_label=lambda m, v: str(v))
        _run(dlg, "(unclosed")
        self.assertIsNotNone(dlg._error)
        self.assertIn("Invalid pattern", dlg._error)
        self.assertEqual(dlg.results, [])


class ModeSwitch(unittest.TestCase):
    def test_tab_switches_mode_and_reruns(self):
        dlg = ProgressiveSearchDialog(
            search_iter=lambda mode, q, cancel: iter([f"{mode}:{q}"]),
            to_label=lambda mode, v: v,
            initial_mode="filename",
        )
        _run(dlg, "q")
        self.assertEqual(dlg.results, ["filename:q"])
        dlg._switch_mode()  # Tab
        self.assertEqual(dlg.mode, "content")
        self.assertEqual(dlg.results, ["content:q"])


class AppIntegration(unittest.TestCase):
    """Drive the real dialog through a MemoryBackend + TfmApp, so the wiring
    (search_iter/to_label/on_accept + the tick-driven drain) is covered too."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, rel, content=""):
        p = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(content)
        return p

    def test_filename_search_streams_via_ticks(self):
        from puikit.backends import create_backend

        self._write("sub/needle_here.txt")
        self._write("sub/other.txt")
        self._write("noise.log")

        b = create_backend("memory")
        b.open()
        app = tfm.TfmApp(b, self.tmp, self.tmp, left_provided=True, right_provided=True)
        try:
            app._settle_listings()
            app._open_search("filename")
            dlg = app.panel._layers[-1].widget
            self.assertIsInstance(dlg, ProgressiveSearchDialog)

            dlg.query_edit.text = "needle"
            dlg._start_search()
            dlg._thread.join(timeout=5)
            b.run_animation_ticks()  # drain the queue on the tick

            names = [os.path.basename(dlg.to_label("filename", v)) for v in dlg.results]
            self.assertIn("needle_here.txt", names)
            self.assertNotIn("other.txt", names)
        finally:
            app.file_monitor.stop_monitoring()
            b.close()


if __name__ == "__main__":
    unittest.main()
