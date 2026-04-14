"""Side-by-side comparison plot: target, Python forward, CST near-field.

Each panel is drawn on the same 0..300 mm extent. The CST image is upscaled
to the target resolution via nearest-neighbor so the three panels share
grid coordinates. The figure is saved to python/outputs/figures/.
"""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MPLCONFIGDIR = Path(tempfile.gettempdir()) / "nfmhi_mplconfig"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR))

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

TARGET_DEFAULT = PROJECT_ROOT / "python" / "data" / "targets" / "target_GHZ_60x60.npy"
PYTHON_DEFAULT = PROJECT_ROOT / "python" / "outputs" / "figures" / "dnn_train_intensity.npy"
CST_DEFAULT = PROJECT_ROOT / "cst" / "results" / "array_sim" / "field_plane_30GHz_100mm.npy"
FIG_DIR = PROJECT_ROOT / "python" / "outputs" / "figures"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot CST near-field vs target vs Python forward.")
    p.add_argument("--target", type=Path, default=TARGET_DEFAULT)
    p.add_argument("--python-output", type=Path, default=PYTHON_DEFAULT)
    p.add_argument("--cst-output", type=Path, default=CST_DEFAULT)
    p.add_argument("--out-prefix", type=str, default="cst_vs_target")
    return p.parse_args()


def resize_nn(arr: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    if arr.shape == shape:
        return arr.astype(np.float32)
    src_h, src_w = arr.shape
    dst_h, dst_w = shape
    y_idx = np.clip(np.round(np.linspace(0, src_h - 1, dst_h)).astype(int), 0, src_h - 1)
    x_idx = np.clip(np.round(np.linspace(0, src_w - 1, dst_w)).astype(int), 0, src_w - 1)
    return arr[np.ix_(y_idx, x_idx)].astype(np.float32)


def main() -> None:
    args = parse_args()
    target = np.load(args.target).astype(np.float32)
    python_out = np.load(args.python_output).astype(np.float32)
    cst_out_raw = np.load(args.cst_output).astype(np.float32)

    cst_out = resize_nn(cst_out_raw, target.shape)

    extent_mm = (0.0, 300.0, 0.0, 300.0)
    ticks_mm = np.arange(0, 301, 50)
    paper_red = LinearSegmentedColormap.from_list(
        "paper_red", ["#000000", "#260000", "#7a0000", "#ff0000"]
    )

    plt.rcParams.update(
        {
            "font.family": "STIXGeneral",
            "mathtext.fontset": "stix",
            "axes.labelsize": 14,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    ax_t, ax_py, ax_cst = axes

    im_t = ax_t.imshow(
        target,
        cmap=paper_red,
        origin="lower",
        vmin=0.0,
        vmax=float(target.max()),
        extent=extent_mm,
        interpolation="nearest",
    )
    ax_t.set_title("(a) Target (GHZ)")
    ax_t.set_xlabel(r"$x/mm$")
    ax_t.set_ylabel(r"$y/mm$")
    ax_t.set_xticks(ticks_mm)
    ax_t.set_yticks(ticks_mm)
    fig.colorbar(im_t, ax=ax_t, fraction=0.046, pad=0.04)

    im_py = ax_py.imshow(
        python_out,
        cmap=paper_red,
        origin="lower",
        vmin=0.0,
        vmax=float(python_out.max()),
        extent=extent_mm,
        interpolation="nearest",
    )
    ax_py.set_title(f"(b) Python forward |E|$^2$  (max {python_out.max():.2f})")
    ax_py.set_xlabel(r"$x/mm$")
    ax_py.set_ylabel(r"$y/mm$")
    ax_py.set_xticks(ticks_mm)
    ax_py.set_yticks(ticks_mm)
    fig.colorbar(im_py, ax=ax_py, fraction=0.046, pad=0.04)

    im_cst = ax_cst.imshow(
        cst_out,
        cmap=paper_red,
        origin="lower",
        vmin=0.0,
        vmax=float(cst_out.max()),
        extent=extent_mm,
        interpolation="nearest",
    )
    ax_cst.set_title(
        f"(c) CST |E|$^2$ at z=102 mm  ({cst_out_raw.shape[0]}x{cst_out_raw.shape[1]}, max {cst_out.max():.2f})"
    )
    ax_cst.set_xlabel(r"$x/mm$")
    ax_cst.set_ylabel(r"$y/mm$")
    ax_cst.set_xticks(ticks_mm)
    ax_cst.set_yticks(ticks_mm)
    fig.colorbar(im_cst, ax=ax_cst, fraction=0.046, pad=0.04)

    fig.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out_png = FIG_DIR / f"{args.out_prefix}.png"
    fig.savefig(out_png, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {out_png}")
    print(f"  target shape: {target.shape}, max {target.max():.3f}")
    print(f"  python shape: {python_out.shape}, max {python_out.max():.3f}")
    print(f"  CST raw shape: {cst_out_raw.shape}, resized to {cst_out.shape}, max {cst_out.max():.3f}")


if __name__ == "__main__":
    main()