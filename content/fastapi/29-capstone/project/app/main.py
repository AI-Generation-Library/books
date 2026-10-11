import asyncio
import json
import os
import secrets
import sqlite3
import time
from contextlib import asynccontextmanager, suppress
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .db import Database
from .pipeline import event, worker
from .security import decode_token, hash_password, issue_token, verify_password

bearer = HTTPBearer(auto_error=False)


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(min_length=12, max_length=128)


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=1200)


def create_app(db_path: str = "data/hub.sqlite3", secret: str | None = None,
               start_worker: bool = True) -> FastAPI:
    secret = secret or os.environ.get("HUB_JWT_SECRET")
    if secret is None or len(secret) < 32:
        raise RuntimeError("HUB_JWT_SECRET must contain at least 32 characters")
    database = Database(db_path)

    @asynccontextmanager
    async def lifespan(app):
        await database.initialize()
        stop = asyncio.Event()
        task = asyncio.create_task(worker(database, stop)) if start_worker else None
        try:
            yield
        finally:
            stop.set()
            if task is not None:
                try:
                    await asyncio.wait_for(task, timeout=2)
                except TimeoutError:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task

    app = FastAPI(title="Knowledge Hub local mock", lifespan=lifespan)
    app.state.database = database

    async def current_user(credentials: Annotated[HTTPAuthorizationCredentials | None,
                                                  Depends(bearer)]):
        if credentials is None:
            raise HTTPException(401, "authentication_required", headers={"WWW-Authenticate": "Bearer"})
        try:
            claims = decode_token(credentials.credentials, secret)
            user_id = int(claims["sub"])
            user = await database.call(lambda c: c.execute(
                "SELECT id,username,used,reserved,quota FROM users WHERE id=?", (user_id,)).fetchone())
            if user is None:
                raise ValueError("unknown user")
            return dict(user)
        except (jwt.InvalidTokenError, ValueError, TypeError):
            raise HTTPException(401, "invalid_token", headers={"WWW-Authenticate": "Bearer"}) from None

    async def owned_job(job_id: str, user: dict):
        row = await database.call(lambda c: c.execute(
            "SELECT id,status,question,answer,error FROM jobs WHERE id=? AND owner=?",
            (job_id, user["id"])).fetchone())
        if row is None:
            raise HTTPException(404, "job_not_found")
        return dict(row)

    @app.get("/health")
    async def health():
        return {"status": "ok", "mode": "local-mock"}

    @app.post("/users", status_code=201)
    async def register(body: Credentials):
        hashed = await asyncio.to_thread(hash_password, body.password)
        try:
            user_id = await database.call(lambda c: c.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (body.username, hashed)).lastrowid)
        except sqlite3.IntegrityError:
            raise HTTPException(409, "username_exists") from None
        return {"id": user_id, "username": body.username}

    @app.post("/token")
    async def login(body: Credentials):
        row = await database.call(lambda c: c.execute(
            "SELECT id,password FROM users WHERE username=?", (body.username,)).fetchone())
        valid = False
        if row is not None:
            valid = await asyncio.to_thread(verify_password, body.password, row["password"])
        if not valid:
            raise HTTPException(401, "invalid_credentials")
        return {"access_token": issue_token(row["id"], secret), "token_type": "bearer"}

    @app.get("/me")
    async def me(user: Annotated[dict, Depends(current_user)]):
        return {**user, "currency_cost": 0, "usage_kind": "mock_character_units"}

    @app.post("/documents", status_code=201)
    async def upload(request: Request, user: Annotated[dict, Depends(current_user)],
                     title: Annotated[str, Query(min_length=1, max_length=120)] = "문서"):
        if request.headers.get("content-type", "").split(";")[0].lower() != "text/plain":
            raise HTTPException(415, "text_plain_required")
        payload = bytearray()
        async for chunk in request.stream():
            payload.extend(chunk)
            if len(payload) > 65536:
                raise HTTPException(413, "document_too_large")
        try:
            content = payload.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(422, "utf8_required") from None
        if not content.strip():
            raise HTTPException(422, "empty_document")
        def store(c):
            c.execute("BEGIN IMMEDIATE")
            count = c.execute("SELECT count(*) FROM documents WHERE owner=?",
                              (user["id"],)).fetchone()[0]
            if count >= 30:
                raise HTTPException(429, "document_limit")
            return c.execute("INSERT INTO documents(owner,title,content) VALUES(?,?,?)",
                             (user["id"], title, content)).lastrowid
        doc_id = await database.call(store)
        return {"id": doc_id, "title": title}

    @app.post("/jobs", status_code=202)
    async def submit(body: Question, user: Annotated[dict, Depends(current_user)],
                     idempotency_key: Annotated[str, Header(min_length=1, max_length=80)]):
        if not body.question.strip():
            raise HTTPException(422, "empty_question")
        reservation = len(body.question) + 800

        def enqueue(c):
            c.execute("BEGIN IMMEDIATE")
            existing = c.execute("SELECT id,question,status FROM jobs WHERE owner=? AND idem=?",
                                 (user["id"], idempotency_key)).fetchone()
            if existing is not None:
                if existing["question"] != body.question:
                    raise HTTPException(409, "idempotency_payload_conflict")
                return {"id": existing["id"], "status": existing["status"], "replayed": True}
            pending = c.execute("SELECT count(*) FROM jobs WHERE owner=? AND status IN ('queued','running')",
                                (user["id"],)).fetchone()[0]
            if pending >= 5:
                raise HTTPException(429, "active_job_limit")
            result = c.execute("UPDATE users SET reserved=reserved+? WHERE id=? AND used+reserved+?<=quota",
                               (reservation, user["id"], reservation))
            if result.rowcount != 1:
                raise HTTPException(429, "budget_exceeded")
            job_id = secrets.token_hex(16)
            c.execute("INSERT INTO jobs(id,owner,idem,question,status,reservation) VALUES(?,?,?,?,?,?)",
                      (job_id, user["id"], idempotency_key, body.question, "queued", reservation))
            event(c, job_id, "state", {"status": "queued"})
            return {"id": job_id, "status": "queued", "replayed": False}

        return await database.call(enqueue)

    @app.get("/jobs/{job_id}")
    async def job_status(job_id: str, user: Annotated[dict, Depends(current_user)]):
        return await owned_job(job_id, user)

    @app.get("/jobs/{job_id}/events")
    async def events(job_id: str, request: Request, user: Annotated[dict, Depends(current_user)],
                     last_event_id: Annotated[int, Header(ge=0)] = 0):
        await owned_job(job_id, user)  # Reject BEFORE response headers are sent.

        async def generate():
            cursor = last_event_id
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if await request.is_disconnected():
                    return
                rows = await database.call(lambda c: [dict(r) for r in c.execute(
                    "SELECT id,kind,data FROM events WHERE job=? AND id>? ORDER BY id LIMIT 100",
                    (job_id, cursor))])
                for row in rows:
                    cursor = row["id"]
                    yield f"id: {cursor}\nevent: {row['kind']}\ndata: {row['data']}\n\n"
                    if row["kind"] in {"done", "error"}:
                        return
                state = await owned_job(job_id, user)
                if state["status"] in {"succeeded", "failed"} and not rows:
                    return
                yield ": heartbeat\n\n"
                await asyncio.sleep(0.1)
            yield "event: reconnect\ndata: {}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})

    return app
