import { resolve } from 'node:path';
import { MemoryRepository } from './memory-repository.mjs';
import { PostgresRepository } from './postgres-repository.mjs';
import { MemoryQueue, dispatcher } from './queue.mjs';
import { BullQueue } from './bull-queue.mjs';
import { processJob } from './files.mjs';
export function config(env = process.env) {
  const mode = env.MODE || 'memory';
  if (!['memory', 'production'].includes(mode)) throw new Error('MODE must be memory or production');
  if (mode === 'production' && (!env.DATABASE_URL || !env.REDIS_URL)) throw new Error('DATABASE_URL and REDIS_URL are required');
  const port = Number(env.PORT || 3000);
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Invalid PORT');
  return { mode, port, host: env.HOST || '127.0.0.1', root: resolve(env.UPLOAD_DIR || 'var/uploads') };
}
export function runtime(c, env = process.env) {
  const repo = c.mode === 'memory' ? new MemoryRepository() : new PostgresRepository(env.DATABASE_URL);
  const queue = c.mode === 'memory' ? new MemoryQueue(id => processJob(repo, c.root, id), repo) : new BullQueue(env.REDIS_URL);
  const stop = dispatcher(repo, queue, error => console.error(JSON.stringify({ event: 'dispatch_error', name: error.name })));
  return { repo, queue, async close() { await stop(); await queue.close(); await repo.close(); } };
}
