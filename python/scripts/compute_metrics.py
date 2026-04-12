from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
try:
    from skimage.metrics import peak_signal_noise_ratio, structural_similarity
except ImportError:
    peak_signal_noise_ratio = None
    structural_similarity = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
METRICS_DIR = PROJECT_ROOT / "python" / "outputs" / "metrics"
PAPER_REFERENCE = {
    "ie": 0.6834,
    "psnr_db": 10.47,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute PSNR/SSIM/IE for Python and CST outputs.")
    parser.add_argument(
        "--target",
        type=str,
        default=str(PROJECT_ROOT / "python" / "data" / "targets" / "target_GHZ_60x60.npy"),
        help="Target image (.npy or .png).",
    )
    parser.add_argument(
        "--python-output",
        type=str,
        default=str(PROJECT_ROOT / "python" / "outputs" / "figures" / "dnn_train_intensity.npy"),
        help="Predicted intensity from Python (.npy).",
    )
    parser.add_argument(
        "--cst-output",
        type=str,
        default=str(PROJECT_ROOT / "cst" / "results" / "array_sim" / "field_plane_30GHz_100mm.csv"),
        help="CST exported field/intensity CSV.",
    )
    parser.add_argument("--out-prefix", type=str, default="final_compare")
    return parser.parse_args()


def load_image_like(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"Input not found: {path}")
    if path.suffix.lower() == ".npy":
        arr = np.load(path).astype(np.float32)
    elif path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}:
        arr = np.array(Image.open(path).convert("L"), dtype=np.float32) / 255.0
    elif path.suffix.lower() == ".csv":
        arr = load_csv_as_image(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D array, got shape={arr.shape} for {path}")
    return arr


def load_csv_as_image(path: Path) -> np.ndarray:
    df = pd.read_csv(path, header=None)
    numeric = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
    if numeric.empty:
        raise ValueError(f"CSV contains no numeric data: {path}")

    values = numeric.to_numpy(dtype=np.float32)
    if values.ndim != 2:
        raise ValueError(f"CSV could not be parsed as a numeric table: {path}")

    if values.shape[0] == 1 and values.shape[1] == 1:
        return values

    # Typical CST ASCII export may contain x/y coordinates plus a field column.
    if values.shape[1] >= 3:
        x = values[:, 0]
        y = values[:, 1]
        z = values[:, -1]
        ux = np.unique(x)
        uy = np.unique(y)
        if ux.size * uy.size == values.shape[0]:
            image = np.full((uy.size, ux.size), np.nan, dtype=np.float32)
            x_index = {val: idx for idx, val in enumerate(ux.tolist())}
            y_index = {val: idx for idx, val in enumerate(uy.tolist())}
            for xv, yv, zv in zip(x, y, z):
                image[y_index[float(yv)], x_index[float(xv)]] = float(zv)
            return np.nan_to_num(image, nan=0.0)

    if values.shape[0] == 1 or values.shape[1] == 1:
        flat = values.reshape(-1)
        side = int(np.sqrt(flat.size))
        if side * side == flat.size:
            return flat.reshape(side, side)
        return flat.reshape(1, -1)

    return values


def resize_nn(arr: np.ndarray, target_shape: tuple[int, int]) -> np.ndarray:
    if arr.shape == target_shape:
        return arr.astype(np.float32)
    src_h, src_w = arr.shape
    dst_h, dst_w = target_shape
    y_idx = np.clip(np.round(np.linspace(0, src_h - 1, dst_h)).astype(int), 0, src_h - 1)
    x_idx = np.clip(np.round(np.linspace(0, src_w - 1, dst_w)).astype(int), 0, src_w - 1)
    return arr[np.ix_(y_idx, x_idx)].astype(np.float32)


def normalize(arr: np.ndarray) -> np.ndarray:
    arr = np.nan_to_num(arr.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    arr_min = float(arr.min())
    arr_max = float(arr.max())
    if arr_max - arr_min < 1e-12:
        return np.zeros_like(arr, dtype=np.float32)
    return (arr - arr_min) / (arr_max - arr_min)


def info_entropy(arr: np.ndarray) -> float:
    hist, _ = np.histogram(arr.ravel(), bins=256, range=(0.0, 1.0), density=True)
    p = hist / (hist.sum() + 1e-12)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def compute_psnr(ref: np.ndarray, pred: np.ndarray) -> float:
    if peak_signal_noise_ratio is not None:
        return float(peak_signal_noise_ratio(ref, pred, data_range=1.0))

    mse = float(np.mean((ref - pred) ** 2))
    if mse <= 1e-12:
        return float("inf")
    return float(10.0 * np.log10(1.0 / mse))


def compute_ssim(ref: np.ndarray, pred: np.ndarray) -> float:
    if structural_similarity is not None:
        return float(structural_similarity(ref, pred, data_range=1.0))

    k1 = 0.01
    k2 = 0.03
    c1 = (k1 * 1.0) ** 2
    c2 = (k2 * 1.0) ** 2
    mu_x = float(np.mean(ref))
    mu_y = float(np.mean(pred))
    sigma_x = float(np.mean((ref - mu_x) ** 2))
    sigma_y = float(np.mean((pred - mu_y) ** 2))
    sigma_xy = float(np.mean((ref - mu_x) * (pred - mu_y)))
    numerator = (2.0 * mu_x * mu_y + c1) * (2.0 * sigma_xy + c2)
    denominator = (mu_x ** 2 + mu_y ** 2 + c1) * (sigma_x + sigma_y + c2)
    if abs(denominator) < 1e-12:
        return 1.0
    return float(numerator / denominator)


def compute_pair_metrics(ref: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    psnr = compute_psnr(ref, pred)
    ssim = compute_ssim(ref, pred)
    ie_ref = info_entropy(ref)
    ie_pred = info_entropy(pred)
    return {
        "psnr": psnr,
        "ssim": ssim,
        "ie_ref": ie_ref,
        "ie_pred": ie_pred,
        "ie_abs_diff": float(abs(ie_ref - ie_pred)),
    }


def main() -> None:
    args = parse_args()
    target = normalize(load_image_like(Path(args.target)))
    python_out = normalize(resize_nn(load_image_like(Path(args.python_output)), target.shape))
    cst_out = normalize(resize_nn(load_image_like(Path(args.cst_output)), target.shape))

    metrics = {
        "target_shape": list(target.shape),
        "paper_reference": PAPER_REFERENCE,
        "python_vs_target": compute_pair_metrics(target, python_out),
        "cst_vs_target": compute_pair_metrics(target, cst_out),
        "python_vs_cst": compute_pair_metrics(python_out, cst_out),
        "inputs": {
            "target": str(Path(args.target)),
            "python_output": str(Path(args.python_output)),
            "cst_output": str(Path(args.cst_output)),
        },
    }

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    out_json = METRICS_DIR / f"{args.out_prefix}_metrics.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Saved metrics JSON: {out_json}")
    print("python_vs_target:", metrics["python_vs_target"])
    print("cst_vs_target:", metrics["cst_vs_target"])
    print("python_vs_cst:", metrics["python_vs_cst"])


if __name__ == "__main__":
    main()
