"""Build a deterministic accounting review queue from translation audit CSVs."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ACCOUNTING_TERMS = {
	"account",
	"accounting",
	"asset",
	"balance",
	"bank",
	"budget",
	"cash",
	"cost center",
	"credit",
	"currency",
	"customer",
	"debit",
	"depreciation",
	"exchange",
	"expense",
	"fiscal",
	"general ledger",
	"income",
	"invoice",
	"journal",
	"ledger",
	"loss",
	"payable",
	"payment",
	"profit",
	"purchase",
	"receivable",
	"reconciliation",
	"sales",
	"stock",
	"supplier",
	"tax",
	"valuation",
	"write off",
}

CATEGORY_PRIORITY = {
	"glossary-conflict": 100,
	"duplicated-source": 95,
	"untranslated": 90,
	"fuzzy": 85,
	"cross-app-conflict": 80,
	"english-residue": 60,
}

TECHNICAL_TOKENS = {
	"api",
	"bom",
	"csv",
	"duckdb",
	"erpnext",
	"fifo",
	"frappe",
	"hrms",
	"html",
	"iban",
	"jinja",
	"json",
	"pdf",
	"pos",
	"swift",
	"uom",
	"url",
	"xml",
}

HTML_TAG_RE = re.compile(r"<[^>]+>")
JINJA_RE = re.compile(r"{{.*?}}|{%.*?%}|{#.*?#}", re.DOTALL)
URL_RE = re.compile(r"(?:https?://|www\.)\S+|\b\S+@\S+\.\S+\b", re.IGNORECASE)
CODE_RE = re.compile(r"`[^`]+`|\b[A-Za-z][A-Za-z0-9]*[_./:][A-Za-z0-9_.:/-]*\b")
PLACEHOLDER_RE = re.compile(r"%\([^)]+\)[a-zA-Z]|%[a-zA-Z]|{[^{}]+}")
ENGLISH_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")

OUTPUT_FIELDS = ["priority", "category", "app", "msgid", "msgstr", "reason", "source_report"]


def normalized(value: str) -> str:
	return re.sub(r"\s+", " ", value).strip().casefold()


def is_accounting_related(*values: str) -> bool:
	text = " ".join(normalized(value) for value in values if value)
	return any(term in text for term in ACCOUNTING_TERMS)


def visible_text(value: str) -> str:
	"""Remove markup and machine tokens while preserving user-facing words."""
	value = JINJA_RE.sub(" ", value)
	value = HTML_TAG_RE.sub(" ", value)
	value = URL_RE.sub(" ", value)
	value = CODE_RE.sub(" ", value)
	return PLACEHOLDER_RE.sub(" ", value)


def english_words(value: str) -> list[str]:
	"""Return meaningful English residue, excluding approved technical tokens."""
	return [
		word
		for word in ENGLISH_WORD_RE.findall(visible_text(value))
		if word.casefold() not in TECHNICAL_TOKENS
	]


def has_duplicated_source(msgid: str, msgstr: str) -> bool:
	"""Detect an English source sentence appended to an Arabic translation."""
	source_words = [word.casefold() for word in english_words(msgid)]
	translation_words = [word.casefold() for word in english_words(msgstr)]
	if len(source_words) < 2 or sum(len(word) for word in source_words) < 8:
		return False
	window = len(source_words)
	return any(
		translation_words[index : index + window] == source_words
		for index in range(len(translation_words) - window + 1)
	)


def read_csv(path: Path) -> list[dict[str, str]]:
	if not path.is_file():
		return []
	with path.open(encoding="utf-8-sig", newline="") as handle:
		return [{key: value or "" for key, value in row.items()} for row in csv.DictReader(handle)]


def finding(
	category: str,
	row: dict[str, str],
	reason: str,
	source_report: str,
	priority_adjustment: int = 0,
) -> dict[str, object]:
	return {
		"priority": CATEGORY_PRIORITY[category] + priority_adjustment,
		"category": category,
		"app": row.get("app", ""),
		"msgid": row.get("msgid", ""),
		"msgstr": row.get("msgstr", row.get("translations", "")),
		"reason": reason,
		"source_report": source_report,
	}


def build_queue(audit_dir: Path) -> list[dict[str, object]]:
	queue: list[dict[str, object]] = []

	for row in read_csv(audit_dir / "glossary-conflicts.csv"):
		queue.append(
			finding(
				"glossary-conflict",
				row,
				row.get("reason", "glossary conflict"),
				"glossary-conflicts.csv",
			)
		)

	for row in read_csv(audit_dir / "untranslated-and-fuzzy.csv"):
		if not is_accounting_related(row.get("msgid", ""), row.get("msgstr", "")):
			continue
		category = "fuzzy" if normalized(row.get("fuzzy", "")) in {"1", "true", "yes"} else "untranslated"
		queue.append(
			finding(category, row, "accounting string requires review", "untranslated-and-fuzzy.csv")
		)

	for row in read_csv(audit_dir / "cross-app-conflicts.csv"):
		if not is_accounting_related(row.get("msgid", ""), row.get("translations", "")):
			continue
		conflict_row = {**row, "app": row.get("apps", ""), "msgstr": row.get("translations", "")}
		queue.append(
			finding(
				"cross-app-conflict",
				conflict_row,
				"same source has different translations across apps",
				"cross-app-conflicts.csv",
			)
		)

	for row in read_csv(audit_dir / "english-residue.csv"):
		if not is_accounting_related(row.get("msgid", "")):
			continue
		msgid = row.get("msgid", "")
		msgstr = row.get("msgstr", "")
		if has_duplicated_source(msgid, msgstr):
			queue.append(
				finding(
					"duplicated-source",
					row,
					"English source text is duplicated inside the Arabic translation",
					"english-residue.csv",
				)
			)
			continue
		residue = english_words(msgstr)
		if not residue:
			continue
		queue.append(
			finding(
				"english-residue",
				row,
				f"English candidates: {' | '.join(residue)}",
				"english-residue.csv",
			)
		)

	deduplicated: dict[tuple[str, str, str], dict[str, object]] = {}
	for row in queue:
		key = (str(row["category"]), str(row["app"]), str(row["msgid"]))
		current = deduplicated.get(key)
		if current is None or int(row["priority"]) > int(current["priority"]):
			deduplicated[key] = row

	return sorted(
		deduplicated.values(),
		key=lambda row: (-int(row["priority"]), str(row["category"]), str(row["app"]), str(row["msgid"])),
	)


def write_queue(path: Path, rows: list[dict[str, object]]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
		writer.writeheader()
		writer.writerows(rows)


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--audit-dir", type=Path, default=Path("reports/audit"))
	parser.add_argument(
		"--output",
		type=Path,
		default=Path("reports/audit/accounting-priority.csv"),
	)
	parser.add_argument("--print-limit", type=int, default=50)
	args = parser.parse_args()

	queue = build_queue(args.audit_dir)
	write_queue(args.output, queue)
	counts: dict[str, int] = {}
	for row in queue:
		category = str(row["category"])
		counts[category] = counts.get(category, 0) + 1
	print(json.dumps({"total": len(queue), "categories": counts}, ensure_ascii=False, sort_keys=True))
	for row in queue[: max(args.print_limit, 0)]:
		print("ACCOUNTING_REVIEW " + json.dumps(row, ensure_ascii=False, sort_keys=True))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

