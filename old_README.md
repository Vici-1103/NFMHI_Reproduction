# NFMHI 论文复现仓库

本仓库用于复现论文 **Near-Field Microwave Holographic Imaging Using a Metamaterial-Based Diffraction Neural Network With Angular Spectrum-Assisted Computation**。

## 当前固定基线
- 目标图案：`GHZ`
- 网络尺寸：`60 x 60`
- 层数：`1`
- 学习率：`0.05`
- 训练轮数：`1000`
- 单元尺寸：`L_N = 5 mm`
- 中心频率：`30 GHz`
- 中心波长：`10 mm`
- 传播距离：`Z_c = 100 mm`
- 介质材料：`VeroWhitePlus`
- 材料参数：`eps_r = 2.802`，`mu_r = 1`，`tanδ = 0.0557`
- 单元高度范围：`2 mm ~ 8 mm`

以上内容均按论文页图整理；若论文未明确给出实现细节，仓库会在文档里显式标注为“实现假设”，不再使用占位结果冒充论文结果。

## 运行环境
- CST Studio Suite 2026
- Python 3.8.20
- TensorFlow 2.9.0
- 推荐解释器：`V:\Apps\conda_envs\cst2020_env\python.exe`

PowerShell 中建议先固定解释器：

```powershell
$env:NFMHI_PYTHON = "V:\Apps\conda_envs\cst2020_env\python.exe"
& $env:NFMHI_PYTHON --version
& $env:NFMHI_PYTHON -c "import tensorflow as tf; print(tf.__version__)"
& $env:NFMHI_PYTHON -c "import cst.interface; print('cst.interface ok')"
```

## Python 主链路
```powershell
& $env:NFMHI_PYTHON python/scripts/generate_target.py --pattern GHZ --size 60
& $env:NFMHI_PYTHON python/scripts/run_forward_only.py --target python/data/targets/target_GHZ_60x60.npy
& $env:NFMHI_PYTHON python/scripts/train_dnn.py --target python/data/targets/target_GHZ_60x60.npy --epochs 1000 --lr 0.05
& $env:NFMHI_PYTHON python/scripts/phase_to_height.py --phase python/outputs/phase_maps/phase_matrix.npy --method interp --scan-csv cst/results/unit_scan/phase_height_curve.csv --out-prefix height_matrix
& $env:NFMHI_PYTHON python/scripts/compute_metrics.py --target python/data/targets/target_GHZ_60x60.npy --python-output python/outputs/figures/dnn_train_intensity.npy --cst-output cst/results/array_sim/field_plane_30GHz_100mm.csv --out-prefix final_compare
```

## CST 自动化入口
仓库现在只保留一个 CST 自动化入口：

```powershell
& $env:NFMHI_PYTHON python/scripts/cst_pipeline.py boot-test
& $env:NFMHI_PYTHON python/scripts/cst_pipeline.py unit-scan
& $env:NFMHI_PYTHON python/scripts/cst_pipeline.py full-array-export
```

说明：
- `boot-test`：验证 `cst.interface` 和 CST 2026 可调用。
- `unit-scan`：创建或更新真实单元扫描工程，并可选择运行参数扫描与导出 `phase_height_curve.csv`。
- `full-array-export`：创建或更新真实整阵列工程，并可选择运行求解与导出 `field_plane_30GHz_100mm.csv`。

## 目录说明
- `paper/`：论文 PDF 与转出的页图
- `python/`：目标图生成、训练、映射、指标计算
- `cst/`：CST 工程、宏模板、导出结果
- `docs/`：论文参数基线、复现报告
- `env/`：环境说明

## 重要原则
- 不再保留伪造的 CST 占位结果。
- 不为了“长得像论文”而改写真实训练 loss。
- 任何与论文不一致、但论文又未明确说明的实现细节，都必须在文档中注明为假设。
