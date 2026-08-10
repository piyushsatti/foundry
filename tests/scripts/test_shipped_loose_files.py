"""`.github/checks/shipped.py` enforced a rule that was already narrowed.

The unread-file rule reads, in `CLAUDE.md` and the wiki's `Emitters` page: a
folder must not hold a neutral file whose translated twin it also holds.
Everything else the repository ships, ships, the same way every packaged
folder already carries `README.md`. `harnesses.py`'s `MANIFESTS` table still
listed `package.json` as belonging exclusively to Pi, even though no emitter
writes that file for Pi or anyone else, so an ordinary plugin repository's own
root `package.json` failed every other harness's folder as though it held a
manifest that was not its own.

Run: python3 -m unittest discover -s tests   (from the repo root)
"""

from __future__ import annotations

import sys
from pathlib import Path

from tests.repos import RepoCase, build, make_repo

CHECKS_DIR = Path(__file__).resolve().parents[2] / ".github" / "checks"
if str(CHECKS_DIR) not in sys.path:
    sys.path.insert(0, str(CHECKS_DIR))

import shipped  # noqa: E402
from report import Report  # noqa: E402


class ALooseFileTheHarnessDoesNotReadIsAccepted(RepoCase):
    def test_claude_code_accepts_an_ordinary_root_package_json(self):
        plugin = make_repo(
            self.workspace,
            "has-package-json",
            files={
                "skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n",
                "package.json": '{"name": "has-package-json", "private": true}\n',
            },
            provides={"skills": ["greet"]},
            targets=["claude-code"],
        )
        out = self.destination()
        build.build(plugin, out)

        manifest = shipped.read_manifest(plugin)
        report = Report()
        shipped.check_folder("claude-code", out, manifest, report)

        self.assertEqual(report.problems, [], f"an ordinary package.json was refused: {report.problems}")
        self.assertTrue((out / "package.json").exists(), "the file did not even ship")

    def test_agent_plugins_still_refuses_a_real_manifest_from_another_harness(self):
        """The narrowing must not swallow the check it exists beside: a real
        manifest another harness wrote is still a fault, because two schemas
        would then claim one filename."""
        plugin = make_repo(
            self.workspace,
            "has-a-foreign-manifest",
            files={
                "skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n",
                ".codex-plugin/plugin.json": '{"name": "not-really-codexs"}\n',
            },
            provides={"skills": ["greet"]},
            targets=["agent-plugins"],
        )
        out = self.destination()
        build.build(plugin, out)

        manifest = shipped.read_manifest(plugin)
        report = Report()
        shipped.check_folder("agent-plugins", out, manifest, report)

        self.assertTrue(
            any(".codex-plugin/plugin.json" in problem for problem in report.problems),
            f"a foreign manifest was not caught: {report.problems}",
        )
