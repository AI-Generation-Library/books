// producer가 입력 전체를 미리 Promise로 만들지 않도록 worker가 항목을 가져간다.
export async function mapLimit(items, concurrency, fn, { signal } = {}) {
  if (!Number.isInteger(concurrency) || concurrency < 1) throw new RangeError('Invalid concurrency');
  let next = 0, stopped = false;
  const results = new Array(items.length);
  async function run() {
    while (!stopped) {
      signal?.throwIfAborted();
      const i = next++;
      if (i >= items.length) return;
      try { results[i] = await fn(items[i], i, signal); }
      catch (error) { stopped = true; throw error; }
    }
  }
  const workers = await Promise.allSettled(Array.from({ length: Math.min(concurrency, items.length) }, run));
  const failed = workers.find(x => x.status === 'rejected');
  if (failed) throw failed.reason;
  return results;
}
