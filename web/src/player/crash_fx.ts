import * as THREE from 'three';

/**
 * Crash effects: a small pool of sprites for smoke (rises, grows, fades) and sparks (short, bright, fall),
 * plus speech bubbles for the NPC drivers. No fire, no explosion: light smoke and sparks only.
 */
interface P { s: THREE.Sprite; life: number; max: number; vx: number; vy: number; vz: number; grow: number; a0: number; spark: boolean }

function dot(inner: string, outer: string) {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d')!, gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, inner); gr.addColorStop(1, outer);
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export class CrashFx {
  private pool: P[] = [];
  private smokeTex = dot('rgba(255,255,255,0.9)', 'rgba(255,255,255,0)');
  private sparkTex = dot('rgba(255,235,160,1)', 'rgba(255,140,30,0)');
  private acc = new Map<object, number>();
  live = 0;

  constructor(private scene: THREE.Scene, size = 56) {
    for (let i = 0; i < size; i++) {
      const s = new THREE.Sprite(new THREE.SpriteMaterial({ transparent: true, depthWrite: false, fog: true }));
      s.visible = false; s.frustumCulled = false; scene.add(s);
      this.pool.push({ s, life: 0, max: 1, vx: 0, vy: 0, vz: 0, grow: 0, a0: 1, spark: false });
    }
  }

  private take(): P | null { return this.pool.find((p) => p.life <= 0) ?? null; }

  /** Emit smoke from a source at world three-coordinates; `level` 0..1 = thickness. `key` keeps the emission rate per source. */
  smoke(key: object, x: number, y: number, z: number, level: number, dt: number) {
    if (level <= 0) return;
    const a = (this.acc.get(key) ?? 0) + dt * (3 + 9 * level);
    let n = Math.floor(a);
    this.acc.set(key, a - n);
    while (n-- > 0) {
      const p = this.take(); if (!p) return;
      const m = p.s.material as THREE.SpriteMaterial;
      m.map = this.smokeTex; const g = 0.28 + 0.2 * (1 - level); m.color.setRGB(g, g, g); m.blending = THREE.NormalBlending;
      p.spark = false; p.max = p.life = 1.6 + 1.4 * level; p.a0 = 0.3 + 0.35 * level;
      p.s.position.set(x + (Math.random() - 0.5) * 0.3, y, z + (Math.random() - 0.5) * 0.3);
      p.vx = (Math.random() - 0.5) * 0.4; p.vy = 0.9 + Math.random() * 0.7 + level; p.vz = (Math.random() - 0.5) * 0.4;
      p.grow = 0.8 + level; p.s.scale.setScalar(0.35); p.s.visible = true;
    }
  }

  sparks(x: number, y: number, z: number, n: number, dirx = 0, dirz = 0) {
    for (let i = 0; i < n; i++) {
      const p = this.take(); if (!p) return;
      const m = p.s.material as THREE.SpriteMaterial;
      m.map = this.sparkTex; m.color.setRGB(1, 0.85, 0.5); m.blending = THREE.AdditiveBlending;
      p.spark = true; p.max = p.life = 0.3 + Math.random() * 0.35; p.a0 = 1;
      p.s.position.set(x, y, z);
      p.vx = dirx * 3 + (Math.random() - 0.5) * 6; p.vy = 1 + Math.random() * 4; p.vz = dirz * 3 + (Math.random() - 0.5) * 6;
      p.grow = 0; p.s.scale.setScalar(0.14); p.s.visible = true;
    }
  }

  update(dt: number) {
    let live = 0;
    for (const p of this.pool) {
      if (p.life <= 0) continue;
      p.life -= dt; live++;
      const m = p.s.material as THREE.SpriteMaterial;
      if (p.life <= 0) { p.s.visible = false; continue; }
      const k = p.life / p.max;
      p.s.position.x += p.vx * dt; p.s.position.y += p.vy * dt; p.s.position.z += p.vz * dt;
      if (p.spark) { p.vy -= 12 * dt; m.opacity = k; } else { p.s.scale.addScalar(p.grow * dt); m.opacity = p.a0 * Math.min(1, k * 2.2); }
    }
    this.live = live;
  }

  forget(key: object) { this.acc.delete(key); }

  dispose() {
    for (const p of this.pool) { this.scene.remove(p.s); p.s.material.dispose(); }
    this.smokeTex.dispose(); this.sparkTex.dispose();
  }
}

/** Speech bubble sprite above a figure. */
export function bubble(text: string): THREE.Sprite {
  const c = document.createElement('canvas'); c.width = 256; c.height = 72;
  const g = c.getContext('2d')!;
  g.fillStyle = '#fffffff0'; g.strokeStyle = '#111'; g.lineWidth = 4;
  g.beginPath(); g.roundRect(4, 4, 248, 50, 14); g.fill(); g.stroke();
  g.beginPath(); g.moveTo(110, 54); g.lineTo(128, 70); g.lineTo(138, 54); g.fill();
  g.fillStyle = '#111'; g.font = '700 24px Barlow, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText(text, 128, 30, 236);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true, depthWrite: false }));
  s.scale.set(1.9, 0.53, 1); s.position.y = 2.25; s.frustumCulled = false;
  return s;
}
