# NFMHI Reproduction

This repository reproduces the paper *Near-Field Microwave Holographic Imaging Using a Metamaterial-Based Diffraction Neural Network With Angular Spectrum-Assisted Computation* with a single baseline:

- target pattern: `GHZ`
- grid: `60 x 60`
- frequency: `30 GHz`
- wavelength: `10 mm`
- cell size: `5 mm`
- imaging distance: `100 mm`
- printable height range: `2-8 mm`
- material: `VeroWhitePlus`, `eps_r = 2.802`, `mu_r = 1`, `tan_delta = 0.0357`

## Key Files
- spec: [docs/project_spec.md](docs/project_spec.md)
- training script: [python/scripts/train_dnn.py](python/scripts/train_dnn.py)
- phase-to-height mapping: [python/scripts/phase_to_height.py](python/scripts/phase_to_height.py)
- CST automation: [python/scripts/cst_pipeline.py](python/scripts/cst_pipeline.py)
- server macro: [cst/macros/build_full_array_from_height_csv_cst2021.bas](cst/macros/build_full_array_from_height_csv_cst2021.bas)
- server workflow: [docs/cst2021_full_array_workflow.md](docs/cst2021_full_array_workflow.md)

## Reproduction Flow
1. Generate or confirm the `GHZ` target in `python/data/targets/`.
2. Train the phase mask with `python/scripts/train_dnn.py`.
3. Convert the trained phase map into heights with `python/scripts/phase_to_height.py`.
4. Build the full-array CST model:
   - locally with `python/scripts/cst_pipeline.py`, or
   - on the server by importing `cst/macros/build_full_array_from_height_csv_cst2021.bas` into a new empty project and changing `CSV_PATH`.
5. Run the CST solver and export the target-plane field result at `z = 102 mm`.
6. Compare Python and CST results with `python/scripts/compute_metrics.py`.

## Important Outputs
- target image: [python/data/targets/target_GHZ_60x60.npy](python/data/targets/target_GHZ_60x60.npy)
- trained phase map: [python/outputs/phase_maps/phase_matrix.npy](python/outputs/phase_maps/phase_matrix.npy)
- height matrix: [python/outputs/height_maps/height_matrix.csv](python/outputs/height_maps/height_matrix.csv)
- unwrapped scan curve: [python/outputs/height_maps/phase_height_curve_unwrapped.csv](python/outputs/height_maps/phase_height_curve_unwrapped.csv)
- Python intensity: [python/outputs/figures/dnn_train_result.png](python/outputs/figures/dnn_train_result.png)
- CST scan curve: [cst/results/unit_scan/phase_height_curve.csv](cst/results/unit_scan/phase_height_curve.csv)
- CST field export: [cst/results/array_sim/field_plane_30GHz_100mm.csv](cst/results/array_sim/field_plane_30GHz_100mm.csv)

## Evaluation Reference
The paper reports these DNN reference values:

- `IE = 0.6834`
- `PSNR = 10.47 dB`

They are useful as comparison targets, not as strict pass/fail thresholds for every CST environment.
