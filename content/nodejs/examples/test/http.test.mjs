import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
import { createApp } from '../src/app.mjs';
import { MemoryRepository } from '../src/memory-repository.mjs';
import { MemoryQueue, dispatcher } from '../src/queue.mjs';
import { processJob } from '../src/files.mjs';
import { getJson } from '../fundamentals/21-fetch.mjs';

async function fixture(t, options = {}) {
  const root = await mkdtemp(join(tmpdir(), 'nodebook-http-'));
  const repo = new MemoryRepository();
  const queue = new MemoryQueue(id => processJob(repo, root, id), repo);
  const service = createApp({ repo, queue, root, ...options });
  const stop = dispatcher(repo, queue, () => {}, 5);
  const server = createServer(service.app); server.listen(0, '127.0.0.1'); await once(server, 'listening');
  t.after(async () => { await stop(); server.closeAllConnections(); await new Promise(r => server.close(r)); await queue.close(); await rm(root, { recursive: true, force: true }); });
  const base = `http://127.0.0.1:${server.address().port}`;
  const request = (path, options) => fetch(base + path, options);
  const json = (path, body) => request(path, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
  async function signup(email = `${randomUUID()}@example.test`) {
    const credentials = { email, password: 'long-password-123' };
    assert.equal((await json('/auth/register', credentials)).status, 201);
    return (await (await json('/auth/login', credentials)).json()).token;
  }
  return { ...service, repo, base, request, json, signup };
}
test('인증부터 업로드, 결과, SSE, 로그아웃까지', async t => {
  const f = await fixture(t), token = await f.signup();
  const headers = { authorization: `Bearer ${token}` };
  const upload = await f.request('/jobs', { method: 'POST', headers: { ...headers, 'content-type': 'application/octet-stream' }, body: '안녕\nNode' });
  assert.equal(upload.status, 202); const { id } = await upload.json();
  assert.equal(upload.headers.get('location'), `/jobs/${id}`);
  let job;
  for (let i = 0; i < 100; i++) { job = await (await f.request(`/jobs/${id}`, { headers })).json(); if (job.state === 'completed') break; await delay(10); }
  assert.equal(job.state, 'completed'); assert.deepEqual(job.result, { bytes: 11, characters: 7, lines: 2 });
  const events = await f.request(`/jobs/${id}/events`, { headers });
  assert.match(await events.text(), /event: status\ndata:.*completed/);
  assert.equal((await f.request('/auth/logout', { method: 'POST', headers })).status, 204);
  assert.equal((await f.request(`/jobs/${id}`, { headers })).status, 401);
});
test('다른 사용자의 작업은 ID를 알아도 조회할 수 없다', async t => {
  const f = await fixture(t), first = await f.signup(), second = await f.signup();
  const r = await f.request('/jobs', { method: 'POST', headers: { authorization: `Bearer ${first}`, 'content-type': 'application/octet-stream' }, body: 'abc' });
  const { id } = await r.json();
  assert.equal((await f.request(`/jobs/${id}`, { headers: { authorization: `Bearer ${second}` } })).status, 404);
  assert.equal((await f.request(`/jobs/${id}/events`, { headers: { authorization: `Bearer ${second}` } })).status, 404);
});
test('오류 응답: JSON, 중복 이메일, 잘못된 로그인, 업로드 크기와 타입', async t => {
  const f = await fixture(t, { maxBytes: 4 });
  const bad = await f.request('/auth/register', { method: 'POST', headers: { 'content-type': 'application/json' }, body: '{' });
  assert.equal(bad.status, 400); assert.equal((await bad.json()).error.code, 'INVALID_JSON');
  const email = `${randomUUID()}@example.test`, token = await f.signup(email);
  assert.equal((await f.json('/auth/register', { email, password: 'long-password-123' })).status, 409);
  assert.equal((await f.json('/auth/login', { email, password: 'wrong-password-123' })).status, 401);
  const auth = { authorization: `Bearer ${token}` };
  assert.equal((await f.request('/jobs', { method: 'POST', headers: auth, body: 'abc' })).status, 415);
  assert.equal((await f.request('/jobs', { method: 'POST', headers: { ...auth, 'content-type': 'application/octet-stream' }, body: '12345' })).status, 413);
  assert.equal((await f.request('/jobs/bad', { headers: auth })).status, 400);
});
test('readiness, draining, 잘못된 경로와 내부 오류 정보 제한', async t => {
  const f = await fixture(t);
  assert.equal((await f.request('/health/ready')).status, 200);
  assert.equal((await f.request('/unknown')).status, 404);
  f.repo.ping = async () => { throw new Error('database-secret'); };
  const r = await f.request('/health/ready'); assert.equal(r.status, 500); assert.doesNotMatch(await r.text(), /database-secret|stack/);
  f.drain(); assert.equal((await f.request('/health/ready')).status, 503);
  assert.equal((await f.request('/health/live')).status, 200);
});
test('요청 제한은 429와 Retry-After를 반환한다', async t => {
  const f = await fixture(t, { authLimit: 1 });
  await f.json('/auth/login', {}); const r = await f.json('/auth/login', {});
  assert.equal(r.status, 429); assert.ok(Number(r.headers.get('retry-after')) > 0);
});
test('fetch는 HTTP 실패와 기한 초과를 호출자에게 전달한다', async t => {
  const f = await fixture(t);
  await assert.rejects(getJson(f.base + '/not-found'), /HTTP 404/);
  assert.deepEqual(await getJson(f.base + '/health/live'), { live: true });
  await assert.rejects(getJson(f.base, { signal: AbortSignal.abort() }), { name: 'AbortError' });
});
test('fetch 기한은 실제 지연 응답을 중단한다', async t => {
  const server = createServer((req, res) => {
    const timer = setTimeout(() => res.end('{}'), 200);
    res.on('close', () => clearTimeout(timer));
  });
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  t.after(async () => { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); });
  await assert.rejects(getJson(`http://127.0.0.1:${server.address().port}`, { timeoutMs: 20 }), { name: 'TimeoutError' });
});
