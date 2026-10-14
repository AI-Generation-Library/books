from collections import Counter
from dataclasses import dataclass
import math
from .data import Chunk, tokenize
from .embedding import cosine


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


def bm25(query, chunks, k1=1.5, b=0.75):
    if not chunks:
        return []
    documents = [Counter(tokenize(c.text)) for c in chunks]
    lengths = [sum(d.values()) for d in documents]
    average = sum(lengths) / len(chunks) or 1
    query_terms = set(tokenize(query))
    results = []
    for index, (chunk, counts) in enumerate(zip(chunks, documents)):
        score = 0.0
        for term in query_terms:
            df = sum(term in d for d in documents)
            if not df or not counts[term]:
                continue
            idf = math.log(1 + (len(chunks) - df + 0.5) / (df + 0.5))
            tf = counts[term]
            score += (
                idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * lengths[index] / average))
            )
        if score > 0:
            results.append(Hit(chunk, score))
    return sorted(results, key=lambda x: (-x.score, x.chunk.id))


def dense(query, chunks, embedder):
    if not chunks:
        return []
    vector = embedder.embed([query])[0]
    hits = [Hit(c, cosine(vector, c.vector)) for c in chunks]
    return sorted(hits, key=lambda x: (-x.score, x.chunk.id))


def rrf(rankings, k=60):
    if k < 1:
        raise ValueError("rrf k must be positive")
    scores = {}
    objects = {}
    for ranking in rankings:
        seen = set()
        for rank, hit in enumerate(ranking, 1):
            if hit.chunk.id in seen:
                continue
            seen.add(hit.chunk.id)
            objects[hit.chunk.id] = hit.chunk
            scores[hit.chunk.id] = scores.get(hit.chunk.id, 0) + 1 / (k + rank)
    return sorted(
        [Hit(objects[key], value) for key, value in scores.items()],
        key=lambda x: (-x.score, x.chunk.id),
    )


def mmr(hits, query_vector, count=3, weight=0.7):
    if not 0 <= weight <= 1:
        raise ValueError("weight 0..1")
    selected = []
    remaining = list(hits)
    while remaining and len(selected) < count:

        def value(hit):
            relevance = cosine(query_vector, hit.chunk.vector)
            duplicate = max(
                (cosine(hit.chunk.vector, x.chunk.vector) for x in selected), default=0
            )
            return weight * relevance - (1 - weight) * duplicate

        chosen = max(remaining, key=value)
        remaining.remove(chosen)
        selected.append(chosen)
    return selected


def retrieve(query, chunks, embedder, mode="hybrid", limit=5):
    if not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError("limit 1..20")
    if mode not in ("bm25", "dense", "hybrid"):
        raise ValueError("invalid retrieval mode")
    lexical = bm25(query, chunks) if mode != "dense" else []
    vectors = dense(query, chunks, embedder) if mode != "bm25" else []
    # 각 검색의 후보 수와 융합 후 결과 수를 구분한다. 여기서는 각 최대20개다.
    hits = (
        lexical
        if mode == "bm25"
        else vectors
        if mode == "dense"
        else rrf([lexical[:20], vectors[:20]])
    )
    return hits[:limit]
