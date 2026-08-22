# Translation Guide

## Language standard

Use clear Modern Standard Arabic suitable for accounting and ERP users. Avoid colloquial interface text. Egyptian professional terminology may be selected when it is established in accounting practice and remains understandable across Arabic-speaking markets.

## Decision order

1. Determine the business context.
2. Check the approved glossary.
3. Inspect the actual ERPNext screen or report.
4. Preserve placeholders and markup exactly.
5. Prefer concise professional terminology.
6. Record ambiguous cases instead of guessing.
7. Cite the Egyptian accounting or professional basis for high-impact terms.

## Required statuses

- `proposed`
- `needs-context`
- `accounting-review`
- `language-review`
- `approved`
- `rejected`

Only `approved` terms may be applied as glossary-wide replacements.

## Core rules

- `Balance` in an account context is **الرصيد**, not **الموازنة**.
- `Budget` must not be translated as balance.
- `Debit` and `Credit` are **مدين** and **دائن** in ledger contexts.
- `Submit` in ERPNext DocStatus context means **اعتماد**. Use **ترحيل** for the accounting posting effect, not for every workflow action.
- Translate `Entry` by context: قيد، حركة، or سند.
- Do not translate the same English word mechanically across unrelated contexts.
- Do not change placeholders such as `{0}`, `{name}`, or `%(company)s`.
- Preserve HTML, Markdown, and Jinja syntax.

## Review evidence

Every translation PR must state:

- Domain and screens reviewed
- Number of entries changed
- Important terminology decisions
- ERPNext/Frappe versions tested
- Catalog validation result
- Reference/reviewer status
- Screenshots for high-impact UI changes when available

## File workflow

Canonical translations are edited under:

```text
arabic_translations/locale/source/<app>/ar.po
```

Generated bundles must be rebuilt using the repository scripts. Generated files are never edited as the only source of a correction.

## Egyptian terminology authority

Use the following decision hierarchy instead of requiring an accountant to approve every established term:

1. Egyptian Accounting Standards and official Financial Regulatory Authority publications.
2. Stable terminology in Egyptian university accounting curricula and professional practice.
3. The business meaning and actual screen context in ERPNext/Frappe.
4. Clear Modern Standard Arabic suitable for users outside Egypt when it does not conflict with Egyptian usage.

Human specialist review is reserved for genuinely ambiguous treatments or legal/tax wording. Established terms such as **قائمة المركز المالي**، **قائمة الدخل**، **ميزان المراجعة**، **مدين**، and **دائن** can be approved from authoritative references and context.
