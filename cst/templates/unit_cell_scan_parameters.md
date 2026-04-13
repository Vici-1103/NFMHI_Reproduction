# Unit-cell Scan Parameters

## Paper-aligned constants
- Cell size: `5 mm x 5 mm`
- Height range: `2 mm ~ 8 mm`
- Frequency point: `30 GHz`
- Material: `VeroWhitePlus`
- Material properties: `eps_r = 2.802`, `mu_r = 1`, `tanδ = 0.0357`
- Boundary family: `Master-Slave / Unit Cell + Floquet ports`

## Export target
- Required CSV path: `cst/results/unit_scan/phase_height_curve.csv`
- Required columns:
  - `height_mm`
  - `phase_rad`
  - `s21_mag`

## Important note
- The paper page images do not explicitly state the sweep step size.
- The CST automation script therefore keeps the step size configurable and records the chosen value in the final report.
