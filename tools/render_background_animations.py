"""Rasterize TFM's background animations to PNGs, to check how a scene actually
looks without launching the app.

The test suite checks invariants, not aesthetics, and TFM's TUI cannot be launched
non-interactively. This renders a frame the same way the macOS backend does —
clear to the theme backdrop, group segments by alpha, stroke each bucket in the
theme foreground at line width 1.5, flipped to a top-left origin — so what comes
out is what the app shows.

    PYTHONPATH=.:src python tools/render_background_animations.py
    PYTHONPATH=.:src python tools/render_background_animations.py --time 12 --out /tmp
    PYTHONPATH=.:src python tools/render_background_animations.py --kind starfield --size 1600x1000

Requires PyObjC (already a dependency of puikit's macOS backend); macOS only.
"""

import argparse
import os
import sys

try:
    import Quartz
    from Quartz import CGBitmapContextCreate, CGColorSpaceCreateDeviceRGB
except ImportError:  # pragma: no cover - developer tool, macOS only
    sys.exit("This tool needs PyObjC (macOS only): pip install pyobjc-framework-Quartz")

from puikit.background import ANIMATIONS, group_by_alpha

import tfm_background_animations  # noqa: F401  (import registers the scenes)

#: Matches _BG3D_LINE_WIDTH in puikit's macOS backend.
LINE_WIDTH = 1.5

#: Theme colors to render against, so a scene is judged on the palette it ships
#: with rather than an arbitrary one. (foreground, background) per TFM theme.
THEMES = {
    "sci-fi": ((200, 224, 245), (16, 30, 50)),
    "phosphor": ((51, 245, 121), (4, 15, 7)),
    "dark": ((212, 212, 212), (30, 30, 30)),
}

#: Which theme suits each scene, used when --theme is not given.
SCENE_THEME = {"starfield": "sci-fi", "rain": "phosphor",
               "constellation": "sci-fi", "grid": "sci-fi"}


def render(kind, width, height, t, *, speed, opacity, theme, path):
    """Draw one frame of ``kind`` to a PNG at ``path``; returns (segments, strokes)."""
    fg, bg = THEMES[theme]
    ctx = CGBitmapContextCreate(None, width, height, 8, 0,
                                CGColorSpaceCreateDeviceRGB(),
                                Quartz.kCGImageAlphaPremultipliedLast)
    Quartz.CGContextSetRGBFillColor(ctx, *[c / 255.0 for c in bg], 1.0)
    Quartz.CGContextFillRect(ctx, Quartz.CGRectMake(0, 0, width, height))
    Quartz.CGContextSetLineWidth(ctx, LINE_WIDTH)
    Quartz.CGContextSetLineJoin(ctx, Quartz.kCGLineJoinRound)

    segments = ANIMATIONS[kind](width, height, t, speed=speed)
    buckets = group_by_alpha(segments)
    fr, fg_, fb = [c / 255.0 for c in fg]
    for alpha, group in buckets:
        Quartz.CGContextSetRGBStrokeColor(ctx, fr, fg_, fb, opacity * alpha)
        Quartz.CGContextBeginPath(ctx)
        for s in group:
            # The backend draws into a flipped (top-left origin) view; CoreGraphics
            # is bottom-left, so flip y to match what the app actually shows.
            Quartz.CGContextMoveToPoint(ctx, s[0], height - s[1])
            Quartz.CGContextAddLineToPoint(ctx, s[2], height - s[3])
        Quartz.CGContextStrokePath(ctx)

    image = Quartz.CGBitmapContextCreateImage(ctx)
    url = Quartz.CFURLCreateWithFileSystemPath(None, path, Quartz.kCFURLPOSIXPathStyle, False)
    dest = Quartz.CGImageDestinationCreateWithURL(url, "public.png", 1, None)
    Quartz.CGImageDestinationAddImage(dest, image, None)
    if not Quartz.CGImageDestinationFinalize(dest):
        raise RuntimeError(f"could not write {path}")
    return len(segments), len(buckets)


def _size(text):
    try:
        w, h = text.lower().split("x")
        return int(w), int(h)
    except ValueError:
        raise argparse.ArgumentTypeError("size must look like 1200x800")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--kind", action="append", choices=sorted(ANIMATIONS),
                        help="animation to render (repeatable; default: all of TFM's)")
    parser.add_argument("--size", type=_size, default=(900, 600), help="WxH, default 900x600")
    parser.add_argument("--time", type=float, default=6.0, help="scene time in seconds")
    parser.add_argument("--speed", type=float, default=0.6, help="speed multiplier (TFM default 0.6)")
    parser.add_argument("--opacity", type=float, default=0.6, help="line opacity (TFM default 0.6)")
    parser.add_argument("--theme", choices=sorted(THEMES), help="palette (default: per scene)")
    parser.add_argument("--out", default="temp", help="output directory (default: temp/)")
    args = parser.parse_args()

    kinds = args.kind or sorted(tfm_background_animations.ANIMATION_KINDS)
    width, height = args.size
    os.makedirs(args.out, exist_ok=True)
    for kind in kinds:
        path = os.path.join(args.out, f"bg_{kind}.png")
        theme = args.theme or SCENE_THEME.get(kind, "dark")
        count, strokes = render(kind, width, height, args.time, speed=args.speed,
                                opacity=args.opacity, theme=theme, path=path)
        print(f"{kind:14s} {count:5d} segments  {strokes:3d} strokes  {theme:9s} -> {path}")


if __name__ == "__main__":
    sys.exit(main())
