import { monitorEventLoopDelay, performance } from 'node:perf_hooks';
import { setTimeout as delay } from 'node:timers/promises';
const histogram = monitorEventLoopDelay({ resolution: 10 }); histogram.enable();
await delay(20);
const start = performance.now(); while (performance.now() - start < 40) { /* 의도적인 CPU 부하 */ }
await delay(20); histogram.disable();
console.log({ p99Ms: histogram.percentile(99) / 1e6, memory: process.memoryUsage() });
