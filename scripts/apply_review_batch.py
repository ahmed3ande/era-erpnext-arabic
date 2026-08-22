"""Safely apply an approved translation-review CSV to source and shipped catalogs."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from babel.messages.pofile import read_po

sys.path.insert(0, str(Path(__file__).parent))
from audit_translations import placeholders

APPS = ("frappe", "erpnext", "hrms")
APP_ORDER = {app: index for index, app in enumerate(APPS)}
FIELDS = ("batch_id", "app", "msgid", "current_arabic", "approved_arabic", "rationale")


class BatchError(ValueError):
	"""Raised when a review batch cannot be applied safely."""


def read_batch(path: Path) -> list[dict[str, str]]:
	with path.open(encoding="utf-8-sig", newline="") as handle:
		reader = csv.DictReader(handle)
		if tuple(reader.fieldnames or ()) != FIELDS:
			raise BatchError(f"{path}: expected columns {FIELDS}")
		rows = [{key: value or "" for key, value in row.items()} for row in reader]

	seen: set[tuple[str, str]] = set()
	for number, row in enumerate(rows, 2):
		key = (row["app"], row["msgid"])
		if row["app"] not in APPS:
			raise BatchError(f"{path}:{number}: unsupported app {row['app']!r}")
		if not row["msgid"] or not row["approved_arabic"] or not row["rationale"]:
			raise BatchError(f"{path}:{number}: msgid, approved_arabic, and rationale are required")
		if key in seen:
			raise BatchError(f"{path}:{number}: duplicate app/msgid {key!r}")
		seen.add(key)
		if placeholders(row["msgid"]) != placeholders(row["approved_arabic"]):
			raise BatchError(f"{path}:{number}: placeholder mismatch for {row['msgid']!r}")
	return rows


def po_paths(root: Path, app: str) -> list[Path]:
	paths = [
		root / "arabic_translations/locale/source" / app / "ar.po",
		root / "arabic_translations/locale/other-apps/v16" / app / app / "locale/ar.po",
	]
	if app == "frappe":
		paths.append(root / "arabic_translations/locale/other-apps/v15/frappe/frappe/locale/ar.po")
	return paths


def csv_path(root: Path, app: str) -> Path:
	return root / "arabic_translations/locale/other-apps/v15" / app / app / "translations/ar.csv"


def block_msgid(block: str) -> str | None:
	lines = block.splitlines()
	for index, line in enumerate(lines):
		if not line.startswith("msgid "):
			continue
		parts = [line.removeprefix("msgid ").strip()]
		for continuation in lines[index + 1 :]:
			if not continuation.startswith('"'):
				break
			parts.append(continuation.strip())
		try:
			return "".join(ast.literal_eval(part) for part in parts)
		except (SyntaxError, ValueError) as error:
			raise BatchError(f"invalid PO msgid block: {block[:120]!r}") from error
	return None


def render_translation(block: str, approved: str) -> str:
	lines = block.splitlines()
	for index, line in enumerate(lines):
		if line.startswith("#,"):
			flags = [flag.strip() for flag in line[2:].split(",") if flag.strip() != "fuzzy"]
			if flags:
				lines[index] = "#, " + ", ".join(flags)
			else:
				lines.pop(index)
			break
	for index, line in enumerate(lines):
		if not line.startswith("msgstr "):
			continue
		end = index + 1
		while end < len(lines) and lines[end].startswith('"'):
			end += 1
		lines[index:end] = ["msgstr " + json.dumps(approved, ensure_ascii=False)]
		return "\n".join(lines)
	raise BatchError(f"PO entry has no singular msgstr: {block[:120]!r}")


def rewrite_po_entries(
	path: Path,
	rows: list[dict[str, str]],
	*,
	allow_missing: bool,
	append_missing: bool = False,
) -> None:
	text = path.read_text(encoding="utf-8")
	separator = "\r\n\r\n" if "\r\n" in text else "\n\n"
	blocks = text.split(separator)
	by_msgid = {block_msgid(block): index for index, block in enumerate(blocks)}
	for row in rows:
		index = by_msgid.get(row["msgid"])
		if index is None:
			if append_missing:
				blocks.append(
					f"#. source: {row['app']}\n"
					f"msgid {json.dumps(row['msgid'], ensure_ascii=False)}\n"
					f"msgstr {json.dumps(row['approved_arabic'], ensure_ascii=False)}"
				)
			elif not allow_missing:
				raise BatchError(f"{path}: missing msgid {row['msgid']!r}")
			continue
		blocks[index] = render_translation(blocks[index], row["approved_arabic"])
	path.write_text(separator.join(blocks), encoding="utf-8", newline="")


def apply_po(
	path: Path,
	rows: list[dict[str, str]],
	*,
	write: bool,
	guard_current: bool,
	require_all: bool = True,
	append_missing: bool = False,
) -> int:
	if not path.is_file():
		raise BatchError(f"required catalog is missing: {path}")
	with path.open(encoding="utf-8") as handle:
		catalog = read_po(handle)
	messages = {
		(message.id if isinstance(message.id, str) else message.id[0]): message
		for message in catalog
		if message.id
	}
	changed = 0
	for row in rows:
		message = messages.get(row["msgid"])
		if message is None:
			if append_missing:
				if not write:
					raise BatchError(f"{path}: batch is not applied for {row['msgid']!r}")
				changed += 1
				continue
			if require_all:
				raise BatchError(f"{path}: missing msgid {row['msgid']!r}")
			continue  # Older generated version bundles may not contain a newer source key.
		current = message.string if isinstance(message.string, str) else ""
		if guard_current and current not in {row["current_arabic"], row["approved_arabic"]}:
			raise BatchError(
				f"{path}: stale current_arabic guard for {row['msgid']!r}; found {current!r}"
			)
		if current != row["approved_arabic"] or "fuzzy" in message.flags:
			if not write:
				raise BatchError(f"{path}: batch is not applied for {row['msgid']!r}")
			message.string = row["approved_arabic"]
			message.flags.discard("fuzzy")
			changed += 1
	if write and changed:
		rewrite_po_entries(
			path,
			rows,
			allow_missing=not require_all,
			append_missing=append_missing,
		)
	return changed


def apply_csv(path: Path, rows: list[dict[str, str]], *, write: bool) -> int:
	if not path.is_file():
		raise BatchError(f"required catalog is missing: {path}")
	with path.open(encoding="utf-8", newline="") as handle:
		catalog_rows = list(csv.reader(handle))
	by_msgid = {row[0]: row for row in catalog_rows if len(row) >= 2}
	changed = 0
	for row in rows:
		entry = by_msgid.get(row["msgid"])
		if entry is None:
			continue  # A v16 message may legitimately be absent from the v15 bundle.
		if entry[1] != row["approved_arabic"]:
			if not write:
				raise BatchError(f"{path}: batch is not applied for {row['msgid']!r}")
			entry[1] = row["approved_arabic"]
			changed += 1
	if write and changed:
		with path.open("w", encoding="utf-8", newline="") as handle:
			csv.writer(handle).writerows(catalog_rows)
	return changed


def apply_overlay(root: Path, rows: list[dict[str, str]], *, write: bool) -> int:
	# The overlay uses the last installed app's translation for duplicate source keys.
	effective: dict[str, dict[str, str]] = {}
	for row in sorted(rows, key=lambda item: APP_ORDER[item["app"]]):
		effective[row["msgid"]] = row
	path = root / "arabic_translations/locale/ar.po"
	with path.open(encoding="utf-8") as handle:
		catalog = read_po(handle)
	messages = {
		(message.id if isinstance(message.id, str) else message.id[0]): message
		for message in catalog
		if message.id
	}
	changed = 0
	for row in effective.values():
		message = messages.get(row["msgid"])
		if message is None:
			if not write:
				raise BatchError(f"{path}: batch is not applied for {row['msgid']!r}")
			catalog.add(row["msgid"], row["approved_arabic"], auto_comments=[f"source: {row['app']}"])
			changed += 1
		elif message.string != row["approved_arabic"] or "fuzzy" in message.flags:
			if not write:
				raise BatchError(f"{path}: batch is not applied for {row['msgid']!r}")
			message.string = row["approved_arabic"]
			message.flags.discard("fuzzy")
			changed += 1
	if write and changed:
		rewrite_po_entries(
			path,
			list(effective.values()),
			allow_missing=False,
			append_missing=True,
		)
	return changed


def apply_batch(root: Path, batch_path: Path, *, write: bool) -> dict[str, int]:
	rows = read_batch(batch_path)
	by_app: dict[str, list[dict[str, str]]] = defaultdict(list)
	for row in rows:
		by_app[row["app"]].append(row)

	counts: dict[str, int] = {}
	for app, app_rows in sorted(by_app.items()):
		for path in po_paths(root, app):
			is_source = "locale/source" in path.as_posix()
			is_v16 = "/v16/" in path.as_posix()
			counts[path.relative_to(root).as_posix()] = apply_po(
				path,
				app_rows,
				write=write,
				guard_current=is_source,
				require_all=is_source,
				append_missing=is_v16,
			)
		path = csv_path(root, app)
		counts[path.relative_to(root).as_posix()] = apply_csv(path, app_rows, write=write)
	counts["arabic_translations/locale/ar.po"] = apply_overlay(root, rows, write=write)
	return counts


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("batch", type=Path)
	parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
	parser.add_argument("--write", action="store_true", help="apply changes; default is check-only")
	args = parser.parse_args()
	counts = apply_batch(args.root.resolve(), args.batch.resolve(), write=args.write)
	action = "updated" if args.write else "verified"
	print(f"{action} {len(counts)} catalog outputs")
	for path, count in counts.items():
		print(f"  {path}: {count} change(s)")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
