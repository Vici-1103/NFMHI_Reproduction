# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Reproduces the paper *Near-Field Microwave Holographic Imaging Using a Metamaterial-Based Diffraction Neural Network With Angular Spectrum-Assisted Computation*. A single fixed baseline is targeted (GHZ pattern, 60x60 grid, 30 GHz, 100 mm imaging distance, VeroWhitePlus material, printable height 2-8 mm). All per-parameter values live in [python/src/config/defaults.yaml](python/src/config/defaults.yaml) and must stay aligned with the paper - see [docs/project_spec.md](docs/project_spec.md).

## Environment

- Python: `V:\Apps\conda_envs\cst2020_env\python.exe` (Python 3.8.20, TensorFlow 2.9.0). Set `$env:NFMHI_PYTHON` to that path; CST scripts expect it.
- CST Studio Suite: `V:\Apps\CST Studio Suite 2026` (Python automation via `cst.interface`; server macro targets CST 2021).
- Dependencies: [env/requirements.txt](env/requirements.txt).

## Reproduction pipeline (run in order)

```bash
# 1. Generate the 60x60 GHZ target
$NFMHI_PYTHON python/scripts/generate_target.py --pattern GHZ

# 2. Train phase mask (Adam, lr=0.05, 1000 epochs, MMSE loss per Eq. 5)
$NFMHI_PYTHON python/scripts/train_dnn.py

# 3. Map trained phase to printable heights using the unwrapped CST unit-cell scan
$NFMHI_PYTHON python/scripts/phase_to_height.py

# 4. Build/run CST (two paths):
#    a. Local automation (requires cst.interface):
$NFMHI_PYTHON python/scripts/cst_pipeline.py boot-test
$NFMHI_PYTHON python/scripts/cst_pipeline.py unit-scan --run-solver
$NFMHI_PYTHON python/scripts/cst_pipeline.py full-array-export --run-solver --export-results
#    b. Server workflow: import cst/macros/build_full_array_from_height_csv_cst2021.bas
#       into an empty MW Studio project, edit CSV_PATH, run macro. See docs/cst2021_full_array_workflow.md

# 5. Compare Python vs CST vs target
$NFMHI_PYTHON python/scripts/compute_metrics.py
```

`python/scripts/run_forward_only.py` is a NumPy-only angular-spectrum forward pass used for diagnostics - it does not train.

## Architecture

The reproduction chain has three stages whose I/O contracts are load-bearing; changing one without the others breaks the pipeline.

**Stage 1 - Phase training ([train_dnn.py](python/scripts/train_dnn.py)):** TensorFlow forward model is `IFFT2(FFT2(exp(i*phi)) * H)` where `H = exp(i*kz*z)` from the angular spectrum (see `make_transfer_function` and `propagate_with_phase`). Loss is MMSE on unit-sum-normalized intensity vs. target (Eq. 5 of the paper). Writes `python/outputs/phase_maps/phase_matrix.npy` (wrapped to [0, 2pi]) plus a 2x2 result figure matching the paper's Fig. 4.

**Stage 2 - Phase-to-height mapping ([phase_to_height.py](python/scripts/phase_to_height.py)):** Reads the CST unit-cell S21 sweep at `cst/results/unit_scan/phase_height_curve.csv`, unwraps it, and converts to a monotonic *additional-phase* curve referenced to `h = 2 mm` (the zero-phase reference height). Default `paper_interp` method does 1D interpolation from wrapped trained phase -> height. `linear` method is diagnostic only. Writes `python/outputs/height_maps/height_matrix.csv` (60x60, no header) and `phase_height_curve_unwrapped.csv`.

**Stage 3 - CST project generation:** Two code paths that must stay semantically equivalent:
- [python/scripts/cst_pipeline.py](python/scripts/cst_pipeline.py) drives CST via `cst.interface` for boot-test / unit-scan / full-array-export modes.
- [cst/macros/build_full_array_from_height_csv_cst2021.bas](cst/macros/build_full_array_from_height_csv_cst2021.bas) is a standalone VBA macro for the older CST 2021 server. Only `CSV_PATH` is meant to change.

Both produce: `expanded open` boundaries on all six faces, +z plane-wave excitation, VeroWhitePlus bricks per cell, E-field monitor at `z = 102 mm` (= 2 mm reference + 100 mm propagation), solver band 29-31 GHz. Expected export: `cst/results/array_sim/field_plane_30GHz_100mm.csv`.

## Conventions

- Config single source of truth is [defaults.yaml](python/src/config/defaults.yaml); both `train_dnn.py` and `phase_to_height.py` parse it with a hand-rolled YAML loader (scripts are standalone - there is no `src` package to import from).
- All scripts are CLI-driven with argparse; defaults are sourced from the YAML so you usually don't need flags.
- Units: mm for lengths, GHz for frequencies. When passing to physics code, convert mm -> m (see `cell_size_mm * 1e-3` in `train_dnn.make_transfer_function`).
- Height matrix CSV is strictly 60x60, header-less, values in [2, 8] mm. Both CST entry points assert this.
- CST result CSVs must be real solver exports. Per [cst/README.md](cst/README.md), missing is acceptable; placeholder files masquerading as results are not.
- The paper reference metrics `IE = 0.6834`, `PSNR = 10.47 dB` are comparison targets, not pass/fail gates.

## Reference reading

- [docs/project_spec.md](docs/project_spec.md) - full parameter lock list and interpretation notes (why the monitor is at 102 mm, why phase is referenced from h=2 mm).
- [docs/cst2021_full_array_workflow.md](docs/cst2021_full_array_workflow.md) - server macro procedure.
- [cst/templates/full_array_simulation_checklist.md](cst/templates/full_array_simulation_checklist.md) / [cst/templates/unit_cell_scan_parameters.md](cst/templates/unit_cell_scan_parameters.md) - paper-alignment checklists.
