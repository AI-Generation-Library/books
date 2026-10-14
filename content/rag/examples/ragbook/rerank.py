from .retrieval import Hit
import math


class FastCrossEncoder:
    def __init__(self, cache_dir="model-cache-rerank"):
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        self.model = TextCrossEncoder(
            model_name="BAAI/bge-reranker-v2-m3-int8", cache_dir=cache_dir, threads=2
        )

    def rerank(self, question, hits):
        if not hits:
            return []
        # FastEmbed 0.9의 반환값은 입력 후보 순서의 점수이며 정렬된 객체가 아니다.
        scores = list(self.model.rerank(question, [h.chunk.text for h in hits]))
        if len(scores) != len(hits) or not all(math.isfinite(float(x)) for x in scores):
            raise ValueError("invalid reranker scores")
        return sorted(
            [Hit(hit.chunk, float(score)) for hit, score in zip(hits, scores)],
            key=lambda hit: (-hit.score, hit.chunk.id),
        )
