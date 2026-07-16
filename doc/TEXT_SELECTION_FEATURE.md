# Text Selection & Clipboard Copy

## Overview

TFM's file viewers let you **select text with the mouse and copy it to the
clipboard**. This works in both viewer modes:

- the **raw text viewer** (any file), and
- the **Markdown viewer** (the rendered view of a `.md` file).

When you copy from the Markdown viewer, the copy is **rich text**: paste it into
a formatting-aware app (Notes, Mail, TextEdit, Word, Pages, …) and the bold,
italics, inline code, links and headings come across intact. Paste into a plain
editor and you get the plain text.

## Selecting text

| Gesture | Selects |
|---------|---------|
| Click & drag | An arbitrary range from where you press to where you release |
| Double-click | The whole word under the pointer |
| Triple-click | The whole line under the pointer |
| Drag after a double/triple click | Extends by whole words / lines |
| Shift-click | Extends the current selection to the click |
| `Cmd`/`Ctrl` + `A` | Selects the entire document |

The highlighted range tracks the pointer as you drag, and the selection survives
scrolling — scroll away and back and it is still there.

## Copying

Press **`Cmd`+`C`** (macOS) or **`Ctrl`+`C`** (Linux/Windows) to copy the
selection.

- **Raw text viewer** — copies the selected source text exactly (each display
  line as its own line).
- **Markdown viewer** — copies **plain text and rich HTML** at once. The target
  app decides which it wants: a rich editor keeps the formatting, a plain one
  takes the text.

### What the Markdown rich copy preserves

- **Bold**, *italic*, ~~strikethrough~~ and underline
- `inline code`
- Links (the link text stays clickable, pointing at the same URL)
- Heading levels (`#`, `##`, … become real headings on paste)
- **Tables** — a selection that crosses a table copies as a real table. Paste into
  a document and you get a formatted table; paste into a spreadsheet or a plain
  editor and you get tab-separated columns. You can select whole tables or just
  part of a cell.

Selecting part way through a paragraph (or a table cell) copies exactly what you
see, formatting and all.

## Notes & limits

- Selection in the Markdown viewer covers prose, headings, lists, fenced code and
  tables. Images are not part of a text selection.
- On a terminal, whether the copy reaches your **system** clipboard depends on
  the terminal supporting the OSC 52 clipboard escape (most modern terminals do;
  the copy also always works for pasting back inside TFM). Rich HTML is a
  desktop-app feature — a terminal copy is plain text.
- Clicking a link in the Markdown viewer still opens it; a *drag* that ends on a
  link selects text instead of opening it.

## Related

- [Built-in Viewer Association](BUILTIN_VIEWER_ASSOCIATION_FEATURE.md) — how a
  file type picks the raw vs. rich viewer.
- Developer notes: `doc/dev/TEXT_SELECTION_IMPLEMENTATION.md`.
