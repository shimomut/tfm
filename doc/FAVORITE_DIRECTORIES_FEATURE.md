# Favorite Directories Feature

## Overview

The Favorite Directories feature lets you quickly jump to frequently used directories. Press 'J' to open a searchable list of your favorite directories and navigate to any of them instantly.

## What It Does

- **Quick Access**: Press 'J' to open your favorites
- **Searchable**: Type to find the directory you want
- **Instant Navigation**: Select a directory to go there immediately
- **Customizable**: Set up your own favorite directories
- **Smart**: Only shows directories that actually exist

## Default Favorites

TFM comes with these default favorites:
- **Home** - Your home directory
- **Documents** - Your Documents folder
- **Downloads** - Your Downloads folder
- **Desktop** - Your Desktop folder
- **Projects** - Your Projects folder (if it exists)
- **Root** - The root directory (/)
- **Temp** - Temporary files (/tmp)
- **Config** - Your config directory

## Customizing Your Favorites

Edit your `~/.tfm/config.py` file to add your own favorites:

```python
class Config:
    # Your favorite directories
    FAVORITE_DIRECTORIES = [
        {'name': 'Home', 'path': '~'},
        {'name': 'Work Projects', 'path': '~/work'},
        {'name': 'Personal Projects', 'path': '~/personal'},
        {'name': 'Scripts', 'path': '~/bin'},
        {'name': 'Web Server', 'path': '/var/www'},
        # Add your own here
    ]
```

### Format
Each favorite needs:
- **name**: What you want to call it
- **path**: Where it is (you can use `~` for your home directory)

### Changing the Key
If you don't like using 'J', you can change it:

```python
KEY_BINDINGS = {
    'favorites': ['f'],  # Use 'f' instead of 'J'
}
```

## How to Use

### Open Favorites
1. Press **J** (or your configured key)
2. A list of your favorites appears

### Navigate the List
- **↑/↓** arrows to move through the list
- **Page Up/Down** for fast scrolling
- **Home/End** to jump to first/last item
- **Type** to search for a specific directory
- **Backspace** to clear your search

### Go to a Directory
1. Press **Enter** to go to the selected directory
2. Press **ESC** to cancel and close the list

### What You'll See
The list shows each favorite like this:
```
Home (/Users/username)
Projects (/Users/username/Projects)
Web Server (/var/www)
```

## Benefits

- **Fast Navigation**: Jump to any directory instantly
- **No Manual Navigation**: Skip clicking through directory trees
- **Search Support**: Quickly find the directory you need
- **Persistent**: Your favorites are saved between sessions
- **Safe**: Only shows directories that actually exist

## Troubleshooting

### "No favorite directories configured"
- Check your `~/.tfm/config.py` file
- Make sure `FAVORITE_DIRECTORIES` is set up correctly

### Favorites not showing up
- Check that the directory paths actually exist
- Look for warning messages in the log pane
- Try the default favorites first

### Key binding not working
- Make sure you're pressing 'J' (capital J)
- Check if you changed the key binding in your config
- Try restarting TFM

## Example Setups

### Simple Setup
```python
# Basic favorites for everyday use
FAVORITE_DIRECTORIES = [
    {'name': 'Home', 'path': '~'},
    {'name': 'Projects', 'path': '~/dev'},
    {'name': 'Downloads', 'path': '~/Downloads'},
    {'name': 'Temp', 'path': '/tmp'},
]
```

### Power User Setup
```python
# More comprehensive favorites
FAVORITE_DIRECTORIES = [
    # Personal
    {'name': 'Home', 'path': '~'},
    {'name': 'Documents', 'path': '~/Documents'},
    {'name': 'Downloads', 'path': '~/Downloads'},
    
    # Development
    {'name': 'Projects', 'path': '~/projects'},
    {'name': 'Scripts', 'path': '~/bin'},
    
    # System
    {'name': 'Root', 'path': '/'},
    {'name': 'Config', 'path': '/etc'},
    {'name': 'Logs', 'path': '/var/log'},
    {'name': 'Temp', 'path': '/tmp'},
]
```

The Favorite Directories feature makes navigating your filesystem much faster and more efficient!