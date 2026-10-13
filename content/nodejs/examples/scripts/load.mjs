import { performance } from 'node:perf_hooks';
const target = process.env.TARGET_URL || 'http://127.0.0.1:3000/health/live';
const total = Number(process.env.REQUESTS || 100), concurrency = Number(process.env.CONCURRENCY || 4);
if (!Number.isInteger(total) || total < 1 || total > 10_000 || !Number.isInteger(concurrency) || concurrency < 1 || concurrency > 32) {
  throw new Error('REQUESTS=1..10000, CONCURRENCY=1..32');
}
const u = new URL(target);
if (!['localhost', '127.0.0.1', '[::1]'].includes(u.hostname)) throw new Error('This teaching tool accepts localhost targets only');
let next = 0, errors = 0; const durations = [];
const start = performance.now();
await Promise.all(Array.from({ length: concurrency }, async () => {
  while (next++ < total) {
    const tick = performance.now();
    try {
      const response = await fetch(target, { signal: AbortSignal.timeout(3000) });
      await response.arrayBuffer();
      if (!response.ok) errors++;
    } catch { errors++; }
    durations.push(performance.now() - tick);
  }
}));
const elapsed = performance.now() - start;
durations.sort((a, b) => a - b);
const percentile = p => Number(durations[Math.min(durations.length - 1, Math.ceil(durations.length * p) - 1)].toFixed(2));
console.log(JSON.stringify({ model: 'closed-loop', total, concurrency, errors, elapsedMs: Number(elapsed.toFixed(2)),
  requestsPerSecond: Number((total / elapsed * 1000).toFixed(2)), p50Ms: percentile(.5), p95Ms: percentile(.95), p99Ms: percentile(.99) }, null, 2));
if (errors) process.exitCode = 1;
