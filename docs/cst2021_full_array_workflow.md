# CST 2021 Full-array Workflow

This workflow is separate from the CST 2026 automation path. It exists for environments where CST 2021 is available but `cst.interface` automation is not usable.

## Inputs
- height matrix: `python/outputs/height_maps/height_matrix.csv`
- CST 2021 macro: `cst/macros/build_full_array_from_height_csv_cst2021.bas`

## Procedure
1. Start CST Studio Suite 2021.
2. Create a new MW Studio project.
3. Open `Macros -> Edit Macros`.
4. Import `cst/macros/build_full_array_from_height_csv_cst2021.bas`.
5. Edit `CSV_PATH` at the top of the macro so it points to the height CSV on the server.
6. Run the macro.
7. Save the generated project under a new name, for example `nfmhi_full_array_60x60_cst2021.cst`.
8. Run the solver in CST 2021.
9. Export the field monitor manually or with the existing export macro after the solve completes.

## Notes
- This path generates a new CST 2021-native project. It does not attempt to open the CST 2026 project archive.
- The macro assumes a `60 x 60` array, `5 mm` cell pitch, and height values in the range `2 mm` to `8 mm`.
- The configured monitor plane is `z = 102 mm`, matching the current repository baseline.
