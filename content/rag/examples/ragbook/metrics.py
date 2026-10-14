import math


def unique(values):
    return list(dict.fromkeys(values))


def retrieval_metrics(ranked, qrels, k=5):
    if k < 1:
        raise ValueError("k>=1")
    ranked = unique(ranked)[:k]
    relevant = {key for key, grade in qrels.items() if grade > 0}
    hits = sum(key in relevant for key in ranked)
    rr = next((1 / rank for rank, key in enumerate(ranked, 1) if key in relevant), 0.0)
    dcg = sum(
        (2 ** qrels.get(key, 0) - 1) / math.log2(rank + 1)
        for rank, key in enumerate(ranked, 1)
    )
    ideal = sum(
        (2**grade - 1) / math.log2(rank + 1)
        for rank, grade in enumerate(sorted(qrels.values(), reverse=True)[:k], 1)
    )
    return {
        "precision": hits / k,
        "recall": hits / len(relevant) if relevant else None,
        "reciprocal_rank": rr,
        "ndcg": dcg / ideal if ideal else None,
    }


def evaluate(engine, cases, principal, mode="hybrid", k=3):
    rows = []
    for case in cases:
        ranked = unique(
            [
                h.chunk.doc_id
                for h in engine.search(case["question"], principal, mode, 20)
            ]
        )[:k]
        scores = retrieval_metrics(ranked, case["qrels"], k)
        answer = engine.answer(case["question"], principal, mode, k)
        rows.append(
            {
                "id": case["id"],
                "answerable": bool(case["qrels"]),
                "ranked_documents": unique(ranked),
                "metrics": scores,
                "abstained": answer["abstained"],
                "abstention_correct": answer["abstained"] == case["should_abstain"],
            }
        )
    means = {
        metric: sum(values) / len(values) if values else None
        for metric in ("precision", "recall", "reciprocal_rank", "ndcg")
        for values in [
            [
                row["metrics"][metric]
                for row in rows
                if row["answerable"] and row["metrics"][metric] is not None
            ]
        ]
    }
    return {
        "mode": mode,
        "k": k,
        "retrieval_unit": "unique document, up to 20 candidate chunks",
        "cases": rows,
        "mean_retrieval": means,
        "abstention_accuracy": sum(row["abstention_correct"] for row in rows)
        / len(rows)
        if rows
        else None,
        "scope": "synthetic author-created fixture; retrieval and refusal only; not LLM answer correctness",
    }
