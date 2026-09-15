#!/usr/bin/env python3
"""eliza_gate.py -- a modern gate in front of the revived ELIZA relic.

POST /say {"conversation_id": "...", "message": "..."} -> JSON reply. State
(the live port's MEMORY queue and its per-group reassembly cycling, plus a
replay cursor) is kept per conversation_id, in memory, for the life of the
process -- so a multi-turn conversation behaves the same over HTTP as it
does in reconcile.py's single continuous session.

Which engine answers is a routing decision, not a rewrite:
  --engine replay  play back relic/golden/cacm_1966_conversation.txt in
                   order, per conversation (the default: nothing runs the
                   port at all). This is the closest thing to "the relic"
                   this dig site has: Weizenbaum's original 1966 MAD-SLIP
                   ELIZA cannot be run here -- no MAD-SLIP compiler is
                   available at this dig site (see work/EXPEDITION.md) --
                   so its one surviving, published transcript stands in for
                   it. Replay does not read `message`; it has nothing to
                   run it against, and says so if asked (see eliza.py's own
                   docstring on what is reconstructed vs. verified).
  --engine shadow  the caller is served the replay answer, exactly as
                   above; behind that answer eliza.py (the live port) also
                   runs, on the same conversation and the same message, and
                   every mismatch between the two is logged. Because
                   reconcile.py already establishes that eliza.py reproduces
                   the golden transcript turn for turn when fed the golden
                   USER lines in order, feeding this chapter's shadow mode
                   that same 15-line conversation should log fifteen
                   MATCHes -- that is the load test this gate is built to
                   pass.
  --engine live    eliza.py (the live port) answers for real, from
                   `message`.

Cutover and rollback are the same flag: kill the process and restart it
with a different --engine. Nothing about routing is compiled in.

Stdlib only. Usage: python3 eliza_gate.py --engine shadow --port 8765
"""
import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from eliza import Eliza  # noqa: E402

GOLDEN_PATH = os.path.join(HERE, "..", "relic", "golden", "cacm_1966_conversation.txt")


def load_golden(path):
    """Same parse reconcile.py and test_eliza.py use: USER/ELIZA line pairs."""
    with open(path) as f:
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


GOLDEN_PAIRS = load_golden(GOLDEN_PATH)


class BadRequest(Exception):
    """Raised by parse_say_request. Carries the message for the 400 body.
    Nothing that raises this ever touches an engine -- do_POST validates
    and returns before either replay_reply() or live_reply() is called."""


def parse_say_request(raw_body):
    """Validate a POST /say body. Returns (conversation_id, message) or
    raises BadRequest. This is the whole door: it is deliberately the only
    function in this file that looks at the request body."""
    try:
        body = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise BadRequest(f"body is not valid JSON: {exc}") from exc
    if not isinstance(body, dict):
        raise BadRequest("body must be a JSON object")
    conversation_id = body.get("conversation_id")
    message = body.get("message")
    if not isinstance(conversation_id, str) or not conversation_id:
        raise BadRequest("conversation_id must be a non-empty string")
    if not isinstance(message, str):
        raise BadRequest("message must be a string")
    return conversation_id, message


class Conversation:
    """Per-conversation state. `eliza` is a live Eliza() session -- its
    MEMORY queue and each rule-group's next-alternative counter live inside
    it and persist across turns exactly as they would in one continuous
    reconcile.py-style session. `replay_next` is the analogous cursor for
    replay mode: which golden line this conversation is up to."""

    def __init__(self):
        self.eliza = Eliza()
        self.replay_next = 0

    def replay_reply(self):
        reply = GOLDEN_PAIRS[self.replay_next % len(GOLDEN_PAIRS)][1]
        self.replay_next += 1
        return reply

    def live_reply(self, message):
        return self.eliza.respond(message)


class Gate(BaseHTTPRequestHandler):
    engine = "replay"
    conversations = {}   # conversation_id -> Conversation, for the life of the process

    def _conversation(self, conversation_id):
        conv = self.conversations.get(conversation_id)
        if conv is None:
            conv = Conversation()
            self.conversations[conversation_id] = conv
        return conv

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/say":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length"))
        except (TypeError, ValueError):
            self._send_json(400, {"error": "missing or invalid Content-Length"})
            return
        raw = self.rfile.read(length)

        try:
            conversation_id, message = parse_say_request(raw)
        except BadRequest as exc:
            self._send_json(400, {"error": str(exc)})
            return

        # -- the door is shut behind us; only now does an engine run --------
        conv = self._conversation(conversation_id)

        if self.engine == "shadow":
            served = conv.replay_reply()
            live = conv.live_reply(message)
            verdict = "MATCH" if served == live else f"MISMATCH live={live!r}"
            print(f"SHADOW conversation={conversation_id} replay={served!r} {verdict}",
                  file=sys.stderr)
            reply, served_engine = served, "replay"
        elif self.engine == "replay":
            reply, served_engine = conv.replay_reply(), "replay"
        else:
            reply, served_engine = conv.live_reply(message), "live"

        self._send_json(200, {
            "conversation_id": conversation_id,
            "engine": served_engine,
            "reply": reply,
        })

    def do_GET(self):
        self.send_error(405, "use POST /say")

    def log_message(self, fmt, *args):
        print(f"GATE {self.command} {self.path} -> {args[1]}", file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=("replay", "shadow", "live"), default="replay")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    Gate.engine = a.engine
    print(f"gate open on http://127.0.0.1:{a.port}/say  engine={a.engine}", file=sys.stderr)
    HTTPServer(("127.0.0.1", a.port), Gate).serve_forever()
