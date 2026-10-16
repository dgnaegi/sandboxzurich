/** "Stimmt etwas nicht?": builds a mailto: URL with position, view direction, time, tile and device (no server involved).
 *  Corrections are collected by mail and applied by pipeline/apply_corrections.py (see research/corrections.md). */
export const REPORT_MAIL = 'daniel.gnaegi@protonmail.com';
const O = { x: 2681400, y: 1248700 };

/** Local game metres -> WGS84 (swisstopo approximate LV95 formulas, error below 1 m). */
export function localToWgs(x: number, y: number): { lat: number; lon: number } {
  const e = (x + O.x - 2600000) / 1e6, n = (y + O.y - 1200000) / 1e6;
  const lon = 2.6779094 + 4.728982 * e + 0.791484 * e * n + 0.1306 * e * n * n - 0.0436 * e * e * e;
  const lat = 16.9023892 + 3.238272 * n - 0.270978 * e * e - 0.002528 * n * n - 0.0447 * e * e * n - 0.0140 * n * n * n;
  return { lat: (lat * 100) / 36, lon: (lon * 100) / 36 };
}

export interface ReportCtx { x: number; y: number; yaw: number; min: number; day: number; tile: string; touch: boolean; ua: string; w: number; h: number; href: string }

const DIRS = ['Norden', 'Nordosten', 'Osten', 'Südosten', 'Süden', 'Südwesten', 'Westen', 'Nordwesten'];
const DAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

export function buildReportUrl(c: ReportCtx): string {
  const w = localToWgs(c.x, c.y), deg = ((c.yaw * 180) / Math.PI % 360 + 360) % 360;   // yaw 0 = north, clockwise
  const hh = String(Math.floor(c.min / 60)).padStart(2, '0'), mm = String(Math.floor(c.min % 60)).padStart(2, '0');
  const base = c.href.split('?')[0];
  const lines = [
    'Was stimmt nicht? Foto gern anhängen:',
    '', '', '',
    '--- automatisch eingefügt, bitte stehen lassen ---',
    `Ort (lokal, m): x=${c.x.toFixed(1)} y=${c.y.toFixed(1)}`,
    `WGS84: ${w.lat.toFixed(6)}, ${w.lon.toFixed(6)} (https://www.openstreetmap.org/?mlat=${w.lat.toFixed(6)}&mlon=${w.lon.toFixed(6)}#map=19/${w.lat.toFixed(6)}/${w.lon.toFixed(6)})`,
    `Blickrichtung: ${DIRS[Math.round(deg / 45) % 8]} (${deg.toFixed(0)}°)`,
    `Spielzeit: ${DAYS[c.day] ?? '?'} ${hh}:${mm}`,
    `Kachel: ${c.tile}`,
    `Gerät: ${c.touch ? 'Touch' : 'Maus/Tastatur'}, ${c.w}x${c.h}, ${c.ua}`,
    `Link: ${base}?at=${c.x.toFixed(0)},${c.y.toFixed(0)},${c.yaw.toFixed(2)}&t=${hh}:${mm}`,
  ];
  return `mailto:${REPORT_MAIL}?subject=${encodeURIComponent('Sandbox Zürich – Korrektur')}&body=${encodeURIComponent(lines.join('\n'))}`;
}

type Hooks = { sbxPlayer?: { x: number; y: number; yaw: number }; sbxClock?: { min: number; day: number }; sbxTiles?: { world?: { tile?: number } } };

export function openReport(): string | null {
  const h = window as unknown as Hooks & { sbxLastReportUrl?: string };
  if (!h.sbxPlayer) return null;
  const p = h.sbxPlayer, s = h.sbxTiles?.world?.tile ?? 200;
  const url = buildReportUrl({
    x: p.x, y: p.y, yaw: p.yaw, min: h.sbxClock?.min ?? 0, day: h.sbxClock?.day ?? 0,
    tile: `t_${Math.floor(p.x / s)}_${Math.floor(p.y / s)}`, touch: matchMedia('(pointer: coarse)').matches,
    ua: navigator.userAgent.slice(0, 120), w: innerWidth, h: innerHeight, href: location.href,
  });
  h.sbxLastReportUrl = url;   // for tests
  location.href = url;
  return url;
}
