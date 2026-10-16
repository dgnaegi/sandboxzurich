// Bytes transferred until ready, grouped by folder (prod preview). node tests/netsize_prod.mjs [base]
import { chromium, devices } from 'playwright';
import { gzipSync } from 'node:zlib';
const BASE = process.argv[2] ?? 'http://localhost:4173';
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const ctx = await b.newContext({ ...devices['iPhone 13'], viewport: { width: 844, height: 390 } });
const p = await ctx.newPage();
const by = {}, gz = {};
p.on('response', async (r) => {
  try { const buf = await r.body(); const u = new URL(r.url()); const k = u.pathname.split('/').slice(0, 3).join('/'); by[k] = (by[k] ?? 0) + buf.length; gz[k] = (gz[k] ?? 0) + gzipSync(buf, { level: 6 }).length; } catch { /* redirects */ }
});
await p.goto(`${BASE}/?at=785,-635,0.37`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
if (!process.env.AFTER) { } else await p.waitForTimeout(4000);
const tot = Object.values(by).reduce((a, c) => a + c, 0);
const tg = Object.values(gz).reduce((a, c) => a + c, 0);
console.log('total MB raw', (tot / 1e6).toFixed(1), '| gzip', (tg / 1e6).toFixed(1));
for (const [k, v] of Object.entries(by).sort((a, c) => c[1] - a[1]).slice(0, 24)) console.log((v / 1e6).toFixed(2).padStart(7), (gz[k] / 1e6).toFixed(2).padStart(6), k);
await b.close();
