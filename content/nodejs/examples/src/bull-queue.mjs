import { Queue, Worker } from 'bullmq';
export function redisOptions(url, worker = false) {
  const u = new URL(url);
  if (u.protocol !== 'redis:' && u.protocol !== 'rediss:') throw new Error('Invalid Redis URL');
  return { host: u.hostname, port: Number(u.port || 6379), db: Number(u.pathname.slice(1) || 0),
    username: decodeURIComponent(u.username) || undefined, password: decodeURIComponent(u.password) || undefined,
    ...(u.protocol === 'rediss:' ? { tls: {} } : {}), maxRetriesPerRequest: worker ? null : 1 };
}
export class BullQueue {
  constructor(url) {
    this.queue = new Queue('file-processing', { connection: redisOptions(url),
      defaultJobOptions: { attempts: 3, backoff: { type: 'exponential', delay: 500 },
        removeOnComplete: { age: 86400 }, removeOnFail: { age: 604800 } } });
    this.queue.on('error', () => {});
  }
  async add(id) { await this.queue.add('count', { id }, { jobId: id }); }
  async ping() { return (await (await this.queue.client).ping()) === 'PONG'; }
  async close() { await this.queue.close(); }
}
export function startWorker(url, repo, processJob) {
  const worker = new Worker('file-processing', async job => {
    try { return await processJob(job.data.id); }
    catch (error) {
      const exhausted = job.attemptsMade + 1 >= (job.opts.attempts || 1);
      await repo.updateJob(job.data.id, exhausted ? 'failed' : 'retrying');
      throw error;
    }
  }, { connection: redisOptions(url, true), concurrency: 2 });
  worker.on('error', error => console.error(JSON.stringify({ event: 'worker_error', name: error.name })));
  return worker;
}
