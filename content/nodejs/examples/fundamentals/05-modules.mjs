import legacy from './05-legacy.cjs';
console.log(legacy.add(2, 3));
console.log(new URL('./05-legacy.cjs', import.meta.url).protocol);
