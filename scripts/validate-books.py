"""Validate all registered book metadata and paths without modifying manuscripts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from book_metadata import load_books

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Books repository root")
    args = parser.parse_args()
    try:
        books = load_books(args.root.resolve())
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        raise SystemExit(str(error))
    for _, meta in books:
        print(f"{meta['id']}: {len(meta['chapters'])} chapters, {len(meta['parts'])} parts, {len(meta.get('downloads', []))} downloads")
    print(f"Validated {len(books)} book(s); source files unchanged")


if __name__ == "__main__":
    main()
