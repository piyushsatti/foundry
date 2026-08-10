"""Nothing in Foundry considered a symlink, and it leaked.

`fingerprint` in `scripts/resolve.py` walked with `rglob("*")` and `is_file()`,
which steps over a symlinked directory entirely and reads a symlinked file as
an ordinary one, hashing whatever currently sits at the far end of the link.
`shutil.copytree` then dereferences a symlinked directory and copies whatever
it currently points to. So a pin, defined as the fingerprint of a dependency's
source checkout, could stay byte-identical while what shipped changed
underneath it, and nothing anywhere said so.

The ruling: a symlink anywhere in a plugin's content, or in a dependency's
taken content, stops the build and names the path. Not a resolution policy,
not a rule about which links are safe to follow. A refusal. `SKIP_DIRS`,
`SKIP_SUFFIXES` and `SKIP_NAMES` are honoured exactly as `fingerprint` already
honours them, so a link inside `.venv` or `node_modules` is not a build error.

Run: python3 -m unittest discover -s tests   (from the repo root)
"""

from __future__ import annotations

import os

from tests.repos import RepoCase, build, make_repo, needs, resolve


class ASymlinkInThePluginsOwnContentIsRefused(RepoCase):
    """`fingerprint` is the chokepoint every build passes through: `resolve()`
    fingerprints the plugin's own root before `build()` copies anything."""

    def test_a_symlinked_file_is_refused_and_names_the_path(self):
        plugin = make_repo(
            self.workspace,
            "linked-file",
            files={"skills/greet/SKILL.md": "greet\n", "README.md": "notes\n"},
        )
        link = plugin / "skills" / "greet" / "pointer.md"
        os.symlink(plugin / "README.md", link)

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.fingerprint(plugin)

        message = str(refusal.exception)
        self.assertIn(str(link), message)
        self.assertIn("symlink", message)

    def test_a_symlinked_directory_is_refused_and_names_the_path(self):
        plugin = make_repo(self.workspace, "linked-dir", files={"skills/greet/SKILL.md": "greet\n"})
        outside = self.workspace / "outside"
        outside.mkdir()
        (outside / "extra.md").write_text("extra\n")
        link = plugin / "skills" / "linked"
        os.symlink(outside, link, target_is_directory=True)

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.fingerprint(plugin)

        message = str(refusal.exception)
        self.assertIn(str(link), message)
        self.assertIn("symlink", message)

    def test_the_whole_build_refuses_before_anything_is_copied(self):
        """`resolve()` runs before `copy_own_content`, so the author who would
        otherwise watch a pin stay put while the shipped folder moved
        underneath it never gets that far."""
        plugin = make_repo(self.workspace, "linked-build", files={"skills/greet/SKILL.md": "greet\n"})
        os.symlink(plugin / "skills" / "greet", plugin / "skills" / "alias", target_is_directory=True)

        with self.assertRaises(resolve.ResolveError) as refusal:
            build.build(plugin, self.destination())

        self.assertIn("symlink", str(refusal.exception))
        self.assertFalse(self.destination().exists(), "a refused build left a folder on disk")


class ASymlinkInsideADependencysTakenContentIsRefused(RepoCase):
    """Reproduces the leak from the audit: a symlinked directory sitting
    inside what a `take` entry asks for, whose target can change without ever
    moving the fingerprint the old code computed."""

    def test_the_full_build_refuses_rather_than_shipping_the_leak(self):
        library = make_repo(self.workspace, "library", files={"skills/audit/reference.md": "audit\n"})
        outside = self.workspace / "outside-the-dependency"
        outside.mkdir()
        (outside / "secret.md").write_text("before\n")
        link = library / "skills" / "audit" / "linked"
        os.symlink(outside, link, target_is_directory=True)

        # A pin is passed explicitly rather than computed from `fingerprint`,
        # because computing it here would hit the very refusal this test is
        # about before the build under test even starts.
        plugin = make_repo(
            self.workspace,
            "consumer",
            requires=[needs(library, take={"skills": ["audit"]}, pin="deadbeef0000")],
        )

        with self.assertRaises(resolve.ResolveError) as refusal:
            build.build(plugin, self.destination())

        message = str(refusal.exception)
        self.assertIn("symlink", message)
        self.assertIn(str(link), message)

    def test_copy_dependency_content_itself_refuses_the_symlinked_item(self):
        """The same refusal fingerprint() already raises on the dependency's
        own checkout, checked again at the point the copy actually happens,
        so a symlink inside one specific taken item cannot slip through any
        future path that reaches this function without going through
        resolve() first."""
        library = make_repo(self.workspace, "library", files={"skills/audit/reference.md": "audit\n"})
        outside = self.workspace / "outside"
        outside.mkdir()
        link = library / "skills" / "audit" / "linked"
        os.symlink(outside, link, target_is_directory=True)

        consumer = make_repo(
            self.workspace,
            "consumer",
            requires=[
                {
                    "id": "library",
                    "pin": "deadbeef0000",
                    "path": "../library",
                    "take": {"skills": ["audit"]},
                }
            ],
        )
        manifest = resolve.read_manifest(consumer)

        with self.assertRaises(build.BuildError) as refusal:
            build.copy_dependency_content(manifest, self.destination(), {})

        message = str(refusal.exception)
        self.assertIn("symlink", message)
        self.assertIn(str(link), message)


class ASymlinkUnderASkippedDirectoryIsNotRefused(RepoCase):
    """`.venv`, `node_modules` and the rest of `SKIP_DIRS` are already outside
    every fingerprint. A link inside one of them must stay outside this rule
    too, or an ordinary virtualenv would stop every build that has one."""

    def test_a_symlink_inside_dot_venv_does_not_fire_the_rule(self):
        plugin = make_repo(self.workspace, "has-a-venv", files={"skills/greet/SKILL.md": "greet\n"})
        venv_bin = plugin / ".venv" / "bin"
        venv_bin.mkdir(parents=True)
        os.symlink("/usr/bin/python3", venv_bin / "python3")

        digest = resolve.fingerprint(plugin)  # must not raise

        self.assertTrue(digest)

    def test_a_symlink_inside_node_modules_does_not_fire_the_rule(self):
        plugin = make_repo(self.workspace, "has-node-modules", files={"skills/greet/SKILL.md": "greet\n"})
        bin_dir = plugin / "node_modules" / ".bin"
        bin_dir.mkdir(parents=True)
        os.symlink("../some-package/cli.js", bin_dir / "some-tool")

        digest = resolve.fingerprint(plugin)  # must not raise

        self.assertTrue(digest)
