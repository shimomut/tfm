"""Tests for the shared file-operation engine (tfm_file_operations) and the
central task system (tfm_task): recursive counting, per-file execution, the
TTK-style conflict resolution (skip / overwrite / keep-both + apply-to-all),
cancellation, and the worker↔main-thread UI bridge."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

import _config
import tfm_file_operations as F
from tfm_file_operations import FileOperationService, _unique_dest
from tfm_path import Path
from tfm_task import Cancelled, Task, TaskManager


def _P(p):
    return Path(str(p))


@pytest.fixture
def cfg():
    """Config with confirmation prompts off, so sync ops run without a panel."""
    c = _config.Config()
    c.CONFIRM_COPY = c.CONFIRM_MOVE = c.CONFIRM_DELETE = False
    return c


@pytest.fixture
def svc(cfg):
    return FileOperationService(cfg)


def _run_sync(svc, method, *args, **kw):
    """Invoke a service op synchronously and return its result dict."""
    result = {}
    method(None, *args, on_complete=lambda r: result.update(r), background=False, **kw)
    return result


# --- _unique_dest ------------------------------------------------------------

def test_unique_dest_free_name_unchanged(tmp_path):
    assert _unique_dest(_P(tmp_path), "new.txt").name == "new.txt"


def test_unique_dest_file_inserts_before_extension(tmp_path):
    (tmp_path / "foo.txt").write_text("x")
    assert _unique_dest(_P(tmp_path), "foo.txt").name == "foo (1).txt"
    (tmp_path / "foo (1).txt").write_text("x")
    assert _unique_dest(_P(tmp_path), "foo.txt").name == "foo (2).txt"


def test_unique_dest_multiple_dots_in_stem(tmp_path):
    # Only the last extension moves; dots in the stem stay put (the reported bug:
    # "Screenshot … 5.36.02 PM.png" must not become "… 5 (1).36.02 PM.png").
    name = "Screenshot 2026-06-27 at 5.36.02 PM.png"
    (tmp_path / name).write_text("x")
    assert _unique_dest(_P(tmp_path), name).name == "Screenshot 2026-06-27 at 5.36.02 PM (1).png"


def test_unique_dest_directory_appends(tmp_path):
    (tmp_path / "bar").mkdir()
    assert _unique_dest(_P(tmp_path), "bar", is_dir=True).name == "bar (1)"


def test_unique_dest_dotted_directory_appends(tmp_path):
    # A dotted directory name is not an extension — append, don't split.
    (tmp_path / "my.backup").mkdir()
    assert _unique_dest(_P(tmp_path), "my.backup", is_dir=True).name == "my.backup (1)"


def test_unique_dest_dotfile_appends(tmp_path):
    (tmp_path / ".bashrc").write_text("x")
    assert _unique_dest(_P(tmp_path), ".bashrc").name == ".bashrc (1)"


# --- synchronous copy / move / delete ---------------------------------------

def test_copy_tree_and_large_file(tmp_path, svc):
    src, dst = tmp_path / "s", tmp_path / "d"
    src.mkdir(); dst.mkdir()
    (src / "a.txt").write_text("hello")
    (src / "sub").mkdir()
    (src / "sub" / "big.bin").write_bytes(b"x" * (2 * 1024 * 1024))  # chunked path
    res = _run_sync(svc, svc.copy, [_P(src / "a.txt"), _P(src / "sub")], _P(dst))
    assert res == {"done": 2, "skipped": 0, "failed": 0, "cancelled": False}
    assert (dst / "a.txt").read_text() == "hello"
    assert (dst / "sub" / "big.bin").stat().st_size == 2 * 1024 * 1024


def test_move_same_storage_is_atomic(tmp_path, svc):
    src, dst = tmp_path / "s", tmp_path / "d"
    src.mkdir(); dst.mkdir()
    (src / "m.txt").write_text("move")
    res = _run_sync(svc, svc.move, [_P(src / "m.txt")], _P(dst))
    assert res["done"] == 1
    assert (dst / "m.txt").read_text() == "move"
    assert not (src / "m.txt").exists()


def test_delete_recurses(tmp_path, svc):
    d = tmp_path / "d"
    (d / "sub").mkdir(parents=True)
    (d / "sub" / "f.txt").write_text("x")
    res = _run_sync(svc, svc.delete, [_P(d / "sub")])
    assert res["done"] >= 1
    assert not (d / "sub").exists()


# --- conflict resolution -----------------------------------------------------

def test_conflict_headless_defaults_to_skip(tmp_path, svc):
    src, dst = tmp_path / "s", tmp_path / "d"
    src.mkdir(); dst.mkdir()
    (src / "c.txt").write_text("NEW")
    (dst / "c.txt").write_text("OLD")
    res = _run_sync(svc, svc.copy, [_P(src / "c.txt")], _P(dst))
    assert res["skipped"] == 1 and res["done"] == 0
    assert (dst / "c.txt").read_text() == "OLD"  # untouched


def _scripted_task(cfg, answers):
    """A Task whose ``ask`` yields the given (action, apply_to_all) answers."""
    task = Task("Copy…", config=cfg)
    seq = iter(answers)
    task.ask = lambda show_fn, headless: next(seq)  # type: ignore[assignment]
    return task


def test_resolve_overwrite(tmp_path, cfg, svc):
    src, dst = tmp_path / "s", tmp_path / "d"
    src.mkdir(); dst.mkdir()
    (src / "c.txt").write_text("x")
    (dst / "c.txt").write_text("old")
    task = _scripted_task(cfg, [("overwrite", False)])
    plan, skipped = svc._resolve(task, [_P(src / "c.txt")], _P(dst), 70, None)
    assert skipped == 0
    assert plan[0][1].name == "c.txt" and plan[0][2] is True  # overwrite flag set


def test_resolve_keep_both(tmp_path, cfg, svc):
    src, dst = tmp_path / "s", tmp_path / "d"
    src.mkdir(); dst.mkdir()
    (src / "c.txt").write_text("x")
    (dst / "c.txt").write_text("old")
    task = _scripted_task(cfg, [("keep_both", False)])
    plan, skipped = svc._resolve(task, [_P(src / "c.txt")], _P(dst), 70, None)
    assert plan[0][1].name == "c (1).txt" and plan[0][2] is False


def test_resolve_apply_to_all(tmp_path, cfg, svc):
    """A single answer with apply_to_all=True governs every later conflict; ask is
    called exactly once."""
    src, dst = tmp_path / "s", tmp_path / "d"
    src.mkdir(); dst.mkdir()
    names = ["a.txt", "b.txt", "c.txt"]
    for n in names:
        (src / n).write_text("new")
        (dst / n).write_text("old")
    calls = {"n": 0}
    task = Task("Copy…", config=cfg)

    def ask(show_fn, headless):
        calls["n"] += 1
        return ("skip", True)  # skip, apply to all remaining
    task.ask = ask  # type: ignore[assignment]
    plan, skipped = svc._resolve(task, [_P(src / n) for n in names], _P(dst), 70, None)
    assert calls["n"] == 1          # asked only for the first conflict
    assert skipped == 3 and plan == []


def test_resolve_cancel_raises(tmp_path, cfg, svc):
    src, dst = tmp_path / "s", tmp_path / "d"
    src.mkdir(); dst.mkdir()
    (src / "c.txt").write_text("x")
    (dst / "c.txt").write_text("old")
    task = _scripted_task(cfg, [("cancel", False)])
    with pytest.raises(Cancelled):
        svc._resolve(task, [_P(src / "c.txt")], _P(dst), 70, None)


# --- counting + cancellation -------------------------------------------------

def test_count_nodes_and_bytes(tmp_path, svc):
    root = tmp_path / "r"
    (root / "sub").mkdir(parents=True)
    (root / "f1").write_bytes(b"ab")
    (root / "sub" / "f2").write_bytes(b"abcd")
    task = Task("Copy…")
    # nodes = root dir + sub dir + f1 + f2 = 4; bytes = 2 + 4 = 6
    items, nbytes = svc._count(task, "copy", _P(tmp_path / "d"), [_P(root)])
    assert items == 4 and nbytes == 6
    assert task.counted == 4


def test_count_atomic_move_is_one_item(tmp_path, svc):
    root = tmp_path / "r"
    (root / "sub").mkdir(parents=True)
    (root / "sub" / "f").write_text("x")
    task = Task("Move…")
    items, _ = svc._count(task, "move", _P(tmp_path), [_P(root)])
    assert items == 1  # same-storage move = one atomic rename


def test_cancelled_before_run_reports_cancelled(tmp_path, svc):
    src, dst = tmp_path / "s", tmp_path / "d"
    src.mkdir(); dst.mkdir()
    (src / "a.txt").write_text("x")
    task = Task("Copy…", config=svc.config)
    task.request_cancel()  # cancel before it starts
    res = svc._run(task, "copy", [_P(src / "a.txt")], _P(dst), None, None, 70)
    assert res["cancelled"] is True
    assert not (dst / "a.txt").exists()


# --- TaskManager + UI bridge -------------------------------------------------

def test_manager_sync_submit_runs_inline():
    tm = TaskManager()
    task = Task("Job…")
    calls = {"done": None}

    def run(t):
        return {"done": 7, "skipped": 0, "failed": 0, "cancelled": False}
    tm.submit(task, None, run=run, on_done=lambda r: calls.update(done=r),
              background=False)
    assert calls["done"]["done"] == 7
    assert not tm.has_active()  # finished tasks are dropped from the registry


def test_ask_headless_returns_default():
    task = Task("Job…")
    task._headless = True
    assert task.ask(lambda p, d: None, headless=("skip", False)) == ("skip", False)


# --- background path: threaded worker + conflict dialog over the bridge -------

import time  # noqa: E402

from puikit import Event, EventType, Panel, PROFILE_GUI_DESKTOP  # noqa: E402
from puikit.backends.memory_backend import MemoryBackend  # noqa: E402


def _panel():
    backend = MemoryBackend(width=100, height=30, capabilities=PROFILE_GUI_DESKTOP)
    return backend, Panel(backend)


def _pump_until(backend, panel, pred, limit=400):
    """Run tick rounds until ``pred()`` or a bound is hit (guards against a hang)."""
    for _ in range(limit):
        backend.run_animation_ticks()
        if pred():
            return True
        time.sleep(0.002)
    return False


def _top(panel):
    return type(panel._layers[-1].widget).__name__ if panel._layers else None


def test_background_conflict_dialog_overwrite(tmp_path, cfg):
    src, dst = tmp_path / "s", tmp_path / "d"
    src.mkdir(); dst.mkdir()
    (src / "c.txt").write_text("NEW")
    (dst / "c.txt").write_text("OLD")
    backend, panel = _panel()
    svc = FileOperationService(cfg)
    done = {}
    svc.copy(panel, [_P(src / "c.txt")], _P(dst),
             on_complete=lambda r: done.update(r), background=True)

    assert _pump_until(backend, panel, lambda: _top(panel) == "ConflictDialog")
    panel.dispatch_event(Event(EventType.KEY, key="o", char="o", modifiers=set()))
    assert _pump_until(backend, panel, lambda: bool(done))
    assert done["done"] == 1
    assert (dst / "c.txt").read_text() == "NEW"  # overwritten
    assert panel._layers == []  # dialog torn down


def test_background_cancel_stops_and_cleans_up(tmp_path, cfg):
    src, dst = tmp_path / "s", tmp_path / "d"
    src.mkdir(); dst.mkdir()
    # Many files so the op is reliably still running when we request cancel.
    for i in range(400):
        (src / f"f{i:03d}.bin").write_bytes(b"x" * (256 * 1024))
    backend, panel = _panel()
    svc = FileOperationService(cfg)
    done = {}
    svc.copy(panel, [_P(src / n) for n in sorted(os.listdir(src))], _P(dst),
             on_complete=lambda r: done.update(r), background=True)

    assert _pump_until(backend, panel, lambda: _top(panel) == "ProgressDialog")
    # Request cancellation on the live task (same effect as the Esc→confirm path).
    active = svc.tasks.active_tasks()
    assert active, "expected a running task"
    active[0].request_cancel()
    assert _pump_until(backend, panel, lambda: bool(done))
    assert done["cancelled"] is True
    assert panel._layers == []           # progress dialog torn down
    assert not svc.tasks.has_active()    # task dropped from the registry
    # It stopped early — not every file made it across.
    assert len(os.listdir(dst)) < 400
