import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
const base = process.env.BASE_URL || 'http://127.0.0.1:3000';
const body = { email: `${randomUUID()}@example.test`, password: 'long-password-123' };
const json = data => ({ method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(data) });
assert.equal((await fetch(base + '/auth/register', json(body))).status, 201);
const login = await fetch(base + '/auth/login', json(body)); assert.equal(login.status, 200);
const { token } = await login.json(); const headers = { authorization: `Bearer ${token}` };
const response = await fetch(base + '/jobs', { method: 'POST', headers: { ...headers, 'content-type': 'application/octet-stream' }, body: '안녕\nNode' });
assert.equal(response.status, 202); const { id } = await response.json();
let result;
for (let i = 0; i < 100; i++) {
  const r = await fetch(`${base}/jobs/${id}`, { headers }); assert.equal(r.status, 200); result = await r.json();
  if (['completed', 'failed'].includes(result.state)) break; await delay(100);
}
assert.equal(result.state, 'completed'); assert.deepEqual(result.result, { bytes: 11, characters: 7, lines: 2 });
assert.equal((await fetch(base + '/auth/logout', { method: 'POST', headers })).status, 204);
console.log(JSON.stringify({ smoke: 'passed', result: result.result }));
// 데모 데이터는 생성된다. production 모드라면 검증 전용 DB/파일 볼륨을 사용한다.
