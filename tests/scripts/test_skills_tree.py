"""The two hook `Cannot` sentences soften to the form Codex already uses.

`CAPABILITIES["opencode"]` and `CAPABILITIES["pi"]` in
`scripts/emitters/skills_tree.py` used to say "OpenCode has no declarative
hook surface" and "Pi has no declarative hook surface". Both are a claim about
the harness: that no such surface exists anywhere. Pi ruled that a harness
with no `hooks` entry in Foundry's own capability table means only that
Foundry found no surface it could map onto its own six moments, not that no
surface exists. `agent_plugins.py` already states the weaker, true claim for
Codex: "no Codex hook event vocabulary has been read from source". These two
sentences are rewritten to match that form, one per harness.

The refusal these sentences sit inside is printed verbatim to a plugin author,
so this is checked at the point it reaches them: a real build of a plugin
naming hooks and one of the two harnesses, read back out of the `EmitError`
`refusal()` raises in `scripts/emitters/__init__.py`.

Run: python3 -m unittest discover -s tests   (from the repo root)
"""

from __future__ import annotations

from tests.repos import RepoCase, make_repo

from emitters import EmitError

SKILL_TEXT = "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n"
HOOKS_TEXT = "- at: session-start\n  run: hooks/announce.sh\n"
ANNOUNCE_TEXT = "#!/bin/sh\necho 'review panel loaded'\n"


class TheTwoCannotSentencesSoftenToTheFormCodexAlreadyUses(RepoCase):
    """One plugin shape, built once per harness, read for the exact wording."""

    def with_hooks(self, target: str):
        return make_repo(
            self.workspace,
            "guarded",
            files={
                "skills/greet/SKILL.md": SKILL_TEXT,
                "hooks/hooks.yaml": HOOKS_TEXT,
                "hooks/announce.sh": ANNOUNCE_TEXT,
            },
            targets=[target],
        )

    def refusal_text(self, target: str) -> str:
        plugin = self.with_hooks(target)
        with self.assertRaises(EmitError) as refusal:
            self.ship(plugin, self.destination(target))
        return str(refusal.exception)

    def test_opencode_names_what_foundry_read_not_what_opencode_lacks(self):
        """Reproduces the ruling: today this asserts the old, stronger claim
        and fails, because the sentence still says OpenCode itself has no
        hook surface rather than saying Foundry has not read one from
        source."""
        message = self.refusal_text("opencode")
        self.assertIn(
            "no OpenCode hook event vocabulary has been read from source",
            message,
        )
        self.assertNotIn("OpenCode has no declarative hook surface", message)

    def test_pi_names_what_foundry_read_not_what_pi_lacks(self):
        """Same reproduction, for Pi's sentence."""
        message = self.refusal_text("pi")
        self.assertIn("no Pi hook event vocabulary has been read from source", message)
        self.assertNotIn("Pi has no declarative hook surface", message)

    def test_agent_plugins_hook_sentence_is_untouched(self):
        """The ruling draws the line at Agent Plugins on purpose: version
        1.0.0 of that specification defining no hook component is a checkable
        fact about a published document, not a claim about a harness, so it
        is not one of the two sentences softened here. This is the negative
        case: it must keep saying exactly what it said before."""
        message = self.refusal_text("codex")
        self.assertIn(
            "no Codex hook event vocabulary has been read from source",
            message,
        )
