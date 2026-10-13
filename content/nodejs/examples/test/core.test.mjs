import test from 'node:test';
import assert from 'node:assert/strict';
import { Readable } from 'node:stream';
import { mkdtemp, rm, readdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
import { storeUpload, countFile, processJob } from '../src/files.mjs';
import { hashPassword, checkPassword, tokenHash, credentials } from '../src/security.mjs';
import { MemoryRepository } from '../src/memory-repository.mjs';
import { MemoryQueue, dispatch } from '../src/queue.mjs';
import { mapLimit } from '../src/map-limit.mjs';
import { config } from '../src/runtime.mjs';

async function temp(t) {
  const root = await mkdtemp(join(tmpdir(), 'nodebook-test-'));
  t.after(() => rm(root, { recursive: true, force: true })); return root;
}
test('UTF-8 코드포인트가 청크 경계에 걸려도 정확히 센다', async t => {
  const root = await temp(t), id = randomUUID(), b = Buffer.from('안녕🙂\nNode\n');
  await storeUpload(Readable.from([...b].map(byte => Buffer.from([byte]))), root, id);
  assert.deepEqual(await countFile(root, id), { bytes: b.length, characters: 9, lines: 2 });
});
test('빈 파일과 마지막 개행이 없는 파일의 줄 수', async t => {
  const root = await temp(t);
  for (const [text, lines] of [['', 0], ['a', 1], ['a\n', 1], ['\n\n', 2]]) {
    const id = randomUUID(); await storeUpload(Readable.from([text]), root, id);
    assert.equal((await countFile(root, id)).lines, lines);
  }
});
test('초과 파일의 부분 데이터를 지운다', async t => {
  const root = await temp(t), id = randomUUID();
  await assert.rejects(storeUpload(Readable.from([Buffer.alloc(10)]), root, id, 4), { status: 413 });
  assert.deepEqual(await readdir(root), []);
});
test('같은 ID 파일이 이미 있으면 실패하되 기존 파일을 보존한다', async t => {
  const root = await temp(t), id = randomUUID();
  await storeUpload(Readable.from(['old']), root, id);
  await assert.rejects(storeUpload(Readable.from(['new-data']), root, id), { code: 'EEXIST' });
  assert.deepEqual(await countFile(root, id), { bytes: 3, characters: 3, lines: 1 });
});
test('만료 세션을 인증하지 않는다', async () => {
  const repo = new MemoryRepository();
  await repo.addSession('expired', 'user', Date.now() - 1);
  assert.equal(await repo.session('expired'), null);
});
test('경로 조작과 잘못된 UTF-8 거부', async t => {
  const root = await temp(t), id = randomUUID();
  await assert.rejects(storeUpload(Readable.from(['a']), root, '../bad'), { status: 400 });
  await storeUpload(Readable.from([Buffer.from([0xff])]), root, id);
  await assert.rejects(countFile(root, id), TypeError);
});
test('비밀번호 해시와 자격 증명 검증', async () => {
  const hash = await hashPassword('long-password-123');
  assert.equal(await checkPassword('long-password-123', hash), true);
  assert.equal(await checkPassword('wrong-password-123', hash), false);
  assert.notEqual(await hashPassword('long-password-123'), hash);
  assert.equal(tokenHash('a').length, 64);
  assert.throws(() => credentials({ email: 'a b@c.d', password: 'long-password-123' }), { status: 400 });
  assert.throws(() => credentials({ email: 'user@example.test', password: '🙂'.repeat(6) }), { status: 400 });
  assert.equal(credentials({ email: 'USER@example.test', password: 'long-password-123' }).email, 'user@example.test');
});
test('제한된 동시 실행과 입력 순서', async () => {
  let active = 0, max = 0;
  const result = await mapLimit([4, 3, 2, 1], 2, async n => { active++; max = Math.max(max, active); await delay(n); active--; return n * 2; });
  assert.equal(max, 2); assert.deepEqual(result, [8, 6, 4, 2]);
});
test('작업 실패 이후 새 작업 시작을 멈추고 실행 중 작업을 정리한다', async () => {
  const started = [];
  await assert.rejects(mapLimit([0, 1, 2, 3], 2, async n => { started.push(n); if (n === 0) throw new Error('failed'); await delay(5); }), /failed/);
  assert.deepEqual(started, [0, 1]);
});
test('취소 신호와 잘못된 동시 실행 수', async () => {
  await assert.rejects(mapLimit([1], 1, async n => n, { signal: AbortSignal.abort() }), { name: 'AbortError' });
  await assert.rejects(mapLimit([1], 0, async n => n), RangeError);
});
test('outbox 전달과 완료 작업의 멱등성', async t => {
  const root = await temp(t), repo = new MemoryRepository(), id = randomUUID();
  await repo.createJob({ id, ownerId: randomUUID() });
  await storeUpload(Readable.from(['abc']), root, id); await repo.enqueueJob(id);
  const queue = new MemoryQueue(jobId => processJob(repo, root, jobId), repo);
  await dispatch(repo, queue); await queue.close();
  assert.deepEqual(await repo.pending(), []); assert.equal((await repo.job(id)).state, 'completed');
  await processJob(repo, root, id); await repo.updateJob(id, 'failed');
  assert.equal((await repo.job(id)).state, 'completed');
});
test('전송 실패 시 outbox에 남긴다', async () => {
  const repo = new MemoryRepository(), id = randomUUID(); await repo.createJob({ id }); await repo.enqueueJob(id);
  await assert.rejects(dispatch(repo, { add: async () => { throw new Error('offline'); } }), /offline/);
  assert.deepEqual(await repo.pending(), [id]);
});
test('설정은 누락되거나 잘못되면 시작에 실패한다', () => {
  assert.throws(() => config({ MODE: 'production' }), /required/);
  assert.throws(() => config({ PORT: 'NaN' }), /PORT/);
});
