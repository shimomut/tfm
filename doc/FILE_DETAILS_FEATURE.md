# File Details (I Key)

Press **I** to open a scrollable dialog with detailed information about files and
directories.

## Usage

- **I** — show details
  - If files are selected, shows details for every selected item
  - If nothing is selected, shows details for the item under the cursor
- **↑/↓** — scroll line by line
- **Page Up/Down** — scroll by page
- **Home/End** — jump to top/bottom
- **Q** or **ESC** — close

## Information shown

### Files

- **Name** and full **path**
- **Type** — File / Directory / Symbolic Link / Special
- **Size** — human-readable (B, KB, MB, GB)
- **Timestamps** — last modified and last accessed
- **Permissions** — Unix-style `rwxrwxrwx`, plus owner and group
- **Symlink target** — for symbolic links

### Directories

Directories show the same timestamps and permissions, plus a contents summary
(number of subdirectories and files, counting only what you have permission to
read).

Example:

```
┌─────────────── Details: filename.txt ───────────────┐
│ File: filename.txt                                   │
│ Path: /home/user/documents/filename.txt              │
│ Type: File                                           │
│ Size: 1.2 MB                                          │
│ Modified: 2024-03-15 14:30:22                        │
│ Accessed: 2024-03-15 16:45:10                        │
│ Permissions: -rw-r--r--                              │
│ Owner: user:staff                                    │
└──────────────────────────────────────────────────────┘
```

When multiple items are selected, each one's details are listed in turn,
separated by dividers.

## Notes

- **Permission and access errors** are handled gracefully: unreadable symlink
  targets show as `<unreadable>`, and inaccessible directories show
  `<permission denied>` rather than failing.
- On **Windows**, owner/group fall back to numeric UID/GID.
- Works the same in both panes, and can inspect the results of a search or a
  multi-file selection (select with **Space** or **A** first).
