"""Create a new book scaffold without replacing an existing book."""
from __future__ import annotations

import argparse
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
tools = runpy.run_path(str(Path(__file__).with_name("sync-book.py")))


def create_book(root: Path, slug: str, title: str) -> None:
    tools["registry"]["check_slug"](slug)
    target = root / "content" / slug
    if target.exists():
        raise ValueError(f"Book directory already exists; no files changed: {target}")
    if not title.strip():
        raise ValueError("Book title cannot be empty")
    meta = tools["empty_metadata"](slug, title)
    meta["chapters"] = [{"number": 1, "title": "시작하기", "href": "01-introduction/chapter", "part": 1}]
    meta["parts"] = [{"number": 1, "title": "첫 번째 파트", "first": 1, "last": 1}]
    meta["provenance"]["review"]["verification"] = "appendices/verification"
    chapter = target / "01-introduction/chapter.md"
    chapter.parent.mkdir(parents=True)
    template = root / "templates/book/chapter.md"
    chapter_body = template.read_text(encoding="utf-8") if template.is_file() else "## 학습 목표\n\n이 장의 목표를 작성하세요.\n"
    chapter.write_text(tools["frontmatter"]("01장. 시작하기", meta["description"], meta, chapter=1, part=1, enableToc=True) + chapter_body, encoding="utf-8")
    (chapter.parent / "index.md").write_text(tools["frontmatter"]("01장. 시작하기", meta["description"], meta, enableToc=False) + "[본문 읽기](./chapter.md)\n\n[책 목차](../index.md)\n", encoding="utf-8")
    verification = target / "appendices/verification.md"
    verification.parent.mkdir()
    verification_template = root / "templates/book/verification.md"
    verification_body = verification_template.read_text(encoding="utf-8") if verification_template.is_file() else "아직 검증하지 않았습니다. 실행한 검사와 결과를 기록하세요.\n"
    verification.write_text(tools["frontmatter"]("검증 범위", "이 책에서 확인한 내용과 확인하지 않은 내용을 기록합니다.", meta, enableToc=True) + verification_body, encoding="utf-8")
    (target / "index.md").write_text(tools["book_home"](meta), encoding="utf-8")
    tools["registry"]["write_json"](target / "book.json", meta)
    tools["registry"]["generate"](root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True, help="Lowercase directory name, for example python-basics")
    parser.add_argument("--title", required=True, help="Display title")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        create_book(args.root.resolve(), args.slug, args.title)
    except (ValueError, KeyError, TypeError) as error:
        raise SystemExit(str(error))
    print(f"Created content/{args.slug}; fill in book.json, chapters and verification before publishing")
