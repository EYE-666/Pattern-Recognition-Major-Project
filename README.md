# 模式识别大作业

已按原始要求完成 USPS 和 UCI Sonar 数据集上的 Fisher、KNN 与 Fisher+KNN 实验。

项目仓库：[EYE-666/Pattern-Recognition-Major-Project](https://github.com/EYE-666/Pattern-Recognition-Major-Project)。

## 先看哪些文件

- [Word 实验报告](report/模式识别大作业报告.docx)：17 页中文报告，9 张实验图，包含要求的七部分和实际核心代码。
- [在线阅读报告](report/模式识别大作业报告.md)：便于搜索和修改的正文副本。
- `report/作业要求.docx`：原始要求的只读来源副本。
- [阅读与答辩指南](阅读与答辩指南.md)：读懂实验和回答常见问题的简明说明。
- [核心算法](src/models.py)：从定义实现 Fisher 与精确 KNN。
- [完整实验流程](src/experiment.py)。
- `results/`：真实运行指标、划分索引、预测结果、日志和数据检查记录。
- `figures/`：报告使用的九张原始高清图。
- `data/`：三个已下载并校验的数据文件，正常复现不必重新下载。

报告首页的姓名、学号、班级未填写；请在阅读并核对课程格式要求后补充。正文没有编造个人经历、教师信息或实验成绩。

## 已完成的真实结果

| 方法 | USPS 原始测试集正确率 | Sonar 20 次重新调参的正确率均值 ± 标准差 |
| --- | --- | --- |
| KNN | 94.37% | 83.45% ± 5.32 个百分点 |
| Fisher 最近类中心 | 88.59% | 78.93% ± 5.48 个百分点 |
| Fisher+KNN | 90.43% | 78.45% ± 4.97 个百分点 |

USPS 使用 7291/2007 原始划分。Sonar 每次分层划分为 166/42，每次均在训练集内做五折调参。曲线实验固定参数，和主实验口径不同；报告有详细说明。

Fisher 降维没有在本次数据上提高平均正确率，这是真实实验结论。不要把曲线中最高测试点改写为“验证选出的最好成绩”。

## 获取项目与安装依赖

本次实验使用 Python 3.13.5。无须 PyTorch 或 GPU。建议在独立虚拟环境中安装依赖：

```powershell
git clone https://github.com/EYE-666/Pattern-Recognition-Major-Project.git
cd Pattern-Recognition-Major-Project
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

以下命令中的 `python` 应指向装好依赖的解释器，例如 `.\.venv\Scripts\python.exe`。制图采用 Microsoft YaHei；非 Windows 环境需换成可用的中文字体。

## 运行实验

Windows 提供快捷脚本，优先使用已有的 `E:\anaconda\python.exe`，否则使用 PATH 中的 Python：

```powershell
.\run_experiments.ps1
```

若本机执行策略不允许运行脚本，可以逐条执行 Python 命令，无需修改系统执行策略：

```powershell
python src/download_data.py
python src/verify_models.py
python src/experiment.py
python src/make_figures.py
python src/audit_results.py
```

实验本次用时约 57 秒；电脑负载和依赖版本变化会影响时间。结果写入 results，图写入 figures。默认重复次数为 USPS 学习曲线 5 次、Sonar 20 次。`audit_results.py` 和报告默认针对这一完整协议。

## 重新生成报告

```powershell
python src/build_report.py
```

这需要 python-docx，已列入 requirements.txt。仓库已提供生成好的报告，不必重新生成即可阅读。

报告中的表格从结果文件读取，分析段落按本次默认实验编写。如果改变算法、随机种子、重复次数或数据集，须同步修改分析文字。不要只重跑实验而沿用旧报告结论。

文档使用本机 Microsoft Word 后台导出并逐页检查；`qa/` 仅为本地排版检查过程，不纳入提交包。若自行修改 Word 文档，提交前检查分页、公式及姓名等信息。

需要生成包含数据、代码、报告和结果的完整作业压缩包时，运行 `python src/package_assignment.py`。根目录压缩包由脚本生成，不纳入 Git 版本控制；原始数据压缩文件仍保留在 data 中。SHA256SUMS.txt 记录文件校验值。

## 复现与正确性检查

- `verify_models.py`：与 sklearn KNN 预测对照；Fisher 与等先验正则化 LDA 公式对照；检查归一化、奇异矩阵、同票规则和训练集标准化。
- `audit_results.py`：检查训练/测试索引互斥、嵌套训练子集、预测与指标一致性、指标范围及重复行。
- `settings.json`：记录版本、随机种子及数据 SHA256。
- `split_indices.npz`：保存外层划分与 USPS 子集索引；Sonar 子集可由外层训练索引和相同种子的 `nested_subset` 确定性重建。
- Sonar 重复留出之间样本重叠，标准差不是置信区间；报告不宣称显著性。

## 数据与方法出处

1. [教材配套 USPS 数据页](https://hastie.su.domains/ElemStatLearn/data.html)；[ZIP 数据说明](https://hastie.su.domains/ElemStatLearn/datasets/zip.info.txt)。
2. [UCI Sonar](https://archive.ics.uci.edu/dataset/151/connectionist+bench+sonar+mines+vs+rocks)，Sejnowski 与 Gorman，1988，DOI 10.24432/C5T01Q，CC BY 4.0。
3. [scikit-learn 判别分析说明](https://scikit-learn.org/stable/modules/lda_qda.html)。
4. [scikit-learn 近邻方法说明](https://scikit-learn.org/stable/modules/neighbors.html)。
