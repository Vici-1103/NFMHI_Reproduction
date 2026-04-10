# Project Specification

## Objective
This repository reproduces the workflow described in the paper *Near-Field Microwave Holographic Imaging Using a Metamaterial-Based Diffraction Neural Network With Angular Spectrum-Assisted Computation*. The current repository scope covers:

- target generation and diffraction-network training in Python
- phase-to-height conversion using CST-derived unit-cell data
- CST project preparation for unit-cell scanning and full-array validation

This document records the project baseline used in this repository. It is not a paper summary and does not attempt to restate all material from the publication.

## Fixed Baseline

### Imaging and network
- target pattern: `GHZ`
- grid size: `60 x 60`
- layer count: `1`
- cell size: `5 mm`
- operating frequency: `30 GHz`
- wavelength: `10 mm`
- propagation distance: `100 mm`

### Training
- optimizer: `Adam`
- learning rate: `0.05`
- epoch count: `1000`
- random seed: `42`

### Unit-cell and material
- height range: `2 mm` to `8 mm`
- substrate / printable material: `VeroWhitePlus`
- relative permittivity: `2.802`
- relative permeability: `1`
- loss tangent: `0.0557`

## Repository Interfaces

### Primary inputs
- target image: `python/data/targets/target_GHZ_60x60.npy`
- unit-cell scan data: `cst/results/unit_scan/phase_height_curve.csv`
- default configuration: `python/src/config/defaults.yaml`

### Primary generated outputs
- trained phase map: `python/outputs/phase_maps/phase_matrix.npy`
- mapped height matrix: `python/outputs/height_maps/height_matrix.csv`
- training visualization: `python/outputs/figures/dnn_train_result.png`
- training metrics: `python/outputs/metrics/dnn_train_metrics.json`

### CST assets
- full-array project archive: `cst/full_array/nfmhi_full_array_60x60.cst`
- unit-cell project workspace: `cst/unit_cell/nfmhi_unit_cell_30ghz/`
- CST automation entrypoint: `python/scripts/cst_pipeline.py`

## Interpretation Notes
- The repository uses `GHZ` as the canonical reproduction target.
- The full-array monitor plane is treated as a project-level configuration item. When the current CST setup is discussed in repository documents, the working monitor location is `z = 102 mm`.
- The unit-cell height sweep resolution is implementation-defined in this repository and should not be interpreted as a directly quoted paper parameter unless separately cited.

## Out of Scope
- long-form derivation of the paper method
- archival storage of CST solver caches or large field-monitor outputs
- claims of exact paper parity where the publication does not provide enough implementation detail
