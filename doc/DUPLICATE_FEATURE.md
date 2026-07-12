# Duplicate Feature

Make an in-place copy of a file or directory — TFM's equivalent of Finder's
**Duplicate** (⌘D). The copy lands in the **same directory** as the original,
automatically renamed so it never collides.

## How to use it

Select one or more items (or just place the cursor on one), then choose
**Duplicate** from either:

- the **File** menu in the menu bar, or
- the **right-click context menu** on a file row.

TFM confirms once (see [Confirmation](#confirmation)), then creates the copies.
When nothing is explicitly selected, the entry under the cursor is duplicated;
after the operation the cursor lands on the new copy.

There is **no default keyboard shortcut**. To add one, bind the
`duplicate_files` action in your config, e.g.:

```python
KEY_BINDINGS['duplicate_files'] = ['Shift-D']
```

## Naming

Duplicates use the same ` (N)` scheme as "Keep both" conflict resolution:

| Original            | Duplicate            | Next duplicate         |
|---------------------|----------------------|------------------------|
| `report.pdf`        | `report (1).pdf`     | `report (2).pdf`       |
| `photos` (folder)   | `photos (1)`         | `photos (2)`           |
| `.bashrc` (dotfile) | `.bashrc (1)`        | `.bashrc (2)`          |
| `archive.tar.gz`    | `archive.tar (1).gz` | `archive.tar (2).gz`   |

The suffix is inserted before the last extension for files and appended for
directories and extension-less names.

## Duplicating via same-directory copy

**Copy to Other Pane** (`C`) also duplicates now: when both panes show the same
directory, copying no longer errors with "source and destination are the same
directory" — it auto-renames exactly like Duplicate. (Move still refuses a
same-directory target.)

## Confirmation

Duplicating shows a confirmation dialog by default. Turn it off for instant,
Finder-like behavior:

```python
CONFIRM_DUPLICATE = False   # default: True
```

Directories are duplicated recursively, so the confirmation is a useful guard
against duplicating a large tree by accident.

## Notes and limits

- **Read-only archives**: you cannot duplicate into a browsed archive.
- **Search-results (virtual) panes**: Duplicate is unavailable — those results
  span many directories, so there is no single place to write the copy.
- Large files show the usual byte-level progress and can be cancelled mid-copy.
