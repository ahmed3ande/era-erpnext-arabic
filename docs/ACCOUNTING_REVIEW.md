# Accounting Review Queue

The accounting review queue converts broad CP-02 findings into a smaller deterministic list.

## Generate

```bash
python scripts/audit_translations.py
python scripts/prioritize_review.py
```

Output:

```text
reports/audit/accounting-priority.csv
```

GitHub Actions uploads it in the `translation-audit` artifact and prints at most 50 highest-priority rows in the job log.

## Priority model

| Finding | Priority |
|---|---:|
| Approved/rejected glossary conflict | 100 |
| English source duplicated inside Arabic translation | 95 |
| Untranslated accounting string | 90 |
| Fuzzy accounting string | 85 |
| Accounting cross-app conflict | 80 |
| Meaningful English residue in an accounting string | 60 |

The queue uses an explicit accounting keyword set, deterministic ordering, and deduplication by category, app, and source message.

Before classifying residue, it removes HTML markup, URLs, Jinja expressions, placeholders, and code-like identifiers. Common technical tokens such as BOM, UOM, FIFO, DuckDB, POS, ERPNext, Frappe, and HRMS are allowed by themselves. If the complete English source is appended to an Arabic translation, the row is classified separately as `duplicated-source` so that this high-confidence defect is reviewed first.

## Review batches

A translation batch should contain no more than 50 related entries and must record:

- Source message
- Current Arabic translation
- Proposed Arabic translation
- Screen/report context
- Accounting rationale
- Reviewer status
- PO app/catalog
- Validation result

## Safety

Queue generation never edits PO catalogs. A reviewed batch is applied separately to canonical source catalogs and regenerated using the existing build pipeline.

## Apply an approved batch

Approved rows are versioned under `review_batches/`. Each row records the expected current Arabic, approved Arabic, and rationale.

```bash
python scripts/apply_review_batch.py review_batches/accounting-001.csv --write
python scripts/apply_review_batch.py review_batches/accounting-001.csv
```

The first command applies the batch to canonical source catalogs, matching shipped version bundles, v15 CSV bundles, and the runtime overlay. The second command is an idempotent check and is enforced in CI.

The tool refuses stale current text, unknown apps, duplicate app/source rows, missing canonical messages, and placeholder mismatches. Messages absent from an older generated version bundle are allowed; the runtime overlay is always required and receives the approved entry.

