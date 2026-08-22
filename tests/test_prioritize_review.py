from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.prioritize_review import (
	build_queue,
	english_words,
	has_duplicated_source,
	is_accounting_related,
	write_queue,
)


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

	def test_duplicated_source_detection(self):
		self.assertTrue(
			has_duplicated_source(
				"Account {0} does not belong to company: {1}",
				"الحساب {0} لا ينتمي إلى الشركة {1}<br>Account {0} does not belong to company: {1}",
			)
		)
		self.assertTrue(
			has_duplicated_source(
				"Account with existing transaction can not be deleted",
				"الحساب لديه معاملات موجودة لا يمكن حذفه\\n<br>\\nAccount with existing transaction can not be deleted",
			)
		)
		self.assertFalse(has_duplicated_source("Sales Invoice", "فاتورة مبيعات"))

	def test_markup_and_technical_tokens_are_not_residue(self):
		value = (
			'<b class="x">{{ doc.name }}</b> https://example.com FIFO UOM BOM DuckDB POS CWIP '
			'&lt;p&gt;نص عربي&lt;/p&gt; <b>customer</b> مثال: doc.item_code == "Stock Entry"'
		)
		self.assertEqual(english_words(value), [])
		self.assertEqual(english_words("فاتورة Sales"), ["Sales"])

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
				[
					["erpnext", "Sales Invoice", "فاتورة Sales", "Sales"],
					[
						"erpnext",
						"Account does not belong to company",
						"الحساب لا ينتمي إلى الشركة<br>Account does not belong to company",
						"Account | does | not | belong | to | company",
					],
					["erpnext", "Stock valuation", "التقييم FIFO عبر {{ method }}", "FIFO | method"],
				],
			)

			queue = build_queue(root)
			self.assertEqual([row["priority"] for row in queue], [100, 95, 90, 85, 80, 60])
			self.assertNotIn("Employee birthday", {row["msgid"] for row in queue})
			self.assertNotIn("Stock valuation", {row["msgid"] for row in queue})
			output = root / "accounting-priority.csv"
			write_queue(output, queue)
			self.assertTrue(output.read_text(encoding="utf-8").startswith("priority,category"))


if __name__ == "__main__":
	unittest.main()

