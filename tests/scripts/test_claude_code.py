"""Claude Code refuses to overwrite a file the author already wrote.

`emit` in `scripts/emitters/claude_code.py` used to write two paths with no
guard at all: `.claude-plugin/plugin.json` on every build, and
`hooks/hooks.json` whenever the plugin also shipped a neutral
`hooks/hooks.yaml`. `.claude` sits in `NEVER_SHIP`, but `.claude-plugin` is a
plugin's own directory name and is not, so a plugin repository that already
holds either file had it silently replaced by a generated one: no refusal,
nothing printed, nothing in the lock file. That is the build picking a winner,
which the loss policy this repository is built around says never happens.

Run: python3 -m unittest discover -s tests   (from the repo root)
"""

from __future__ import annotations

from tests.repos import RepoCase, make_repo

from emitters import EmitError

SKILL_TEXT = "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n"
ANNOUNCE_TEXT = "#!/bin/sh\necho 'review panel loaded'\n"
HOOKS_TEXT = "- at: session-start\n  run: hooks/announce.sh\n"

HAND_WRITTEN_MANIFEST = '{\n  "name": "hand-written",\n  "somethingOfMine": true\n}\n'
HAND_WRITTEN_HOOKS = '{\n  "hooks": {\n    "somethingOfMine": true\n  }\n}\n'


class ClaudeCodeRefusesToOverwriteAFileTheAuthorWrote(RepoCase):
    """The one code defect the audit found on the minimum support channel.

    Two other emitters already carry `refuse_to_overwrite_theirs`, for their
    own manifests: `agent_plugins.py` and `instructions.py`. This is the same
    principle applied to Claude Code's own two unguarded writes, with the two
    halves checked differently because they are not the same shape: the
    manifest write is unconditional, and the hooks write only happens at all
    when the plugin also ships the neutral `hooks/hooks.yaml` Foundry
    translates.
    """

    def owning_a_manifest(self):
        return make_repo(
            self.workspace,
            "owns-a-manifest",
            files={
                "skills/greet/SKILL.md": SKILL_TEXT,
                ".claude-plugin/plugin.json": HAND_WRITTEN_MANIFEST,
            },
            targets=["claude-code"],
        )

    def owning_both_hook_files(self):
        return make_repo(
            self.workspace,
            "owns-a-hooks-file",
            files={
                "skills/greet/SKILL.md": SKILL_TEXT,
                "hooks/hooks.yaml": HOOKS_TEXT,
                "hooks/announce.sh": ANNOUNCE_TEXT,
                "hooks/hooks.json": HAND_WRITTEN_HOOKS,
            },
            targets=["claude-code"],
        )

    # --------------------------------------------------------------- refused
    def test_a_claude_plugin_manifest_the_author_wrote_is_not_silently_replaced(self):
        """Reproduces the defect: today this build succeeds and the author's
        file is gone with nothing said. `write_json` in `emit` has no guard,
        so the generated manifest simply lands on top of theirs."""
        plugin = self.owning_a_manifest()
        out = self.destination()

        with self.assertRaises(EmitError) as refusal:
            self.ship(plugin, out)

        message = str(refusal.exception)
        self.assertIn("CANNOT SHIP THIS TO CLAUDE-CODE.", message)
        self.assertIn(".claude-plugin/plugin.json", message)
        self.assertIn(str(plugin / "foundry.plugin.yaml"), message)
        self.assertIn("exclude", message)
        self.assertIn("drop claude-code from 'targets'", message)
        self.assertFalse(out.exists(), "a refused build left a half-written folder on disk")

    def test_claude_codes_own_hooks_json_is_not_silently_replaced_when_hooks_yaml_is_also_shipped(self):
        """Reproduces the defect: today this build succeeds, `translate_hooks`
        writes straight over the author's `hooks/hooks.json`, and the folder
        that ships holds the generated file with no trace of theirs."""
        plugin = self.owning_both_hook_files()
        out = self.destination()

        with self.assertRaises(EmitError) as refusal:
            self.ship(plugin, out)

        message = str(refusal.exception)
        self.assertIn("CANNOT SHIP THIS TO CLAUDE-CODE.", message)
        self.assertIn("hooks/hooks.json", message)
        self.assertIn(str(plugin / "foundry.plugin.yaml"), message)
        self.assertIn("exclude", message)
        self.assertFalse(out.exists(), "a refused build left a half-written folder on disk")

    def test_both_at_once_names_both_files_in_one_refusal(self):
        plugin = make_repo(
            self.workspace,
            "owns-both",
            files={
                "skills/greet/SKILL.md": SKILL_TEXT,
                ".claude-plugin/plugin.json": HAND_WRITTEN_MANIFEST,
                "hooks/hooks.yaml": HOOKS_TEXT,
                "hooks/announce.sh": ANNOUNCE_TEXT,
                "hooks/hooks.json": HAND_WRITTEN_HOOKS,
            },
            targets=["claude-code"],
        )
        out = self.destination()

        with self.assertRaises(EmitError) as refusal:
            self.ship(plugin, out)

        message = str(refusal.exception)
        self.assertIn(".claude-plugin/plugin.json", message)
        self.assertIn("hooks/hooks.json", message)
        self.assertIn("Each name above is", message)

    # -------------------------------------------------------- not over-refused
    def test_a_hand_written_hooks_json_with_no_neutral_hooks_yaml_ships_untouched(self):
        """The correction to the audit's framing. `translate_hooks` never runs
        at all when there is no neutral `hooks/hooks.yaml`, so a plugin that
        hand-writes `hooks/hooks.json` for Claude Code and nothing else is not
        a collision: it is just the file Claude Code reads, and it has to
        reach the folder exactly as the author wrote it."""
        plugin = make_repo(
            self.workspace,
            "hand-writes-hooks-only",
            files={
                "skills/greet/SKILL.md": SKILL_TEXT,
                "hooks/hooks.json": HAND_WRITTEN_HOOKS,
            },
            targets=["claude-code"],
        )
        out = self.destination()

        self.ship(plugin, out)

        self.assertEqual((out / "hooks/hooks.json").read_text(), HAND_WRITTEN_HOOKS)

    def test_an_empty_hooks_yaml_alongside_a_hand_written_hooks_json_is_not_a_collision(self):
        """The false positive the audit found: an empty `hooks/hooks.yaml`
        holds no rules, so `translate_hooks` never writes to `hooks/hooks.json`
        for any target, the same as if the neutral file were not there at all.
        Refusing here would stop a build that was never going to overwrite
        anything."""
        plugin = make_repo(
            self.workspace,
            "empty-hooks-yaml",
            files={
                "skills/greet/SKILL.md": SKILL_TEXT,
                "hooks/hooks.yaml": "[]\n",
                "hooks/hooks.json": HAND_WRITTEN_HOOKS,
            },
            targets=["claude-code"],
        )
        out = self.destination()

        self.ship(plugin, out)

        self.assertEqual((out / "hooks/hooks.json").read_text(), HAND_WRITTEN_HOOKS)

    def test_a_plugin_holding_neither_file_builds_exactly_as_before(self):
        """Nothing in play holds either file today, across all eight
        repositories and the template, so this refuses nothing today."""
        plugin = make_repo(
            self.workspace,
            "holds-neither",
            files={
                "skills/greet/SKILL.md": SKILL_TEXT,
                "hooks/hooks.yaml": HOOKS_TEXT,
                "hooks/announce.sh": ANNOUNCE_TEXT,
            },
            targets=["claude-code"],
        )
        out = self.destination()

        self.ship(plugin, out)

        self.assertTrue((out / ".claude-plugin/plugin.json").is_file())
        self.assertTrue((out / "hooks/hooks.json").is_file())

    def test_fixing_it_means_excluding_the_name_and_the_build_goes_back_to_green(self):
        """The way forward the refusal itself names, proven rather than asserted."""
        plugin = make_repo(
            self.workspace,
            "owns-a-manifest-excluded",
            files={
                "skills/greet/SKILL.md": SKILL_TEXT,
                ".claude-plugin/plugin.json": HAND_WRITTEN_MANIFEST,
            },
            exclude=[".claude-plugin"],
            targets=["claude-code"],
        )
        out = self.destination()

        self.ship(plugin, out)

        self.assertNotEqual((out / ".claude-plugin/plugin.json").read_text(), HAND_WRITTEN_MANIFEST)
