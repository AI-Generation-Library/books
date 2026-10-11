"""Explicitly import a manuscript into one library book; never run during builds."""
from __future__ import annotations

import argparse
from datetime import date
import html
import json
from pathlib import Path
import re
import runpy
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
registry = runpy.run_path(str(Path(__file__).with_name("index-library.py")))
EXCLUDED = {".git", "node_modules", "__pycache__", ".pytest_cache", ".venv", ".openai", "dist"}


def frontmatter(title: str, description: str, meta: dict, **extra) -> str:
    values = {"title": title, "description": description, "tags": meta.get("tags", []),
              "created": meta["provenance"].get("created", date.today().isoformat()),
              "modified": date.today().isoformat(), **extra}
    return "---\n" + "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in values.items()) + "\n---\n\n"


def without_frontmatter(text: str) -> str:
    return re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", text, count=1, flags=re.S).lstrip()


def empty_metadata(slug: str, title: str) -> dict:
    return {"id": slug, "title": title, "description": "AI로 생성하고 검토하며 발전시키는 책입니다.",
            "status": "draft", "tags": [],
            "provenance": {"generator": "AI assistant", "model": None,
                           "created": date.today().isoformat(), "updated": date.today().isoformat(),
                           "source": "생성 출처와 사용한 목차를 작성하세요.",
                           "review": {"status": "unreviewed", "scope": [], "verification": None}},
            "chapters": [], "parts": [], "downloads": []}


def book_home(meta: dict) -> str:
    chapters = sorted(meta["chapters"], key=lambda item: item["number"])
    first = html.escape(chapters[0]["href"], quote=True)
    body = frontmatter(meta["title"], meta["description"], meta, enableToc=False, bookHome=True)
    body += f'<section class="book-hero"><p class="book-eyebrow">AI GENERATION LIBRARY</p><h1>{html.escape(meta["title"])}</h1><p class="book-lead">{html.escape(meta["description"])}</p><div class="book-actions"><a class="book-button book-button-primary" href="{first}">첫 장부터 읽기 →</a><a class="book-button book-button-secondary" href="../">서재로 이동</a></div></section>\n\n'
    body += f'<section class="book-progress-panel" aria-label="학습 진도"><div><strong data-book-progress-count>0 / {len(chapters)}장 완료</strong><p>진도는 이 브라우저에 저장됩니다.</p></div><progress data-book-progress max="{len(chapters)}" value="0" aria-label="완료한 챕터 수"></progress><a class="book-button book-button-secondary" data-book-resume href="{first}">이어서 읽기 →</a></section>\n\n'
    body += '<section class="book-parts" aria-label="전체 학습 목차">\n'
    for part in meta["parts"]:
        body += f'<section class="book-part"><header><span class="book-eyebrow">PART {part["number"]:02d}</span><h2>{html.escape(part["title"])}</h2></header><div class="book-chapters">\n'
        for chapter in chapters:
            if chapter["part"] != part["number"]:
                continue
            number = chapter["number"]
            body += f'<a class="book-chapter" data-book-chapter="{number}" href="{html.escape(chapter["href"], quote=True)}"><span class="chapter-number">{number:02d}</span><span class="chapter-name">{html.escape(chapter["title"])}</span><span class="chapter-status" data-book-completed="{number}">읽기 전</span><span class="chapter-arrow" aria-hidden="true">↗</span></a>\n'
        body += '</div></section>\n'
    body += '</section>\n\n## 출처와 검증\n\n'
    body += f'{meta["provenance"].get("source", "생성 출처 미기록")}\n\n'
    body += f"- 생성 도구: {meta['provenance'].get('generator', '미기록')}\n- 상세 모델: {meta['provenance'].get('model') or '미기록'}\n- 생성일: {meta['provenance'].get('created', '미기록')}\n- 갱신일: {meta['provenance'].get('updated', '미기록')}\n\n"
    verification = meta["provenance"].get("review", {}).get("verification")
    if verification:
        body += f'[검증 범위 확인]({verification}.md)\n\n'
    for download in meta.get("downloads", []):
        body += f'- [{download.get("title", "다운로드")}]({download["href"]})\n'
    return body


def import_book(source: Path, root: Path, slug: str, title: str | None = None) -> dict:
    registry["check_slug"](slug)
    source = source.resolve()
    target = (root / "content" / slug).resolve()
    if not source.is_dir():
        raise ValueError(f"Manuscript directory not found: {source}")
    if source == target or source in target.parents or target in source.parents:
        raise ValueError("Source and target directories must be separate; edit content directly without importing")
    metadata_path = source / "book.json"
    if not metadata_path.is_file():
        metadata_path = target / "book.json"
    meta = json.loads(metadata_path.read_text(encoding="utf-8-sig")) if metadata_path.is_file() else empty_metadata(slug, title or slug)
    meta["id"] = slug
    if title:
        meta["title"] = title
    if not meta.get("chapters"):
        manifest = source / "static/book-manifest.json"
        if manifest.is_file():
            source_manifest = json.loads(manifest.read_text(encoding="utf-8-sig"))
            meta["chapters"] = source_manifest["chapters"]
            meta["parts"] = source_manifest.get("parts", [])
        else:
            toc_path = source / "README.md"
            toc = toc_path.read_text(encoding="utf-8-sig") if toc_path.is_file() else ""
            entries = re.findall(r"^\s*(\d+)\. \[(.*?)\]\(([^)]+\.md)\)\s*$", toc, re.M)
            if not entries:
                for number, path in enumerate(sorted(source.glob("*/chapter.md")), 1):
                    text = without_frontmatter(path.read_text(encoding="utf-8-sig"))
                    heading = re.search(r"^# (.+)$", text, re.M)
                    entries.append((str(number), heading.group(1) if heading else path.parent.name, path.relative_to(source).as_posix()))
            meta["chapters"] = [{"number": int(number), "title": heading, "href": href.removesuffix(".md"), "part": 1} for number, heading, href in entries]
    if not meta["chapters"]:
        raise ValueError("No chapters found; provide book.json or numbered Markdown chapter links in README.md")
    if not meta.get("parts"):
        numbers = [chapter["number"] for chapter in meta["chapters"]]
        meta["parts"] = [{"number": 1, "title": "전체 목차", "first": min(numbers), "last": max(numbers)}]
        for chapter in meta["chapters"]:
            chapter["part"] = 1
    if [chapter["number"] for chapter in meta["chapters"]] != list(range(1, len(meta["chapters"]) + 1)):
        raise ValueError("Source chapters must be ordered consecutively from 1 to their total count")
    if len({chapter["href"] for chapter in meta["chapters"]}) != len(meta["chapters"]):
        raise ValueError("Source chapter hrefs must be unique")
    for chapter in meta["chapters"]:
        if len([part for part in meta["parts"] if part["number"] == chapter["part"] and part["first"] <= chapter["number"] <= part["last"]]) != 1:
            raise ValueError(f"Source chapter {chapter['number']} is not in its declared part")
    for chapter in meta["chapters"]:
        href = registry["local_href"](chapter["href"])
        if not (source / (href + ".md")).is_file():
            raise ValueError(f"Missing source chapter: {href}.md")
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(*EXCLUDED, "*.pyc", "*.db", "*.sqlite3"))
    for chapter in meta["chapters"]:
        path = target / (chapter["href"] + ".md")
        body = without_frontmatter((source / (chapter["href"] + ".md")).read_text(encoding="utf-8-sig"))
        body = re.sub(r"\A# [^\n]*\n+", "", body, count=1).replace("../README.md", "../index.md")
        description = meta["description"]
        path.write_text(frontmatter(f"{chapter['number']:02d}장. {chapter['title']}", description, meta,
                                   chapter=chapter["number"], part=chapter["part"], enableToc=True) + body, encoding="utf-8")
        landing = frontmatter(f"{chapter['number']:02d}장. {chapter['title']}", description, meta, enableToc=False)
        landing += f"[이 장 본문 읽기](./{path.stem}.md)\n\n[책 목차](../index.md)\n"
        if path.parent != target:
            (path.parent / "index.md").write_text(landing, encoding="utf-8")
    meta["provenance"]["updated"] = date.today().isoformat()
    downloads = target / "downloads"
    downloads.mkdir(exist_ok=True)
    archive_href = f"downloads/{slug}-book.zip"
    with zipfile.ZipFile(target / archive_href, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file() and not EXCLUDED.intersection(path.relative_to(source).parts) and path.suffix not in {".pyc", ".db", ".sqlite3", ".zip"}:
                archive.write(path, Path(slug) / path.relative_to(source))
    meta["downloads"] = [download for download in meta.get("downloads", []) if download.get("type") != "manuscript"]
    meta["downloads"].insert(0, {"title": "원고 ZIP", "href": archive_href, "type": "manuscript"})
    (target / "index.md").write_text(book_home(meta), encoding="utf-8")
    registry["write_json"](target / "book.json", meta)
    registry["generate"](root)
    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="External manuscript directory")
    parser.add_argument("--slug", required=True, help="Owned content/<slug> directory")
    parser.add_argument("--title", help="Book title, if not provided by book.json")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        meta = import_book(args.source, args.root.resolve(), args.slug, args.title)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise SystemExit(str(error))
    print(f"Imported {len(meta['chapters'])} chapters into content/{args.slug}; source and other books unchanged")
