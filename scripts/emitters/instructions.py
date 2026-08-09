#!/usr/bin/env python3
"""Repository instruction files, which are copied into a repository, not installed.

Every other target Foundry emits is a folder somebody installs. This one is
not, and the difference is the whole reason it exists. No surveyed harness lets
a package carry a repository instructions file: Claude Code's plugin reference
states that a `CLAUDE.md` at a plugin root is not loaded as project context and
that plugins contribute through skills, agents and hooks instead. So the only
way an instructions file reaches a repository is that a person copies it there,
and from that moment nothing installs it, updates it or removes it. A later
version of the plugin does not reach the copy. That has to be said in the
plugin's README rather than glossed as support, and it is said again at the top
of every file this emitter writes, because the folder is what travels and the
README is not.

Three filenames, because three harnesses read three names, each checked against
that project's own documentation on 2026-08-09:

  AGENTS.md   what Codex, Cursor, Copilot, VS Code, Zed and most others read.
              No schema, no frontmatter, no validator: it is plain markdown and
              there is nothing to conform to, so the value is entirely in the
              filename and in what the prose says
  CLAUDE.md   Claude Code reads this and states plainly that it does not read
              AGENTS.md. Its own documentation gives the fix used here, a
              CLAUDE.md holding `@AGENTS.md`
  GEMINI.md   Gemini CLI's default context filename. It reads AGENTS.md only if
              a user opts in through `context.fileName` in settings.json, which
              is a user's choice and not a thing a plugin can arrange. It reads
              `@file.md` imports, so the same one-line pointer works

The two pointers exist so that one file holds the instructions and the other
two agree with it forever. Writing the prose three times would let two copies of
it drift, and a reader has no way to tell which copy is the current one.

What an instructions file can carry is prose, and what prose can do is say that
something exists and when to reach for it. So a skill and a command come along
as the files the author wrote, untouched, with one entry each in AGENTS.md
naming the file and carrying the `description` verbatim as the sentence that
says when it applies. Nothing is inlined: an instructions file is in context for
every session, and pasting a skill's body into one turns something read when
relevant into something read always, which every harness's own guidance warns
against. An agent cannot come along at all, and that loss is stated below.

The folder holds the three files and the content they name, and nothing else.
Everything else a plugin ships is taken out, because this folder's contents are
copied into somebody else's repository: a README carried in here would land on
top of theirs, and a skill directory holding no SKILL.md would land there as a
directory nobody put there and nothing points at.

Taking something out is a change to what the author ships, so every path this
folder leaves behind is both printed and put on the record. The lock file's
`dropped` list is for a kind a harness cannot carry, and these are not kinds:
they are files the author wrote that this folder's own generated index does
not name. They land in this same lock file's `left_behind` list instead, read
back from a private file the emitter leaves in the tree for `write_lock` in
`scripts/build.py` to find, because printing reaches whoever is watching the
build run and not whoever downloads this folder afterwards, and this is the
one folder that lands inside somebody else's repository where nobody ever
sees that log.

A folder that names nothing is refused. Three files carrying a title and one
description line install cleanly, report success and change nothing about how
anybody's agent behaves, and that silent nothing is the failure this target
exists to avoid rather than to produce.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .contract import (
    CONTENT_KINDS,
    MCP_NAME,
    SKILL_NAME,
    Cannot,
    Capability,
    EmitError,
    frontmatter,
    remove,
    skill_dirs,
)

TARGETS = ("instructions",)

# The file that holds the instructions, and the two that only point at it. Each
# pointer's sentence is the reason that file exists, and it is written into the
# file itself: the person merging it into a repository that already has one is
# the person who needs to know why there are three.
AGENTS_NAME = "AGENTS.md"

POINTERS = {
    "CLAUDE.md": "Claude Code reads CLAUDE.md and states plainly that it does not read AGENTS.md",
    "GEMINI.md": "Gemini CLI reads GEMINI.md unless a user opts into another name through context.fileName",
}

FILENAMES = (AGENTS_NAME, *POINTERS)

# Where a kind sits at the top of a folder. A content kind is a directory of
# its own name and `mcp` is one file, so either is a name this folder can keep.
# `allowed-tools` is a field inside a skill rather than a path, so it is absent
# here on purpose: a capability carrying it leaves nothing extra at the top.
AT_TOP = {**{kind: kind for kind in CONTENT_KINDS}, "mcp": MCP_NAME}

# A private handoff to write_lock in scripts/build.py, the only other place
# this name is read. Printing what this folder left behind, which report()
# below already does, reaches whoever is watching the build run. It does not
# reach whoever downloads this folder afterwards and never sees that output,
# and this is the one folder that lands inside somebody else's repository
# rather than being installed, so a person reading it later than the build
# has no other way to find out. write_lock reads this file back into this
# folder's own lock file and deletes it before the folder is fingerprinted,
# so nothing written here ships and nothing written here moves a `contents`
# fingerprint: it is read and gone before either is decided.
LEFT_BEHIND_NAME = ".foundry-left-behind.json"

CAPABILITIES = {
    "instructions": Capability(
        carries=("skills", "commands"),
        cannot={
            "agents": Cannot(
                "an agent file is a system prompt for a separate agent, so always-on prose "
                "carrying it would redefine the reader rather than describe the agent"
            ),
            "hooks": Cannot("an instructions file is prose and runs nothing"),
            "mcp": Cannot("an instructions file cannot start a server"),
            "allowed-tools": Cannot("an instructions file enforces nothing"),
        },
    ),
}


def kept_names(target: str) -> tuple[str, ...]:
    """What a person copies into their repository, and the whole of what this folder may hold.

    Everything else is taken out rather than shipped: this is the one target
    whose contents land in a working tree somebody else owns, so a stray file
    here is not an unread file, it is a file that overwrites one of theirs.

    Which kinds this harness carries is stated once, in its Capability, and read
    back from there rather than written out a second time. Two statements of one
    fact drift, and these two would never be read against each other: a kind
    added to `carries` is pruned by nothing and then deleted here, so the folder
    arrives without it while the capability says it is carried.
    """
    carried = CAPABILITIES[target].carries
    return FILENAMES + tuple(AT_TOP[kind] for kind in carried if kind in AT_TOP)


@dataclass(frozen=True)
class Entry:
    """One thing AGENTS.md names: the file to read, and when to read it."""

    heading: str
    path: str
    description: str


def emit(target: str, manifest: dict, tree: Path) -> None:
    """Write the three files, then keep only what a person is meant to copy."""
    refuse_to_overwrite_theirs(manifest, tree)
    skills = skill_entries(manifest, tree)
    commands = command_entries(manifest, tree)
    refuse_to_name_nothing(manifest, skills, commands)

    (tree / AGENTS_NAME).write_text(agents_file(manifest, skills, commands))
    for name, because in POINTERS.items():
        (tree / name).write_text(pointer_file(manifest, name, because))

    left_behind = keep_only_what_is_named(target, tree, skills, commands)
    report(target, left_behind)
    record_left_behind(tree, left_behind)


# ------------------------------------------------------------- what is refused
def refuse_to_overwrite_theirs(manifest: dict, tree: Path) -> None:
    """An instructions file the author wrote is not a file this target may replace.

    A plugin repository that holds its own `AGENTS.md` or `CLAUDE.md` almost
    always holds instructions for working on the plugin, and those ship today
    because a manifest ships every top-level file it does not exclude. Writing
    over one would silently swap the author's instructions for a generated
    pointer, and keeping theirs would ship a file that imports an AGENTS.md that
    is not there. Both are the build picking a winner, so it refuses instead.
    """
    theirs = [name for name in FILENAMES if (tree / name).exists()]
    if not theirs:
        return
    subject = "That name is" if len(theirs) == 1 else "Each name above is"
    raise EmitError(
        "CANNOT SHIP THIS TO INSTRUCTIONS.\n\n  "
        + "\n  ".join(theirs)
        + f"\n\n  {subject} both a file this plugin already holds and a file this\n"
        f"  folder writes. Overwriting yours would swap your instructions for a\n"
        f"  generated pointer, and keeping yours would ship a file naming an\n"
        f"  {AGENTS_NAME} that is not there.\n\n"
        f"  Every top-level file ships unless 'exclude' names it, and an instructions\n"
        f"  file in a plugin repository is usually about working on the plugin rather\n"
        f"  than about using it.\n\n"
        f"  Declared by {manifest['manifest_path']}.\n\n"
        f"  Either add each name above to 'exclude', so it stays a file of this\n"
        f"  repository and ships nowhere, or drop instructions from 'targets'."
    )


def refuse_to_name_nothing(manifest: dict, skills: list[Entry], commands: list[Entry]) -> None:
    """A folder whose instructions name no file is a folder that does nothing.

    Every other target is refused when a kind it cannot carry is declared, and
    the framework decides that from the manifest before any emitter runs. This
    one cannot be decided there: whether the index came out empty is known only
    after the tree has been read, so it is a refusal about content and belongs
    here.

    The absence is invisible without it. The folder copies in, the harness loads
    the files, and the whole of what it delivers is a title and one description
    line, because Claude Code strips block-level HTML comments before a
    CLAUDE.md reaches a session, so even the provenance at the top does not
    arrive (https://code.claude.com/docs/en/memory). Nothing errors, nothing
    warns, and the author is told the build succeeded.
    """
    if skills or commands:
        return
    raise EmitError(
        f"CANNOT SHIP THIS TO INSTRUCTIONS.\n\n"
        f"  {AGENTS_NAME} would name nothing.\n\n"
        f"  This plugin holds no skills/<name>/{SKILL_NAME} and no commands/<name>.md,\n"
        f"  and naming a file and saying when to read it is the whole of what an\n"
        f"  instructions file can do. The folder would carry a title, one description\n"
        f"  line and two pointers into a repository somebody else owns, and nothing\n"
        f"  there would behave any differently for having them.\n\n"
        f"  Declared by {manifest['manifest_path']}.\n\n"
        f"  Either add a skill or a command for {AGENTS_NAME} to name, or drop\n"
        f"  instructions from 'targets'."
    )


def describe(manifest: dict, path: Path, relative: str, required: bool) -> str:
    """The sentence saying when to read a file, refused when a skill has none.

    A skill is reached for because it became relevant, and its `description` is
    the only thing in an always-on file that can say when that is. Without one
    the entry is a heading nobody can act on, so the skill gets read in every
    session or in none, and neither is what the author wrote. A command is asked
    for by name, so its name already says when, and a missing description there
    costs a line of help rather than the whole mechanism.
    """
    value = frontmatter(path).get("description")
    text = str(value).strip() if value else ""
    if text or not required:
        return text
    raise EmitError(
        f"CANNOT SHIP THIS TO INSTRUCTIONS.\n\n"
        f"  {relative} has no 'description'.\n\n"
        f"  An instructions file is in context for every session, so the description\n"
        f"  is the only thing in it that can say when this skill applies. Without one\n"
        f"  the entry is a heading nobody can act on, and the skill gets followed in\n"
        f"  every session or in none.\n\n"
        f"  Declared by {manifest['manifest_path']}.\n\n"
        f"  Either write a description into that file, which the Agent Skills format\n"
        f"  requires of every skill anyway, or drop instructions from 'targets'."
    )


# ------------------------------------------------------------ what gets indexed
def skill_entries(manifest: dict, tree: Path) -> list[Entry]:
    """One entry per skill, named by its directory, which is its name everywhere."""
    entries = []
    for skill in skill_dirs(tree):
        relative = f"skills/{skill.name}/{SKILL_NAME}"
        entries.append(
            Entry(
                heading=skill.name,
                path=relative,
                description=describe(manifest, skill / SKILL_NAME, relative, required=True),
            )
        )
    return entries


def command_entries(manifest: dict, tree: Path) -> list[Entry]:
    """One entry per command file, at whatever depth the author grouped them.

    Commands nest, unlike skills: a harness that groups them reads
    `commands/git/commit.md` as one name made of two parts. Nothing here depends
    on the depth, because the entry names a path a reader opens rather than a
    name a harness registers, so the grouping survives as written.
    """
    commands = tree / "commands"
    if not commands.is_dir():
        return []
    entries = []
    for path in sorted(commands.rglob("*.md")):
        relative = path.relative_to(commands)
        if any(part.startswith(".") for part in relative.parts):
            continue
        entries.append(
            Entry(
                heading=str(relative.with_suffix("")),
                path=f"commands/{relative}",
                description=describe(manifest, path, f"commands/{relative}", required=False),
            )
        )
    return entries


# -------------------------------------------------------------- what is written
def provenance(manifest: dict) -> list[str]:
    """Which plugin this came from, for the person holding a copy of it later.

    A copied file has no version, no lock file beside it and no way back to the
    repository it came from, so the only place that can say is the file.
    """
    lines = [f"{manifest['id']} {manifest['version']}, written by Foundry."]
    if manifest.get("homepage"):
        lines.append(f"Source: {manifest['homepage']}")
    return lines


def agents_file(manifest: dict, skills: list[Entry], commands: list[Entry]) -> str:
    """The instructions themselves: what this plugin is, and what to read when."""
    lines = [
        "<!--",
        *provenance(manifest),
        "",
        "This folder is not installed. No agent harness lets a package carry a",
        "repository instructions file, so these files are copied by hand into the",
        "repository where they should apply, and nothing there installs, updates or",
        "removes them. A later version of this plugin does not reach the copy.",
        "",
        "Copy everything in this folder except foundry.lock.json into the root of that",
        "repository. Where a file or a directory of the same name is already there,",
        "merge into it rather than replacing it.",
        "-->",
        "",
        f"# {manifest['id']}",
        "",
    ]
    if manifest.get("description"):
        lines += [manifest["description"], ""]

    if skills:
        lines += [
            "## Skills",
            "",
            "Read the file named under a heading before doing the work that heading",
            "describes, and only when the sentence under it applies.",
            "",
        ]
        lines += section(skills)

    if commands:
        lines += [
            "## Commands",
            "",
            "These are asked for by name. A repository instructions file has no slash",
            "commands, so when someone asks for one of these, read its file and follow it.",
            "",
        ]
        lines += section(commands)

    return "\n".join(lines).rstrip("\n") + "\n"


def section(entries: list[Entry]) -> list[str]:
    lines = []
    for entry in entries:
        lines.append(f"### {entry.heading}")
        lines.append("")
        if entry.description:
            lines += [entry.description, ""]
        lines += [f"Read `{entry.path}`.", ""]
    return lines


def pointer_file(manifest: dict, name: str, because: str) -> str:
    """One line pulling in AGENTS.md, and a comment saying why the file exists.

    The prose lives in one file so that three files cannot disagree about what
    the plugin says. Both harnesses that read their own name also read an
    `@path` import, which is what makes one file possible at all, and Claude
    Code's own documentation gives exactly this arrangement.
    """
    return "\n".join(
        [
            "<!--",
            *provenance(manifest),
            "",
            *wrap(f"{because}, so this file exists only to pull in the {AGENTS_NAME} beside it."),
            f"If this repository already has a {name}, add the line below to it and delete",
            "this file.",
            "-->",
            "",
            f"@{AGENTS_NAME}",
            "",
        ]
    )


def wrap(text: str, width: int = 78) -> list[str]:
    """Comment prose at a readable width, without importing anything to do it."""
    lines, current = [], ""
    for word in text.split():
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines


# --------------------------------------------------------- what is left behind
def keep_only_what_is_named(target: str, tree: Path, skills: list[Entry], commands: list[Entry]) -> list[str]:
    """Everything the three files do not name goes, and comes back as a report.

    Keeping a whole content directory is not enough. A skill directory with no
    SKILL.md, a command that is not markdown, a supporting file beside one: none
    of them is named by anything this folder writes, and every one of them lands
    in a working tree somebody else owns as a path nobody put there. That is the
    same hazard as the README the loop below takes out, and being one level down
    does not soften it.

    A content directory left holding nothing goes with it. An empty `skills/`
    arriving in a repository root is still a directory that repository did not
    have, and the placeholder keeping it alive in the plugin repo is a fact
    about that repo rather than anything to deliver.
    """
    keep = kept_names(target)
    left_behind = []
    for entry in sorted(tree.iterdir()):
        if entry.name in keep:
            continue
        left_behind.append(named(entry, tree))
        remove(entry)

    skills_named = {(tree / entry.path).parent for entry in skills}
    commands_named = {tree / entry.path for entry in commands}
    left_behind += keep_only(tree / "skills", skills_named, tree)
    left_behind += keep_only(tree / "commands", commands_named, tree)
    return sorted(left_behind)


def keep_only(path: Path, wanted: set[Path], tree: Path) -> list[str]:
    """Take out everything under one directory except the paths handed in.

    A wanted path is kept whole: a skill is its directory, because the files
    beside its SKILL.md are the skill, and a command is the one markdown file.
    A directory holding nothing wanted is taken out entire rather than walked,
    so the report names the grouping the author will recognise instead of every
    file underneath it.
    """
    if not path.exists():
        return []
    if not wanted or not path.is_dir():
        name = named(path, tree)
        remove(path)
        return [name]

    left_behind = []
    for entry in sorted(path.iterdir()):
        if entry in wanted:
            continue
        if entry.is_dir() and any(kept.is_relative_to(entry) for kept in wanted):
            left_behind += keep_only(entry, wanted, tree)
            continue
        left_behind.append(named(entry, tree))
        remove(entry)
    return left_behind


def named(path: Path, tree: Path) -> str:
    """A path as it reads in a report, with a directory marked as one."""
    relative = str(path.relative_to(tree))
    return f"{relative}/" if path.is_dir() else relative


def report(target: str, left_behind: list[str]) -> None:
    """Print what was taken out: a deletion nobody sees is one nobody can review.

    Reaches whoever is watching this build run. `record_left_behind`, called
    right after this in `emit`, is what reaches whoever downloads the folder
    afterwards: the same list, put on this folder's own lock file rather than
    only the terminal.
    """
    if not left_behind:
        return
    thing = "path" if len(left_behind) == 1 else "paths"
    for line in wrap(
        f"{target} left behind {len(left_behind)} {thing}. This folder is copied into a "
        f"repository somebody else owns, so it holds {', '.join(FILENAMES)} and the files "
        f"{AGENTS_NAME} names, and nothing else:",
        width=76,
    ):
        print(f"  {line}")
    for name in left_behind:
        print(f"    {name}")


def record_left_behind(tree: Path, left_behind: list[str]) -> None:
    """Leave what this folder dropped where write_lock in scripts/build.py will look.

    A line printed by report() reaches the build log and nothing else. This
    folder is the one that lands in somebody else's repository, where nobody
    ever sees that log, so the loss also has to be on the record inside the
    folder itself, the same as a kind a harness cannot carry already is.
    Nothing here is content this folder ships: write_lock reads it back into
    this folder's own lock file and removes it before the folder is
    fingerprinted, so nothing written here ships and nothing here moves a
    `contents` fingerprint.

    Written only when there is something to say, the same as every other loss
    this build records only when it is real.
    """
    if not left_behind:
        return
    (tree / LEFT_BEHIND_NAME).write_text(json.dumps(left_behind, indent=2) + "\n")
