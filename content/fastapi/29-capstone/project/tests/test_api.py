import secrets
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor

import jwt
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.db import Database
from app.security import AUDIENCE, ISSUER


@pytest.fixture
def session(tmp_path):
    secret = secrets.token_urlsafe(48)
    app = create_app(str(tmp_path / "hub.sqlite3"), secret)
    with TestClient(app) as client:
        yield client, secret


def user(client, name):
    body = {"username": name, "password": "local-password-12345"}
    assert client.post("/users", json=body).status_code == 201
    token = client.post("/token", json=body).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def wait_done(client, job_id, headers):
    for _ in range(100):
        result = client.get(f"/jobs/{job_id}", headers=headers).json()
        if result["status"] in {"succeeded", "failed"}:
            return result
        time.sleep(0.02)
    raise AssertionError("worker did not complete")


def test_whole_flow_and_sse_replay(session):
    client, _ = session
    headers = user(client, "alice")
    response = client.post("/documents?title=guide", content="FastAPI supports asynchronous API services.",
                           headers={**headers, "Content-Type": "text/plain"})
    assert response.status_code == 201
    submitted = client.post("/jobs", json={"question": "FastAPI"},
                            headers={**headers, "Idempotency-Key": "question-1"})
    assert submitted.status_code == 202
    job_id = submitted.json()["id"]
    assert wait_done(client, job_id, headers)["status"] == "succeeded"
    stream = client.get(f"/jobs/{job_id}/events", headers=headers)
    assert "event: sources" in stream.text
    assert "event: delta" in stream.text
    assert "event: done" in stream.text
    ids = [int(line[4:]) for line in stream.text.splitlines() if line.startswith("id: ")]
    replay = client.get(f"/jobs/{job_id}/events",
                        headers={**headers, "Last-Event-ID": str(ids[-2])})
    assert "event: done" in replay.text
    assert f"id: {ids[0]}\n" not in replay.text
    ledger = client.get("/me", headers=headers).json()
    assert ledger["reserved"] == 0 and ledger["used"] > 0
    assert ledger["currency_cost"] == 0


def test_owner_isolation_before_retrieval(session):
    client, _ = session
    alice, bob = user(client, "alice"), user(client, "bob")
    client.post("/documents", content="FastAPI private alice-only-secret",
                headers={**alice, "Content-Type": "text/plain"})
    response = client.post("/jobs", json={"question": "FastAPI"},
                           headers={**bob, "Idempotency-Key": "bob-job"})
    job_id = response.json()["id"]
    result = wait_done(client, job_id, bob)
    assert "alice-only-secret" not in result["answer"]
    assert "근거를 찾지" in result["answer"]
    assert client.get(f"/jobs/{job_id}", headers=alice).status_code == 404
    assert client.get(f"/jobs/{job_id}/events", headers=alice).status_code == 404


def test_idempotency_and_payload_conflict(session):
    client, _ = session
    headers = {**user(client, "alice"), "Idempotency-Key": "same"}
    first = client.post("/jobs", json={"question": "hello"}, headers=headers).json()
    again = client.post("/jobs", json={"question": "hello"}, headers=headers).json()
    assert first["id"] == again["id"] and again["replayed"]
    assert client.post("/jobs", json={"question": "changed"}, headers=headers).status_code == 409


def test_bad_auth_upload_and_validation(session):
    client, secret = session
    headers = user(client, "alice")
    assert client.get("/me").status_code == 401
    token = jwt.encode({"sub": "1", "iss": ISSUER, "aud": AUDIENCE, "iat": 1,
                        "nbf": 1, "exp": 2}, secret, algorithm="HS256")
    assert client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    assert client.post("/documents", content="a", headers=headers).status_code == 415
    assert client.post("/documents", content=b"a" * 65537,
                       headers={**headers, "Content-Type": "text/plain"}).status_code == 413
    assert client.post("/jobs", json={"question": " "},
                       headers={**headers, "Idempotency-Key": "empty"}).status_code == 422


def test_concurrent_idempotency_has_one_job(session):
    client, _ = session
    headers = {**user(client, "alice"), "Idempotency-Key": "concurrent"}
    def submit(_):
        response = client.post("/jobs", json={"question": "same question"}, headers=headers)
        assert response.status_code == 202
        return response.json()["id"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(submit, range(8)))
    assert len(set(ids)) == 1
    wait_done(client, ids[0], headers)
    with sqlite3.connect(client.app.state.database.path) as connection:
        assert connection.execute("SELECT count(*) FROM jobs").fetchone()[0] == 1


def test_budget_rejection_does_not_reserve(session):
    client, _ = session
    headers = user(client, "alice")
    with sqlite3.connect(client.app.state.database.path) as connection:
        connection.execute("UPDATE users SET quota=10")
    response = client.post("/jobs", json={"question": "hello"},
                           headers={**headers, "Idempotency-Key": "expensive"})
    assert response.status_code == 429
    ledger = client.get("/me", headers=headers).json()
    assert ledger["used"] == 0 and ledger["reserved"] == 0


def test_restart_recovers_single_process_running_job(tmp_path):
    secret = secrets.token_urlsafe(48)
    path = str(tmp_path / "restart.sqlite3")
    with TestClient(create_app(path, secret, start_worker=False)) as first:
        headers = user(first, "alice")
        response = first.post("/jobs", json={"question": "hello"},
                              headers={**headers, "Idempotency-Key": "restart"})
        job_id = response.json()["id"]
        with sqlite3.connect(path) as connection:
            connection.execute("UPDATE jobs SET status='running' WHERE id=?", (job_id,))
    with TestClient(create_app(path, secret)) as recovered:
        assert wait_done(recovered, job_id, headers)["status"] == "succeeded"
        ledger = recovered.get("/me", headers=headers).json()
        assert ledger["reserved"] == 0 and ledger["used"] > 0


def test_jwt_audience_algorithm_and_required_claims(session):
    client, secret = session
    user(client, "alice")
    now = int(time.time())
    base = {"sub": "1", "iss": ISSUER, "aud": AUDIENCE, "iat": now,
            "nbf": now, "exp": now + 60}
    candidates = [(dict(base, aud="other-api"), "HS256"),
                  (base, "HS384"),
                  ({key: value for key, value in base.items() if key != "exp"}, "HS256")]
    for claims, algorithm in candidates:
        token = jwt.encode(claims, secret, algorithm=algorithm)
        response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_database_connection_closes_and_rolls_back(tmp_path, monkeypatch):
    original_connect = sqlite3.connect
    closed = []
    class TrackedConnection(sqlite3.Connection):
        def close(self):
            closed.append(self)
            super().close()
    def connect(*args, **kwargs):
        return original_connect(*args, **kwargs, factory=TrackedConnection)
    monkeypatch.setattr("app.db.sqlite3.connect", connect)
    database = Database(str(tmp_path / "connections.sqlite3"))
    database._execute(lambda c: c.execute("CREATE TABLE sample(id INTEGER)"))
    def fail(connection):
        connection.execute("INSERT INTO sample VALUES(1)")
        raise ValueError("injected failure")
    with pytest.raises(ValueError):
        database._execute(fail)
    count = database._execute(lambda c: c.execute("SELECT count(*) FROM sample").fetchone()[0])
    assert count == 0 and len(closed) == 3
    for connection in closed:
        with pytest.raises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")
