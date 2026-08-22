from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.prioritize_ui_review import build_queue


class PrioritizeUiReviewTest(unittest.TestCase):
	def test_core_ui_findings_are_selected_and_sorted(self) -> None:
		with tempfile.TemporaryDirectory() as temp_dir:
			audit_dir = Path(temp_dir)
			self._write(
				audit_dir / "untranslated-and-fuzzy.csv",
				["app", "msgid", "msgstr", "fuzzy", "path"],
				[
					{"app": "frappe", "msgid": "User Settings", "msgstr": "", "fuzzy": "False", "path": "frappe/ar.po"},
					{"app": "frappe", "msgid": "Unrelated sentence", "msgstr": "", "fuzzy": "False", "path": "frappe/ar.po"},
				],
			)
			self._write(audit_dir / "cross-app-conflicts.csv", ["msgid", "apps", "translations"], [])
			self._write(
				audit_dir / "english-residue.csv",
				["app", "msgid", "msgstr", "fuzzy", "path", "english_words"],
				[{"app": "erpnext", "msgid": "Payment Settings", "msgstr": "إعدادات Payment", "fuzzy": "False", "path": "erpnext/ar.po", "english_words": "Payment"}],
			)

			queue = build_queue(audit_dir)
			self.assertEqual([row["msgid"] for row in queue], ["User Settings", "Payment Settings"])
			self.assertEqual(queue[0]["priority"], 100)

	@staticmethod
	def _write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
		with path.open("w", encoding="utf-8", newline="") as handle:
			writer = csv.DictWriter(handle, fieldnames=fields)
			writer.writeheader()
			writer.writerows(rows)


if __name__ == "__main__":
	unittest.main()
