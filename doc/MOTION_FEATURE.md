# Motion & Pane Focus Chrome

TFM animates a few things on a GUI backend — dialogs arriving, the Sci-Fi theme's
starfield drifting behind the UI — and marks which file pane has focus. This page
covers what you see and how to change it.

---

## Dialogs

Every modal (input prompts, the filter and favorites pickers, batch rename, the
text / diff / directory-diff viewers) enters the same way: it grows from 92% to
full size while fading in, decelerating sharply and gliding to a stop.

Pickers take 180 ms, full-screen viewers 140 ms — viewers are usually opened
deliberately, and a shorter beat keeps them from feeling like they lag behind the
keystroke.

In a terminal there is no compositing, so the same intent plays as two frames —
one inset frame, then the finished box. Nothing is lost; the beat is just
coarser.

---

## Arriving text (Sci-Fi)

Under the **Sci-Fi** theme, text types itself into place as it arrives: a file
pane filling in left to right when you enter a directory, a dialog's labels
doing the same as it opens, and **each new line in the log pane** as it is
written. Every other theme draws text plainly.

It fires when something *arrives* — a new listing, a dialog, a fresh log line.
It deliberately does **not** fire while you scroll, or when a status value ticks
over, so it never sits between you and something you are reading. Scrolling back
over log lines you have already read leaves them alone.

### Choosing a different one

Four styles ship. Any theme can name one in your `config.py`:

```python
THEMES = {
    'Dracula': {
        'text_effect': 'decode',   # or 'typewriter', 'wipe', 'flicker'
        # ...or tune it:
        # 'text_effect': {'kind': 'typewriter', 'duration_ms': 300,
        #                 'stagger_ms': 12, 'max_strings': 40},
    },
}
```

- `typewriter` — characters appear left to right, nothing in the tail (the Sci-Fi default)
- `decode` — the un-revealed tail churns as junk glyphs until the reveal passes over it
- `wipe` — the tail is held open by a block glyph until it resolves
- `flicker` — the text is present but interferes, then settles

`duration_ms` is per string; `stagger_ms` cascades a pane's rows; `max_strings`
caps how many rows animate before the rest simply appear (so a long listing
does not cascade for seconds). A misspelled name turns the effect off rather
than breaking anything.

---

## Pane focus

Two cues mark which pane you are working in. Both are per-theme, and only the
Sci-Fi theme turns them on by default:

- **Corner brackets** frame the focused pane (GUI only — see below).
- The **resting pane's text recedes** slightly toward the pane background.

Filenames in the resting pane stay readable: the wash is applied before TFM's
legibility pass, which lifts any color pushed under the contrast floor back over
it. A theme cannot configure its resting pane into illegibility.

In a terminal the brackets are skipped. A character grid has no sub-cell room for
them, and reserving whole columns and rows for decoration would cost real listing
space — so terminal focus stays marked by the cursor cue, which is vivid on the
focused pane and muted on the resting one. The ink wash still applies, since a
color change costs no space.

### Turning them on for another theme

Both are plain theme data in your `config.py`:

```python
THEMES = {
    'Dracula': {
        # Brackets in the theme accent, default arm length:
        'pane_frame': True,
        # ...or spell it out:
        # 'pane_frame': {'color': (130, 205, 255), 'arm': 2, 'thickness': 1.0},

        # Default wash strength:
        'pane_dim': True,
        # ...or set your own, 0.0 (untouched) to 1.0 (invisible):
        # 'pane_dim': 0.15,
    },
}
```

---

## Reduced motion

To suppress decorative motion everywhere, set this in `config.py`:

```python
REDUCED_MOTION = True
```

With it on:

- dialogs appear at once instead of scaling in;
- text appears immediately instead of decoding in;
- an animated theme background (Sci-Fi's starfield) decelerates to a stop and
  holds a still frame;
- a CRT-style theme keeps its glow, scanlines and vignette — the screen still
  looks like a CRT — but the rolling band and flicker stop.

Everything lands in its **final** state, never frozen part-way, so nothing is
hidden by turning it on.

Worth knowing: this only affects decoration. Progress bars, file-list reloads,
search results and every other functional update keep running exactly as before.

It is also worth setting over a slow SSH link, where each animated frame is a
full screen repaint.
