/** GTA-style radar (top left) and full-screen map; clicking inside the playable area jumps there. */
export interface MapPlace { name: string; sub: string; x: number; y: number; yaw: number; built: boolean }
interface MapMeta { mpp: number; x0: number; y1: number; w: number; h: number; built: number[]; polygon?: number[][]; places: MapPlace[]; kreise: Record<string, number[][]> }

export class GtaMap {
  private img = new Image();
  private meta!: MapMeta;
  private radar = document.getElementById('radar') as HTMLCanvasElement;
  private big = document.getElementById('bigmap') as HTMLDivElement;
  private canvas = document.getElementById('bigmap-canvas') as HTMLCanvasElement;
  private view = { cx: 0, cy: 0, scale: 1 }; // map pixel at screen centre, screen px per map px
  open = false;
  onJump: (x: number, y: number) => void = () => {};

  async load(base = '/map') {
    this.meta = await (await fetch(`${base}/map.json`)).json();
    this.img.src = `${base}/map.webp`;
    await this.img.decode();
    this.radar.addEventListener('click', () => this.toggle(true));
    document.getElementById('bigmap-close')!.addEventListener('click', () => this.toggle(false));
    window.addEventListener('keydown', (e) => {
      if (e.code === 'KeyM') this.toggle(!this.open);
      if (e.code === 'Escape') this.toggle(false);
    });
    this.initPanZoom();
  }

  /** Local metres -> map pixels. */
  private mp(x: number, y: number): [number, number] {
    return [(x - this.meta.x0) / this.meta.mpp, (this.meta.y1 - y) / this.meta.mpp];
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

  toggle(on: boolean) {
    this.open = on;
    this.big.style.display = on ? 'block' : 'none';
    if (on) {
      const [bx0, by1] = this.mp(this.meta.built[0], this.meta.built[3]);
      const [bx1, by0] = this.mp(this.meta.built[2], this.meta.built[1]);
      this.view.cx = (bx0 + bx1) / 2; this.view.cy = (by0 + by1) / 2;
      this.view.scale = Math.min(innerWidth, innerHeight) / 2600;
      document.exitPointerLock?.();
    }
  }

  /** Radar: map around the player, rotated so the camera looks up. */
  /** Optional overlay polylines (local metres), e.g. cycle lanes while riding. */
  overlay: number[][][] = [];

  drawRadar(px: number, py: number, yaw: number, heading: number, blips: { x: number; y: number; color: string }[] = []) {
    const c = this.radar, g = c.getContext('2d')!, dpr = devicePixelRatio;
    const S = Math.round(c.clientWidth * dpr);
    if (c.width !== S) c.width = c.height = S;
    const r = S / 2, zoom = S / 360; // ~360 m across
    g.save();
    g.beginPath(); g.arc(r, r, r - 2, 0, Math.PI * 2); g.clip();
    g.fillStyle = '#22282c'; g.fillRect(0, 0, S, S);
    const [mx, my] = this.mp(px, py);
    g.translate(r, r); g.rotate(-yaw); g.scale(zoom * this.meta.mpp, zoom * this.meta.mpp); g.translate(-mx, -my);
    g.drawImage(this.img, 0, 0);
    if (this.overlay.length) {
      g.strokeStyle = '#3fd0ff'; g.lineWidth = 3.5 / (zoom * this.meta.mpp) * dpr; g.lineCap = 'round';
      for (const l of this.overlay) {
        g.beginPath();
        l.forEach(([x, y], i) => { const [mx2, my2] = this.mp(x, y); if (i) g.lineTo(mx2, my2); else g.moveTo(mx2, my2); });
        g.stroke();
      }
    }
    g.restore();
    // blips (missions, targets, police); clamped to the radar edge like in GTA
    for (const b of blips) {
      const dx = (b.x - px) * zoom, dy = -(b.y - py) * zoom;
      const c = Math.cos(-yaw), s = Math.sin(-yaw);
      let bx = dx * c - dy * s, by = dx * s + dy * c;
      const len = Math.hypot(bx, by), maxR = r - 10 * dpr;
      if (len > maxR) { bx *= maxR / len; by *= maxR / len; }
      g.beginPath(); g.arc(r + bx, r + by, 5 * dpr, 0, Math.PI * 2);
      g.fillStyle = b.color; g.fill(); g.lineWidth = 1.5 * dpr; g.strokeStyle = '#000'; g.stroke();
    }
    g.save(); g.translate(r, r); g.rotate(heading - yaw); // player arrow relative to the camera
    g.fillStyle = '#fff'; g.strokeStyle = '#000'; g.lineWidth = 2 * dpr;
    const a = 9 * dpr;
    g.beginPath(); g.moveTo(0, -a); g.lineTo(a * 0.7, a * 0.8); g.lineTo(0, a * 0.4); g.lineTo(-a * 0.7, a * 0.8); g.closePath(); g.fill(); g.stroke();
    g.restore();
    g.save(); g.translate(r, r); g.rotate(-yaw); g.translate(0, -(r - 12 * dpr)); g.rotate(yaw); // north marker
    g.fillStyle = '#e8e8e8'; g.font = `700 ${12 * dpr}px Anton`; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText('N', 0, 0); g.restore();
    g.lineWidth = 4 * dpr; g.strokeStyle = '#111c'; g.beginPath(); g.arc(r, r, r - 2, 0, Math.PI * 2); g.stroke();
  }

  /** Full map (call every frame while open). */
  drawBig(px: number, py: number) {
    const c = this.canvas, g = c.getContext('2d')!, dpr = devicePixelRatio;
    if (c.width !== innerWidth * dpr) { c.width = innerWidth * dpr; c.height = innerHeight * dpr; }
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.fillStyle = '#1b2023'; g.fillRect(0, 0, innerWidth, innerHeight);
    const v = this.view;
    g.translate(innerWidth / 2, innerHeight / 2); g.scale(v.scale, v.scale); g.translate(-v.cx, -v.cy);
    g.imageSmoothingQuality = 'high';
    g.drawImage(this.img, 0, 0);
    const [bx0, by1] = this.mp(this.meta.built[0], this.meta.built[3]);
    const [bx1, by0] = this.mp(this.meta.built[2], this.meta.built[1]);
    // playable area (fence line)
    g.beginPath();
    (this.meta.polygon ?? [[this.meta.built[0], this.meta.built[1]], [this.meta.built[2], this.meta.built[1]], [this.meta.built[2], this.meta.built[3]], [this.meta.built[0], this.meta.built[3]]])
      .forEach(([x, y], i) => { const [mx2, my2] = this.mp(x, y); if (i) g.lineTo(mx2, my2); else g.moveTo(mx2, my2); });
    g.closePath();
    g.fillStyle = 'rgba(245,197,24,0.13)'; g.fill();
    g.strokeStyle = '#f5c518'; g.lineWidth = 3 / v.scale; g.setLineDash([12 / v.scale, 8 / v.scale]); g.stroke(); g.setLineDash([]);
    void bx0; void bx1; void by0; void by1;
    const [mx, my] = this.mp(px, py);
    g.fillStyle = '#fff'; g.strokeStyle = '#000'; g.lineWidth = 3 / v.scale;
    g.beginPath(); g.arc(mx, my, 8 / v.scale, 0, Math.PI * 2); g.fill(); g.stroke();
  }

  private screenToMap(sx: number, sy: number): [number, number] {
    const v = this.view;
    return [(sx - innerWidth / 2) / v.scale + v.cx, (sy - innerHeight / 2) / v.scale + v.cy];
  }

  /** Screen point -> local metres if inside the playable area. */
  private hit(sx: number, sy: number): [number, number] | null {
    const [mx, my] = this.screenToMap(sx, sy);
    const x = this.meta.x0 + mx * this.meta.mpp, y = this.meta.y1 - my * this.meta.mpp;
    const r = this.meta.polygon;
    if (!r) { const [x0, y0, x1, y1] = this.meta.built; return x > x0 && x < x1 && y > y0 && y < y1 ? [x, y] : null; }
    let c = false;
    for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
      const [xi, yi] = r[i], [xj, yj] = r[j];
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
    }
    return c ? [x, y] : null;
  }

  private initPanZoom() {
    const c = this.canvas, pts = new Map<number, { x: number; y: number }>();
    let moved = 0, pinch = 0;
    const zoomAt = (f: number, sx: number, sy: number) => {
      const [mx, my] = this.screenToMap(sx, sy);
      this.view.scale = Math.min(4, Math.max(0.15, this.view.scale * f));
      const [nx, ny] = this.screenToMap(sx, sy);
      this.view.cx += mx - nx; this.view.cy += my - ny;
    };
    c.addEventListener('wheel', (e) => { e.preventDefault(); zoomAt(Math.exp(-e.deltaY * 0.0015), e.clientX, e.clientY); }, { passive: false });
    c.addEventListener('pointerdown', (e) => { c.setPointerCapture(e.pointerId); pts.set(e.pointerId, { x: e.clientX, y: e.clientY }); moved = 0; });
    c.addEventListener('pointermove', (e) => {
      const p = pts.get(e.pointerId);
      if (!p) { c.style.cursor = this.hit(e.clientX, e.clientY) ? 'crosshair' : 'grab'; return; }
      if (pts.size === 2) {
        const [a, b] = [...pts.values()];
        const d0 = Math.hypot(a.x - b.x, a.y - b.y);
        p.x = e.clientX; p.y = e.clientY;
        const [a2, b2] = [...pts.values()];
        if (pinch && d0 > 0) zoomAt(Math.hypot(a2.x - b2.x, a2.y - b2.y) / d0, (a2.x + b2.x) / 2, (a2.y + b2.y) / 2);
        pinch = 1; moved += 10;
        return;
      }
      const dx = e.clientX - p.x, dy = e.clientY - p.y;
      moved += Math.abs(dx) + Math.abs(dy);
      this.view.cx -= dx / this.view.scale; this.view.cy -= dy / this.view.scale;
      p.x = e.clientX; p.y = e.clientY;
    });
    const up = (e: PointerEvent) => {
      pts.delete(e.pointerId);
      if (pts.size < 2) pinch = 0;
      if (moved < 8 && pts.size === 0) {
        const h = this.hit(e.clientX, e.clientY);
        if (h) { this.toggle(false); this.onJump(h[0], h[1]); }
      }
    };
    c.addEventListener('pointerup', up);
    c.addEventListener('pointercancel', up);
    document.getElementById('bigmap-in')!.addEventListener('click', () => zoomAt(1.4, innerWidth / 2, innerHeight / 2));
    document.getElementById('bigmap-out')!.addEventListener('click', () => zoomAt(1 / 1.4, innerWidth / 2, innerHeight / 2));
  }
}
