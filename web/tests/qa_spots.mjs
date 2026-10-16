// QA: screenshots of listed spots: node qa_spots.mjs BASE name:x,y,yaw,t ...   (output preview/qa_review_spot_<name>.jpg, phone landscape or pc via VP env)
import { launch, open, OUT } from './qa_lib.mjs';
const BASE = process.argv[2]; const vp = process.env.VP ?? 'pc';
const b = await launch();
const { page } = await open(b, vp, `${BASE}/?at=0,0,0&nopost`, { wait: false });
await page.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
for (const a of process.argv.slice(3)) {
  const [name, rest] = a.split(':'); const [x, y, yaw = 0, t = '12:00'] = rest.split(',');
  await page.evaluate(async ([x, y, yaw, t]) => { await window.sbxTiles.update(+x, +y); window.sbxPlayer.teleport(+x, +y, +yaw); { const [h, m] = t.split(':').map(Number); window.sbxClock.paused = true; window.sbxClock.min = h * 60 + (m || 0); window.sbxClock.onChange(); } }, [x, y, yaw, t]);
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `${OUT}qa_review_spot_${name}.jpg`, type: 'jpeg', quality: 60 });
}
await b.close();
