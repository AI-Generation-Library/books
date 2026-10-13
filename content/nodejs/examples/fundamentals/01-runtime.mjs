import { version, versions, platform } from 'node:process';
console.log({ version, v8: versions.v8, uv: versions.uv, platform });
console.log(typeof document, typeof fetch); // undefined function
