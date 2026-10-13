import test from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { Readable } from 'node:stream';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { PostgresRepository } from '../src/postgres-repository.mjs';
import { BullQueue, startWorker } from '../src/bull-queue.mjs';
import { storeUpload, processJob } from '../src/files.mjs';
import { dispatch } from '../src/queue.mjs';
test('PostgreSQL outbox → Redis/BullMQ → worker → PostgreSQL result', {
  skip: process.env.NODEBOOK_INTEGRATION !== '1', timeout: 30_000
}, async t => {
  if (!process.env.DATABASE_URL || !process.env.REDIS_URL) throw new Error('Test services are required');
  const repo = new PostgresRepository(process.env.DATABASE_URL), queue = new BullQueue(process.env.REDIS_URL);
  const root = await mkdtemp(join(tmpdir(), 'nodebook-integration-'));
  const uid = randomUUID(), id = randomUUID();
  const worker = startWorker(process.env.REDIS_URL, repo, jobId => processJob(repo, root, jobId));
  t.after(async () => {
    await worker.close();
    await queue.queue.remove(id);
    await queue.close();
    await repo.pool.query('DELETE FROM outbox WHERE job_id=$1', [id]);
    await repo.pool.query('DELETE FROM jobs WHERE id=$1', [id]);
    await repo.pool.query('DELETE FROM users WHERE id=$1', [uid]);
    await repo.close(); await rm(root, { recursive: true, force: true });
  });
  await repo.addUser({ id: uid, email: uid + '@example.test', passwordHash: 'test-only' });
  await repo.createJob({ id, ownerId: uid });
  await storeUpload(Readable.from(['abc\n']), root, id);
  await repo.enqueueJob(id); await dispatch(repo, queue);
  let job;
  for (let i = 0; i < 100; i++) { job = await repo.job(id); if (job.state === 'completed') break; await delay(100); }
  assert.deepEqual(job.result, { bytes: 4, characters: 4, lines: 1 });
  assert.equal(job.state, 'completed');
});
