export class MemoryQueue {
  constructor(process, repo, capacity = 32) { this.process = process; this.repo = repo; this.capacity = capacity; this.active = new Map(); this.closed = false; }
  async add(id) {
    if (this.active.has(id)) return;
    if (this.closed || this.active.size >= this.capacity) throw new Error('queue capacity');
    // 호출 뒤 dispatched가 실행되기 전에 reject하지 않도록 작업을 Promise로 분리한다.
    const task = Promise.resolve().then(() => this.process(id)).catch(async () => {
      await this.repo.updateJob(id, 'failed');
    }).catch(() => {}).finally(() => this.active.delete(id));
    this.active.set(id, task);
  }
  async ping() { return !this.closed; }
  async close() { this.closed = true; await Promise.allSettled(this.active.values()); }
}
export async function dispatch(repo, queue) {
  for (const id of await repo.pending()) { await queue.add(id); await repo.dispatched(id); }
}
// setInterval의 비동기 작업 중첩을 피한다.
export function dispatcher(repo, queue, onError = () => {}, intervalMs = 250) {
  let stopped = false, timer, running = Promise.resolve();
  function tick() {
    running = dispatch(repo, queue).catch(onError).finally(() => {
      if (!stopped) { timer = setTimeout(tick, intervalMs); timer.unref(); }
    });
  }
  tick();
  return async () => { stopped = true; clearTimeout(timer); await running; };
}
