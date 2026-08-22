# Project Status

This file is the single resume point for the Era Arabic translation project.

## Identity

- Project: Era ERPNext Arabic
- Maintainer: Techno Era
- Upstream: [ibrahim317/erpnext-arabic-full-translation](https://github.com/ibrahim317/erpnext-arabic-full-translation)
- Baseline: `0038ad7dc4f2b3e3cde5706d5fbd02bbd8be3f10`
- License: MIT

## Current position

- Milestone: M2 — Accounting terminology review
- Checkpoint: CP-03B — First accounting correction batch
- Active issue: #7
- Active branch: `feature/accounting-batch-001`
- Target: Frappe 16 / ERPNext 16 / HRMS 16
- Production reference: Arabic Translations 0.3.2
- Status: Draft PR #8 is v16-complete; validation commit `701df721` passed GitHub Actions run 26

## Completed

- [x] Fork created under Techno Era ownership
- [x] Original Git history and MIT license preserved
- [x] GitHub write access verified
- [x] Production and rebuild sites upgraded to 0.3.2
- [x] Project bootstrap issue created
- [x] Governance documentation and initial glossary merged
- [x] Translation audit tool and unit tests implemented
- [x] Placeholder regression gate passed
- [x] Audit reports published as CI artifact
- [x] Accounting priority queue implemented and documented
- [x] Markup, code, URL, Jinja, and technical-token noise filtered
- [x] Duplicated English source text classified separately
- [x] Queue validated: 110 rows (70 duplicated source, 31 English residue, 5 fuzzy, 3 cross-app conflicts, 1 glossary conflict)
- [x] CP-03A merged in PR #6
- [x] Batch 001 review CSV created with 33 guarded rows
- [x] Deterministic batch application and idempotency checks implemented
- [x] Local audit delta verified with zero placeholder errors
- [x] ERPNext and HRMS v16 source, runtime overlay, and v16 overwrite bundles synchronized
- [x] Missing reviewed v16 keys are appended and enforced by the idempotent check
- [x] Arabic wording independently reviewed against accounting and ERPNext context
- [x] Draft PR #8 opened
- [x] GitHub catalog, msgfmt, batch, audit, placeholder, and Ruff checks passed

## Next action

Perform the final human review of Draft PR #8, then decide whether to merge Batch 001. Do not deploy to production until the merged commit is separately verified.

## Resume protocol

When work resumes:

1. Read this file.
2. Open the active issue.
3. Check the linked pull request and CI status.
4. Continue only from the “Next action” above.
5. Update this file before ending a work session.

## Blockers

None.
