/**
 * Resolved look of one ground-floor venue. Venues with photo notes (tile `signs[].v`, pipeline/shopfronts_v3.py) use the
 * real colours / sign style / awning / seating; all others get plausible values from the name hash and the venue kind
 * (Zürich mix: dark green, bordeaux, black/white, mustard ...). Colours only, never logos; text is drawn in free fonts.
 */
export type SignStyle = 'box' | 'letters' | 'neon' | 'paint' | 'blade' | 'plain';
export interface Notes { b?: string; f?: string; s?: SignStyle; a?: string; as?: number; c?: string; w?: string; t?: number; p?: number; n?: number }
export interface ShopSign { x: number; y: number; z: number; tx: number; ty: number; w: number; name: string; kind: string; pd?: number; v?: Notes }

export interface Look {
  real: boolean;
  bg: string; fg: string; st: SignStyle; font: string; hf: number;
  fc: string | null;                    // ground-floor facade colour (piers + riser overlays), only with notes
  aw: string | null; stripes: boolean;  // awning colour
  seat: boolean; plants: boolean; blade: boolean; parasol: string; neon: string | null;
}

export function hash(s: string) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
}

export function lum(hex: string) {
  const n = parseInt(hex.slice(1), 16);
  return (0.299 * (n >> 16) + 0.587 * (n >> 8 & 255) + 0.114 * (n & 255)) / 255;
}
export function mix(a: string, b: string, t: number) {
  const x = parseInt(a.slice(1), 16), y = parseInt(b.slice(1), 16);
  const ch = (s: number) => Math.round((x >> s & 255) * (1 - t) + (y >> s & 255) * t);
  return '#' + ((1 << 24) | ch(16) << 16 | ch(8) << 8 | ch(0)).toString(16).slice(1);
}

const BARS = ['bar', 'pub', 'nightclub', 'biergarten'];
const FOOD = ['restaurant', 'cafe', 'fast_food', 'ice_cream', 'bakery', 'pastry', 'food_court'];
// [background, text]
const PAIRS_GASTRO: [string, string][] = [['#1d1d1f', '#f2e6c9'], ['#6e1428', '#f4ead8'], ['#24473a', '#f0e9d6'], ['#f1ece0', '#26262a'],
  ['#1f3a5c', '#f3efe4'], ['#c9972e', '#1c1a18'], ['#3a2a22', '#e8d6b0'], ['#e9e3d3', '#7a1f2b'], ['#2f2f33', '#ffffff'], ['#8a3b2a', '#f6ecd8'],
  ['#5d6f4f', '#f7f3e6'], ['#0f6f73', '#ffffff']];
const PAIRS_FAST: [string, string][] = [['#c8352b', '#ffffff'], ['#f2c230', '#1c1a18'], ['#2e9a4a', '#ffffff'], ['#1e5fb0', '#ffffff'], ['#e8651f', '#ffffff'], ['#f1ece0', '#c8352b']];
const PAIRS_SHOP: [string, string][] = [['#1d1d1f', '#ffffff'], ['#efeeea', '#1d1d1f'], ['#d9d4c8', '#2a2a2a'], ['#3a3d42', '#f2f2f2'], ['#b9c7cf', '#1f2a33'],
  ['#e7d2c4', '#4a2a22'], ['#c4441c', '#ffffff'], ['#2d6b45', '#ffffff'], ['#f0c6cf', '#4a1f2e'], ['#1f4e8c', '#ffffff']];
const NEON = ['#ff3caa', '#28e6dc', '#ffb43c', '#8c64ff', '#ff5a46'];
const AWN = ['#b8202a', '#2d6b45', '#1f4e8c', '#d9a020', '#6e1428', '#0f6f73', '#c4441c', '#2b2b2e', '#d8cfb8', '#4a6a3a', '#1c3560'];
const PARASOL = ['#e8e1cf', '#b8202a', '#c9972e', '#2d6b45', '#1c3560', '#d8cfb8', '#2b2b2e'];
const FONTS = ['"Barlow Condensed"', 'Anton', 'Barlow'];

type W = [SignStyle, number][];
function pick<T>(h: number, a: readonly T[]): T { return a[(h >>> 0) % a.length]; }
function pickW(h: number, w: W): SignStyle {
  const sum = w.reduce((s, x) => s + x[1], 0);
  let r = (h >>> 0) % sum;
  for (const [k, v] of w) { if (r < v) return k; r -= v; }
  return w[0][0];
}

function styleWeights(kind: string): W {
  if (BARS.includes(kind)) return [['neon', 38], ['paint', 20], ['letters', 22], ['plain', 12], ['blade', 8]];
  if (kind === 'fast_food' || kind === 'food_court') return [['box', 70], ['letters', 15], ['paint', 15]];
  if (kind === 'restaurant') return [['letters', 26], ['paint', 26], ['box', 16], ['plain', 14], ['blade', 18]];
  if (kind === 'cafe' || kind === 'ice_cream' || kind === 'bakery' || kind === 'pastry') return [['paint', 30], ['letters', 28], ['plain', 16], ['blade', 14], ['box', 12]];
  if (kind === 'kiosk' || kind === 'convenience' || kind === 'tobacco') return [['box', 60], ['paint', 25], ['letters', 15]];
  if (kind === 'pharmacy') return [['box', 100]];
  return [['letters', 36], ['plain', 28], ['box', 20], ['paint', 10], ['blade', 6]];
}

export function lookOf(s: ShopSign): Look {
  const h = hash(s.name), k = s.kind, v = s.v, bar = BARS.includes(k), food = FOOD.includes(k) || bar;
  const fastLike = k === 'fast_food' || k === 'food_court' || k === 'kiosk' || k === 'convenience';
  const pool = fastLike ? PAIRS_FAST : food ? PAIRS_GASTRO : PAIRS_SHOP;
  let [bg, fg] = pick(h >> 5, pool);
  let st = pickW(h >> 9, styleWeights(k));
  let font = pick(h >> 13, FONTS);
  if (bar) { bg = '#120d1a'; }
  if (k === 'pharmacy') { bg = '#ffffff'; fg = '#1f9a62'; }
  let aw: string | null = null, stripes = false;
  const awnP = k === 'cafe' ? 55 : k === 'restaurant' ? 40 : k === 'bakery' || k === 'pastry' || k === 'ice_cream' ? 50 : k === 'greengrocer' || k === 'florist' ? 70 : fastLike ? 25 : 0;
  if (awnP && (h >>> 0) % 100 < awnP && s.w > 2.4) { aw = pick(h >> 3, AWN); stripes = (h >>> 17) % 100 < 58; }
  let seat = false;
  const seatP = k === 'cafe' || k === 'ice_cream' ? 40 : k === 'restaurant' ? 32 : k === 'bar' || k === 'pub' || k === 'biergarten' ? 24 : k === 'fast_food' ? 10 : 0;
  if (seatP && (h >>> 7) % 100 < seatP) seat = true;
  let plants = food && (h >>> 11) % 100 < 22;
  let fc: string | null = null, neon: string | null = null, real = false;
  if (v) {
    real = true;
    if (v.c) fc = v.c;
    if (v.s) st = v.s;
    aw = v.a ?? null; stripes = !!v.a && !!v.as;
    seat = !!v.t; plants = !!v.p;
    if (v.b) { bg = v.b; if (v.f) fg = v.f; else fg = lum(bg) > 0.55 ? '#1c1a18' : '#f4efe4'; }
    else if (v.f) {   // letters straight on the wall: board in the facade colour
      bg = fc ?? bg; fg = v.f;
      if (Math.abs(lum(bg) - lum(fg)) < 0.3) bg = lum(fg) > 0.5 ? mix(bg, '#000000', 0.55) : mix(bg, '#ffffff', 0.6);
    } else if (fc) { bg = fc; fg = lum(fc) > 0.55 ? '#1c1a18' : '#f4efe4'; }
    if (Math.abs(lum(bg) - lum(fg)) < 0.25) fg = lum(bg) > 0.5 ? '#1c1a18' : '#f4efe4';
    if (st === 'neon') { neon = lum(fg) > 0.25 ? fg : pick(h >> 2, NEON); bg = '#120d1a'; }
  }
  if (st === 'neon' && !neon) neon = pick(h >> 2, NEON);
  if (st === 'neon') bg = '#120d1a';
  const hf = st === 'plain' ? 0.62 : st === 'blade' ? 0.78 : st === 'letters' ? 0.9 : 1;
  if (st === 'plain' || st === 'blade') font = '"Barlow Condensed"';
  return { real, bg, fg, st, font, hf, fc, aw, stripes, seat, plants, blade: st === 'blade', parasol: aw ?? pick(h >> 4, PARASOL), neon };
}
