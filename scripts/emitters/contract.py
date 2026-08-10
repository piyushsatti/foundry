#!/usr/bin/env python3
"""What every emitter module declares, and what it is handed to work with.

An emitter turns the staged neutral tree into one harness's folder. It runs
after resolution, fingerprinting, collision detection and the `provides` check
have all finished, so there is nothing left to decide about content: it may add
files, write the harness's manifest, translate a neutral file into the shape
that harness reads, and delete a neutral file that harness does not read. It
may not resolve, fetch, reorder or reach outside the tree it was given.

A module in this package declares two names and one function:

    TARGETS       the harness names it emits, as a tuple
    CAPABILITIES  one Capability per name in TARGETS
    emit          writes that harness's folder, in place, in the tree given

Everything about loss lives in the framework, never in an emitter. A module
states what its harness cannot represent and why; whether that is a refusal or
a recorded drop is decided once, in `emitters/__init__.py`, from the manifest.

The one thing an emitter does decide is a refusal about content rather than
about kinds: a transport a harness rejects, a matcher a harness ignores, a
blocking hook a harness cannot express. Those depend on what is inside the
file, not on which kind it is, so the emitter raises EmitError itself.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from resolve import CONTENT_KINDS, KINDS, METADATA_KEYS

# The Agent Plugins 1.0.0 file, at the path that specification names. Emitters
# that read it translate it; emitters whose harness reads it copy it through.
MCP_NAME = "mcp.json"

# The neutral hook declaration. This file never ships anywhere: every harness
# with a hook surface has its own event vocabulary, so an emitter that carries
# hooks translates this and removes it.
HOOKS_NAME = "hooks/hooks.yaml"

SKILL_NAME = "SKILL.md"

# Every moment a rule may name, in the order an emitter writes them out. Order
# is fixed here rather than left to a dictionary somewhere, because a folder's
# bytes are inside its own `contents` fingerprint and a map that reordered
# itself would move that number for nobody.
#
# The first three and the last are what every harness with a hook surface has
# in common, and any harness carrying hooks at all expresses all four. The two
# in the middle are not universal: a harness may carry hooks and still have no
# event for them, which is why a rule can name the harnesses it is for. That is
# the whole reason `only` exists.
MOMENTS = (
    "session-start",
    "before-tool",
    "after-tool",
    "turn-end",
    "before-compact",
    "session-end",
)

# The four every hook-carrying harness expresses. A capability naming hooks
# without these is a Foundry defect, checked when the framework dispatches.
COMMON_MOMENTS = ("session-start", "before-tool", "after-tool", "session-end")

# What a rule may name and nothing else. An unknown key is refused rather than
# ignored, because an ignored key in a guard is a guard that does less than it
# appears to.
RULE_KEYS = ("at", "run", "match", "only", "timeout")

# What YAML 1.1 turns a bare `on` key into. Named here so that a rule written
# the old way is refused by that name instead of being reported as a rule
# holding a key called True, which sends the author looking for a typo.
COERCED = True


class EmitError(Exception):
    """This harness's folder could not be written. The message is the report."""


@dataclass(frozen=True)
class Cannot:
    """One kind a harness cannot represent, and the sentence saying why.

    `why` is read into a refusal as "... is declared in <manifest>, and <why>."
    so write it as a statement about the harness, lowercase, no full stop:
    "Pi has no MCP surface", not "Foundry cannot emit MCP for Pi".
    """

    why: str


@dataclass(frozen=True)
class Capability:
    """What one harness can carry and what it cannot.

    `carries` and `cannot` together name every kind in KINDS, and the framework
    checks that before dispatching. Requiring both, rather than deriving one
    from the other, is what stops a kind added later from being silently
    carried by a harness nobody re-read: the omission is a loud error at build
    time instead of a directory shipping where nothing reads it.
    """

    carries: tuple[str, ...]
    cannot: dict[str, Cannot]
    moments: tuple[str, ...] = ()

    def expresses(self, moment: str) -> bool:
        return moment in self.moments

    def missing(self) -> tuple[str, ...]:
        """Kinds this capability answers for neither way."""
        answered = set(self.carries) | set(self.cannot)
        return tuple(kind for kind in KINDS if kind not in answered)

    def doubled(self) -> tuple[str, ...]:
        """Kinds this capability answers for both ways, which cannot be true."""
        return tuple(kind for kind in self.carries if kind in self.cannot)


# --------------------------------------------------------------- the refusal
def refuse_plugin(problem: list[str], fix: list[str]) -> EmitError:
    """A fault in a file the build has to read, which no choice of `targets` fixes.

    Headed differently from a harness refusal on purpose. `CANNOT SHIP THIS TO
    <harness>` says the plugin is fine and that one folder cannot carry it. This
    says a file the build reads before any folder is written is not readable
    yet, so every folder would be wrong the same way and naming a harness is
    beside the point.
    """
    lines = ["CANNOT BUILD THIS PLUGIN.", ""]
    lines += [f"  {line}" if line else "" for line in problem]
    lines.append("")
    lines += [f"  {line}" if line else "" for line in fix]
    return EmitError("\n".join(lines))


# ----------------------------------------------------------- shared file work
def write_json(path: Path, payload: dict) -> None:
    """Two-space indent and a trailing newline, everywhere, without exception.

    Every manifest Foundry writes goes through here. Emitters that format their
    own JSON drift apart one release at a time, and the drift lands in a
    `contents` fingerprint where it looks like a content change.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.is_file() else {}


def metadata(manifest: dict) -> dict:
    """Name, version, and whichever descriptive fields the manifest actually set.

    The order is fixed by METADATA_KEYS in `resolve.py` so that two harnesses
    describing the same plugin describe it in the same order. A field the
    author left out is left out here: no emitter invents a value.
    """
    described = {"name": manifest["id"], "version": manifest["version"]}
    for key in METADATA_KEYS:
        value = manifest.get(key)
        if value:
            described[key] = value
    return described


def frontmatter(path: Path) -> dict:
    """The YAML block a markdown content file opens with, or an empty map.

    Anything that is not a map at the top is treated as absent rather than
    refused, because deciding a content file is malformed is the validating
    tools' job and not the build's.

    A block that does not parse at all is the other thing, and it is refused.
    Not a map is an answer: the file declares nothing. Unparseable is no answer:
    the build cannot tell an `allowed-tools` line that is not there from one it
    failed to read, and reading it as absent ships a skill without the guard its
    author wrote. That is the silent drop wearing different clothes, so the
    build stops and names the file instead.
    """
    if not path.is_file():
        return {}
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            try:
                loaded = yaml.safe_load("\n".join(lines[1:index])) or {}
            except Exception as broken:  # yaml raises its own family of errors
                raise refuse_plugin(
                    [
                        f"{path.parent.name}/{path.name} does not open with a valid YAML block: {broken}.",
                        f"Look for it under skills/{path.parent.name}/ in the plugin, or in a dependency it takes that skill from.",
                        "",
                        "Foundry reads that block to find out what the file declares, so a",
                        "block it cannot parse stops the build rather than being read as",
                        "empty. Read as empty, a skill whose 'allowed-tools' line could not",
                        "be parsed would ship everywhere with no restriction on it.",
                    ],
                    [
                        "Fix the block between the two '---' lines. A value holding ':',",
                        "'{', '[', '#' or '*' has to be quoted to stay text.",
                    ],
                ) from broken
            return loaded if isinstance(loaded, dict) else {}
    return {}


def frontmatter_key(line: str) -> str:
    """The key at the start of one frontmatter line, a matching quote pair stripped.

    `"allowed-tools":` and `'arguments':` are both ordinary valid YAML, and
    read identically to the bare form by anything that actually parses them.
    A surgical line edit that keyed off the text before the first colon
    without stripping quotes read the two differently: the quoted form looked
    absent to the edit while `frontmatter` still saw it, so the edit and the
    parser disagreed about whether the key was there. Every surgical rewrite
    that keys off the start of a line reads it through here first, so a
    quoted key is recognised the same way the parser recognises it.
    """
    key = line.partition(":")[0].strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in "'\"":
        key = key[1:-1]
    return key


def skill_dirs(tree: Path) -> list[Path]:
    """Every skill directory, which is every directory holding a SKILL.md.

    Exactly one level under `skills/`, because the build refuses anything
    deeper before an emitter ever runs.
    """
    skills = tree / "skills"
    if not skills.is_dir():
        return []
    return sorted(path.parent for path in skills.glob(f"*/{SKILL_NAME}"))


def mcp_servers(tree: Path) -> dict:
    """The `mcpServers` map from the plugin's own mcp.json, or an empty map.

    A plugin's MCP servers are always its own. Nothing is ever taken from a
    dependency, so there are never two of these maps to merge.

    A file that is not JSON at all is refused here rather than read as empty.
    This is the first thing in the build that opens the file, before any harness
    folder exists, so an unreadable one read as empty means the framework never
    learns the plugin declared MCP: nothing is pruned, nothing is refused, no
    emitter that checks the file for itself is ever reached, and a plugin that
    exists to serve one server ships everywhere with no server in it.
    """
    path = tree / MCP_NAME
    try:
        payload = read_json(path)
    except json.JSONDecodeError as broken:
        raise refuse_plugin(
            [
                f"{MCP_NAME} is not valid JSON: {broken}.",
                f"Look for it at {path.relative_to(tree)} in the plugin.",
                "",
                "Foundry opens this file before it writes any folder, to find out whether",
                "the plugin declares MCP at all. A file it cannot read is refused rather",
                "than counted as absent, because counted as absent it would ship a plugin",
                "whose whole point is a server with no server in it and say nothing.",
            ],
            ["Fix the file. The line and column above are where the reader stopped."],
        ) from broken
    servers = payload.get("mcpServers") if isinstance(payload, dict) else None
    return servers if isinstance(servers, dict) else {}


def hook_rules(tree: Path) -> list[dict]:
    """The neutral hook list, in the four-moment vocabulary, or an empty list."""
    path = tree / HOOKS_NAME
    if not path.is_file():
        return []
    loaded = yaml.safe_load(path.read_text()) or []
    return loaded if isinstance(loaded, list) else []


def refuse_rule(problem: list[str], fix: list[str]) -> EmitError:
    """A fault in the neutral rule itself, which no harness could read.

    `refuse_plugin` under the name the hook checks read it by: this one says the
    file is not a hook file yet, and no choice of `targets` changes that.
    """
    return refuse_plugin(problem, fix)


def check_rule(rule: object, index: int, where: Path, tree: Path, targets: tuple[str, ...]) -> None:
    """One neutral rule, against the five keys a rule has.

    Every fault here is silent at the user's end. A harness does not report an
    event name it does not know, or a command that is not there: the hook simply
    never fires, and a hook that never fires is usually a guard somebody is
    relying on.

    Checked once on the neutral tree rather than inside the emitter that reads
    hooks, so a plugin whose only target prunes hooks still finds out its hook
    file is broken. The alternative is a rule that is never looked at until
    somebody adds a harness, months later, and then reads a refusal about a line
    they wrote long ago.
    """
    named = f"rule {index + 1} of {HOOKS_NAME}"

    if not isinstance(rule, dict):
        raise refuse_rule(
            [f"{named} is not a block.", f"Declared in {where}."],
            ["Write each rule as a block naming 'at' and 'run'."],
        )

    if COERCED in rule:
        raise refuse_rule(
            [
                f"{named} names the moment with 'on'.",
                f"Declared in {where}.",
                "",
                "YAML 1.1 resolves a bare 'on' to the boolean true, so that line does not",
                "reach Foundry as a key called 'on' at all, and the rule it belongs to",
                "names no moment. Every YAML 1.1 reader does this, so quoting it here",
                "would only move the problem to whatever reads the file next.",
            ],
            ["Rename the key to 'at'. The value does not change."],
        )

    unknown = sorted(key for key in rule if key not in RULE_KEYS)
    if unknown:
        listed = ", ".join(repr(key) for key in unknown)
        it = "it" if len(unknown) == 1 else "them"
        raise refuse_rule(
            [
                f"{named} holds {listed}.",
                f"A hook rule names {', '.join(RULE_KEYS)} and nothing else.",
                f"Declared in {where}.",
                "",
                "An unknown key is refused rather than ignored: a guard that quietly",
                "does less than it says is worse than one that does not build.",
            ],
            [f"Take {it} out."],
        )

    moment = rule.get("at")
    if moment not in MOMENTS:
        said = "names no 'at'" if "at" not in rule else f"is set to run at {moment!r}"
        raise refuse_rule(
            [
                f"{named} {said}.",
                f"The moments a hook can name are: {', '.join(MOMENTS)}.",
                f"Declared in {where}.",
                "",
                "A moment outside them is a hook that does not fire, which is a guard",
                "that is not there.",
            ],
            ["Set 'at' to one of those."],
        )

    run = rule.get("run")
    if not isinstance(run, str) or not run:
        raise refuse_rule(
            [f"{named} names no 'run'.", f"Declared in {where}."],
            ["Add 'run', the path to the file this hook runs."],
        )

    if not (tree / run).is_file():
        raise refuse_rule(
            [
                f"{named} runs {run!r}, which this plugin does not hold.",
                f"Declared in {where}.",
                "",
                "'run' is a path to a file inside the plugin, not a shell line, so that",
                "a hook pointing at nothing is caught here rather than never firing on",
                "somebody else's machine. Put any shell work inside that file.",
            ],
            [
                "Either correct the path, or add the file. If 'exclude' names the",
                "directory it lives in, that is why it is not here.",
            ],
        )

    match = rule.get("match")
    if match is not None and not isinstance(match, str):
        raise refuse_rule(
            [f"{named} has a 'match' that is not a line of text.", f"Declared in {where}."],
            ["Write it as a single pattern, or take the line out."],
        )

    timeout = rule.get("timeout")
    if timeout is not None and (isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0):
        raise refuse_rule(
            [
                f"{named} has a 'timeout' of {timeout!r}.",
                f"Declared in {where}.",
                "",
                "A timeout is a whole number of seconds, greater than zero. It exists",
                "because some harnesses give a hook a budget short enough to kill work",
                "the author meant to finish, and the only way to say otherwise is to",
                "name the number.",
            ],
            ["Write a whole number of seconds, or take the line out."],
        )

    only = rule.get("only")
    if only is not None:
        if not isinstance(only, list) or not only or not all(isinstance(name, str) for name in only):
            raise refuse_rule(
                [f"{named} has an 'only' that is not a list of harness names.", f"Declared in {where}."],
                ["Write it as a list, such as 'only: [claude-code]', or take the line out."],
            )
        outside = sorted(name for name in only if name not in targets)
        if outside:
            listed = ", ".join(repr(name) for name in outside)
            raise refuse_rule(
                [
                    f"{named} is for {listed}, which this plugin does not build.",
                    f"targets: {', '.join(targets)}.",
                    f"Declared in {where}.",
                    "",
                    "A rule reserved for a harness nobody builds fires nowhere, and reads",
                    "as a rule somebody wrote. That is the same fault as a waiver naming",
                    "a harness outside 'targets'.",
                ],
                ["Either add that harness to 'targets', or correct the name in 'only'."],
            )


def check_rules(tree: Path, manifest_path: Path, targets: tuple[str, ...]) -> None:
    """Every rule in the neutral file, before any harness folder is written."""
    path = tree / HOOKS_NAME
    if not path.is_file():
        return
    try:
        rules = hook_rules(tree)
    except Exception as broken:  # yaml raises its own family of errors
        raise refuse_rule(
            [f"{HOOKS_NAME} is not valid YAML: {broken}.", f"Declared in {manifest_path}."],
            ["Fix the file."],
        ) from broken

    if not isinstance(rules, list):
        raise refuse_rule(
            [f"{HOOKS_NAME} does not hold a list of rules.", f"Declared in {manifest_path}."],
            ["Write it as a list, one block per hook, each naming 'at' and 'run'."],
        )

    for index, rule in enumerate(rules):
        check_rule(rule, index, manifest_path, tree, targets)


def rules_for(rules: list[dict], target: str) -> tuple[list[dict], list[dict]]:
    """The rules this harness carries, and the ones it will not, already checked.

    A rule with no `only` is for every harness that carries hooks. A rule naming
    `only` is for the harnesses it names and is absent everywhere else, which is
    a loss the framework prints and records rather than something an emitter
    decides quietly.
    """
    kept, dropped = [], []
    for rule in rules:
        only = rule.get("only")
        (kept if (only is None or target in only) else dropped).append(rule)
    return kept, dropped


def remove(path: Path) -> None:
    """Take a file or a directory out of a target's folder, if it is there.

    No harness folder may hold a file that harness does not read, so removing
    a neutral file an emitter has just translated is the normal end of the
    translation rather than tidying.
    """
    import shutil

    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink()


__all__ = [
    "COMMON_MOMENTS",
    "CONTENT_KINDS",
    "Cannot",
    "Capability",
    "EmitError",
    "HOOKS_NAME",
    "KINDS",
    "MCP_NAME",
    "METADATA_KEYS",
    "MOMENTS",
    "RULE_KEYS",
    "SKILL_NAME",
    "check_rule",
    "check_rules",
    "frontmatter",
    "frontmatter_key",
    "hook_rules",
    "refuse_plugin",
    "refuse_rule",
    "rules_for",
    "mcp_servers",
    "metadata",
    "read_json",
    "remove",
    "skill_dirs",
    "write_json",
]
