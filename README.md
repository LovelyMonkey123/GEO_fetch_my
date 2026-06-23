# geo-ncbi-fetch

[![version](https://img.shields.io/badge/version-1.2.0-blue)](https://github.com/LovelyMonkey123/GEO_fetch_my)

Claude Code skill — 从 NCBI GEO 批量提取数据集元数据，翻译为学术中文，输出 Excel。

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/LovelyMonkey123/GEO_fetch_my.git
```

### 2. 安装为 Claude Code Skill

将 `geo-ncbi-fetch/` 目录复制到 Claude Code 的 skills 目录：

```bash
# Windows
xcopy geo-ncbi-fetch %USERPROFILE%\.claude\skills\geo-ncbi-fetch\ /E /I

# macOS / Linux
cp -r geo-ncbi-fetch ~/.claude/skills/geo-ncbi-fetch/
```

### 3. 安装 Python 依赖

需要 conda 环境 + Biopython：

```bash
# 二选一：已有 conda 环境
conda activate <your_env>
pip install biopython openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或新建环境
conda create -n geo python=3.11 -y
conda activate geo
pip install biopython openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> 如果在 Claude Code 中通过 Skill 调用，Step 0 会自动检测 conda 环境，缺失时引导安装。

## 使用

### 方式 A：Claude Code 对话调用（推荐）

安装后直接对 Claude 说：

```
用 geo-ncbi-fetch 查一下这几个 GSE：GSE184362, GSE33630, GSE76039
```

```
把甲状腺数据集.xlsx 里的 GSE 元数据都拉下来
```

Skill 会自动：
1. 选择 conda 环境 → 2. 提取 NCBI 元数据 → 3. 翻译为学术中文 → 4. 输出 Excel

**输出策略（自动选择）：**
- 给 GSE 编号 → 新建 Excel
- 给已有 `.xlsx` → 追加到原表，输出 `<原名>_annotated.xlsx`

### 方式 B：命令行独立调用

```bash
# Step 1: 提取元数据
python scripts/fetch_geo.py \
  --input "GSE184362,GSE33630,GSE76039" \
  --output meta.json \
  --email your@email.edu

# Step 2: 翻译（通过 academic-translate skill 或手动翻译）
# → 生成 trans.json

# Step 3: 生成 Excel
python scripts/build_excel.py \
  --meta meta.json \
  --trans trans.json \
  --output result.xlsx
```

**批量模式（>5 个编号）：**

```bash
python scripts/fetch_geo.py \
  --input accs.txt \
  --output meta.json \
  --batch-size 5

# 中断后可从指定批次恢复
python scripts/fetch_geo.py \
  --input accs.txt \
  --output meta.json \
  --batch-size 5 \
  --start-batch 3
```

**追加到已有表格：**

```bash
python scripts/build_excel.py \
  --meta meta.json \
  --trans trans.json \
  --append existing.xlsx
# → existing_annotated.xlsx（不覆盖原文件）
```

## 输出

### JSON（fetch_geo.py）

```json
{
  "GSE184362": {
    "accession": "GSE184362",
    "title_en": "Single-cell sequencing of tumor ecosystems in PTC",
    "summary_en": "The tumor ecosystem of papillary thyroid carcinoma...",
    "gdsType": "Expression profiling by high throughput sequencing",
    "n_samples": "23",
    "taxon": "Homo sapiens",
    "PDAT": "2021/09/19",
    "supplFiles": ["MTX, TSV"],
    "pmids": ["34663816", "36523593"],
    "sample_types": ["肿瘤组织", "癌旁组织", "转移灶"],
    "geo_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE184362"
  }
}
```

### Excel（build_excel.py）

| Accession | GEO标题(中) | 实验类型(中) | GEO摘要(中) | 样本类型 | 样本数 | PubMed IDs | 发布日期 | 数据下载 |
|-----------|-------------|-------------|-------------|---------|-------|-----------|---------|---------|
| GSE184362 | 甲状腺乳头状癌... | 高通量测序... | ... | 肿瘤组织、癌旁组织 | 23 | 34663816 | 2021/09/19 | GEO页面 🔗 |

## 依赖

- Python ≥ 3.8
- [Biopython](https://biopython.org/) — NCBI E-utilities
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel 读写

## 版本

| 版本 | 更新 |
|------|------|
| v1.2.0 | 修复 n_samples/pmids、新增 sample_types、内置 build_excel.py、双输出策略 |
| v1.1.0 | conda 环境自检、批次断点续跑 |
| v1.0.0 | 基础提取 + JSON 输出 |

## 作者

[@LovelyMonkey123](https://github.com/LovelyMonkey123)
