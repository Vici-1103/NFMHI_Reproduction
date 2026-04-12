# Project Specification

## Objective
This repository reproduces the workflow in the paper *Near-Field Microwave Holographic Imaging Using a Metamaterial-Based Diffraction Neural Network With Angular Spectrum-Assisted Computation*. The repository covers:

- target generation and DNN training in Python
- conversion from trained phase to printable unit height
- CST full-array model generation and field export

## Fixed Baseline

### Paper parameters used as the repository baseline
- target pattern: `GHZ`
- grid size: `60 x 60`
- layer count: `1`
- cell size: `5 mm`
- operating frequency: `30 GHz`
- wavelength: `10 mm`
- propagation distance from the zero-phase reference plane: `100 mm`
- optimizer: `Adam`
- learning rate: `0.05`
- epoch count: `1000`
- printable material: `VeroWhitePlus`
- relative permittivity: `2.802`
- relative permeability: `1`
- loss tangent: `0.0357`
- printable height range: `2 mm` to `8 mm`
- zero-phase reference height: `2 mm`

### Repository implementation choices
- canonical target file: `python/data/targets/target_GHZ_60x60.npy`
- default training seed: `42`
- full-array monitor plane: `z = 102 mm`
- CST export band for validation: `29-31 GHz`

## Interfaces

### Primary inputs
- target image: `python/data/targets/target_GHZ_60x60.npy`
- wrapped unit-cell scan: `cst/results/unit_scan/phase_height_curve.csv`
- default configuration: `python/src/config/defaults.yaml`

### Primary generated outputs
- trained phase map: `python/outputs/phase_maps/phase_matrix.npy`
- mapped height matrix: `python/outputs/height_maps/height_matrix.csv`
- unwrapped unit-cell curve: `python/outputs/height_maps/phase_height_curve_unwrapped.csv`
- training figure: `python/outputs/figures/dnn_train_result.png`
- training metrics: `python/outputs/metrics/dnn_train_metrics.json`
- CST field export: `cst/results/array_sim/field_plane_30GHz_100mm.csv`

## Interpretation Notes
- The height mapping used by this repository is defined from the additional phase relative to `h = 2 mm`.
- The wrapped unit-cell phase exported from CST is not used directly for full-array height mapping. It is unwrapped first and converted into a monotonic additional-phase curve.
- The target imaging plane is defined as `100 mm` after the zero-phase reference plane. Because the reference plane is at `h = 2 mm`, the CST monitor is placed at `z = 102 mm`.

## Acceptance References
- Paper reference metrics for the DNN result: `IE = 0.6834`, `PSNR = 10.47 dB`
- The repository does not claim exact parity where the paper does not publish enough implementation detail, but all exposed parameters are aligned to the published values above.
