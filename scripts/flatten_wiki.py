#!/usr/bin/env python3
"""Flatten the folder-structured wiki/ source into GitHub-wiki-flat pages.

GitHub's wiki has a single flat page namespace: a file at any depth is served
by its basename, so `plugins/manifold/overview.md` and `distribution/overview.md`
collide, and nested links (`../lifecycle`, `plugins/x/y`) 302 to raw. This
transform gives every page a unique slug and rewrites every internal link to it.

Slug rule: drop the kind-wrapper prefixes (`plugins/`, `harnesses/`), title-case
the remaining path segments, join with `-`. `plugins/manifold/overview.md` ->
`Manifold-Overview`; `harnesses/claude-code/hooks/guard-hooks.md` ->
`Claude-Code-Hooks-Guard-Hooks`. Root files keep their name (`Home`, `Glossary`).

Usage:
  flatten_wiki.py <src_dir> <out_dir>   # write flat pages to out_dir
  flatten_wiki.py <src_dir> --print-map # just print the source -> slug table
"""
import sys, os, re, posixpath

WRAPPERS = {"plugins", "harnesses"}
SPECIAL = {"Home", "_Footer", "_Sidebar"}
LINK = re.compile(r"\]\((?!https?:|mailto:|#)([^)]+)\)")


def slug(relpath: str) -> str:
    p = relpath[:-3] if relpath.endswith(".md") else relpath
    if p in SPECIAL:
        return p
    parts = p.split("/")
    while parts and parts[0] in WRAPPERS:
        parts = parts[1:]
    tc = lambda seg: "-".join(w.capitalize() for w in seg.split("-"))
    return "-".join(tc(s) for s in parts)


def collect(src: str) -> dict:
    files = {}
    for root, _, names in os.walk(src):
        for n in names:
            if n.endswith(".md"):
                rel = os.path.relpath(os.path.join(root, n), src).replace(os.sep, "/")
                files[rel] = slug(rel)
    return files


def rewrite_links(text: str, src_rel: str, by_noext: dict) -> tuple[str, list]:
    unresolved = []

    def repl(m):
        target = m.group(1)
        anchor = ""
        if "#" in target:
            target, anchor = target.split("#", 1)
            anchor = "#" + anchor
        if target == "":
            return m.group(0)  # pure anchor
        base = posixpath.dirname(src_rel)
        resolved = posixpath.normpath(posixpath.join(base, target))
        if resolved in by_noext:
            return f"]({by_noext[resolved]}{anchor})"
        unresolved.append(target)
        return m.group(0)

    return LINK.sub(repl, text), unresolved


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src = sys.argv[1]
    files = collect(src)
    by_noext = {rel[:-3]: s for rel, s in files.items()}

    # collision check
    seen = {}
    for rel, s in files.items():
        seen.setdefault(s, []).append(rel)
    collisions = {s: v for s, v in seen.items() if len(v) > 1}

    if sys.argv[2] == "--print-map":
        for rel in sorted(files):
            print(f"{rel:55s} -> {files[rel]}")
        if collisions:
            print("\nCOLLISIONS:", collisions)
            sys.exit(1)
        print(f"\n{len(files)} pages, all unique.")
        return

    if collisions:
        sys.exit(f"refusing to publish — slug collisions: {collisions}")

    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    total_unresolved = {}
    for rel, s in files.items():
        text = open(os.path.join(src, rel), encoding="utf-8").read()
        text, unresolved = rewrite_links(text, rel, by_noext)
        if unresolved:
            total_unresolved[rel] = unresolved
        open(os.path.join(out, s + ".md"), "w", encoding="utf-8").write(text)
    print(f"wrote {len(files)} flat pages to {out}")
    if total_unresolved:
        print("unresolved links (left as-is):")
        for rel, links in total_unresolved.items():
            print(f"  {rel}: {links}")


if __name__ == "__main__":
    main()
