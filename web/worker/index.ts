/**
 * The one server-side route of the otherwise static site: `POST /api/report` turns a bug report from the game
 * (ui/report.ts, Menü → «Fehler melden») into a GitHub issue, using the maintainer's token. Players need no GitHub
 * account; the token never reaches the browser (docs/DECISIONS.md #80, setup in docs/DEPLOY.md).
 * Everything else is served from `dist/` as static assets (wrangler.jsonc: `run_worker_first: ["/api/*"]`).
 *
 * Secret: REPORT_GITHUB_TOKEN (fine-grained PAT, «Issues: Read and write» on REPORT_REPO). Without it the route answers
 * 503 and the game falls back to the pre-filled GitHub link. Vars: REPORT_REPO, REPORT_GITHUB_API (tests use a stub).
 * Abuse guard: same-origin only, size limits, rate-limit bindings per client IP and for everyone (wrangler.jsonc).
 */
interface RateLimit { limit(opts: { key: string }): Promise<{ success: boolean }> }
export interface Env {
  REPORT_GITHUB_TOKEN?: string;
  REPORT_REPO?: string;
  REPORT_GITHUB_API?: string;
  REPORT_LIMIT_IP?: RateLimit;
  REPORT_LIMIT_ALL?: RateLimit;
}

const ROUTE = '/api/report';
const MAX_JSON = 16_000, MAX_TITLE = 120, MAX_BODY = 8_000;
const LABELS = ['bug'];
const PROVENANCE = '_Aus dem Spiel gemeldet (Menü → «Fehler melden»)._';
const USER_AGENT = 'sandboxzurich-report (+https://github.com/dgnaegi/sandboxzurich)';

const json = (status: number, data: unknown) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });
/** Error codes are stable strings; ui/report.ts translates them for the player. */
const fail = (status: number, error: string) => json(status, { error });

/** Browsers send `Origin` on every fetch POST; only this site (or a dev server) may post. Scripts can fake it, the rate limit handles those. */
function sameOrigin(request: Request, url: URL): boolean {
  const origin = request.headers.get('origin');
  if (!origin) return false;
  if (origin === url.origin) return true;
  try { return /^(localhost|127\.0\.0\.1)$/.test(new URL(origin).hostname); } catch { return false; }
}

async function limited(request: Request, env: Env): Promise<boolean> {
  const ip = request.headers.get('cf-connecting-ip') ?? 'unknown';
  const limits: [RateLimit | undefined, string][] = [[env.REPORT_LIMIT_IP, ip], [env.REPORT_LIMIT_ALL, 'all']];
  for (const [rl, key] of limits) if (rl && !(await rl.limit({ key })).success) return true;
  return false;
}

interface Draft { title: string; body: string }
/** Validates the JSON the game sends; null when it is not a report. */
async function parse(request: Request): Promise<Draft | null> {
  if (Number(request.headers.get('content-length') ?? 0) > MAX_JSON) return null;
  const text = await request.text();
  if (text.length > MAX_JSON) return null;
  let data: unknown;
  try { data = JSON.parse(text); } catch { return null; }
  if (!data || typeof data !== 'object') return null;
  const { title, body } = data as Record<string, unknown>;
  if (typeof title !== 'string' || typeof body !== 'string') return null;
  const t = title.replace(/\s+/g, ' ').trim(), b = body.trim();
  if (!t || !b || t.length > MAX_TITLE || b.length > MAX_BODY) return null;
  return { title: t, body: b };
}

async function createIssue(request: Request, env: Env, url: URL): Promise<Response> {
  if (!sameOrigin(request, url)) return fail(403, 'origin');
  const token = env.REPORT_GITHUB_TOKEN, repo = env.REPORT_REPO ?? '';
  if (!token || !/^[\w.-]+\/[\w.-]+$/.test(repo)) return fail(503, 'unavailable');
  if (await limited(request, env)) return fail(429, 'ratelimit');
  const draft = await parse(request);
  if (!draft) return fail(400, 'invalid');

  const api = (env.REPORT_GITHUB_API ?? 'https://api.github.com').replace(/\/+$/, '');
  let res: Response;
  try {
    res = await fetch(`${api}/repos/${repo}/issues`, {
      method: 'POST',
      headers: {
        authorization: `Bearer ${token}`, accept: 'application/vnd.github+json', 'x-github-api-version': '2022-11-28',
        'user-agent': USER_AGENT, 'content-type': 'application/json',
      },
      body: JSON.stringify({ title: draft.title, body: `${PROVENANCE}\n\n${draft.body}`, labels: LABELS }),
      signal: AbortSignal.timeout(10_000),
    });
  } catch (e) {
    console.error('report: github unreachable', (e as Error).message);
    return fail(502, 'github');
  }
  if (!res.ok) {
    console.error('report: github', res.status, (await res.text()).slice(0, 300));
    return fail(502, 'github');
  }
  const issue = await res.json() as { html_url?: string; number?: number };
  if (!issue.html_url || !issue.number) return fail(502, 'github');
  return json(201, { url: issue.html_url, number: issue.number });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname !== ROUTE) return fail(404, 'notfound');
    if (request.method !== 'POST') return new Response(null, { status: 405, headers: { allow: 'POST' } });
    return createIssue(request, env, url);
  },
};
