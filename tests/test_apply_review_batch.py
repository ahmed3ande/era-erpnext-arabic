from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from babel.messages.catalog import Catalog
from babel.messages.pofile import read_po, write_po

from scripts.apply_review_batch import BatchError, apply_batch, read_batch


class ApplyReviewBatchTest(unittest.TestCase):
	def setUp(self):
		self.temp_dir = tempfile.TemporaryDirectory()
		self.root = Path(self.temp_dir.name)
		self.batch = self.root / "batch.csv"
		self._write_batch("فاتورة شراء", "فاتورة مشتريات")
		for path in (
			self.root / "arabic_translations/locale/source/erpnext/ar.po",
			self.root / "arabic_translations/locale/other-apps/v16/erpnext/erpnext/locale/ar.po",
			self.root / "arabic_translations/locale/ar.po",
		):
			self._write_po(path, "فاتورة شراء", fuzzy=True)
		csv_path = (
			self.root
			/ "arabic_translations/locale/other-apps/v15/erpnext/erpnext/translations/ar.csv"
		)
		csv_path.parent.mkdir(parents=True)
		with csv_path.open("w", encoding="utf-8", newline="") as handle:
			csv.writer(handle).writerow(["Purchase Invoice", "فاتورة شراء", ""])

	def tearDown(self):
		self.temp_dir.cleanup()

	def _write_batch(self, current: str, approved: str):
		with self.batch.open("w", encoding="utf-8", newline="") as handle:
			writer = csv.writer(handle)
			writer.writerow(
				["batch_id", "app", "msgid", "current_arabic", "approved_arabic", "rationale"]
			)
			writer.writerow(["test", "erpnext", "Purchase Invoice", current, approved, "test rationale"])

	def _write_po(self, path: Path, translation: str, *, fuzzy: bool):
		path.parent.mkdir(parents=True, exist_ok=True)
		catalog = Catalog(locale="ar")
		message = catalog.add("Purchase Invoice", translation)
		if fuzzy:
			message.flags.add("fuzzy")
		with path.open("wb") as handle:
			write_po(handle, catalog)

	def _translation(self, path: Path) -> tuple[str, set[str]]:
		with path.open(encoding="utf-8") as handle:
			message = read_po(handle).get("Purchase Invoice")
		return message.string, message.flags

	def test_write_then_check_is_idempotent(self):
		counts = apply_batch(self.root, self.batch, write=True)
		self.assertGreater(sum(counts.values()), 0)
		for path in (
			self.root / "arabic_translations/locale/source/erpnext/ar.po",
			self.root / "arabic_translations/locale/other-apps/v16/erpnext/erpnext/locale/ar.po",
			self.root / "arabic_translations/locale/ar.po",
		):
			translation, flags = self._translation(path)
			self.assertEqual(translation, "فاتورة مشتريات")
			self.assertNotIn("fuzzy", flags)
		self.assertEqual(sum(apply_batch(self.root, self.batch, write=False).values()), 0)

	def test_stale_current_guard_is_rejected(self):
		self._write_po(
			self.root / "arabic_translations/locale/source/erpnext/ar.po",
			"ترجمة عدّلها مراجع آخر",
			fuzzy=False,
		)
		with self.assertRaisesRegex(BatchError, "stale current_arabic guard"):
			apply_batch(self.root, self.batch, write=True)

	def test_placeholder_mismatch_is_rejected(self):
		self._write_batch("الحساب {0}", "الحساب {1}")
		with self.assertRaisesRegex(BatchError, "placeholder mismatch"):
			read_batch(self.batch)


if __name__ == "__main__":
	unittest.main()

