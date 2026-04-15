"""Convert a CST ASCII field export at z = 102 mm into a 2D |E|^2 image.

CST exports the plane monitor as whitespace-separated rows:
    x [mm]  y [mm]  z [mm]  ExRe  ExIm  EyRe  EyIm  EzRe  EzIm
with two header lines. This script reduces each sample to
    |E|^2 = ExRe^2 + ExIm^2 + EyRe^2 + EyIm^2 + EzRe^2 + EzIm^2
and places the values on the regular (x, y) grid found in the file.

If the export contains multiple z slices (because CST's export dialog
forced Nz > 1 even for a plane monitor), only the slice closest to
--target-z is kept. The output .npy is the form compute_metrics.py
expects as --cst-output.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = PROJECT_ROOT / "cst" / "results" / "array_sim"
DEFAULT_DST = EXPORT_DIR / "field_plane_30GHz_100mm.npy"
TARGET_Z_MM = 102.0


def _autodetect_source() -> Path:
    # CST's 2D/3D Plot Data Export writes .txt; earlier workflows saved
    # the same whitespace-separated content as .csv. Try the extensions
    # the server is known to produce, newest first.
    candidates = [
        EXPORT_DIR / "field_plane_30GHz_100mm.txt",
        EXPORT_DIR / "field_plane_30GHz_100mm.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert CST ASCII field export to 2D |E|^2 .npy")
    p.add_argument("--src", type=Path, default=None,
                   help="CST ASCII export (.txt or .csv). Autodetects if omitted.")
    p.add_argument("--dst", type=Path, default=DEFAULT_DST)
    p.add_argument("--target-z", type=float, default=TARGET_Z_MM,
                   help="Target z slice in mm; closest z in the export is used.")
    args = p.parse_args()
    if args.src is None:
        args.src = _autodetect_source()
    return args


def main() -> None:
    args = parse_args()
    print(f"Source: {args.src}")
    data = np.loadtxt(args.src, skiprows=2)
    if data.ndim != 2 or data.shape[1] < 9:
        raise ValueError(f"Unexpected CST export shape {data.shape}; expected >=9 columns")

    x_all = data[:, 0]
    y_all = data[:, 1]
    z_all = data[:, 2]
    ex_re, ex_im = data[:, 3], data[:, 4]
    ey_re, ey_im = data[:, 5], data[:, 6]
    ez_re, ez_im = data[:, 7], data[:, 8]

    e_sq_all = (
        ex_re ** 2 + ex_im ** 2
        + ey_re ** 2 + ey_im ** 2
        + ez_re ** 2 + ez_im ** 2
    ).astype(np.float32)

    z_unique = np.unique(z_all)
    if z_unique.size == 1:
        print(f"Single z plane in export: {z_unique[0]:.3f} mm")
        mask = np.ones_like(z_all, dtype=bool)
        z_used = float(z_unique[0])
    else:
        z_used = float(z_unique[np.argmin(np.abs(z_unique - args.target_z))])
        mask = np.isclose(z_all, z_used)
        print(f"Multiple z slices detected ({z_unique.size} unique z values: "
              f"{z_unique.min():.3f} to {z_unique.max():.3f} mm).")
        print(f"Keeping slice at z = {z_used:.3f} mm (closest to target {args.target_z} mm); "
              f"{mask.sum()} of {data.shape[0]} samples selected.")

    x = x_all[mask]
    y = y_all[mask]
    e_sq = e_sq_all[mask]

    ux = np.unique(x)
    uy = np.unique(y)
    print(f"grid: {uy.size} (y) x {ux.size} (x) = {uy.size * ux.size} samples; selected rows: {x.size}")

    if uy.size * ux.size != x.size:
        # Duplicates possible if CST exported the same (x,y,z) more than once;
        # take the mean of duplicate (x,y) samples at the chosen z slice.
        print("Non-unique (x, y) samples detected at the selected z; averaging duplicates.")
        x_idx_arr = np.searchsorted(ux, x)
        y_idx_arr = np.searchsorted(uy, y)
        image = np.zeros((uy.size, ux.size), dtype=np.float64)
        counts = np.zeros((uy.size, ux.size), dtype=np.int64)
        for yi, xi, v in zip(y_idx_arr, x_idx_arr, e_sq):
            image[yi, xi] += float(v)
            counts[yi, xi] += 1
        counts[counts == 0] = 1
        image = (image / counts).astype(np.float32)
    else:
        x_idx = {v: i for i, v in enumerate(ux.tolist())}
        y_idx = {v: i for i, v in enumerate(uy.tolist())}
        image = np.zeros((uy.size, ux.size), dtype=np.float32)
        for xv, yv, val in zip(x, y, e_sq):
            image[y_idx[float(yv)], x_idx[float(xv)]] = float(val)

    args.dst.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.dst, image)
    print(f"Saved {image.shape} |E|^2 image (z = {z_used:.3f} mm) to {args.dst}")
    print(f"min/mean/max |E|^2: {image.min():.4f} / {image.mean():.4f} / {image.max():.4f}")


if __name__ == "__main__":
    main()