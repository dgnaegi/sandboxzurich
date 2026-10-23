// Glitch sweep: teleports through viewpoints, 4 directions each, low-res shots -> shot dir; sheets built by python (see research/sweep).
// node tests/glitch_sweep.mjs <pointsJson> <outDir> [from] [to]
import { chromium } from 'playwright';
import { readFileSync, mkdirSync } from 'node:fs';
const pts = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const out = process.argv[3]; mkdirSync(out, { recursive: true });
const from = +(process.argv[4] ?? 0), to = +(process.argv[5] ?? pts.length);
const W = 400, H = 225;
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on('pageerror', (e) => console.log('pageerror', e.message));
const p0 = pts[from];
await page.goto(`http://localhost:5173/?at=${p0.x},${p0.y},0&t=13:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
await page.addStyleTag({ content: 'body > *:not(canvas):not(script){display:none !important}' });
for (let i = from; i < to; i++) {
  const p = pts[i];
  const [fx, fy] = p.exact ? [p.x, p.y] : await page.evaluate(([x, y]) => window.sbxFindSpot(x, y), [p.x, p.y]);
  for (let d = 0; d < 4; d++) {
    const yaw = (p.yaw ?? 0) + d * Math.PI / 2;
    await page.evaluate(([x, y, yw, z]) => { const P = window.sbxPlayer; P.teleport(x, y, yw); if (z != null) P.z = z; }, [fx, fy, yaw, p.z ?? null]);
    await page.waitForTimeout(d === 0 ? 2200 : 700);
    await page.screenshot({ path: `${out}/p${String(i).padStart(3, '0')}_${d}.jpg`, type: 'jpeg', quality: 80 });
  }
  console.log(i, p.name, fx.toFixed(0), fy.toFixed(0));
}
await browser.close();
