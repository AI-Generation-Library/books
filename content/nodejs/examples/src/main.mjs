import { createServer } from 'node:http';
import { createApp } from './app.mjs';
import { config, runtime } from './runtime.mjs';
const c = config(); const resources = runtime(c);
const { app, drain } = createApp({ ...resources, root: c.root, log: row => console.log(JSON.stringify(row)) });
const server = createServer({ requestTimeout: 15_000, headersTimeout: 10_000 }, app);
server.on('error', error => { console.error(error.message); process.exitCode = 1; void resources.close(); });
server.listen(c.port, c.host, () => console.log(JSON.stringify({ event: 'listening', port: c.port, mode: c.mode })));
let closing = false;
async function shutdown() {
  if (closing) return; closing = true; drain();
  const deadline = setTimeout(() => { server.closeAllConnections(); process.exit(1); }, 10_000); deadline.unref();
  try { await new Promise(resolve => server.close(resolve)); await resources.close(); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
  finally { clearTimeout(deadline); }
}
process.on('SIGINT', shutdown); process.on('SIGTERM', shutdown);
