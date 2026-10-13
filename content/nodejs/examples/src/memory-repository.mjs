import { HttpError } from './errors.mjs';
// 프로세스 재시작 시 사라지는 학습용 구현. production 모드에서는 사용하지 않는다.
export class MemoryRepository {
  users = new Map(); sessions = new Map(); jobs = new Map(); outbox = new Set();
  async addUser(user) {
    if ([...this.users.values()].some(x => x.email === user.email)) throw new HttpError(409, 'EMAIL_EXISTS', '이미 등록된 이메일입니다.');
    this.users.set(user.id, { ...user });
  }
  async userByEmail(email) { return [...this.users.values()].find(x => x.email === email); }
  async addSession(hash, userId, expiresAt) { this.sessions.set(hash, { userId, expiresAt }); }
  async session(hash) { const s = this.sessions.get(hash); return s && s.expiresAt > Date.now() ? s : null; }
  async deleteSession(hash) { this.sessions.delete(hash); }
  async createJob(job) { this.jobs.set(job.id, { ...job, state: 'uploading', result: null }); }
  async enqueueJob(id) { const j = this.jobs.get(id); j.state = 'queued'; this.outbox.add(id); }
  async job(id) { const j = this.jobs.get(id); return j ? structuredClone(j) : null; }
  async updateJob(id, state, result = null) {
    const j = this.jobs.get(id);
    if (j && j.state !== 'completed') Object.assign(j, { state, result });
  }
  async pending() { return [...this.outbox].slice(0, 50); }
  async dispatched(id) { this.outbox.delete(id); }
  async ping() { return true; }
  async close() {}
}
