"""A release Foundry already wrote is not source, and was being treated as source.

Left in the checkout and built around, a previous output directory was copied
into every shipped folder and hashed into every fingerprint. Reproduced from an
author's chair: the same plugin built to `dist`, then built somewhere else, put
a whole previous release inside the Claude Code folder, seven lock files deep,
and moved five of the six `contents` values. `.github/checks/shipped.py` passed
that build.

Half of this was already written down, in `TODO.md` under "A build's own output
sits inside the fingerprint", and that half is about the pin. The other half,
that the same directory is also copied into what ships, was stated nowhere.

The ruling: a directory inside a plugin's source tree that is a built release
stops the build and names the path. Recognised by content and never by name,
because `--out` takes any path and `dist` is only a convention in a README,
while `foundry.lock.json` and `foundry.release.json` are files only Foundry
writes. The build's own destination is exempt, matched by resolved path,
because `--out dist` twice is the command the template hands everybody.

`exclude` is deliberately not a way out. It decides what ships and never
reaches the fingerprint, so excluding a stale release would fix what ships,
leave the pin still wrong, and read like a complete fix.

Run: python3 -m unittest discover -s tests   (from the repo root)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from tests.repos import RepoCase, build, make_repo, needs, resolve

CHECKS_DIR = Path(__file__).resolve().parents[2] / ".github" / "checks"
if str(CHECKS_DIR) not in sys.path:
    sys.path.insert(0, str(CHECKS_DIR))

import shipped  # noqa: E402
from report import Report  # noqa: E402

CONTENT = {"skills/greet/SKILL.md": "greet\n"}
SKILL = {"skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n"}


def plant_release(directory, *, several: bool = False) -> None:
    """A directory shaped like something Foundry wrote, without running a build.

    Used where the test is about detection rather than about the build, so the
    tree under test says exactly what it means and nothing else is in it.
    """
    directory.mkdir(parents=True, exist_ok=True)
    if several:
        (directory / resolve.RELEASE_NAME).write_text(json.dumps({"folders": {}}) + "\n")
        folder = directory / "claude-code"
        folder.mkdir()
        (folder / resolve.LOCK_NAME).write_text(json.dumps({"contents": "0" * 12}) + "\n")
        return
    (directory / resolve.LOCK_NAME).write_text(json.dumps({"contents": "0" * 12}) + "\n")


class AReleaseLeftInTheCheckoutStopsTheBuild(RepoCase):
    """The reported bug. The first build is fine; the second one, pointed
    anywhere else, met the first one's output as ordinary content."""

    def test_building_somewhere_else_refuses_and_names_the_earlier_release(self):
        plugin = make_repo(self.workspace, "built-once", files=CONTENT)
        build.build(plugin, plugin / "dist")

        with self.assertRaises(resolve.ResolveError) as refusal:
            build.build(plugin, plugin / "out2")

        message = str(refusal.exception)
        self.assertIn(str(plugin / "dist"), message)
        self.assertIn(resolve.LOCK_NAME, message)

    def test_the_refused_build_leaves_nothing_on_disk(self):
        plugin = make_repo(self.workspace, "no-residue", files=CONTENT)
        build.build(plugin, plugin / "dist")

        with self.assertRaises(resolve.ResolveError):
            build.build(plugin, plugin / "out2")

        self.assertFalse((plugin / "out2").exists(), "a refused build left a folder on disk")

    def test_the_refusal_names_a_way_out_and_rules_the_wrong_one_out(self):
        """A refusal with no next step is a bug. `exclude` is the next step an
        author would reach for and it does not work: it governs what ships and
        never reaches the fingerprint, so it would leave the pin still wrong
        while looking like a fix. The message has to say so rather than stay
        silent about it."""
        plugin = make_repo(self.workspace, "way-out", files=CONTENT)
        build.build(plugin, plugin / "dist")

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.fingerprint(plugin)

        message = str(refusal.exception)
        self.assertIn(f"Delete {plugin / 'dist'}", message)
        self.assertIn("--out somewhere outside this plugin", message)
        self.assertIn("'exclude' is not a way out", message)


class TheBuildsOwnDestinationIsExempt(RepoCase):
    """`--out dist` twice is the command the template's README gives everybody
    and CI asserts it. The exemption is by resolved path, not by name."""

    def test_building_into_the_same_place_twice_still_works(self):
        plugin = make_repo(self.workspace, "twice", files=CONTENT)
        build.build(plugin, plugin / "dist")

        answer = build.build(plugin, plugin / "dist")  # must not raise

        self.assertTrue(answer)
        self.assertFalse((plugin / "dist" / "dist").exists(), "a release shipped inside the next one")

    def test_a_destination_below_the_plugin_root_is_exempt_too(self):
        plugin = make_repo(self.workspace, "nested-out", files=CONTENT)
        build.build(plugin, plugin / "build" / "dist")

        answer = build.build(plugin, plugin / "build" / "dist")  # must not raise

        self.assertTrue(answer)

    def test_the_pin_does_not_move_when_a_build_went_into_the_tree(self):
        """The half already logged in TODO.md. The exempt directory is left out
        of the digest, not merely allowed past the refusal: hashing it would
        leave the same source pinning differently once it had been built."""
        plugin = make_repo(self.workspace, "pin-holds", files=CONTENT)
        clean = resolve.fingerprint(plugin)
        build.build(plugin, plugin / "dist")

        after = resolve.fingerprint(plugin, exempt=(plugin / "dist",))

        self.assertEqual(clean, after, "the pin moved because the checkout had been built into")

    def test_reading_a_pin_off_a_built_checkout_refuses_rather_than_answering(self):
        """Nothing exempts the directory when nobody names it, which is what a
        consumer reading a pin does. The old code answered with a different
        number and said nothing."""
        plugin = make_repo(self.workspace, "dirty-pin", files=CONTENT)
        build.build(plugin, plugin / "dist")

        with self.assertRaises(resolve.ResolveError):
            resolve.fingerprint(plugin)


class AReleaseIsRecognisedByWhatFoundryWrote(RepoCase):
    """Both names, at any depth. `--out` takes any path, so the name of the
    directory says nothing and the files inside it say everything."""

    def test_a_release_of_several_folders_is_named_at_its_top(self):
        """A multi-harness release carries the record at its top and a lock
        file one level down in each folder. Naming the child would send an
        author to delete one folder out of six."""
        plugin = make_repo(self.workspace, "several", files=CONTENT)
        plant_release(plugin / "dist", several=True)

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.fingerprint(plugin)

        message = str(refusal.exception)
        self.assertIn(str(plugin / "dist"), message)
        self.assertNotIn(str(plugin / "dist" / "claude-code"), message)

    def test_a_release_under_a_name_no_readme_suggests_is_still_found(self):
        plugin = make_repo(self.workspace, "odd-name", files=CONTENT)
        plant_release(plugin / "shipped-yesterday")

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.fingerprint(plugin)

        self.assertIn(str(plugin / "shipped-yesterday"), message := str(refusal.exception))
        self.assertIn(resolve.LOCK_NAME, message)

    def test_a_release_nested_below_the_top_level_is_still_found(self):
        plugin = make_repo(self.workspace, "deep", files=CONTENT)
        plant_release(plugin / "build" / "dist")

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.fingerprint(plugin)

        self.assertIn(str(plugin / "build" / "dist"), str(refusal.exception))


class TheExemptionReachesOneDirectoryAndOneRoot(RepoCase):
    """An exemption that stopped the walk, or that reached a dependency, would
    be a hole exactly where the original bug was."""

    def test_a_second_release_beside_the_exempt_one_still_refuses(self):
        plugin = make_repo(self.workspace, "two-releases", files=CONTENT)
        plant_release(plugin / "dist")
        plant_release(plugin / "old")

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.fingerprint(plugin, exempt=(plugin / "dist",))

        message = str(refusal.exception)
        self.assertIn(str(plugin / "old"), message)
        self.assertNotIn(str(plugin / "dist"), message)

    def test_a_dependencys_own_stale_release_is_refused(self):
        """The exemption is threaded to the plugin being built and to nothing
        else. A dependency's checkout is what a pin is taken from, so a stale
        release in one is the case TODO.md reproduced against review-library."""
        library = make_repo(self.workspace, "library", files={"skills/audit/reference.md": "audit\n"})
        plant_release(library / "dist")

        # The pin is written out rather than computed, because computing it
        # would hit this very refusal before the build under test starts.
        plugin = make_repo(
            self.workspace,
            "consumer",
            requires=[needs(library, take={"skills": ["audit"]}, pin="deadbeef0000")],
        )

        with self.assertRaises(resolve.ResolveError) as refusal:
            build.build(plugin, plugin / "dist")

        self.assertIn(str(library / "dist"), str(refusal.exception))


class AReleaseUnderASkippedDirectoryIsNotRefused(RepoCase):
    """`SKIP_DIRS` is honoured exactly as fingerprinting already honours it, so
    a cached release inside `.foundry` or a virtualenv is not a build error."""

    def test_a_lock_file_inside_the_bootstrap_cache_does_not_fire_the_rule(self):
        plugin = make_repo(self.workspace, "has-a-cache", files=CONTENT)
        plant_release(plugin / ".foundry" / "0.1.1" / "dist")

        digest = resolve.fingerprint(plugin)  # must not raise

        self.assertTrue(digest)

    def test_a_lock_file_inside_dot_venv_does_not_fire_the_rule(self):
        plugin = make_repo(self.workspace, "has-a-venv", files=CONTENT)
        plant_release(plugin / ".venv" / "share" / "sample")

        digest = resolve.fingerprint(plugin)  # must not raise

        self.assertTrue(digest)


class TheCopyRefusesOnItsOwn(RepoCase):
    """Checked again where the copy happens, so no future path that reaches
    this function without going through resolve() first can ship one."""

    def test_copy_own_content_itself_refuses_the_stale_release(self):
        plugin = make_repo(self.workspace, "direct", files=CONTENT)
        plant_release(plugin / "dist")
        manifest = resolve.read_manifest(plugin)

        with self.assertRaises(build.BuildError) as refusal:
            build.copy_own_content(manifest, self.destination())

        message = str(refusal.exception)
        self.assertIn(str(plugin / "dist"), message)
        self.assertIn(resolve.LOCK_NAME, message)


class TheCheckThatWasMissingReportsIt(RepoCase):
    """`shipped.py` passed the folder that held seven lock files. It is an
    independent check rather than a second opinion from the build: nothing in
    `.github/checks/` imports from `scripts/`, on purpose, so this one would
    still catch the fault if the refusal above were ever weakened."""

    def build_one(self):
        plugin = make_repo(
            self.workspace,
            "shipped-check",
            files=SKILL,
            provides={"skills": ["greet"]},
            targets=["claude-code"],
        )
        out = self.destination()
        build.build(plugin, out)
        return plugin, out

    def test_a_clean_folder_is_accepted(self):
        plugin, out = self.build_one()
        report = Report()

        shipped.check_lock("claude-code", out, shipped.read_manifest(plugin), report)

        self.assertEqual(report.problems, [], f"a clean folder was refused: {report.problems}")

    def test_a_second_lock_file_below_the_root_is_reported(self):
        plugin, out = self.build_one()
        nested = out / "dist" / "agent-plugins"
        nested.mkdir(parents=True)
        (nested / resolve.LOCK_NAME).write_text(json.dumps({"contents": "0" * 12}) + "\n")
        report = Report()

        shipped.check_lock("claude-code", out, shipped.read_manifest(plugin), report)

        self.assertTrue(
            any("previous release shipped inside this one" in problem for problem in report.problems),
            f"a release inside the folder was not caught: {report.problems}",
        )
