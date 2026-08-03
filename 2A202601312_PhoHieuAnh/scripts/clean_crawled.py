#!/usr/bin/env python3
"""Strip site chrome (menus, headers, footers) from crawled Markdown documents.

docs/DATA_COLLECTION.md requires removing repeated menus, ads and footers before
a page is used as corpus. Rather than maintaining a per-site blacklist, this
script exploits a structural fact: every page of one website shares the same
navigation block at the top and the same footer block at the bottom. Grouping
the crawled files by host and removing their longest common prefix / suffix of
lines therefore removes exactly the chrome and nothing else.

Single-page hosts fall back to a small regex blacklist.

Usage:
    python3 scripts/clean_crawled.py data/k4_ecommerce
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
SOURCE_URL = re.compile(r"^source_url:\s*\"?([^\"\n]+)\"?", re.MULTILINE)

# Per-page widgets that survive the common prefix/suffix pass because they vary
# slightly between pages (login prompts, "ask a question" boxes, social footers).
BOILERPLATE = re.compile(
    r"^(skip to content|trang chủ|đăng nhập|đăng ký|giỏ hàng|tìm kiếm|menu|/"
    r"|liên hệ|về chúng tôi|copyright|©.*|facebook|youtube|tiktok|zalo"
    r"|smember|vui lòng đăng nhập.*|gửi câu hỏi|nội dung chính|xem nhanh"
    r"|thông tin có thể thay đổi.*|mở cửa .*|cửa hàngtra cứu đơn hàng"
    r"|website:\s*https?://.*|fanpage.*|youtube channel.*|instagram.*"
    r"|trang tin tức.*|hotline.*)\s*$",
    re.IGNORECASE,
)
TITLE_LINE = re.compile(r"^title:\s*\"?(.*?)\"?\s*$", re.MULTILINE)


def normalize(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip().lower().rstrip(" .-|")


def split_document(text: str) -> tuple[str, str]:
    match = FRONT_MATTER.match(text)
    if not match:
        raise ValueError("missing front matter")
    return match.group(1), match.group(2)


def common_prefix_length(line_lists: list[list[str]]) -> int:
    shortest = min(len(lines) for lines in line_lists)
    for index in range(shortest):
        if len({lines[index].strip() for lines in line_lists}) > 1:
            return index
    return shortest


def common_suffix_length(line_lists: list[list[str]]) -> int:
    reversed_lists = [list(reversed(lines)) for lines in line_lists]
    return common_prefix_length(reversed_lists)


def tidy(lines: list[str], title: str) -> str:
    """Drop boilerplate widgets and every echo of the page title after the H1."""
    wanted_title = normalize(title)
    kept: list[str] = []
    seen_heading = False
    for line in lines:
        stripped = line.strip()
        if BOILERPLATE.match(stripped):
            continue
        if stripped.startswith("# "):
            seen_heading = True
        elif seen_heading and normalize(stripped) in {wanted_title, normalize(title.split(" - ")[0])}:
            continue  # the site repeats its own title in breadcrumbs and banners
        if stripped and kept and normalize(stripped) == normalize(kept[-1]):
            continue  # banner text duplicated back-to-back by the page template
        kept.append(line)
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path)
    args = parser.parse_args()

    documents: dict[Path, tuple[str, list[str]]] = {}
    hosts: dict[str, list[Path]] = {}
    for path in sorted(args.data_dir.glob("*.md")):
        try:
            front_matter, body = split_document(path.read_text(encoding="utf-8"))
        except ValueError as error:
            print(f"Skipping {path}: {error}", file=sys.stderr)
            continue
        documents[path] = (front_matter, body.splitlines())
        url_match = SOURCE_URL.search(front_matter)
        host = urlparse(url_match.group(1)).netloc if url_match else "unknown"
        hosts.setdefault(host, []).append(path)

    if not documents:
        print(f"No Markdown documents found in {args.data_dir}", file=sys.stderr)
        return 2

    for host, paths in sorted(hosts.items()):
        line_lists = [documents[path][1] for path in paths]
        if len(paths) > 1:
            head = common_prefix_length(line_lists)
            tail = common_suffix_length(line_lists)
        else:
            head = tail = 0
        for path in paths:
            front_matter, lines = documents[path]
            body_lines = lines[head : len(lines) - tail] if tail else lines[head:]
            before = len("\n".join(lines))
            title_match = TITLE_LINE.search(front_matter)
            cleaned = tidy(body_lines, title_match.group(1) if title_match else "")
            path.write_text(f"---\n{front_matter}\n---\n\n{cleaned}", encoding="utf-8")
            print(
                f"{path.name:<38} {host:<22} chrome_lines={head + tail:>3} "
                f"{before:>6} -> {len(cleaned):>6} bytes"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
