"""Convert a CST ASCII field export at z = 102 mm into a 2D |E|^2 image.

CST exports the plane monitor as whitespace-separated rows:
    x [mm]  y [mm]  z [mm]  ExRe  ExIm  EyRe  EyIm  EzRe  EzIm
with two header lines. This script reduces each sample to
    |E|^2 = ExRe^2 + ExIm^2 + EyRe^2 + EyIm^2 + EzRe^2 + EzIm^2
and places the values on the regular (x, y) grid found in the file.

The output .npy is the form compute_metrics.py expects as --cst-output.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SRC = PROJECT_ROOT / "cst" / "results" / "array_sim" / "field_plane_30GHz_100mm.csv"
DEFAULT_DST = PROJECT_ROOT / "cst" / "results" / "array_sim" / "field_plane_30GHz_100mm.npy"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert CST ASCII field export to 2D |E|^2 .npy")
    p.add_argument("--src", type=Path, default=DEFAULT_SRC)
    p.add_argument("--dst", type=Path, default=DEFAULT_DST)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    data = np.loadtxt(args.src, skiprows=2)
    if data.ndim != 2 or data.shape[1] < 9:
        raise ValueError(f"Unexpected CST export shape {data.shape}; expected >=9 columns")

    x = data[:, 0]
    y = data[:, 1]
    z = data[:, 2]
    ex_re, ex_im = data[:, 3], data[:, 4]
    ey_re, ey_im = data[:, 5], data[:, 6]
    ez_re, ez_im = data[:, 7], data[:, 8]

    e_sq = (
        ex_re ** 2 + ex_im ** 2
        + ey_re ** 2 + ey_im ** 2
        + ez_re ** 2 + ez_im ** 2
    ).astype(np.float32)

    z_unique = np.unique(z)
    if z_unique.size != 1:
        print(f"WARNING: multiple z values in export: {z_unique[:5]}... (n={z_unique.size})")
    else:
        print(f"z plane: {z_unique[0]:.3f} mm")

    ux = np.unique(x)
    uy = np.unique(y)
    print(f"grid: {uy.size} (y) x {ux.size} (x) = {uy.size * ux.size} samples; file rows: {data.shape[0]}")
    if uy.size * ux.size != data.shape[0]:
        raise ValueError("Samples do not form a regular rectangular grid; aborting.")

    x_idx = {v: i for i, v in enumerate(ux.tolist())}
    y_idx = {v: i for i, v in enumerate(uy.tolist())}
    image = np.zeros((uy.size, ux.size), dtype=np.float32)
    for xv, yv, val in zip(x, y, e_sq):
        image[y_idx[float(yv)], x_idx[float(xv)]] = float(val)

    args.dst.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.dst, image)
    print(f"Saved {image.shape} |E|^2 image to {args.dst}")
    print(f"min/mean/max |E|^2: {image.min():.4f} / {image.mean():.4f} / {image.max():.4f}")


if __name__ == "__main__":
    main()