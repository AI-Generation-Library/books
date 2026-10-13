BEGIN;
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY, email text NOT NULL UNIQUE, password_hash text NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash text PRIMARY KEY, user_id uuid NOT NULL REFERENCES users(id), expires_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_expiry ON sessions(expires_at);
CREATE TABLE IF NOT EXISTS jobs (
  id uuid PRIMARY KEY, owner_id uuid NOT NULL REFERENCES users(id),
  state text NOT NULL CHECK(state IN ('uploading','queued','processing','retrying','completed','failed')),
  result jsonb, updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS jobs_owner ON jobs(owner_id,id);
CREATE TABLE IF NOT EXISTS outbox (
  job_id uuid PRIMARY KEY REFERENCES jobs(id), created_at timestamptz NOT NULL DEFAULT now()
);
COMMIT;
