import { mkdtemp, writeFile, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const directory = await mkdtemp(join(tmpdir(), 'nodebook-'));
try {
  const filename = join(directory, 'note.txt');
  await writeFile(filename, '안녕 Node.js\n', 'utf8');
  console.log((await readFile(filename, 'utf8')).trim());
} finally { await rm(directory, { recursive: true, force: true }); }
