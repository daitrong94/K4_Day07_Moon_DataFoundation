"""Ép data/k4_ecommerce/*.md khớp data/k4_ecommerce/metadata_schema.json.

Kiểm tra: field bắt buộc có đủ, đúng kiểu/pattern/enum, doc_id không trùng,
và sources.csv khớp 1-1 với các file .md — đúng "Checklist trước benchmark"
ở docs/DATA_COLLECTION.md, nhưng tự động hóa thay vì rà tay.

Chạy: python scripts/validate_metadata.py [data_dir]
Thoát code 0 nếu mọi thứ OK, 1 nếu có lỗi (in danh sách lỗi ra stderr).
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

DEFAULT_DATA_DIR = "data/k4_ecommerce"


def parse_front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    closing = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing = i
            break
    if closing is None:
        return {}
    metadata: dict = {}
    for raw in lines[1:closing]:
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.split(" #", 1)[0].strip().strip('"').strip("'")
        metadata[key.strip()] = value
    return metadata


def validate_field(name: str, spec: dict, metadata: dict, errors: list[str], filename: str) -> None:
    if spec.get("required") and name not in metadata:
        errors.append(f"{filename}: thiếu field bắt buộc '{name}'")
        return
    if name not in metadata:
        return
    value = metadata[name]
    if spec["type"] == "enum" and value not in spec["values"]:
        errors.append(f"{filename}: '{name}={value}' không thuộc enum {spec['values']}")
    pattern = spec.get("pattern")
    if pattern and not re.match(pattern, value):
        errors.append(f"{filename}: '{name}={value}' không khớp pattern {pattern}")


def main(argv: list[str]) -> int:
    data_dir = Path(argv[1] if len(argv) > 1 else DEFAULT_DATA_DIR)
    schema_path = data_dir / "metadata_schema.json"
    if not schema_path.exists():
        print(f"Không tìm thấy schema: {schema_path}", file=sys.stderr)
        return 1
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    fields = schema["fields"]

    md_files = sorted(data_dir.glob("*.md"))
    errors: list[str] = []
    seen_doc_ids: dict[str, str] = {}

    for path in md_files:
        metadata = parse_front_matter(path.read_text(encoding="utf-8"))
        for name, spec in fields.items():
            if spec.get("added_by"):
                continue  # gắn tự động lúc ingest, không bắt buộc có trong front matter
            validate_field(name, spec, metadata, errors, path.name)

        doc_id = metadata.get("doc_id")
        if doc_id:
            if fields["doc_id"].get("unique") and doc_id in seen_doc_ids:
                errors.append(f"{path.name}: doc_id '{doc_id}' trùng với {seen_doc_ids[doc_id]}")
            seen_doc_ids[doc_id] = path.name
            if doc_id != path.stem:
                errors.append(
                    f"{path.name}: doc_id '{doc_id}' không trùng tên file '{path.stem}' (khuyến nghị, không bắt buộc)"
                )

    sources_path = data_dir / "sources.csv"
    if sources_path.exists():
        rows = list(csv.DictReader(sources_path.open(encoding="utf-8")))
        csv_ids = sorted(r["doc_id"] for r in rows)
        md_ids = sorted(seen_doc_ids.keys())
        if csv_ids != md_ids:
            errors.append(f"sources.csv lệch với doc_id trong .md: csv={csv_ids} md={md_ids}")
    else:
        errors.append(f"Không tìm thấy {sources_path}")

    if not (5 <= len(md_files) <= 10):
        errors.append(f"Số tài liệu = {len(md_files)}, cần 5-10 theo docs/DATA_COLLECTION.md")

    print(f"Kiểm tra {len(md_files)} tài liệu trong {data_dir} theo {schema_path.name}")
    if errors:
        print(f"\n{len(errors)} lỗi:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("OK — tất cả tài liệu khớp schema, sources.csv khớp 1-1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
