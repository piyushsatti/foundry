// Law check: no internal ids (nXX, aXX, @vN) in any DISPLAY string.
// Runs toFlow on every dataset in src/data/, expanded and fully collapsed,
// and greps every string that reaches the screen. Quotes are exempt
// (byte-exact law wins). Usage: node scripts/check-ids.mjs
import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { toFlow, detectExcursions } from '../src/transform.js';

const dataDir = path.join(path.dirname(fileURLToPath(import.meta.url)), '../src/data');
const ID_RE = /(\b[na]\d{2}(@\d+)?\b|@v?\d+\b)/;

let bad = 0;
for (const f of readdirSync(dataDir).filter((f) => f.endsWith('.json'))) {
  const data = JSON.parse(readFileSync(path.join(dataDir, f), 'utf8'));
  const allCollapsed = new Set(detectExcursions(data).map((e) => e.key));
  for (const collapsed of [new Set(), allCollapsed]) {
    const { nodes, edges, meta } = toFlow(data, collapsed);
    const strings = [meta.title, meta.date, meta.thesis, ...meta.lines.map((l) => l.label)];
    for (const e of edges) strings.push(e.ariaLabel);
    for (const n of nodes) {
      const d = n.data;
      strings.push(d.title, d.summary, d.settled, d.supersededBy, d.lineLabel, d.moment);
      for (const a of d.artifacts) strings.push(a.name);
      for (const ex of d.excursions || []) strings.push(`${ex.label} · ${ex.stops} stops`);
    }
    for (const s of strings) {
      if (s && ID_RE.test(s)) {
        console.error(`${f}: internal id leaked into display string:\n  ${JSON.stringify(s)}`);
        bad++;
      }
    }
  }
}

if (bad) {
  console.error(`\nFAIL: ${bad} display string(s) leak internal ids.`);
  process.exit(1);
}
console.log('OK: no internal ids in any display string (all datasets, expanded + collapsed).');
