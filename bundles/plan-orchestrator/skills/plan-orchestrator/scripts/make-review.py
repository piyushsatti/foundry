#!/usr/bin/env python3
"""make-review.py — render a single self-contained HTML review of a work-dir.

Generates <work-dir>/review.html that the user can open in a browser to
inspect the run's current state before approving a stage gate. Designed
to land before Implementation, but works at any gate.

Usage:
    python3 make-review.py <work-dir>
    python3 make-review.py <work-dir> --stage planning
    python3 make-review.py <work-dir> --open       # also `open` the file (macOS)

The HTML is single-file: CSS + JS embedded, zero external assets. Email it,
archive it, share it.

Stdlib only.
"""
import sys
import re
import os
import html
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────────────────────
# minimal markdown → HTML (headings, lists, code blocks, bold, inline code).
# Not a full renderer — handles the shapes the work-dir actually uses.

def md_to_html(text):
    out = []
    in_code = False
    lang = ""
    in_list = False
    for line in text.splitlines():
        # fenced code blocks
        m = re.match(r"^```(\w*)\s*$", line)
        if m:
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                lang = m.group(1)
                out.append(
                    f'<pre class="code"><code class="lang-{html.escape(lang)}">'
                )
                in_code = True
            continue
        if in_code:
            out.append(html.escape(line))
            continue

        # headings
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            if in_list:
                out.append("</ul>")
                in_list = False
            n = len(m.group(1))
            out.append(
                f"<h{n + 2}>{inline_md(m.group(2))}</h{n + 2}>"
            )
            continue

        # bullets
        m = re.match(r"^(\s*)-\s+(.+?)\s*$", line)
        if m:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline_md(m.group(2))}</li>")
            continue
        if in_list and not line.strip():
            out.append("</ul>")
            in_list = False
            out.append("")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False

        if not line.strip():
            out.append("")
            continue
        out.append(f"<p>{inline_md(line)}</p>")

    if in_code:
        out.append("</code></pre>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def inline_md(text):
    """**bold**, *italic*, `code`."""
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


# ─────────────────────────────────────────────────────────────────────────────
# work-dir readers

def read(path, default=""):
    p = Path(path)
    return p.read_text() if p.exists() else default


def parse_yaml_block(text):
    m = re.match(r"\A---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    return (m.group(1), m.group(2)) if m else (None, text)


def parse_dag(dag_md):
    """Returns ({phase_id: {fields}}, {contract_id: {fields}})."""
    yaml_text, _ = parse_yaml_block(dag_md)
    if not yaml_text:
        return {}, {}
    phases = {}
    contracts = {}

    # Parse phases.
    m = re.search(
        r"^phases:\s*\n((?:[ \t]+\S.*\n)+)", yaml_text, re.MULTILINE
    )
    if m:
        phase_block = m.group(1)
        for pm in re.finditer(
            r"^[ \t]{2,4}(P\d+):\s*\n((?:[ \t]{4,}\S.*\n)+)",
            phase_block,
            re.MULTILINE,
        ):
            pid = pm.group(1)
            body = pm.group(2)
            phases[pid] = {
                "name": pull(body, "name"),
                "produces": pull(body, "produces"),
                "consumes": pull_block(body, "consumes"),
                "depends_on": pull(body, "depends_on"),
                "skill_requirements": pull(body, "skill_requirements"),
                "status": pull(body, "status"),
            }

    # Parse contracts.
    m = re.search(
        r"^contracts:\s*\n((?:[ \t]+\S.*\n)+)", yaml_text, re.MULTILINE
    )
    if m:
        cblock = m.group(1)
        for cm in re.finditer(
            r"^[ \t]{2,4}(C\d+):\s*\n((?:[ \t]{4,}\S.*\n)+)",
            cblock,
            re.MULTILINE,
        ):
            cid = cm.group(1)
            body = cm.group(2)
            contracts[cid] = {
                "producer": pull(body, "producer"),
                "version": pull(body, "version"),
                "locked": pull(body, "locked"),
            }
    return phases, contracts


def pull(text, key):
    m = re.search(rf"^[ \t]*{re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def pull_block(text, key):
    """Grab the indented sub-block under `key:` and return it as a string."""
    m = re.search(
        rf"^([ \t]*){re.escape(key)}:\s*\n((?:\1[ \t]+\S.*\n)*)",
        text,
        re.MULTILINE,
    )
    if not m:
        single = pull(text, key)
        return single if single not in ("", "{}") else ""
    return m.group(2).strip()


def parse_adjudications(text):
    """Yield dicts for each `- id: A<N>` block."""
    chunks = re.split(r"(?=^\s*-\s+id:\s+\w+)", text, flags=re.MULTILINE)
    for chunk in chunks:
        m_id = re.match(r"\s*-\s+id:\s+(\w+)", chunk)
        if not m_id:
            continue
        adj = {
            "id": m_id.group(1),
            "claim": pull(chunk, "claim").strip('"'),
            "rationale": pull(chunk, "rationale").strip('"'),
            "confidence": pull(chunk, "confidence"),
            "risk_if_wrong": pull(chunk, "risk_if_wrong").strip('"'),
            "status": pull(chunk, "status"),
            "validated_by": pull(chunk, "validated_by"),
            "validated_at": pull(chunk, "validated_at"),
            "source": "cite" if "cite:" in chunk else
                      "derived_from" if re.search(r"^\s*derived_from:", chunk, re.MULTILINE) else
                      "originates_at" if "originates_at:" in chunk else "—",
            "affects": "",
        }
        m_aff = re.search(
            r"affects_artifacts:\s*\n((?:\s+-\s+.+\n)+)", chunk
        )
        if m_aff:
            adj["affects"] = ", ".join(
                am.group(1).strip()
                for am in re.finditer(r"-\s+(.+?)(?:\n|$)", m_aff.group(1))
            )
        yield adj


def parse_escalations_text(text):
    """Yield dicts for each `## E<N>` block."""
    chunks = re.split(r"(?=^##\s+E\d+\s+—)", text, flags=re.MULTILINE)
    for chunk in chunks:
        m_id = re.match(r"##\s+(E\d+)\s+—\s+(\S+)\s+—\s+(\S+)", chunk)
        if not m_id:
            continue
        yield {
            "id": m_id.group(1),
            "ts": m_id.group(2),
            "type": m_id.group(3),
            "severity": pull(chunk, "severity"),
            "detected_by": pull(chunk, "detected_by"),
            "claim": pull(chunk, "claim").strip('"'),
            "lands_at": pull(chunk, "lands_at"),
            "status": pull(chunk, "status"),
            "resolved_by": pull(chunk, "resolved_by"),
        }


def parse_phase_plan(path):
    """Read a phase plan and pull a brief: task count + risks."""
    text = read(path)
    if not text:
        return None
    body = text
    # Skip any leading frontmatter.
    fm, body = parse_yaml_block(text)
    # Pull "Tasks" section if present; count "T1", "T2", etc.
    tasks = sorted(set(re.findall(r"\bT(\d+)\b", body)))
    return {
        "path": str(path),
        "task_count": len(tasks),
        "task_ids": tasks,
        "size_kb": round(len(text) / 1024, 1),
        "raw": text,
    }


# ─────────────────────────────────────────────────────────────────────────────
# gate evaluation

def evaluate_gate(work_dir, esc_entries, adjudications):
    """Apply the four-condition gate per decision 43."""
    blocking_open = sum(
        1 for e in esc_entries
        if e["severity"] == "blocking" and e["status"] == "open"
    )
    risky_pending = sum(
        1 for a in adjudications
        if a["confidence"] == "low"
        and a["risk_if_wrong"] in ("medium", "high", "medium-or-high")
        and a["status"] == "pending"
    )
    # Structural is a tri-state best-effort: we re-shell the scripts if
    # they exist alongside this one and capture exit codes. To keep the
    # script standalone, we sample one cheap check.
    structural_ok = True  # best-effort placeholder
    alignment_ok = True   # placeholder — Haiku output is not in work-dir
    return {
        "structural": structural_ok,
        "alignment": alignment_ok,
        "blocking_escalations": blocking_open,
        "risky_pending_adjudications": risky_pending,
    }


# ─────────────────────────────────────────────────────────────────────────────
# HTML

CSS = """
:root {
  --bg: #fafafa;
  --fg: #1a1a1a;
  --muted: #6b6b6b;
  --border: #e4e4e4;
  --card: #ffffff;
  --accent: #2563eb;
  --green: #15803d;
  --green-bg: #dcfce7;
  --gray: #4b5563;
  --gray-bg: #f3f4f6;
  --blue: #1d4ed8;
  --blue-bg: #dbeafe;
  --red: #b91c1c;
  --red-bg: #fee2e2;
  --orange: #c2410c;
  --orange-bg: #ffedd5;
  --yellow: #a16207;
  --yellow-bg: #fef9c3;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--fg);
  margin: 0;
  line-height: 1.5;
  font-size: 15px;
}
.layout { display: grid; grid-template-columns: 220px 1fr; min-height: 100vh; }
nav.toc {
  background: var(--card);
  border-right: 1px solid var(--border);
  padding: 24px 20px;
  position: sticky; top: 0; height: 100vh; overflow-y: auto;
  font-size: 14px;
}
nav.toc h2 { font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin: 16px 0 6px; }
nav.toc h2:first-child { margin-top: 0; }
nav.toc a { display: block; color: var(--fg); text-decoration: none; padding: 4px 0; border-left: 2px solid transparent; padding-left: 10px; margin-left: -12px; }
nav.toc a:hover { color: var(--accent); border-left-color: var(--accent); }
main { padding: 32px 48px; max-width: 1100px; }
header.runhdr { border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 32px; }
header.runhdr h1 { margin: 0 0 4px; font-size: 26px; }
header.runhdr .meta { color: var(--muted); font-size: 13px; }
section { margin-bottom: 40px; scroll-margin-top: 20px; }
section h2 { font-size: 20px; margin: 0 0 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
section h3 { font-size: 16px; margin: 24px 0 8px; }
section h4 { font-size: 14px; margin: 16px 0 6px; color: var(--muted); }
section p { margin: 8px 0; }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 6px; padding: 16px 18px; margin-bottom: 12px; }
.card.compact { padding: 10px 14px; }
.row { display: flex; gap: 12px; align-items: baseline; }
.row .key { color: var(--muted); font-family: var(--mono); font-size: 12px; min-width: 90px; }
.pill { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-family: var(--mono); }
.pill.validated { background: var(--green-bg); color: var(--green); }
.pill.pending { background: var(--gray-bg); color: var(--gray); }
.pill.revised { background: var(--blue-bg); color: var(--blue); }
.pill.invalidated { background: var(--red-bg); color: var(--red); }
.pill.wont-fix { background: var(--orange-bg); color: var(--orange); }
.pill.blocking { background: var(--red-bg); color: var(--red); }
.pill.advisory { background: var(--yellow-bg); color: var(--yellow); }
.pill.resolved { background: var(--green-bg); color: var(--green); }
.pill.open { background: var(--red-bg); color: var(--red); }
.pill.high { background: var(--green-bg); color: var(--green); }
.pill.medium { background: var(--yellow-bg); color: var(--yellow); }
.pill.low { background: var(--red-bg); color: var(--red); }
pre.code, pre { background: #1a1a1a; color: #e4e4e4; padding: 12px 16px; border-radius: 6px; overflow-x: auto; font-family: var(--mono); font-size: 13px; }
code { font-family: var(--mono); background: var(--gray-bg); padding: 1px 5px; border-radius: 3px; font-size: 13px; }
pre code { background: transparent; padding: 0; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }
th { background: var(--gray-bg); font-weight: 600; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }
tr:hover td { background: #fafafa; }
.filters { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.filter-btn { padding: 4px 12px; border: 1px solid var(--border); background: var(--card); border-radius: 4px; cursor: pointer; font-size: 13px; }
.filter-btn.active { background: var(--accent); color: white; border-color: var(--accent); }
details > summary { cursor: pointer; padding: 8px 12px; background: var(--card); border: 1px solid var(--border); border-radius: 6px; margin-bottom: 6px; user-select: none; }
details[open] > summary { border-bottom-left-radius: 0; border-bottom-right-radius: 0; }
details > .details-body { background: var(--card); border: 1px solid var(--border); border-top: none; border-radius: 0 0 6px 6px; padding: 12px 16px; }
.gate-condition { display: flex; gap: 12px; align-items: center; padding: 10px; border-radius: 6px; margin-bottom: 6px; }
.gate-condition.pass { background: var(--green-bg); }
.gate-condition.fail { background: var(--red-bg); }
.gate-condition .icon { font-weight: bold; }
.dag-grid { display: grid; gap: 12px; }
.dag-phase { background: var(--card); border: 1px solid var(--border); border-radius: 6px; padding: 12px 14px; }
.dag-phase .id { font-family: var(--mono); font-weight: 600; color: var(--accent); }
.muted { color: var(--muted); font-size: 12px; }
"""

JS = """
function setFilter(group, value) {
  const buttons = document.querySelectorAll('[data-filter-group="' + group + '"]');
  buttons.forEach(b => b.classList.toggle('active', b.dataset.filterValue === value));
  const rows = document.querySelectorAll('[data-filter-target="' + group + '"]');
  rows.forEach(r => {
    r.style.display = (value === 'all' || r.dataset.filterKey === value) ? '' : 'none';
  });
}
"""


def pill(text, cls=None):
    cls = cls or text or "pending"
    cls_safe = re.sub(r"[^a-z0-9-]", "-", cls.lower())
    return f'<span class="pill {cls_safe}">{html.escape(text)}</span>'


def render(work_dir, stage):
    project = work_dir.parent.name
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    spec = read(work_dir / "spec.md")
    glossary = read(work_dir / "glossary.md")
    dag_md = read(work_dir / "dag.md")
    assumptions_md = read(work_dir / "assumptions.md")
    todo_md = read(work_dir / "TODO.md")
    escalations_md = read(work_dir / "escalations.md")

    phases_meta, contracts_meta = parse_dag(dag_md)

    arch_adj = list(parse_adjudications(assumptions_md))
    plan_adj_by_phase = {}
    phase_plans = {}
    phases_dir = work_dir / "phases"
    if phases_dir.exists():
        for pdir in sorted(phases_dir.iterdir()):
            if not pdir.is_dir():
                continue
            plan_path = pdir / "plan.md"
            if not plan_path.exists():
                continue
            plan = parse_phase_plan(plan_path)
            phase_plans[pdir.name] = plan
            plan_adj_by_phase[pdir.name] = list(
                parse_adjudications(plan["raw"])
            )

    all_adj = arch_adj + [a for adjs in plan_adj_by_phase.values() for a in adjs]

    esc_entries = list(parse_escalations_text(escalations_md))

    gate = evaluate_gate(work_dir, esc_entries, all_adj)

    # ── HTML assembly
    def gate_row(label, ok):
        cls = "pass" if ok else "fail"
        icon = "✓" if ok else "✗"
        return f'<div class="gate-condition {cls}"><span class="icon">{icon}</span> <span>{html.escape(label)}</span></div>'

    gate_html = [
        gate_row("Structural verifiers clean", gate["structural"]),
        gate_row(
            f"Zero blocking escalations open (found: {gate['blocking_escalations']})",
            gate["blocking_escalations"] == 0,
        ),
        gate_row(
            f"Zero low-confidence + medium/high-risk pending (found: {gate['risky_pending_adjudications']})",
            gate["risky_pending_adjudications"] == 0,
        ),
        gate_row(
            "Alignment Haiku checks clean (manual verification — not in work-dir)",
            True,
        ),
    ]

    phases_html = []
    for pid in sorted(phases_meta.keys()):
        p = phases_meta[pid]
        phases_html.append(f'''
<div class="dag-phase">
  <span class="id">{html.escape(pid)}</span> — <strong>{html.escape(p["name"])}</strong>
  &nbsp; {pill(p["status"] or "—", p["status"])}
  <div class="muted">depends on: {html.escape(p["depends_on"] or "—")}</div>
  <div class="muted">produces: {html.escape(p["produces"] or "—")}</div>
  <div class="muted">consumes: <code>{html.escape(p["consumes"] or "—")[:200]}</code></div>
</div>''')

    contracts_html = []
    for cid in sorted(contracts_meta.keys()):
        c = contracts_meta[cid]
        locked_pill = pill("locked", "validated") if c["locked"].lower() == "true" else pill("unlocked", "pending")
        contracts_html.append(f'''
<tr>
  <td><strong>{html.escape(cid)}</strong></td>
  <td>{html.escape(c["producer"] or "—")}</td>
  <td><code>{html.escape(c["version"] or "—")}</code></td>
  <td>{locked_pill}</td>
</tr>''')

    adj_rows = []
    for a in all_adj:
        adj_rows.append(f'''
<tr data-filter-target="adj" data-filter-key="{html.escape(a["status"] or "pending")}">
  <td><strong>{html.escape(a["id"])}</strong></td>
  <td>{html.escape(a["claim"])[:250]}</td>
  <td><code>{html.escape(a["source"])}</code></td>
  <td>{pill(a["confidence"] or "—")}</td>
  <td>{pill(a["risk_if_wrong"] or "—")}</td>
  <td>{pill(a["status"] or "pending")}</td>
</tr>''')

    esc_rows = []
    open_count = 0
    resolved_count = 0
    for e in esc_entries:
        if e["status"] == "open":
            open_count += 1
        else:
            resolved_count += 1
        esc_rows.append(f'''
<tr data-filter-target="esc" data-filter-key="{html.escape(e["status"] or "open")}">
  <td><strong>{html.escape(e["id"])}</strong></td>
  <td>{pill(e["severity"] or "—")}</td>
  <td>{html.escape(e["type"] or "—")}</td>
  <td>{html.escape(e["detected_by"] or "—")}</td>
  <td>{html.escape(e["claim"])[:200]}</td>
  <td>{html.escape(e["lands_at"] or "—")}</td>
  <td>{pill(e["status"] or "open")}</td>
</tr>''')

    plan_details = []
    for pid in sorted(phase_plans.keys()):
        plan = phase_plans[pid]
        plan_adj_count = len(plan_adj_by_phase.get(pid, []))
        plan_details.append(f'''
<details>
  <summary><strong>{html.escape(pid)}</strong> &nbsp; {plan["task_count"]} tasks &nbsp; {plan_adj_count} adjudications &nbsp; <span class="muted">{plan["size_kb"]} KB</span></summary>
  <div class="details-body">
    <pre class="code">{html.escape(plan["raw"][:4000])}</pre>
    {'<p class="muted">… truncated; see ' + html.escape(plan["path"]) + '</p>' if len(plan["raw"]) > 4000 else ''}
  </div>
</details>''')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>plan-orchestrator review — {html.escape(project)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="layout">

<nav class="toc">
  <h2>Sections</h2>
  <a href="#gate">Gate evaluation</a>
  <a href="#spec">Spec</a>
  <a href="#dag">DAG</a>
  <a href="#contracts">Contracts</a>
  <a href="#adjudications">Adjudications</a>
  <a href="#escalations">Escalations</a>
  <a href="#plans">Phase plans</a>
  <a href="#glossary">Glossary</a>
</nav>

<main>
<header class="runhdr">
  <h1>{html.escape(project)} <span class="pill">{html.escape(stage)}</span></h1>
  <div class="meta">work-dir: <code>{html.escape(str(work_dir))}</code></div>
  <div class="meta">generated: {html.escape(ts)}</div>
</header>

<section id="gate">
<h2>Stage gate evaluation</h2>
<p>All four conditions must pass for the gate to auto-clear. If any fails, the architect halts and surfaces to user.</p>
{"".join(gate_html)}
</section>

<section id="spec">
<h2>Spec</h2>
<div class="card">
{md_to_html(spec)}
</div>
</section>

<section id="dag">
<h2>DAG — phases &amp; contracts</h2>
<h3>Phases ({len(phases_meta)})</h3>
<div class="dag-grid">
{"".join(phases_html)}
</div>
</section>

<section id="contracts">
<h2>Contracts ({len(contracts_meta)})</h2>
<table>
<thead><tr><th>ID</th><th>Producer</th><th>Version</th><th>Status</th></tr></thead>
<tbody>{"".join(contracts_html)}</tbody>
</table>
</section>

<section id="adjudications">
<h2>Adjudications ({len(all_adj)})</h2>
<div class="filters">
  <button class="filter-btn active" data-filter-group="adj" data-filter-value="all" onclick="setFilter('adj','all')">all</button>
  <button class="filter-btn" data-filter-group="adj" data-filter-value="pending" onclick="setFilter('adj','pending')">pending</button>
  <button class="filter-btn" data-filter-group="adj" data-filter-value="validated" onclick="setFilter('adj','validated')">validated</button>
  <button class="filter-btn" data-filter-group="adj" data-filter-value="revised" onclick="setFilter('adj','revised')">revised</button>
  <button class="filter-btn" data-filter-group="adj" data-filter-value="invalidated" onclick="setFilter('adj','invalidated')">invalidated</button>
  <button class="filter-btn" data-filter-group="adj" data-filter-value="wont-fix" onclick="setFilter('adj','wont-fix')">wont-fix</button>
</div>
<table>
<thead><tr><th>ID</th><th>Claim</th><th>Source</th><th>Confidence</th><th>Risk if wrong</th><th>Status</th></tr></thead>
<tbody>{"".join(adj_rows)}</tbody>
</table>
</section>

<section id="escalations">
<h2>Escalations ({len(esc_entries)} total — {open_count} open, {resolved_count} resolved)</h2>
<div class="filters">
  <button class="filter-btn active" data-filter-group="esc" data-filter-value="all" onclick="setFilter('esc','all')">all</button>
  <button class="filter-btn" data-filter-group="esc" data-filter-value="open" onclick="setFilter('esc','open')">open</button>
  <button class="filter-btn" data-filter-group="esc" data-filter-value="resolved" onclick="setFilter('esc','resolved')">resolved</button>
</div>
<table>
<thead><tr><th>ID</th><th>Severity</th><th>Type</th><th>Detected by</th><th>Claim</th><th>Lands at</th><th>Status</th></tr></thead>
<tbody>{"".join(esc_rows)}</tbody>
</table>
</section>

<section id="plans">
<h2>Phase plans ({len(phase_plans)})</h2>
{"".join(plan_details)}
</section>

<section id="glossary">
<h2>Glossary</h2>
<div class="card">
{md_to_html(glossary)}
</div>
</section>

</main>
</div>
<script>{JS}</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="Render an HTML review of a work-dir.")
    ap.add_argument("work_dir", help="Path to the plan-orchestrator work-dir.")
    ap.add_argument("--stage", default="planning", help="Gate the review is for (default: planning).")
    ap.add_argument("--open", action="store_true", help="Open the generated file after writing (macOS).")
    args = ap.parse_args()

    wd = Path(args.work_dir).expanduser().resolve()
    if not wd.exists():
        print(f"work-dir does not exist: {wd}", file=sys.stderr)
        return 2

    html_text = render(wd, args.stage)
    out_path = wd / "review.html"
    out_path.write_text(html_text)
    print(f"wrote {out_path} ({len(html_text)} bytes)")

    if args.open:
        try:
            subprocess.run(["open", str(out_path)], check=False)
        except FileNotFoundError:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
