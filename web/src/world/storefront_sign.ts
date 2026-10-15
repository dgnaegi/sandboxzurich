import { lookOf, mix, lum, hash, type Look, type ShopSign } from './storefront_style';

/** Paints one venue name board (TEXW x ROW px) into the shared sign canvas: real name in a free font, colours/style from the look. */
export function drawSignRow(g: CanvasRenderingContext2D, y0: number, W: number, ROW: number, s: ShopSign, look: Look = lookOf(s)) {
  const { bg, fg, st } = look;
  g.save();
  g.beginPath(); g.rect(0, y0, W, ROW); g.clip();
  g.fillStyle = bg; g.fillRect(0, y0, W, ROW);
  const upper = st === 'box' || st === 'neon' || st === 'paint' || hash(s.name) % 3 === 0;
  const text = upper ? s.name.toUpperCase() : s.name;
  let size = st === 'plain' ? 62 : st === 'letters' ? 78 : 74;
  const setFont = () => { g.font = `700 ${size}px ${look.font}, "Barlow Condensed", "Arial Narrow", sans-serif`; };
  setFont();
  if (st === 'paint') g.letterSpacing = '3px';
  const maxPx = W - (st === 'box' ? 70 : 44);
  const tw = g.measureText(text).width;
  if (tw > maxPx) { size = Math.floor(size * maxPx / tw); setFont(); }
  g.textAlign = 'center'; g.textBaseline = 'middle';
  const cy = y0 + ROW / 2 + (look.font === 'Anton' ? 5 : 3);
  if (st === 'neon') {
    const c = look.neon ?? fg;
    g.shadowColor = c; g.shadowBlur = 14; g.fillStyle = c;
    g.fillText(text, W / 2, cy);
    g.shadowBlur = 0; g.strokeStyle = c; g.lineWidth = 3; g.strokeRect(6, y0 + 6, W - 12, ROW - 12);
  } else if (st === 'box') {
    const edge = lum(bg) > 0.5 ? mix(bg, '#000000', 0.35) : mix(bg, '#ffffff', 0.4);
    g.strokeStyle = edge; g.lineWidth = 7; g.strokeRect(4, y0 + 4, W - 8, ROW - 8);
    g.fillStyle = fg; g.fillText(text, W / 2, cy);
  } else if (st === 'paint') {
    g.strokeStyle = fg; g.globalAlpha = 0.55; g.lineWidth = 2; g.strokeRect(14, y0 + 12, W - 28, ROW - 24); g.globalAlpha = 1;
    g.fillStyle = fg; g.fillText(text, W / 2, cy);
  } else {
    if (st === 'letters') { g.fillStyle = lum(fg) > 0.5 ? 'rgba(0,0,0,0.35)' : 'rgba(255,255,255,0.25)'; g.fillText(text, W / 2 + 3, cy + 3); }
    g.fillStyle = fg; g.fillText(text, W / 2, cy);
  }
  g.restore();
}
