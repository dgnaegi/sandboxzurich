/**
 * Procedural sound (WebAudio, no files): city ambience (filtered noise, louder by day), birds by day,
 * tram bell, bike bell, comic police siren, mission jingles. Starts on the first user gesture (autoplay rules).
 */
export class Audio {
  private ctx: AudioContext | null = null;
  private master!: GainNode;
  private amb!: GainNode;
  private sirenOsc: OscillatorNode | null = null;
  private sirenGain: GainNode | null = null;
  private birdT = 0;
  muted = false;

  constructor() {
    const start = () => { this.init(); window.removeEventListener('pointerdown', start); window.removeEventListener('keydown', start); };
    window.addEventListener('pointerdown', start);
    window.addEventListener('keydown', start);
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
  }

  setMuted(m: boolean) { this.muted = m; if (this.ctx) this.master.gain.value = m ? 0 : 0.8; }

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
  jingle(ok: boolean) {
    if (!this.ctx) return; const t = this.ctx.currentTime;
    (ok ? [523, 659, 784, 1047] : [392, 330, 262]).forEach((f, i) => this.tone(f, t + i * 0.13, 0.35, 'square', 0.08));
  }

  /** Per-frame: ambience by daytime/activity, birds, siren while wanted. */
  update(dt: number, night: number, wanted: boolean, policeDist: number) {
    if (!this.ctx) return;
    this.amb.gain.value = 0.12 + 0.18 * (1 - night);
    this.birdT -= dt;
    if (night < 0.3 && this.birdT <= 0) {
      this.birdT = 1.5 + Math.random() * 4;
      const t = this.ctx.currentTime, f = 2500 + Math.random() * 2000;
      for (let i = 0; i < 2 + Math.floor(Math.random() * 3); i++) this.tone(f * (1 + Math.random() * 0.2), t + i * 0.09, 0.08, 'sine', 0.03, 1.4);
    }
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
