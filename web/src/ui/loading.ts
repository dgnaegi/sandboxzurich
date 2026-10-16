/** Start screen: game name, real progress bar (share of finished start resources), fade-out, readable errors. */
const el = () => document.getElementById('loading');

export const loading = {
  total: 19, done: 0, shown: 0, finished: false,
  /** Count one start resource as loaded when its promise resolves. */
  track<T>(p: Promise<T>): Promise<T> {
    void p.then(() => { this.done++; this.render(); }, () => {});
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
    this.done = this.total; this.render();
    e.classList.add('out');
    window.setTimeout(() => e.remove(), 700);
  },
  fail(msg: string, reload = true) {
    const e = el();
    if (!e || this.finished) return;
    e.classList.add('err');
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
