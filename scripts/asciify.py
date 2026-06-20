#!/usr/bin/env python3
"""One-off: turn a photo into a dot-matrix portrait grid for the jelly hero canvas.

Pipeline:
  1. Remove the background with rembg (falls back to near-uniform-border
     keying if rembg is unavailable).
  2. Crop to the subject, frame to 3:4 (matches the .portrait-card slot).
  3. Resize to ~80 columns, accounting for the ~2:1 monospace cell ratio.
  4. Keep every subject cell's luminance (transparent cells are dropped) so
     the canvas can pick the ramp char " .:-=+*#%@" per theme — bright=dense
     on the dark site, dark=dense (ink-on-paper) on the light site.
  5. Write portrait.json as { cols, rows, cells: [{ x, y, l, a }] }, where
     l = luminance (0-1) and a = alpha (0-1).
  6. Print the grid so you can sanity-check it in the terminal.

Re-run with --cols / --gamma / --contrast to retune.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

REPO_ROOT = Path(__file__).resolve().parent.parent
# The brief says ./me.jpg; this repo keeps the photo at Images/Krushal.jpeg.
SOURCE = REPO_ROOT / "Images" / "Krushal.jpeg"
OUTPUT = REPO_ROOT / "portrait.json"

# Dark -> light. Index 0 (space) is darkest/empty, "@" is brightest/densest.
RAMP = " .:-=+*#%@"
TARGET_RATIO_W_OVER_H = 3 / 4  # matches .portrait-card aspect-ratio: 3 / 4
CHAR_W_OVER_H = 0.5            # a monospace cell is ~twice as tall as it is wide
ALPHA_VISIBLE = 128           # alpha below this counts as background


def cutout_with_rembg(source: Path, model: str) -> Image.Image | None:
    try:
        from rembg import new_session, remove
    except Exception as exc:  # noqa: BLE001 - any import/runtime failure -> fallback
        sys.stderr.write(f"rembg unavailable ({exc}); using border-key fallback.\n")
        return None
    try:
        session = new_session(model)
        cut = remove(source.read_bytes(), session=session)
        return Image.open(io.BytesIO(cut)).convert("RGBA")
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"rembg failed ({exc}); using border-key fallback.\n")
        return None


def cutout_by_border_key(source: Path, tolerance: int = 42) -> Image.Image:
    """Fallback: treat pixels near the average border colour as transparent."""
    img = Image.open(source).convert("RGBA")
    px = img.load()
    w, h = img.size

    # Average colour around the 1px border = best guess at the background.
    samples: list[tuple[int, int, int]] = []
    for x in range(w):
        samples.append(px[x, 0][:3])
        samples.append(px[x, h - 1][:3])
    for y in range(h):
        samples.append(px[0, y][:3])
        samples.append(px[w - 1, y][:3])
    n = len(samples)
    br = sum(s[0] for s in samples) / n
    bg = sum(s[1] for s in samples) / n
    bb = sum(s[2] for s in samples) / n

    tol_sq = (tolerance * 1.732) ** 2  # tolerance per-channel -> euclidean
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            d2 = (r - br) ** 2 + (g - bg) ** 2 + (b - bb) ** 2
            if d2 <= tol_sq:
                px[x, y] = (r, g, b, 0)
    return img


def crop_to_subject(img: Image.Image) -> Image.Image:
    bbox = img.split()[-1].getbbox()
    if bbox is None:
        sys.exit("Empty alpha mask — nothing to render.")
    return img.crop(bbox)


def frame_to_ratio(img: Image.Image, ratio_w_over_h: float) -> Image.Image:
    """Crop (top-anchored) to the target aspect ratio — no blank padding."""
    w, h = img.size
    current = w / h
    if abs(current - ratio_w_over_h) < 1e-3:
        return img
    if current > ratio_w_over_h:  # too wide -> trim sides symmetrically
        new_w = round(h * ratio_w_over_h)
        left = (w - new_w) // 2
        return img.crop((left, 0, left + new_w, h))
    # too tall -> keep the top (head + shoulders)
    new_h = round(w / ratio_w_over_h)
    return img.crop((0, 0, w, new_h))


def build_grid(img: Image.Image, cols: int, gamma: float, contrast: float):
    rows = max(1, round(cols * (1 / TARGET_RATIO_W_OVER_H) * CHAR_W_OVER_H))

    gray = ImageOps.grayscale(img).resize((cols, rows), Image.LANCZOS)
    if contrast > 0:
        gray = ImageOps.autocontrast(gray, cutoff=contrast)
    alpha = img.split()[-1].resize((cols, rows), Image.NEAREST)

    gray_px = gray.load()
    alpha_px = alpha.load()
    last = len(RAMP) - 1

    cells = []
    rows_text: list[str] = []
    for y in range(rows):
        line = []
        for x in range(cols):
            a = alpha_px[x, y]
            if a < ALPHA_VISIBLE:
                line.append(" ")
                continue
            v = gray_px[x, y] / 255.0
            v = max(0.0, min(1.0, v ** gamma))
            idx = int(round(v * last))  # bright -> "@", dark -> space
            line.append(RAMP[idx])
            # Store luminance (not a baked char) so the canvas can choose
            # density per theme: bright=dense on dark, dark=dense on light.
            cells.append({
                "x": x,
                "y": y,
                "l": round(v, 3),
                "a": round(a / 255.0, 3),
            })
        rows_text.append("".join(line))

    return cols, rows, cells, rows_text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cols", type=int, default=80)
    parser.add_argument("--gamma", type=float, default=0.85,
                        help=">1 darkens, <1 lifts mid-tones. Default 0.85.")
    parser.add_argument("--contrast", type=float, default=1.5,
                        help="autocontrast cutoff %%. 0 disables. Default 1.5.")
    parser.add_argument("--model", type=str, default="u2net_human_seg",
                        help="rembg model when available.")
    args = parser.parse_args()

    if not SOURCE.exists():
        sys.exit(f"Source photo not found: {SOURCE}")

    cut = cutout_with_rembg(SOURCE, args.model)
    if cut is None:
        cut = cutout_by_border_key(SOURCE)

    subject = crop_to_subject(cut)
    framed = frame_to_ratio(subject, TARGET_RATIO_W_OVER_H)
    cols, rows, cells, rows_text = build_grid(
        framed, args.cols, args.gamma, args.contrast)

    OUTPUT.write_text(
        json.dumps({"cols": cols, "rows": rows, "cells": cells}),
        encoding="utf-8",
    )

    # Sanity-check print.
    print("\n".join(rows_text))
    sys.stderr.write(
        f"\nWrote {OUTPUT.relative_to(REPO_ROOT)} — "
        f"{cols} cols x {rows} rows, {len(cells)} live cells.\n"
    )


if __name__ == "__main__":
    main()
