"""Build a deterministic project-wide UI review queue from translation audits."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
	from scripts.prioritize_review import english_words, has_duplicated_source, read_csv
except ModuleNotFoundError:  # Direct execution: python scripts/prioritize_ui_review.py
	from prioritize_review import english_words, has_duplicated_source, read_csv

CORE_UI_TERMS = {
	"user",
	"users",
	"view",
	"workspace",
	"dashboard",
	"report",
	"list",
	"image",
	"kanban",
	"invoicing",
	"subscription",
	"budget",
	"banking",
	"payment",
	"tax",
	"share management",
	"role",
	"permission",
	"setting",
	"notification",
}

FIELDS = ["priority", "category", "app", "msgid", "msgstr", "reason", "source_report"]


def is_core_ui(msgid: str) -> bool:
	value = msgid.casefold()
	return any(term in value for term in CORE_UI_TERMS)


def build_queue(audit_dir: Path) -> list[dict[str, object]]:
	rows: list[dict[str, object]] = []
	for row in read_csv(audit_dir / "untranslated-and-fuzzy.csv"):
		if is_core_ui(row.get("msgid", "")):
			rows.append({
				"priority": 100,
				"category": "untranslated-or-fuzzy",
				"app": row.get("app", ""),
				"msgid": row.get("msgid", ""),
				"msgstr": row.get("msgstr", ""),
				"reason": "Core UI string requires review",
				"source_report": "untranslated-and-fuzzy.csv",
			})
	for row in read_csv(audit_dir / "cross-app-conflicts.csv"):
		if is_core_ui(row.get("msgid", "")):
			rows.append({
				"priority": 90,
				"category": "cross-app-conflict",
				"app": row.get("apps", ""),
				"msgid": row.get("msgid", ""),
				"msgstr": row.get("translations", ""),
				"reason": "Core UI term differs across apps",
				"source_report": "cross-app-conflicts.csv",
			})
	for row in read_csv(audit_dir / "english-residue.csv"):
		msgid = row.get("msgid", "")
		msgstr = row.get("msgstr", "")
		if not is_core_ui(msgid):
			continue
		residue = english_words(msgstr)
		if not residue:
			continue
		rows.append({
			"priority": 95 if has_duplicated_source(msgid, msgstr) else 70,
			"category": "duplicated-source" if has_duplicated_source(msgid, msgstr) else "english-residue",
			"app": row.get("app", ""),
			"msgid": msgid,
			"msgstr": msgstr,
			"reason": "English source duplicated" if has_duplicated_source(msgid, msgstr) else f"English candidates: {' | '.join(residue)}",
			"source_report": "english-residue.csv",
		})
	unique = {(str(row["category"]), str(row["app"]), str(row["msgid"])): row for row in rows}
	return sorted(unique.values(), key=lambda row: (-int(row["priority"]), str(row["app"]), str(row["msgid"])))


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--audit-dir", type=Path, default=Path("reports/audit"))
	parser.add_argument("--output", type=Path, default=Path("reports/audit/ui-priority.csv"))
	args = parser.parse_args()
	rows = build_queue(args.audit_dir)
	args.output.parent.mkdir(parents=True, exist_ok=True)
	with args.output.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.DictWriter(handle, fieldnames=FIELDS)
		writer.writeheader()
		writer.writerows(rows)
	print(f"ui-priority: {len(rows)}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
