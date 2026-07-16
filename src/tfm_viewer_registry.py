"""Rich-viewer registry — maps a file's type to an optional *rich* (formatted)
rendering widget the modal file viewer can switch to, alongside its always-
available raw plain-text view.

Today only Markdown is registered (``*.md`` / ``*.markdown`` → PuiKit's
``MarkdownView``). This registry is the seam for future formatted viewers such
as JSON and CSV: each registers a :class:`RichRenderer` for its extensions and
the viewer's *toggle view mode* action picks it up with no other change. The raw
text view is the universal fallback, so an unregistered file type simply has
nothing to toggle to (:func:`rich_renderer_for` returns ``None``).

A renderer's ``build`` turns the file's raw source text into a scrollable PuiKit
:class:`~puikit.widgets.base.Widget`, styled onto the viewer's content surface so
the rendered document follows the active theme like the rest of TFM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from puikit.backend import Style
from puikit.widgets.base import Widget

from tfm_log_manager import getLogger

logger = getLogger("ViewerReg")


@dataclass(frozen=True)
class RichRenderer:
    """A named formatted renderer for one family of file types.

    ``name`` is the short label shown in the viewer chrome (e.g. ``"Markdown"``);
    ``build(source, *, style)`` turns the file's raw source text into a scrollable
    PuiKit widget drawn on ``style`` (the viewer's content surface)."""

    name: str
    build: Callable[..., Widget]


#: Extension (lower-cased, with leading dot) → the rich renderer for that type.
_REGISTRY: dict[str, RichRenderer] = {}


def register(renderer: RichRenderer, *suffixes: str) -> None:
    """Associate ``renderer`` with each lower-cased file ``suffix`` (``".md"`` …).
    Later registrations for the same suffix win, so a config could override a
    built-in renderer in the future."""
    for suffix in suffixes:
        _REGISTRY[suffix.lower()] = renderer


def rich_renderer_for(path: Any) -> RichRenderer | None:
    """The rich renderer registered for ``path``'s extension, or ``None`` when the
    type has only the raw text view (nothing to toggle to). ``path`` is any object
    exposing a ``suffix`` (``tfm_path.Path`` / ``pathlib.Path``)."""
    try:
        suffix = path.suffix.lower()
    except AttributeError:
        return None
    return _REGISTRY.get(suffix)


def _build_markdown(source: str, *, style: Style) -> Widget:
    """Build a PuiKit ``MarkdownView`` for ``source`` on the viewer's surface.
    Imported here (not at module load) so the registry stays cheap to import and
    free of any widget-import ordering concerns."""
    from puikit.widgets import MarkdownView

    # ``selectable`` turns on mouse text-selection + Cmd/Ctrl+C copy (plain text
    # plus rich HTML) in the file viewer; help / message popups build their own
    # MarkdownView without it, so those stay inert.
    return MarkdownView(source, style=style, selectable=True)


register(RichRenderer("Markdown", _build_markdown), ".md", ".markdown")
