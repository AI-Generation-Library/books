import json
import os
import uvicorn
from ragbook.api import create_app
from ragbook.cli import make_engine
from ragbook.data import Principal

if __name__ == "__main__":
    engine = make_engine(
        os.getenv("RAG_DB", "var/index-demo.sqlite3"),
        os.getenv("RAG_EMBEDDING", "character"),
        os.getenv("RAG_MODEL_CACHE", "model-cache"),
        os.getenv("RAG_OLLAMA_MODEL"),
        os.getenv("RAG_RERANK") == "1",
    )
    # 가상 문서 localhost 학습용 계정. 실제 운영은 검증된 인증 제공자와 연결한다.
    raw = json.loads(
        os.getenv(
            "RAG_DEMO_TOKENS",
            '{"reader-local-token":{"tenant":"acme","roles":["reader"]},"admin-local-token":{"tenant":"acme","roles":["admin"]}}',
        )
    )
    tokens = {
        token: Principal(value["tenant"], frozenset(value["roles"]))
        for token, value in raw.items()
    }
    if not tokens or any(len(token) < 16 for token in tokens):
        raise ValueError("tokens must be at least 16 characters")
    app = create_app(engine, tokens)
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.getenv("PORT", "8000")),
        limit_concurrency=16,
        timeout_keep_alive=5,
    )
