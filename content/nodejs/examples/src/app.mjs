import express from 'express';
import { randomUUID } from 'node:crypto';
import { AsyncLocalStorage } from 'node:async_hooks';
import { HttpError, requireId } from './errors.mjs';
import { credentials, hashPassword, checkPassword, newToken, tokenHash, limiter } from './security.mjs';
import { storeUpload } from './files.mjs';
const context = new AsyncLocalStorage();

export function createApp({ repo, queue, root, maxBytes = 1024 * 1024, log = () => {}, authLimit = 30 }) {
  const app = express(); let ready = true;
  app.disable('x-powered-by');
  app.use((req, res, next) => context.run({ requestId: randomUUID() }, () => {
    const { requestId } = context.getStore();
    res.set({ 'X-Request-Id': requestId, 'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'no-store' });
    const start = performance.now();
    res.on('finish', () => log({ requestId, method: req.method, status: res.statusCode, durationMs: Math.round(performance.now() - start) }));
    next();
  }));
  app.get('/health/live', (req, res) => res.json({ live: true }));
  app.get('/health/ready', async (req, res) => {
    if (!ready) return res.status(503).json({ ready: false });
    await repo.ping();
    if (!await queue.ping()) throw new Error('queue unavailable');
    res.json({ ready: true });
  });
  app.use((req, res, next) => ready ? next() : next(new HttpError(503, 'DRAINING', '종료 중입니다.')));
  app.use(express.json({ limit: '8kb' }));
  app.use('/auth', limiter({ max: authLimit }));
  app.post('/auth/register', async (req, res) => {
    const { email, password } = credentials(req.body);
    const id = randomUUID();
    await repo.addUser({ id, email, passwordHash: await hashPassword(password) });
    res.status(201).json({ id, email });
  });
  app.post('/auth/login', async (req, res) => {
    const { email, password } = credentials(req.body);
    const user = await repo.userByEmail(email);
    // 존재하지 않는 이메일도 같은 KDF를 수행해 큰 시간 차이를 줄인다.
    const fallback = 'scrypt-v1:00000000000000000000000000000000:' + '00'.repeat(64);
    const valid = await checkPassword(password, user?.passwordHash ?? fallback);
    if (!user || !valid) throw new HttpError(401, 'LOGIN_FAILED', '로그인에 실패했습니다.');
    const token = newToken(); const expiresAt = Date.now() + 60 * 60 * 1000;
    await repo.addSession(tokenHash(token), user.id, expiresAt);
    res.json({ token, expiresAt });
  });
  async function authenticated(req, res, next) {
    const header = req.get('authorization') || '';
    if (!/^Bearer [A-Za-z0-9_-]{43}$/.test(header)) throw new HttpError(401, 'UNAUTHORIZED', '인증이 필요합니다.');
    req.sessionHash = tokenHash(header.slice(7));
    req.session = await repo.session(req.sessionHash);
    if (!req.session) throw new HttpError(401, 'UNAUTHORIZED', '세션이 만료되었습니다.');
    next();
  }
  app.post('/auth/logout', authenticated, async (req, res) => {
    await repo.deleteSession(req.sessionHash); res.status(204).end();
  });
  app.post('/jobs', authenticated, async (req, res) => {
    if (!req.is('application/octet-stream')) throw new HttpError(415, 'CONTENT_TYPE', 'application/octet-stream이 필요합니다.');
    const length = req.get('content-length');
    if (length && Number(length) > maxBytes) throw new HttpError(413, 'FILE_TOO_LARGE', '파일 크기를 초과했습니다.');
    const id = randomUUID();
    await repo.createJob({ id, ownerId: req.session.userId });
    try { await storeUpload(req, root, id, maxBytes); await repo.enqueueJob(id); }
    catch (error) { await repo.updateJob(id, 'failed'); throw error; }
    res.status(202).location(`/jobs/${id}`).json({ id, state: 'queued' });
  });
  async function owned(req) {
    const job = await repo.job(requireId(req.params.id));
    if (!job || job.ownerId !== req.session.userId) throw new HttpError(404, 'NOT_FOUND', '작업을 찾을 수 없습니다.');
    return { id: job.id, state: job.state, result: job.result };
  }
  app.get('/jobs/:id', authenticated, async (req, res) => res.json(await owned(req)));
  app.get('/jobs/:id/events', authenticated, async (req, res, next) => {
    const first = await owned(req);
    res.set({ 'Content-Type': 'text/event-stream', 'Connection': 'keep-alive', 'X-Accel-Buffering': 'no' });
    res.flushHeaders();
    let stopped = false, timer; const deadline = Date.now() + 30_000;
    const stop = () => { stopped = true; clearTimeout(timer); };
    res.on('close', stop);
    async function emit(job) {
      if (stopped) return;
      if (!res.write(`event: status\ndata: ${JSON.stringify(job)}\n\n`)) { stop(); res.end(); return; }
      if (['completed', 'failed'].includes(job.state) || Date.now() >= deadline) { stop(); res.end(); return; }
      timer = setTimeout(async () => {
        try { await emit(await owned(req)); }
        catch (error) { stop(); res.destroy(error); }
      }, 250);
    }
    await emit(first);
  });
  app.use((req, res, next) => next(new HttpError(404, 'NOT_FOUND', '경로를 찾을 수 없습니다.')));
  app.use((error, req, res, next) => {
    if (res.headersSent || res.destroyed) return next(error);
    const status = error instanceof HttpError ? error.status : error.type === 'entity.too.large' ? 413 : error.type === 'entity.parse.failed' ? 400 : 500;
    log({ requestId: context.getStore()?.requestId, event: 'request_error', name: error.name });
    res.status(status).json({ error: { code: error instanceof HttpError ? error.code : status === 400 ? 'INVALID_JSON' : status === 413 ? 'BODY_TOO_LARGE' : 'INTERNAL_ERROR',
      message: error instanceof HttpError ? error.message : '요청을 처리하지 못했습니다.', requestId: context.getStore()?.requestId } });
  });
  return { app, drain: () => { ready = false; } };
}
