from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PHASE_DIR = PROJECT_ROOT / "python" / "outputs" / "phase_maps"
HEIGHT_DIR = PROJECT_ROOT / "python" / "outputs" / "height_maps"
DEFAULT_SCAN_CSV = PROJECT_ROOT / "cst" / "results" / "unit_scan" / "phase_height_curve.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Map trained phase matrix to unit-cell height matrix.")
    parser.add_argument(
        "--phase",
        type=str,
        default=str(PROJECT_ROOT / "python" / "outputs" / "phase_maps" / "phase_matrix.npy"),
        help="Input wrapped phase matrix (*.npy).",
    )
    parser.add_argument(
        "--method",
        choices=["linear", "interp"],
        default="interp",
        help="Mapping method: linear baseline or interpolation from CST scan CSV.",
    )
    parser.add_argument(
        "--scan-csv",
        type=str,
        default=str(DEFAULT_SCAN_CSV),
        help="CSV containing height-phase curve. Required for --method interp.",
    )
    parser.add_argument("--h-min-mm", type=float, default=2.0)
    parser.add_argument("--h-max-mm", type=float, default=8.0)
    parser.add_argument("--phase-col", type=str, default="phase_rad")
    parser.add_argument("--height-col", type=str, default="height_mm")
    parser.add_argument("--out-prefix", type=str, default="height_matrix")
    return parser.parse_args()


def wrap_phase_2pi(phase: np.ndarray) -> np.ndarray:
    return np.mod(phase, 2.0 * np.pi).astype(np.float32)


def linear_map(phase_wrapped: np.ndarray, h_min: float, h_max: float) -> np.ndarray:
    # Baseline mapping: phase in [0, 2pi) -> height in [h_min, h_max].
    ratio = phase_wrapped / (2.0 * np.pi)
    return (h_min + ratio * (h_max - h_min)).astype(np.float32)


def _infer_columns(df: pd.DataFrame, phase_col: str, height_col: str) -> tuple[str, str]:
    if phase_col in df.columns and height_col in df.columns:
        return phase_col, height_col

    lower_map = {col.lower(): col for col in df.columns}
    cand_phase = ["phase_rad", "phase", "s21_phase_rad", "s21_phase", "phase_deg"]
    cand_height = ["height_mm", "height", "h_mm", "h"]

    resolved_phase = None
    for c in cand_phase:
        if c in lower_map:
            resolved_phase = lower_map[c]
            break
    resolved_height = None
    for c in cand_height:
        if c in lower_map:
            resolved_height = lower_map[c]
            break

    if resolved_phase is None or resolved_height is None:
        raise ValueError(
            f"Cannot infer columns from {list(df.columns)}. "
            "Please pass --phase-col and --height-col explicitly."
        )
    return resolved_phase, resolved_height


def interp_map(phase_wrapped: np.ndarray, scan_csv: Path, phase_col: str, height_col: str) -> np.ndarray:
    if not scan_csv.exists():
        raise FileNotFoundError(f"Scan CSV not found: {scan_csv}")

    df = pd.read_csv(scan_csv)
    phase_col, height_col = _infer_columns(df, phase_col, height_col)

    phase_curve = df[phase_col].to_numpy(dtype=np.float64)
    height_curve = df[height_col].to_numpy(dtype=np.float64)
    if phase_curve.size < 2:
        raise ValueError("Scan CSV needs at least 2 points.")

    # Accept degrees if user exported degree phase.
    if np.nanmax(np.abs(phase_curve)) > 2.0 * np.pi + 1.0:
        phase_curve = np.deg2rad(phase_curve)

    phase_curve_raw = phase_curve.copy()
    phase_curve = np.mod(phase_curve, 2.0 * np.pi)
    endpoint_mask = np.isclose(phase_curve, 0.0) & (np.abs(phase_curve_raw) > np.pi)
    phase_curve[endpoint_mask] = np.nextafter(2.0 * np.pi, 0.0)

    # Use unique sorted phases for stable interpolation.
    order = np.argsort(phase_curve)
    x = phase_curve[order]
    y = height_curve[order]
    x_unique, unique_idx = np.unique(x, return_index=True)
    y_unique = y[unique_idx]
    if x_unique.size < 2:
        raise ValueError("Phase curve collapses to <2 unique points after wrapping.")

    mapped = np.interp(phase_wrapped.ravel(), x_unique, y_unique, left=y_unique[0], right=y_unique[-1])
    return mapped.reshape(phase_wrapped.shape).astype(np.float32)


def save_outputs(height_map: np.ndarray, prefix: str) -> tuple[Path, Path]:
    HEIGHT_DIR.mkdir(parents=True, exist_ok=True)
    npy_path = HEIGHT_DIR / f"{prefix}.npy"
    csv_path = HEIGHT_DIR / f"{prefix}.csv"
    np.save(npy_path, height_map.astype(np.float32))
    pd.DataFrame(height_map).to_csv(csv_path, index=False, header=False)
    return npy_path, csv_path


def main() -> None:
    args = parse_args()
    phase_path = Path(args.phase)
    if not phase_path.exists():
        raise FileNotFoundError(f"Phase matrix not found: {phase_path}")

    phase = np.load(phase_path).astype(np.float32)
    phase_wrapped = wrap_phase_2pi(phase)

    if args.method == "linear":
        height_map = linear_map(phase_wrapped, h_min=args.h_min_mm, h_max=args.h_max_mm)
    else:
        height_map = interp_map(
            phase_wrapped,
            scan_csv=Path(args.scan_csv),
            phase_col=args.phase_col,
            height_col=args.height_col,
        )

    npy_path, csv_path = save_outputs(height_map, args.out_prefix)
    print(f"Method: {args.method}")
    print(f"Input phase: {phase_path}")
    if args.method == "interp":
        print(f"Scan CSV: {Path(args.scan_csv)}")
    print(f"Height range [mm]: min={height_map.min():.4f}, max={height_map.max():.4f}")
    print(f"Saved height map NPY: {npy_path}")
    print(f"Saved height map CSV: {csv_path}")


if __name__ == "__main__":
    main()
