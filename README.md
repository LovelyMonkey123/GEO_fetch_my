# geo-ncbi-fetch

[![version](https://img.shields.io/badge/version-1.2.0-blue)](https://github.com/LovelyMonkey123/GEO_fetch_my)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

从 NCBI GEO 数据库批量提取数据集元数据，翻译为学术中文，输出结构化 Excel。适配 scRNA-seq / 生信数据集整理 / GEO 数据库注释工作流。

## 快速开始

```bash
# 1. 安装依赖（推荐 conda + 清华镜像）
pip install biopython openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 提取元数据
python scripts/fetch_geo.py \
  --input "GSE184362,GSE33630,GSE76039" \
  --output meta.json \
  --email your@email.edu

# 3. 翻译 + 生成 Excel
python scripts/build_excel.py \
  --meta meta.json \
  --trans trans.json \
  --output result.xlsx
```

## 核心特性

- **双输出策略** — 提供原始 GSE 编号 → 新建 Excel；提供已有表格 → 追加列到原表
- **批量提取 + 断点续跑** — >5 个编号自动分批，中断后 `--start-batch N` 恢复
- **学术中文翻译** — 配合 `academic-translate` skill，医学术语/缩写保留原文
- **样本类型提取** — 从摘要中自动识别肿瘤组织/正常组织/转移灶等类型
- **速率控制** — 遵守 NCBI 官方限制（≤3 req/s），不触发 HTTP 429
- **环境自检** — 自动检测 conda 环境 + Biopython 安装，缺失时引导安装

## 目录结构

```
geo-ncbi-fetch/
├── SKILL.md                        # Skill 路由协议（含双策略分支）
├── manifest.yaml                   # 声明式配置
├── scripts/
│   ├── fetch_geo.py                # 核心提取脚本（NCBI E-utilities）
│   └── build_excel.py              # Excel 输出脚本（新建/追加）
├── static/core/
│   ├── tools.md                    # NCBI E-utilities API 参考手册
│   └── workflow.md                 # 完整工作流（环境→提取→翻译→Excel）
└── references/
    └── ncbi-guidelines.md          # NCBI 使用政策参考
```

## 提取字段

| 字段 | 说明 |
|------|------|
| `accession` | GEO 编号 |
| `title_en` | 英文标题 |
| `summary_en` | 实验设计描述 |
| `gdsType` | 实验类型（测序/芯片等） |
| `n_samples` | NCBI 记录样本数 |
| `taxon` | 物种 |
| `PDAT` | 发布日期 |
| `supplFiles` | 补充文件类型列表 |
| `pmids` | 关联 PubMed ID 列表 |
| `sample_types` | 样本类型（从摘要提取，中文） |
| `geo_url` | GEO 数据库页面链接 |

## Excel 输出列

```
Accession | GEO标题(中) | 实验类型(中) | GEO摘要(中) | 样本类型 | 样本数 | PubMed IDs | 发布日期 | 数据下载
```

"数据下载" 列为 HYPERLINK，指向 NCBI GEO 数据库页面。

## 命令行用法

### fetch_geo.py

```bash
# 直接模式（≤5 个编号）
python scripts/fetch_geo.py \
  --input "GSE184362,GSE33630" \
  --output meta.json \
  --email your@email.edu

# 批量模式（自动拆分批次）
python scripts/fetch_geo.py \
  --input accs.txt \
  --output meta.json \
  --email your@email.edu \
  --batch-size 5

# 断点续跑（从第 3 批恢复）
python scripts/fetch_geo.py \
  --input accs.txt \
  --output meta.json \
  --batch-size 5 \
  --start-batch 3
```

### build_excel.py

```bash
# 新建 Excel
python scripts/build_excel.py \
  --meta meta.json \
  --trans trans.json \
  --output result.xlsx

# 追加到已有表格
python scripts/build_excel.py \
  --meta meta.json \
  --trans trans.json \
  --append existing.xlsx
# → 输出 existing_annotated.xlsx（不覆盖原文件）
```

## 工作流

```
  原始数据列表 / 已有Excel
       │
       ▼
  ┌──────────────────────┐
  │  geo-ncbi-fetch       │
  │  ① 解析编号 / Excel   │
  │  ② 提取 NCBI 元数据   │
  │  ③ academic-translate │
  │  ④ build_excel.py     │
  │     ├─ 新建模式        │
  │     └─ 追加模式        │
  │  输出: .xlsx           │
  └──────────────────────┘
```

## 速率参考

| 编号数量 | 模式 | 预计耗时 |
|---------|------|---------|
| 1–5 | 直接 | ~2s |
| 10 | 批处理 (5×2) | ~4s |
| 50 | 批处理 (5×10) | ~20s |
| 100 | 批处理 (5×20) | ~40s |

> 注册免费 [NCBI API Key](https://www.ncbi.nlm.nih.gov/account/) 可提升至 10 req/s。

## 局限性

- 仅返回 NCBI Entrez 中索引的元数据，原始表达矩阵需手动下载
- 仅提供 GEO 数据库页面 URL，不提供 FTP 下载链接
- 仅支持 GEO（GSE/GSM/GPL），不支持 GSA/ENA/CNGB/Zenodo
- NCBI 偶尔索引延迟，新提交数据集可能 1–2 天后才能查到
- 速率限制为 per-IP，不支持多进程并行

## 依赖

- Python ≥ 3.8
- [Biopython](https://biopython.org/) — NCBI E-utilities 接口
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel 读写

## 版本历史

| 版本 | 日期 | 更新 |
|------|------|------|
| v1.2.0 | 2025-06 | 修复 `clean()` 正则、pmids 切到 `PubMedIds` 字段、新增 `sample_types`、内置 `build_excel.py`、双输出策略 |
| v1.1.0 | 2025-06 | conda 环境选择、批次断点续跑 |
| v1.0.0 | 2025-06 | 初始版本：基础提取 + JSON 输出 |

## 作者

- GitHub: [@LovelyMonkey123](https://github.com/LovelyMonkey123)
- Skill 架构参考: nature-skill family
