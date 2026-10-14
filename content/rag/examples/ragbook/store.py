from contextlib import contextmanager
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
import re
from .data import Chunk, Document, Principal, chunks
from .embedding import unit


class Store:
    def __init__(self, path, embedding_signature):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.signature = embedding_signature
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS documents(
              tenant TEXT NOT NULL,id TEXT NOT NULL,roles TEXT NOT NULL,title TEXT NOT NULL,
              source TEXT NOT NULL,version TEXT NOT NULL,PRIMARY KEY(tenant,id));
            CREATE TABLE IF NOT EXISTS chunks(
              id TEXT PRIMARY KEY,tenant TEXT NOT NULL,doc_id TEXT NOT NULL,start INTEGER NOT NULL,
              end INTEGER NOT NULL,text TEXT NOT NULL,vector TEXT NOT NULL,
              FOREIGN KEY(tenant,doc_id) REFERENCES documents(tenant,id) ON DELETE CASCADE);
            """)
            old = db.execute(
                "SELECT value FROM metadata WHERE key='embedding'"
            ).fetchone()
            if old and old[0] != embedding_signature:
                raise ValueError("embedding mismatch: build a separate index")
            db.execute(
                "INSERT OR IGNORE INTO metadata VALUES('embedding',?)",
                (embedding_signature,),
            )

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def upsert(self, doc: Document, embedder, size=320, overlap=40):
        if embedder.signature != self.signature:
            raise ValueError("embedding mismatch")
        if (
            not doc.id
            or not doc.tenant
            or not doc.roles
            or not doc.version
            or not doc.title
            or len(doc.text) > 200_000
        ):
            raise ValueError("invalid document")
        if not all(
            re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value)
            for value in (doc.id, doc.tenant, doc.version, *doc.roles)
        ):
            raise ValueError("invalid identifiers")
        if not doc.source.startswith(("https://", "fixture://")):
            raise ValueError("invalid source scheme")
        parts = chunks(doc, size, overlap)
        vectors = embedder.embed([x.text for x in parts]) if parts else []
        vectors = [unit(v) for v in vectors]
        if len(vectors) != len(parts):
            raise ValueError("embedding count mismatch")
        dimensions = {len(x) for x in vectors}
        if vectors and (len(dimensions) != 1 or 0 in dimensions):
            raise ValueError("invalid dimensions")
        # 추론은 쓰기 트랜잭션 밖에서 수행하고 DB 교체만 원자적으로 실행한다.
        with self.connect() as db:
            old_dimension = db.execute(
                "SELECT value FROM metadata WHERE key='dimension'"
            ).fetchone()
            dimension = next(iter(dimensions), None)
            if (
                old_dimension
                and dimension is not None
                and int(old_dimension[0]) != dimension
            ):
                raise ValueError("dimension mismatch")
            if dimension is not None:
                db.execute(
                    "INSERT OR IGNORE INTO metadata VALUES('dimension',?)",
                    (str(dimension),),
                )
            db.execute(
                "DELETE FROM documents WHERE tenant=? AND id=?", (doc.tenant, doc.id)
            )
            db.execute(
                "INSERT INTO documents VALUES(?,?,?,?,?,?)",
                (
                    doc.tenant,
                    doc.id,
                    json.dumps(doc.roles),
                    doc.title,
                    doc.source,
                    doc.version,
                ),
            )
            db.executemany(
                "INSERT INTO chunks VALUES(?,?,?,?,?,?,?)",
                [
                    (
                        c.id,
                        c.tenant,
                        c.doc_id,
                        c.start,
                        c.end,
                        c.text,
                        json.dumps(list(v)),
                    )
                    for c, v in zip(parts, vectors)
                ],
            )
        return len(parts)

    def delete(self, tenant, doc_id):
        with self.connect() as db:
            db.execute(
                "DELETE FROM documents WHERE tenant=? AND id=?", (tenant, doc_id)
            )

    def authorized(self, principal: Principal):
        # 후보 생성 전에 tenant와 역할을 적용한다. 비인가 청크는 랭커/프롬프트에 넘기지 않는다.
        with self.connect() as db:
            rows = db.execute(
                """
            SELECT c.*,d.roles,d.title,d.source,d.version FROM chunks c JOIN documents d
            ON c.tenant=d.tenant AND c.doc_id=d.id WHERE d.tenant=? ORDER BY c.id
            """,
                (principal.tenant,),
            ).fetchall()
        result = []
        for row in rows:
            if not principal.roles.intersection(json.loads(row["roles"])):
                continue
            result.append(
                Chunk(
                    row["id"],
                    row["doc_id"],
                    row["tenant"],
                    row["title"],
                    row["source"],
                    row["version"],
                    row["start"],
                    row["end"],
                    row["text"],
                    tuple(json.loads(row["vector"])),
                )
            )
        return result
