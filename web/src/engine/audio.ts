/**
 * Procedural sound (WebAudio, no files): city ambience (filtered noise, louder by day), birds by day,
 * tram bell, bike bell, comic police siren, mission jingles. Starts on the first user gesture (autoplay rules).
 */
import { Ambience, type AmbIn } from './audio_amb';
import { Music } from './audio_music';

export class Audio {
  private ctx: AudioContext | null = null;
  private master!: GainNode;
  private amb!: GainNode;
  private sirenOsc: OscillatorNode | null = null;
  private sirenGain: GainNode | null = null;
  private amb2: Ambience | null = null;
  private eng: { o1: OscillatorNode; o2: OscillatorNode; g: GainNode; lp: BiquadFilterNode; tyre: GainNode } | null = null;
  muted = false;
  music: Music | null = null;
  private musicOn = true;
  private musicVol = 0.5;

  constructor() {
    // browsers (iOS: touchend/click only) unlock audio on a user gesture; keep trying until the context is running
    const evs = ['pointerdown', 'pointerup', 'touchend', 'click', 'keydown'];
    const start = () => {
      this.init();
      void this.ctx?.resume();
      if (this.ctx?.state === 'running') evs.forEach((e) => window.removeEventListener(e, start));
    };
    evs.forEach((e) => window.addEventListener(e, start, { passive: true }));
    document.addEventListener('visibilitychange', () => {
      if (!this.ctx) return;
      if (document.hidden) void this.ctx.suspend(); else void this.ctx.resume();
    });
  }

  private init() {
    if (this.ctx) return;
    const ctx = this.ctx = new AudioContext();
    this.master = ctx.createGain(); this.master.gain.value = this.muted ? 0 : 0.8; this.master.connect(ctx.destination);
    // city hum: brown noise through a low-pass
    const len = ctx.sampleRate * 4, buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0);
    let last = 0;
    for (let i = 0; i < len; i++) { last = (last + 0.02 * (Math.random() * 2 - 1)) / 1.02; d[i] = last * 3.5; }
    const src = ctx.createBufferSource(); src.buffer = buf; src.loop = true;
    const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 700;
    this.amb = ctx.createGain(); this.amb.gain.value = 0.25;
    src.connect(lp).connect(this.amb).connect(this.master); src.start();
    // shared white noise for the place-dependent layers; map + layers are set up after the first gesture (not in the start budget)
    const nb = ctx.createBuffer(1, ctx.sampleRate * 3, ctx.sampleRate), nd = nb.getChannelData(0);
    for (let i = 0; i < nd.length; i++) nd[i] = Math.random() * 2 - 1;
    this.music = new Music(ctx, this.master);
    this.music.setVolume(this.musicVol);
    this.music.setEnabled(this.musicOn);
    // music streams only after the first gesture + a short delay (not part of the start budget; ?nomusic for tests)
    if (!location.search.includes('nomusic')) setTimeout(() => this.music?.start(), 1500);
    setTimeout(() => {
      if (location.search.includes('noamb')) return;
      const a = new Ambience(ctx, this.master, nb);
      a.load().then(() => { this.amb2 = a; }).catch(() => { /* no ambience map: keep the city hum only */ });
    }, 400);
  }

  setMuted(m: boolean) { this.muted = m; if (this.ctx) this.master.gain.value = m ? 0 : 0.8; }

  setMusic(on: boolean, vol: number) { this.musicOn = on; this.musicVol = vol; this.music?.setEnabled(on); this.music?.setVolume(vol); }

  private tone(freq: number, t0: number, dur: number, type: OscillatorType = 'sine', vol = 0.2, bend = 1) {
    const ctx = this.ctx!; const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type; o.frequency.setValueAtTime(freq, t0); o.frequency.exponentialRampToValueAtTime(freq * bend, t0 + dur);
    g.gain.setValueAtTime(vol, t0); g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g).connect(this.master); o.start(t0); o.stop(t0 + dur + 0.05);
  }

  /** Zürich tram «ding ding». */
  tramBell(vol = 0.25) { if (!this.ctx) return; const t = this.ctx.currentTime; this.tone(1568, t, 0.6, 'triangle', vol); this.tone(1568, t + 0.28, 0.7, 'triangle', vol); }
  /** Short double honk. */
  honk() { if (!this.ctx) return; const t = this.ctx.currentTime; this.tone(392, t, 0.18, 'square', 0.06); this.tone(370, t + 0.22, 0.25, 'square', 0.06); }
  bikeBell() { if (!this.ctx) return; const t = this.ctx.currentTime; this.tone(2637, t, 0.35, 'sine', 0.15); this.tone(2637, t + 0.12, 0.4, 'sine', 0.12); }
  /** Car door / thud on impact. */
  carDoor() { if (!this.ctx) return; const t = this.ctx.currentTime; this.tone(160, t, 0.12, 'square', 0.12, 0.5); this.tone(95, t + 0.05, 0.14, 'sine', 0.2, 0.6); }
  /** Crash thud + metal crunch, scaled by strength 0..1; `dead` adds a last cough of the engine. */
  carCrash(strength: number, dead = false) {
    if (!this.ctx) return; this.music?.duck(); const ctx = this.ctx, t = ctx.currentTime, s = Math.max(0.15, Math.min(1, strength));
    this.tone(120, t, 0.25 + 0.2 * s, 'sawtooth', 0.08 + 0.2 * s, 0.4); this.tone(60, t, 0.3 + 0.3 * s, 'sine', 0.15 + 0.35 * s, 0.5);
    const len = Math.floor(ctx.sampleRate * (0.15 + 0.35 * s)), buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len) ** 2;
    const src = ctx.createBufferSource(), bp = ctx.createBiquadFilter(), g = ctx.createGain();
    src.buffer = buf; bp.type = 'bandpass'; bp.frequency.value = 500 + 1500 * s; bp.Q.value = 0.6; g.gain.value = 0.15 + 0.5 * s;
    src.connect(bp).connect(g).connect(this.master); src.start(t);
    if (dead) this.tone(70, t + 0.25, 0.5, 'sawtooth', 0.1, 0.3);
  }
  /** Breaking glass: short high noise burst. */
  glass() {
    if (!this.ctx) return; const ctx = this.ctx, t = ctx.currentTime;
    const len = Math.floor(ctx.sampleRate * 0.35), buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len) ** 3 * (Math.random() < 0.5 ? 1 : 0.3);
    const src = ctx.createBufferSource(), hp = ctx.createBiquadFilter(), g = ctx.createGain();
    src.buffer = buf; hp.type = 'highpass'; hp.frequency.value = 3000; g.gain.value = 0.25;
    src.connect(hp).connect(g).connect(this.master); src.start(t);
  }
  /**
   * Engine + tyre noise while driving. rpm 0..1, load 0..1, slip = lateral/braking squeal amount. Called every frame
   * while driving and once with on = false to fade it out.
   */
  engine(rpm: number, load: number, slip: number, on: boolean, speed = 0) {
    if (!this.ctx) return;
    const ctx = this.ctx;
    if (!this.eng) {
      const o1 = ctx.createOscillator(), o2 = ctx.createOscillator(), g = ctx.createGain(), lp = ctx.createBiquadFilter();
      o1.type = 'sawtooth'; o2.type = 'square'; lp.type = 'lowpass'; g.gain.value = 0;
      o1.connect(lp); o2.connect(lp); lp.connect(g).connect(this.master); o1.start(); o2.start();
      // tyre / road noise: looping noise through a band-pass
      const len = ctx.sampleRate * 2, buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0);
      for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
      const src = ctx.createBufferSource(); src.buffer = buf; src.loop = true;
      const bp = ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 900; bp.Q.value = 0.7;
      const tyre = ctx.createGain(); tyre.gain.value = 0;
      src.connect(bp).connect(tyre).connect(this.master); src.start();
      this.eng = { o1, o2, g, lp, tyre };
    }
    const e = this.eng, t = ctx.currentTime;
    const f = 38 + rpm * 95;
    e.o1.frequency.setTargetAtTime(f, t, 0.05); e.o2.frequency.setTargetAtTime(f * 0.5, t, 0.05);
    e.lp.frequency.setTargetAtTime(260 + rpm * 500 + load * 700, t, 0.08);
    e.g.gain.setTargetAtTime(on ? 0.035 + 0.05 * load + 0.02 * rpm : 0, t, 0.1);
    e.tyre.gain.setTargetAtTime(on ? Math.min(0.1, Math.abs(speed) * 0.0022 + Math.min(1, slip) * 0.06) : 0, t, 0.1);
  }
  private humN: { o: OscillatorNode; g: GainNode } | null = null;
  /** Very quiet electric-motor whine of the e-scooter (speed in m/s); call each frame while riding and once with on = false. */
  hum(speed: number, on: boolean) {
    if (!this.ctx) return;
    const ctx = this.ctx, t = ctx.currentTime;
    if (!this.humN) {
      if (!on) return;
      const o = ctx.createOscillator(), g = ctx.createGain(), lp = ctx.createBiquadFilter();
      o.type = 'triangle'; lp.type = 'lowpass'; lp.frequency.value = 1400; g.gain.value = 0;
      o.connect(lp).connect(g).connect(this.master); o.start();
      this.humN = { o, g };
    }
    this.humN.o.frequency.setTargetAtTime(210 + speed * 75, t, 0.06);
    this.humN.g.gain.setTargetAtTime(on ? Math.min(0.022, speed * 0.005) : 0, t, 0.12);
  }
  jingle(ok: boolean) {
    if (!this.ctx) return; const t = this.ctx.currentTime;
    (ok ? [523, 659, 784, 1047] : [392, 330, 262]).forEach((f, i) => this.tone(f, t + i * 0.13, 0.35, 'square', 0.08));
  }

  /** Per-frame: place-dependent ambience (layers in audio_amb.ts), siren while wanted. */
  update(dt: number, night: number, wanted: boolean, policeDist: number, amb?: AmbIn) {
    if (!this.ctx) return;
    this.amb.gain.value = 0.05 + 0.07 * (1 - night); // far city hum; near roads the traffic layer adds to it
    if (amb) this.amb2?.update(dt, amb);
    this.music?.update(dt, night, wanted && policeDist < 120);
    if (wanted && policeDist < 120) {
      if (!this.sirenOsc) {
        const ctx = this.ctx;
        this.sirenOsc = ctx.createOscillator(); this.sirenOsc.type = 'sawtooth';
        const lfo = ctx.createOscillator(), lg = ctx.createGain(); lfo.frequency.value = 0.9; lg.gain.value = 180;
        lfo.connect(lg).connect(this.sirenOsc.frequency); this.sirenOsc.frequency.value = 760;
        const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 1800;
        this.sirenGain = ctx.createGain(); this.sirenGain.gain.value = 0;
        this.sirenOsc.connect(lp).connect(this.sirenGain).connect(this.master); this.sirenOsc.start(); lfo.start();
      }
      this.sirenGain!.gain.value = 0.06 * Math.max(0, 1 - policeDist / 120);
    } else if (this.sirenGain) this.sirenGain.gain.value = 0;
  }
}
