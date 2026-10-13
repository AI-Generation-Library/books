import { setTimeout as delay } from 'node:timers/promises';
const first = delay(10, 'A');
const second = delay(5, 'B');
console.log(await Promise.all([first, second])); // 입력 순서: A, B
try { await Promise.reject(new Error('expected')); }
catch (error) { console.log(error.message); }
