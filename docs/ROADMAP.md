# Era ERPNext Arabic Roadmap

## Mission

Provide professional, context-aware Arabic accounting translations for Frappe, ERPNext, and HRMS while preserving the original work and contribution history.

## Principles

- Accounting meaning takes priority over literal translation.
- Modern Standard Arabic is the public baseline.
- Egyptian accounting usage is documented where terminology differs.
- Existing internal package name `arabic_translations` remains stable.
- Every translation batch is reviewed, tested, and traceable.
- General fixes should be offered back to the upstream project when practical.

## Checkpoints

### CP-01 — Project governance

- Attribution and licensing
- Resumable status file
- Translation guide
- Initial glossary
- Contribution and release workflow

### CP-02 — Translation audit

- Catalog coverage report
- Conflicting translation report
- Suspicious accounting terminology report
- Placeholder and formatting validation
- Prioritized review queue

### CP-03 — Core accounting

- Chart of Accounts
- Journal Entry
- General Ledger
- Trial Balance
- Profit and Loss
- Balance Sheet
- Cost Centers and dimensions

### CP-04 — Commercial accounting

- Accounts Receivable
- Accounts Payable
- Payments
- Selling
- Buying
- Taxes and returns

### CP-05 — Operations

- Stock
- Assets
- Manufacturing
- Projects
- HRMS

### CP-06 — ERPNext v16 UAT

- Rebuild-site testing
- Production-safe deployment instructions
- Before/after screenshots
- Regression checklist

### CP-07 — First stable Era release

- Release notes
- Supported-version matrix
- Installation and rollback instructions
- Tagged stable release

## Git workflow

- `develop`: integration branch
- `main`: stable releases only
- `translation/<domain>`: reviewed translation batches
- `feature/<name>`: tooling and documentation
- `fix/<name>`: defects
- `maintenance/sync-upstream-YYYY-MM-DD`: upstream synchronization

No direct project changes are committed to `develop` or `main`.
