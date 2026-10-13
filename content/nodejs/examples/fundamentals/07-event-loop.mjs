import { readFile } from 'node:fs';
console.log('sync');
queueMicrotask(() => console.log('microtask'));
Promise.resolve().then(() => console.log('promise'));
process.nextTick(() => console.log('nextTick'));
readFile(new URL(import.meta.url), () => {
  setTimeout(() => console.log('io:timeout'), 0);
  setImmediate(() => console.log('io:immediate'));
});
// ESM의 최상위 평가 문맥과 I/O 콜백의 문맥을 구분한다.
