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
| `wave` | A dense field of particles flowing over a rolling wave surface, with a colour gradient sweeping along it. |
| `datastream` | Horizontal telemetry traffic: layered rows of dashes streaming past at different rates, mostly short with the occasional long streak, each leading with a bright head and some ending in a small upright tick. Busy and quiet regions drift across the field. |
| `earth` | The planet seen from orbit, turning slowly. Dark glossy oceans that mirror the sun where it strikes them, matte continents banded between green and desert and shaded by their own terrain, a cloud deck riding above the surface — so it slides over the ground toward the limb and casts shadows that lengthen as the sun sinks — polar caps, and an atmosphere that runs from blue overhead to gold at the terminator, flaring where that gold band meets the edge. Clustered city lights come up on the night side. Stars behind it. |
| `hologram` | A depth of holographic panels drifting toward you, each a small flat readout — pseudo-text that types itself out left to right, bar and line charts, progress bars, ring gauges, wireframe meshes — struck here and there with a warm accent. Panels fade up, hold and vanish on their own clock as the field flies slowly past, with a fine haze of distant ones behind, a few thick speed streaks raking outward from the vanishing point, soft out-of-focus dots and strokes drifting slowly across it all, and bright traffic — barcode bursts, dashes and dots — running fast along horizontal lanes. |

The UI toolkit's own `cube` (a spinning wireframe) also works. It exists as a
reference scene for the rendering path rather than as a finished look.

### Where they run

Every scene is a **GPU shader**, computed for each pixel on the graphics card.
That is what lets them be dense, use real colour gradients rather than a single
flat line colour, and cost almost nothing while TFM sits idle — the graphics card
advances the scene behind the UI without TFM having to redraw the interface.

They need **desktop mode** (`tfm.py --backend gui`), on macOS or Windows. In a
terminal there are no pixels to draw into, so the `animation` key is ignored and
you get the plain theme background. The same is true on the rare desktop setup
with no usable GPU shader support.

## Turning one on

Animations are chosen per theme. Among the built-in themes, **Sci-Fi** ships with
the starfield, **Cyber** with the hologram, **Shinagawa** with the wave and **Earth**
with the planet; select one from **View → Theme** or cycle themes with `T`.

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
| `opacity` | How strongly the scene itself is drawn, 0–1. Not to be confused with the theme-level `opacity`, which is about the UI on top of it. |
| `color` | The colour the scene is built on, if you want something other than the theme foreground. Scenes anchor their own colouring on it rather than using it flat, so a scene with a gradient shifts with it instead of losing the gradient. |

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
