import { createServer } from 'node:http';
import { once } from 'node:events';
const server = createServer((req, res) => {
  if (req.method !== 'GET' || req.url !== '/hello') { res.writeHead(404).end(); return; }
  const data = Buffer.from(JSON.stringify({ message: '안녕' }));
  res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': data.length });
  res.end(data);
});
server.listen(0, '127.0.0.1'); await once(server, 'listening');
try { const r = await fetch(`http://127.0.0.1:${server.address().port}/hello`); console.log(r.status, await r.json()); }
finally { await new Promise(resolve => server.close(resolve)); }
