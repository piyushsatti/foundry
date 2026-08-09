"""'exclude' takes globs, with negation, and a bare name stays anchored to the top level.

Companion to `tests/scripts/test_build.py`, kept separate because that file is
not this ruling's to add to. `tests/fixtures/negation/`, `tests/fixtures/precedence/`
and the other three fixtures under `tests/fixtures/` record the same shapes this
file tests, but their manifests are deliberately left on today's bare, flat
'exclude' entries: their whole value to `.github/checks/repos.py` is staying
byte-for-byte unchanged while the code under them changes. Every scenario a
future negation or precedence pattern would need is built fresh here instead,
against a throwaway repository `tests/repos.py` writes and discards.

Run: python3 -m unittest discover   (from the repo root)
"""

from __future__ import annotations

import json

from tests.repos import RepoCase, build, files_under, make_repo


class ABareNameStaysAnchoredToTheTopLevel(RepoCase):
    """The one place this diverges from '.gitignore', on purpose.

    Under real '.gitignore' semantics a bare name matches at any depth. Doing
    that here would silently take a nested path sharing a name with a
    top-level exclude, which is exactly the shape devtools, manifold and
    plan-orchestrator already ship. Reaching deeper needs '**/name' instead.
    """

    def test_a_bare_name_excludes_only_the_top_level_entry(self):
        plugin = make_repo(
            self.workspace,
            "solo",
            exclude=["tests"],
            provides={"skills": ["demo"]},
            files={
                "tests/top.md": "top\n",
                "skills/demo/SKILL.md": "demo\n",
                "skills/demo/tests/inner.md": "inner\n",
            },
        )
        out = self.destination()

        build.build(plugin, out)

        shipped = files_under(out)
        self.assertNotIn("tests/top.md", shipped, "the top-level tests/ shipped")
        self.assertIn(
            "skills/demo/tests/inner.md",
            shipped,
            "a bare name reached past the top level",
        )


class DoubleStarReachesAnyDepth(RepoCase):
    def test_double_star_slash_name_excludes_the_nested_copy_too(self):
        plugin = make_repo(
            self.workspace,
            "solo",
            exclude=["**/tests"],
            provides={"skills": ["demo"]},
            files={
                "tests/top.md": "top\n",
                "skills/demo/SKILL.md": "demo\n",
                "skills/demo/tests/inner.md": "inner\n",
            },
        )
        out = self.destination()

        build.build(plugin, out)

        shipped = files_under(out)
        self.assertNotIn("tests/top.md", shipped)
        self.assertNotIn("skills/demo/tests/inner.md", shipped, "'**/tests' did not reach the nested copy")
        self.assertIn("skills/demo/SKILL.md", shipped, "excluding tests took the skill's own file with it")


class NegationReinstatesOnePathInsideAnAlreadyExcludedDirectory(RepoCase):
    """The exact shape `tests/fixtures/negation/` records, built fresh here
    with the '!' entry that fixture's own manifest deliberately does not
    carry yet, so that fixture's baseline can stay proof that nothing about
    it moved.

    THIS IS THE REPRODUCE-FIRST CASE. Run this test against the code as it
    stands before the ruling lands and it fails: 'copy_own_content' walks the
    plugin root one level deep and drops any entry whose bare name is in the
    exclude set, so 'scripts' is dropped whole and a second entry that starts
    with '!' is just one more string that matches no top-level name, doing
    nothing at all.
    """

    def test_a_leading_bang_reincludes_one_file_an_earlier_entry_excluded(self):
        plugin = make_repo(
            self.workspace,
            "solo",
            exclude=["scripts", "!scripts/keep.md"],
            files={"scripts/keep.md": "keep\n", "scripts/drop.md": "drop\n"},
        )
        out = self.destination()

        build.build(plugin, out)

        shipped = files_under(out)
        self.assertIn("scripts/keep.md", shipped, "negation did not reach inside the excluded directory")
        self.assertNotIn("scripts/drop.md", shipped, "the rest of the excluded directory shipped too")


class OrderDecidesWhichOfTwoMatchingEntriesWins(RepoCase):
    """A later entry wins over an earlier one, '.gitignore' style.

    Both repositories below hold the exact same two entries and the exact
    same two files; the only difference is which entry is written last. That
    is the whole cost the ruling names, and this is the case that proves it.
    """

    def test_the_later_entry_wins_when_two_entries_both_match_one_path(self):
        forward = make_repo(
            self.workspace,
            "forward",
            exclude=["**/summary", "!reports/summary/final.md"],
            files={"reports/summary/final.md": "final\n", "reports/summary/draft.md": "draft\n"},
        )
        reversed_order = make_repo(
            self.workspace,
            "reversed",
            exclude=["!reports/summary/final.md", "**/summary"],
            files={"reports/summary/final.md": "final\n", "reports/summary/draft.md": "draft\n"},
        )
        forward_out, reversed_out = self.destination("forward"), self.destination("reversed")

        build.build(forward, forward_out)
        build.build(reversed_order, reversed_out)

        forward_shipped = files_under(forward_out)
        reversed_shipped = files_under(reversed_out)

        self.assertIn("reports/summary/final.md", forward_shipped, "the negation written last did not win")
        self.assertNotIn("reports/summary/draft.md", forward_shipped)

        self.assertNotIn(
            "reports/summary/final.md",
            reversed_shipped,
            "writing the same two entries in the opposite order did not change which one wins",
        )
        self.assertNotIn("reports/summary/draft.md", reversed_shipped)


class DoubleStarSegmentRequiresASlashBoundaryOnBothSides(RepoCase):
    """'skills/**/tests' must not match 'skillset/tests'.

    The stitching used to replace '/\\*\\*/' with a group that had no mandatory
    slash after the fixed segment on its left, so any name merely starting
    with 'skills' and ending in '/tests' matched too, regardless of what came
    between. That is a silent drop: 'skillset/tests/should_keep.md' has
    nothing to do with the 'skills' directory this entry was written against,
    and it shipped missing anyway.
    """

    def test_a_double_star_segment_does_not_eat_the_boundary_slash(self):
        plugin = make_repo(
            self.workspace,
            "solo",
            exclude=["skills/**/tests"],
            provides={"skills": ["demo"]},
            files={
                "skills/demo/SKILL.md": "demo\n",
                "skills/demo/tests/inner.md": "inner\n",
                "skillset/tests/should_keep.md": "keep\n",
            },
        )
        out = self.destination()

        build.build(plugin, out)

        shipped = files_under(out)
        self.assertNotIn(
            "skills/demo/tests/inner.md", shipped, "'skills/**/tests' did not reach the nested copy it names"
        )
        self.assertIn(
            "skillset/tests/should_keep.md",
            shipped,
            "'skills/**/tests' reached across the 'skills'/'skillset' boundary and silently dropped a file "
            "the entry was never written to match",
        )

    def test_a_leading_double_star_still_matches_the_bare_name(self):
        plugin = make_repo(
            self.workspace,
            "solo",
            exclude=["**/tests"],
            files={"tests/top.md": "top\n"},
        )
        out = self.destination()

        build.build(plugin, out)

        self.assertNotIn("tests/top.md", files_under(out), "'**/tests' stopped matching the bare name")


class ATrailingSlashExcludesTheDirectory(RepoCase):
    """A trailing slash is how '.gitignore' says 'this name is a directory',
    and plugin authors will write it.

    Splitting 'scripts/' on '/' the naive way leaves a dangling empty final
    segment, which used to compile to a pattern that can never match
    anything at all: not the directory, not a direct child, not something
    nested inside it. The file shipped, and the build's own report called
    the entry unused, which was false in both directions.
    """

    def test_a_trailing_slash_excludes_the_directory_and_everything_inside_it(self):
        plugin = make_repo(
            self.workspace,
            "solo",
            exclude=["scripts/"],
            files={"scripts/build.py": "build\n", "scripts/sub/deep.py": "deep\n", "README.md": "solo\n"},
        )
        out = self.destination()

        printed = self.ship(plugin, out)

        shipped = files_under(out)
        self.assertNotIn("scripts/build.py", shipped, "a trailing slash did not exclude a direct child")
        self.assertNotIn("scripts/sub/deep.py", shipped, "a trailing slash did not exclude a nested file")
        self.assertIn("README.md", shipped)
        self.assertNotIn(
            "matched nothing",
            printed,
            "an entry that excluded two files was reported as having matched nothing",
        )


class BracketNegationExcludesEverythingExceptTheNamedCharacter(RepoCase):
    """Glob syntax writes a negated class as '[!t]'; regex writes it as
    '[^t]', where '!' is only a literal character. Copying the bracket
    straight into the regex kept the class syntactically valid while
    flipping what it meant: '*.[!t]md' excluded exactly the file it was
    written to keep, and let through exactly the one it was written to drop.
    """

    def test_a_leading_bang_in_a_bracket_class_negates_rather_than_matches_literally(self):
        plugin = make_repo(
            self.workspace,
            "solo",
            exclude=["*.[!t]md"],
            files={"notes.xmd": "x\n", "notes.tmd": "t\n"},
        )
        out = self.destination()

        build.build(plugin, out)

        shipped = files_under(out)
        self.assertNotIn(
            "notes.xmd", shipped, "'[!t]' did not negate: a character other than 't' was not excluded"
        )
        self.assertIn("notes.tmd", shipped, "'[!t]' excluded the one character it was written to keep")


class AnEntryMatchingNothingIsPrintedNotRefused(RepoCase):
    """Refusing this would refuse the template's own manifest, which excludes
    'notes': the template does not have a 'notes' directory, and its
    'degrade' blocks are inert in the same way, on purpose.
    """

    def test_an_exclude_entry_matching_nothing_is_printed_and_the_build_stays_green(self):
        plugin = make_repo(
            self.workspace,
            "solo",
            exclude=["notes", "tests"],
            files={"tests/top.md": "top\n"},
        )
        out = self.destination()

        printed = self.ship(plugin, out)

        self.assertIn("notes", printed, "an exclude entry matching nothing was not printed")
        self.assertIn("matched nothing", printed)
        self.assertNotIn(
            "'tests', which matched nothing",
            printed,
            "an entry that did match something was reported as unused too",
        )

    def test_an_unused_entry_does_not_stop_the_build(self):
        plugin = make_repo(self.workspace, "solo", exclude=["notes"], files={"README.md": "solo\n"})
        out = self.destination()

        build.build(plugin, out)

        self.assertTrue((out / "README.md").is_file(), "an unused exclude entry stopped the build")

    def test_an_unused_entry_does_not_appear_in_the_lock_file(self):
        """Printed at build time, and nowhere else: the lock file is a record
        of what shipped, not a second copy of the manifest's own declarations.
        """
        plugin = make_repo(self.workspace, "solo", exclude=["notes"], files={"README.md": "solo\n"})
        out = self.destination()

        build.build(plugin, out)

        lock = json.loads((out / "foundry.lock.json").read_text())
        self.assertNotIn("unused_exclude", lock, "a build-time report leaked into the shipped lock file")
        self.assertNotIn("exclude", lock, "the manifest's own declarations leaked into the lock file")
