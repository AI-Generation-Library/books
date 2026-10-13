import pg from 'pg';
import { HttpError } from './errors.mjs';
const { Pool } = pg;
const mapJob = row => row && ({ id: row.id, ownerId: row.owner_id, state: row.state, result: row.result });
export class PostgresRepository {
  constructor(connectionString) {
    this.pool = new Pool({ connectionString, max: 5, connectionTimeoutMillis: 3000,
      idleTimeoutMillis: 10_000, statement_timeout: 5000 });
    this.pool.on('error', error => console.error(JSON.stringify({ event: 'pg_idle_error', code: error.code })));
  }
  async addUser(user) {
    try { await this.pool.query('INSERT INTO users(id,email,password_hash) VALUES($1,$2,$3)', [user.id, user.email, user.passwordHash]); }
    catch (error) { if (error.code === '23505') throw new HttpError(409, 'EMAIL_EXISTS', '이미 등록된 이메일입니다.'); throw error; }
  }
  async userByEmail(email) {
    const { rows } = await this.pool.query('SELECT id,email,password_hash FROM users WHERE email=$1', [email]);
    return rows[0] && { id: rows[0].id, email: rows[0].email, passwordHash: rows[0].password_hash };
  }
  async addSession(hash, userId, expiresAt) {
    await this.pool.query('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES($1,$2,$3)', [hash, userId, new Date(expiresAt)]);
  }
  async session(hash) {
    const { rows } = await this.pool.query('SELECT user_id FROM sessions WHERE token_hash=$1 AND expires_at>now()', [hash]);
    return rows[0] && { userId: rows[0].user_id };
  }
  async deleteSession(hash) { await this.pool.query('DELETE FROM sessions WHERE token_hash=$1', [hash]); }
  async createJob(job) {
    await this.pool.query("INSERT INTO jobs(id,owner_id,state) VALUES($1,$2,'uploading')", [job.id, job.ownerId]);
  }
  async enqueueJob(id) {
    const c = await this.pool.connect();
    try {
      await c.query('BEGIN');
      await c.query("UPDATE jobs SET state='queued',updated_at=now() WHERE id=$1 AND state='uploading'", [id]);
      await c.query('INSERT INTO outbox(job_id) VALUES($1) ON CONFLICT DO NOTHING', [id]);
      await c.query('COMMIT');
    } catch (error) { await c.query('ROLLBACK'); throw error; }
    finally { c.release(); }
  }
  async job(id) { const { rows } = await this.pool.query('SELECT * FROM jobs WHERE id=$1', [id]); return mapJob(rows[0]); }
  async updateJob(id, state, result = null) {
    await this.pool.query("UPDATE jobs SET state=$2,result=$3,updated_at=now() WHERE id=$1 AND state<>'completed'", [id, state, result]);
  }
  async pending() { const { rows } = await this.pool.query('SELECT job_id FROM outbox ORDER BY created_at LIMIT 50'); return rows.map(r => r.job_id); }
  async dispatched(id) { await this.pool.query('DELETE FROM outbox WHERE job_id=$1', [id]); }
  async ping() { await this.pool.query('SELECT 1'); return true; }
  async close() { await this.pool.end(); }
}
