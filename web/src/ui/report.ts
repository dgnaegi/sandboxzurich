import { BUILD } from '../engine/assetver';

/**
 * «Fehler melden»: a pre-filled GitHub issue with what the player saw, where they stood and what the device was.
 * Nothing leaves the browser until the player submits the issue on GitHub: static site, no server, no token
 * (docs/DECISIONS.md #80). The issue tracker is https://github.com/<REPO>/issues.
 * The module also keeps the last console errors so a report can include them (installed at import time).
 */
export const REPO = 'dgnaegi/sandboxzurich';
const TEMPLATE = 'bug_report.md';   // .github/ISSUE_TEMPLATE/bug_report.md; title and body from the query replace its text
const MAX_ERRORS = 5, MAX_TEXT = 1500;
const WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

/** What main.ts knows about the moment of the report. */
export interface ReportInfo {
  x: number; y: number; z: number; yaw: number;
  /** zu Fuss | Velo (…) | Trottinett | Auto (…) | Bus | Tram */
  mode: string;
  /** m/s */
  speed: number;
  mobile: boolean;
  /** Quality governor state, e.g. "q1, Post aus, 1.25x" */
  quality: string;
  fps: number; calls: number;
  /** Game clock HH:MM and weekday (0 = Mo) */
  time: string; day: number;
}

export interface Report { title: string; body: string }

// --- recent errors (ring buffer, never sent anywhere by itself) -----------------------------------------
const errors: string[] = [];
const safe = (v: unknown): string => { try { return typeof v === 'string' ? v : v instanceof Error ? v.message : JSON.stringify(v) ?? String(v); } catch { return String(v); } };
function remember(msg: string) {
  const m = msg.replace(/\s+/g, ' ').trim().slice(0, 160);
  if (!m || errors[errors.length - 1] === m) return;
  errors.push(m);
  if (errors.length > MAX_ERRORS) errors.shift();
}
window.addEventListener('error', (e) => remember(e.message || safe(e.error)));
window.addEventListener('unhandledrejection', (e) => remember(safe(e.reason)));
const consoleError = console.error.bind(console);
console.error = (...a: unknown[]) => { remember(a.map(safe).join(' ')); consoleError(...a); };
/** Last console errors / unhandled rejections (newest last). */
export const recentErrors = (): readonly string[] => errors;

// --- report text -------------------------------------------------------------------------------------------
/** `?at=x,y,yaw,z&t=HH:MM&day=N` on the current origin: the maintainer lands exactly where the player stood. */
export function deepLink(i: ReportInfo): string {
  const q = `at=${i.x.toFixed(1)},${i.y.toFixed(1)},${i.yaw.toFixed(2)},${i.z.toFixed(1)}&t=${i.time}&day=${i.day}`;
  return `${location.origin}${location.pathname}?${q}`;
}

const text = (id: string) => document.getElementById(id)?.textContent?.trim() ?? '';

/** The automatic part of the report (Markdown); the player sees it before sending. */
export function context(i: ReportInfo): string {
  const place = text('place-name'), kreis = text('place-kreis');
  const net = (navigator as unknown as { connection?: { effectiveType?: string } }).connection?.effectiveType;
  const lines = [
    `**Ort:** ${[place, kreis].filter(Boolean).join(', ') || 'unbekannt'} · x ${i.x.toFixed(1)}, y ${i.y.toFixed(1)}, z ${i.z.toFixed(1)}`,
    `**Direkt dorthin:** ${deepLink(i)}`,
    `**Unterwegs:** ${i.mode}${i.speed > 0.5 ? `, ${Math.round(i.speed * 3.6)} km/h` : ''}`,
    `**Spielzeit:** ${WEEKDAYS[i.day] ?? ''} ${i.time}`,
    `**Gerät:** ${i.mobile ? 'Handy/Tablet' : 'PC'}, ${innerWidth}×${innerHeight} @${devicePixelRatio}x${net ? `, Netz ${net}` : ''}`,
    `**Browser:** ${navigator.userAgent}`,
    `**Grafik:** ${i.quality}, ${i.fps} fps, ${i.calls} Draw Calls`,
    `**Build:** ${BUILD}`,
  ];
  if (errors.length) lines.push('', '**Letzte Fehlermeldungen:**', '```', ...errors, '```');
  return lines.join('\n');
}

export function report(i: ReportInfo, what: string): Report {
  const place = text('place-name');
  const title = `Fehler: ${place || `bei ${i.x.toFixed(0)}, ${i.y.toFixed(0)}`}`;
  const body = ['**Was ist passiert?**', what.trim().slice(0, MAX_TEXT) || '_(bitte beschreiben)_', '', context(i)].join('\n');
  return { title, body };
}

const enc = encodeURIComponent;
/** GitHub pre-fills title and body from the query; the template supplies the label and the headings for issues opened by hand. */
export const issueUrl = (r: Report) => `https://github.com/${REPO}/issues/new?template=${TEMPLATE}&labels=bug&title=${enc(r.title)}&body=${enc(r.body)}`;

// --- menu page ---------------------------------------------------------------------------------------------
/** Fills the «Fehler melden» page of the menu; call `refresh()` when the page opens. */
export function bindReportPage(page: HTMLElement, info: () => ReportInfo | null) {
  const q = <T extends HTMLElement>(s: string) => page.querySelector<T>(s)!;
  const what = q<HTMLTextAreaElement>('#r-text'), pre = q<HTMLPreElement>('#r-info'), github = q<HTMLAnchorElement>('#r-github');
  let snap: ReportInfo | null = null;
  const link = () => { if (snap) github.href = issueUrl(report(snap, what.value)); };
  const refresh = () => {
    snap = info();
    pre.textContent = snap ? context(snap).replace(/\*\*/g, '') : 'Das Spiel ist noch nicht geladen.';
    link();
  };
  what.maxLength = MAX_TEXT;
  what.addEventListener('input', link);
  return { refresh };
}
