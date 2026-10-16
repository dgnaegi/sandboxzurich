/**
 * Place-dependent ambience layers (procedural WebAudio, no sample files). A handful of looping layers is cross-faded by
 * where the player is: traffic (distance to main roads), voices (squares, busy streets, passer-by density), wind and
 * leaves + birds (parks), tram rolling/squeal, church bells on the hour, distant bike bells. The map comes from
 * /audio/soundmap.json (pipeline/soundmap.py), loaded lazily after the first interaction.
 */
interface SoundMap { roads: number[][]; green: number[][]; squares: number[][]; churches: number[][] }
export interface AmbIn {
  x: number; y: number; heading: number; night: number; density: number; hour: number;
  trams: { x: number; y: number; heading: number }[];
}
const CELL = 120;
const key = (i: number, j: number) => i * 8192 + j + 4096;
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));

class Grid {
  private m = new Map<number, number[]>();
  add(idx: number, x0: number, y0: number, x1: number, y1: number) {
    for (let i = Math.floor(x0 / CELL); i <= Math.floor(x1 / CELL); i++) for (let j = Math.floor(y0 / CELL); j <= Math.floor(y1 / CELL); j++) {
      const k = key(i, j); let a = this.m.get(k); if (!a) this.m.set(k, a = []); a.push(idx);
    }
  }
  at(x: number, y: number): number[] { return this.m.get(key(Math.floor(x / CELL), Math.floor(y / CELL))) ?? []; }
}

export class Ambience {
  private map: SoundMap | null = null;
  private roadG = new Grid(); private greenG = new Grid(); private sqG = new Grid();
  private g: Record<'traffic' | 'voices' | 'wind' | 'leaves' | 'tram' | 'squeal' | 'pass', GainNode>;
  private trafficLp: BiquadFilterNode; private passBp: BiquadFilterNode; private passPan: StereoPannerNode; private tramPan: StereoPannerNode;
  private t = 0; private birdT = 4; private passT = 3; private bikeT = 30;
  private road = 0; private green = 0; private square = 0;
  private lastHour = -1; private strikes = 0; private strikeT = 0; private bellVol = 0; private bellPan = 0;
  private prevTram = { x: 0, y: 0, h: 0 }; private turn = 0;

  constructor(private ctx: AudioContext, private out: AudioNode, noise: AudioBuffer) {
    const mk = (type: BiquadFilterType, f: number, q = 0.7, off = Math.random() * 3) => {
      const s = ctx.createBufferSource(); s.buffer = noise; s.loop = true;
      const b = ctx.createBiquadFilter(); b.type = type; b.frequency.value = f; b.Q.value = q;
      const g = ctx.createGain(); g.gain.value = 0;
      s.connect(b); b.connect(g); s.start(0, off); return { b, g };
    };
    const traffic = mk('lowpass', 500), wind = mk('bandpass', 420, 0.6), leaves = mk('highpass', 4200, 0.5);
    const tram = mk('lowpass', 220), squeal = mk('bandpass', 3300, 14), pass = mk('bandpass', 500, 1.2);
    this.trafficLp = traffic.b; this.passBp = pass.b;
    this.passPan = ctx.createStereoPanner(); this.tramPan = ctx.createStereoPanner();
    pass.g.connect(this.passPan).connect(out); tram.g.connect(this.tramPan); squeal.g.connect(this.tramPan); this.tramPan.connect(out);
    traffic.g.connect(out);
    // slow gusts modulate wind and leaves (gain 0.65 +- 0.35)
    const gust = ctx.createGain(); gust.gain.value = 0.65; wind.g.connect(gust); leaves.g.connect(gust); gust.connect(out);
    const lfo = ctx.createOscillator(), lg = ctx.createGain(); lfo.frequency.value = 0.11; lg.gain.value = 0.35;
    lfo.connect(lg); lg.connect(gust.gain); lfo.start();
    // voices: synthesised babble, looped
    const voices = ctx.createBufferSource(); voices.buffer = babble(ctx); voices.loop = true;
    const vg = ctx.createGain(); vg.gain.value = 0; voices.connect(vg).connect(out); voices.start();
    this.g = { traffic: traffic.g, voices: vg, wind: wind.g, leaves: leaves.g, tram: tram.g, squeal: squeal.g, pass: pass.g };
  }

  async load() {
    const m = (await (await fetch('/audio/soundmap.json')).json()) as SoundMap;
    m.roads.forEach((r, i) => this.roadG.add(i, r[0] - CELL, r[1] - CELL, r[0] + CELL, r[1] + CELL));
    m.green.forEach((r, i) => this.greenG.add(i, r[0] - r[2] - 40, r[1] - r[2] - 40, r[0] + r[2] + 40, r[1] + r[2] + 40));
    m.squares.forEach((r, i) => this.sqG.add(i, r[0] - r[2] - 60, r[1] - r[2] - 60, r[0] + r[2] + 60, r[1] + r[2] + 60));
    this.map = m;
  }

  private sense(x: number, y: number) {
    const m = this.map!; let road = 0, green = 0, sq = 0;
    for (const i of this.roadG.at(x, y)) {
      const r = m.roads[i], d = Math.hypot(r[0] - x, r[1] - y);
      if (d < 110) road = Math.max(road, (r[2] / 10) * (1 - d / 110) ** 1.5);
    }
    for (const i of this.greenG.at(x, y)) { const r = m.green[i]; green = Math.max(green, clamp(1 - (Math.hypot(r[0] - x, r[1] - y) - r[2]) / 40)); }
    for (const i of this.sqG.at(x, y)) { const r = m.squares[i]; sq = Math.max(sq, clamp(1 - (Math.hypot(r[0] - x, r[1] - y) - r[2]) / 60)); }
    this.road = road; this.green = green; this.square = sq;
  }

  /** Screen-relative stereo position of a world point, -1 (left) .. 1 (right). */
  private pan(h: number, dx: number, dy: number) { const d = Math.hypot(dx, dy) || 1; return clamp((dx * Math.cos(h) - dy * Math.sin(h)) / d, -0.9, 0.9); }

  update(dt: number, s: AmbIn) {
    const ctx = this.ctx, now = ctx.currentTime, day = 1 - s.night;
    this.strike(now);
    this.t -= dt;
    if (!this.map || this.t > 0) return;
    this.sense(s.x, s.y);
    this.t = 0.25 + dt;
    const { road, green, square } = this, set = (n: GainNode, v: number) => n.gain.setTargetAtTime(v, now, 0.4);
    const dens = s.density, lull = 0.55 + 0.45 * day;
    set(this.g.traffic, (0.012 + 0.2 * road) * lull);
    this.trafficLp.frequency.setTargetAtTime(280 + road * 650, now, 0.4);
    set(this.g.voices, 0.17 * clamp(square + 0.3 * road + 0.08) * dens * (1 - 0.35 * green));
    set(this.g.wind, (0.012 + 0.03 * green + 0.01 * road) * (0.6 + 0.4 * day));
    set(this.g.leaves, 0.03 * green * day);
    // passing cars: short band-pass sweeps, panned across
    this.passT -= 0.25;
    if (road > 0.2 && this.passT <= 0) {
      this.passT = (1.5 + Math.random() * 3.5) / road;
      const dir = Math.random() < 0.5 ? -1 : 1, f0 = 330 + Math.random() * 200;
      this.passBp.frequency.cancelScheduledValues(now); this.passBp.frequency.setValueAtTime(f0, now); this.passBp.frequency.linearRampToValueAtTime(f0 * 0.8, now + 2.2);
      this.passPan.pan.setValueAtTime(-0.8 * dir, now); this.passPan.pan.linearRampToValueAtTime(0.8 * dir, now + 2.2);
      const g = this.g.pass.gain; g.cancelScheduledValues(now); g.setValueAtTime(0, now);
      g.linearRampToValueAtTime(0.09 * road * lull, now + 1.0); g.linearRampToValueAtTime(0, now + 2.2);
    }
    // trams: rolling rumble by distance, squeal in curves
    let best = 1e9, bt: AmbIn['trams'][number] | null = null;
    for (const v of s.trams) { const d = Math.hypot(v.x - s.x, v.y - s.y); if (d < best) { best = d; bt = v; } }
    if (bt && best < 70) {
      const p = this.prevTram;
      if (Math.hypot(bt.x - p.x, bt.y - p.y) < 8) { let dh = bt.heading - p.h; dh = Math.atan2(Math.sin(dh), Math.cos(dh)); this.turn = Math.abs(dh) / 0.25; }
      this.prevTram = { x: bt.x, y: bt.y, h: bt.heading };
      const k = (1 - best / 70) ** 2;
      set(this.g.tram, 0.16 * k); set(this.g.squeal, clamp(this.turn * 4) * 0.045 * k);
      this.tramPan.pan.setTargetAtTime(this.pan(s.heading, bt.x - s.x, bt.y - s.y), now, 0.3);
    } else { set(this.g.tram, 0); set(this.g.squeal, 0); this.turn = 0; }
    // birds by day, more in parks
    this.birdT -= 0.25;
    if (day > 0.6 && this.birdT <= 0) {
      const lvl = 0.12 + 0.88 * green;
      this.birdT = (2 + Math.random() * 5) / lvl;
      this.chirp(now, 0.02 + 0.035 * lvl);
    }
    // faint bike bell now and then in lively streets
    this.bikeT -= 0.25;
    if (this.bikeT <= 0) {
      this.bikeT = 35 + Math.random() * 50;
      if (day > 0.5 && dens > 0.4 && (road > 0.15 || square > 0.1)) this.ping(now, 0.035);
    }
    // church bells at full hour
    if (s.hour !== this.lastHour) {
      if (this.lastHour >= 0 && this.strikes === 0) this.startBells(s);
      this.lastHour = s.hour;
    }
  }

  private startBells(s: AmbIn) {
    let best = 1e9, bx = 0, by = 0;
    for (const c of this.map!.churches) { const d = Math.hypot(c[0] - s.x, c[1] - s.y); if (d < best) { best = d; bx = c[0]; by = c[1]; } }
    if (best > 320) return;
    this.bellVol = 0.16 * (1 - best / 320) ** 1.4 * (s.night > 0.5 ? 0.6 : 1);
    this.bellPan = this.pan(s.heading, bx - s.x, by - s.y);
    this.strikes = Math.min(12, s.hour % 12 || 12); this.strikeT = this.ctx.currentTime + 0.3;
  }

  private strike(now: number) {
    if (this.strikes <= 0 || now < this.strikeT - 0.05) return;
    const ctx = this.ctx, pan = ctx.createStereoPanner(); pan.pan.value = this.bellPan; pan.connect(this.out);
    const t = Math.max(now, this.strikeT);
    // inharmonic bell partials around ~ 330 Hz
    [[0.5, 0.5, 7], [1, 1, 6], [1.2, 0.45, 5], [1.5, 0.3, 4], [2, 0.55, 3.5], [2.7, 0.25, 2.5], [4.1, 0.12, 1.8]].forEach(([r, a, dec]) => {
      const o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.value = 330 * r;
      g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(this.bellVol * a * 0.5, t + 0.008); g.gain.exponentialRampToValueAtTime(0.0001, t + dec);
      o.connect(g).connect(pan); o.start(t); o.stop(t + dec + 0.1);
    });
    this.strikes--; this.strikeT = t + 1.9;
  }

  private chirp(t: number, vol: number) {
    const ctx = this.ctx, pan = ctx.createStereoPanner(); pan.pan.value = Math.random() * 1.8 - 0.9; pan.connect(this.out);
    const f = 2400 + Math.random() * 2200, n = 2 + Math.floor(Math.random() * 4), gap = 0.07 + Math.random() * 0.06;
    for (let i = 0; i < n; i++) {
      const o = ctx.createOscillator(), g = ctx.createGain(), t0 = t + i * gap;
      o.frequency.setValueAtTime(f * (1 + Math.random() * 0.15), t0); o.frequency.exponentialRampToValueAtTime(f * (1.3 + Math.random() * 0.4), t0 + 0.06);
      g.gain.setValueAtTime(vol, t0); g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.07);
      o.connect(g).connect(pan); o.start(t0); o.stop(t0 + 0.09);
    }
  }

  private ping(t: number, vol: number) {
    const ctx = this.ctx, pan = ctx.createStereoPanner(); pan.pan.value = Math.random() * 1.6 - 0.8; pan.connect(this.out);
    [0, 0.14].forEach((d) => {
      const o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.value = 2637;
      g.gain.setValueAtTime(vol, t + d); g.gain.exponentialRampToValueAtTime(0.0001, t + d + 0.4);
      o.connect(g).connect(pan); o.start(t + d); o.stop(t + d + 0.45);
    });
  }
}

/** ~8 s of crowd babble: several talkers, each a pulse train shaped by two moving formant resonators and syllable envelopes. */
function babble(ctx: AudioContext): AudioBuffer {
  const sr = 16000, n = sr * 8, buf = ctx.createBuffer(1, n, sr), d = buf.getChannelData(0);
  for (let tk = 0; tk < 7; tk++) {
    const f0 = 95 + Math.random() * 130; let ph = 0, y1a = 0, y2a = 0, y1b = 0, y2b = 0, i = 0;
    while (i < n) {
      const len = Math.floor(sr * (0.1 + Math.random() * 0.17)), gap = Math.random() < 0.35 ? Math.floor(sr * Math.random() * 0.6) : 0;
      const F1 = 330 + Math.random() * 450, F2 = 950 + Math.random() * 1400, c1 = 2 * Math.exp(-Math.PI * 90 / sr) * Math.cos(2 * Math.PI * F1 / sr), r1 = Math.exp(-2 * Math.PI * 90 / sr);
      const c2 = 2 * Math.exp(-Math.PI * 140 / sr) * Math.cos(2 * Math.PI * F2 / sr), r2 = Math.exp(-2 * Math.PI * 140 / sr);
      const bend = 1 + (Math.random() - 0.5) * 0.25;
      for (let k = 0; k < len && i < n; k++, i++) {
        const env = Math.sin(Math.PI * k / len) ** 2;
        ph += f0 * (1 + (bend - 1) * k / len) / sr; ph -= Math.floor(ph);
        const ex = ((ph < 0.04 ? 1 : 0) + (Math.random() - 0.5) * 0.15) * env;
        const a = ex + c1 * y1a - r1 * y2a; y2a = y1a; y1a = a;
        const b = ex + c2 * y1b - r2 * y2b; y2b = y1b; y1b = b;
        d[i] += (a * 0.03 + b * 0.05);
      }
      i += gap;
    }
  }
  let mx = 0; for (let i = 0; i < n; i++) mx = Math.max(mx, Math.abs(d[i]));
  const sc = 0.9 / (mx || 1), fade = Math.floor(sr * 0.05);
  for (let i = 0; i < n; i++) d[i] *= sc * Math.min(1, i / fade, (n - i) / fade);
  return buf;
}
