"""tfm_file_operations — shared copy / move / delete engine + progress dialog.

Both the main file-manager view (:class:`tfm.TfmApp`) and the directory diff
viewer (:class:`tfm_directory_diff_viewer.DirectoryDiffView`) run their file
operations through a single :class:`FileOperationService`, so the confirmation
policy (``CONFIRM_COPY`` / ``CONFIRM_MOVE`` / ``CONFIRM_DELETE``), the conflict
prompt, the background worker, and the animated modal progress dialog are
written once and shared rather than reimplemented per view.

The service is deliberately view-agnostic: it operates on an explicit list of
``Path`` targets plus a destination directory, and reports back through an
``on_complete`` callback (each view refreshes itself its own way — the panes
reload, the diff viewer rescans). A large operation runs on a worker thread and
drives a :class:`~tfm_progress_manager.ProgressManager`; a per-frame animation
tick reads that state on the main thread and repaints the :class:`ProgressDialog`
— the same worker + ``request_animation_ticks`` pattern the app uses for async
directory listings. Pass ``background=False`` (tests) to run inline and skip the
dialog, so an operation completes deterministically within the call.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Optional

from puikit.backend import DEFAULT_STYLE, Style, TextAttribute
from puikit.event import Event, EventType
from puikit.widgets import ProgressBar, show_message_box
from puikit.widgets.base import Widget

from tfm_path import Path
from tfm_progress_manager import OperationType, ProgressManager
from tfm_str_format import format_size


#: Operation kind -> (button/label verb, progress-manager op type).
_VERB = {"copy": "Copy", "move": "Move", "delete": "Delete"}
_OP_TYPE = {
    "copy": OperationType.COPY,
    "move": OperationType.MOVE,
    "delete": OperationType.DELETE,
}


def recursive_delete(entry: Path) -> None:
    """Delete a file or directory through the storage-agnostic Path API,
    recursing into directories (``copy_to`` / ``move_to`` handle their own
    recursion, but delete has no single primitive)."""
    if entry.is_dir() and not entry.is_symlink():
        for child in entry.iterdir():
            recursive_delete(child)
        entry.rmdir()
    else:
        entry.unlink()


class FileOperationService:
    """Runs copy / move / delete for any view. Construct once per owner (bound to
    that owner's ``config``); each call takes the ``panel`` to draw dialogs on and
    a ``z`` so a full-window modal (the diff viewer) can stack its dialogs above
    itself. One operation runs at a time per service instance."""

    def __init__(self, config: Any):
        self.config = config

    # --- public API ----------------------------------------------------------

    def copy(self, panel: Any, targets: list, dest_dir: Path, *,
             on_complete: Optional[Callable[[dict], None]] = None,
             log: Optional[Callable[[str], None]] = None,
             z: int = 70, background: bool = True) -> None:
        """Copy ``targets`` into ``dest_dir`` (each becomes ``dest_dir/name``),
        prompting per ``CONFIRM_COPY`` and on conflicts."""
        self._transfer(panel, "copy", targets, dest_dir, on_complete, log, z, background)

    def move(self, panel: Any, targets: list, dest_dir: Path, *,
             on_complete: Optional[Callable[[dict], None]] = None,
             log: Optional[Callable[[str], None]] = None,
             z: int = 70, background: bool = True) -> None:
        """Move ``targets`` into ``dest_dir``, prompting per ``CONFIRM_MOVE`` and
        on conflicts."""
        self._transfer(panel, "move", targets, dest_dir, on_complete, log, z, background)

    def delete(self, panel: Any, targets: list, *,
               on_complete: Optional[Callable[[dict], None]] = None,
               log: Optional[Callable[[str], None]] = None,
               z: int = 70, background: bool = True) -> None:
        """Delete ``targets`` (directories recursively), prompting per
        ``CONFIRM_DELETE`` (which defaults its confirm button to Cancel)."""
        if not targets:
            return
        names = ", ".join(t.name for t in targets[:3])
        if len(targets) > 3:
            names += f", … ({len(targets)} total)"

        def run() -> None:
            self._run(panel, "delete", targets, None, False, on_complete, log, z, background)

        if getattr(self.config, "CONFIRM_DELETE", True):
            def on_result(label: str) -> None:
                if label == "Delete":
                    run()
                else:
                    panel.render()
            show_message_box(
                panel, f"Delete {len(targets)} item(s)?\n{names}\nThis cannot be undone.",
                title="Delete", icon="warning", buttons=("Delete", "Cancel"),
                default=1, cancel=1, on_result=on_result, z=z)
            panel.render()
        else:
            run()

    # --- confirm flow --------------------------------------------------------

    def _transfer(self, panel: Any, kind: str, targets: list, dest_dir: Path,
                  on_complete, log, z: int, background: bool) -> None:
        """Shared copy/move confirm flow: detect conflicts, prompt (honouring the
        ``CONFIRM_*`` flag), then hand the run off to :meth:`_run`. A conflict
        always prompts (never silently overwrite) even when confirm is disabled;
        the buttons then choose the overwrite policy."""
        if not targets:
            return
        verb = _VERB[kind]
        conflicts = [t for t in targets if (dest_dir / t.name).exists()]
        message = f"{verb} {len(targets)} item(s) to {dest_dir}?"
        if conflicts:
            message += f"\n{len(conflicts)} already exist there."

        def run(overwrite: bool) -> None:
            self._run(panel, kind, targets, dest_dir, overwrite, on_complete, log, z, background)

        confirm = getattr(self.config, f"CONFIRM_{verb.upper()}", True)
        if conflicts:
            def on_result(label: str) -> None:
                if label == "Cancel":
                    panel.render()
                else:
                    run(overwrite=(label == "Overwrite"))
            show_message_box(
                panel, message, title=verb, icon="warning",
                buttons=("Overwrite", "Skip existing", "Cancel"),
                default=2, cancel=2, on_result=on_result, z=z)
            panel.render()
        elif confirm:
            def on_result(label: str) -> None:
                if label == verb:
                    run(overwrite=False)
                else:
                    panel.render()
            show_message_box(
                panel, message, title=verb, icon="info",
                buttons=(verb, "Cancel"), default=0, cancel=1, on_result=on_result, z=z)
            panel.render()
        else:
            run(overwrite=False)

    # --- execution -----------------------------------------------------------

    def _run(self, panel: Any, kind: str, targets: list, dest_dir: Optional[Path],
             overwrite: bool, on_complete, log, z: int, background: bool) -> None:
        """Execute the (already-confirmed) operation. In background mode the work
        runs on a daemon thread driving a :class:`ProgressManager`, and a per-frame
        tick pops the :class:`ProgressDialog` and fires ``on_complete`` on the main
        thread when it finishes. In synchronous mode (tests) the work runs inline
        and ``on_complete`` fires immediately — no dialog, no thread."""
        verb = _VERB[kind]
        progress = ProgressManager(self.config)
        progress.start_operation(_OP_TYPE[kind], len(targets), description="")
        result = {"done": 0, "skipped": 0, "failed": 0}
        cancel = threading.Event()

        def work() -> None:
            # Copy/move materialises the destination directory first (it may be a
            # mirrored subpath that doesn't exist yet on the other side); a no-op
            # when it already exists, as in the main view's other-pane case.
            if kind != "delete" and dest_dir is not None:
                try:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                except Exception:  # noqa: BLE001 — per-target copy will surface it
                    pass
            for t in targets:
                if cancel.is_set():
                    break
                progress.update_progress(t.name)
                try:
                    if kind == "delete":
                        recursive_delete(t)
                        result["done"] += 1
                        continue
                    dest = dest_dir / t.name
                    if dest.exists() and not overwrite:
                        result["skipped"] += 1
                        continue
                    if kind == "copy":
                        t.copy_to(dest, overwrite=overwrite,
                                  progress_callback=progress.update_file_byte_progress)
                    else:
                        t.move_to(dest, overwrite=overwrite)
                    result["done"] += 1
                except Exception as exc:  # noqa: BLE001 — report, keep going
                    result["failed"] += 1
                    progress.increment_errors()
                    if log is not None:
                        log(f"{verb} failed for {t.name}: {exc}")
            progress.finish_operation()

        if not background:
            work()
            if on_complete is not None:
                on_complete(result)
            return

        dialog = ProgressDialog(progress, f"{verb}…", on_cancel=cancel.set)
        dialog.show(panel, z=z)
        finished = threading.Event()

        def worker() -> None:
            try:
                work()
            finally:
                finished.set()

        threading.Thread(target=worker, name=f"tfm-op-{kind}", daemon=True).start()

        def tick() -> bool:
            # Main thread: repaint the live dialog; when the worker is done, pop it
            # and hand the summary back to the caller (so on_complete's UI work —
            # pane refresh / rescan / render — runs on the main thread).
            if not finished.is_set():
                panel.render()
                return True
            dialog.close()
            if on_complete is not None:
                on_complete(result)
            return False

        panel.request_animation_ticks(tick)


class ProgressDialog(Widget):
    """Modal progress dialog for a running file operation. Renders the operation
    verb, a determinate :class:`~puikit.widgets.progress_bar.ProgressBar`, the
    item count, and the current item; ``Esc`` requests cancellation. Construct via
    :meth:`show` (sizes and pushes the layer, centred with a shadow like a
    message box). The owning service repaints it each frame and pops it on
    completion."""

    focusable = True

    def __init__(self, progress: ProgressManager, title: str,
                 on_cancel: Optional[Callable[[], None]] = None):
        self.progress = progress
        self.title = title
        self._on_cancel = on_cancel
        self._bar = ProgressBar()
        self._panel: Any = None

    def show(self, panel: Any, z: int = 70) -> None:
        self._panel = panel
        sw, _sh = panel.backend.size_units
        w = float(max(40, min(64, int(sw) - 4)))
        h = 6.0
        panel.push_layer(self, z=z, hints={"shadow": True, "w": w, "h": h})
        panel.animate(self, hints={"transition": "fade", "duration_ms": 120})

    def close(self) -> None:
        panel = self._panel
        if panel is not None and panel.has_layers and panel._layers[-1].widget is self:
            panel.pop_layer()

    def draw(self, ctx) -> None:
        self._panel = ctx.panel
        theme = ctx.theme
        box_style = (Style(bg=theme.popup_bg, fg=theme.popup_border)
                     if theme is not None else DEFAULT_STYLE)
        surface_bg = theme.popup_bg if theme is not None else None
        box_w, box_h = ctx.size_units
        ctx.draw_box(0, 0, box_w, box_h, box_style, hints={"fill": True})
        title_style = Style(bg=surface_bg, attr=TextAttribute.BOLD)
        text_style = Style(bg=surface_bg)
        ctx.draw_text(2, 0.5, self.title, title_style)
        # Determinate bar spanning the box, one row up from the status line.
        self._bar.value = self.progress.get_progress_percentage() / 100.0
        ctx.draw_child(self._bar, 2, box_h - 2.5, max(1.0, box_w - 4), 1.0)
        ctx.draw_text(2, box_h - 1.4, self._status_line(int(box_w) - 4), text_style)

    def _status_line(self, max_width: int) -> str:
        """One-line readout: ``processed/total`` plus the current item (with byte
        progress for a large file), elided to the box width."""
        op = self.progress.get_current_operation()
        if not op:
            return ""
        line = f"{op['processed_items']}/{op['total_items']}"
        item = op.get("current_item")
        if item:
            line += f"  {item}"
        bc, bt = op.get("file_bytes_copied", 0), op.get("file_bytes_total", 0)
        if bt > 1024 * 1024 and bc > 0:
            line += f"  [{format_size(bc, compact=True)}/{format_size(bt, compact=True)}]"
        return line[:max_width] if max_width > 0 else ""

    def handle_event(self, event: Event) -> bool:
        if event.type is EventType.KEY and event.key == "escape":
            if self._on_cancel is not None:
                self._on_cancel()
        return True  # modal: swallow everything else
