# About Dialog Feature

## Overview

The About Dialog displays TFM application information with an animated Matrix-style background effect. It shows the TFM logo, version number, and GitHub repository URL.

## Features

- **ASCII Art Logo**: Large TFM logo displayed prominently
- **Version Information**: Current TFM version number
- **GitHub URL**: Link to the official repository
- **Matrix Animation**: Falling green zenkaku katakana characters in the background, inspired by the iconic "Matrix" movie visual effect
  - Uses authentic full-width Japanese katakana characters
  - Dense column layout (no spacing between columns)
  - Brightness gradient with brightest characters at the head (bottom) of each trail

## Accessing the About Dialog

### From Menu Bar (Desktop Mode)

1. **macOS**: Click "TFM" → "About TFM" in the menu bar
2. **Other platforms**: Click "Help" → "About TFM" in the menu bar

### Keyboard Shortcut

The About dialog can be accessed through the Help menu, which is typically bound to a keyboard shortcut depending on your platform.

## Using the About Dialog

- **Close the dialog**: Press any key, click the mouse button, or press ESC
- **View animation**: The Matrix-style falling characters animate continuously while the dialog is open

## Visual Design

The dialog features:
- Centered dialog box with border
- TFM ASCII art logo at the top
- Version number below the logo
- "Terminal File Manager" subtitle
- GitHub URL (underlined)
- Matrix-style green falling zenkaku katakana characters in the background
- Dense column layout for authentic Matrix look
- Brightness gradient with head (bottom) of trails being brightest
- Black background for optimal contrast

## Technical Details

- The Matrix animation runs at the application's frame rate
- Uses full-width katakana characters (zenkaku) for authentic Matrix aesthetic
- Each column of characters falls at a random speed
- Character brightness increases toward the head (bottom) of each trail
- Dense column layout with no spacing between columns
- The animation automatically adjusts to terminal resize events
