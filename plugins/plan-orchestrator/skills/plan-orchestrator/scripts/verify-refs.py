#!/usr/bin/env python3
"""verify-refs.py — unified Structural-class reference check.

Consolidates four checks:
  cites          — adjudication `source.cite:` files+anchors must resolve
  derived-from   — adjudication `source.derived_from:` IDs must resolve
  references     — prose references (per A<N>, see E<N>, resolved_by, ...) must resolve
  source-form    — adjudication `source:` block must contain exactly one of
                   cite / derived_from / originates_at (cite + derived_from MAY
                   coexist; originates_at MUST be alone)
  all            — run every subcommand; final exit code is max() of all

Usage:
  python3 verify-refs.py <subcommand> <work-dir>
  python3 verify-refs.py all <work-dir>

Slug rule for cites (canonical):
  lowercase  →  non-alphanumeric runs collapse to a single dash
              →  strip leading/trailing dashes

Exit codes:
  0   clean
  1   one or more issues
  2   usage error
"""
import sys
import re
import difflib
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# shared helpers

def slugify(text):
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def adj_chunks(text):
    """Split a markdown blob into per-adjudication chunks keyed by `- id: A<N>`."""
    chunks = re.split(r"(?=^\s*-\s+id:\s+\w+)", text, flags=re.MULTILINE)
    for chunk in chunks:
        m = re.match(r"\s*-\s+id:\s+(\w+)", chunk)
        if m:
            yield m.group(1), chunk


def adjudication_files(work_dir):
    out = [work_dir / "assumptions.md"]
    phases = work_dir / "phases"
    if phases.exists():
        out.extend(phases.rglob("plan.md"))
    return [f for f in out if f.exists()]


def collect_defined_adjudications(work_dir):
    ids = set()
    for f in adjudication_files(work_dir):
        for m in re.finditer(r"^\s*-\s+id:\s+(A\d+)", f.read_text(), re.MULTILINE):
            ids.add(m.group(1))
    return ids


def collect_defined_escalations(work_dir):
    """E<N> definitions live either in the concatenated escalations.md or in
    per-dispatch files under escalations/*.md (round-3: per-dispatch files
    replace shared E-numbering)."""
    ids = set()
    cat = work_dir / "escalations.md"
    if cat.exists():
        ids.update(re.findall(r"^## (E\d+)", cat.read_text(), re.MULTILINE))
    per_dispatch = work_dir / "escalations"
    if per_dispatch.exists():
        for f in per_dispatch.rglob("*.md"):
            # Per-dispatch IDs are locally namespaced as "<dispatch-id>.E<N>"
            for m in re.finditer(r"^## (E\d+)", f.read_text(), re.MULTILINE):
                ids.add(f"{f.stem}.{m.group(1)}")
                ids.add(m.group(1))  # also bare-form, since prose may abbreviate
    return ids


# ─────────────────────────────────────────────────────────────────────────────
# subcommand: cites

def headings_in_file(path):
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        m = re.match(r"^#+\s+(.+?)\s*$", line)
        if not m:
            continue
        text = m.group(1)
        out[text] = text
        out[slugify(text)] = text
        stripped = re.sub(r"^[A-Z]\d+\s*[—\-:.]\s*", "", text)
        if stripped and stripped != text:
            out[slugify(stripped)] = text
    return out


def closest(needle, choices):
    if not choices:
        return None
    matches = difflib.get_close_matches(needle, list(choices), n=1, cutoff=0.6)
    return choices[matches[0]] if matches else None


def extract_cites(chunk):
    """Yield (file, anchor) pairs from a `source.cite:` block inside a chunk.
    Accepts both legacy top-level `cites:` and new `source: cite:` shapes."""
    m = re.search(
        r"^\s*(?:cites|cite):\s*\n((?:\s+-\s+file:.+\n\s+anchor:.+\n?)+)",
        chunk,
        re.MULTILINE,
    )
    if not m:
        return
    for cm in re.finditer(
        r"-\s+file:\s+(.+?)\n\s+anchor:\s+(.+?)(?:\n|$)", m.group(1)
    ):
        yield cm.group(1).strip(), cm.group(2).strip()


def cmd_cites(work_dir):
    issues = []
    total = 0
    for f in adjudication_files(work_dir):
        for adj_id, chunk in adj_chunks(f.read_text()):
            for cited_file, anchor in extract_cites(chunk):
                total += 1
                full = work_dir / cited_file
                if not full.exists():
                    issues.append(
                        f"{adj_id} in {f.relative_to(work_dir)}: cited file "
                        f"'{cited_file}' does not exist"
                    )
                    continue
                heads = headings_in_file(full)
                slug = slugify(anchor)
                if anchor in heads or slug in heads:
                    continue
                suggestion = closest(anchor, heads) or closest(slug, heads)
                msg = (
                    f"{adj_id} in {f.relative_to(work_dir)}: anchor '{anchor}' "
                    f"not found in {cited_file}"
                )
                if suggestion:
                    msg += (
                        f"  (did you mean '{suggestion}' → "
                        f"slug '{slugify(suggestion)}'?)"
                    )
                issues.append(msg)
    if not issues:
        print(f"cites: OK ({total} resolved)")
        return 0
    print(f"cites: FAIL — {len(issues)} unresolved of {total}:")
    for i in issues[:30]:
        print(f"  {i}")
    return 1


# ─────────────────────────────────────────────────────────────────────────────
# subcommand: derived-from

def extract_derived_from(chunk):
    """Accept both `derived_from:` at top-level (legacy) and nested under
    `source:` (current)."""
    m = re.search(r"^\s*derived_from:\s*\[([^\]]+)\]", chunk, re.MULTILINE)
    if not m:
        return []
    return re.findall(r"A\d+", m.group(1))


def cmd_derived_from(work_dir):
    defined = collect_defined_adjudications(work_dir)
    unresolved = []
    total = 0
    for f in adjudication_files(work_dir):
        for adj_id, chunk in adj_chunks(f.read_text()):
            for ref in extract_derived_from(chunk):
                total += 1
                if ref not in defined:
                    unresolved.append(
                        f"{f.relative_to(work_dir)}::{adj_id}: derived_from "
                        f"references undefined {ref}"
                    )
    if not unresolved:
        print(
            f"derived-from: OK ({total} refs resolved; {len(defined)} defined)"
        )
        return 0
    print(f"derived-from: FAIL — {len(unresolved)} unresolved:")
    for u in unresolved[:30]:
        print(f"  {u}")
    return 1


# ─────────────────────────────────────────────────────────────────────────────
# subcommand: references

REF_PATTERNS = [
    r"\bper\s+(A\d+|E\d+)\b",
    r"\bsee\s+(A\d+|E\d+)\b",
    r"resolved_by:\s+(A\d+|E\d+)\b",
    r"resolves(?:_escalation)?:\s*\[?\s*(A\d+|E\d+)\b",
]


def collect_references(work_dir):
    refs = []
    for f in work_dir.rglob("*.md"):
        text = f.read_text()
        for pat in REF_PATTERNS:
            for m in re.finditer(pat, text):
                token = m.group(1)
                refs.append((token[0], token, f))
    return refs


def cmd_references(work_dir):
    defined_a = collect_defined_adjudications(work_dir)
    defined_e = collect_defined_escalations(work_dir)
    refs = collect_references(work_dir)
    unresolved = []
    for kind, ref_id, f in refs:
        defined = defined_a if kind == "A" else defined_e
        if ref_id not in defined:
            unresolved.append((ref_id, f.relative_to(work_dir)))
    if not unresolved:
        print(
            f"references: OK ({len(refs)} checked; {len(defined_a)} A, "
            f"{len(defined_e)} E defined)"
        )
        return 0
    print(f"references: FAIL — {len(unresolved)} unresolved:")
    for ref_id, f in unresolved[:30]:
        print(f"  {ref_id} referenced in {f}")
    if len(unresolved) > 30:
        print(f"  ... and {len(unresolved) - 30} more")
    return 1


# ─────────────────────────────────────────────────────────────────────────────
# subcommand: source-form (exclusivity check)
#
# `source:` must contain exactly one of cite / derived_from / originates_at.
# Exceptions: cite + derived_from MAY coexist (a derived adjudication that also
# cites supporting facts). originates_at MUST be alone — if you can cite, you
# should. This check rejects empty `derived_from: []` or empty `cite: []`
# coexisting with originates_at, which round-3's A14 case slipped past.

def has_originates_at(chunk):
    return bool(re.search(r"^\s*originates_at:\s+\S", chunk, re.MULTILINE))


def has_cite(chunk):
    # Strict: any cite/cites key counts. Empty cite: [] still violates
    # exclusivity (per round-3 A14 case — the reviewer caught a presence-
    # of-key violation that a "must have content" check missed).
    return bool(re.search(r"^\s*(?:cites|cite):\s", chunk, re.MULTILINE))


def has_derived_from(chunk):
    # Strict: any derived_from key counts, including the empty list form.
    return bool(re.search(r"^\s*derived_from:\s", chunk, re.MULTILINE))


def cmd_source_form(work_dir):
    issues = []
    total = 0
    for f in adjudication_files(work_dir):
        for adj_id, chunk in adj_chunks(f.read_text()):
            total += 1
            c = has_cite(chunk)
            d = has_derived_from(chunk)
            o = has_originates_at(chunk)
            forms = sum([c, d, o])
            if forms == 0:
                issues.append(
                    f"{adj_id} in {f.relative_to(work_dir)}: source block has "
                    f"no form (need cite / derived_from / originates_at)"
                )
                continue
            if o and (c or d):
                issues.append(
                    f"{adj_id} in {f.relative_to(work_dir)}: originates_at "
                    f"must be alone — found alongside "
                    f"{'cite' if c else ''}{' + ' if c and d else ''}{'derived_from' if d else ''}"
                )
    if not issues:
        print(f"source-form: OK ({total} adjudications)")
        return 0
    print(f"source-form: FAIL — {len(issues)} violation(s):")
    for i in issues[:30]:
        print(f"  {i}")
    return 1


# ─────────────────────────────────────────────────────────────────────────────
# dispatch

SUBCMDS = {
    "cites": cmd_cites,
    "derived-from": cmd_derived_from,
    "references": cmd_references,
    "source-form": cmd_source_form,
}


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: verify-refs.py <cites|derived-from|references|all> <work-dir>",
            file=sys.stderr,
        )
        return 2
    sub, wd = sys.argv[1], Path(sys.argv[2])
    if sub == "all":
        codes = [fn(wd) for fn in SUBCMDS.values()]
        return max(codes)
    fn = SUBCMDS.get(sub)
    if not fn:
        print(f"Unknown subcommand '{sub}'", file=sys.stderr)
        return 2
    return fn(wd)


if __name__ == "__main__":
    sys.exit(main())
