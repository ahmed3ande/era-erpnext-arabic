from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.prioritize_review import build_queue, is_accounting_related, write_queue


def write_csv(path: Path, fieldnames: list[str], rows: list[list[str]]) -> None:
	with path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.writer(handle)
		writer.writerow(fieldnames)
		writer.writerows(rows)


class PrioritizeReviewTest(unittest.TestCase):
	def test_accounting_filter(self):
		self.assertTrue(is_accounting_related("Outstanding invoice balance"))
		self.assertTrue(is_accounting_related("General Ledger"))
		self.assertFalse(is_accounting_related("Employee birthday"))

	def test_queue_order_and_filtering(self):
		with tempfile.TemporaryDirectory() as temp_dir:
			root = Path(temp_dir)
			write_csv(
				root / "glossary-conflicts.csv",
				["app", "msgid", "msgstr", "reason"],
				[["erpnext", "Balance", "الموازنة", "uses-rejected-term"]],
			)
			write_csv(
				root / "untranslated-and-fuzzy.csv",
				["app", "msgid", "msgstr", "fuzzy"],
				[
					["erpnext", "Bank reconciliation", "", "False"],
					["hrms", "Employee birthday", "", "False"],
					["erpnext", "Tax Account", "حساب الضريبة", "True"],
				],
			)
			write_csv(
				root / "cross-app-conflicts.csv",
				["msgid", "apps", "translations"],
				[["Account", "erpnext | frappe", "حساب || محاسبة"]],
			)
			write_csv(
				root / "english-residue.csv",
				["app", "msgid", "msgstr", "english_words"],
				[["erpnext", "Sales Invoice", "فاتورة Sales", "Sales"]],
			)

			queue = build_queue(root)
			self.assertEqual([row["priority"] for row in queue], [100, 90, 85, 80, 60])
			self.assertNotIn("Employee birthday", {row["msgid"] for row in queue})
			output = root / "accounting-priority.csv"
			write_queue(output, queue)
			self.assertTrue(output.read_text(encoding="utf-8").startswith("priority,category"))


if __name__ == "__main__":
	unittest.main()

