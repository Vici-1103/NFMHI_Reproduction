from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "python" / "src" / "config" / "defaults.yaml"
PHASE_DIR = PROJECT_ROOT / "python" / "outputs" / "phase_maps"
HEIGHT_DIR = PROJECT_ROOT / "python" / "outputs" / "height_maps"
DEFAULT_SCAN_CSV = PROJECT_ROOT / "cst" / "results" / "unit_scan" / "phase_height_curve.csv"


def parse_scalar(value: str) -> object:
    value = value.strip()
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_defaults() -> dict[str, object]:
    root: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-1, root)]

    for raw_line in CONFIG_PATH.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, _, value = raw_line.strip().partition(":")
        while indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip() == "":
            parent[key] = {}
            stack.append((indent, parent[key]))
        else:
            parent[key] = parse_scalar(value)
    return root


def parse_args() -> argparse.Namespace:
    defaults = load_defaults()
    cst_defaults = defaults["cst"]

    parser = argparse.ArgumentParser(description="Map trained phase matrix to unit-cell height matrix.")
    parser.add_argument(
        "--phase",
        type=str,
        default=str(PROJECT_ROOT / "python" / "outputs" / "phase_maps" / "phase_matrix.npy"),
        help="Input phase matrix (*.npy).",
    )
    parser.add_argument(
        "--method",
        choices=["linear", "paper_interp"],
        default="paper_interp",
        help="Mapping method. paper_interp unwraps the CST phase curve and maps the additional phase from h_min.",
    )
    parser.add_argument(
        "--scan-csv",
        type=str,
        default=str(DEFAULT_SCAN_CSV),
        help="CSV containing the wrapped height-phase scan exported from CST.",
    )
    parser.add_argument("--h-min-mm", type=float, default=float(cst_defaults["unit_height_min_mm"]))
    parser.add_argument("--h-max-mm", type=float, default=float(cst_defaults["unit_height_max_mm"]))
    parser.add_argument(
        "--zero-phase-reference-height-mm",
        type=float,
        default=float(cst_defaults["zero_phase_reference_height_mm"]),
    )
    parser.add_argument("--phase-col", type=str, default="phase_rad")
    parser.add_argument("--height-col", type=str, default="height_mm")
    parser.add_argument("--out-prefix", type=str, default="height_matrix")
    return parser.parse_args()


def wrap_phase_2pi(phase: np.ndarray) -> np.ndarray:
    return np.mod(phase, 2.0 * np.pi).astype(np.float32)


def linear_map(phase_wrapped: np.ndarray, h_min: float, h_max: float) -> np.ndarray:
    ratio = phase_wrapped / (2.0 * np.pi)
    return (h_min + ratio * (h_max - h_min)).astype(np.float32)


def _infer_columns(df: pd.DataFrame, phase_col: str, height_col: str) -> tuple[str, str]:
    if phase_col in df.columns and height_col in df.columns:
        return phase_col, height_col

    lower_map = {col.lower(): col for col in df.columns}
    cand_phase = ["phase_rad", "phase", "s21_phase_rad", "s21_phase", "phase_deg"]
    cand_height = ["height_mm", "height", "h_mm", "h"]

    resolved_phase = next((lower_map[c] for c in cand_phase if c in lower_map), None)
    resolved_height = next((lower_map[c] for c in cand_height if c in lower_map), None)

    if resolved_phase is None or resolved_height is None:
        raise ValueError(
            f"Cannot infer columns from {list(df.columns)}. "
            "Please pass --phase-col and --height-col explicitly."
        )
    return resolved_phase, resolved_height


def preprocess_scan_curve(
    scan_csv: Path | str,
    phase_col: str,
    height_col: str,
    zero_phase_reference_height_mm: float,
) -> pd.DataFrame:
    scan_csv = Path(scan_csv)
    if not scan_csv.exists():
        raise FileNotFoundError(f"Scan CSV not found: {scan_csv}")

    df = pd.read_csv(scan_csv)
    phase_col, height_col = _infer_columns(df, phase_col, height_col)

    curve = (
        df[[height_col, phase_col] + ([c for c in ["s21_mag"] if c in df.columns])]
        .copy()
        .rename(columns={height_col: "height_mm", phase_col: "phase_rad_wrapped"})
        .sort_values("height_mm")
        .reset_index(drop=True)
    )

    if curve.shape[0] < 2:
        raise ValueError("Scan CSV needs at least 2 samples.")

    phase_wrapped = curve["phase_rad_wrapped"].to_numpy(dtype=np.float64)
    if np.nanmax(np.abs(phase_wrapped)) > 2.0 * np.pi + 1.0:
        phase_wrapped = np.deg2rad(phase_wrapped)
        curve["phase_rad_wrapped"] = phase_wrapped

    phase_unwrapped = np.unwrap(phase_wrapped)
    curve["phase_rad_unwrapped"] = phase_unwrapped

    ref_idx = int(np.argmin(np.abs(curve["height_mm"].to_numpy(dtype=np.float64) - zero_phase_reference_height_mm)))
    ref_height = float(curve.loc[ref_idx, "height_mm"])
    if abs(ref_height - zero_phase_reference_height_mm) > 1e-6:
        raise ValueError(
            f"Zero-phase reference height {zero_phase_reference_height_mm} mm is not present in the scan CSV."
        )

    ref_phase = float(curve.loc[ref_idx, "phase_rad_unwrapped"])
    curve["additional_phase_rad"] = -(curve["phase_rad_unwrapped"] - ref_phase)

    additional_phase = curve["additional_phase_rad"].to_numpy(dtype=np.float64)
    if np.any(np.diff(additional_phase) <= 0):
        raise ValueError("Unwrapped additional phase is not strictly increasing with height.")

    return curve


def paper_interp_map(
    phase_wrapped: np.ndarray,
    scan_csv: Path,
    phase_col: str,
    height_col: str,
    zero_phase_reference_height_mm: float,
    h_min_mm: float,
    h_max_mm: float,
) -> tuple[np.ndarray, pd.DataFrame]:
    curve = preprocess_scan_curve(
        scan_csv=scan_csv,
        phase_col=phase_col,
        height_col=height_col,
        zero_phase_reference_height_mm=zero_phase_reference_height_mm,
    )
    curve = curve[(curve["height_mm"] >= h_min_mm) & (curve["height_mm"] <= h_max_mm)].reset_index(drop=True)
    if curve.empty:
        raise ValueError("No scan samples remain after height-range filtering.")

    x = curve["additional_phase_rad"].to_numpy(dtype=np.float64)
    y = curve["height_mm"].to_numpy(dtype=np.float64)
    mapped = np.interp(phase_wrapped.ravel(), x, y, left=y[0], right=y[-1]).reshape(phase_wrapped.shape)
    mapped = np.clip(mapped, h_min_mm, h_max_mm).astype(np.float32)
    return mapped, curve


def save_outputs(height_map: np.ndarray, prefix: str, curve: pd.DataFrame | None, metadata: dict[str, object]) -> tuple[Path, Path, Path | None, Path]:
    HEIGHT_DIR.mkdir(parents=True, exist_ok=True)
    npy_path = HEIGHT_DIR / f"{prefix}.npy"
    csv_path = HEIGHT_DIR / f"{prefix}.csv"
    meta_path = HEIGHT_DIR / f"{prefix}_metadata.json"
    unwrapped_path = None

    np.save(npy_path, height_map.astype(np.float32))
    pd.DataFrame(height_map).to_csv(csv_path, index=False, header=False)

    if curve is not None:
        unwrapped_path = HEIGHT_DIR / "phase_height_curve_unwrapped.csv"
        curve.to_csv(unwrapped_path, index=False)

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return npy_path, csv_path, unwrapped_path, meta_path


def validate_height_map(height_map: np.ndarray, h_min_mm: float, h_max_mm: float) -> None:
    if np.isnan(height_map).any() or np.isinf(height_map).any():
        raise ValueError("Height map contains NaN or inf values.")
    if float(height_map.min()) < h_min_mm - 1e-6 or float(height_map.max()) > h_max_mm + 1e-6:
        raise ValueError(
            f"Height map is outside the configured range [{h_min_mm}, {h_max_mm}] mm: "
            f"min={height_map.min():.6f}, max={height_map.max():.6f}"
        )


def main() -> None:
    args = parse_args()
    phase_path = Path(args.phase)
    if not phase_path.exists():
        raise FileNotFoundError(f"Phase matrix not found: {phase_path}")

    phase = np.load(phase_path).astype(np.float32)
    phase_wrapped = wrap_phase_2pi(phase)

    curve = None
    if args.method == "linear":
        height_map = linear_map(phase_wrapped, h_min=args.h_min_mm, h_max=args.h_max_mm)
    else:
        height_map, curve = paper_interp_map(
            phase_wrapped=phase_wrapped,
            scan_csv=Path(args.scan_csv),
            phase_col=args.phase_col,
            height_col=args.height_col,
            zero_phase_reference_height_mm=args.zero_phase_reference_height_mm,
            h_min_mm=args.h_min_mm,
            h_max_mm=args.h_max_mm,
        )

    validate_height_map(height_map, h_min_mm=args.h_min_mm, h_max_mm=args.h_max_mm)

    metadata = {
        "method": args.method,
        "phase_input": str(phase_path),
        "scan_csv": str(Path(args.scan_csv)),
        "used_unwrap": args.method == "paper_interp",
        "zero_phase_reference_height_mm": args.zero_phase_reference_height_mm,
        "height_range_mm": [args.h_min_mm, args.h_max_mm],
        "height_map_min_mm": float(height_map.min()),
        "height_map_max_mm": float(height_map.max()),
    }
    npy_path, csv_path, unwrapped_path, meta_path = save_outputs(height_map, args.out_prefix, curve, metadata)

    print(f"Method: {args.method}")
    print(f"Input phase: {phase_path}")
    print(f"Scan CSV: {Path(args.scan_csv)}")
    print(f"Height range [mm]: min={height_map.min():.4f}, max={height_map.max():.4f}")
    if unwrapped_path is not None:
        print(f"Saved unwrapped scan CSV: {unwrapped_path}")
    print(f"Saved height map NPY: {npy_path}")
    print(f"Saved height map CSV: {csv_path}")
    print(f"Saved metadata JSON: {meta_path}")


if __name__ == "__main__":
    main()
