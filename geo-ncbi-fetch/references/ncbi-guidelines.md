# NCBI Usage Guidelines — Deep Reference

Loaded on demand when user needs detailed policy information.

## Rate Limits (Official)

| Tier | Rate | Requirement |
|------|------|-------------|
| Anonymous | ≤ 3 req/s | No registration |
| API Key | ≤ 10 req/s | Free NCBI account + registered API key |
| Enhanced | > 10 req/s | Email NCBI Help Desk with project description |

- API key registration: https://www.ncbi.nlm.nih.gov/account/
- Do NOT exceed limits: IP may be temporarily blocked
- Off-peak hours: 9 PM–5 AM US Eastern (weekdays) or weekends

## E-utilities Best Practices

1. **Always set `email`** — parameter is mandatory, not optional
2. **Set `tool`** in production — identifies your application to NCBI
3. **Batch sensibly** — prefer sequential with sleep over parallel bursts
4. **Handle 429 gracefully** — sleep 5s and retry once
5. **Cache locally** — metadata changes infrequently; avoid re-fetching

## GEO vs Entrez

- GEO records are indexed in Entrez under `db="gds"`
- Not all GEO records appear instantly: allow 1-2 days after submission
- Superseded/withdrawn records return no UID from `esearch`
- `esummary` returns Entrez-indexed metadata only — raw data files on FTP

## Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Empty `IdList` | Accession not in Entrez | Verify on GEO website manually |
| Missing `ExtRelations` | NCBI XML structure change | Fall back to manual PMID lookup |
| `ptech` field empty | NCBI record incomplete | Not a script error; field is optional |
| `CEL, TXT` in suppFile | Comma-separated multi-value | Split by ";" or "," |
