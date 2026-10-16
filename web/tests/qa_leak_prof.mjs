// QA: sampling heap profile of live allocations after N teleports (finds the leaking call sites)
import { chromium } from 'playwright';
const BASE = process.argv[2] ?? 'http://localhost:5199';
const b = await chromium.launch({ args: ['--js-flags=--expose-gc', '--use-gl=angle', '--enable-precise-memory-info'] });
const ctx = await b.newContext({ viewport: { width: 1280, height: 720 } });
const page = await ctx.newPage();
await page.goto(`${BASE}/?at=789,-873,0&t=12:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
const cdp = await ctx.newCDPSession(page);
await cdp.send('HeapProfiler.enable');
await cdp.send('HeapProfiler.startSampling', { samplingInterval: 8192 });
const pts = [[789, -873], [58, 117], [-491, -690]];
for (let i = 0; i < 9; i++) {
  const [x, y] = pts[i % 3];
  await page.evaluate(async ([x, y]) => { await window.sbxTiles.update(x, y); window.sbxPlayer.teleport(x, y, 0); }, [x, y]);
  await page.waitForTimeout(3000);
}
await cdp.send('HeapProfiler.collectGarbage');
const { profile } = await cdp.send('HeapProfiler.getSamplingProfile');
const acc = new Map();
(function walk(n) { const f = n.callFrame; const k = `${f.functionName || '(anon)'} ${f.url.split('/').slice(-2).join('/')}:${f.lineNumber}`; acc.set(k, (acc.get(k) ?? 0) + n.selfSize); n.children.forEach(walk); })(profile.head);
const paths = [];
(function walk(n, st) { const f = n.callFrame; const nm = `${f.functionName || '(anon)'}@${f.url.split('/').slice(-1)[0].replace(/\?.*/, '')}:${f.lineNumber}`; const s2 = [...st, nm]; if (n.selfSize > 0) paths.push([n.selfSize, s2.slice(-6).join(' < ')]); n.children.forEach((c) => walk(c, s2)); })(profile.head, []);
if (process.argv[3]) { const m = new Map(); for (const [sz, p] of paths) m.set(p, (m.get(p) ?? 0) + sz); for (const [p, v] of [...m].sort((a, c) => c[1] - a[1]).slice(0, 12)) console.log((v / 1e6).toFixed(1), p); }
const rows = [...acc].sort((a, c) => c[1] - a[1]).slice(0, 25);
for (const [k, v] of rows) console.log((v / 1e6).toFixed(1).padStart(7), 'MB', k);
await b.close();
