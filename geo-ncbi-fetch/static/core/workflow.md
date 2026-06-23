# GEO Metadata Extraction — Workflow

## Overview

Extract structured metadata from NCBI GEO for a list of accession numbers (GSE/GSM/GPL).
Outputs JSON ready for downstream tools — including the `academic-translate` skill for
Chinese translation.

## Input Format

Accept accessions from any of:
- Direct user input (space/comma/newline separated list)
- Excel file — filter by `数据来源 == "GEO"` column
- IMA note content containing GEO accession patterns
- JSON file (dict keyed by accession or array of strings)

Extract all tokens matching the regex: `(GSE|GSM|GPL)\d+`

## Execution Steps

### Step 0: Select Conda Environment

**ALWAYS perform this step before any other action.** The user may be new and not know
which environment has Biopython installed.

1. List available conda environments:
   ```bash
   conda info --envs
   ```

2. Ask the user which environment to use. Present options as a numbered list.

3. Record the Python path:
   ```bash
   /path/to/conda/envs/<env_name>/python
   ```

4. Check Biopython availability:
   ```bash
   <python_path> -c "from Bio import Entrez; print('OK')"
   ```

5. If Biopython is missing, install it:
   ```bash
   <python_path> -m pip install biopython -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### Step 1: Parse Accessions

Extract and deduplicate all GEO accessions from the user's input. Report the count to
the user before proceeding.

### Step 2: Configure NCBI Credentials

- `--email` is **mandatory** — use the user's institutional email or a default
- NCBI API key is optional; if the user has one, pass `--api-key` for 10 req/s
  (without key: 3 req/s)

### Step 3: Execute Extraction

The script supports two modes:

**Direct mode** (≤5 accessions):
```bash
<python_path> scripts/fetch_geo.py \
  --input <accessions> \
  --output <output.json> \
  --email user@institution.edu
```

**Batch mode** (>5 accessions, automatically applied):
```bash
<python_path> scripts/fetch_geo.py \
  --input <accessions> \
  --output <output.json> \
  --email user@institution.edu \
  --batch-size 5
```

In batch mode:
- Accessions are split into groups of `--batch-size` (default 5)
- Each batch runs **sequentially** (parallel would violate NCBI per-IP rate limits)
- Each batch writes a checkpoint file: `output_b000.json`, `output_b001.json`, etc.
- If the process is interrupted, resume with `--start-batch N`
- All batch files are merged into the final `--output` JSON

### Step 4: Review Output

Report summary counts:
```
Done: 53 OK, 0 not_found, 0 errors -> output.json
```

For any `not_found`, verify the accession on the GEO website manually.
For any `error`, inspect the error message and retry if transient.

### Step 5: Output Structure

```json
{
  "GSE184362": {
    "status":     "ok",
    "accession":  "GSE184362",
    "title_en":   "Single-cell sequencing of tumor ecosystems in papillary thyroid carcinoma",
    "summary_en": "The tumor ecosystem of papillary thyroid carcinoma...",
    "gdsType":    "Expression profiling by high throughput sequencing",
    "n_samples":  "23",
    "taxon":      "Homo sapiens",
    "PDAT":       "2021/09/19",
    "supplFiles": ["MTX", "TSV"],
    "pmids":      ["34663816"],
    "geo_url":    "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE184362"
  }
}
```

The `geo_url` links to the GEO database page (the same page a browser would show at
`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE{xxxxx}`). FTP download links
are deliberately out of scope; use the page for manual download.

### Step 6: Build or Update Excel (built-in)

The skill now includes `scripts/build_excel.py` which handles both output strategies:

**Strategy A — 新建 Excel（from raw GSE numbers）：**
```bash
<python_path> scripts/build_excel.py \
  --meta meta.json \
  --trans trans.json \
  --output <name>.xlsx
```
Output columns: Accession | GEO标题(中) | 实验类型(中) | GEO摘要(中) | 样本类型 | 样本数 | PubMed IDs | 发布日期 | 数据下载(HYPERLINK)

**Strategy B — 追加策略（from existing spreadsheet）：**
```bash
<python_path> scripts/build_excel.py \
  --meta meta.json \
  --trans trans.json \
  --append existing.xlsx
```
- Finds the `Accession` column in the existing sheet
- Matches rows by Accession, appends 8 new columns to the right
- Adds HYPERLINK formulas for 数据下载
- Saves as `<original>_annotated.xlsx` (never overwrites original)

**Output strategy selection rule:**
- User provides raw GSE/GSM/GPL numbers → 新建 Excel
- User provides an `.xlsx` / `.xls` file → 追加策略

## Downstream Integration

### With academic-translate skill

After extraction, the JSON contains English `title_en`, `summary_en`, and `gdsType`
fields. Invoke the `academic-translate` skill to translate these into academic Chinese.

## Limitations

- Only returns metadata indexed in NCBI Entrez — raw expression matrices require
  separate download via GEO FTP or the GEO page
- Does NOT provide FTP download links (only `geo_url` to the database page)
- Non-GEO sources (GSA/ENA/Zenodo/CNGB) are out of scope
- `ExtRelations` parsing may miss some PubMed references depending on NCBI XML structure
- Rate limit is per-IP; batching is for checkpoint/resume benefit, not parallelism
