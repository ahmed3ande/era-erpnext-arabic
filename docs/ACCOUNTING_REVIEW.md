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
| Untranslated accounting string | 90 |
| Fuzzy accounting string | 85 |
| Accounting cross-app conflict | 80 |
| Accounting string with English residue | 60 |

The queue uses an explicit accounting keyword set, deterministic ordering, and deduplication by category, app, and source message.

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
