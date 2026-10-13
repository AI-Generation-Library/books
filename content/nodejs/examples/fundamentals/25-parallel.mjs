import { Worker } from 'node:worker_threads';
import { pathToFileURL } from 'node:url';
export function fibWorker(n) {
  return new Promise((resolve, reject) => {
    const worker = new Worker(new URL('./25-worker.mjs', import.meta.url), { workerData: n });
    worker.once('message', resolve); worker.once('error', reject);
    worker.once('exit', code => { if (code !== 0) reject(new Error(`Worker exited ${code}`)); });
  });
}
if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  console.log(await fibWorker(20));
}
