"""
Build a tiny v0.2-style git repo for importer tests.

Used by tests via `build_mini_repo(target_dir)` — creates a 2-commit history
under `target_dir` (caller-supplied, typically a tempdir).

Layout:
    <target_dir>/
      specs/
        spec.yaml
        intent/
          I.1.md          # first version
                          # second commit revises body

Git history: 2 commits with deterministic author dates.
"""
import subprocess
from pathlib import Path


SPEC_YAML = """name: mini
framework_version: 0.2.0
layers:
  - name: intent
    purpose: "why"
    verdict_default: human_signoff
  - name: realizations
    purpose: "files"
    verdict_default: automated_check
"""

I1_V1 = """---
id: I.1
title: Initial thesis
layer: intent
kind: spec
parents: []
verdict:
  mechanism: human_signoff
  status: satisfied
---

# I.1

The thing exists.
"""

I1_V2 = """---
id: I.1
title: Revised thesis
layer: intent
kind: spec
parents: []
verdict:
  mechanism: human_signoff
  status: satisfied
---

# I.1

The thing exists and matters.
"""


def _run(args, cwd, env=None):
    full_env = {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@x",
                "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@x"}
    if env:
        full_env.update(env)
    subprocess.run(args, cwd=str(cwd), check=True,
                   capture_output=True, env={**__import__("os").environ, **full_env})


def build_mini_repo(target_dir: Path) -> Path:
    """Create a fresh mini v0.2 repo at `target_dir`. Returns the path."""
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    specs = target_dir / "specs"
    (specs / "intent").mkdir(parents=True, exist_ok=True)
    (specs / "realizations").mkdir(parents=True, exist_ok=True)

    (specs / "spec.yaml").write_text(SPEC_YAML, encoding="utf-8")
    (specs / "intent" / "I.1.md").write_text(I1_V1, encoding="utf-8")

    _run(["git", "init", "-q", "-b", "main"], cwd=target_dir)
    _run(["git", "config", "user.email", "t@x"], cwd=target_dir)
    _run(["git", "config", "user.name", "Test"], cwd=target_dir)
    _run(["git", "add", "specs/"], cwd=target_dir)
    _run(["git", "commit", "-q", "-m", "initial spec"], cwd=target_dir,
         env={"GIT_AUTHOR_DATE": "2025-01-01T00:00:00+00:00",
              "GIT_COMMITTER_DATE": "2025-01-01T00:00:00+00:00"})

    (specs / "intent" / "I.1.md").write_text(I1_V2, encoding="utf-8")
    _run(["git", "add", "specs/"], cwd=target_dir)
    _run(["git", "commit", "-q", "-m", "revise I.1 body"], cwd=target_dir,
         env={"GIT_AUTHOR_DATE": "2025-02-01T00:00:00+00:00",
              "GIT_COMMITTER_DATE": "2025-02-01T00:00:00+00:00"})

    return target_dir
