# Background Animations Feature

## Overview

A theme can draw a slow animated scene *behind* the file panes. The animation is
rendered under the whole UI and shows through wherever the interface is not fully
opaque, so it reads as a living wallpaper rather than as decoration on top of your
files.

Animations are drawn in **your theme's own colours** — the line colour comes from
the theme foreground and the backdrop from the theme background — so a scene stays
on-palette whichever theme (or custom palette) you use.

> **GUI backend only.** Animations need real pixels. They are rendered by the
> desktop backend (`tfm.py --backend gui` on macOS/Windows). In a terminal there
> are no sub-cell pixels to draw into, so the setting is silently ignored and you
> simply get the theme's plain background colour.

## Available animations

| Name | What it looks like |
|------|--------------------|
| `starfield` | Stars streaming toward you out of a vanishing point, drawn as motion streaks that lengthen and brighten as they approach. |
| `rain` | Falling streaks with fading tails, each column at its own speed — the classic phosphor-terminal rain. |
| `constellation` | Slowly drifting points that link to their near neighbours, the links fading in and out as points pass. |
| `grid` | Flying down a wireframe corridor — floor, ceiling and both walls gridded, converging on a vanishing point that wanders as the camera slowly drifts and turns. |
| `wave` | A dense field of particles flowing over a rolling wave surface, with a colour gradient sweeping along it. Drawn on the GPU — see the note below. |

The UI toolkit's own `cube` (a spinning wireframe) also works. It exists as a
reference scene for the rendering path rather than as a finished look.

### `wave` is drawn differently

Most animations are drawn line by line on the CPU, which puts a ceiling on how
much they can draw and means the whole scene is one colour — your theme's
foreground. `wave` is a **GPU shader** instead: it is computed for every pixel on
the graphics card, so it can be far denser and can use a real colour gradient
(the gradient is still derived from your theme's foreground, so it stays in
family with your palette).

The practical differences:

- It needs **macOS desktop mode with Metal**. On Windows, in a terminal, or
  anywhere Metal is unavailable, it draws nothing and you get the plain theme
  background — the other four animations work everywhere the GUI backend does.
- It is rendered at half resolution and scaled up. This is invisible for a soft,
  diffuse scene and keeps it affordable on a Retina display.

## Turning one on

Animations are chosen per theme. Among the built-in themes, **Sci-Fi** ships with
the starfield; select it from **View → Theme** or cycle themes with `T`.

To use one in your own theme, add an `animation` key to a theme in the `THEMES`
dict in `~/.tfm/config.py`:

```python
THEMES = {
    'Deep Space': {
        'base': 'Dark+',
        'animation': 'starfield',
        'opacity': 0.6,          # let the scene show through the panes
    },
}
```

### `opacity` — letting the animation show through

An animation is drawn *behind* the UI, so with a fully opaque interface you would
only see it in whatever gaps the layout leaves. The theme's `opacity` value (0–1)
controls how opaque the pane and row backgrounds are; lower it and the scene
becomes visible through them.

- `1.0` — fully opaque UI (default). The animation is essentially hidden.
- `0.6` — a good starting point: the scene reads clearly, text stays crisp.
- `0.3` — very translucent; atmospheric, but check legibility with your palette.

Text, outlines and dialog boxes always stay opaque, so lowering `opacity` does not
make the interface unreadable.

### It stops when you're not using it

An animation that ran forever would keep your machine busy — and drain the
battery — while you were reading something else. So it doesn't:

- After about 15 seconds without input, or as soon as TFM loses focus, the
  animation **very gradually slows to a stop**, taking a further 40 seconds or so
  to wind down. The slowing is deliberately too gentle to notice — an abrupt halt
  would catch the eye as much as the movement does.
- The scene stays on screen, frozen, rather than disappearing.
- The moment you press a key or move the mouse, it **eases back up to speed**.
- It resumes from exactly where it stopped. Leave TFM alone for an hour and the
  wave picks up where you left it, instead of jumping to wherever it "would have"
  been.

There is nothing to configure and no interruption to what you're doing — while
parked, TFM uses no more power than it would with a plain background.

### Tuning speed and strength

Give `animation` a dict instead of a name to adjust it:

```python
'animation': {'type': 'rain', 'speed': 1.0, 'opacity': 0.8},
```

| Key | Meaning |
|-----|---------|
| `type` | Which animation (see the table above). |
| `speed` | Motion-rate multiplier. `1.0` is the tuned look; TFM's default is `0.6`. `0` freezes the scene. |
| `opacity` | How strongly the scene's *lines* are drawn, 0–1. Not to be confused with the theme-level `opacity`, which is about the UI on top of it. |
| `color` | Line colour, if you want something other than the theme foreground. |

All animations are deliberately slow and understated — they sit behind a working
file manager, so they are tuned to stay in the background rather than compete with
filenames for attention. Raising `speed` much above `1.0` works, but is likely to
be distracting during real use.

## Using an image instead

The background can be a static image rather than an animation — see the
`wallpaper` key in the theme documentation. A theme has one background: naming
both `wallpaper` and `animation` uses the wallpaper.

## See also

- [Color Schemes](COLOR_SCHEMES_FEATURE.md) — themes, palettes and screen effects
- [Configuration](CONFIGURATION_FEATURE.md) — where `~/.tfm/config.py` lives and how themes are defined
- [Developer notes](dev/BACKGROUND_ANIMATIONS_IMPLEMENTATION.md) — how a scene is defined and how to add one
