# Accounting Batch 001

Batch file: `review_batches/accounting-001.csv`

## Scope

- 33 reviewed app/message rows
- 29 unique source messages
- 1 approved glossary correction
- 5 fuzzy accounting corrections
- 3 cross-app conflicts unified
- 21 duplicated-English catalog entries removed

The batch concentrates on invoices, accounts, journal entries, payment entries, cost centers, currency, and opening-stock messages.

## Safety controls

- Exact current-Arabic guard on canonical source catalogs
- Exact placeholder-set validation
- Duplicate app/message rejection
- Fuzzy flag removal only for approved rows
- Deterministic sync into the runtime overlay and matching shipped bundles
- Required append of reviewed messages missing from ERPNext or HRMS v16 bundles
- Idempotent CI verification

The Arabic wording received a second independent accounting review before publication. In particular, the review aligned Stock Entry, ledger account, closing account, payment voucher, debit/credit movement, and grand-total terminology with their ERPNext context.

## Verified local audit delta

| Finding | Before | After | Delta |
|---|---:|---:|---:|
| Prioritized accounting queue | 110 | 80 | -30 |
| Duplicated-source queue | 70 | 49 | -21 |
| Fuzzy ERPNext entries | 23 | 18 | -5 |
| Accounting cross-app queue | 3 | 0 | -3 |
| Glossary conflicts | 1 | 0 | -1 |
| Placeholder errors | 0 | 0 | 0 |

The broad cross-app audit decreased from 35 to 32 and English-residue candidates from 1,242 to 1,221.

## Deployment

This batch is not deployed automatically. Production remains on the last verified 0.3.2 installation until the pull request passes CI and a separate deployment decision is made.
