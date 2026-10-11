"""Validate generated Pages links and every registered book, with no fixed chapter count."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in (("href",) if tag in {"a", "link"} else ("src",) if tag in {"img", "script", "source"} else ()):
            if attrs.get(key):
                self.links.append(attrs[key])


def check_output(output: Path, base_path: str) -> dict:
    output = output.resolve()
    if not output.is_dir():
        raise ValueError(f"Build directory missing: {output}")
    prefix = "/" + base_path.strip("/") + "/" if base_path.strip("/") else "/"
    broken = []

    def resolve(href: str, current: Path) -> Path | None:
        url = urlsplit(href)
        if url.scheme or url.netloc or not url.path:
            return None
        local_path = unquote(url.path)
        if local_path.startswith("/"):
            if prefix != "/":
                if local_path.startswith(prefix):
                    local_path = local_path[len(prefix):]
                elif local_path.rstrip("/") == prefix.rstrip("/"):
                    local_path = "index.html"
                else:
                    raise ValueError("absolute path escapes Pages base path")
            target = output / local_path.lstrip("/")
        else:
            target = current.parent / local_path
        target = target.resolve()
        if not target.is_relative_to(output):
            raise ValueError("relative path escapes build directory")
        options = [target, Path(str(target) + ".html"), target / "index.html"]
        return next((candidate for candidate in options if candidate.is_file()), target)

    html_pages = list(output.rglob("*.html"))
    for path in html_pages:
        parser = Links()
        parser.feed(path.read_text(encoding="utf-8"))
        for href in parser.links:
            try:
                target = resolve(href, path)
                if target is not None and not target.is_file():
                    broken.append({"file": str(path.relative_to(output)), "href": href, "reason": "missing file"})
            except ValueError as error:
                broken.append({"file": str(path.relative_to(output)), "href": href, "reason": str(error)})
    registry_file = output / "static/library-manifest.json"
    if not registry_file.is_file():
        raise ValueError("Missing static/library-manifest.json; run the library indexer before building")
    registry = json.loads(registry_file.read_text(encoding="utf-8"))
    summaries, ids = [], set()
    for book in registry.get("books", []):
        if book["id"] in ids:
            raise ValueError(f"Duplicate book id in registry: {book['id']}")
        ids.add(book["id"])
        manifest_path = resolve(book["manifest"], output / "index.html")
        if manifest_path is None or not manifest_path.is_file():
            raise ValueError(f"Missing manifest for {book['id']}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["id"] != book["id"] or len(manifest["chapters"]) != book["chapterCount"]:
            raise ValueError(f"Registry and book manifest disagree: {book['id']}")
        landing = resolve(book["href"], output / "index.html")
        if landing is None or not landing.is_file():
            raise ValueError(f"Book landing page missing: {book['href']}")
        # A book manifest lives in static/, but chapter/download hrefs are book-relative.
        book_page = output / book["href"] / "index.html"
        for chapter in manifest["chapters"]:
            target = resolve(chapter["href"], book_page)
            if target is None or target.suffix != ".html" or not target.is_file():
                raise ValueError(f"Chapter output missing: {book['id']}/{chapter['href']}")
        for download in manifest.get("downloads", []):
            target = resolve(download["href"], book_page)
            if target is None or not target.is_file():
                raise ValueError(f"Download missing: {book['id']}/{download['href']}")
        verification = manifest.get("provenance", {}).get("review", {}).get("verification")
        if verification:
            target = resolve(verification, book_page)
            if target is None or not target.is_file():
                raise ValueError(f"Verification page missing: {book['id']}/{verification}")
        summaries.append({"id": book["id"], "chapters": len(manifest["chapters"]), "downloads": len(manifest.get("downloads", []))})
    if not summaries:
        raise ValueError("Library registry contains no books")
    return {"books": summaries, "html_pages": len(html_pages), "base_path": prefix, "broken_links": broken}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-path", default="/books/", help="Pages URL path, for example /books/")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        result = check_output(args.output, args.base_path)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise SystemExit(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["broken_links"]:
        raise SystemExit("Generated HTML contains unresolved local links")
