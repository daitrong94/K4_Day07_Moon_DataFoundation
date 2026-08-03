#!/usr/bin/env python3
"""Enforce the corpus metadata schema before the corpus is used for benchmarking.

A schema that is only described in a report is a suggestion. This script turns
data/k4_ecommerce/metadata_schema.json into a gate: it checks every document's
front matter against the declared types, enums and patterns, checks doc_id
uniqueness, and checks that sources.csv matches the .md files one-to-one — the
"Checklist trước benchmark" in docs/DATA_COLLECTION.md, automated.

Exit code 0 = corpus conforms, 1 = at least one violation.

Usage:
    python3 scripts/validate_metadata.py data/k4_ecommerce
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import load_documents  # noqa: E402


def check_field(name: str, spec: dict, metadata: dict) -> list[str]:
    errors: list[str] = []
    value = metadata.get(name)

    if value in (None, ""):
        if spec.get("required"):
            errors.append(f"thiếu trường bắt buộc `{name}`")
        return errors

    text = str(value)
    if spec["type"] == "enum" and text not in spec["values"]:
        errors.append(f"`{name}`={text!r} không thuộc {spec['values']}")
    if spec.get("pattern") and not re.match(spec["pattern"], text):
        errors.append(f"`{name}`={text!r} không khớp mẫu {spec['pattern']}")
    if spec["type"] == "int" and not text.lstrip("-").isdigit():
        errors.append(f"`{name}`={text!r} không phải số nguyên")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path, nargs="?", default=Path("data/k4_ecommerce"))
    args = parser.parse_args()

    schema = json.loads((args.data_dir / "metadata_schema.json").read_text(encoding="utf-8"))
    fields = schema["fields"]
    documents = load_documents(args.data_dir)

    failures = 0
    seen_ids: dict[str, str] = {}
    for doc in sorted(documents, key=lambda d: d.id):
        errors: list[str] = []
        for name, spec in fields.items():
            errors.extend(check_field(name, spec, doc.metadata))
        if doc.id in seen_ids:
            errors.append(f"doc_id trùng với {seen_ids[doc.id]}")
        seen_ids[doc.id] = doc.metadata.get("source", doc.id)

        if errors:
            failures += 1
            print(f"✗ {doc.id}")
            for error in errors:
                print(f"    {error}")
        else:
            print(f"✓ {doc.id}")

    manifest_path = args.data_dir / "sources.csv"
    manifest_ids = {
        row["doc_id"] for row in csv.DictReader(manifest_path.open(encoding="utf-8"))
    }
    document_ids = {doc.id for doc in documents}
    if manifest_ids != document_ids:
        failures += 1
        missing = document_ids - manifest_ids
        extra = manifest_ids - document_ids
        print("✗ sources.csv không khớp 1-1 với tài liệu")
        if missing:
            print(f"    thiếu trong sources.csv: {sorted(missing)}")
        if extra:
            print(f"    thừa trong sources.csv: {sorted(extra)}")
    else:
        print(f"✓ sources.csv khớp 1-1 với {len(document_ids)} tài liệu")

    print(
        f"\n{len(documents)} tài liệu, {len(documents) - failures} hợp lệ, {failures} lỗi."
        if failures
        else f"\n{len(documents)} tài liệu — corpus hợp lệ theo schema {schema['schema_version']}."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
