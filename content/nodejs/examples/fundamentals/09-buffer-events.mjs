import { EventEmitter } from 'node:events';
const b = Buffer.from('노드');
console.log('노드'.length, b.length); // 2 6
const bus = new EventEmitter();
bus.once('done', value => console.log(value));
bus.emit('done', 'first'); bus.emit('done', 'ignored');
