from .data import Principal, tokenize
from .retrieval import retrieve, bm25
from .generation import validate_claims


class Engine:
    def __init__(self, store, embedder, generator, reranker=None):
        self.store = store
        self.embedder = embedder
        self.generator = generator
        self.reranker = reranker
        if store.signature != embedder.signature:
            raise ValueError("embedding mismatch")

    def search(self, question, principal, mode="hybrid", limit=5):
        if (
            not isinstance(question, str)
            or not question.strip()
            or len(question) > 2000
        ):
            raise ValueError("question length 1..2000")
        if not isinstance(limit, int) or not 1 <= limit <= 20:
            raise ValueError("limit 1..20")
        hits = retrieve(
            question,
            self.store.authorized(principal),
            self.embedder,
            mode,
            20 if self.reranker else limit,
        )
        return self.reranker.rerank(question, hits)[:limit] if self.reranker else hits

    def answer(self, question, principal, mode="hybrid", limit=5, budget=1200):
        hits = self.search(question, principal, mode, limit)
        # 오프라인 데모의 보수적 거절 규칙. 학습한 answerability 점수/확률이 아니다.
        if not hits or not bm25(question, [h.chunk for h in hits]):
            return self.abstain("no_evidence")
        context = []
        used = 0
        for hit in hits:
            if used + len(hit.chunk.text) > budget:
                continue
            context.append(hit)
            used += len(hit.chunk.text)
        if not context:
            return self.abstain("context_budget")
        try:
            generated = self.generator.generate(question, context)
            if not generated:
                return self.abstain("model_abstained")
            claims = validate_claims(generated, context)
        except (ValueError, KeyError, TypeError):
            return self.abstain("invalid_citation")
        # 모델 호출 동안 삭제/버전/권한이 바뀌었으면 이전 근거의 답을 전달하지 않는다.
        current = {c.id for c in self.store.authorized(principal)}
        if any(hit.chunk.id not in current for hit in context):
            return self.abstain("context_changed")
        cited = {claim.chunk_id for claim in claims}
        return {
            "abstained": False,
            "reason": None,
            "generator": self.generator.name,
            "answer": "\n".join(c.text for c in claims),
            "claims": [
                {"text": c.text, "chunk_id": c.chunk_id, "quote": c.quote}
                for c in claims
            ],
            "citations": [
                {
                    "id": h.chunk.id,
                    "document_id": h.chunk.doc_id,
                    "version": h.chunk.version,
                    "title": h.chunk.title,
                    "source": h.chunk.source,
                    "start": h.chunk.start,
                    "end": h.chunk.end,
                }
                for h in context
                if h.chunk.id in cited
            ],
            "citation_check": "source-and-substring-only",
        }

    def abstain(self, reason):
        return {
            "abstained": True,
            "reason": reason,
            "generator": self.generator.name,
            "answer": "허용된 문서에서 충분한 근거를 확인하지 못했습니다.",
            "claims": [],
            "citations": [],
            "citation_check": "source-and-substring-only",
        }
