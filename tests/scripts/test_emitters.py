"""One source, one release, one folder per harness, and never a silent loss.

Two things are being guarded here and they pull in opposite directions. The
first is that a plugin which says nothing about harnesses still ships exactly
the bytes it shipped before harnesses existed, because every `contents`
fingerprint already recorded in a lock file is a promise that folder has not
moved. The second is that a plugin which does name harnesses gets one complete
folder each, and that anything a harness cannot carry either stops the build or
is written down twice, in that folder's lock file and in the release record.

So the fixture below is deliberately one plugin holding all six kinds. Reused
across both halves, it is the only way to assert that naming five more
harnesses changes nothing at all about the sixth.

Run: python3 -m unittest discover -s tests   (from the repo root)
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import types
import unittest.mock

from tests.repos import RUNNING_FOUNDRY, RepoCase, build, files_under, make_repo, resolve

import emitters  # noqa: E402  reachable once tests.repos has put scripts/ on the path
from emitters import COMMON_MOMENTS, Cannot, Capability, EmitError  # noqa: E402

LOCK_NAME = "foundry.lock.json"
RELEASE_NAME = "foundry.release.json"

ALL_TARGETS = ("agent-plugins", "claude-code", "codex", "instructions", "opencode", "pi")

SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"


# --------------------------------------------------------------- the fixture
# One plugin holding every one of the six kinds: a skill, an agent, a command,
# a hook, an MCP server, and `allowed-tools` inside the skill. Every harness
# below carries a different subset of it, which is what makes one fixture
# enough to check them all against each other.
SKILL_TEXT = """---
name: incident-review
description: Use when a production incident needs a written timeline.
allowed-tools: Read Grep
---

Read the alert history first, then the deploy log.
"""

AGENT_TEXT = """---
name: panelist
description: Reviews one change against one named concern.
---

You are one member of a review panel.
"""

COMMAND_TEXT = """---
name: review
description: Run the review panel over the working tree diff.
arguments: "[path]"
---

Collect the diff, then dispatch one panelist per concern.
"""

# The moment is `at` and not `on` because YAML 1.1 resolves a bare `on` to the
# boolean true, so a rule written the other way reaches Foundry keyed `true` and
# naming no moment. `run` is a path to a file inside the plugin, which is why
# the script below is part of the fixture: a rule pointing at nothing is refused.
HOOKS_TEXT = """- at: session-start
  run: hooks/announce.sh
"""

ANNOUNCE_TEXT = "#!/bin/sh\necho 'review panel loaded'\n"

MCP_TEXT = """{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "manifold": {
      "type": "stdio",
      "command": "manifold-mcp",
      "args": ["serve"]
    }
  }
}
"""

README_TEXT = "review-panel\n"

EVERY_KIND = {
    "README.md": README_TEXT,
    "skills/incident-review/SKILL.md": SKILL_TEXT,
    "agents/panelist.md": AGENT_TEXT,
    "commands/review.md": COMMAND_TEXT,
    "hooks/hooks.yaml": HOOKS_TEXT,
    "hooks/announce.sh": ANNOUNCE_TEXT,
    "mcp.json": MCP_TEXT,
}

METADATA = {
    "description": "A review panel that runs one reviewer per concern.",
    "author": {"name": "Review Panel Maintainers"},
    "homepage": "https://example.invalid/review-panel",
    "license": "Apache-2.0",
    "keywords": ["review", "incident"],
}

# What every emitter that writes a manifest describes the plugin as, in the
# order METADATA_KEYS fixes. Written out rather than derived from METADATA so
# that a change to either one has to be made twice on purpose.
DESCRIBED = {
    "name": "review-panel",
    "version": "1.4.2",
    "description": "A review panel that runs one reviewer per concern.",
    "author": {"name": "Review Panel Maintainers"},
    "homepage": "https://example.invalid/review-panel",
    "license": "Apache-2.0",
    "keywords": ["review", "incident"],
}

# Everything each harness cannot carry, waived so that the multi-target fixture
# builds. Claude Code is absent because it carries all six.
WAIVED = {
    "agent-plugins": {"drop": ["agents", "commands", "hooks", "allowed-tools"]},
    "codex": {"drop": ["agents", "commands", "hooks", "allowed-tools"]},
    "instructions": {"drop": ["agents", "hooks", "mcp", "allowed-tools"]},
    "opencode": {"drop": ["commands", "hooks", "mcp", "allowed-tools"]},
    "pi": {"drop": ["agents", "hooks", "mcp"]},
}


def read_json(path):
    return json.loads(path.read_text())


class Fixtures(RepoCase):
    """The one plugin, written either way: silent about harnesses, or naming six."""

    def silent_about_harnesses(self):
        return make_repo(
            self.workspace,
            "review-panel",
            version="1.4.2",
            metadata=METADATA,
            files=EVERY_KIND,
        )

    def naming_six_harnesses(self):
        return make_repo(
            self.workspace,
            "review-panel",
            version="1.4.2",
            metadata=METADATA,
            files=EVERY_KIND,
            provides={"skills": ["incident-review"], "commands": ["review.md"]},
            targets=list(ALL_TARGETS),
            degrade=WAIVED,
        )


class TheFolderThatAlreadyShips(Fixtures):
    """A manifest that never mentions harnesses gets what it always got.

    This is the compatibility gate and it is the most load-bearing test in the
    file. `contents` in a lock file is what a person compares a downloaded
    folder against, and the number below is not read back from the build: it is
    the sha256 of the bytes a Claude Code folder is meant to hold, written out
    by hand. So the assertion is that the build agrees with the specification of
    the folder, not that the build agrees with itself.
    """

    # sha256 over each shipped path and its bytes, sorted, NUL-separated, first
    # 12 characters: the eight files listed in SHIPPED below, being the plugin's
    # own content plus the three files Claude Code reads. foundry.lock.json is
    # outside it because `contents` is measured before the lock is written, so a
    # lock file is never inside its own fingerprint.
    #
    # This number moved once, when the two neutral files below started being
    # translated instead of shipped unread. It moved for every plugin declaring
    # an MCP server or a hook and for no other plugin, and what it used to cover
    # was two files Claude Code never opened.
    CONTENTS = "cb43209d0585"

    SHIPPED = [
        ".claude-plugin/plugin.json",
        ".mcp.json",
        "README.md",
        "agents/panelist.md",
        "commands/review.md",
        "foundry.lock.json",
        "hooks/announce.sh",
        "hooks/hooks.json",
        "skills/incident-review/SKILL.md",
    ]

    # What Claude Code opens, written out rather than read back from the build,
    # for the same reason CONTENTS is. `mcpServers` alone crosses over from the
    # portable file: Claude Code's format does not name `$schema`.
    MCP_TRANSLATED = """{
  "mcpServers": {
    "manifold": {
      "type": "stdio",
      "command": "manifold-mcp",
      "args": [
        "serve"
      ]
    }
  }
}
"""

    HOOKS_TRANSLATED = """{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\\"${CLAUDE_PLUGIN_ROOT}\\"/hooks/announce.sh"
          }
        ]
      }
    ]
  }
}
"""

    METADATA_TEXT = """{
  "name": "review-panel",
  "version": "1.4.2",
  "description": "A review panel that runs one reviewer per concern.",
  "author": {
    "name": "Review Panel Maintainers"
  },
  "homepage": "https://example.invalid/review-panel",
  "license": "Apache-2.0",
  "keywords": [
    "review",
    "incident"
  ]
}
"""

    def test_the_folder_at_out_is_the_plugin_and_holds_exactly_what_it_always_held(self):
        out = self.destination()

        self.ship(self.silent_about_harnesses(), out)

        self.assertEqual(sorted(files_under(out)), self.SHIPPED)
        self.assertFalse(
            (out / "claude-code").exists(),
            "a manifest naming no harness got a per-harness subdirectory",
        )
        self.assertFalse(
            (out / RELEASE_NAME).exists(),
            "a single folder got a release record, which only a release of several has",
        )
        self.assertEqual((out / ".claude-plugin/plugin.json").read_text(), self.METADATA_TEXT)

    def test_the_contents_fingerprint_is_the_one_every_recorded_lock_file_holds(self):
        out = self.destination()

        self.ship(self.silent_about_harnesses(), out)

        lock = read_json(out / LOCK_NAME)
        self.assertEqual(
            lock["contents"],
            self.CONTENTS,
            "the Claude Code folder moved, so every pin written against one stops matching",
        )
        self.assertNotIn(
            "target",
            lock,
            "a manifest that never mentioned targets got a lock file naming one",
        )
        self.assertNotIn("dropped", lock, "a manifest that never mentioned targets got a drops list")

    def test_a_rule_set_naming_only_the_original_four_moments_moves_no_byte_and_gets_no_rules_key(self):
        """The most important test in the batch. `hooks/hooks.yaml` above names
        only 'session-start', with no 'only' and no 'timeout' anywhere, which
        is the rule shape every plugin wrote before this change. Every
        `contents` fingerprint already recorded in a shipped lock file was
        measured on bytes produced by exactly that shape, so if this number
        moves, or a 'rules' key starts appearing where there used to be none,
        every one of those pins stops matching, silently, on somebody else's
        machine."""
        out = self.destination()

        self.ship(self.silent_about_harnesses(), out)

        lock = read_json(out / LOCK_NAME)
        self.assertEqual(
            lock["contents"],
            self.CONTENTS,
            "growing the moment vocabulary or adding 'only'/'timeout' moved bytes nobody asked to move",
        )
        self.assertNotIn(
            "rules",
            lock,
            "a rule set with no 'only' anywhere got a 'rules' key it never had before",
        )

    def test_the_two_files_claude_code_reads_are_written_and_the_neutral_ones_are_gone(self):
        """The folder held an MCP file and a hook file that Claude Code never opened.

        Both shipped at their neutral names, `claude plugin details` reported
        `MCP servers (0)` and `Hooks (0)`, and the install reported success. That
        is a silent drop, which the loss policy says cannot exist: a loss is
        either refused or written down under `degrade`, and this was neither.

        So the assertion is in two halves and both matter. The translated file is
        there, and the neutral one is not, because a folder that held both would
        ship a file nothing reads inside its own fingerprint.
        """
        out = self.destination()

        self.ship(self.silent_about_harnesses(), out)

        self.assertEqual((out / ".mcp.json").read_text(), self.MCP_TRANSLATED)
        self.assertEqual((out / "hooks/hooks.json").read_text(), self.HOOKS_TRANSLATED)
        self.assertFalse((out / "mcp.json").exists(), "the neutral MCP file shipped unread")
        self.assertFalse((out / "hooks/hooks.yaml").exists(), "the neutral hook file shipped unread")

    def test_the_hook_directory_keeps_the_scripts_its_rules_run(self):
        """Only the neutral declaration is removed, never the directory.

        `hooks/` is a content directory and the scripts a rule points at usually
        sit in it. Removing the directory would ship a hook file naming a
        command that is not there, which fails at the moment somebody needed it.
        """
        out = self.destination()

        self.ship(self.silent_about_harnesses(), out)

        self.assertEqual((out / "hooks/announce.sh").read_text(), ANNOUNCE_TEXT)

    def test_content_a_person_wrote_is_not_rewritten_on_the_way_into_the_folder(self):
        """Translation is for the files a harness reads, and nothing else.

        A skill, an agent and a command are prose somebody wrote. Reformatting
        one would land in the folder's `contents` fingerprint looking like a
        content change, so no emitter touches them.
        """
        plugin = self.silent_about_harnesses()
        out = self.destination()

        self.ship(plugin, out)

        for relative in ("skills/incident-review/SKILL.md", "agents/panelist.md", "commands/review.md"):
            with self.subTest(relative):
                self.assertEqual((out / relative).read_text(), (plugin / relative).read_text())
        self.assertIn("allowed-tools: Read Grep", (out / "skills/incident-review/SKILL.md").read_text())


class SeveralHarnessesFromOneSource(Fixtures):
    def test_every_named_harness_gets_a_complete_folder_holding_only_what_it_reads(self):
        out = self.destination()

        self.ship(self.naming_six_harnesses(), out)

        expected = {
            "agent-plugins": [
                "README.md",
                "foundry.lock.json",
                "mcp.json",
                "plugin.json",
                "skills/incident-review/SKILL.md",
            ],
            "claude-code": [
                ".claude-plugin/plugin.json",
                ".mcp.json",
                "README.md",
                "agents/panelist.md",
                "commands/review.md",
                "foundry.lock.json",
                "hooks/announce.sh",
                "hooks/hooks.json",
                "skills/incident-review/SKILL.md",
            ],
            "codex": [
                ".codex-plugin/plugin.json",
                "README.md",
                "foundry.lock.json",
                "mcp.json",
                "plugin.json",
                "skills/incident-review/SKILL.md",
            ],
            "instructions": [
                "AGENTS.md",
                "CLAUDE.md",
                "GEMINI.md",
                "commands/review.md",
                "foundry.lock.json",
                "skills/incident-review/SKILL.md",
            ],
            "opencode": [
                "README.md",
                "agents/panelist.md",
                "foundry.lock.json",
                "skills/incident-review/SKILL.md",
            ],
            "pi": [
                "README.md",
                "foundry.lock.json",
                "prompts/review.md",
                "skills/incident-review/SKILL.md",
            ],
        }
        for target, files in expected.items():
            with self.subTest(target):
                self.assertEqual(sorted(files_under(out / target)), files)

    def test_naming_five_more_harnesses_changes_nothing_about_the_claude_code_folder(self):
        """The whole point of the compatibility default, stated the other way.

        A plugin that adds harnesses is not asking for its existing folder to
        move, and nothing in the fork above it may reach the folder it already
        ships.
        """
        alone, together = self.destination("alone"), self.destination("together")

        self.ship(self.silent_about_harnesses(), alone)
        self.ship(self.naming_six_harnesses(), together)

        self.assertEqual(
            read_json(together / "claude-code" / LOCK_NAME)["contents"],
            read_json(alone / LOCK_NAME)["contents"],
        )
        self.assertEqual(
            (together / "claude-code/.claude-plugin/plugin.json").read_text(),
            (alone / ".claude-plugin/plugin.json").read_text(),
        )

    def test_the_release_record_names_every_harness_with_its_fingerprint_and_its_drops(self):
        out = self.destination()

        self.ship(self.naming_six_harnesses(), out)

        release = read_json(out / RELEASE_NAME)
        self.assertEqual(release["plugin"], "review-panel")
        self.assertEqual(release["version"], "1.4.2")
        self.assertEqual(release["foundry"], RUNNING_FOUNDRY)

        records = {record["target"]: record for record in release["targets"]}
        self.assertEqual(sorted(records), sorted(ALL_TARGETS))
        for target, record in records.items():
            with self.subTest(target):
                self.assertEqual(
                    record["contents"],
                    read_json(out / target / LOCK_NAME)["contents"],
                    "the release record and the folder's own lock file disagree",
                )
                self.assertEqual(
                    [drop["kind"] for drop in record["dropped"]],
                    WAIVED.get(target, {"drop": []})["drop"],
                )

        fingerprints = {record["contents"] for record in release["targets"]}
        self.assertEqual(
            len(fingerprints),
            len(ALL_TARGETS),
            "two harness folders share one fingerprint, so the record cannot tell them apart",
        )

    def test_the_same_source_built_twice_gives_the_same_folder_for_every_harness(self):
        plugin = self.naming_six_harnesses()
        first, second = self.destination("first"), self.destination("second")

        self.ship(plugin, first)
        self.ship(plugin, second)

        self.assertEqual(files_under(first), files_under(second))
        differing = [
            path
            for path in sorted(files_under(first))
            if (first / path).read_bytes() != (second / path).read_bytes()
        ]
        self.assertEqual(differing, [], f"two builds of one source differ: {differing}")

    def test_one_named_harness_still_writes_the_folder_at_out_itself(self):
        """The layout follows the count, so a marketplace listing keeps working.

        A listing can only exist for a plugin with one target, and it points at
        the folder rather than at a subdirectory of it.
        """
        plugin = make_repo(
            self.workspace,
            "solo",
            files={"skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n"},
            targets=["claude-code"],
        )
        out = self.destination()

        self.ship(plugin, out)

        self.assertTrue((out / ".claude-plugin/plugin.json").is_file())
        self.assertFalse((out / "claude-code").exists())
        self.assertFalse((out / RELEASE_NAME).exists())
        # Named, so it is on the record, unlike the manifest that stayed silent.
        self.assertEqual(read_json(out / LOCK_NAME)["target"], "claude-code")
        self.assertEqual(read_json(out / LOCK_NAME)["dropped"], [])


class WhatEachEmitterWrites(Fixtures):
    """The manifest path and its fields, against literal values rather than output.

    A manifest one directory off is a plugin no client finds at all, and a field
    of the wrong shape is a plugin the client rejects whole. Neither reports
    anything to the author, so both are checked here against what the harness
    documents rather than against whatever the emitter currently produces.
    """

    def setUp(self):
        super().setUp()
        self.out = self.destination()
        self.printed = self.ship(self.naming_six_harnesses(), self.out)

    def test_claude_code_writes_its_manifest_inside_the_dot_directory_it_reads(self):
        path = self.out / "claude-code/.claude-plugin/plugin.json"
        self.assertEqual(read_json(path), DESCRIBED)
        self.assertEqual(
            list(read_json(path)),
            list(DESCRIBED),
            "the field order moved, and this file's bytes are inside a fingerprint",
        )

    def test_the_portable_manifest_is_the_schema_first_and_then_the_metadata(self):
        path = self.out / "agent-plugins/plugin.json"
        self.assertEqual(read_json(path), {"$schema": SCHEMA, **DESCRIBED})
        self.assertEqual(
            list(read_json(path)),
            ["$schema", *DESCRIBED],
            "$schema is not the first field, and the schema is a closed object",
        )

    def test_codex_gets_the_portable_manifest_and_an_overlay_naming_where_things_are(self):
        """Codex 0.139.0 reads only the overlay, and only what the overlay points at.

        A component the overlay does not name is one Codex never looks for, so
        an mcp.json shipped without the line sits unread while the install
        reports success.
        """
        self.assertEqual(read_json(self.out / "codex/plugin.json"), {"$schema": SCHEMA, **DESCRIBED})
        self.assertEqual(
            read_json(self.out / "codex/.codex-plugin/plugin.json"),
            {**DESCRIBED, "skills": "./skills", "mcpServers": "./mcp.json"},
        )

    def test_the_overlay_names_a_component_only_when_the_folder_actually_holds_it(self):
        plugin = make_repo(
            self.workspace,
            "skills-only",
            version="0.2.0",
            files={"skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n"},
            targets=["codex"],
        )
        out = self.destination("skills-only")

        self.ship(plugin, out)

        self.assertEqual(
            read_json(out / ".codex-plugin/plugin.json"),
            {"name": "skills-only", "version": "0.2.0", "skills": "./skills"},
            "the overlay points at an mcp.json this folder does not hold",
        )

    def test_opencode_and_pi_get_no_manifest_of_any_kind(self):
        """Neither has a package format, so what they get is loose files.

        A manifest written for either one would be a file the harness does not
        read, sitting inside the folder's fingerprint with nothing to explain it.
        """
        for target in ("opencode", "pi"):
            for name in ("plugin.json", "package.json", ".claude-plugin", ".codex-plugin"):
                with self.subTest(f"{target}/{name}"):
                    self.assertFalse((self.out / target / name).exists())

    def test_pi_gets_its_commands_as_prompt_templates_under_the_name_pi_reads(self):
        self.assertFalse(
            (self.out / "pi/commands").exists(),
            "the neutral directory stayed behind, where Pi never looks",
        )
        self.assertEqual(
            (self.out / "pi/prompts/review.md").read_text(),
            COMMAND_TEXT.replace('arguments: "[path]"', 'argument-hint: "[path]"'),
        )

    def test_instructions_writes_one_file_of_prose_and_two_that_only_point_at_it(self):
        folder = self.out / "instructions"
        agents = (folder / "AGENTS.md").read_text()

        self.assertIn("### incident-review", agents)
        self.assertIn("Use when a production incident needs a written timeline.", agents)
        self.assertIn("Read `skills/incident-review/SKILL.md`.", agents)
        self.assertIn("Read `commands/review.md`.", agents)

        for name in ("CLAUDE.md", "GEMINI.md"):
            with self.subTest(name):
                self.assertTrue((folder / name).read_text().endswith("@AGENTS.md\n"))

        self.assertFalse(
            (folder / "README.md").exists(),
            "a file nothing names landed in a repository somebody else owns",
        )
        self.assertIn("instructions left behind 1 path", self.printed)
        self.assertIn("README.md", self.printed)


class ALossIsRefusedOrWrittenDown(RepoCase):
    """Two outcomes and no third, and Foundry never decides between them."""

    def printed_by(self, call) -> str:
        """What the command line prints, which is where a drop is announced.

        `build.build` writes the drop into the lock file; only `main` says it
        out loud, and the person watching the build is the last one who can
        notice a loss that was agreed to months ago.
        """
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            self.assertEqual(call(), 0)
        return captured.getvalue()

    def with_hooks(self, **manifest):
        return make_repo(
            self.workspace,
            "guarded",
            files={
                "skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n",
                "hooks/hooks.yaml": HOOKS_TEXT,
                "hooks/announce.sh": ANNOUNCE_TEXT,
            },
            **manifest,
        )

    def test_a_kind_a_harness_cannot_carry_stops_the_build_and_names_the_kind_and_the_harness(self):
        plugin = self.with_hooks(targets=["claude-code", "opencode"])

        with self.assertRaises(EmitError) as refusal:
            self.ship(plugin, self.destination())

        message = str(refusal.exception)
        self.assertIn("CANNOT SHIP THIS TO OPENCODE.", message)
        self.assertIn("hooks/hooks.yaml", message)
        self.assertIn("OpenCode has no declarative hook surface", message)
        self.assertIn(str(plugin / "foundry.plugin.yaml"), message)
        self.assertIn("degrade.opencode.drop: [hooks]", message)

    def test_hooks_are_refused_on_opencode_and_on_pi(self):
        """A hook is usually a guard, and a package that appears to guard and
        does not is worse than one that refuses to install."""
        for target in ("opencode", "pi"):
            with self.subTest(target):
                plugin = self.with_hooks(targets=[target])
                with self.assertRaises(EmitError) as refusal:
                    self.ship(plugin, self.destination(target))
                message = str(refusal.exception)
                self.assertIn(f"CANNOT SHIP THIS TO {target.upper()}.", message)
                self.assertIn("hooks/hooks.yaml", message)
                self.assertIn("no declarative hook surface", message)

    def test_an_mcp_server_is_refused_on_pi(self):
        """For many plugins the server is the whole product, and Pi has no
        surface for one, so the wrapper would install and do nothing."""
        plugin = make_repo(
            self.workspace,
            "server-plugin",
            files={
                "skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n",
                "mcp.json": MCP_TEXT,
            },
            targets=["pi"],
        )

        with self.assertRaises(EmitError) as refusal:
            self.ship(plugin, self.destination())

        message = str(refusal.exception)
        self.assertIn("CANNOT SHIP THIS TO PI.", message)
        self.assertIn("mcp/manifold", message)
        self.assertIn("Pi has no MCP surface", message)
        self.assertIn("degrade.pi.drop: [mcp]", message)

    def test_the_same_loss_written_down_drops_instead_and_lands_in_that_folders_lock_file(self):
        plugin = self.with_hooks(
            targets=["claude-code", "opencode"],
            degrade={"opencode": {"drop": ["hooks"]}},
        )
        out = self.destination()

        self.ship(plugin, out)

        self.assertFalse((out / "opencode/hooks").exists())
        self.assertTrue((out / "claude-code/hooks/hooks.json").is_file())
        self.assertEqual(
            read_json(out / "opencode" / LOCK_NAME)["dropped"],
            [{"kind": "hooks", "why": "OpenCode has no declarative hook surface"}],
        )
        self.assertEqual(read_json(out / "claude-code" / LOCK_NAME)["dropped"], [])

        records = {record["target"]: record for record in read_json(out / RELEASE_NAME)["targets"]}
        self.assertEqual([drop["kind"] for drop in records["opencode"]["dropped"]], ["hooks"])

    def test_a_recorded_drop_is_printed_at_build_time_as_well_as_written_down(self):
        """A loss agreed to months ago is still a loss shipping today, and the
        person watching the build is the last one who can notice."""
        plugin = self.with_hooks(
            targets=["claude-code", "opencode"],
            degrade={"opencode": {"drop": ["hooks"]}},
        )
        out = self.destination()
        argv = ["build.py", str(plugin), "--out", str(out)]

        with unittest.mock.patch.object(sys, "argv", argv):
            printed = self.printed_by(build.main)

        self.assertIn("dropped hooks from opencode", printed)
        self.assertIn("OpenCode has no declarative hook surface", printed)

    def test_when_every_named_harness_drops_everything_the_build_refuses(self):
        """Every folder in the release would be an empty wrapper, and a release
        of empty wrappers reports success."""
        plugin = make_repo(
            self.workspace,
            "hooks-only",
            files={"hooks/hooks.yaml": HOOKS_TEXT, "hooks/announce.sh": ANNOUNCE_TEXT},
            targets=["opencode", "pi"],
            degrade={"opencode": {"drop": ["hooks"]}, "pi": {"drop": ["hooks"]}},
        )
        out = self.destination()

        with self.assertRaises(EmitError) as refusal:
            self.ship(plugin, out)

        message = str(refusal.exception)
        self.assertIn("NOTHING WOULD SHIP.", message)
        self.assertIn("opencode", message)
        self.assertIn("pi", message)
        self.assertFalse(out.exists())

    def test_an_unknown_harness_name_is_refused_and_the_message_lists_what_foundry_emits(self):
        plugin = self.with_hooks(targets=["clod-code"])

        with self.assertRaises(EmitError) as refusal:
            self.ship(plugin, self.destination())

        message = str(refusal.exception)
        self.assertIn("NO SUCH TARGET: clod-code", message)
        for target in ALL_TARGETS:
            self.assertIn(target, message)

    def test_a_waiver_for_a_harness_that_is_not_built_is_refused_when_the_manifest_is_read(self):
        """A misspelled name here reads as a waiver that was written, and then
        the refusal it was meant to answer fires anyway with the waiver in view."""
        plugin = self.with_hooks(
            targets=["opencode"],
            degrade={"opencodde": {"drop": ["hooks"]}},
        )

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.read_manifest(plugin)

        message = str(refusal.exception)
        self.assertIn("degrade.opencodde", message)
        self.assertIn("opencode", message)

    def test_an_empty_targets_list_is_refused_when_the_manifest_is_read(self):
        plugin = self.with_hooks(targets=[])

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.read_manifest(plugin)

        self.assertIn("'targets' is empty", str(refusal.exception))


class AHookThatWouldNotFireIsRefused(RepoCase):
    """Every fault here reaches a user as a guard that is quietly not there.

    Claude Code reports none of them. An event name it does not know, a command
    that is not on disk, a key it never looked at: the hook does not fire, the
    plugin installs, and the install reports success. The person who can fix it
    is the author at build time, so all of it is refused here.
    """

    def with_rule(self, rule: str, *, script: bool = True):
        files = {
            "skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n",
            "hooks/hooks.yaml": rule,
        }
        if script:
            files["hooks/announce.sh"] = ANNOUNCE_TEXT
        return make_repo(self.workspace, "guarded", files=files, targets=["claude-code"])

    def refusal_for(self, rule: str, **kwargs) -> str:
        with self.assertRaises(EmitError) as refusal:
            self.ship(self.with_rule(rule, **kwargs), self.destination())
        return str(refusal.exception)

    def test_the_old_on_key_is_named_rather_than_reported_as_a_key_called_true(self):
        """YAML 1.1 resolves a bare `on` to the boolean true, in every reader.

        So the line never arrives as a key called 'on' and the rule it belongs
        to names no moment. Left generic, the message would say the rule holds a
        key called True and send the author looking for a typo they did not make.
        """
        message = self.refusal_for("- on: session-start\n  run: hooks/announce.sh\n")

        self.assertIn("names the moment with 'on'", message)
        self.assertIn("YAML 1.1 resolves a bare 'on' to the boolean true", message)
        self.assertIn("Rename the key to 'at'", message)

    def test_a_moment_outside_the_six_is_refused_and_the_six_are_listed(self):
        message = self.refusal_for("- at: mid-turn\n  run: hooks/announce.sh\n")

        self.assertIn("'mid-turn'", message)
        for moment in (
            "session-start",
            "before-tool",
            "after-tool",
            "turn-end",
            "before-compact",
            "session-end",
        ):
            self.assertIn(moment, message)

    def test_a_run_naming_a_file_the_plugin_does_not_hold_is_refused(self):
        message = self.refusal_for("- at: session-start\n  run: hooks/announce.sh\n", script=False)

        self.assertIn("'hooks/announce.sh', which this plugin does not hold", message)
        self.assertIn("'exclude'", message)

    def test_a_key_a_rule_does_not_name_is_refused_rather_than_ignored(self):
        message = self.refusal_for("- at: session-start\n  run: hooks/announce.sh\n  blocking: true\n")

        self.assertIn("'blocking'", message)
        self.assertIn("A hook rule names at, run, match, only, timeout and nothing else", message)

    def test_a_match_becomes_the_matcher_claude_code_reads(self):
        out = self.destination()

        self.ship(self.with_rule("- at: before-tool\n  match: Bash\n  run: hooks/announce.sh\n"), out)

        self.assertEqual(
            read_json(out / "hooks/hooks.json"),
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": '"${CLAUDE_PLUGIN_ROOT}"/hooks/announce.sh',
                                }
                            ],
                        }
                    ]
                }
            },
        )

    def test_turn_end_and_before_compact_translate_to_stop_and_precompact(self):
        """If this breaks, a plugin's turn-end or before-compact hook either
        stops firing on Claude Code, because the moment landed on no event at
        all, or fires under the wrong event name, which is the same silent
        loss as a moment outside the vocabulary altogether."""
        out = self.destination()

        self.ship(
            self.with_rule(
                "- at: turn-end\n  run: hooks/announce.sh\n- at: before-compact\n  run: hooks/announce.sh\n"
            ),
            out,
        )

        events = read_json(out / "hooks/hooks.json")["hooks"]
        self.assertIn("Stop", events)
        self.assertIn("PreCompact", events)

    def test_a_named_timeout_is_in_the_hook_entry_and_an_absent_one_leaves_no_key(self):
        """If this breaks, either a hook's timeout is silently dropped so a
        harness's own default governs it instead of the number the author
        wrote, or every hook carries a 'timeout' key even for a rule that
        never named one, moving every fingerprint that never asked for one."""
        out = self.destination()

        self.ship(
            self.with_rule(
                "- at: before-tool\n  run: hooks/announce.sh\n  timeout: 30\n"
                "- at: after-tool\n  run: hooks/announce.sh\n"
            ),
            out,
        )

        events = read_json(out / "hooks/hooks.json")["hooks"]
        self.assertEqual(events["PreToolUse"][0]["hooks"][0]["timeout"], 30)
        self.assertNotIn("timeout", events["PostToolUse"][0]["hooks"][0])

    def test_a_timeout_that_is_not_a_positive_whole_number_is_refused(self):
        """If this breaks, a plugin can declare a budget Claude Code cannot
        honor and the build ships it anyway. 'true' is included on purpose:
        Python says isinstance(True, int), so a check that only tests for
        int would silently accept a timeout of one and nobody would notice
        the author never wrote a number at all."""
        cases = {
            "zero": "0",
            "negative": "-1",
            "not a whole number": "1.5",
            "a boolean": "true",
            "not a number at all": "thirty",
        }
        for label, value in cases.items():
            with self.subTest(label):
                message = self.refusal_for(
                    f"- at: session-start\n  run: hooks/announce.sh\n  timeout: {value}\n"
                )
                self.assertIn("'timeout'", message)

    def test_only_naming_a_harness_outside_targets_is_refused(self):
        """If this breaks, a rule can name a harness nobody is building and
        the mistake never surfaces, the same fault a 'degrade' block naming
        an unbuilt harness already stops the build over."""
        message = self.refusal_for("- at: session-start\n  run: hooks/announce.sh\n  only: [pi]\n")

        self.assertIn("'pi'", message)
        self.assertIn("targets: claude-code", message)

    def test_a_rule_reserved_for_a_harness_that_carries_no_hooks_here_is_refused(self):
        """The name being in 'targets' is not enough for the rule to run anywhere.

        opencode has no hook surface, so a rule reserved for it is absent from
        the claude-code folder as a rule drop and absent from the opencode
        folder as a kind drop. Both losses are recorded, against two different
        harnesses, and each reads as ordinary. What they add up to is a guard
        that runs in no folder the build writes, and a green build saying so.
        """
        plugin = make_repo(
            self.workspace,
            "reserved",
            files={
                "skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n",
                "hooks/hooks.yaml": "- at: turn-end\n  run: hooks/announce.sh\n  only: [opencode]\n",
                "hooks/announce.sh": ANNOUNCE_TEXT,
            },
            targets=["claude-code", "opencode"],
            degrade={"opencode": {"drop": ["hooks"]}},
        )

        with self.assertRaises(EmitError) as refusal:
            self.ship(plugin, self.destination("reserved"))

        message = str(refusal.exception)
        self.assertIn("NO HARNESS WOULD RUN THIS HOOK", message)
        self.assertIn("'turn-end'", message)
        self.assertIn("is only for opencode", message)
        self.assertIn("Carrying hooks in this build: claude-code", message)


class ThePathVariablesAreClaudeCodesOwn(RepoCase):
    """The portable names reach a Claude Code user as literal text in a path.

    Agent Plugins reserves `${PLUGIN_ROOT}` and `${PLUGIN_DATA}` for the client
    to expand. Claude Code expands `${CLAUDE_PLUGIN_ROOT}` and
    `${CLAUDE_PLUGIN_DATA}` and knows nothing of the shorter pair, so a server
    copied through unchanged fails to start with a path nobody can read.
    """

    def test_both_are_renamed_everywhere_they_appear_in_the_mcp_file(self):
        plugin = make_repo(
            self.workspace,
            "server-plugin",
            files={
                "mcp.json": json.dumps(
                    {
                        "$schema": MCP_SCHEMA,
                        "mcpServers": {
                            "manifold": {
                                "type": "stdio",
                                "command": "${PLUGIN_ROOT}/servers/manifold",
                                "args": ["--config", "${PLUGIN_ROOT}/config.json"],
                                "env": {"CACHE": "${PLUGIN_DATA}/cache"},
                            }
                        },
                    },
                    indent=2,
                )
                + "\n"
            },
            targets=["claude-code"],
        )
        out = self.destination()

        self.ship(plugin, out)

        self.assertEqual(
            read_json(out / ".mcp.json")["mcpServers"]["manifold"],
            {
                "type": "stdio",
                "command": "${CLAUDE_PLUGIN_ROOT}/servers/manifold",
                "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
                "env": {"CACHE": "${CLAUDE_PLUGIN_DATA}/cache"},
            },
        )
        self.assertNotIn(
            "$schema",
            read_json(out / ".mcp.json"),
            "the portable schema line reached a file whose format does not name it",
        )


class AManifestNeverWritesOverOneTheAuthorAlreadyHas(RepoCase):
    """A plugin repository that holds its own root `plugin.json` gets a refusal.

    Every top-level file the manifest does not exclude is copied into the
    neutral tree, and that file is inside the fingerprint the plugin's own pin
    names. Without a check, the Agent Plugins emitter writes its manifest to the
    same path and the author's file is gone, with nothing printed, nothing
    refused and nothing in the lock file. That is the build picking a winner.

    Root `plugin.json` is the likeliest collision Foundry has: it is a common
    filename, and this is the one manifest that sits at the package root rather
    than inside a dot directory, which that emitter's own comment calls the easy
    thing to get wrong.

    Two other emitters already refuse exactly this. `instructions.py` has
    `refuse_to_overwrite_theirs` for AGENTS.md, CLAUDE.md and GEMINI.md, and
    `skills_tree.py` has `check_prompts_is_free` for `prompts/`. Both say the
    same thing: overwriting yours would swap what you wrote for something
    generated, and neither outcome is Foundry's to choose. `agent_plugins.emit`
    now runs `refuse_to_overwrite_theirs` before anything is written, naming the
    file, the manifest that declared it, and both ways forward: add the name to
    'exclude', or drop the harness from 'targets'.

    Claude Code is deliberately not asserted here. `.claude-plugin/plugin.json`
    has been overwritten since before the emitters existed, so refusing there
    changes what an existing plugin ships and belongs to its own change with its
    own before-and-after comparison.
    """

    HAND_WRITTEN = '{\n  "name": "hand-written",\n  "somethingOfMine": true\n}\n'

    def test_a_root_plugin_json_the_author_wrote_is_not_silently_replaced(self):
        for target in ("agent-plugins", "codex"):
            with self.subTest(target):
                plugin = make_repo(
                    self.workspace,
                    "owns-a-manifest",
                    files={
                        "skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n",
                        "plugin.json": self.HAND_WRITTEN,
                    },
                    targets=[target],
                )
                with self.assertRaises(EmitError) as refusal:
                    self.ship(plugin, self.destination(target))
                message = str(refusal.exception)
                self.assertIn("plugin.json", message)
                self.assertIn(str(plugin / "foundry.plugin.yaml"), message)
                self.assertIn("exclude", message)


class SkillsAreExactlyOneLevelDeep(RepoCase):
    """Some harnesses look one level down and some recurse.

    So a grouping directory ships intact on part of the list and hides every
    skill beneath it on the rest, with no error anywhere. The refusal is on the
    neutral tree, before any harness is considered, because the same package has
    to expose the same skills everywhere.
    """

    def nested(self, **manifest):
        return make_repo(
            self.workspace,
            "grouped",
            files={
                "skills/reviews/incident/SKILL.md": (
                    "---\nname: incident\ndescription: Review an incident.\n---\n\nRead the log.\n"
                )
            },
            **manifest,
        )

    def test_a_nested_skill_stops_the_build_whichever_harnesses_are_named(self):
        named = {
            "no targets key at all": {},
            "claude-code": {"targets": ["claude-code"]},
            "agent-plugins": {"targets": ["agent-plugins"]},
            "codex": {"targets": ["codex"]},
            "instructions": {"targets": ["instructions"]},
            "opencode": {"targets": ["opencode"]},
            "pi": {"targets": ["pi"]},
            "all six": {"targets": list(ALL_TARGETS), "degrade": WAIVED},
        }
        for label, manifest in named.items():
            with self.subTest(label):
                plugin = self.nested(**manifest)
                out = self.destination(label.replace(" ", "-"))
                with self.assertRaises(EmitError) as refusal:
                    self.ship(plugin, out)
                message = str(refusal.exception)
                self.assertIn("SKILL NESTED TOO DEEP", message)
                self.assertIn("skills/reviews/incident/SKILL.md", message)
                self.assertFalse(out.exists())


class ARefusedReleaseLeavesNothingBehind(RepoCase):
    """Half a release is worse than none: the folders that did appear look whole.

    So every harness is assessed before any folder is written, and a refusal
    partway through takes the scratch directory with it. The build that follows
    the fix has to be able to write to the same place.
    """

    def cannot_ship_to_pi(self, **extra):
        return make_repo(
            self.workspace,
            "server-plugin",
            files={
                "skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n",
                "mcp.json": MCP_TEXT,
            },
            targets=["claude-code", "pi"],
            **extra,
        )

    def test_no_output_folder_and_no_scratch_directory_survive_a_refusal(self):
        out = self.destination()

        with self.assertRaises(EmitError):
            self.ship(self.cannot_ship_to_pi(), out)

        self.assertFalse(out.exists(), "a refused release left a half-written folder on disk")
        self.assertEqual(
            sorted(entry.name for entry in out.parent.iterdir()),
            [],
            "a refused release left scratch beside the output folder",
        )

    def test_the_harness_that_would_have_worked_is_not_written_either(self):
        out = self.destination()

        with self.assertRaises(EmitError):
            self.ship(self.cannot_ship_to_pi(), out)

        self.assertFalse(
            (out / "claude-code").exists(),
            "one folder shipped while another was refused, so the release is half a release",
        )

    def test_a_harness_that_cannot_be_shipped_at_all_is_reported_before_any_folder_is_built(self):
        """Every harness is judged before the first one is written, not as its turn comes.

        Below, Codex would refuse the `sse` transport while it is writing its
        own folder, and Pi cannot carry an MCP server at all. Judging each
        harness at the moment it is built reports the Codex problem, sends the
        author to move the server to another transport, and only then says the
        release was impossible anyway because of Pi. Judging all of them first
        reports the loss that kills the release, which is the one worth knowing.
        """
        plugin = make_repo(
            self.workspace,
            "remote-server",
            files={
                "skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n",
                "mcp.json": MCP_TEXT.replace(
                    '"type": "stdio",\n      "command": "manifold-mcp",\n      "args": ["serve"]',
                    '"type": "sse",\n      "url": "https://example.invalid/mcp"',
                ),
            },
            targets=["codex", "pi"],
        )
        out = self.destination("remote-server")

        with self.assertRaises(EmitError) as refusal:
            self.ship(plugin, out)

        message = str(refusal.exception)
        self.assertIn("CANNOT SHIP THIS TO PI.", message)
        self.assertIn("Pi has no MCP surface", message)
        self.assertNotIn(
            "CANNOT SHIP THIS TO CODEX.",
            message,
            "a folder was being written before every harness had been judged",
        )
        self.assertFalse(out.exists())

    def test_a_release_that_fails_then_succeeds_into_the_same_out_actually_succeeds(self):
        out = self.destination()

        with self.assertRaises(EmitError):
            self.ship(self.cannot_ship_to_pi(), out)

        self.ship(self.cannot_ship_to_pi(degrade={"pi": {"drop": ["mcp"]}}), out)

        self.assertTrue((out / "claude-code/.mcp.json").is_file())
        self.assertFalse((out / "pi/mcp.json").exists())
        self.assertFalse((out / "pi/.mcp.json").exists())
        self.assertTrue((out / RELEASE_NAME).is_file())


class AnOnlyLimitedRuleIsADropNotARefusal(RepoCase):
    """`only` lets one rule reach one harness without giving up hooks
    everywhere else, which is the whole reason it exists rather than a
    `degrade` block: that would take every other rule down with it.

    Claude Code is the one harness Foundry emits today that expresses every
    moment, so there is no second hook-carrying harness in the registry to
    prove the policy against. This builds one: a synthetic capability,
    injected into `emitters.REGISTRY` and `sys.modules` for the length of
    each test, that carries hooks and expresses only the four moments every
    hook-carrying harness has in common. That is the shape a real second
    harness will have the day one is registered, so the policy is proven
    against it now rather than left untested until then.
    """

    MODULE_NAME = "synthetic_hooks"
    TARGET = "synthetic-hooks"

    def synthetic_module(self) -> types.ModuleType:
        module = types.ModuleType(f"emitters.{self.MODULE_NAME}")
        module.TARGETS = (self.TARGET,)
        module.CAPABILITIES = {
            self.TARGET: Capability(
                carries=("skills", "hooks"),
                cannot={
                    "agents": Cannot("this synthetic harness carries no agents surface"),
                    "commands": Cannot("this synthetic harness carries no commands surface"),
                    "mcp": Cannot("this synthetic harness carries no MCP surface"),
                    "allowed-tools": Cannot("this synthetic harness carries no allowed-tools surface"),
                },
                moments=COMMON_MOMENTS,
            )
        }
        module.emit = lambda target, manifest, tree: None
        return module

    def registered(self):
        """The two patches that make the synthetic harness reachable, together.

        `REGISTRY` is what `emitters.load` reads to find the module name, and
        `sys.modules` is what `importlib.import_module` returns without ever
        touching disk, since no file for this harness exists under `scripts/`.
        """
        return unittest.mock.patch.dict(
            emitters.REGISTRY, {self.TARGET: self.MODULE_NAME}
        ), unittest.mock.patch.dict(sys.modules, {f"emitters.{self.MODULE_NAME}": self.synthetic_module()})

    def with_two_hook_harnesses(self, rule: str):
        return make_repo(
            self.workspace,
            "guarded",
            files={
                "skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n",
                "hooks/hooks.yaml": rule,
                "hooks/announce.sh": ANNOUNCE_TEXT,
            },
            targets=["claude-code", self.TARGET],
        )

    def test_only_claude_code_is_a_recorded_drop_for_the_other_harness(self):
        """If this breaks, a rule meant for one harness either vanishes from
        the other's lock file with nothing to explain the gap, or it stops
        the whole build over a harness the rule was never meant to reach."""
        plugin = self.with_two_hook_harnesses(
            "- at: turn-end\n  run: hooks/announce.sh\n  only: [claude-code]\n"
        )
        out = self.destination()
        argv = ["build.py", str(plugin), "--out", str(out)]

        registry_patch, modules_patch = self.registered()
        with registry_patch, modules_patch:
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                with unittest.mock.patch.object(sys, "argv", argv):
                    self.assertEqual(build.main(), 0)
            printed = captured.getvalue()

        self.assertIn(f"dropped the hook at turn-end from {self.TARGET}", printed)
        self.assertIn("the rule is only for claude-code", printed)

        lock = read_json(out / self.TARGET / LOCK_NAME)
        self.assertEqual(
            lock["rules"],
            [{"at": "turn-end", "run": "hooks/announce.sh", "why": "the rule is only for claude-code"}],
        )
        self.assertTrue((out / "claude-code/hooks/hooks.json").is_file())

    def test_no_only_at_all_is_a_refusal_naming_both_ways_forward(self):
        """If this breaks, a rule with no 'only' reaches a harness with no
        event for it and simply never fires, instead of stopping the build
        the way every other hook that cannot fire already does."""
        plugin = self.with_two_hook_harnesses("- at: turn-end\n  run: hooks/announce.sh\n")
        out = self.destination()

        registry_patch, modules_patch = self.registered()
        with registry_patch, modules_patch:
            with self.assertRaises(EmitError) as refusal:
                self.ship(plugin, out)

        message = str(refusal.exception)
        self.assertIn(f"CANNOT SHIP THIS TO {self.TARGET.upper()}.", message)
        self.assertIn("turn-end", message)
        self.assertIn("drop that harness from 'targets'", message)
        self.assertIn("only: [<harness>]", message)
