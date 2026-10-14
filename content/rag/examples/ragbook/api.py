from dataclasses import asdict
import hmac
import json
import logging
from pathlib import Path
import time
import uuid
import httpx
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool
from .data import Document, Principal


class Query(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=2000)
    mode: str = Field(default="hybrid", pattern="^(bm25|dense|hybrid)$")
    limit: int = Field(default=5, ge=1, le=20)


class DocumentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern="^[A-Za-z0-9_-]{1,64}$")
    version: str = Field(pattern="^[A-Za-z0-9_-]{1,64}$")
    roles: list[str] = Field(min_length=1, max_length=10)
    title: str = Field(min_length=1, max_length=200)
    source: str = Field(min_length=1, max_length=1000)
    text: str = Field(max_length=200_000)


def create_app(engine, tokens):
    app = FastAPI(title="RAG book evidence service", docs_url="/docs")
    logger = logging.getLogger("ragbook")

    @app.middleware("http")
    async def trace(request, call_next):
        request_id = str(uuid.uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "status": response.status_code,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                }
            )
        )
        return response

    def principal(authorization: str | None = Header(default=None)):
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(401, "authentication required")
        for expected, value in tokens.items():
            if hmac.compare_digest(expected, token):
                return value
        raise HTTPException(401, "authentication required")

    def admin(identity=Depends(principal)):
        if "admin" not in identity.roles:
            raise HTTPException(403, "admin required")
        return identity

    @app.exception_handler(ValueError)
    async def invalid(request, error):
        return JSONResponse({"error": "invalid_request_or_index"}, status_code=400)

    @app.exception_handler(httpx.HTTPError)
    async def unavailable(request, error):
        return JSONResponse({"error": "generation_unavailable"}, status_code=502)

    @app.get("/health")
    def health():
        return {"ready": True, "generator": engine.generator.name}

    @app.get("/", response_class=HTMLResponse)
    def ui():
        return (Path(__file__).parents[1] / "ui/index.html").read_text(encoding="utf-8")

    @app.post("/search")
    def search(body: Query, identity=Depends(principal)):
        return {
            "results": [
                {
                    "id": h.chunk.id,
                    "document_id": h.chunk.doc_id,
                    "text": h.chunk.text,
                    "score": h.score,
                    "version": h.chunk.version,
                }
                for h in engine.search(body.question, identity, body.mode, body.limit)
            ]
        }

    @app.post("/query")
    def query(body: Query, identity=Depends(principal)):
        return engine.answer(body.question, identity, body.mode, body.limit)

    @app.post("/query/stream")
    async def stream(body: Query, identity=Depends(principal)):
        async def events():
            yield 'event: status\ndata: {"stage":"retrieving"}\n\n'
            try:
                result = await run_in_threadpool(
                    engine.answer, body.question, identity, body.mode, body.limit
                )
                yield (
                    "event: answer\ndata: "
                    + json.dumps(result, ensure_ascii=False)
                    + "\n\n"
                )
            except (ValueError, httpx.HTTPError):
                yield 'event: error\ndata: {"error":"query_failed"}\n\n'

        return StreamingResponse(events(), media_type="text/event-stream")

    @app.put("/documents")
    def upsert(body: DocumentInput, identity=Depends(admin)):
        document = Document(
            tenant=identity.tenant, **{**body.model_dump(), "roles": tuple(body.roles)}
        )
        return {"chunks": engine.store.upsert(document, engine.embedder)}

    @app.delete("/documents/{doc_id}")
    def delete(doc_id: str, identity=Depends(admin)):
        if len(doc_id) > 64:
            raise HTTPException(400, "invalid ID")
        engine.store.delete(identity.tenant, doc_id)
        return {"deleted": True}

    return app
