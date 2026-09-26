# Era Arabic 0.5.0 — ERPNext and HRMS V16

Prepared 2026-09-26. Upstream source: Ibrahim's
`7168aaf4c5169ee0f477990dbc143b70f74587cc`, combined with Era 0.4.0 and the
user-approved September review. Ibrahim's original MIT copyright is retained.

## Included

- Previously approved accounting and interface corrections, including all five
  requested Journal Entry labels and the four additional approved proposals.
- New upstream terminology corrections and 55 HRMS dashboard labels.
- Egyptian terminology retained: العميل, سند دفع أو قبض, كشف ساعات العمل.
- HR review: المسمى الوظيفي, تعيين الوردية, تقييم الأداء, مفردات المرتب,
  تخصيص رصيد الإجازات and تسجيل حضور وانصراف الموظف.
- Explicit wording decisions are guarded by `review_batches/egypt-hr-002.csv`.
- Historical bilingual-cleanup guards updated where reviewed newer wording
  supersedes the old wording; previous revisions remain in Git history.
- Read-only fixture audit inherited from upstream, and a new site-specific
  deployment report showing effective translations and application precedence.

Translation changes do not change English document identifiers, accounting
logic, payroll calculations, Egyptian tax rates or social-insurance rules.

## Deployment checks — do not skip

This release has not been tested against the user's live database. Before
deployment, record the actual site name, installed versions, current Git SHA,
clean working-tree status and translation delivery mode. Back up database,
files and configuration, and retain the previous Git commit as a rollback point.

All sites on a bench share this application's code and compiled assets. Updating
one checkout is NOT isolation to one site, even when migrate targets one site.
Use an isolated bench for a truly isolated trial.

After the agreed update/migration, run:

```sh
bench --site SITE execute arabic_translations.utils.deployment_report
bench --site SITE execute arabic_translations.audit.report
```

Replace SITE with the verified current site name. The first command reports
whether HRMS is installed, apps loaded after Era, and expected/actual sample
labels. The second discovers untranslated fixture labels. Both are read-only.

If HRMS was installed after Era, it can override shared Arabic keys in overlay
mode. Do not uninstall applications, edit apps.txt blindly, or assume clearing
cache fixes order. Verify site-specific installed-app order and custom database
Translation records first. No automatic reorder is performed in this release.

Do not switch to overwrite/both blindly: those modes modify other applications'
catalogs across the bench. No server operation is performed by preparing this
release on GitHub.

## Scope and known limits

All 2,229 keys in the checked official HRMS V16 template have translations.
The template header is dated June 24, 2026, so this is not a guarantee of every
screen in every HRMS patch release. Custom fields and custom apps need a live
fixture audit and screen checks. Fifteen inherited ERPNext fuzzy messages remain
excluded from the combined overlay pending contextual review; no HRMS messages
are fuzzy or empty in the source catalog.

Review employee records, shifts, attendance, leave requests, salary structures,
salary slips, payroll entries and dashboard cards on the actual site. Verify
ordinary and context-specific UI labels, not only presence of the generated MO.

## Rollback

Retain the pre-update SHA and backup paths. A code-only translation rollback
requires restoring the previous application commit, rebuilding its translations
and clearing the affected sites' translation cache. If an update migration made
database changes, evaluate the matching database/files backup before recovery.
Never run a generic bench update or database restore merely to change wording.
