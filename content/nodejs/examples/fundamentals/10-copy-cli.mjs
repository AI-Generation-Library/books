import { createReadStream, createWriteStream } from 'node:fs';
import { pipeline } from 'node:stream/promises';
const [source, destination] = process.argv.slice(2);
if (!source || !destination) {
  console.error('Usage: node fundamentals/10-copy-cli.mjs source destination'); process.exitCode = 2;
} else {
  try { await pipeline(createReadStream(source), createWriteStream(destination, { flags: 'wx' })); console.log('copied'); }
  catch (error) { console.error(error.code || error.name); process.exitCode = 1; }
}
// 실패 시 부분 파일이 남을 수 있다. 운영용 업로드 구현의 정리 방식은 src/files.mjs를 참고한다.
