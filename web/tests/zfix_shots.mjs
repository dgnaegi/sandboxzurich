// HUD names + flea market: node tests/zfix_shots.mjs -> ../preview/zfix_<name>.jpg
import { chromium } from 'playwright';
const OUT = new URL('../../preview/', import.meta.url).pathname;
const PTS = { limmatplatz: [1131, 74, 5, 15], stauffacher: [991, -1182, 4, 15], hardplatz: [-102, -206, 4, 15], hb: [1700, -640, 4, 15], hardbruecke: [56, 118, 4, 15], langstrasse: [758, -704, 4, 15], flohmarkt: [690, -940, 5, 11] };
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const page = await (await browser.newContext({ viewport: { width: 800, height: 450 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
for (const [n, [x, y, day, h]] of Object.entries(PTS)) {
  await page.goto(`http://localhost:5173/?at=${x},${y}&day=${day}&t=${h}:00`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.waitForTimeout(n === 'flohmarkt' ? 9000 : 3500);
  console.log(n, '|', await page.textContent('#place-name'), '|', await page.textContent('#place-kreis'), n === 'flohmarkt' ? await page.evaluate(() => window.sbxEvents.group.children.length) : '');
  await page.screenshot({ path: `${OUT}zfix_${n}.jpg`, type: 'jpeg', quality: 70 });
}
await browser.close();
