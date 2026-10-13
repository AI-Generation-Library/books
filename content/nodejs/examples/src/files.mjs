import { createReadStream, createWriteStream } from 'node:fs';
import { mkdir, unlink } from 'node:fs/promises';
import { join } from 'node:path';
import { Transform } from 'node:stream';
import { pipeline } from 'node:stream/promises';
import { HttpError, requireId } from './errors.mjs';

export const filePath = (root, id) => join(root, requireId(id) + '.txt');
export async function storeUpload(readable, root, id, maxBytes = 1024 * 1024) {
  await mkdir(root, { recursive: true });
  const destination = filePath(root, id);
  let size = 0;
  const limit = new Transform({ transform(chunk, encoding, callback) {
    size += chunk.length;
    callback(size > maxBytes ? new HttpError(413, 'FILE_TOO_LARGE', '파일 크기를 초과했습니다.') : null, chunk);
  } });
  let created = false;
  const output = createWriteStream(destination, { flags: 'wx', mode: 0o600 });
  output.once('open', () => { created = true; });
  try { await pipeline(readable, limit, output); }
  catch (error) { if (created) await unlink(destination).catch(() => {}); throw error; }
  return size;
}

export async function countFile(root, id) {
  const input = createReadStream(filePath(root, id));
  // fatal=true: UTF-8이 아닌 바이너리를 조용히 치환하지 않는다.
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let characters = 0, bytes = 0, newlines = 0, last = '', nonempty = false;
  function consume(text) {
    if (!text) return;
    nonempty = true; last = text.at(-1);
    characters += [...text].length;
    for (const ch of text) if (ch === '\n') newlines++;
  }
  for await (const chunk of input) { bytes += chunk.length; consume(decoder.decode(chunk, { stream: true })); }
  consume(decoder.decode());
  return { bytes, characters, lines: newlines + (nonempty && last !== '\n' ? 1 : 0) };
}
export async function processJob(repo, root, id) {
  const job = await repo.job(id);
  if (!job || job.state === 'completed') return;
  await repo.updateJob(id, 'processing');
  const result = await countFile(root, id);
  await repo.updateJob(id, 'completed', result);
  return result;
}
