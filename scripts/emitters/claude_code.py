#!/usr/bin/env python3
"""The folder Claude Code installs: its manifest, its MCP file, its hook file.

Claude Code carries every kind Foundry models, so nothing is ever pruned from
this folder and no plugin ever needs a `degrade.claude-code` block. Carrying a
kind is not the same as copying it through, though, and two of the six arrive
in a neutral shape Claude Code does not read:

    neutral                 Claude Code reads          checked against
    mcp.json                .mcp.json                  the plugins reference
    hooks/hooks.yaml        hooks/hooks.json           the plugins reference

Both were shipped untranslated until this change, and neither failed loudly.
`claude plugin details` on such a folder reports `MCP servers (0)` and
`Hooks (0)` while the install reports success and the two files sit there
unread. That is a silent drop, which is the one outcome the loss policy says
cannot exist, and it was worse than a refusal because nothing anywhere said it
had happened. The neutral file is removed once it has been translated, because
no harness folder may hold a file that harness does not read.

Three differences between the two shapes, each verified against Claude Code's
own documentation rather than inferred:

  the MCP wrapper   The portable file carries `$schema` and `mcpServers`.
                    Claude Code's carries `mcpServers` alone, so only the
                    server map crosses over. Transports need no translation:
                    Claude Code takes `streamable-http` as an alias for its own
                    `http`, and takes `stdio` and `sse` under those names.

  the path variables Agent Plugins reserves `${PLUGIN_ROOT}` and
                    `${PLUGIN_DATA}` for the client to expand. Claude Code
                    expands `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}`
                    and knows nothing of the shorter pair, which would reach a
                    user as a literal string in a path. Both are renamed
                    everywhere they appear in either translated file.

  the hook events   Claude Code names about thirty events, and every moment in
                    the neutral vocabulary lands on exactly one of them, so
                    nothing here is approximated. A moment with no exact event
                    would be a hook that does not fire, which is a false
                    security claim, and the framework refuses it rather than
                    mapping it to the nearest thing.

Claude Code is the only harness that expresses all six moments today, which is
why it is the only one that can carry `turn-end` and `before-compact`. Those
two are what a plugin needs to act at the end of a turn or before the context
is compacted, and no other harness Foundry emits for has an event for either.

The rule itself is checked once against the neutral vocabulary, in
`contract.check_rules`, before any folder is written. Nothing in this file
validates a rule: a plugin whose only target prunes hooks would then never find
out its hook file is broken.
"""

from __future__ import annotations

import json
from pathlib import Path

from .contract import (
    HOOKS_NAME,
    KINDS,
    MCP_NAME,
    MOMENTS,
    Capability,
    EmitError,
    hook_rules,
    metadata,
    read_json,
    remove,
    rules_for,
    write_json,
)

TARGETS = ("claude-code",)

CAPABILITIES = {
    "claude-code": Capability(carries=KINDS, cannot={}, moments=MOMENTS),
}

METADATA_DIR = ".claude-plugin"
METADATA_NAME = "plugin.json"

# The two paths Claude Code actually reads, from the plugins reference. Neither
# is the neutral name, and a file at the neutral name is not reported as an
# error by Claude Code, it is simply never opened.
MCP_READS = ".mcp.json"
HOOKS_READS = "hooks/hooks.json"

# The client expands the name on the right and passes the name on the left
# through as text. Applied to every string in both translated files.
PATH_VARIABLES = (
    ("${PLUGIN_ROOT}", "${CLAUDE_PLUGIN_ROOT}"),
    ("${PLUGIN_DATA}", "${CLAUDE_PLUGIN_DATA}"),
)

# Each neutral moment, and the one Claude Code event it names. Keyed by moment
# and read in the order of MOMENTS rather than the order written here, so this
# map cannot reorder the events in a folder whose bytes are inside its own
# `contents` fingerprint.
#
# `turn-end` is Stop, which runs when Claude has finished responding, and is the
# last point in a turn a plugin can act. `before-compact` is PreCompact, which
# runs before the context is compacted, automatically or by hand. Both were
# verified against a live client rather than read off a list.
MOMENT_EVENTS = {
    "session-start": "SessionStart",
    "before-tool": "PreToolUse",
    "after-tool": "PostToolUse",
    "turn-end": "Stop",
    "before-compact": "PreCompact",
    "session-end": "SessionEnd",
}


def refuse(problem: list[str], fix: list[str]) -> EmitError:
    """What is wrong, then what to do about it. A refusal with no next step is a bug."""
    lines = ["CANNOT SHIP THIS TO CLAUDE-CODE.", ""]
    lines += [f"  {line}" if line else "" for line in problem]
    lines.append("")
    lines += [f"  {line}" if line else "" for line in fix]
    return EmitError("\n".join(lines))


def rename_variables(value: object) -> object:
    """Claude Code's own path variables, everywhere a string appears.

    Walks the whole structure rather than a fixed list of fields, because these
    variables are legal in a command, in any argument, in any environment value
    and in a hook's command line, and a field this misses reaches a user as an
    unexpanded literal inside a path.
    """
    if isinstance(value, str):
        for neutral, theirs in PATH_VARIABLES:
            value = value.replace(neutral, theirs)
        return value
    if isinstance(value, dict):
        return {key: rename_variables(item) for key, item in value.items()}
    if isinstance(value, list):
        return [rename_variables(item) for item in value]
    return value


# ------------------------------------------------------------------- mcp.json
def translate_mcp(manifest: dict, tree: Path) -> None:
    """The server map, under the name Claude Code opens, with the neutral one gone.

    Only `mcpServers` crosses over. `$schema` names the portable specification
    this file was written against, which is a fact about the source and not
    about the folder Claude Code installs, and Claude Code's format does not
    name it.
    """
    neutral = tree / MCP_NAME
    if not neutral.is_file():
        return

    try:
        payload = read_json(neutral)
    except json.JSONDecodeError as broken:
        raise refuse(
            [
                f"{MCP_NAME} is not valid JSON: {broken}.",
                f"Declared in {manifest['root'] / MCP_NAME}.",
            ],
            ["Fix the file."],
        ) from broken

    servers = payload.get("mcpServers") if isinstance(payload, dict) else None
    if not isinstance(servers, dict):
        raise refuse(
            [
                f"{MCP_NAME} has no 'mcpServers' object.",
                f"Declared in {manifest['root'] / MCP_NAME}.",
                "",
                "Claude Code reads that map and nothing else out of this file, so a",
                "plugin without one installs, reports success, and starts no server.",
            ],
            ["Add it. An empty one is fine, a missing one is not."],
        )

    remove(neutral)
    write_json(tree / MCP_READS, {"mcpServers": rename_variables(servers)})


# ----------------------------------------------------------- hooks/hooks.yaml
def translate_hooks(target: str, tree: Path) -> None:
    """Each moment as Claude Code's own event, with the neutral file gone.

    Only `hooks/hooks.yaml` is removed, never the `hooks/` directory: it is a
    content directory and the scripts the rules run usually live beside it.

    Events are written in the fixed order of MOMENTS and rules keep the order
    the author wrote them, so the same source always produces the same bytes.
    A folder's bytes are inside its own `contents` fingerprint, and a map whose
    order came from a dictionary somewhere would move that number for nobody.

    Every rule reaching here has already been checked against the neutral
    vocabulary, and every rule this harness does not carry has already been
    printed and recorded by the framework. What is left is translation.
    """
    neutral = tree / HOOKS_NAME
    if not neutral.is_file():
        return

    kept, _ = rules_for(hook_rules(tree), target)

    events: dict[str, list[dict]] = {}
    for moment in MOMENTS:
        entries = []
        for rule in kept:
            if rule["at"] != moment:
                continue
            entry: dict[str, object] = {}
            if rule.get("match"):
                entry["matcher"] = rule["match"]
            # The variable is quoted and the rest of the path is not, which is
            # the form Claude Code's own documentation uses: it survives an
            # install path with a space in it without quoting the whole line
            # into a single argument.
            hook: dict[str, object] = {
                "type": "command",
                "command": f'"${{CLAUDE_PLUGIN_ROOT}}"/{rule["run"]}',
            }
            if rule.get("timeout"):
                hook["timeout"] = rule["timeout"]
            entry["hooks"] = [hook]
            entries.append(entry)
        if entries:
            events[MOMENT_EVENTS[moment]] = entries

    remove(neutral)
    if events:
        write_json(tree / HOOKS_READS, {"hooks": events})


def refuse_to_overwrite_theirs(target: str, manifest: dict, tree: Path) -> None:
    """A file the author wrote is not a file this folder may replace.

    Every top-level file ships unless 'exclude' names it, so a plugin repository
    that keeps its own `.claude-plugin/plugin.json` has already copied it into
    the neutral tree, inside the fingerprint its own pin names. `emit` writes
    that exact path on every build with no guard at all, the same fault
    `agent_plugins.refuse_to_overwrite_theirs` and
    `instructions.refuse_to_overwrite_theirs` already close for their own
    manifests. `.claude` is in `NEVER_SHIP`, but `.claude-plugin` is a plugin's
    own directory name and is not, so the author's file reaches this tree.

    `hooks/hooks.json` is not the same shape, and is not checked the same way.
    `translate_hooks` writes to that path only when at least one rule survives
    for this target: a plugin whose `hooks/hooks.yaml` is empty, or whose every
    rule names an `only` that excludes claude-code, leaves `events` empty and
    never opens `hooks/hooks.json` at all, let alone overwrites it. So the
    check here reruns that same filter rather than only asking whether the
    neutral file exists: the file existing is not enough, since the build it
    guards might never have written to that path regardless. The collision is
    real only when a rule would actually be written there, because that is the
    one case where the plugin is also asking Foundry to translate hooks into
    the exact path the author's own file already occupies, and that is an
    unambiguous conflict rather than a maybe.

    Both are the build picking a winner if it proceeds, so it refuses instead.
    """
    theirs = []
    if (tree / METADATA_DIR / METADATA_NAME).exists():
        theirs.append(f"{METADATA_DIR}/{METADATA_NAME}")
    kept, _ = rules_for(hook_rules(tree), target)
    if kept and (tree / HOOKS_READS).exists():
        theirs.append(HOOKS_READS)
    if not theirs:
        return

    subject = "That name is" if len(theirs) == 1 else "Each name above is"
    raise refuse(
        [
            *theirs,
            "",
            f"{subject} both a file this plugin already holds and a file this",
            "folder writes. Overwriting yours would swap what you wrote for a",
            "generated one, and keeping yours would ship a folder where a file",
            "Claude Code reads is not the one you wrote.",
            "",
            "Every top-level file ships unless 'exclude' names it.",
            "",
            f"Declared by {manifest['manifest_path']}.",
        ],
        [
            "Either add each name above to 'exclude', so it stays a file of this",
            "repository and ships nowhere, or drop claude-code from 'targets'.",
        ],
    )


# ------------------------------------------------------------------- emitting
def emit(target: str, manifest: dict, tree: Path) -> None:
    """Refuse a collision first, then the manifest, then the two translations."""
    refuse_to_overwrite_theirs(target, manifest, tree)
    write_json(tree / METADATA_DIR / METADATA_NAME, metadata(manifest))
    translate_mcp(manifest, tree)
    translate_hooks(target, tree)
