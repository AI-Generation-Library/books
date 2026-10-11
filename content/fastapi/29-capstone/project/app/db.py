import asyncio
import sqlite3
from contextlib import closing
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL,
 used INTEGER NOT NULL DEFAULT 0, reserved INTEGER NOT NULL DEFAULT 0,
 quota INTEGER NOT NULL DEFAULT 100000
);
CREATE TABLE IF NOT EXISTS documents (
 id INTEGER PRIMARY KEY, owner INTEGER NOT NULL REFERENCES users(id),
 title TEXT NOT NULL, content TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
 id TEXT PRIMARY KEY, owner INTEGER NOT NULL REFERENCES users(id),
 idem TEXT NOT NULL, question TEXT NOT NULL, status TEXT NOT NULL,
 reservation INTEGER NOT NULL, answer TEXT, error TEXT,
 UNIQUE(owner, idem)
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, job TEXT NOT NULL REFERENCES jobs(id),
 kind TEXT NOT NULL, data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_job_id ON events(job, id);
CREATE INDEX IF NOT EXISTS documents_owner ON documents(owner);
"""


class Database:
    def __init__(self, path: str):
        self.path = path

    def _execute(self, operation):
        # Every operation owns its connection; no connection crosses threads.
        with closing(sqlite3.connect(self.path, timeout=5)) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            # sqlite3.Connection.__exit__ commits/rolls back; it does NOT close.
            # The outer closing context also closes on every exception path.
            with connection:
                return operation(connection)

    async def call(self, operation):
        return await asyncio.to_thread(self._execute, operation)

    async def initialize(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        await self.call(lambda c: c.executescript(SCHEMA))
        # A SINGLE process owns this database in the teaching application.
        # There are no external effects to repeat. Never use this recovery rule
        # while another worker can still be alive.
        await self.call(lambda c: c.execute(
            "UPDATE jobs SET status='queued' WHERE status='running'"))
