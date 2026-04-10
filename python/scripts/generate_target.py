from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTDIR = PROJECT_ROOT / "python" / "data" / "targets"


def make_canvas(n: int) -> np.ndarray:
    return np.zeros((n, n), dtype=np.float32)


def fill_rect(arr: np.ndarray, r0: float, r1: float, c0: float, c1: float) -> None:
    n = arr.shape[0]
    row_slice = slice(max(0, int(round(r0 * n))), min(n, int(round(r1 * n))))
    col_slice = slice(max(0, int(round(c0 * n))), min(n, int(round(c1 * n))))
    arr[row_slice, col_slice] = 1.0


def stamp_bitmap(arr: np.ndarray, bitmap: list[str], top: int, left: int, scale: int) -> None:
    glyph = np.array([[1.0 if ch == "1" else 0.0 for ch in row] for row in bitmap], dtype=np.float32)
    glyph = np.flipud(glyph)
    glyph = np.repeat(np.repeat(glyph, scale, axis=0), scale, axis=1)
    height, width = glyph.shape
    arr[top:top + height, left:left + width] = np.maximum(arr[top:top + height, left:left + width], glyph)


def draw_ghz(n: int) -> np.ndarray:
    arr = make_canvas(n)
    scale = max(1, n // 30)
    glyph_top = int(round(0.44 * n))

    glyph_g = [
        "01110",
        "10001",
        "10000",
        "10111",
        "10001",
        "10001",
        "01110",
    ]
    glyph_h = [
        "10001",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ]
    glyph_z = [
        "11111",
        "00001",
        "00010",
        "00100",
        "01000",
        "10000",
        "11111",
    ]

    stamp_bitmap(arr, glyph_g, glyph_top, int(round(0.17 * n)), scale)
    stamp_bitmap(arr, glyph_h, glyph_top, int(round(0.42 * n)), scale)
    stamp_bitmap(arr, glyph_z, glyph_top, int(round(0.67 * n)), scale)
    return arr


PATTERN_BUILDERS = {
    "GHZ": draw_ghz,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a 60x60 target image for the NFMHI project.")
    parser.add_argument("--pattern", choices=PATTERN_BUILDERS.keys(), default="GHZ")
    parser.add_argument("--size", type=int, default=60, help="Target image size. Paper default is 60.")
    parser.add_argument("--prefix", type=str, default="target", help="Output filename prefix.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    builder = PATTERN_BUILDERS[args.pattern]
    target = builder(args.size)

    DEFAULT_OUTDIR.mkdir(parents=True, exist_ok=True)
    base_name = f"{args.prefix}_{args.pattern}_{args.size}x{args.size}"

    npy_path = DEFAULT_OUTDIR / f"{base_name}.npy"
    png_path = DEFAULT_OUTDIR / f"{base_name}.png"

    np.save(npy_path, target.astype(np.float32))
    png_array = np.flipud(np.clip(target, 0.0, 1.0))
    Image.fromarray((png_array * 255).astype(np.uint8), mode="L").save(png_path)

    print(f"Saved target array to: {npy_path}")
    print(f"Saved target image to: {png_path}")
    print(f"Pattern: {args.pattern}, size: {args.size}x{args.size}, min/max: {target.min():.3f}/{target.max():.3f}")


if __name__ == "__main__":
    main()
