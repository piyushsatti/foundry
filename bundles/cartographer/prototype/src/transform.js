// Transforms the cartographer session-map schema (v2) into React Flow
// { nodes, edges } plus masthead metadata.
//
// Internal ids (nXX, aXX, @vN) are wiring only: every string placed into
// node.data / meta is passed through `humanize`, which resolves id
// references to verbatim titles. Quotes are NEVER transformed (byte-exact).

const LINE_COLORS = ['#5b84c4', '#a06cb5', '#4e9e7f']; // line hue = line identity, nothing else
const COL_W = 760; // horizontal distance between line columns
const ROW_H = 160; // vertical distance between ranks
const FAN_W = 340; // horizontal spread inside a fan-out rank

export const GLYPHS = {
  breakthrough: '✦', // ✦
  setback: '▽', // ▽
  pivot: '↷', // ↷
  grind: '⋯', // ⋯
};

// Known artifacts → repo-relative paths, served by the vite /artifact/
// middleware (see vite.config.js). An artifact entry may instead carry its
// own `path` field, which wins. Artifacts resolving to nothing render as
// non-links with a "no file" affordance.
const ARTIFACT_PATHS = {
  '00-scope-and-method.md — scope + firsthand findings':
    '.gitignored/audits/meditate-full-review-2026-07-05/00-scope-and-method.md',
  'design/architecture review report':
    '.gitignored/audits/meditate-full-review-2026-07-05/design-review.md',
  'implementation-quality review report':
    '.gitignored/audits/meditate-full-review-2026-07-05/implementation-review.md',
  'memory-curation literature survey':
    '.gitignored/audits/meditate-full-review-2026-07-05/literature-review.md',
  'SYNTHESIS.md — combined verdict, doc-update plan, phased code plan, open decisions':
    '.gitignored/audits/meditate-full-review-2026-07-05/SYNTHESIS.md',
  'vendored authority docs ×6 (five curator docs + applier design doc) → plugins/meditate/docs/':
    'plugins/meditate/docs/README.md',
  "plugins/meditate/README.md — the plugin's front door": 'plugins/meditate/README.md',
  'apply/SKILL.md rewiring': 'plugins/meditate/skills/apply/SKILL.md',
  'per-machine config split — tracked example template + gitignored real config':
    'plugins/meditate/config/targets.example.yaml',
  'migrate_frontmatter.py hardened — line-anchored split, backup-on-write, body-identity self-check':
    'plugins/meditate/scripts/migrate_frontmatter.py',
};

// A collapsible excursion: a line that forks out of node X and merges back
// into the same node X (any version). Pure and schema-level — first bite of
// the mereology epic; will move server-side later.
export function detectExcursions(data) {
  const excursions = [];
  for (const line of data.lines) {
    if (!line.from || !line.into) continue;
    if (line.from.node !== line.into.node) continue;
    const nodeIds = data.nodes.filter((n) => n.line === line.id).map((n) => n.id);
    if (nodeIds.length === 0) continue;
    excursions.push({
      key: line.id, // internal — never displayed
      lineId: line.id,
      anchor: line.from.node,
      label: line.label, // verbatim line label
      stops: nodeIds.length,
      nodeIds,
    });
  }
  return excursions;
}

// Group a line's nodes (file order) into ranks; consecutive segment-carrying
// nodes share one rank (the fan-out row).
function buildRanks(lineNodes) {
  const ranks = [];
  let i = 0;
  while (i < lineNodes.length) {
    if (lineNodes[i].segment) {
      const fan = [];
      while (i < lineNodes.length && lineNodes[i].segment) fan.push(lineNodes[i++]);
      ranks.push(fan);
    } else {
      ranks.push([lineNodes[i++]]);
    }
  }
  return ranks;
}

// Geometric handle pick from node positions: same column (fan spread counts
// as same column) → bottom→top; rightward → right→left; leftward loop-back →
// left→right so the return edge reads as a deliberate loop.
function pickHandles(a, b) {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  if (Math.abs(dx) < COL_W / 2) {
    return dy >= 0
      ? { sourceHandle: 'b-out', targetHandle: 't-in' }
      : { sourceHandle: 't-out', targetHandle: 'b-in' };
  }
  return dx > 0
    ? { sourceHandle: 'r-out', targetHandle: 'l-in' }
    : { sourceHandle: 'l-out', targetHandle: 'r-in' };
}

export function toFlow(data, collapsed = new Set()) {
  const titleById = {};
  for (const n of data.nodes) titleById[n.id] = n.title;
  const artifactById = {};
  for (const a of data.artifacts) artifactById[a.id] = a.name;

  // Replace internal id references inside display prose with verbatim titles.
  const humanize = (text) => {
    if (text == null) return text;
    return text
      .replace(/\bn(\d{2})@\d+\b/g, (_, d) => `“${titleById['n' + d]}”`)
      .replace(/\bn(\d{2})\b/g, (_, d) => `“${titleById['n' + d]}”`)
      .replace(/\ba(\d{2})\b/g, (_, d) => `“${artifactById['a' + d]}”`);
  };

  const frontierId = data.session.frontier.node.split('@')[0];

  // ---- excursions (fork-and-merge loops back into their anchor) ----
  const excursions = detectExcursions(data);
  const hidden = new Set();
  for (const ex of excursions) {
    if (collapsed.has(ex.key)) for (const id of ex.nodeIds) hidden.add(id);
  }

  // ---- layout: one column per line, vertical by sequence, fan rows spread ----
  const pos = {};
  const lineColor = {};
  const lineLabel = {};
  const lineNodesById = {};

  data.lines.forEach((line, li) => {
    lineColor[line.id] = LINE_COLORS[li % LINE_COLORS.length];
    lineLabel[line.id] = line.label;
    const lineNodes = data.nodes.filter((n) => n.line === line.id);
    lineNodesById[line.id] = lineNodes;

    let startY = 0;
    if (line.from && pos[line.from.node]) {
      const fromY = pos[line.from.node].y;
      // A fork starts alongside its origin; a succession starts after it.
      startY = line.from.relation === 'fork' ? fromY - 2 * ROW_H : fromY + 2.5 * ROW_H;
    }
    const baseX = li * COL_W;

    buildRanks(lineNodes).forEach((rank, r) => {
      rank.forEach((n, j) => {
        pos[n.id] = {
          x: baseX + (j - (rank.length - 1) / 2) * FAN_W,
          y: startY + r * ROW_H,
        };
      });
    });
  });

  // ---- excursion badges, injected into each excursion's anchor card ----
  const badgesByAnchor = {};
  for (const ex of excursions) {
    (badgesByAnchor[ex.anchor] ||= []).push({
      key: ex.key,
      label: ex.label, // verbatim
      stops: ex.stops,
      color: lineColor[ex.lineId],
      collapsed: collapsed.has(ex.key),
    });
  }

  // ---- nodes ----
  const nodes = data.nodes
    .filter((n) => !hidden.has(n.id))
    .map((n) => ({
      id: n.id,
      type: 'card',
      position: pos[n.id],
      data: {
        title: n.title,
        moment: n.moment,
        status: n.status,
        standing: n.standing || null,
        lineColor: lineColor[n.line],
        lineLabel: lineLabel[n.line],
        summary: humanize(n.summary),
        settled: humanize(n.settled),
        quote: n.quote ? n.quote.text : null, // byte-exact, never transformed
        supersededBy: n.superseded_by ? titleById[n.superseded_by.split('@')[0]] : null,
        artifacts: data.artifacts
          .filter(
            (a) =>
              a.produced_by.split('@')[0] === n.id ||
              (a.updated_by && a.updated_by.split('@')[0] === n.id),
          )
          .map((a) => ({
            name: a.name,
            path: a.path || ARTIFACT_PATHS[a.name] || null,
          })),
        isFrontier: n.id === frontierId,
        excursions: badgesByAnchor[n.id] || null,
      },
    }));

  // ---- edges ----
  const edges = [];
  const spineStyle = (color) => ({ stroke: color, strokeWidth: 2.25 });

  data.lines.forEach((line) => {
    const color = lineColor[line.id];
    const lineNodes = lineNodesById[line.id];
    const ranks = buildRanks(lineNodes);

    // In-line spine (covers the fan-out and the three-into-one landing).
    for (let r = 0; r < ranks.length - 1; r++) {
      for (const a of ranks[r]) {
        for (const b of ranks[r + 1]) {
          edges.push({
            id: `s-${a.id}-${b.id}`,
            source: a.id,
            target: b.id,
            ariaLabel: `${a.title} → ${b.title}`,
            ...pickHandles(pos[a.id], pos[b.id]),
            style: spineStyle(color),
          });
        }
      }
    }

    // Cross-line: where this line comes from (fork / succession).
    if (line.from) {
      const first = lineNodes[0];
      const succession = line.from.relation === 'succession';
      const dx = pos[first.id].x - pos[line.from.node].x;
      edges.push({
        id: `x-${line.from.node}-${first.id}`,
        source: line.from.node,
        target: first.id,
        ariaLabel: `${titleById[line.from.node]} → ${first.title}`,
        ...pickHandles(pos[line.from.node], pos[first.id]),
        type: 'smoothstep',
        pathOptions: { borderRadius: dx < 0 ? 56 : 24 },
        style: {
          ...spineStyle(color),
          ...(succession ? { strokeDasharray: '8 6' } : {}),
        },
        markerEnd: { type: 'arrowclosed', color },
      });
    }

    // Cross-line: the loop-back merge, returning into the node it forked from.
    if (line.into) {
      const last = lineNodes[lineNodes.length - 1];
      const dx = pos[line.into.node].x - pos[last.id].x;
      edges.push({
        id: `x-${last.id}-${line.into.node}`,
        source: last.id,
        target: line.into.node,
        ariaLabel: `${last.title} → ${titleById[line.into.node]}`,
        ...pickHandles(pos[last.id], pos[line.into.node]),
        type: 'smoothstep',
        pathOptions: { borderRadius: dx < 0 ? 56 : 24 },
        style: spineStyle(color),
        markerEnd: { type: 'arrowclosed', color },
      });
    }
  });

  const visibleEdges = edges.filter((e) => !hidden.has(e.source) && !hidden.has(e.target));

  // ---- masthead meta (thesis assembled from JSON fields only) ----
  const clause = (t) => t.split(':')[0].trim();
  const lcFirst = (s) => s.charAt(0).toLowerCase() + s.slice(1);
  const intent = data.session.intent;
  const firstIntent = intent.history.length ? intent.history[0].text : intent.text;
  const thesis =
    `Set out to ${lcFirst(clause(firstIntent))}; ` +
    `the goal became ${lcFirst(clause(intent.text))} — ` +
    `${data.artifacts.length} artifacts produced, ` +
    `frontier: ${data.session.frontier.detail}.`;

  const meta = {
    title: data.session.title,
    date: data.session.date,
    openCount: data.nodes.filter((n) => n.status === 'open').length,
    thesis,
    lines: data.lines.map((l) => ({ label: l.label, color: lineColor[l.id] })),
  };

  return { nodes, edges: visibleEdges, meta };
}
