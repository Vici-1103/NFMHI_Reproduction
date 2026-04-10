## 已完成内容

### 1. 论文基线梳理
- 已将论文中的核心复现参数整理到项目文档，包括：`GHZ` 目标、`60×60` 网络、`1` 层、`30 GHz`、`100 mm`、`L_N=5 mm`、`1000 epoch`、材料参数等。
- 位置：
  - [docs/project_spec.md](docs/project_spec.md)
  - [README.md](README.md)

### 2. Python 侧复现链路
- 已完成目标图生成、前向传播检查、DNN 训练、相位到高度映射、指标计算脚本整理。
- 当前目标图已按论文使用 `GHZ`。
- 主要脚本位置：
  - [python/scripts/generate_target.py](python/scripts/generate_target.py)
  - [python/scripts/run_forward_only.py](python/scripts/run_forward_only.py)
  - [python/scripts/train_dnn.py](python/scripts/train_dnn.py)
  - [python/scripts/phase_to_height.py](python/scripts/phase_to_height.py)
  - [python/scripts/compute_metrics.py](python/scripts/compute_metrics.py)

### 3. 已生成的 Python 结果
- 目标图：
  - [python/data/targets/target_GHZ_60x60.npy](python/data/targets/target_GHZ_60x60.npy)
  - [python/data/targets/target_GHZ_60x60.png](python/data/targets/target_GHZ_60x60.png)
- 训练得到的相位矩阵：
  - [python/outputs/phase_maps/phase_matrix.npy](python/outputs/phase_maps/phase_matrix.npy)
- 基于真实单元扫描映射得到的高度矩阵：
  - [python/outputs/height_maps/height_matrix.csv](python/outputs/height_maps/height_matrix.csv)
- 训练图与训练指标：
  - [python/outputs/figures/dnn_train_result.png](python/outputs/figures/dnn_train_result.png)
  - [python/outputs/metrics/dnn_train_metrics.json](python/outputs/metrics/dnn_train_metrics.json)

### 4. CST 单元扫描
- 已完成真实单元扫描，并导出了相位-高度曲线。
- 结果位置：
  - [cst/results/unit_scan/phase_height_curve.csv](cst/results/unit_scan/phase_height_curve.csv)
- 单元工程位置：
  - [cst/unit_cell/nfmhi_unit_cell_30ghz](cst/unit_cell/nfmhi_unit_cell_30ghz)

### 5. CST 整阵列工程
- 已基于高度矩阵自动生成整阵列 CST 工程，准备进行长时仿真与场导出。
- 工程位置：
  - [cst/full_array/nfmhi_full_array_60x60.cst](cst/full_array/nfmhi_full_array_60x60.cst)
- 自动化入口脚本：
  - [python/scripts/cst_pipeline.py](python/scripts/cst_pipeline.py)

### 6. 当前复现状态
- 已完成：
  - 论文参数对齐
  - Python 主链路
  - 真实单元扫描
  - 相位到高度映射
  - 整阵列 CST 工程生成
- 正在进行：
  - 整阵列 CST 长时仿真
- 待最终完成：
  - 成像面场分布导出
  - 最终指标计算

## 过程记录
- 最终报告模板：
  - [docs/reports/final_reproduction_report.md](docs/reports/final_reproduction_report.md)

## GitHub 上传策略
- GitHub 只保留可复现所需的脚本、文档、关键输入和小体积结果。
- `cst/full_array/nfmhi_full_array_60x60.cst` 是整阵列工程的主文件，保留上传。
- `cst/full_array/nfmhi_full_array_60x60/` 是 CST 解包后的工作目录，里面的 `Result/`、`ModelCache/`、`Temp/`、`SP/` 等都属于求解缓存或长时仿真产物，不上传到 GitHub。
- 单元扫描保留 `cst/results/unit_scan/phase_height_curve.csv` 这类关键导出结果，不保留大型中间缓存。
- 如果后续需要共享完整场数据或超大仿真结果，建议放到 GitHub Releases、网盘或数据平台，而不是直接放进 Git 历史。
