from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_translations import audit, placeholders


PO_HEADER = '''msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

'''


class AuditTranslationsTest(unittest.TestCase):
	def test_placeholder_detection(self):
		self.assertEqual(placeholders("Invoice {0} for %(company)s: %s"), {"{0}", "%(company)s", "%s"})

	def test_literal_percent_and_braces_are_not_placeholders(self):
		self.assertEqual(placeholders("% Complete must be between 0 and 100"), set())
		self.assertEqual(placeholders("Use % as wildcard and allow 10% of total"), set())
		self.assertEqual(placeholders("Example {0.00, 0.04, 0.09}"), set())
		self.assertEqual(placeholders('JavaScript {fieldname: "company"}'), set())

	def test_reports_are_deterministic_and_find_defects(self):
		with tempfile.TemporaryDirectory() as temp_dir:
			root = Path(temp_dir)
			locale_root = root / "source"
			(locale_root / "frappe").mkdir(parents=True)
			(locale_root / "erpnext").mkdir(parents=True)
			(locale_root / "frappe" / "ar.po").write_text(
				PO_HEADER
				+ '''msgid "Balance"
msgstr "الموازنة"

msgid "Invoice {0}"
msgstr "فاتورة {1}"

msgid "Shared"
msgstr "مشترك"
''',
				encoding="utf-8",
			)
			(locale_root / "erpnext" / "ar.po").write_text(
				PO_HEADER
				+ '''#, fuzzy
msgid "Missing"
msgstr "مفقود"

msgid "Shared"
msgstr "مشتركة"
''',
				encoding="utf-8",
			)
			glossary = root / "accounting.csv"
			with glossary.open("w", encoding="utf-8", newline="") as handle:
				writer = csv.writer(handle)
				writer.writerow(["source", "approved_arabic", "rejected", "status"])
				writer.writerow(["Balance", "الرصيد", "الموازنة", "approved"])

			output = root / "reports"
			summary = audit(locale_root, glossary, output)

			self.assertEqual(summary["entries"], 5)
			self.assertEqual(summary["findings"]["placeholder_errors"], 1)
			self.assertEqual(summary["findings"]["cross_app_conflicts"], 1)
			self.assertEqual(summary["findings"]["glossary_conflicts"], 1)
			self.assertEqual(summary["findings"]["untranslated_or_fuzzy"], 1)
			self.assertEqual(
				json.loads((output / "audit-summary.json").read_text(encoding="utf-8")), summary
			)


if __name__ == "__main__":
	unittest.main()

