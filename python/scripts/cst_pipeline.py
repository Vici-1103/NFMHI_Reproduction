from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

import cst.interface


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CST_INSTALL_DIR = Path(r"V:\Apps\CST Studio Suite 2026")
CST_EXE = CST_INSTALL_DIR / "CST DESIGN ENVIRONMENT.exe"

UNIT_CELL_PROJECT = PROJECT_ROOT / "cst" / "unit_cell" / "nfmhi_unit_cell_30ghz.cst"
FULL_ARRAY_PROJECT = PROJECT_ROOT / "cst" / "full_array" / "nfmhi_full_array_60x60.cst"
UNIT_SCAN_CSV = PROJECT_ROOT / "cst" / "results" / "unit_scan" / "phase_height_curve.csv"
FIELD_PLANE_CSV = PROJECT_ROOT / "cst" / "results" / "array_sim" / "field_plane_30GHz_100mm.csv"
HEIGHT_MATRIX_CSV = PROJECT_ROOT / "python" / "outputs" / "height_maps" / "height_matrix.csv"
PIPELINE_REPORT = PROJECT_ROOT / "docs" / "reports" / "cst_pipeline_status.json"

GRID_SIZE = 60
CELL_SIZE_MM = 5.0
FREQ_GHZ = 30.0
FREQ_MIN_GHZ = 29.0
FREQ_MAX_GHZ = 31.0
WAVELENGTH_MM = 10.0
PROPAGATION_DISTANCE_MM = 100.0
HMIN_MM = 2.0
HMAX_MM = 8.0
MONITOR_Z_MM = HMIN_MM + PROPAGATION_DISTANCE_MM

MATERIAL_NAME = "VeroWhitePlus"
EPSILON_R = 2.802
MU_R = 1.0
TAN_DELTA = 0.0557


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CST automation entry for the NFMHI paper reproduction.")
    parser.add_argument("mode", choices=["boot-test", "unit-scan", "full-array-export"])
    parser.add_argument("--run-solver", action="store_true", help="Run the CST solver after project generation.")
    parser.add_argument("--export-results", action="store_true", help="Export results after solver completion.")
    parser.add_argument(
        "--height-step-mm",
        type=float,
        default=0.25,
        help="Unit-cell sweep step. The paper images do not explicitly state this value; keep it documented.",
    )
    parser.add_argument("--monitor-z-mm", type=float, default=MONITOR_Z_MM)
    parser.add_argument("--height-csv", type=str, default=str(HEIGHT_MATRIX_CSV))
    parser.add_argument("--field-tree-item", type=str, default="")
    parser.add_argument("--unit-project", type=str, default=str(UNIT_CELL_PROJECT))
    parser.add_argument("--array-project", type=str, default=str(FULL_ARRAY_PROJECT))
    return parser.parse_args()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_status(mode: str, status: dict[str, object]) -> None:
    ensure_parent(PIPELINE_REPORT)
    payload: dict[str, object]
    if PIPELINE_REPORT.exists():
        payload = json.loads(PIPELINE_REPORT.read_text(encoding="utf-8"))
    else:
        payload = {}
    payload[mode] = status
    PIPELINE_REPORT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def new_project() -> tuple[cst.interface.DesignEnvironment, object]:
    de = cst.interface.DesignEnvironment()
    project = de.new_mws()
    project.model3d.allow_history_commands()
    return de, project


def save_project(project: object, target: Path) -> Path:
    ensure_parent(target)
    try:
        if target.exists():
            target.unlink()
        extracted_dir = target.with_suffix("")
        if extracted_dir.exists():
            shutil.rmtree(extracted_dir, ignore_errors=True)
        project.save(str(target))
        return target
    except RuntimeError:
        alt_target = target.parent / f"{target.stem}_autosave{target.suffix}"
        if alt_target.exists():
            alt_target.unlink()
        alt_extracted_dir = alt_target.with_suffix("")
        if alt_extracted_dir.exists():
            shutil.rmtree(alt_extracted_dir, ignore_errors=True)
        project.save(str(alt_target))
        return alt_target


def write_history(project: object, title: str, command: str) -> None:
    project.model3d.add_to_history(title, command)


def configure_common_units(project: object) -> None:
    write_history(
        project,
        "Project Units",
        """
With Units
    .Geometry "mm"
    .Frequency "GHz"
    .Time "ns"
End With
With Background
    .ResetBackground
    .Type "Normal"
    .Epsilon "1.0"
    .Mu "1.0"
    .XminSpace "0.0"
    .XmaxSpace "0.0"
    .YminSpace "0.0"
    .YmaxSpace "0.0"
    .ZminSpace "0.0"
    .ZmaxSpace "0.0"
End With
""".strip(),
    )


def create_verowhiteplus_material(project: object) -> None:
    write_history(
        project,
        "Material VeroWhitePlus",
        f"""
With Material
    .Reset
    .Name "{MATERIAL_NAME}"
    .Folder ""
    .Type "Normal"
    .FrqType "all"
    .MaterialUnit "Frequency", "GHz"
    .MaterialUnit "Geometry", "mm"
    .MaterialUnit "Time", "ns"
    .Epsilon "{EPSILON_R}"
    .Mue "{MU_R}"
    .TanD "{TAN_DELTA}"
    .TanDGiven "True"
    .TanDModel "ConstTanD"
    .Colour "0.80", "0.93", "0.95"
    .Create
End With
""".strip(),
    )


def create_unit_cell_project(project: object) -> None:
    project.model3d.SelectQuickStartGuide("Frequency Domain")
    project.model3d.ChangeSolverType("HF Frequency Domain")
    project.model3d.StoreParameterWithDescription("L_cell", str(CELL_SIZE_MM), "Paper LN cell size in mm")
    project.model3d.StoreParameterWithDescription("h", str(HMIN_MM), "Unit-cell height in mm")
    project.model3d.StoreParameterWithDescription("f0", str(FREQ_GHZ), "Paper center frequency in GHz")
    project.model3d.StoreParameterWithDescription("h_min", str(HMIN_MM), "Minimum printable height in mm")
    project.model3d.StoreParameterWithDescription("h_max", str(HMAX_MM), "Maximum printable height in mm")

    configure_common_units(project)
    create_verowhiteplus_material(project)
    write_history(
        project,
        "Unit Cell Geometry",
        """
With Brick
    .Reset
    .Name "unit_cell"
    .Component "meta"
    .Material "VeroWhitePlus"
    .Xrange "0", "L_cell"
    .Yrange "0", "L_cell"
    .Zrange "0", "h"
    .Create
End With
""".strip(),
    )
    write_history(
        project,
        "Unit Cell Boundaries And Ports",
        f"""
With Boundary
    .Xmin "unit cell"
    .Xmax "unit cell"
    .Ymin "unit cell"
    .Ymax "unit cell"
    .Zmin "expanded open"
    .Zmax "expanded open"
    .Xsymmetry "none"
    .Ysymmetry "none"
    .Zsymmetry "none"
    .XPeriodicShift "0.0"
    .YPeriodicShift "0.0"
    .ZPeriodicShift "0.0"
    .PeriodicUseConstantAngles "False"
    .SetPeriodicBoundaryAngles "0", "0"
    .SetPeriodicBoundaryAnglesDirection "outward"
    .UnitCellFitToBoundingBox "True"
    .UnitCellDs1 "0.0"
    .UnitCellDs2 "0.0"
    .UnitCellAngle "90.0"
End With
With FloquetPort
    .SetDialogFrequency "f0"
    .SetDialogTheta "0"
    .SetDialogPhi "0"
    .SetSortCode "+beta/pw"
    .SetCustomizedListFlag "False"
    .Port "Zmin"
    .SetNumberOfModesConsidered "2"
    .Port "Zmax"
    .SetNumberOfModesConsidered "2"
End With
With Solver
    .FrequencyRange "{FREQ_MIN_GHZ}", "{FREQ_MAX_GHZ}"
End With
""".strip(),
    )


def try_extract_unit_scan(project: object, target_csv: Path) -> bool:
    tree = project.model3d.ResultTree
    candidates = [
        r"1D Results\S-Parameters\SZmax(1),Zmin(1)",
        r"1D Results\S-Parameters\SZmax(2),Zmin(2)",
        r"1D Results\S-Parameters\SZmin(1),Zmax(1)",
        r"1D Results\S-Parameters\SZmin(2),Zmax(2)",
    ]
    rows: list[dict[str, float]] = []
    for item in candidates:
        if not tree.DoesTreeItemExist(item):
            continue
        result_ids = tree.GetResultIDsFromTreeItem(item)
        for run_id in result_ids:
            run_id_str = str(run_id)
            if run_id_str.endswith(":0"):
                continue
            exists, names, values = project.model3d.GetParameterCombination(run_id_str)
            if not exists or names is None or values is None:
                continue
            mapping = {str(k): float(v) for k, v in zip(names, values)}
            if "h" not in mapping:
                continue
            result = tree.GetResultFromTreeItem(item, run_id_str)
            n = int(result.GetN())
            if n < 1:
                continue
            x = np.array(result.GetArray("x"), dtype=np.float64)
            yre = np.array(result.GetArray("yre"), dtype=np.float64)
            yim = np.array(result.GetArray("yim"), dtype=np.float64)
            idx = int(np.argmin(np.abs(x - FREQ_GHZ)))
            s21 = complex(float(yre[idx]), float(yim[idx]))
            rows.append(
                {
                    "height_mm": float(mapping["h"]),
                    "phase_rad": float(np.angle(s21)),
                    "s21_mag": float(abs(s21)),
                }
            )
        if rows:
            break

    if not rows:
        return False

    df = pd.DataFrame(rows).sort_values("height_mm").drop_duplicates(subset=["height_mm"], keep="first")
    ensure_parent(target_csv)
    df.to_csv(target_csv, index=False)
    return True


def run_unit_scan(project: object, step_mm: float) -> dict[str, object]:
    ps = project.model3d.ParameterSweep
    ps.DeleteAllSequences()
    ps.AddSequence("HeightSweep")
    ps.SetSimulationType("Frequency")
    ps.SetOptionSkipExistingCombinations(True)
    ps.AddParameter_Stepwidth("HeightSweep", "h", HMIN_MM, HMAX_MM, step_mm)
    ps.StartActiveSolver(True)
    ps.Start()
    exported = try_extract_unit_scan(project, UNIT_SCAN_CSV)
    return {
        "sweep_range_mm": [HMIN_MM, HMAX_MM],
        "sweep_step_mm": step_mm,
        "csv_exported": exported,
        "csv_path": str(UNIT_SCAN_CSV),
    }


def build_full_array_command(height_map: np.ndarray) -> str:
    lines = [
        "With Boundary",
        '    .Xmin "expanded open"',
        '    .Xmax "expanded open"',
        '    .Ymin "expanded open"',
        '    .Ymax "expanded open"',
        '    .Zmin "expanded open"',
        '    .Zmax "expanded open"',
        "End With",
        "With Solver",
        f'    .FrequencyRange "{FREQ_MIN_GHZ}", "{FREQ_MAX_GHZ}"',
        "End With",
        "With PlaneWave",
        "    .Reset",
        '    .Normal "0", "0", "-1"',
        '    .EVector "1", "0", "0"',
        '    .Polarization "Linear"',
        '    .ReferenceFrequency "0.0"',
        '    .PhaseDifference "-90.0"',
        '    .CircularDirection "Left"',
        '    .AxialRatio "1.0"',
        '    .SetUserDecouplingPlane "False"',
        "    .Store",
        "End With",
        "With Monitor",
        "    .Reset",
        f'    .Name "e-field (f={FREQ_GHZ};z={MONITOR_Z_MM})"',
        '    .Domain "Frequency"',
        '    .FieldType "Efield"',
        f'    .Frequency "{FREQ_GHZ}"',
        '    .PlaneNormal "z"',
        f'    .PlanePosition "{MONITOR_Z_MM}"',
        "    .Create",
        "End With",
    ]

    for row_idx in range(height_map.shape[0]):
        for col_idx in range(height_map.shape[1]):
            z2 = float(height_map[row_idx, col_idx])
            if z2 <= 0.0:
                continue
            x1 = col_idx * CELL_SIZE_MM
            x2 = x1 + CELL_SIZE_MM
            y1 = row_idx * CELL_SIZE_MM
            y2 = y1 + CELL_SIZE_MM
            lines.extend(
                [
                    "With Brick",
                    "    .Reset",
                    f'    .Name "cell_{row_idx + 1}_{col_idx + 1}"',
                    '    .Component "array"',
                    f'    .Material "{MATERIAL_NAME}"',
                    f'    .Xrange "{x1}", "{x2}"',
                    f'    .Yrange "{y1}", "{y2}"',
                    f'    .Zrange "0", "{z2}"',
                    "    .Create",
                    "End With",
                ]
            )
    return "\n".join(lines)


def create_full_array_project(project: object, height_csv: Path, monitor_z_mm: float) -> dict[str, object]:
    if not height_csv.exists():
        raise FileNotFoundError(f"Height CSV not found: {height_csv}")

    height_map = pd.read_csv(height_csv, header=None).to_numpy(dtype=np.float64)
    if height_map.shape != (GRID_SIZE, GRID_SIZE):
        raise ValueError(f"Expected {GRID_SIZE}x{GRID_SIZE} height matrix, got {height_map.shape}")

    project.model3d.SelectQuickStartGuide("Transient")
    project.model3d.ChangeSolverType("HF Time Domain")
    project.model3d.StoreParameterWithDescription("L_cell", str(CELL_SIZE_MM), "Paper LN cell size in mm")
    project.model3d.StoreParameterWithDescription("f0", str(FREQ_GHZ), "Paper center frequency in GHz")
    project.model3d.StoreParameterWithDescription("zc", str(PROPAGATION_DISTANCE_MM), "Paper imaging distance in mm")
    configure_common_units(project)
    create_verowhiteplus_material(project)

    global MONITOR_Z_MM
    MONITOR_Z_MM = monitor_z_mm
    write_history(project, "Full Array Build", build_full_array_command(height_map))
    return {
        "height_csv": str(height_csv),
        "array_shape": list(height_map.shape),
        "height_min_mm": float(height_map.min()),
        "height_max_mm": float(height_map.max()),
        "monitor_z_mm": float(monitor_z_mm),
    }


def export_field_csv(project: object, requested_tree_item: str) -> dict[str, object]:
    candidates = [requested_tree_item] if requested_tree_item else []
    candidates.extend(
        [
            fr"2D/3D Results\E-Field\e-field (f={FREQ_GHZ};z={MONITOR_Z_MM}) [1]",
            fr"2D/3D Results\E-Field\e-field (f={FREQ_GHZ};z={MONITOR_Z_MM})",
            fr"2D/3D Results\E-Field\e-field (f={FREQ_GHZ}) [1]",
        ]
    )
    tree = project.model3d.ResultTree
    selected = ""
    for item in candidates:
        if item and tree.DoesTreeItemExist(item):
            selected = item
            break
    if not selected:
        raise RuntimeError("No matching field monitor tree item found for export.")

    ensure_parent(FIELD_PLANE_CSV)
    vba = f"""
SelectTreeItem "{selected}"
With ASCIIExport
    .Reset
    .FileName "{FIELD_PLANE_CSV}"
    .Mode "FixedNumber"
    .StepX 301
    .StepY 301
    .SetFileType "csv"
    .SetCsvSeparator ","
    .Execute
End With
""".strip()
    project.model3d._execute_vba_code(vba)
    return {"field_tree_item": selected, "field_csv": str(FIELD_PLANE_CSV)}


def mode_boot_test(unit_project_path: Path) -> None:
    de, project = new_project()
    try:
        configure_common_units(project)
        create_verowhiteplus_material(project)
        saved_path = save_project(project, unit_project_path)
        append_status(
            "boot-test",
            {
                "cst_exe_exists": CST_EXE.exists(),
                "project_save_probe": str(saved_path),
                "status": "ok",
            },
        )
        print("CST boot-test passed.")
        print(f"CST executable: {CST_EXE}")
        print(f"Probe project saved to: {saved_path}")
    finally:
        project.close()
        de.close()


def mode_unit_scan(unit_project_path: Path, step_mm: float, run_solver: bool) -> None:
    de, project = new_project()
    try:
        create_unit_cell_project(project)
        saved_path = save_project(project, unit_project_path)
        status: dict[str, object] = {
            "project": str(saved_path),
            "height_range_mm": [HMIN_MM, HMAX_MM],
            "paper_frequency_ghz": FREQ_GHZ,
            "solver_band_ghz": [FREQ_MIN_GHZ, FREQ_MAX_GHZ],
            "sweep_step_mm": step_mm,
            "solver_started": bool(run_solver),
            "csv_exported": False,
        }
        if run_solver:
            status.update(run_unit_scan(project, step_mm))
        append_status("unit-scan", status)
        print(f"Unit-cell project saved to: {saved_path}")
        if run_solver:
            print(f"Unit-cell scan CSV: {UNIT_SCAN_CSV}")
        else:
            print("Project created. Re-run with --run-solver to start the CST sweep.")
    finally:
        project.close()
        de.close()


def mode_full_array(
    array_project_path: Path,
    height_csv: Path,
    monitor_z_mm: float,
    run_solver: bool,
    export_results: bool,
    field_tree_item: str,
) -> None:
    de, project = new_project()
    try:
        status = create_full_array_project(project, height_csv, monitor_z_mm)
        saved_path = save_project(project, array_project_path)
        status.update({"project": str(saved_path), "solver_started": bool(run_solver), "field_exported": False})
        if run_solver:
            project.model3d.run_solver()
            if export_results:
                status.update(export_field_csv(project, field_tree_item))
                status["field_exported"] = True
        append_status("full-array-export", status)
        print(f"Full-array project saved to: {saved_path}")
        if run_solver and export_results:
            print(f"Field plane CSV: {FIELD_PLANE_CSV}")
        elif run_solver:
            print("Solver run completed. Re-run with --export-results to export the monitor.")
        else:
            print("Project created. Re-run with --run-solver to start the CST simulation.")
    finally:
        project.close()
        de.close()


def main() -> None:
    args = parse_args()
    if args.mode == "boot-test":
        mode_boot_test(Path(args.unit_project))
    elif args.mode == "unit-scan":
        mode_unit_scan(Path(args.unit_project), step_mm=args.height_step_mm, run_solver=args.run_solver)
    else:
        mode_full_array(
            array_project_path=Path(args.array_project),
            height_csv=Path(args.height_csv),
            monitor_z_mm=args.monitor_z_mm,
            run_solver=args.run_solver,
            export_results=args.export_results,
            field_tree_item=args.field_tree_item,
        )


if __name__ == "__main__":
    main()
