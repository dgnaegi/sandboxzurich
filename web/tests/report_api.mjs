// QA: the /api/report Worker (worker/index.ts) without Cloudflare. esbuild bundles it, the test calls fetch() with a fake
// env (token, rate-limit bindings) and a stubbed GitHub API: method/path/origin checks, missing token -> 503, rate limit
// -> 429, invalid or oversized JSON -> 400, GitHub error -> 502, happy path -> 201 with issue url/number and the request
// GitHub receives (repo, bearer token, label, provenance line). Usage: node tests/report_api.mjs
import { build } from 'esbuild';

const { outputFiles: [out] } = await build({ entryPoints: [new URL('../worker/index.ts', import.meta.url).pathname], bundle: true, write: false, format: 'esm', platform: 'neutral', target: 'es2022', logLevel: 'silent' });
const worker = (await import(`data:text/javascript;base64,${Buffer.from(out.text).toString('base64')}`)).default;

let fails = 0;
const check = (name, ok, extra = '') => { console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${extra ? '  ' + extra : ''}`); if (!ok) fails++; };

// --- stubbed GitHub ----------------------------------------------------------------------------------------
const calls = [];
const created = () => new Response(JSON.stringify({ html_url: 'https://github.com/dgnaegi/sandboxzurich/issues/42', number: 42 }), { status: 201 });
let github = created;
globalThis.fetch = async (url, init) => { calls.push({ url: String(url), init }); return github(String(url), init); };

const ORIGIN = 'https://sandboxzurich.example';
const allow = { limit: async () => ({ success: true }) }, deny = { limit: async () => ({ success: false }) };
const ENV = { REPORT_GITHUB_TOKEN: 'ghp_test', REPORT_REPO: 'dgnaegi/sandboxzurich', REPORT_LIMIT_IP: allow, REPORT_LIMIT_ALL: allow };
const REPORT = { title: 'Fehler: Bullingerplatz', body: '**Was ist passiert?**\nAuto verschwunden\n\n**Ort:** Bullingerplatz · x 789.0, y -873.0, z 2.0' };
const post = (body, { origin = ORIGIN, env = ENV, headers = {}, method = 'POST', path = '/api/report' } = {}) =>
  worker.fetch(new Request(`${ORIGIN}${path}`, { method, headers: { 'content-type': 'application/json', ...(origin ? { origin } : {}), 'cf-connecting-ip': '203.0.113.7', ...headers }, body: method === 'POST' ? (typeof body === 'string' ? body : JSON.stringify(body)) : undefined }), env);
const body = async (res) => { try { return await res.json(); } catch { return {}; } };

let r = await post(null, { method: 'GET' });
check('GET -> 405', r.status === 405 && r.headers.get('allow') === 'POST');
r = await post(REPORT, { path: '/api/other' });
check('unknown path -> 404', r.status === 404 && (await body(r)).error === 'notfound');
r = await post(REPORT, { origin: '' });
check('no Origin -> 403', r.status === 403 && (await body(r)).error === 'origin');
r = await post(REPORT, { origin: 'https://evil.example' });
check('foreign Origin -> 403', r.status === 403);
r = await post(REPORT, { origin: 'http://localhost:5173' });
check('localhost Origin allowed (dev)', r.status === 201);
r = await post(REPORT, { env: { ...ENV, REPORT_GITHUB_TOKEN: undefined } });
check('no token -> 503 unavailable', r.status === 503 && (await body(r)).error === 'unavailable');
r = await post(REPORT, { env: { ...ENV, REPORT_REPO: 'not a repo' } });
check('bad repo var -> 503', r.status === 503);
r = await post(REPORT, { env: { ...ENV, REPORT_LIMIT_IP: deny } });
check('ip rate limit -> 429', r.status === 429 && (await body(r)).error === 'ratelimit');
r = await post(REPORT, { env: { ...ENV, REPORT_LIMIT_ALL: deny } });
check('global rate limit -> 429', r.status === 429);
r = await post(REPORT, { env: { REPORT_GITHUB_TOKEN: 'x', REPORT_REPO: 'a/b' } });
check('works without rate-limit bindings (wrangler dev)', r.status === 201);
r = await post('{not json');
check('invalid JSON -> 400', r.status === 400 && (await body(r)).error === 'invalid');
r = await post({ title: 'x' });
check('missing body -> 400', r.status === 400);
r = await post({ title: '  ', body: 'x' });
check('blank title -> 400', r.status === 400);
r = await post({ title: 'x'.repeat(121), body: 'ok' });
check('title too long -> 400', r.status === 400);
r = await post({ title: 'ok', body: 'x'.repeat(20_000) });
check('oversized -> 400', r.status === 400);
r = await post({ title: 'ok', body: 'x', extra: 1 });
check('extra fields ignored', r.status === 201);

const before = calls.length;
github = () => new Response('{"message":"Bad credentials"}', { status: 401 });
r = await post(REPORT);
check('GitHub 401 -> 502 github', r.status === 502 && (await body(r)).error === 'github' && calls.length === before + 1);
github = () => { throw new TypeError('fetch failed'); };
r = await post(REPORT);
check('GitHub unreachable -> 502', r.status === 502);
github = () => new Response('{}', { status: 201 });
r = await post(REPORT);
check('GitHub answer without url -> 502', r.status === 502);
github = created;

calls.length = 0;
r = await post({ title: '  Fehler:   Bullingerplatz ', body: REPORT.body });
const data = await body(r), gh = calls[0], sent = gh && JSON.parse(gh.init.body), h = gh && gh.init.headers;
check('happy path -> 201 url/number', r.status === 201 && data.url === 'https://github.com/dgnaegi/sandboxzurich/issues/42' && data.number === 42, JSON.stringify(data));
check('GitHub request: repo url, POST', gh && gh.url === 'https://api.github.com/repos/dgnaegi/sandboxzurich/issues' && gh.init.method === 'POST');
check('GitHub request: bearer token, api version, user agent', h && h.authorization === 'Bearer ghp_test' && h['x-github-api-version'] === '2022-11-28' && /sandboxzurich/.test(h['user-agent']) && h.accept === 'application/vnd.github+json');
check('GitHub request: title squeezed, label bug, provenance line + body', sent && sent.title === 'Fehler: Bullingerplatz' && sent.labels.join() === 'bug' && sent.body.startsWith('_Aus dem Spiel gemeldet') && sent.body.endsWith(REPORT.body), sent && sent.body.split('\n')[0]);
check('no-store, json response', r.headers.get('cache-control') === 'no-store' && /application\/json/.test(r.headers.get('content-type')));
r = await post(REPORT, { env: { ...ENV, REPORT_GITHUB_API: 'http://127.0.0.1:9/' } });
check('REPORT_GITHUB_API override (trailing slash)', calls[calls.length - 1].url === 'http://127.0.0.1:9/repos/dgnaegi/sandboxzurich/issues');

console.log(fails ? `REPORT_API FAIL ${fails}` : 'REPORT_API OK');
process.exit(fails ? 1 : 0);
