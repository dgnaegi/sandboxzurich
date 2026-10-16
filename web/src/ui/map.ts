/** Arcade radar (top left) and full-screen city map (M / tap on the radar). Vector data from pipeline/mapdata.py. */
import { MapData } from './map_data';
import { CLASSIC, DARK, applyView, drawBorders, drawWorld, type DrawOpts, type View } from './map_render';
import { drawLabels, type Jump, type PinHit } from './map_labels';

export type MapPlace = Jump;
interface MapMeta { x0?: number; y1?: number; built: number[]; polygon?: number[][]; places: MapPlace[]; kreise: Record<string, number[][]> }

export class CityMap {
  private meta!: MapMeta;
  private data = new MapData();
  private radar = document.getElementById('radar') as HTMLCanvasElement;
  private big = document.getElementById('bigmap') as HTMLDivElement;
  private canvas = document.getElementById('bigmap-canvas') as HTMLCanvasElement;
  private base = document.createElement('canvas');
  private view = { cx: 0, cy: 0, s: 0.2 }; // world metres at screen centre, px per metre
  private baseKey = '';
  private pins: PinHit[] = [];
  private showVelo = false;
  private opts!: DrawOpts;
  private frame = 0;
  open = false;
  onJump: (x: number, y: number) => void = () => {};
  /** Optional overlay polylines (local metres), e.g. cycle lanes while riding. */
  overlay: number[][][] = [];

  async load(base = '/map') {
    const [meta] = await Promise.all([fetch(`${base}/map.json`).then((r) => r.json()), this.data.load()]);
    this.meta = meta;
    this.opts = { velo: false, kreise: Object.values(meta.kreise), playArea: meta.polygon ?? this.rect(), dpr: 1 };
    this.radar.addEventListener('click', () => this.toggle(true));
    document.getElementById('bigmap-close')!.addEventListener('click', () => this.toggle(false));
    window.addEventListener('keydown', (e) => {
      if (e.code === 'KeyM') this.toggle(!this.open);
      if (e.code === 'Escape') this.toggle(false);
      if (this.open && (e.key === '+' || e.key === '=')) this.zoomAt(1.4, innerWidth / 2, innerHeight / 2);
      if (this.open && (e.key === '-' || e.key === '_')) this.zoomAt(1 / 1.4, innerWidth / 2, innerHeight / 2);
    });
    this.buildUi();
    this.initPanZoom();
  }

  private rect(): number[][] { const [a, b, c, d] = this.meta.built; return [[a, b], [c, b], [c, d], [a, d]]; }

  private buildUi() {
    const legend = document.getElementById('bigmap-legend')!;
    legend.innerHTML = 'Irgendwo im Spielgebiet hintippen, um hinzuspringen &nbsp;·&nbsp; <i class="ln"></i> Tram';
    const tools = document.createElement('div');
    tools.id = 'bigmap-tools';
    const mk = (id: string, label: string, title: string, fn: () => void) => {
      const b = document.createElement('button'); b.id = id; b.textContent = label; b.title = title; b.addEventListener('click', fn); tools.appendChild(b); return b;
    };
    mk('bigmap-here', '◎', 'Standort', () => { this.view.cx = this.px; this.view.cy = this.py; this.view.s = Math.max(this.view.s, 0.5); });
    const velo = mk('bigmap-velo', 'Velo', 'Velorouten ein-/ausblenden', () => {
      this.showVelo = !this.showVelo; velo.classList.toggle('on', this.showVelo);
      if (this.showVelo) void this.data.loadVelo().then(() => { this.baseKey = ''; });
    });
    this.big.appendChild(tools);
    const lic = document.createElement('div');
    lic.id = 'bigmap-lic'; lic.textContent = '© OpenStreetMap-Mitwirkende · Stadt Zürich OGD';
    this.big.appendChild(lic);
  }

  kreisAt(x: number, y: number): string {
    for (const [name, ring] of Object.entries(this.meta.kreise)) {
      let c = false;
      for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const [xi, yi] = ring[i], [xj, yj] = ring[j];
        if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
      }
      if (c) return name;
    }
    return 'ZÜRICH';
  }

  nearestPlace(x: number, y: number): MapPlace | null {
    let best: MapPlace | null = null, bd = 160;
    for (const p of this.meta.places) {
      const d = Math.hypot(p.x - x, p.y - y);
      if (d < bd) { bd = d; best = p; }
    }
    return best;
  }

  private px = 0;
  private py = 0;

  toggle(on: boolean) {
    this.open = on;
    this.big.style.display = on ? 'block' : 'none';
    if (on) {
      const [x0, y0, x1, y1] = this.meta.built;
      this.view.cx = (x0 + x1) / 2; this.view.cy = (y0 + y1) / 2;
      this.view.s = Math.min(innerWidth / ((x1 - x0) * 1.05), innerHeight / ((y1 - y0) * 1.2));
      this.baseKey = '';
      document.exitPointerLock?.();
    }
  }

  /** Radar: map around the player, rotated so the camera looks up. */
  drawRadar(px: number, py: number, yaw: number, heading: number, blips: { x: number; y: number; color: string }[] = []) {
    this.px = px; this.py = py;
    const c = this.radar, g = c.getContext('2d')!, dpr = Math.min(2, devicePixelRatio);
    const S = Math.round(c.clientWidth * dpr);
    if (c.width !== S) c.width = c.height = S;
    if (!this.data.ready || ((this.frame++ & 1) && matchMedia('(pointer: coarse)').matches)) { if (!this.data.ready) { g.fillStyle = DARK.bg; g.fillRect(0, 0, S, S); } else return; }
    const r = S / 2, css = c.clientWidth, s = css / (css < 140 ? 250 : 330);
    g.save();
    g.beginPath(); g.arc(r, r, r - 2, 0, Math.PI * 2); g.clip();
    const v: View = { cx: px, cy: py, s, rot: -yaw, w: css, h: css };
    drawWorld(g, this.data, v, DARK, { ...this.opts, velo: false, boost: 1.7, dpr });
    if (this.overlay.length) {
      applyView(g, v, dpr);
      g.strokeStyle = DARK.veloLane; g.lineWidth = 3.5 / s; g.lineCap = 'round'; g.lineJoin = 'round';
      for (const l of this.overlay) { g.beginPath(); l.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.stroke(); }
    }
    g.restore();
    g.setTransform(1, 0, 0, 1, 0, 0);
    // blips (missions, targets, police); clamped to the radar edge like a classic arcade radar
    for (const b of blips) {
      const dx = (b.x - px) * s * dpr, dy = -(b.y - py) * s * dpr;
      const cs = Math.cos(-yaw), sn = Math.sin(-yaw);
      let bx = dx * cs - dy * sn, by = dx * sn + dy * cs;
      const len = Math.hypot(bx, by), maxR = r - 10 * dpr;
      if (len > maxR) { bx *= maxR / len; by *= maxR / len; }
      g.beginPath(); g.arc(r + bx, r + by, 5 * dpr, 0, Math.PI * 2);
      g.fillStyle = b.color; g.fill(); g.lineWidth = 1.5 * dpr; g.strokeStyle = '#000'; g.stroke();
    }
    this.arrow(g, r, r, heading - yaw, 9 * dpr, dpr);
    // north marker rotates with the map
    const na = yaw, nr = r - 13 * dpr;
    const nx = r + Math.sin(na) * nr, ny = r - Math.cos(na) * nr;
    g.fillStyle = '#e4007d'; g.beginPath(); g.arc(nx, ny, 8.5 * dpr, 0, 7); g.fill();
    g.fillStyle = '#fff'; g.font = `700 ${12 * dpr}px Anton, sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText('N', nx, ny + 0.5 * dpr);
    g.lineWidth = 4 * dpr; g.strokeStyle = '#111c'; g.beginPath(); g.arc(r, r, r - 2, 0, Math.PI * 2); g.stroke();
  }

  private arrow(g: CanvasRenderingContext2D, x: number, y: number, ang: number, a: number, dpr: number) {
    g.save(); g.translate(x, y); g.rotate(ang);
    g.fillStyle = '#fff'; g.strokeStyle = '#000'; g.lineWidth = 2 * dpr; g.lineJoin = 'round';
    g.beginPath(); g.moveTo(0, -a); g.lineTo(a * 0.7, a * 0.8); g.lineTo(0, a * 0.4); g.lineTo(-a * 0.7, a * 0.8); g.closePath(); g.fill(); g.stroke();
    g.restore();
  }

  /** Full map (call every frame while open). */
  drawBig(px: number, py: number, heading = 0) {
    this.px = px; this.py = py;
    const c = this.canvas, g = c.getContext('2d')!, dpr = Math.min(2, devicePixelRatio);
    const W = innerWidth, H = innerHeight;
    if (c.width !== Math.round(W * dpr)) { c.width = this.base.width = Math.round(W * dpr); c.height = this.base.height = Math.round(H * dpr); this.baseKey = ''; }
    const v: View = { cx: this.view.cx, cy: this.view.cy, s: this.view.s, rot: 0, w: W, h: H };
    const key = `${v.cx.toFixed(1)}|${v.cy.toFixed(1)}|${v.s.toFixed(4)}|${W}|${H}|${this.showVelo}|${this.data.velo ? 1 : 0}`;
    if (key !== this.baseKey) {
      this.baseKey = key;
      const bg = this.base.getContext('2d')!;
      const o = { ...this.opts, velo: this.showVelo, dpr };
      drawWorld(bg, this.data, v, CLASSIC, o);
      drawBorders(bg, v, CLASSIC, o);
      drawLabels(bg, this.data, v, CLASSIC, { dpr, kreise: this.meta.kreise, jumps: [], pins: this.pins });
    }
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.drawImage(this.base, 0, 0);
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    const [sx, sy] = this.toScreen(px, py);
    const pulse = 1 + 0.25 * Math.sin(performance.now() / 300);
    g.fillStyle = 'rgba(228,0,125,0.22)'; g.beginPath(); g.arc(sx, sy, 17 * pulse, 0, 7); g.fill();
    this.arrow(g, sx, sy, heading, 11, 1);
  }

  private toScreen(x: number, y: number): [number, number] {
    return [innerWidth / 2 + (x - this.view.cx) * this.view.s, innerHeight / 2 - (y - this.view.cy) * this.view.s];
  }

  private toWorld(sx: number, sy: number): [number, number] {
    return [this.view.cx + (sx - innerWidth / 2) / this.view.s, this.view.cy - (sy - innerHeight / 2) / this.view.s];
  }

  private zoomAt(f: number, sx: number, sy: number) {
    const [wx, wy] = this.toWorld(sx, sy);
    this.view.s = Math.min(3, Math.max(0.05, this.view.s * f));
    const [nx, ny] = this.toWorld(sx, sy);
    this.view.cx += wx - nx; this.view.cy += wy - ny;
  }

  /** Screen point -> local metres if inside the playable area. */
  private hit(sx: number, sy: number): [number, number] | null {
    const [x, y] = this.toWorld(sx, sy);
    const r = this.meta.polygon ?? this.rect();
    let c = false;
    for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
      const [xi, yi] = r[i], [xj, yj] = r[j];
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
    }
    return c ? [x, y] : null;
  }

  private pinAt(sx: number, sy: number): PinHit | null {
    return this.pins.find((p) => Math.hypot(p.x - sx, p.y - sy) < 16) ?? null;
  }

  private initPanZoom() {
    const c = this.canvas, pts = new Map<number, { x: number; y: number }>();
    let moved = 0, pinch = 0;
    c.addEventListener('wheel', (e) => { e.preventDefault(); this.zoomAt(Math.exp(-e.deltaY * 0.0015), e.clientX, e.clientY); }, { passive: false });
    c.addEventListener('pointerdown', (e) => { c.setPointerCapture(e.pointerId); pts.set(e.pointerId, { x: e.clientX, y: e.clientY }); moved = 0; });
    c.addEventListener('pointermove', (e) => {
      const p = pts.get(e.pointerId);
      if (!p) { c.style.cursor = this.pinAt(e.clientX, e.clientY) || this.hit(e.clientX, e.clientY) ? 'crosshair' : 'grab'; return; }
      if (pts.size === 2) {
        const [a, b] = [...pts.values()];
        const d0 = Math.hypot(a.x - b.x, a.y - b.y);
        p.x = e.clientX; p.y = e.clientY;
        const [a2, b2] = [...pts.values()];
        if (pinch && d0 > 0) this.zoomAt(Math.hypot(a2.x - b2.x, a2.y - b2.y) / d0, (a2.x + b2.x) / 2, (a2.y + b2.y) / 2);
        pinch = 1; moved += 10;
        return;
      }
      const dx = e.clientX - p.x, dy = e.clientY - p.y;
      moved += Math.abs(dx) + Math.abs(dy);
      this.view.cx -= dx / this.view.s; this.view.cy += dy / this.view.s;
      p.x = e.clientX; p.y = e.clientY;
    });
    const up = (e: PointerEvent) => {
      pts.delete(e.pointerId);
      if (pts.size < 2) pinch = 0;
      if (e.type === 'pointerup' && moved < 8 && pts.size === 0) {
        const pin = this.pinAt(e.clientX, e.clientY);
        const h = pin ? [pin.place.x, pin.place.y] : this.hit(e.clientX, e.clientY);
        if (h) { this.toggle(false); this.onJump(h[0], h[1]); }
      }
    };
    c.addEventListener('pointerup', up);
    c.addEventListener('pointercancel', up);
    document.getElementById('bigmap-in')!.addEventListener('click', () => this.zoomAt(1.4, innerWidth / 2, innerHeight / 2));
    document.getElementById('bigmap-out')!.addEventListener('click', () => this.zoomAt(1 / 1.4, innerWidth / 2, innerHeight / 2));
  }
}
