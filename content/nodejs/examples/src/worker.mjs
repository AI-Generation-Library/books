import { config } from './runtime.mjs';
import { PostgresRepository } from './postgres-repository.mjs';
import { processJob } from './files.mjs';
import { startWorker } from './bull-queue.mjs';
const c = config();
if (c.mode !== 'production') throw new Error('Separate worker requires MODE=production');
const repo = new PostgresRepository(process.env.DATABASE_URL);
const worker = startWorker(process.env.REDIS_URL, repo, id => processJob(repo, c.root, id));
let closing = false;
async function shutdown() {
  if (closing) return; closing = true;
  const deadline = setTimeout(() => process.exit(1), 10_000); deadline.unref();
  try { await worker.close(); await repo.close(); } finally { clearTimeout(deadline); }
}
process.on('SIGINT', shutdown); process.on('SIGTERM', shutdown);
