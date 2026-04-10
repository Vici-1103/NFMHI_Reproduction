# Project Spec

## 1. 论文固定参数
- 成像目标：`GHZ`
- 网络尺寸：`60 x 60`
- 层数：`1`
- 学习率：`0.05`
- 训练轮数：`1000`
- 单元尺寸：`L_N = 5 mm`
- 中心波长：`lambda_c = 10 mm`
- 中心频率：`f_c = 30 GHz`
- 传播距离：`Z_c = 100 mm`
- 单元高度范围：`h = 2 mm ~ 8 mm`
- 材料：`VeroWhitePlus`
- 材料参数：`eps_r = 2.802`，`mu_r = 1`，`tanδ = 0.0557`

以上参数来自论文页图中的 Table 1、Figure 4、Figure 6、Figure 8 及正文说明。

## 2. 与论文配套的实现约束
- 目标图只能使用论文中的 `GHZ`，不得替换成单个字母或其他图案。
- 训练损失图必须来自真实训练记录，不允许通过平滑、归一化或手工改值伪装成论文曲线。
- `phase_height_curve.csv` 必须来自真实 CST 单元扫描，不允许占位文件冒充。
- `field_plane_30GHz_100mm.csv` 必须来自真实 CST 整阵列导出，不允许占位文件冒充。

## 3. 已知的论文信息
- Python 侧成像平面以 `x-y` 展示，Figure 4 中坐标范围为 `0 ~ 300 mm`。
- CST 侧图像展示了目标平面附近 `z = 96 ~ 110 mm` 的成像结果。
- 论文给出了 `h_min = 2 mm` 作为统一基座高度，因此如果以阵列底面为 `z = 0`，则目标成像面可按 `z = 102 mm` 作为默认监视面。

## 4. 明确标记的实现假设
- 论文页图未明确给出单元高度扫描步长，因此仓库中的 CST 自动化脚本把步长做成可配置参数，不把默认值声称为论文原文值。
- 论文图片中的 CST 坐标展示与 Python 算法图存在坐标命名差异；仓库默认采用与 Figure 4 / Figure 8 一致的 `z` 向传播表示，并在报告中记录这一点。

## 5. 关键产物
- `python/data/targets/target_GHZ_60x60.npy`
- `python/outputs/phase_maps/phase_matrix.npy`
- `python/outputs/height_maps/height_matrix.csv`
- `cst/results/unit_scan/phase_height_curve.csv`
- `cst/results/array_sim/field_plane_30GHz_100mm.csv`
- `docs/reports/final_reproduction_report.md`
