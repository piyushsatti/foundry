"""One ruling against `scripts/emitters/__init__.py`, decided 2026-08-09.

    Refuse what can never fire, print what is only inert today.

This file owns only the `degrade` half of that ruling: a waiver naming a kind
the named harness actually carries can never produce a drop, so it is refused.
A waiver naming a kind the harness genuinely cannot carry, but this plugin does
not hold yet, is not wrong, only unused today, so it is printed and the build
stays green. The sibling half of the same ruling, an unrecognised top-level
manifest key and a missing `version`, lives in `scripts/resolve.py` and is
covered by `test_resolve_conformance.py`.

`test_emitters.py` already owns the ordinary loss policy: a kind a harness
truly cannot carry stops the build unless the manifest waives it, and the
waiver then becomes a recorded drop. Nothing here repeats that. Both cases
below name a kind the ordinary policy never reaches at all: one because the
waiver is impossible before the ordinary check would even look at it, one
because the plugin holds nothing for the ordinary check to see.

Run: python3 -m unittest discover -s tests   (from the repo root)
"""

from __future__ import annotations

import contextlib
import io

from tests.repos import RepoCase, build, make_repo

from emitters import EmitError  # noqa: E402  reachable once tests.repos has put scripts/ on the path


class AWaiverNamingAKindTheHarnessCarriesIsRefused(RepoCase):
    """OpenCode carries `agents` (`skills_tree.CAPABILITIES["opencode"]`), so
    `degrade.opencode.drop: [agents]` cannot ever produce a drop: the kind
    ships regardless of what the waiver claims. That is a false statement
    about the build, the same fault `read_degrade` in `scripts/resolve.py`
    already refuses one step earlier, when the waiver names a harness outside
    `targets` instead of a kind inside one.
    """

    def plugin(self):
        return make_repo(
            self.workspace,
            "carried-kind-waived",
            files={
                "agents/helper.md": "---\nname: helper\ndescription: Helps.\n---\n\nHelps.\n",
            },
            targets=["opencode"],
            degrade={"opencode": {"drop": ["agents"]}},
        )

    def test_the_build_refuses_rather_than_shipping_the_waiver_unused(self):
        plugin = self.plugin()
        out = self.destination()

        with self.assertRaises(EmitError) as refusal:
            build.build(plugin, out)

        message = str(refusal.exception)
        self.assertIn("degrade.opencode.drop", message)
        self.assertIn("agents", message)
        self.assertIn("opencode", message)
        self.assertIn(str(plugin / "foundry.plugin.yaml"), message)


class AWaiverForAKindThePluginDoesNotHoldYetIsPrintedNotRefused(RepoCase):
    """Pi cannot carry `mcp` (`skills_tree.CAPABILITIES["pi"]`), and this
    plugin holds no `mcp.json`. The waiver is not wrong, only early: it does
    nothing today and becomes a real, recorded drop the day this plugin grows
    an MCP server. The template ships exactly this shape on purpose, in
    `degrade.pi.drop: [mcp]`, with a comment saying the block is inert in a
    fresh repository.
    """

    def plugin(self):
        return make_repo(
            self.workspace,
            "uninhabited-kind-waived",
            files={
                "skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n",
            },
            targets=["pi"],
            degrade={"pi": {"drop": ["mcp"]}},
        )

    def test_the_build_stays_green_and_prints_the_waiver_is_unused(self):
        plugin = self.plugin()
        out = self.destination()

        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            answer = build.build(plugin, out)

        record = answer["targets"][0]
        self.assertEqual(record["dropped"], [], "nothing was dropped: pi never held an mcp.json to drop")

        message = printed.getvalue()
        self.assertIn("degrade.pi.drop", message)
        self.assertIn("mcp", message)
        self.assertIn("pi", message)
        self.assertIn(str(plugin / "foundry.plugin.yaml"), message)


class TheOrdinaryLossPolicyIsUnchangedForAKindThePluginActuallyHolds(RepoCase):
    """A waiver naming a kind the harness cannot carry, for content the
    plugin really has, is neither of the two new cases: it is the ordinary
    policy `test_emitters.py` already covers, and it must still work exactly
    as it did, recorded as a drop and nothing printed about it being unused.
    """

    def test_a_genuine_drop_is_still_recorded_and_not_reported_as_unused(self):
        plugin = make_repo(
            self.workspace,
            "genuinely-dropped",
            files={
                "skills/greet/SKILL.md": "---\nname: greet\ndescription: Greet.\n---\n\nGreet.\n",
                "mcp.json": (
                    '{"$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",'
                    '"mcpServers": {"demo": {"type": "stdio", "command": "demo"}}}'
                ),
            },
            targets=["pi"],
            degrade={"pi": {"drop": ["mcp"]}},
        )
        out = self.destination()

        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            answer = build.build(plugin, out)

        record = answer["targets"][0]
        self.assertEqual(record["dropped"], [{"kind": "mcp", "why": "Pi has no MCP surface"}])
        self.assertNotIn("unused", printed.getvalue())
        self.assertFalse((out / "mcp.json").exists())


if __name__ == "__main__":
    import unittest

    unittest.main()
