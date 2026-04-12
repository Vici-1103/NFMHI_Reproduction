from __future__ import annotations

import argparse
import json
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
from PIL import Image
try:
    import tensorflow as tf
except ImportError:  # pragma: no cover - environment-dependent import
    tf = None

TARGET_DIR = PROJECT_ROOT / "python" / "data" / "targets"
OUTPUT_DIR = PROJECT_ROOT / "python" / "outputs"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"
FIG_DIR = OUTPUT_DIR / "figures"
PHASE_DIR = OUTPUT_DIR / "phase_maps"
METRIC_DIR = OUTPUT_DIR / "metrics"
LOG_DIR = OUTPUT_DIR / "logs"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "python" / "src" / "config" / "defaults.yaml"
PAPER_INTENSITY_MAX = 3.76



def load_target(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        arr = np.load(path).astype(np.float32)
    else:
        arr = np.array(Image.open(path).convert("L"), dtype=np.float32) / 255.0
    if arr.ndim != 2:
        raise ValueError("Target must be a 2D grayscale array.")
    arr = np.clip(arr, 0.0, 1.0)
    return arr


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

    for raw_line in DEFAULT_CONFIG_PATH.read_text(encoding="utf-8").splitlines():
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



def build_frequency_grids(shape: tuple[int, int], dx: float) -> tuple[np.ndarray, np.ndarray]:
    nrows, ncols = shape
    fx = np.fft.fftfreq(ncols, d=dx)
    fy = np.fft.fftfreq(nrows, d=dx)
    return np.meshgrid(fx, fy)



def make_transfer_function(shape: tuple[int, int], dx: float, wavelength: float, z: float) -> tf.Tensor:
    fx_grid, fy_grid = build_frequency_grids(shape, dx)
    k = 2.0 * np.pi / wavelength
    kx = 2.0 * np.pi * fx_grid
    ky = 2.0 * np.pi * fy_grid
    kz_sq = (k ** 2 - kx ** 2 - ky ** 2).astype(np.complex64)
    kz = np.sqrt(kz_sq)
    transfer = np.exp(1j * kz * z).astype(np.complex64)
    return tf.constant(transfer, dtype=tf.complex64)



def propagate_with_phase(phi: tf.Tensor, transfer: tf.Tensor) -> tf.Tensor:
    phase_wrapped = tf.math.floormod(phi, 2.0 * np.pi)
    field_in = tf.complex(tf.math.cos(phase_wrapped), tf.math.sin(phase_wrapped))
    field_in = tf.cast(field_in, tf.complex64)
    field_out = tf.signal.ifft2d(tf.signal.fft2d(field_in) * transfer)
    intensity = tf.math.abs(field_out) ** 2
    intensity = intensity / (tf.reduce_max(intensity) + 1e-8)
    return intensity



def _configure_plot_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "STIXGeneral",
            "mathtext.fontset": "stix",
            "axes.labelsize": 18,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
        }
    )


def _add_panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(0.5, -0.20, label, ha="center", va="top", transform=ax.transAxes, fontsize=18)


def plot_results(target: np.ndarray, intensity: np.ndarray, phase: np.ndarray, loss_hist: list[float], out_prefix: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    _configure_plot_style()

    phase_wrapped = np.mod(phase, 2.0 * np.pi)
    intensity_norm = intensity / (float(np.max(intensity)) + 1e-8)
    intensity_display = intensity_norm * PAPER_INTENSITY_MAX
    loss_arr = np.asarray(loss_hist, dtype=np.float64)
    extent_mm = (0.0, 300.0, 0.0, 300.0)
    ticks_mm = np.arange(0, 301, 50)
    paper_red = LinearSegmentedColormap.from_list("paper_red", ["#000000", "#260000", "#7a0000", "#ff0000"])

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.6))
    ax_target, ax_intensity, ax_phase, ax_loss = axes.ravel()

    im_target = ax_target.imshow(
        target,
        cmap=paper_red,
        origin="lower",
        vmin=0.0,
        vmax=1.0,
        extent=extent_mm,
        interpolation="nearest",
    )
    ax_target.set_xlabel(r"$x/mm$")
    ax_target.set_ylabel(r"$y/mm$")
    ax_target.set_xticks(ticks_mm)
    ax_target.set_yticks(ticks_mm)
    cbar_target = fig.colorbar(im_target, ax=ax_target, fraction=0.046, pad=0.04)
    cbar_target.set_ticks([0.0, 0.5, 1.0])
    _add_panel_label(ax_target, "(a)")

    im_intensity = ax_intensity.imshow(
        intensity_display,
        cmap=paper_red,
        origin="lower",
        vmin=0.0,
        vmax=PAPER_INTENSITY_MAX,
        extent=extent_mm,
        interpolation="nearest",
    )
    ax_intensity.set_xlabel(r"$x/mm$")
    ax_intensity.set_ylabel(r"$y/mm$")
    ax_intensity.set_xticks(ticks_mm)
    ax_intensity.set_yticks(ticks_mm)
    cbar_intensity = fig.colorbar(im_intensity, ax=ax_intensity, fraction=0.046, pad=0.04)
    cbar_intensity.set_ticks([0.0, PAPER_INTENSITY_MAX / 2.0, PAPER_INTENSITY_MAX])
    _add_panel_label(ax_intensity, "(b)")

    im_phase = ax_phase.imshow(
        phase_wrapped,
        cmap="viridis",
        origin="lower",
        vmin=0.0,
        vmax=2.0 * np.pi,
        extent=extent_mm,
        interpolation="nearest",
    )
    ax_phase.set_xlabel(r"$x/mm$")
    ax_phase.set_ylabel(r"$y/mm$")
    ax_phase.set_xticks(ticks_mm)
    ax_phase.set_yticks(ticks_mm)
    cbar_phase = fig.colorbar(im_phase, ax=ax_phase, fraction=0.046, pad=0.04)
    cbar_phase.set_ticks([0.0, np.pi, 2.0 * np.pi])
    cbar_phase.set_ticklabels(["0", r"$\pi$", r"$2\pi$"])
    _add_panel_label(ax_phase, "(c)")

    ax_loss.plot(np.arange(1, len(loss_arr) + 1), loss_arr, color="red", linewidth=1.0)
    ax_loss.set_xlabel("Epoch")
    ax_loss.set_ylabel("Loss")
    ax_loss.set_xlim(0, len(loss_arr))
    ax_loss.set_ylim(0.0, float(np.max(loss_arr)) * 1.05)
    ax_loss.set_xticks([0, 200, 400, 600, 800, 1000])
    _add_panel_label(ax_loss, "(d)")

    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{out_prefix}_result.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    plt.figure(figsize=(6, 4))
    plt.plot(np.arange(1, len(loss_arr) + 1), loss_arr, color="red", linewidth=1.0)
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.xlim(0, len(loss_arr))
    plt.ylim(0.0, float(np.max(loss_arr)) * 1.05)
    plt.tight_layout()
    plt.savefig(FIG_DIR / f"{out_prefix}_loss_curve.png", dpi=180, bbox_inches="tight")
    plt.close()

    np.save(PHASE_DIR / f"{out_prefix}_phase.npy", phase_wrapped.astype(np.float32))
    np.save(PHASE_DIR / "phase_matrix.npy", phase_wrapped.astype(np.float32))
    np.save(FIG_DIR / f"{out_prefix}_intensity.npy", intensity_display.astype(np.float32))
    np.save(FIG_DIR / "dnn_train_intensity.npy", intensity_display.astype(np.float32))



def parse_args() -> argparse.Namespace:
    defaults = load_defaults()
    training_defaults = defaults["training"]
    sim_defaults = defaults["simulation"]
    project_defaults = defaults["project"]

    parser = argparse.ArgumentParser(description="Train a diffraction phase mask for the NFMHI project.")
    parser.add_argument(
        "--target",
        type=str,
        default=str(TARGET_DIR / "target_GHZ_60x60.npy"),
        help="Path to target .npy or .png file.",
    )
    parser.add_argument("--epochs", type=int, default=int(training_defaults["epochs"]))
    parser.add_argument("--lr", type=float, default=float(training_defaults["learning_rate"]))
    parser.add_argument("--cell-size-mm", type=float, default=float(sim_defaults["cell_size_mm"]))
    parser.add_argument("--wavelength-mm", type=float, default=float(sim_defaults["wavelength_mm"]))
    parser.add_argument("--distance-mm", type=float, default=float(sim_defaults["propagation_distance_mm"]))
    parser.add_argument("--seed", type=int, default=int(project_defaults["random_seed"]))
    parser.add_argument("--loss-type", choices=["mse", "mmse"], default=str(training_defaults["loss_type"]).lower())
    parser.add_argument("--save-every", type=int, default=100, help="Print progress every N epochs.")
    parser.add_argument("--out-prefix", type=str, default="dnn_train")
    return parser.parse_args()



def compute_loss(intensity: tf.Tensor, target: tf.Tensor, loss_type: str) -> tf.Tensor:
    if loss_type == "mse":
        return tf.reduce_mean((intensity - target) ** 2)

    target_energy = target / (tf.reduce_sum(target) + 1e-8)
    output_energy = intensity / (tf.reduce_sum(intensity) + 1e-8)
    return tf.reduce_mean((output_energy - target_energy) ** 2)



def main() -> None:
    args = parse_args()
    if tf is None:
        raise RuntimeError("TensorFlow is required to run train_dnn.py. Install the dependencies from env/requirements.txt.")
    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)

    target_path = Path(args.target)
    target_np = load_target(target_path)
    target_tf = tf.constant(target_np, dtype=tf.float32)

    transfer = make_transfer_function(
        shape=target_np.shape,
        dx=args.cell_size_mm * 1e-3,
        wavelength=args.wavelength_mm * 1e-3,
        z=args.distance_mm * 1e-3,
    )

    init_phi = tf.random.uniform(
        shape=target_np.shape,
        minval=0.0,
        maxval=2.0 * np.pi,
        dtype=tf.float32,
        seed=args.seed,
    )
    phi = tf.Variable(init_phi, trainable=True, name="phase_mask")
    optimizer = tf.keras.optimizers.Adam(learning_rate=args.lr)

    loss_hist: list[float] = []
    best_loss = float("inf")
    best_phase = None
    best_intensity = None

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    METRIC_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        with tf.GradientTape() as tape:
            intensity = propagate_with_phase(phi, transfer)
            loss = compute_loss(intensity, target_tf, args.loss_type)

        grads = tape.gradient(loss, [phi])
        optimizer.apply_gradients(zip(grads, [phi]))

        loss_value = float(loss.numpy())
        loss_hist.append(loss_value)

        if loss_value < best_loss:
            best_loss = loss_value
            best_phase = np.mod(phi.numpy(), 2.0 * np.pi)
            best_intensity = intensity.numpy()

        if epoch % args.save_every == 0 or epoch == 1 or epoch == args.epochs:
            print(f"Epoch {epoch:4d}/{args.epochs} | loss = {loss_value:.8f}")

    if best_phase is None or best_intensity is None:
        raise RuntimeError("Training finished without valid outputs.")

    plot_results(
        target=target_np,
        intensity=best_intensity,
        phase=best_phase,
        loss_hist=loss_hist,
        out_prefix=args.out_prefix,
    )

    ckpt_path = CHECKPOINT_DIR / f"{args.out_prefix}_phase.npy"
    np.save(ckpt_path, best_phase.astype(np.float32))

    metrics = {
        "best_loss": best_loss,
        "epochs": args.epochs,
        "learning_rate": args.lr,
        "optimizer": "adam",
        "loss_type": args.loss_type,
        "target": str(target_path),
        "cell_size_mm": args.cell_size_mm,
        "wavelength_mm": args.wavelength_mm,
        "distance_mm": args.distance_mm,
        "seed": args.seed,
    }
    with open(METRIC_DIR / f"{args.out_prefix}_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with open(LOG_DIR / f"{args.out_prefix}_train.log", "w", encoding="utf-8") as f:
        f.write("NFMHI DNN training summary\n")
        for key, value in metrics.items():
            f.write(f"{key}: {value}\n")

    print("Training finished.")
    print(f"Best loss: {best_loss:.8f}")
    print(f"Saved best phase map to: {ckpt_path}")
    print(f"Saved result figure to: {FIG_DIR / f'{args.out_prefix}_result.png'}")
    print(f"Saved loss curve to: {FIG_DIR / f'{args.out_prefix}_loss_curve.png'}")


if __name__ == "__main__":
    main()
