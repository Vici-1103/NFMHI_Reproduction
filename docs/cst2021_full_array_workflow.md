# Server Full-array Workflow

## Inputs
- height matrix: `python/outputs/height_maps/height_matrix.csv`
- CST macro: `cst/macros/build_full_array_from_height_csv_cst2021.bas`

## Procedure
1. Start CST Studio Suite.
2. Create a new empty MW Studio project.
3. Open `Macros -> Edit Macros`.
4. Import `cst/macros/build_full_array_from_height_csv_cst2021.bas`.
5. Edit `CSV_PATH` at the top of the macro so it points to the server copy of `height_matrix.csv`.
6. Run the macro once.
7. Save the generated project, for example as `nfmhi_full_array_60x60.cst`.
8. Start the time-domain solver.
9. Open the `E-Field` monitor at `z = 102 mm`.
10. Export the target-plane result as CSV if evaluation is needed.

## What the macro configures automatically
- units: `mm / GHz / ns`
- material: `VeroWhitePlus`
- background: normal
- boundaries: six faces `expanded open`
- solver band: `29-31 GHz`
- plane-wave excitation
- target-plane monitor at `z = 102 mm`
- `60 x 60` brick array built from the height CSV

## Validation
- The height CSV must be exactly `60 x 60`.
- The height values must stay in `[2, 8] mm`.
- The expected field result is the target-plane `E-Field` distribution used for the `GHZ` image reconstruction.
