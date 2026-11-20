import { readFile } from 'node:fs/promises';
// Runs HelioFleet's own alignment search (js/tools.js) for comparison.
// Usage: node page_alignments.mjs /path/to/heliofleet/ '<json list of queries>'
const ROOT = process.argv[2].replace(/\/?$/, '/');
globalThis.fetch = async (url) => { const p = String(url).split('?')[0];
  try { const t = await readFile(ROOT + p, 'utf8'); return { ok: true, status: 200, json: async () => JSON.parse(t) }; }
  catch { return { ok: false, status: 404, json: async () => null }; } };
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
const { loadManifest, dateFromJD } = await import(ROOT + 'js/ephem.js');
const { findAlignments } = await import(ROOT + 'js/tools.js');
await loadManifest();
const jd = (s) => Date.parse(s) / 864e5 + 2440587.5;
const iso = (j) => dateFromJD(j + 1 / 172800).toISOString().slice(0, 19) + 'Z';
const qs = JSON.parse(process.argv[3]);
const out = [];
for (const q of qs) {
  const r = await findAlignments({ kind: q.kind, a: q.a, b: q.b, tol: q.tol, jd0: jd(q.from + 'T00:00Z'), jd1: jd(q.to + 'T00:00Z'), wind: 400 });
  out.push(r.windows.map((w) => [iso(w.start), iso(w.end), iso(w.best), +w.value.toFixed(3)]));
}
console.log(JSON.stringify(out));
