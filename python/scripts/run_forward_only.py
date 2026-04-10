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
import numpy as np
from PIL import Image

TARGET_DIR = PROJECT_ROOT / "python" / "data" / "targets"
FIG_DIR = PROJECT_ROOT / "python" / "outputs" / "figures"
PHASE_DIR = PROJECT_ROOT / "python" / "outputs" / "phase_maps"



def load_target(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        arr = np.load(path).astype(np.float32)
    else:
        arr = np.array(Image.open(path).convert("L"), dtype=np.float32) / 255.0
    if arr.ndim != 2:
        raise ValueError("Target must be a 2D grayscale array.")
    return arr



def angular_spectrum_propagate(
    field_in: np.ndarray,
    dx: float,
    wavelength: float,
    z: float,
) -> np.ndarray:
    nrows, ncols = field_in.shape
    fx = np.fft.fftfreq(ncols, d=dx)
    fy = np.fft.fftfreq(nrows, d=dx)
    fx_grid, fy_grid = np.meshgrid(fx, fy)

    k = 2.0 * np.pi / wavelength
    kx = 2.0 * np.pi * fx_grid
    ky = 2.0 * np.pi * fy_grid
    kz_sq = k ** 2 - kx ** 2 - ky ** 2
    kz = np.sqrt(kz_sq.astype(np.complex128))

    transfer = np.exp(1j * kz * z)
    field_out = np.fft.ifft2(np.fft.fft2(field_in) * transfer)
    return field_out



def plot_and_save(target: np.ndarray, phase: np.ndarray, intensity: np.ndarray, out_prefix: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    PHASE_DIR.mkdir(parents=True, exist_ok=True)

    phase_wrapped = np.mod(phase, 2 * np.pi)
    intensity_norm = intensity / (intensity.max() + 1e-8)

    np.save(PHASE_DIR / f"{out_prefix}_phase.npy", phase_wrapped.astype(np.float32))
    np.save(FIG_DIR / f"{out_prefix}_intensity.npy", intensity_norm.astype(np.float32))

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].imshow(target, cmap="gray")
    axes[0].set_title("Target")
    axes[1].imshow(phase_wrapped, cmap="twilight")
    axes[1].set_title("Random Phase [0, 2π)")
    axes[2].imshow(intensity_norm, cmap="inferno")
    axes[2].set_title("Forward Output Intensity")
    for ax in axes:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{out_prefix}_overview.png", dpi=180, bbox_inches="tight")
    plt.close(fig)



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Forward-only angular spectrum check for the NFMHI project.")
    parser.add_argument(
        "--target",
        type=str,
        default=str(TARGET_DIR / "target_GHZ_60x60.npy"),
        help="Path to target .npy or .png file.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cell-size-mm", type=float, default=5.0, help="Paper default LN = 5 mm.")
    parser.add_argument("--wavelength-mm", type=float, default=10.0, help="Paper default λ = 10 mm.")
    parser.add_argument("--distance-mm", type=float, default=100.0, help="Paper default z = 100 mm.")
    parser.add_argument("--out-prefix", type=str, default="forward_only")
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    target_path = Path(args.target)
    target = load_target(target_path)

    rng = np.random.default_rng(args.seed)
    phase = rng.uniform(0.0, 2.0 * np.pi, size=target.shape).astype(np.float32)

    input_amplitude = np.ones_like(target, dtype=np.float32)
    field_in = input_amplitude * np.exp(1j * phase)

    field_out = angular_spectrum_propagate(
        field_in=field_in,
        dx=args.cell_size_mm * 1e-3,
        wavelength=args.wavelength_mm * 1e-3,
        z=args.distance_mm * 1e-3,
    )
    intensity = np.abs(field_out) ** 2

    plot_and_save(target=target, phase=phase, intensity=intensity, out_prefix=args.out_prefix)

    print("Forward-only propagation finished.")
    print(f"Target path: {target_path}")
    print(f"Target shape: {target.shape}")
    print(f"cell size = {args.cell_size_mm} mm, wavelength = {args.wavelength_mm} mm, distance = {args.distance_mm} mm")
    print(f"Saved overview figure to: {FIG_DIR / f'{args.out_prefix}_overview.png'}")


if __name__ == "__main__":
    main()
