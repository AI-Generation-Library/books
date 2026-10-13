import { parentPort, workerData } from 'node:worker_threads';
function fib(n) { return n < 2 ? n : fib(n - 1) + fib(n - 2); }
if (!Number.isInteger(workerData) || workerData < 0 || workerData > 35) throw new RangeError('n must be 0..35');
parentPort.postMessage(fib(workerData));
