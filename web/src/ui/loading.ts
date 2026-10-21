/** Start screen: game name, real progress bar (share of finished start resources), fade-out, readable errors. */
const el = () => document.getElementById('loading');

/** Intro video (pre-rendered GTA-style slideshow). Fetched only once the first world requests are done, never blocks the game. */
const MAX_WAIT_MS = 4000, START_AT = 6;
let vidTimer = 0, vidStarted = false;

function startVideo() {
  window.clearTimeout(vidTimer);
  const v = document.getElementById('ld-video') as HTMLVideoElement | null;
  if (!v || vidStarted || loading.finished) return;
  vidStarted = true;
  const conn = (navigator as unknown as { connection?: { saveData?: boolean } }).connection;
  if (conn?.saveData || matchMedia('(prefers-reduced-motion: reduce)').matches) return; // poster only
  const sfx = matchMedia('(max-aspect-ratio: 6/5)').matches ? '_p' : '';
  for (const [ext, type] of [['webm', 'video/webm; codecs="vp9"'], ['mp4', 'video/mp4']] as const) {
    const s = document.createElement('source');
    s.src = `/loading/intro${sfx}.${ext}`; s.type = type; v.appendChild(s);
  }
  v.addEventListener('playing', () => v.classList.add('on'), { once: true });
  v.load();
  v.play().catch(() => {});
}

function stopVideo() {
  window.clearTimeout(vidTimer);
  const v = document.getElementById('ld-video') as HTMLVideoElement | null;
  if (!v) return;
  v.pause();
  v.replaceChildren();
  v.removeAttribute('src');
  v.load(); // aborts the download and frees the decoder
}

export const loading = {
  total: 19, done: 0, shown: 0, finished: false,
  /** Arm the intro video; call once at start. */
  init() { if (!vidTimer && !vidStarted) vidTimer = window.setTimeout(startVideo, MAX_WAIT_MS); },
  /** Count one start resource as loaded when its promise resolves. */
  track<T>(p: Promise<T>): Promise<T> {
    this.init();
    void p.then(() => { this.done++; this.render(); if (this.done >= START_AT) startVideo(); }, () => {});
    return p;
  },
  render() {
    const fill = document.getElementById('ld-fill');
    if (fill) fill.style.width = `${Math.min(100, Math.round((this.done / this.total) * 100))}%`;
  },
  finish() {
    const e = el();
    if (!e || this.finished) return;
    this.finished = true;
    stopVideo();
    this.done = this.total; this.render();
    e.classList.add('out');
    window.setTimeout(() => e.remove(), 700);
  },
  fail(msg: string, reload = true) {
    const e = el();
    if (!e || this.finished) return;
    e.classList.add('err');
    stopVideo();
    const m = document.getElementById('ld-msg')!;
    m.textContent = msg;
    if (reload && !e.querySelector('button')) {
      const b = document.createElement('button');
      b.textContent = 'Neu laden';
      b.addEventListener('click', () => location.reload());
      e.appendChild(b);
    }
  },
};

export function hasWebGL2(): boolean {
  try { return !!document.createElement('canvas').getContext('webgl2'); } catch { return false; }
}
