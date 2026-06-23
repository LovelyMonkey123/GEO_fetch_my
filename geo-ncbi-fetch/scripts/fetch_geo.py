#!/usr/bin/env python3
"""Fetch GEO metadata from NCBI E-utilities, with batched resume support.

Usage:
  python fetch_geo.py --input "GSE184362,GSE33630" --output meta.json
  python fetch_geo.py --input accs.txt --output meta.json --email u@inst.edu
  python fetch_geo.py --input accs.txt --output meta.json --batch-size 5

Input:  comma/space/newline separated accessions, file path, or JSON array/list.
Output: JSON dict keyed by accession with metadata fields + GEO database page URL.
"""

import argparse, json, re, sys, time

# ── Helpers ────────────────────────────────────────────────

def clean(value, default=""):
    """Strip Biopython element wrappers (IntegerElement, StringElement) to plain Python."""
    if value is None:
        return default
    s = str(value)
    m = re.match(r"(?:Integer|String|List)Element\(([^,)]+)", s)
    if m:
        return m.group(1).strip("'\"")
    return "" if "ListElement" in s else s


def extract_sample_types(summary, samples_titles):
    """Heuristic extraction of sample types from summary text and sample titles."""
    seen = set()
    result = []
    joined = ((summary or "") + " " + " ".join(samples_titles)).lower()
    for kw, label in [
        ("tumor", "肿瘤组织"), ("carcinoma", "肿瘤组织"), ("cancer", "肿瘤组织"),
        ("normal", "正常组织"), ("paratumor", "癌旁组织"), ("adjacent", "癌旁组织"),
        ("metasta", "转移灶"), ("lymph node", "淋巴结"),
        ("blood", "血液"), ("peripheral blood", "外周血"),
        ("cell line", "细胞系"), ("organoid", "类器官"), ("pbmc", "PBMC"),
        ("primary tumor", "原发肿瘤"), ("recurrent", "复发肿瘤"),
        ("anaplastic", "未分化癌"), ("poorly-differentiated", "低分化癌"),
        ("papillary", "乳头状癌"), ("follicular", "滤泡状癌"), ("medullary", "髓样癌"),
    ]:
        if kw in joined and label not in seen:
            seen.add(label)
            result.append(label)
    return result


def parse_accessions(raw):
    """Extract and deduplicate GSE/GSM/GPL accessions from raw text."""
    return list(dict.fromkeys(re.findall(r'(G(?:SE|SM|PL)\d+)', raw.upper())))


def read_input(source):
    """Parse accessions from file, JSON, or inline string. Returns list."""
    if source.endswith(".json"):
        with open(source, encoding="utf-8") as f:
            data = json.load(f)
        accs = list(data.keys()) if isinstance(data, dict) else data
        return parse_accessions(",".join(accs))

    if source.endswith((".txt", ".csv", ".tsv")):
        with open(source, encoding="utf-8") as f:
            return parse_accessions(f.read())

    return parse_accessions(source)


# ── NCBI fetch ─────────────────────────────────────────────

GEO_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={}"


def fetch_one(acc, email, api_key):
    """Query NCBI E-utilities for a single GEO accession. Returns (status, dict)."""
    from Bio import Entrez
    Entrez.email = email
    if api_key:
        Entrez.api_key = api_key

    # Validate
    h = Entrez.esearch(db="gds", term=f"{acc}[ACCN]", retmax=1)
    rec = Entrez.read(h)
    h.close()
    uid = rec["IdList"][0] if rec.get("IdList") else None
    if not uid:
        return ("not_found", {"status": "not_found", "accession": acc})

    # Fetch
    h = Entrez.esummary(db="gds", id=uid)
    rec = Entrez.read(h)
    h.close()
    d = rec[0] if isinstance(rec, list) else rec

    # Parse supplementary files
    sf = clean(d.get("suppFile", ""))
    suppl = [s.strip() for s in sf.split(";") if s.strip()] if sf and sf.upper() != "NONE" else []

    # Parse PubMed IDs from PubMedIds field (not ExtRelations which is often empty)
    pmids_raw = d.get("PubMedIds", [])
    if pmids_raw:
        pmids_list = pmids_raw if isinstance(pmids_raw, list) else [pmids_raw]
        pmids = [clean(x) for x in pmids_list]
    else:
        pmids = []

    # Parse sample titles (hint at tissue/cell types)
    samples = d.get("Samples", [])
    sample_titles = []
    if samples:
        for s in samples:
            title = s.get("Title", "") if isinstance(s, dict) else clean(getattr(s, "Title", ""))
            if title:
                sample_titles.append(title)
    sample_types = extract_sample_types(clean(d.get("summary")), sample_titles)

    result = {
        "status":       "ok",
        "accession":    acc,
        "title_en":     clean(d.get("title")),
        "summary_en":   clean(d.get("summary")),
        "gdsType":      clean(d.get("gdsType")),
        "n_samples":    clean(d.get("n_samples")),
        "taxon":        clean(d.get("taxon")),
        "PDAT":         clean(d.get("PDAT")),
        "supplFiles":   suppl,
        "pmids":        pmids,
        "sample_types": sample_types,
        "geo_url":      GEO_URL.format(acc),
    }
    return ("ok", result)


def fetch_batch(accessions, email, api_key=None, sleep_s=0.35, label=""):
    """Fetch metadata for a batch of accessions sequentially, with rate limiting."""
    results = {}
    total = len(accessions)
    prefix = f"[{label}] " if label else ""

    for i, acc in enumerate(accessions):
        if i > 0:
            time.sleep(sleep_s)

        try:
            status, data = fetch_one(acc, email, api_key)
            results[acc] = data
            tag = f"{data.get('n_samples','?')} samples" if status == "ok" else status
            print(f"  {prefix}[{i+1}/{total}] {acc} -> {tag}", flush=True)
        except Exception as e:
            results[acc] = {"status": "error", "accession": acc, "error": str(e)}
            print(f"  {prefix}[{i+1}/{total}] {acc} -> ERROR ({str(e)[:80]})", flush=True)

    return results


# ── Main ───────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Fetch GEO metadata from NCBI E-utilities")
    p.add_argument("--input", required=True, help="Accessions (inline, file path, or JSON)")
    p.add_argument("--output", required=True, help="Output JSON file path")
    p.add_argument("--email", default="user@institution.edu", help="NCBI-required email")
    p.add_argument("--api-key", default=None)
    p.add_argument("--sleep", type=float, default=0.35)
    p.add_argument("--batch-size", type=int, default=0,
                   help="Split into batches of N; 0 disables batching")
    p.add_argument("--start-batch", type=int, default=0,
                   help="Resume from this batch index (0-based)")
    args = p.parse_args()

    accs = read_input(args.input)
    if not accs:
        print("ERROR: No valid GEO accessions found in input.", file=sys.stderr)
        sys.exit(1)

    total = len(accs)
    print(f"Found {total} GEO accessions.", flush=True)

    # ── Batch mode ──
    batch_size = args.batch_size if args.batch_size > 0 else total
    batches = [accs[i:i+batch_size] for i in range(0, total, batch_size)]

    if len(batches) > 1:
        print(f"Split into {len(batches)} batches (size={batch_size}). "
              f"Starting from batch {args.start_batch}.", flush=True)

    all_results = {}
    for bi in range(args.start_batch, len(batches)):
        baccs = batches[bi]
        tag = f"B{bi+1}/{len(batches)}" if len(batches) > 1 else ""
        print(f"\n-- Batch {bi+1}/{len(batches)} ({len(baccs)} accessions) --", flush=True)

        batch_results = fetch_batch(baccs, args.email, args.api_key, args.sleep, label=tag)

        # Save batch checkpoint
        if len(batches) > 1:
            base, ext = args.output.rsplit(".", 1) if "." in args.output else (args.output, "json")
            batch_file = f"{base}_b{bi:03d}.{ext}" if "." in args.output else f"{args.output}_b{bi:03d}"
            with open(batch_file, "w", encoding="utf-8") as f:
                json.dump(batch_results, f, ensure_ascii=False, indent=2)
            print(f"  Batch saved -> {batch_file}", flush=True)

        all_results.update(batch_results)

    # ── Merge if batched ──
    if len(batches) > 1:
        print(f"\nMerging {len(batches)} batches...", flush=True)

    # Counts
    ok  = sum(1 for v in all_results.values() if v["status"] == "ok")
    nf  = sum(1 for v in all_results.values() if v["status"] == "not_found")
    err = sum(1 for v in all_results.values() if v["status"] == "error")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\nDone: {ok} OK, {nf} not found, {err} errors -> {args.output}", flush=True)


if __name__ == "__main__":
    main()
