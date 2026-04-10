# CST Workspace Notes

## 目录
- `unit_cell/`: 单元扫描工程
- `full_array/`: 整阵列工程
- `macros/`: CST VBA 模板
- `results/`: 真实导出结果
- `templates/`: 论文对齐的检查项

## 自动化入口
统一使用：

```powershell
& $env:NFMHI_PYTHON python/scripts/cst_pipeline.py boot-test
& $env:NFMHI_PYTHON python/scripts/cst_pipeline.py unit-scan
& $env:NFMHI_PYTHON python/scripts/cst_pipeline.py full-array-export
```

## 结果要求
- `cst/results/unit_scan/phase_height_curve.csv` 必须来自真实单元扫描。
- `cst/results/array_sim/field_plane_30GHz_100mm.csv` 必须来自真实整阵列监视器导出。
- 若结果尚未真实生成，宁可缺失，也不能保留占位文件冒充最终结果。
