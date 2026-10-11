import asyncio
import json
import re


def event(connection, job_id: str, kind: str, payload: dict):
    connection.execute("INSERT INTO events(job,kind,data) VALUES(?,?,?)",
                       (job_id, kind, json.dumps(payload, ensure_ascii=False)))


def words(text: str) -> set[str]:
    return set(re.findall(r"[\w]+", text.lower()))


def mock_answer(question: str, documents: list[dict]) -> tuple[str, list[dict]]:
    # This is lexical retrieval and an extractive mock, NOT a real embedding/LLM.
    query = words(question)
    ranked = sorted(documents,
                    key=lambda d: (-len(query & words(d["content"])), d["id"]))
    matches = [d for d in ranked if query & words(d["content"])][:3]
    sources = [{"document_id": d["id"], "title": d["title"]} for d in matches]
    if not matches:
        return "허용된 문서에서 관련 근거를 찾지 못했습니다.", []
    excerpts = [f"[{d['id']}] {d['content'][:180]}" for d in matches]
    return ("모의 답변: " + " / ".join(excerpts))[:800], sources


async def run_once(database) -> bool:
    def claim(c):
        c.execute("BEGIN IMMEDIATE")
        row = c.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY rowid LIMIT 1").fetchone()
        if row is None:
            return None
        c.execute("UPDATE jobs SET status='running' WHERE id=?", (row["id"],))
        event(c, row["id"], "state", {"status": "running"})
        return dict(row)

    job = await database.call(claim)
    if job is None:
        return False
    try:
        # ACL is applied in the SQL before candidate ranking or generation.
        documents = await database.call(lambda c: [dict(row) for row in c.execute(
            "SELECT id,title,content FROM documents WHERE owner=?", (job["owner"],))])
        answer, sources = mock_answer(job["question"], documents)
        await asyncio.sleep(0.01)  # controlled fake provider I/O

        def finish(c):
            c.execute("BEGIN IMMEDIATE")
            current = c.execute("SELECT status FROM jobs WHERE id=?", (job["id"],)).fetchone()
            if current["status"] != "running":
                return
            # Atomic terminal state + ledger settlement + final events.
            billed_units = len(job["question"]) + len(answer)
            c.execute("UPDATE users SET reserved=reserved-?,used=used+? WHERE id=?",
                      (job["reservation"], billed_units, job["owner"]))
            c.execute("UPDATE jobs SET status='succeeded',answer=? WHERE id=?", (answer, job["id"]))
            event(c, job["id"], "sources", {"sources": sources})
            for offset in range(0, len(answer), 40):
                event(c, job["id"], "delta", {"text": answer[offset:offset + 40]})
            event(c, job["id"], "done", {"status": "succeeded", "mock_units": billed_units})

        await database.call(finish)
    except asyncio.CancelledError:
        # Keep reservation; startup can recover this single-process local job.
        raise
    except Exception:
        def fail(c):
            c.execute("BEGIN IMMEDIATE")
            current = c.execute("SELECT status FROM jobs WHERE id=?", (job["id"],)).fetchone()
            if current["status"] != "running":
                return
            c.execute("UPDATE users SET reserved=reserved-? WHERE id=?",
                      (job["reservation"], job["owner"]))
            c.execute("UPDATE jobs SET status='failed',error='pipeline_failed' WHERE id=?", (job["id"],))
            event(c, job["id"], "error", {"code": "pipeline_failed"})
        await database.call(fail)
    return True


async def worker(database, stop: asyncio.Event):
    while not stop.is_set():
        if not await run_once(database):
            try:
                await asyncio.wait_for(stop.wait(), timeout=0.05)
            except TimeoutError:
                pass
