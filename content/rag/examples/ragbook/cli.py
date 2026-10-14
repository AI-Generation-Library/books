import argparse
from dataclasses import asdict
import json
from pathlib import Path
from .data import Document, Principal
from .embedding import CharacterEmbedder, FastEmbedder
from .store import Store
from .engine import Engine
from .generation import ExtractiveGenerator, OllamaGenerator
from .metrics import evaluate


def make_engine(
    db, embedding="character", cache="model-cache", model=None, rerank=False
):
    embedder = (
        CharacterEmbedder()
        if embedding == "character"
        else FastEmbedder(cache_dir=cache)
    )
    generator = OllamaGenerator(model) if model else ExtractiveGenerator()
    if rerank:
        from .rerank import FastCrossEncoder

        reranker = FastCrossEncoder(cache_dir=cache + "-rerank")
    else:
        reranker = None
    return Engine(Store(db, embedder.signature), embedder, generator, reranker)


def main():
    parser = argparse.ArgumentParser(
        description="RAG book: inspectable retrieval and citation pipeline"
    )
    parser.add_argument("--db", default="var/index-demo.sqlite3")
    parser.add_argument(
        "--embedding", choices=["character", "neural"], default="character"
    )
    parser.add_argument("--cache", default="model-cache")
    parser.add_argument(
        "--model", help="Existing local Ollama model; omitted means extractive demo"
    )
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="Download and enable the optional multilingual reranker",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    index = sub.add_parser("index")
    index.add_argument("--documents", default="data/documents.json")
    query = sub.add_parser("query")
    query.add_argument("question")
    query.add_argument("--mode", choices=["bm25", "dense", "hybrid"], default="hybrid")
    query.add_argument("--role", choices=["reader", "admin"], default="reader")
    evaluation = sub.add_parser("evaluate")
    evaluation.add_argument("--cases", default="data/evaluation.json")
    evaluation.add_argument("--split", choices=["dev", "test"], default="test")
    evaluation.add_argument(
        "--mode", choices=["bm25", "dense", "hybrid"], default="hybrid"
    )
    args = parser.parse_args()
    engine = make_engine(args.db, args.embedding, args.cache, args.model, args.rerank)
    if args.command == "index":
        records = json.loads(Path(args.documents).read_text(encoding="utf-8"))
        count = 0
        for record in records:
            record["roles"] = tuple(record["roles"])
            count += engine.store.upsert(Document(**record), engine.embedder)
        output = {
            "documents": len(records),
            "chunks": count,
            "embedding": engine.embedder.signature,
        }
    elif args.command == "query":
        output = engine.answer(
            args.question, Principal("acme", frozenset({args.role})), args.mode
        )
    else:
        cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
        cases = [c for c in cases if c["split"] == args.split]
        output = evaluate(
            engine, cases, Principal("acme", frozenset({"reader"})), args.mode
        )
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
