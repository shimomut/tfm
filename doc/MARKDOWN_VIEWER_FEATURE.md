# Markdown Viewer

TFM's built-in file viewer can render Markdown files (`*.md`, `*.markdown`) as
formatted rich text — headings, **bold** / *italic*, `code`, lists, tables,
block quotes, links and images — in addition to the usual raw, line-numbered
text view.

## Opening a file

Press **V** on a Markdown file (or any text file) to open the viewer. It always
opens in the **raw text** view first, exactly like any other file, with line
numbers, syntax highlighting, incremental search and line wrapping.

## Switching to the rendered view

When the file has a rendered view available (today: Markdown), press **M** to
toggle between:

- **Raw text** — the source, with line numbers and search.
- **Rendered** — the formatted document.

Press **M** again to switch back. The two views are independent: each remembers
where you had scrolled to, so toggling back and forth returns you to where you
were in each.

The footer shows which key toggles the view, and the top-right of the header
shows the current view (the line position in raw text, or the renderer's name —
e.g. *Markdown* — when rendered).

Files with no rendered view (a `.txt`, a `.py`, …) simply have nothing to toggle
to; **M** does nothing there.

## Navigating the rendered view

| Key | Action |
|-----|--------|
| ↑ / ↓ | Scroll a line |
| PgUp / PgDn | Scroll a page |
| Home / End | Jump to top / bottom |
| Mouse wheel | Scroll |
| **M** | Switch back to raw text |
| **?** | Key help |
| **Q** / Esc | Close the viewer |

Incremental search (**F**) and line wrap (**W**) apply to the **raw text** view.
To search within a Markdown file, switch to raw text first.

## Notes

- The rendered view follows the active theme and works on both the terminal and
  the native (macOS / Windows) backends — on the terminal, headings and emphasis
  render as bold/italic; on a graphical backend they render as proportional text
  at their true sizes, with real tables and images.
- More rendered viewers (for example JSON and CSV) are planned and will use the
  same **M** toggle when the file type supports them.
