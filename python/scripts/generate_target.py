from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTDIR = PROJECT_ROOT / "python" / "data" / "targets"


def make_canvas(n: int) -> np.ndarray:
    return np.zeros((n, n), dtype=np.float32)


def stamp_bitmap(arr: np.ndarray, bitmap: list[str], top: int, left: int) -> None:
    glyph = np.array([[1.0 if ch == "1" else 0.0 for ch in row] for row in bitmap], dtype=np.float32)
    glyph = np.flipud(glyph)
    height, width = glyph.shape
    arr[top:top + height, left:left + width] = np.maximum(arr[top:top + height, left:left + width], glyph)


def draw_ghz(n: int) -> np.ndarray:
    if n != 60:
        raise ValueError("The paper-aligned GHZ target is defined explicitly for a 60x60 grid.")

    arr = make_canvas(n)
    glyph_top = 27

    glyph_g = [
        "0111110",
        "1000001",
        "1000000",
        "1000000",
        "1001111",
        "1000001",
        "1000001",
        "1000001",
        "0111110",
    ]
    glyph_h = [
        "1000001",
        "1000001",
        "1000001",
        "1000001",
        "1111111",
        "1000001",
        "1000001",
        "1000001",
        "1000001",
    ]
    glyph_z = [
        "1111111",
        "0000001",
        "0000010",
        "0000100",
        "0001000",
        "0010000",
        "0100000",
        "1000000",
        "1111111",
    ]

    stamp_bitmap(arr, glyph_g, glyph_top, 15)
    stamp_bitmap(arr, glyph_h, glyph_top, 29)
    stamp_bitmap(arr, glyph_z, glyph_top, 43)
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
