/** GTA-style map blips: dark disc, white rim, simple white glyph. Shared by the big map labels and the legend icons. */
export type BlipKind = 'lm' | 'school' | 'church' | 'hospital' | 'culture' | 'civic' | 'bld' | 'stop' | 'station';

export const BLIP_NAMES: [BlipKind, string][] = [
  ['lm', 'Wahrzeichen'], ['school', 'Schule'], ['church', 'Kirche / Synagoge'], ['hospital', 'Spital'],
  ['culture', 'Kultur'], ['civic', 'Behörde'], ['station', 'Bahnhof'], ['stop', 'Tramhaltestelle'],
];
const FILL: Partial<Record<BlipKind, string>> = { lm: '#7a1b1b', hospital: '#9a1f1f', station: '#b3262d' };

function glyph(g: CanvasRenderingContext2D, k: BlipKind, r: number) {
  g.fillStyle = '#fff'; g.strokeStyle = '#fff'; g.lineWidth = Math.max(1, r * 0.2); g.lineJoin = 'miter'; g.lineCap = 'butt';
  g.beginPath();
  if (k === 'lm') { for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.32 : r * 0.68; g.lineTo(Math.cos(a) * rr, Math.sin(a) * rr + r * 0.03); } g.closePath(); g.fill(); }
  else if (k === 'church') { g.rect(-r * 0.12, -r * 0.62, r * 0.24, r * 1.24); g.rect(-r * 0.4, -r * 0.28, r * 0.8, r * 0.24); g.fill(); }
  else if (k === 'hospital') { g.rect(-r * 0.14, -r * 0.55, r * 0.28, r * 1.1); g.rect(-r * 0.55, -r * 0.14, r * 1.1, r * 0.28); g.fill(); }
  else if (k === 'school') { g.moveTo(0, -r * 0.55); g.lineTo(r * 0.7, -r * 0.18); g.lineTo(0, r * 0.2); g.lineTo(-r * 0.7, -r * 0.18); g.closePath(); g.moveTo(-r * 0.4, 0.05 * r); g.lineTo(-r * 0.4, r * 0.4); g.lineTo(0, r * 0.58); g.lineTo(r * 0.4, r * 0.4); g.lineTo(r * 0.4, 0.05 * r); g.lineTo(0, r * 0.28); g.closePath(); g.fill(); }
  else if (k === 'culture') { g.moveTo(-r * 0.62, -r * 0.18); g.lineTo(0, -r * 0.62); g.lineTo(r * 0.62, -r * 0.18); g.closePath(); g.rect(-r * 0.5, -r * 0.08, r * 0.22, r * 0.56); g.rect(-r * 0.11, -r * 0.08, r * 0.22, r * 0.56); g.rect(r * 0.28, -r * 0.08, r * 0.22, r * 0.56); g.fill(); }
  else if (k === 'civic') { g.rect(-r * 0.5, -r * 0.5, r * 0.12, r * 1.05); g.rect(-r * 0.38, -r * 0.5, r * 0.85, r * 0.5); g.fill(); }
  else if (k === 'station') { g.font = `800 ${r * 1.25}px Barlow, sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('S', 0, r * 0.06); }
  else if (k === 'stop') { g.roundRect(-r * 0.5, -r * 0.55, r, r * 0.95, r * 0.18); g.fill(); g.fillStyle = '#1a1612'; g.fillRect(-r * 0.32, -r * 0.38, r * 0.64, r * 0.34); g.fillStyle = '#fff'; g.fillRect(-r * 0.5, r * 0.5, r, r * 0.14); }
  else { g.arc(0, 0, r * 0.3, 0, 7); g.fill(); }
}

/** Draw a blip centred at x,y with outer radius r (CSS px). */
export function drawBlip(g: CanvasRenderingContext2D, k: BlipKind, x: number, y: number, r: number) {
  g.save(); g.translate(x, y);
  g.beginPath();
  if (k === 'station') g.roundRect(-r, -r, r * 2, r * 2, r * 0.3); else g.arc(0, 0, r, 0, Math.PI * 2);
  g.fillStyle = 'rgba(0,0,0,0.25)'; g.save(); g.translate(0.8, 1.6); g.fill(); g.restore();
  g.fillStyle = FILL[k] ?? '#1b1814'; g.fill();
  g.lineWidth = Math.max(1.4, r * 0.22); g.strokeStyle = '#fff'; g.stroke();
  glyph(g, k, r * 0.78);
  g.restore();
}

/** Classic white player arrow with black outline. */
export function drawArrow(g: CanvasRenderingContext2D, x: number, y: number, ang: number, a: number, lw: number) {
  g.save(); g.translate(x, y); g.rotate(ang);
  g.fillStyle = '#fff'; g.strokeStyle = '#000'; g.lineWidth = lw; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(0, -a); g.lineTo(a * 0.7, a * 0.8); g.lineTo(0, a * 0.4); g.lineTo(-a * 0.7, a * 0.8); g.closePath(); g.stroke(); g.fill();
  g.restore();
}

/** Small icon canvas for the legend. */
export function blipIcon(k: BlipKind | 'arrow'): HTMLCanvasElement {
  const c = document.createElement('canvas'), d = Math.min(2, devicePixelRatio || 1);
  c.width = c.height = 26 * d; c.style.width = c.style.height = '26px';
  const g = c.getContext('2d')!; g.scale(d, d);
  if (k === 'arrow') drawArrow(g, 13, 13, 0, 9, 2); else drawBlip(g, k, 13, 13, 10);
  return c;
}
