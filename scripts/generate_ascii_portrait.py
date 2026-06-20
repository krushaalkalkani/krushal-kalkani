#!/usr/bin/env python3
"""Generate an ASCII portrait of Krushal from Images/Krushal.jpeg.

Removes the stadium background with rembg, crops to the person, pads to a
3:4 aspect ratio (matches .portrait-card on the site), then maps brightness
to the ramp ` .:-=+*#%` and writes the result to Images/krushal-ascii.txt.

Re-run with --cols / --rows / --gamma to retune.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from PIL import Image, ImageOps
from rembg import new_session, remove

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "Images" / "Krushal.jpeg"
OUTPUT = REPO_ROOT / "Images" / "krushal-ascii.txt"

RAMP = " .:-=+*#%@"
TARGET_RATIO_W_OVER_H = 3 / 4
CHAR_W_OVER_H = 0.5


def cutout_person(source: Path, model: str) -> Image.Image:
    raw = source.read_bytes()
    session = new_session(model)
    cut = remove(raw, session=session)
    img = Image.open(io.BytesIO(cut)).convert("RGBA")
    bbox = img.split()[-1].getbbox()
    if bbox is None:
        sys.exit("rembg returned an empty alpha mask — nothing to render.")
    return img.crop(bbox)


def fit_to_ratio(img: Image.Image, ratio_w_over_h: float) -> Image.Image:
    """Crop top-anchored to match target aspect ratio (no padding, no blank space)."""
    w, h = img.size
    current = w / h
    if abs(current - ratio_w_over_h) < 1e-3:
        return img
    if current > ratio_w_over_h:
        # too wide → trim left/right symmetrically
        new_w = int(round(h * ratio_w_over_h))
        left = (w - new_w) // 2
        return img.crop((left, 0, left + new_w, h))
    # too tall → keep the top (head + upper body)
    new_h = int(round(w / ratio_w_over_h))
    return img.crop((0, 0, w, new_h))


def to_ascii(img: Image.Image, cols: int, rows: int | None,
             gamma: float, contrast_cutoff: float) -> str:
    if rows is None:
        rows = max(1, round(cols * (1 / TARGET_RATIO_W_OVER_H) * CHAR_W_OVER_H))

    gray = ImageOps.grayscale(img).resize((cols, rows), Image.LANCZOS)
    if contrast_cutoff > 0:
        gray = ImageOps.autocontrast(gray, cutoff=contrast_cutoff)
    alpha = img.split()[-1].resize((cols, rows), Image.NEAREST)

    gray_px = gray.load()
    alpha_px = alpha.load()
    ramp = RAMP
    last = len(ramp) - 1

    lines = []
    for y in range(rows):
        row_chars = []
        for x in range(cols):
            if alpha_px[x, y] < 128:
                row_chars.append(" ")
                continue
            v = gray_px[x, y] / 255.0
            v = max(0.0, min(1.0, v ** gamma))
            idx = int(round((1.0 - v) * last))
            row_chars.append(ramp[idx])
        lines.append("".join(row_chars).rstrip())
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cols", type=int, default=90)
    parser.add_argument("--rows", type=int, default=None,
                        help="Auto-derived from --cols for 3:4 monospace if omitted.")
    parser.add_argument("--gamma", type=float, default=0.7,
                        help=">1 darkens, <1 lightens. Default 0.7 lifts mid-tones.")
    parser.add_argument("--contrast", type=float, default=1.0,
                        help="autocontrast cutoff %. 0 disables. Default 1.0.")
    parser.add_argument("--model", type=str, default="u2net_human_seg",
                        help="rembg model: u2net, u2net_human_seg, isnet-general-use, etc.")
    args = parser.parse_args()

    person = cutout_person(SOURCE, args.model)
    framed = fit_to_ratio(person, TARGET_RATIO_W_OVER_H)
    art = to_ascii(framed, args.cols, args.rows, args.gamma, args.contrast)

    OUTPUT.write_text(art + "\n", encoding="utf-8")
    line_count = art.count("\n") + 1
    width = max((len(line) for line in art.splitlines()), default=0)
    sys.stderr.write(f"Wrote {OUTPUT} — {width} cols x {line_count} rows\n")
    print(art)


if __name__ == "__main__":
    main()
