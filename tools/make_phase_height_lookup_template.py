from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build uniform phase-height lookup from CST sweep CSV.")
    parser.add_argument("--input", required=True, type=str, help="CST scan CSV with height and phase columns.")
    parser.add_argument("--output", required=True, type=str, help="Output lookup CSV path.")
    parser.add_argument("--phase-col", type=str, default="phase_rad")
    parser.add_argument("--height-col", type=str, default="height_mm")
    parser.add_argument("--bins", type=int, default=361, help="Number of phase bins in [0, 2pi].")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output)
    if not in_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {in_path}")

    df = pd.read_csv(in_path)
    if args.phase_col not in df.columns or args.height_col not in df.columns:
        raise ValueError(
            f"CSV columns are {list(df.columns)}; expected {args.phase_col} and {args.height_col}"
        )

    phase = df[args.phase_col].to_numpy(dtype=np.float64)
    height = df[args.height_col].to_numpy(dtype=np.float64)
    if np.nanmax(np.abs(phase)) > 2.0 * np.pi + 1.0:
        phase = np.deg2rad(phase)
    phase = np.mod(phase, 2.0 * np.pi)

    order = np.argsort(phase)
    phase_sorted = phase[order]
    height_sorted = height[order]
    phase_unique, idx = np.unique(phase_sorted, return_index=True)
    height_unique = height_sorted[idx]
    if phase_unique.size < 2:
        raise ValueError("Need at least two unique phase points for interpolation.")

    bins = np.linspace(0.0, 2.0 * np.pi, args.bins)
    lookup_h = np.interp(bins, phase_unique, height_unique, left=height_unique[0], right=height_unique[-1])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df = pd.DataFrame({"phase_rad": bins, "height_mm": lookup_h})
    out_df.to_csv(out_path, index=False)
    print(f"Saved lookup CSV to: {out_path}")


if __name__ == "__main__":
    main()
