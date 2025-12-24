# Dual-Pane File Management

## Overview

TFM uses a dual-pane interface that allows you to work with two directories simultaneously. This makes file operations like copying and moving between directories much more efficient.

## Key Concepts

### Active and Inactive Panes

- **Active Pane** - The pane you're currently working in (highlighted)
- **Inactive Pane** - The other pane (dimmed)
- **Tab Key** - Switch between panes

### Pane Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Left Pane (Active)        │ Right Pane (Inactive)           │
│                            │                                 │
│ file1.txt                  │ document.pdf                    │
│ file2.txt                  │ image.png                       │
│ directory/                 │ folder/                         │
│                            │                                 │
├─────────────────────────────────────────────────────────────┤
│ Log Pane                                                     │
└─────────────────────────────────────────────────────────────┘
```

## Key Bindings

### Pane Navigation

- **Tab** - Switch active pane
- **o** - Sync current pane directory to other pane
- **O** (Shift+o) - Sync other pane directory to current pane

### Pane Size Adjustment

- **[** - Make left pane smaller (move boundary left)
- **]** - Make left pane larger (move boundary right)

## Features

### Independent Navigation

Each pane maintains its own:
- Current directory
- Cursor position
- File selection
- Sort mode
- Filter settings
- Directory history

### Pane Synchronization

#### Sync Current to Other (o)

Copies the current pane's directory to the other pane:

```
Before:
Left: /home/user/documents    Right: /home/user/downloads

Press 'o' in left pane:

After:
Left: /home/user/documents    Right: /home/user/documents
```

#### Sync Other to Current (O)

Copies the other pane's directory to the current pane:

```
Before:
Left: /home/user/documents    Right: /home/user/downloads

Press 'O' (Shift+o) in left pane:

After:
Left: /home/user/downloads    Right: /home/user/downloads
```

### Cross-Pane Operations

Many operations work between panes:

- **Copy (c/C)** - Copy selected files to other pane's directory
- **Move (m/M)** - Move selected files to other pane's directory
- **Compare (w/W)** - Compare files between panes

## Usage Patterns

### Copying Files Between Directories

1. Navigate left pane to source directory
2. Navigate right pane to destination directory
3. Select files in left pane (Space key)
4. Press **c** or **C** to copy to right pane

### Moving Files

1. Navigate panes to source and destination
2. Select files in source pane
3. Press **m** or **M** to move to other pane

### Comparing Directories

1. Navigate both panes to directories you want to compare
2. Press **w** or **W** to open compare selection menu
3. Choose comparison option:
   - Files in current pane not in other
   - Files in other pane not in current
   - Files in both panes
   - Directories

### Working with Same Directory

Sometimes you want both panes in the same directory:

1. Navigate one pane to desired directory
2. Press **o** to sync other pane
3. Now both panes show the same directory
4. Useful for: Selecting files, viewing different parts of large directory

## Pane Size Adjustment

### Adjusting Pane Boundary

The vertical boundary between panes can be adjusted:

- **[** - Move boundary left (left pane smaller, right pane larger)
- **]** - Move boundary right (left pane larger, right pane smaller)

**Tips:**
- Adjust based on filename lengths
- Make active pane larger for better visibility
- Pane ratio is saved and restored on restart

### Default Pane Ratio

Configure the default pane ratio in `~/.tfm/config.py`:

```python
DEFAULT_LEFT_PANE_RATIO = 0.5  # 50/50 split (default)
# DEFAULT_LEFT_PANE_RATIO = 0.6  # 60/40 split (left pane larger)
# DEFAULT_LEFT_PANE_RATIO = 0.4  # 40/60 split (right pane larger)
```

## State Persistence

TFM remembers pane state between sessions:

- Current directory in each pane
- Cursor position in each directory
- Pane ratio (boundary position)
- Active pane

**State File:** `~/.tfm/state.json`

## Command Line Arguments

Set initial directories for each pane:

```bash
# Set left pane directory
tfm --left /path/to/directory

# Set right pane directory
tfm --right /path/to/directory

# Set both panes
tfm --left /home/user/documents --right /home/user/downloads
```

## Visual Indicators

### Active Pane

- Brighter colors
- Highlighted border (if supported)
- Cursor visible

### Inactive Pane

- Dimmed colors
- No cursor
- Still shows file list

### Pane Boundary

- Vertical line separating panes
- Can be adjusted with [ and ] keys

## Tips and Tricks

### Quick Directory Comparison

1. Navigate both panes to related directories
2. Use **w** to select files unique to each pane
3. Copy or move to synchronize directories

### Efficient File Organization

1. Left pane: Source directory (unsorted files)
2. Right pane: Destination directory (organized)
3. Select and move files to organize

### Backup Workflow

1. Left pane: Original files
2. Right pane: Backup location
3. Select all files (a key)
4. Copy to backup (c key)

### Working with Archives

1. Left pane: Regular filesystem
2. Right pane: Navigate into archive (archive://...)
3. Copy files from archive to filesystem

### S3 Integration

1. Left pane: Local filesystem
2. Right pane: S3 bucket (s3://bucket/path)
3. Copy files between local and cloud storage

## Troubleshooting

### Panes Show Same Directory Unexpectedly

**Problem:** Both panes show the same directory after restart

**Cause:** State persistence restored both panes to same directory

**Solution:** Navigate one pane to different directory, or use --left/--right arguments

### Can't Switch Panes

**Problem:** Tab key doesn't switch panes

**Solution:** Ensure you're not in a dialog or input mode (press Escape first)

### Pane Boundary Won't Move

**Problem:** [ and ] keys don't adjust pane boundary

**Solution:** Check if keys are bound to other actions in your config

### Lost Cursor Position

**Problem:** Cursor position not restored after restart

**Solution:** Check state file exists: `~/.tfm/state.json`

## Related Features

- **File Operations** - Copy, move, delete between panes
- **Selection System** - Select files for operations
- **Compare Selection** - Compare files between panes
- **State Persistence** - Save and restore pane state

## See Also

<!-- TODO: Create FILE_OPERATIONS_FEATURE.md -->
<!-- - File Operations Feature -->
<!-- TODO: Create SELECTION_FEATURE.md -->
<!-- - Selection Feature -->
<!-- TODO: Create COMPARE_SELECTION_FEATURE.md -->
<!-- - Compare Selection Feature -->
<!-- TODO: Create STATE_PERSISTENCE_FEATURE.md -->
<!-- - State Persistence Feature -->
