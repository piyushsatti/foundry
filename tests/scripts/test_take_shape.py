"""A `take` value written as a plain string is read one character at a time.

`take: {skills: audit}` meant one skill, but Python reads a string exactly
like any other sequence, so `check_take_entry` in `scripts/build.py` walked it
one letter at a time and refused the first of them: a build reporting a
missing skill named after the first letter of the intended name, sending its
author to fix something that was never the problem. `read_take` in
`scripts/resolve.py` refuses the shape itself, before a single item is looked
up, so the message names the actual mistake.

Run: python3 -m unittest discover -s tests   (from the repo root)
"""

from __future__ import annotations

from tests.repos import RepoCase, make_repo, needs, resolve


class ATakeWrittenAsAStringIsRefusedForItsShape(RepoCase):
    def test_the_refusal_names_the_shape_not_a_missing_one_letter_skill(self):
        library = make_repo(self.workspace, "library", files={"skills/audit/SKILL.md": "audit\n"})
        plugin = make_repo(
            self.workspace,
            "consumer",
            requires=[needs(library, take={"skills": "audit"})],
        )

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.read_manifest(plugin)

        message = str(refusal.exception)
        self.assertIn("take.skills", message)
        self.assertIn("list", message)
        self.assertNotIn(
            "has no skills/a",
            message,
            "blamed a one-letter skill instead of naming the shape mistake",
        )

    def test_a_take_written_as_a_list_is_unaffected(self):
        """The ordinary shape keeps working: this refusal only ever fires on
        the mistake it exists for."""
        library = make_repo(self.workspace, "library", files={"skills/audit/SKILL.md": "audit\n"})
        plugin = make_repo(
            self.workspace,
            "consumer",
            requires=[needs(library, take={"skills": ["audit"]})],
        )

        manifest = resolve.read_manifest(plugin)

        self.assertEqual(manifest["dependencies"][0]["take"], {"skills": ["audit"]})

    def test_take_itself_written_as_a_string_is_also_refused(self):
        """One level up from the reported bug: `take` itself has to be a map,
        not a bare value, and the same refusal has to catch that shape too."""
        library = make_repo(self.workspace, "library", files={"skills/audit/SKILL.md": "audit\n"})
        plugin = make_repo(
            self.workspace,
            "consumer",
            requires=[needs(library, take={"skills": ["audit"]})],
        )
        # Overwrite the dependency's 'take' with a bare string after the fact,
        # rather than teaching make_repo a shape it exists to catch.
        import yaml

        manifest_path = plugin / resolve.MANIFEST_NAME
        raw = yaml.safe_load(manifest_path.read_text())
        raw["requires"]["plugins"][0]["take"] = "audit"
        manifest_path.write_text(yaml.safe_dump(raw, sort_keys=False))

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.read_manifest(plugin)

        self.assertIn("take", str(refusal.exception))
