"""Build registries from book.json; never rewrite Markdown manuscripts."""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
TITLE = "AI Generation Library"


def check_slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError("Book id must use lowercase ASCII letters, numbers and hyphens")
    return value


def local_href(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or "?" in value or "#" in value:
        raise ValueError(f"Invalid book-relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Path must stay inside its book: {value!r}")
    return value


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != encoded:
        path.write_text(encoded, encoding="utf-8")


def validate_book(book: Path) -> dict:
    meta = json.loads((book / "book.json").read_text(encoding="utf-8-sig"))
    if check_slug(meta.get("id", "")) != book.name:
        raise ValueError(f"{book}: book.json id must equal the directory name")
    for field in ("title", "description", "status"):
        if not isinstance(meta.get(field), str) or not meta[field].strip():
            raise ValueError(f"{book}: {field} must be a nonempty string")
    if not isinstance(meta.get("tags"), list) or not all(isinstance(tag, str) for tag in meta["tags"]):
        raise ValueError(f"{book}: tags must be an array of strings")
    if not isinstance(meta.get("provenance"), dict):
        raise ValueError(f"{book}: provenance must record generation and review information")
    if not (book / "index.md").is_file():
        raise ValueError(f"{book}: index.md is required")
    chapters = meta.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise ValueError(f"{book}: chapters must contain at least one chapter")
    numbers, hrefs = set(), set()
    for chapter in chapters:
        number = chapter.get("number")
        if isinstance(number, bool) or not isinstance(number, int) or number < 1 or number in numbers:
            raise ValueError(f"{book}: chapter numbers must be unique positive integers")
        if not isinstance(chapter.get("title"), str) or not chapter["title"].strip():
            raise ValueError(f"{book}: chapter {number} needs a title")
        href = local_href(chapter.get("href"))
        if href.endswith(".md") or href in hrefs or not (book / (href + ".md")).is_file():
            raise ValueError(f"{book}: chapter {number} needs a unique existing Markdown href without .md")
        if not isinstance(chapter.get("part"), int) or chapter["part"] < 1:
            raise ValueError(f"{book}: chapter {number} needs a positive part number")
        numbers.add(number)
        hrefs.add(href)
    if [chapter["number"] for chapter in chapters] != list(range(1, len(chapters) + 1)):
        raise ValueError(f"{book}: chapters must be ordered consecutively from 1 to their total count")
    parts = meta.get("parts", [])
    if not isinstance(parts, list) or not parts:
        raise ValueError(f"{book}: parts must contain at least one part")
    part_numbers = set()
    for part in parts:
        number = part.get("number")
        first, last = part.get("first"), part.get("last")
        if not isinstance(number, int) or number < 1 or number in part_numbers:
            raise ValueError(f"{book}: part numbers must be unique positive integers")
        if not isinstance(first, int) or not isinstance(last, int) or first > last or first not in numbers or last not in numbers:
            raise ValueError(f"{book}: part {number} has an invalid chapter range")
        if not isinstance(part.get("title"), str) or not part["title"].strip():
            raise ValueError(f"{book}: part {number} needs a title")
        part_numbers.add(number)
    for chapter in chapters:
        matches = [part for part in parts if part["number"] == chapter["part"] and part["first"] <= chapter["number"] <= part["last"]]
        if len(matches) != 1:
            raise ValueError(f"{book}: chapter {chapter['number']} is not in its declared part")
    for download in meta.get("downloads", []):
        href = local_href(download.get("href"))
        if not (book / href).is_file():
            raise ValueError(f"{book}: download is missing: {href}")
    review = meta["provenance"].get("review", {})
    if review.get("verification"):
        href = local_href(review["verification"])
        if not (book / (href + ".md")).is_file():
            raise ValueError(f"{book}: verification Markdown is missing: {href}")
    return meta


def library_card(meta: dict, position: int) -> str:
    escape = html.escape
    slug, title = escape(meta["id"], quote=True), escape(meta["title"])
    description = escape(meta["description"])
    chapters, parts = len(meta["chapters"]), len(meta["parts"])
    href = f"{slug}/"
    tags = "".join(f"<span>{escape(tag)}</span>" for tag in meta["tags"])
    first = escape(meta["chapters"][0]["href"], quote=True)
    verification = meta["provenance"].get("review", {}).get("verification")
    review_link = f'<a class="library-validation-link" href="{href}{escape(verification, quote=True)}">출처·검증 범위 보기 <span aria-hidden="true">↗</span></a>' if verification else ''
    topic_summary = f" · {meta['topicCount']}개 주제" if meta.get("topicCount") else ""
    practice = f'<div><dt>실습</dt><dd>{escape(meta["practiceSummary"])}</dd></div>' if meta.get("practiceSummary") else ''
    return f'''<article class="library-book" data-library-book="{slug}" aria-labelledby="{slug}-title">
<a class="library-cover-link" href="{href}" aria-hidden="true" tabindex="-1"><div class="library-cover"><div class="library-cover-top"><span>AI GENERATION<br>LIBRARY</span><span>{position:02d}</span></div><div class="library-cover-title">{title}</div><div class="library-cover-symbol" aria-hidden="true"><span class="library-cover-code">&lt;/&gt;</span><span class="library-cover-orbit"></span></div><div class="library-cover-bottom"><span>{parts:02d} PARTS · {chapters:02d} CHAPTERS</span><span>OPEN SOURCE</span></div></div></a>
<div class="library-book-content"><div class="library-book-tags">{tags}<span>AI 생성</span></div><h3 id="{slug}-title"><a href="{href}">{title}</a></h3><p class="library-book-description">{description}</p><dl class="library-book-facts"><div><dt>구성</dt><dd>{parts}부 · {chapters}장{topic_summary}</dd></div>{practice}</dl><div class="library-book-progress"><span class="library-progress-dot" aria-hidden="true"></span><span data-library-progress="{slug}">0 / {chapters}장 완료</span><span class="library-progress-note">진도는 이 브라우저에 저장됩니다.</span></div><div class="library-book-actions"><a class="library-button library-button-primary" href="{href}">책 펼치기 <span aria-hidden="true">↗</span></a><a class="library-text-link" href="{href}{first}">첫 장 바로 읽기 →</a></div>{review_link}</div>
</article>'''


def update_home(content: Path, books: list[dict]) -> None:
    home = content / "index.md"
    if not home.is_file():
        return
    text = home.read_text(encoding="utf-8")
    start, end = "<!-- library-books:start -->", "<!-- library-books:end -->"
    if start not in text or end not in text:
        return
    cards = "\n\n".join(library_card(meta, position) for position, meta in enumerate(books, 1))
    updated = re.sub(re.escape(start) + r".*?" + re.escape(end), start + "\n" + cards + "\n" + end, text, count=1, flags=re.S)
    updated = re.sub(r'(<[^>]+class="library-count"[^>]*>)[^<]*(</[^>]+>)', lambda match: match[1] + f"{len(books):02d} BOOK{'S' if len(books) != 1 else ''}" + match[2], updated)
    for attribute, total in (("data-library-total-books", len(books)), ("data-library-total-chapters", sum(len(meta["chapters"]) for meta in books))):
        updated = re.sub(r'(<strong\s+' + attribute + r'(?:="[^"]*")?\s*>)[^<]*(</strong>)', lambda match: match[1] + f"{total:02d}" + match[2], updated)
    if updated != text:
        home.write_text(updated, encoding="utf-8")


def generate(root: Path = ROOT) -> dict:
    content = root / "content"
    books = [(path.parent, validate_book(path.parent)) for path in sorted(content.glob("*/book.json"))]
    if not books:
        raise ValueError("No books registered: add content/<id>/book.json")
    registry = {"title": TITLE, "books": []}
    # Validate every book before updating any generated registry or card.
    for book, meta in books:
        manifest = {key: meta[key] for key in ("id", "title", "description", "status", "tags", "provenance", "chapters", "parts")}
        manifest["downloads"] = meta.get("downloads", [])
        write_json(book / "static/book-manifest.json", manifest)
        registry["books"].append({
            "id": meta["id"], "title": meta["title"], "description": meta["description"],
            "href": f"{meta['id']}/", "manifest": f"{meta['id']}/static/book-manifest.json",
            "chapterCount": len(meta["chapters"]), "partCount": len(meta["parts"]),
            "status": meta["status"], "tags": meta["tags"], "provenance": meta["provenance"],
        })
    write_json(content / "static/library-manifest.json", registry)
    update_home(content, [meta for _, meta in books])
    return registry


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        registry = generate(args.root.resolve())
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise SystemExit(str(error))
    print(f"Indexed {len(registry['books'])} book(s); chapter manuscripts unchanged")
