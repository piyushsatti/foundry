"""'A folder's lock file describes that folder, not the build that made it.'

Two failures, one ruling, split across build.py and scripts/emitters/instructions.py
because the fix touches both:

  `build` computed `taken` once, against the single neutral tree every harness
  starts from, and handed that same list to `write_lock` for every target
  unfiltered. A pi folder built with `degrade.pi.drop: [agents]` holds no
  agents/ directory at all, and its lock file still recorded taking an agent
  file from a dependency it does not ship a single byte of.

  `keep_only_what_is_named` in instructions.py deletes every top-level path
  this folder does not name and every unnamed path under skills/ and
  commands/, prints the list once, and writes nothing into the folder. The
  loss policy has exactly two outcomes, refuse or record, and a line printed
  to stdout is neither: the instructions folder is the one that lands inside
  somebody else's repository, where nobody ever sees the build log.

Run: python3 -m unittest discover -s tests   (from the repo root)
"""

from __future__ import annotations

import json

from tests.repos import RepoCase, build, files_under, make_repo, needs

LOCK_NAME = "foundry.lock.json"


class TookDescribesTheFolderItSitsIn(RepoCase):
    """A kind pi dropped must not be recorded as taken in pi's own lock file."""

    def test_a_kind_pi_drops_is_not_recorded_as_taken_in_pis_own_lock_file(self):
        dependency = make_repo(
            self.workspace,
            "library",
            files={"agents/helper.md": "help the caller\n"},
        )
        plugin = make_repo(
            self.workspace,
            "consumer",
            requires=[needs(dependency, take={"agents": ["helper.md"]})],
            targets=["claude-code", "pi"],
            degrade={"pi": {"drop": ["agents"]}},
        )
        out = self.destination()

        build.build(plugin, out)

        claude = json.loads((out / "claude-code" / LOCK_NAME).read_text())
        pi = json.loads((out / "pi" / LOCK_NAME).read_text())

        self.assertEqual(
            claude["took"],
            [{"from": "library", "item": "agents/helper.md"}],
            "claude-code carries agents, so its lock file should still say it took the file",
        )
        self.assertFalse((out / "pi" / "agents").exists(), "pi dropped the whole agents/ directory")
        self.assertEqual(
            pi["took"],
            [],
            "pi holds no agents/ directory, so its lock file must not say it took one",
        )
        self.assertEqual(
            pi["dropped"],
            [
                {
                    "kind": "agents",
                    "why": (
                        "Pi has no agent surface: its packages carry skills, "
                        "prompt templates, themes and extensions"
                    ),
                }
            ],
        )


class InstructionsRecordsWhatItLeftBehind(RepoCase):
    """A file-level loss instructions.py makes has to be on the record too."""

    def test_a_path_instructions_leaves_out_is_recorded_in_its_own_lock_file(self):
        plugin = make_repo(
            self.workspace,
            "solo",
            files={
                "skills/greet/SKILL.md": (
                    "---\nname: greet\ndescription: Greets whoever asks.\n---\n\nSay hello.\n"
                ),
                "README.md": "not shipped into an instructions folder\n",
            },
            targets=["instructions"],
        )
        out = self.destination()

        printed = self.ship(plugin, out)

        lock = json.loads((out / LOCK_NAME).read_text())

        self.assertIn("left behind", printed, "report() should still print, as it always has")
        self.assertEqual(
            lock.get("left_behind"),
            ["README.md"],
            "a path this folder left out has to be on the record, not only in the build log",
        )
        self.assertNotIn(
            ".foundry-left-behind.json",
            files_under(out),
            "the handoff file to write_lock must never itself ship",
        )
