#!/usr/bin/env python3
"""test_eliza.py — characterization trials for a not-yet-written ELIZA port.

golden/cacm_1966_conversation.txt (relic/golden/) is the golden master: the
15-exchange sample conversation Weizenbaum printed in his January 1966 CACM
paper, as USER/ELIZA line pairs. These trials pin it. They do not say what a
port SHOULD do; they say what the golden master already records, so any port
that drifts from it fails loudly.

The trials run one continuous session, turn by turn, rather than a fresh
session per turn: ELIZA's MEMORY mechanism carries state forward (turn 30,
"DOES THAT HAVE ANYTHING TO DO WITH THE FACT THAT YOUR BOYFRIEND MADE YOU
COME HERE", echoes turn 5's "boyfriend made me come here"), so restarting the
session each turn would make that trial untestable.

No `eliza` module exists yet in this chapter — the port is Chapter V's job.
Every trial below that touches `eliza` is therefore EXPECTED TO FAIL right
now, with ModuleNotFoundError. That failure is the red gauntlet: proof the
trials actually exercise something, not evidence the trials are broken.

Run: python3 -m unittest -v test_eliza
"""
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.path.join(HERE, "..", "relic", "golden", "cacm_1966_conversation.txt")


def load_golden():
    """Parse the golden transcript into an ordered list of (user, eliza) pairs."""
    with open(GOLDEN) as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]
    pairs = []
    for i in range(0, len(lines), 2):
        u_speaker, _, u_text = lines[i].partition(": ")
        e_speaker, _, e_text = lines[i + 1].partition(": ")
        assert u_speaker == "USER" and e_speaker == "ELIZA", (
            f"golden master out of order at line {i + 1}: {lines[i]!r}, {lines[i + 1]!r}"
        )
        pairs.append((u_text, e_text))
    return pairs


GOLDEN_PAIRS = load_golden()


class GoldenMasterIsIntact(unittest.TestCase):
    """Sanity trials on the fixture itself. No `eliza` module involved, so
    these pass today — they pin the target before anything is built against it."""

    def test_golden_master_has_fifteen_exchanges(self):
        self.assertEqual(len(GOLDEN_PAIRS), 15)

    def test_first_exchange_matches_the_1966_paper(self):
        self.assertEqual(GOLDEN_PAIRS[0], ("Men are all alike.", "IN WHAT WAY"))

    def test_last_exchange_matches_the_1966_paper(self):
        self.assertEqual(
            GOLDEN_PAIRS[-1],
            (
                "Bullies.",
                "DOES THAT HAVE ANYTHING TO DO WITH THE FACT THAT "
                "YOUR BOYFRIEND MADE YOU COME HERE",
            ),
        )

    def test_memory_turn_echoes_the_earlier_boyfriend_exchange(self):
        # turn 5/6 plants "boyfriend made me/you come here"; turn 29/30 recalls it.
        self.assertIn("boyfriend made me come here", GOLDEN_PAIRS[2][0].lower())
        self.assertIn("YOUR BOYFRIEND MADE YOU COME HERE", GOLDEN_PAIRS[-1][1])


class ElizaReproducesTheCacm1966Conversation(unittest.TestCase):
    """Turn-by-turn characterization of the golden master, run as one
    continuous session so state (e.g. MEMORY) carries across turns.

    setUpClass swallows the import error instead of letting it abort the
    whole class, so each of the 15 turn trials below is reported on its own
    — one witness per turn, all fifteen visibly red — rather than collapsing
    into a single class-level error."""

    session = None
    import_error = None

    @classmethod
    def setUpClass(cls):
        try:
            import eliza  # does not exist yet — this chapter only pins the target
            cls.session = eliza.Eliza()
        except Exception as exc:  # noqa: BLE001 — deliberately broad: any import-time failure should fail every trial
            cls.import_error = exc

    def setUp(self):
        if self.import_error is not None:
            self.fail(f"eliza module not available yet: {self.import_error!r}")


def _make_turn_test(index, user_text, expected_reply):
    def test(self):
        reply = self.session.respond(user_text)
        self.assertEqual(reply, expected_reply)

    test.__doc__ = f'turn {index}: USER {user_text!r} -> ELIZA {expected_reply!r}'
    return test


for _index, (_user_text, _expected_reply) in enumerate(GOLDEN_PAIRS, start=1):
    setattr(
        ElizaReproducesTheCacm1966Conversation,
        f"test_turn_{_index:02d}",
        _make_turn_test(_index, _user_text, _expected_reply),
    )
del _index, _user_text, _expected_reply


class ElizaIsScriptDriven(unittest.TestCase):
    """Novel inputs, own session. Replies must come from the script, not a table."""

    def setUp(self):
        import eliza
        self.session = eliza.Eliza()

    def test_computer_keyword_outranks_dream(self):
        reply = self.session.respond("I dreamed about my computer last night.")
        self.assertEqual(reply, "DO COMPUTERS WORRY YOU")
        self.assertEqual(self.session.last["keyword"], "COMPUTER")
        self.assertEqual(self.session.last["source"], "rule")

    def test_everybody_links_to_everyone(self):
        reply = self.session.respond("Everybody hates me.")
        self.assertEqual(reply, "REALLY, EVERYBODY")
        self.assertEqual(self.session.last["keyword"], "EVERYBODY")

    def test_none_rule_when_no_keyword(self):
        reply = self.session.respond("asdfgh qwerty zxcvb")
        self.assertEqual(reply, "I AM NOT SURE I UNDERSTAND YOU FULLY")
        self.assertIsNone(self.session.last["keyword"])
        self.assertEqual(self.session.last["source"], "none")

    def test_sessions_do_not_share_reassembly_cycles(self):
        import eliza
        a = eliza.Eliza()
        b = eliza.Eliza()
        self.assertEqual(a.respond("Men are all alike."), "IN WHAT WAY")
        self.assertEqual(b.respond("Men are all alike."), "IN WHAT WAY")


if __name__ == "__main__":
    unittest.main()
