# NCBI E-utilities for GEO — Tool Reference

## Database Parameters

| Accession Type | `db` Parameter | Description |
|---------------|---------------|-------------|
| GSE (Series) | `gds` | GEO DataSets — series-level experiment metadata |
| GSM (Sample) | `gds` | Individual sample records within a series |
| GPL (Platform) | `gds` | Array/sequencer platform definitions |

All GEO records are accessed through `db="gds"` in Entrez.

## Core API Calls

### 1. Validate Accession — `esearch`

```python
from Bio import Entrez
Entrez.email = "user@institution.edu"  # REQUIRED by NCBI

handle = Entrez.esearch(db="gds", term="GSE184362[ACCN]", retmax=1)
record = Entrez.read(handle)
uid = record["IdList"][0]  # None if not found
handle.close()
```

### 2. Fetch Metadata — `esummary`

```python
handle = Entrez.esummary(db="gds", id=uid)
record = Entrez.read(handle)
# record[0] keys: title, summary, gdsType, n_samples, taxon, PDAT,
#                 suppFile, ExtRelations, accession, ptech
handle.close()
```

## Extracted Fields

| Field | NCBI Key | Description |
|-------|----------|-------------|
| title_en | `title` | Dataset title (English) |
| summary_en | `summary` | Experimental design description |
| gdsType | `gdsType` | e.g. "Expression profiling by high throughput sequencing" |
| n_samples | `n_samples` | Number of samples in the series |
| taxon | `taxon` | Species (e.g. "Homo sapiens") |
| PDAT | `PDAT` | Publication/release date (YYYY/MM/DD) |
| supplFiles | `suppFile` | Supplementary file types (CEL, MTX, TSV, etc.) |
| pmids | `ExtRelations` | PubMed IDs linked to the dataset |
| geo_url | *constructed* | `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={ACC}` |

## Rate Limiting

NCBI enforces per-IP rate limits:

| Configuration | Rate Limit |
|--------------|-----------|
| Default (no API key) | ≤ 3 requests/second |
| With registered API key | ≤ 10 requests/second |

- Default sleep interval: **0.35s** (accounts for network jitter)
- API key registration: https://www.ncbi.nlm.nih.gov/account/ (free, ~30 seconds)
- Large batches: schedule during NCBI off-peak hours (US Eastern night/weekends)

**Important:** The limit is per-IP, not per-process. Running parallel scripts will
trigger HTTP 429 errors. Sequential execution with proper sleep is the correct approach.

## Batch Mode (built into fetch_geo.py)

For >5 accessions, use `--batch-size 5` to enable checkpoint/resume:

```
python fetch_geo.py --batch-size 5 --input accs.txt --output meta.json
```

- Each batch of N accessions runs sequentially
- Batch results saved to `meta_b000.json`, `meta_b001.json`, etc.
- On interruption, resume: `--start-batch 3` (skips batches 0-2)
- All batches merged into final `meta.json` on completion

## Error Handling

| Condition | Handling |
|-----------|----------|
| Accession not found in Entrez | Mark `not_found`, continue |
| Network timeout / HTTP error | Mark `error`, continue |
| Malformed response | Mark `error` with exception message |
| Interrupted batch run | Resume with `--start-batch N` |
