import test from 'node:test';
import assert from 'node:assert/strict';
import { Worker } from 'node:worker_threads';
import { once } from 'node:events';
test('Worker Threads는 메시지로 계산 결과를 전달한다', async () => {
  const worker = new Worker(new URL('../fundamentals/25-worker.mjs', import.meta.url), { workerData: 20 });
  const [result] = await once(worker, 'message'); assert.equal(result, 6765);
  await worker.terminate();
});
test('작업 입력 제한 위반은 error로 전달된다', async () => {
  const worker = new Worker(new URL('../fundamentals/25-worker.mjs', import.meta.url), { workerData: 99 });
  const [error] = await once(worker, 'error'); assert.match(error.message, /0..35/);
});
