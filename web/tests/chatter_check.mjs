// QA: speech-bubble lines (ui/chatter.ts). Samples chatLine() per mode/time in the real page and checks that the owner
// lines show up in a plain context, that scooter -> "Hesch Termin?" and car -> "Voll wüests Auto." appear, that nothing
// from RESERVE (unvetted lines) ever appears, that no line exceeds 72 chars and that no Hochdeutsch leftovers remain
// ("Guten Tag", "Schönen", "ich muss"); then shows the longest line in the bubble on a phone portrait viewport and
// screenshots it -> preview/chatter_bubble_phoneP.jpg. Usage: node tests/chatter_check.mjs [base]
import { launch, open, OUT } from './qa_lib.mjs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const b = await launch();
let fails = 0;
const check = (name, ok, extra = '') => { console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${extra ? '  ' + extra : ''}`); if (!ok) fails++; };
const { ctx, page } = await open(b, 'phoneP', `${BASE}/?at=789,-873,0.3&t=12:00&nohelp&nopost`);
const { sample, reserve } = await page.evaluate(async () => {
  const m = await import('/src/ui/chatter.ts');
  const out = {};
  const ctxs = {
    plain: { place: '', min: 15 * 60, day: 2, night: false, mode: 'foot' },
    scooter: { place: 'Langstrasse', min: 12 * 60, day: 2, night: false, mode: 'scooter' },
    car: { place: 'Hardbrücke', min: 18 * 60, day: 4, night: false, mode: 'car' },
    bike: { place: 'Helvetiaplatz', min: 8 * 60, day: 0, night: false, mode: 'bike' },
    night: { place: 'Langstrasse', min: 23 * 60, day: 5, night: true, mode: 'foot' },
    sunday: { place: 'Bäckeranlage', min: 10 * 60, day: 6, night: false, mode: 'run' },
    transit: { place: 'Stauffacher', min: 15 * 60, day: 1, night: false, mode: 'transit' },
  };
  for (const [k, c] of Object.entries(ctxs)) {
    const n = {};
    for (let i = 0; i < 3000; i++) { const l = m.chatLine(c); n[l] = (n[l] ?? 0) + 1; }
    out[k] = Object.entries(n).sort((a, b) => b[1] - a[1]);
  }
  const r = m.RESERVE, flat = [...r.generic, ...r.cliche, ...r.morning, ...r.noon, ...r.evening, ...r.night, ...r.weekend, ...r.sunday, ...Object.values(r.mode).flat(), ...Object.values(r.place).flat()];
  return { sample: out, reserve: flat };
});
const all = new Set(Object.values(sample).flat().map(([l]) => l));
const longest = [...all].sort((a, b) => b.length - a.length)[0];
const OWNER = ['So en Lappe!', 'Bisch scho imne Verein?', 'Angst und Geld hani kei.', 'Hey, gömmer Bulle go schlah?', 'Multipli hundert.', 'Chatsy.', 'Hey, I just moved here from California, can I join your inner circle?'];
const plain = new Map(sample.plain);
check('owner lines all appear in a plain context', OWNER.every((l) => (plain.get(l) ?? 0) > 50), OWNER.map((l) => `${l.slice(0, 14)}… ${plain.get(l) ?? 0}`).join(' · '));
check('scooter says "Hesch Termin?" often', (sample.scooter.find(([l]) => l === 'Hesch Termin?')?.[1] ?? 0) > 200, `${sample.scooter[0][0]} ×${sample.scooter[0][1]} of 3000`);
check('car says "Voll wüests Auto." often', (sample.car.find(([l]) => l === 'Voll wüests Auto.')?.[1] ?? 0) > 200, sample.car.slice(0, 3).map(([l]) => l).join(' | '));
const leaked = reserve.filter((l) => all.has(l));
check('no RESERVE line is active', leaked.length === 0, leaked.slice(0, 3).join(' | '));
check('night lines appear', sample.night.some(([l]) => /Füür|Nacht|Abig/.test(l)));
check('no line longer than 72 chars', longest.length <= 72, `${longest.length}: ${longest}`);
const hochdeutsch = [...all].filter((l) => /\b(Guten|Schönen|ich muss|nicht|noch mal|heute|Entschuldigung)\b/i.test(l));
check('no Hochdeutsch leftovers', hochdeutsch.length === 0, hochdeutsch.slice(0, 3).join(' | '));
console.log(`active distinct lines: ${all.size}; reserve: ${reserve.length}; top plain: ${sample.plain.slice(0, 4).map(([l, n]) => `${l} (${n})`).join(' · ')}`);
// the game loop hides the bubble every frame unless a passer-by is close: pause it with the menu, then show the longest line
await page.click('#btn-menu'); await page.waitForTimeout(200);
await page.evaluate((t) => { const e = document.getElementById('bubble'); e.textContent = t; e.style.display = 'block'; e.style.left = '50%'; e.style.top = '45%'; e.style.zIndex = '30'; }, longest);
await page.waitForTimeout(200);
const box = await page.evaluate(() => { const r = document.getElementById('bubble').getBoundingClientRect(); return { l: r.left, r: r.right, w: innerWidth, lines: Math.round(r.height / 17.5) }; });
check('bubble stays on screen (phone portrait)', box.r - box.l > 100 && box.l >= 0 && box.r <= box.w, `${Math.round(box.l)}..${Math.round(box.r)} of ${box.w}px, ~${box.lines} lines`);
await page.screenshot({ path: `${OUT}chatter_bubble_phoneP.jpg`, type: 'jpeg', quality: 60 });
await ctx.close();
await b.close();
console.log(fails ? `CHATTER FAIL ${fails}` : 'CHATTER OK');
process.exit(fails ? 1 : 0);
