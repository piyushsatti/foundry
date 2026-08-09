"""Three rulings against `scripts/resolve.py`, decided 2026-08-09.

    One vocabulary for `id`, the strictest, refused when the manifest is read.
    Hash the path POSIX-style, and promise nothing about Windows.
    The manifest-reading half of "Refuse what can never fire".

None of the three touches what a real plugin ships: `repos.py` builds the
template plus every repository named in `repos.local` and every one of them
still declares a plain lowercase `id`, a `version`, and no key outside what
`RECOGNIZED_KEYS` now names. These tests are about the manifests that would
have slipped through before today and do not.

`test_resolve.py` already owns the fingerprint-skip-list tests and the pin,
dependency-walk and Foundry-version tests. Nothing here repeats them.

Run: python3 -m unittest discover -s tests   (from the repo root)
"""

from __future__ import annotations

import inspect
from pathlib import Path

import yaml

from tests.repos import MANIFEST_NAME, RUNNING_FOUNDRY, RepoCase, build, make_repo, resolve


def write_manifest(root: Path, raw: dict) -> Path:
    """A manifest written exactly as given, bypassing `make_repo`'s own shape.

    `make_repo` always writes `id`, `version` and `foundry`, and always uses
    `plugin_id` as both the `id` field and the directory name. Several cases
    below are about a manifest missing one of those three keys, or an `id`
    that would be a dangerous directory name (`..`, a leading `-`), so they
    write the file directly into a directory whose name is never read.
    """
    root.mkdir(parents=True, exist_ok=True)
    (root / MANIFEST_NAME).write_text(yaml.safe_dump(raw, sort_keys=False))
    return root


class IdIsOneVocabularyTheStrictestOneDemands(RepoCase):
    """`NAME_RE` now refuses exactly what `name_fault` in `agent_plugins.py`
    refuses: the character set without the underscore, no leading or
    trailing non-alphanumeric character, no doubled hyphen or dot, and a 64
    character cap.
    """

    # One example per rule `name_fault` checks, each on its own so a failure
    # names the one rule that let it through rather than a batch of them.
    REFUSED = {
        "an-underscore": "my_plugin",
        "a-leading-hyphen": "-plugin",
        "a-leading-dot": ".plugin",
        "a-trailing-hyphen": "plugin-",
        "a-trailing-dot": "plugin.",
        "a-doubled-hyphen": "my--plugin",
        "a-doubled-dot": "my..plugin",
        "sixty-five-characters": "a" * 65,
    }

    def manifest(self, case: str, plugin_id: str) -> Path:
        return write_manifest(
            self.workspace / case,
            {"id": plugin_id, "version": "0.1.0", "foundry": RUNNING_FOUNDRY, "requires": {"plugins": []}},
        )

    def test_each_shape_the_strictest_harness_rejects_is_refused_here_first(self):
        for case, plugin_id in self.REFUSED.items():
            with self.subTest(case):
                root = self.manifest(case, plugin_id)
                with self.assertRaises(resolve.ResolveError) as refusal:
                    resolve.read_manifest(root)
                self.assertIn(plugin_id, str(refusal.exception))

    def test_a_name_of_exactly_sixty_four_characters_is_still_accepted(self):
        """The cap is 64, not 63: the boundary itself has to stay open."""
        root = self.manifest("sixty-four", "a" * 64)
        manifest = resolve.read_manifest(root)
        self.assertEqual(manifest["id"], "a" * 64)

    def test_an_ordinary_lowercase_hyphenated_name_still_works(self):
        root = self.manifest("ordinary", "plan-orchestrator")
        manifest = resolve.read_manifest(root)
        self.assertEqual(manifest["id"], "plan-orchestrator")


class ARefusedIdIsCaughtBeforeAnyFolderIsBuilt(RepoCase):
    """The cost the ruling names: `id: my_plugin` used to pass the loose
    check here, build a claude-code folder in staging, and only then stop
    the whole release the moment `agent-plugins` came up in the per-target
    loop, deep inside that harness's own emitter, as an `EmitError` naming
    one harness rather than the id. `read_manifest` runs before `build()`
    goes anywhere near a target, so the same manifest now stops as a
    `ResolveError` about the id, and nothing is ever written to `--out`,
    not even the claude-code folder that would have built cleanly alone.
    """

    def test_the_refusal_is_a_resolve_error_and_nothing_is_written(self):
        root = write_manifest(
            self.workspace / "priority-channel",
            {
                "id": "my_plugin",
                "version": "0.1.0",
                "foundry": RUNNING_FOUNDRY,
                "requires": {"plugins": []},
                "targets": ["claude-code", "agent-plugins"],
            },
        )
        out = self.destination()

        with self.assertRaises(resolve.ResolveError) as refusal:
            build.build(root, out)

        self.assertIn("my_plugin", str(refusal.exception))
        self.assertFalse(out.exists(), "a folder was written even though the id was refused")


class UnrecognisedTopLevelKeyIsRefused(RepoCase):
    """An ignored key reads to whoever wrote it as a rule that took effect."""

    def manifest(self, case: str, **fields) -> Path:
        raw = {"id": case, "version": "0.1.0", "foundry": RUNNING_FOUNDRY, "requires": {"plugins": []}}
        raw.update(fields)
        return write_manifest(self.workspace / case, raw)

    def test_target_typo_for_targets_is_refused_rather_than_silently_ignored(self):
        """The exact case the ruling names: `target:` used to build the
        default folder and never say the harness that was actually written
        was never read."""
        root = self.manifest("typo", target=["claude-code"])

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.read_manifest(root)

        self.assertIn("target", str(refusal.exception))

    def test_an_arbitrary_unknown_key_is_refused_and_named(self):
        root = self.manifest("arbitrary", nonsense="whatever")

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.read_manifest(root)

        self.assertIn("nonsense", str(refusal.exception))

    def test_foundry_source_is_a_real_key_and_is_never_refused(self):
        """The trap named in the ruling: `foundry_source` is read only by
        `template/scripts/foundry.py`'s own regex, never by `read_manifest`.
        An allowlist built from what this module happens to consume would
        refuse the one documented way to build against a local Foundry
        checkout, which `template/foundry.plugin.yaml` carries commented out
        for exactly that reason.
        """
        root = self.manifest("local-checkout", foundry_source="../../foundry/foundry")

        manifest = resolve.read_manifest(root)

        self.assertEqual(manifest["id"], "local-checkout")

    def test_every_metadata_key_is_recognised_together(self):
        root = self.manifest(
            "described",
            description="One line.",
            author={"name": "Someone"},
            homepage="https://example.com",
            license="MIT",
            keywords=["review"],
        )

        manifest = resolve.read_manifest(root)

        self.assertEqual(manifest["description"], "One line.")
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["keywords"], ["review"])

    def test_requires_targets_degrade_provides_and_exclude_are_all_recognised(self):
        root = self.manifest(
            "structured",
            targets=["claude-code"],
            degrade={},
            provides={"skills": []},
            exclude=["notes"],
        )

        manifest = resolve.read_manifest(root)

        self.assertEqual(manifest["targets"], ["claude-code"])
        self.assertEqual(manifest["exclude"], ["notes"])


class MissingVersionIsRefused(RepoCase):
    """A manifest with no `version` used to ship `0.0.0` into every harness
    manifest and lock file without saying so. It is refused instead.
    """

    def test_a_manifest_with_no_version_key_at_all_is_refused(self):
        root = write_manifest(
            self.workspace / "no-version-key",
            {"id": "no-version-key", "foundry": RUNNING_FOUNDRY, "requires": {"plugins": []}},
        )

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.read_manifest(root)

        self.assertIn("version", str(refusal.exception))

    def test_a_version_key_written_with_no_value_is_refused_the_same_way(self):
        root = self.workspace / "null-version"
        root.mkdir(parents=True, exist_ok=True)
        (root / MANIFEST_NAME).write_text(
            f"id: null-version\nversion:\nfoundry: {RUNNING_FOUNDRY}\nrequires:\n  plugins: []\n"
        )

        with self.assertRaises(resolve.ResolveError) as refusal:
            resolve.read_manifest(root)

        self.assertIn("version", str(refusal.exception))

    def test_a_manifest_that_declares_a_version_resolves_fine_and_keeps_it(self):
        root = make_repo(self.workspace, "versioned", version="1.2.3")

        manifest = resolve.read_manifest(root)

        self.assertEqual(manifest["version"], "1.2.3")
        self.assertNotEqual(manifest["version"], "0.0.0", "the old silent default is still reachable")


class FingerprintHashesThePathPosixStyle(RepoCase):
    """`fingerprint` now hashes `relative.as_posix()`, never `str(relative)`.

    On macOS and Linux `Path.__str__` already prints with `/`, so the two
    expressions produce identical bytes for every tree buildable on this
    machine: no digest already published moves, and no tree built here can
    behave differently before and after the edit. That symmetry is the whole
    reason the ruling calls this change free, and it is also why the source
    itself, not a built tree, is what has to be checked to tell the two
    implementations apart on this platform.
    """

    SAMPLE = {"README.md": "readme\n", "skills/greet/SKILL.md": "greet\n"}
    # sha256 over "README.md\0readme\n\0skills/greet/SKILL.md\0greet\n\0", first
    # 12 hex characters. The same tree and the same digest as test_resolve.py's
    # FingerprintIsFrozen, which is the point: this change moves nothing here.
    SAMPLE_DIGEST = "518d7c109d4d"

    def test_the_hashed_bytes_come_from_as_posix_not_str(self):
        source = inspect.getsource(resolve.fingerprint)
        self.assertIn(
            "relative.as_posix()",
            source,
            "fingerprint() does not hash the POSIX form of the relative path",
        )
        self.assertNotIn(
            "digest.update(str(relative)",
            source,
            "fingerprint() still hashes str(relative), the platform-dependent form",
        )

    def test_a_known_tree_still_hashes_to_the_digest_it_has_always_hashed_to(self):
        """The proof the ruling itself points to: on this platform, nothing moved."""
        root = self.workspace / "posix-sample"
        for relative, text in self.SAMPLE.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)

        self.assertEqual(
            resolve.fingerprint(root),
            self.SAMPLE_DIGEST,
            "the digest moved on macOS/Linux, where the ruling promised it would not",
        )
