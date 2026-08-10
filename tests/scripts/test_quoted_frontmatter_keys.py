"""A YAML key matched by reading lines, with a parser sitting right next to it.

`strip_allowed_tools` in `scripts/emitters/__init__.py` matched
`line.split(":")[0].strip() == "allowed-tools"`. `declared_kinds` decides the
same fact by calling `frontmatter`, which parses real YAML. Write the key
quoted, ordinary valid YAML, and the two disagreed: the drop was recorded and
the field still shipped. `with_argument_hint` in
`scripts/emitters/skills_tree.py` had the identical bug for `arguments`.

These tests build a plugin holding a quoted key each way and read the shipped
file back through the real parser, `frontmatter`, rather than trusting the
line edit's own idea of what it did. The promise is not that the matcher
recognises every quoted form on sight, it is that the lock file never records
a drop, or a rename, that the shipped file does not actually carry.

Run: python3 -m unittest discover -s tests   (from the repo root)
"""

from __future__ import annotations

from tests.repos import RepoCase, build, make_repo

from emitters.contract import frontmatter  # noqa: E402  reachable once tests.repos has put scripts/ on the path


class AQuotedAllowedToolsKeyIsHandledCorrectly(RepoCase):
    def test_the_field_is_actually_gone_not_only_recorded_as_dropped(self):
        plugin = make_repo(
            self.workspace,
            "quoted-allowed-tools",
            files={
                "skills/greet/SKILL.md": (
                    '---\nname: greet\ndescription: Greet.\n"allowed-tools": Read\n---\n\nGreet.\n'
                ),
            },
            targets=["opencode"],
            degrade={"opencode": {"drop": ["allowed-tools"]}},
        )
        out = self.destination()

        answer = build.build(plugin, out)

        shipped = frontmatter(out / "skills" / "greet" / "SKILL.md")
        self.assertNotIn("allowed-tools", shipped)

        record = answer["targets"][0]
        dropped_kinds = {drop["kind"] for drop in record["dropped"]}
        self.assertIn("allowed-tools", dropped_kinds, "the drop the manifest waived was not recorded")


class AQuotedArgumentsKeyIsHandledCorrectly(RepoCase):
    def test_the_rename_actually_happens_not_only_the_visible_form(self):
        plugin = make_repo(
            self.workspace,
            "quoted-arguments",
            files={
                "commands/review.md": (
                    "---\ndescription: Review something.\n'arguments': \"[path]\"\n---\n\nReview.\n"
                ),
            },
            targets=["pi"],
        )
        out = self.destination()

        build.build(plugin, out)

        shipped = frontmatter(out / "prompts" / "review.md")
        self.assertNotIn("arguments", shipped)
        self.assertEqual(shipped.get("argument-hint"), "[path]")
