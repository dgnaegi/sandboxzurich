// Static server for sweeps: code from a frozen dist snapshot, data (tiles, textures, models) live from web/public.
// node tests/sweep_server.mjs <distDir> [port=5199]
import http from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { extname, join, normalize } from 'node:path';
const dist = process.argv[2], port = Number(process.argv[3] ?? 5199);
const pub = new URL('../public/', import.meta.url).pathname;
const T = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.css': 'text/css', '.ktx2': 'image/ktx2', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.woff2': 'font/woff2', '.wasm': 'application/wasm' };
http.createServer((q, r) => {
  const u = normalize(decodeURIComponent(q.url.split('?')[0])).replace(/^(\.\.[/\\])+/, '');
  const live = /^\/(tiles|data|tex|models|map)\//.test(u);
  const cands = (live ? [pub, dist] : [dist, pub]).map((d) => join(d, u === '/' ? 'index.html' : u));
  const f = cands.find((c) => existsSync(c) && statSync(c).isFile());
  if (!f) { r.writeHead(404); r.end(); return; }
  r.writeHead(200, { 'content-type': T[extname(f)] ?? 'application/octet-stream', 'cache-control': 'no-store' });
  createReadStream(f).pipe(r);
}).listen(port, () => console.log('sweep server on', port));
