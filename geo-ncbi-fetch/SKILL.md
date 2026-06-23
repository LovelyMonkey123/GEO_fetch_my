---
name: geo-ncbi-fetch
description: >-
  Batch fetch GEO dataset metadata from NCBI E-utilities, translate to academic
  Chinese, and output as structured Excel. Two modes: (1) raw GSE numbers → build
  new Excel from scratch; (2) existing dataset spreadsheet → append metadata
  columns. Extracts title, summary, sample count, sample types, taxonomy,
  publication date, supplementary files, and PubMed IDs. Supports batched
  checkpoint/resume for large lists (>5 entries). Pairs with academic-translate
  skill for translation.
  Trigger phrases: GEO元数据、NCBI查询、GSE信息提取、GEO数据注释、
  批量查询GEO、补充数据集信息、fetch GEO metadata、查一下这几个GSE、
  把这些GSE的信息拉下来.
version: 1.2.0
author: Community contribution, structured as static/dynamic skill
---

# GEO NCBI Metadata Fetch — Router

This skill is split into two layers:

- A **static layer** under `static/` that holds the E-utilities tool reference and the
  extraction workflow (including conda environment setup and batch execution).
- A **dynamic layer** (this file plus `manifest.yaml`) that routes the user's request
  through environment setup, extraction, and optional translation.

Do not apply extraction logic from memory. Always load fragments from disk.

## Routing Protocol

Follow these steps every time the skill is invoked.

### 0. Environment Setup (MANDATORY for first-time users)

**Always perform this step before any API call.** Do not assume the environment is ready.

1. **List available conda environments:**
   ```bash
   conda info --envs
   ```

2. **Ask the user which environment to use.** Present numbered options. For example:
   > "以下 conda 环境可用，请选择运行环境："
   > 1. py311
   > 2. jupyter
   > 3. CellRank
   > ...

3. **Record the Python path:**
   ```
   /path/to/conda/envs/<selected>/python
   ```

4. **Check Biopython:**
   ```bash
   <python_path> -c "from Bio import Entrez; print('OK')"
   ```
   If missing:
   ```bash
   <python_path> -m pip install biopython -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

5. **Confirm ready** before proceeding to extraction.

### 1. Load the manifest and core layer

Read [manifest.yaml](manifest.yaml). Then read every file under `always_load`:

- `static/core/tools.md` — NCBI E-utilities: database parameters, API calls,
  extracted fields, rate limits, batch mode, error handling.
- `static/core/workflow.md` — full extraction workflow: conda setup, input parsing,
  script execution, batch resume, output structure, downstream integration.

### 2. Detect the accession source and output strategy

Map the user's input to one or more accessions, AND determine the output strategy:

**Input sources:**

- **Direct list** — user provides comma/space/newline separated GSE/GSM/GPL
- **Excel file** — parse `Accession` column filtered by `数据来源 == "GEO"`
- **Note content** — extract all `(GSE|GSM|GPL)\d+` tokens with regex
- **JSON file** — read an existing JSON keyed by accession

**Output strategy (MANDATORY branching):**

| Input type | Strategy | Behavior |
|-----------|----------|----------|
| Raw GSE numbers (direct list / note / JSON) | **新建Excel** | Fetch → translate → build new `.xlsx` from scratch |
| Existing dataset spreadsheet (`.xlsx` / `.xls`) | **追加策略** | Parse accessions from sheet → fetch → translate → append new columns to original file |

State the detected source, accession count, and chosen strategy before proceeding.

### 3. Run the extraction workflow

Apply the loaded material in order:

1. **Parse accessions** — extract and deduplicate from the input source
2. **Choose mode:**
   - **≤5 accessions** → direct execution
   - **>5 accessions** → `--batch-size 5` (checkpoint per batch, resumable)
3. **Execute** — run `scripts/fetch_geo.py` with the selected Python and mode
4. **Review** — check `ok` / `not_found` / `error` counts; inspect errors

### 4. Hand off to academic-translate (optional but recommended)

After extraction, the JSON contains English `title_en`, `summary_en`, and `gdsType` fields.
For Chinese-language dataset curation, invoke the `academic-translate` skill to translate
these fields into academic Chinese.

### 5. Build or update Excel (built-in)

After extraction and translation, produce the final Excel output following the chosen strategy:

**新建 Excel（from raw GSE numbers）：**
1. Read `meta.json` + `trans.json`
2. Run `scripts/build_excel.py --meta meta.json --trans trans.json --output <name>.xlsx`
3. Output columns: Accession | GEO标题(中) | 实验类型(中) | GEO摘要(中) | 样本类型 | 样本数 | PubMed IDs | 发布日期 | 数据下载(HYPERLINK)

**追加策略（from existing spreadsheet）：**
1. Read the existing Excel with openpyxl
2. Add new columns (GEO标题(中), 实验类型(中), GEO摘要(中), 样本类型, NCBI样本数, PubMed IDs, 发布日期, 数据下载) after existing columns
3. Match rows by Accession column
4. Add HYPERLINK formulas for the 数据下载 column
5. Save as `<original_name>_annotated.xlsx` (never overwrite original)

## Output Specification

```json
{
  "GSE{xxxxx}": {
    "status":     "ok" | "not_found" | "error",
    "accession":  "GSE{xxxxx}",
    "title_en":   "English dataset title from NCBI",
    "summary_en": "Experimental design description",
    "gdsType":    "Expression profiling by high throughput sequencing",
    "n_samples":  "23",
    "taxon":      "Homo sapiens",
    "PDAT":       "2021/09/19",
    "supplFiles": ["MTX", "TSV"],
    "pmids":      ["34663816"],
    "geo_url":    "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE{xxxxx}"
  }
}
```

The `geo_url` is the **only** URL provided — it points to the GEO database page.
FTP download links are out of scope.

## Why This Split

- The static layer (tools + workflow) is versioned and independently reviewable
- The extraction script is a standalone CLI tool with batch/resume support
- Step 0 (conda environment) prevents the most common first-run failure
- Batch mode with checkpoints prevents data loss on long runs
- Translation is a separate concern, delegated to `academic-translate`
- This structure mirrors the nature-* skill family
