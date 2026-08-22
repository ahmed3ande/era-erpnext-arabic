"""Deterministic audit reports for Era Arabic PO catalogs and glossary."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from babel.messages.pofile import read_po

BRACE_PLACEHOLDER = re.compile(
	r"(?<!\{)\{(?:\d+|[A-Za-z_][\w.]*)(?:![rsa])?(?::[^{}]+)?\}(?!\})"
)
NAMED_PERCENT_PLACEHOLDER = re.compile(r"%\([^)]+\)[#0 +\-]?(?:\d+|\*)?(?:\.\d+|\.\*)?[a-zA-Z]")
POSITIONAL_PERCENT_PLACEHOLDER = re.compile(
	r"(?<!%)%(?:[#0+\-]?(?:\d+|\*)?(?:\.\d+|\.\*)?)[diouxXeEfFgGcrsa]"
)
ENGLISH_WORD = re.compile(r"\b[A-Za-z]{3,}\b")


@dataclass(frozen=True)
class Entry:
	app: str
	msgid: str
	msgstr: str
	fuzzy: bool
	path: str


def placeholders(value: str) -> set[str]:
	"""Return Python brace and percent placeholders used by a message."""
	return {
		*BRACE_PLACEHOLDER.findall(value),
		*NAMED_PERCENT_PLACEHOLDER.findall(value),
		*POSITIONAL_PERCENT_PLACEHOLDER.findall(value),
	}


def message_text(value: str | tuple[str, ...] | list[str] | None) -> str:
	if isinstance(value, (tuple, list)):
		return " | ".join(part for part in value if part)
	return value or ""


def load_entries(locale_root: Path) -> list[Entry]:
	entries: list[Entry] = []
	for po_path in sorted(locale_root.glob("*/ar.po")):
		app = po_path.parent.name
		with po_path.open(encoding="utf-8") as handle:
			catalog = read_po(handle)
		for message in catalog:
			msgid = message_text(message.id)
			if not msgid:
				continue
			entries.append(
				Entry(
					app=app,
					msgid=msgid,
					msgstr=message_text(message.string),
					fuzzy="fuzzy" in message.flags,
					path=po_path.as_posix(),
				)
			)
	return entries


def load_glossary(path: Path) -> list[dict[str, str]]:
	with path.open(encoding="utf-8-sig", newline="") as handle:
		return [
			{key: (value or "").strip() for key, value in row.items()}
			for row in csv.DictReader(handle)
		]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
		writer.writeheader()
		writer.writerows(rows)


def audit(locale_root: Path, glossary_path: Path, output_dir: Path) -> dict[str, object]:
	entries = load_entries(locale_root)
	glossary = load_glossary(glossary_path)

	coverage: dict[str, dict[str, int]] = defaultdict(
		lambda: {"total": 0, "translated": 0, "untranslated": 0, "fuzzy": 0}
	)
	untranslated: list[dict[str, object]] = []
	placeholder_errors: list[dict[str, object]] = []
	english_residue: list[dict[str, object]] = []

	for entry in entries:
		stats = coverage[entry.app]
		stats["total"] += 1
		if entry.msgstr:
			stats["translated"] += 1
		else:
			stats["untranslated"] += 1
		if entry.fuzzy:
			stats["fuzzy"] += 1
		if not entry.msgstr or entry.fuzzy:
			untranslated.append(asdict(entry))
		if entry.msgstr:
			source_placeholders = placeholders(entry.msgid)
			translation_placeholders = placeholders(entry.msgstr)
			if source_placeholders != translation_placeholders:
				placeholder_errors.append(
					{
						**asdict(entry),
						"source_placeholders": " | ".join(sorted(source_placeholders)),
						"translation_placeholders": " | ".join(sorted(translation_placeholders)),
					}
				)
			words = sorted(set(ENGLISH_WORD.findall(entry.msgstr)))
			if words:
				english_residue.append({**asdict(entry), "english_words": " | ".join(words)})

	by_msgid: dict[str, list[Entry]] = defaultdict(list)
	for entry in entries:
		if entry.msgstr and not entry.fuzzy:
			by_msgid[entry.msgid].append(entry)
	cross_app_conflicts: list[dict[str, object]] = []
	for msgid, matches in sorted(by_msgid.items()):
		translations = sorted({match.msgstr for match in matches})
		apps = sorted({match.app for match in matches})
		if len(translations) > 1 and len(apps) > 1:
			cross_app_conflicts.append(
				{
					"msgid": msgid,
					"apps": " | ".join(apps),
					"translations": " || ".join(translations),
				}
			)

	glossary_by_source = {row.get("source", ""): row for row in glossary if row.get("source")}
	glossary_conflicts: list[dict[str, object]] = []
	for entry in entries:
		term = glossary_by_source.get(entry.msgid)
		if not term or not entry.msgstr:
			continue
		approved = term.get("approved_arabic", "")
		rejected = {item.strip() for item in term.get("rejected", "").split("|") if item.strip()}
		reasons: list[str] = []
		if term.get("status") == "approved" and approved and entry.msgstr != approved:
			reasons.append("does-not-match-approved")
		if entry.msgstr in rejected:
			reasons.append("uses-rejected-term")
		if reasons:
			glossary_conflicts.append(
				{
					**asdict(entry),
					"approved_arabic": approved,
					"rejected": " | ".join(sorted(rejected)),
					"reason": " | ".join(reasons),
				}
			)

	for rows in (untranslated, placeholder_errors, english_residue, glossary_conflicts):
		rows.sort(key=lambda row: (str(row.get("app", "")), str(row.get("msgid", ""))))

	entry_fields = ["app", "msgid", "msgstr", "fuzzy", "path"]
	write_csv(output_dir / "untranslated-and-fuzzy.csv", entry_fields, untranslated)
	write_csv(
		output_dir / "placeholder-errors.csv",
		entry_fields + ["source_placeholders", "translation_placeholders"],
		placeholder_errors,
	)
	write_csv(
		output_dir / "english-residue.csv", entry_fields + ["english_words"], english_residue
	)
	write_csv(
		output_dir / "cross-app-conflicts.csv",
		["msgid", "apps", "translations"],
		cross_app_conflicts,
	)
	write_csv(
		output_dir / "glossary-conflicts.csv",
		entry_fields + ["approved_arabic", "rejected", "reason"],
		glossary_conflicts,
	)

	summary: dict[str, object] = {
		"apps": {app: coverage[app] for app in sorted(coverage)},
		"entries": len(entries),
		"findings": {
			"untranslated_or_fuzzy": len(untranslated),
			"placeholder_errors": len(placeholder_errors),
			"english_residue": len(english_residue),
			"cross_app_conflicts": len(cross_app_conflicts),
			"glossary_conflicts": len(glossary_conflicts),
		},
	}
	output_dir.mkdir(parents=True, exist_ok=True)
	(output_dir / "audit-summary.json").write_text(
		json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
	)
	return summary


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"--locale-root",
		type=Path,
		default=Path("arabic_translations/locale/source"),
	)
	parser.add_argument("--glossary", type=Path, default=Path("glossary/accounting.csv"))
	parser.add_argument("--output-dir", type=Path, default=Path("reports/audit"))
	parser.add_argument("--fail-on-placeholder", action="store_true")
	args = parser.parse_args()

	summary = audit(args.locale_root, args.glossary, args.output_dir)
	print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
	if args.fail_on_placeholder and summary["findings"]["placeholder_errors"]:
		with (args.output_dir / "placeholder-errors.csv").open(encoding="utf-8", newline="") as handle:
			for row in csv.DictReader(handle):
				print(
					"PLACEHOLDER_ERROR "
					+ json.dumps(
						{
							"app": row["app"],
							"msgid": row["msgid"],
							"source_placeholders": row["source_placeholders"],
							"translation_placeholders": row["translation_placeholders"],
						},
						ensure_ascii=False,
						sort_keys=True,
					)
				)
		return 1
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

