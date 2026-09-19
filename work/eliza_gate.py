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
                   port at all). Replay does not read `message`.
  --engine shadow  the caller is served the replay answer; eliza.py also
                   runs, and every mismatch is logged (and returned as
                   additive JSON fields).
  --engine live    eliza.py answers for real, from `message`.

GET / serves the housing UI. Additive JSON routes under /api/ do not
touch an engine. POST /say still validates before any engine runs.

Cutover and rollback are the same flag: kill the process and restart it
with a different --engine. Nothing about routing is compiled in.

Stdlib only. Usage: python3 eliza_gate.py --engine live --port 8765
"""
import argparse
import json
import os
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from eliza import Eliza  # noqa: E402

GOLDEN_PATH = os.path.join(HERE, "..", "relic", "golden", "cacm_1966_conversation.txt")
STATIC_DIR = os.path.join(HERE, "static")
INDEX_PATH = os.path.join(STATIC_DIR, "index.html")


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
    raises BadRequest. This is the whole door for /say: it is deliberately
    the only function that looks at that request body."""
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


def parse_create_request(raw_body):
    if not raw_body:
        return None
    try:
        body = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise BadRequest(f"body is not valid JSON: {exc}") from exc
    if not isinstance(body, dict):
        raise BadRequest("body must be a JSON object")
    conversation_id = body.get("conversation_id")
    if conversation_id is None:
        return None
    if not isinstance(conversation_id, str) or not conversation_id:
        raise BadRequest("conversation_id must be a non-empty string")
    return conversation_id


class Conversation:
    """Per-conversation state. `eliza` is a live Eliza() session -- its
    MEMORY queue and each rule-group's next-alternative counter live inside
    it and persist across turns exactly as they would in one continuous
    reconcile.py-style session. `replay_next` is the analogous cursor for
    replay mode: which golden line this conversation is up to."""

    def __init__(self):
        self.eliza = Eliza()
        self.replay_next = 0
        self.turns = []

    def replay_reply(self):
        reply = GOLDEN_PAIRS[self.replay_next % len(GOLDEN_PAIRS)][1]
        self.replay_next += 1
        return reply

    def live_reply(self, message):
        return self.eliza.respond(message)

    def snapshot(self):
        return {
            "greeting": self.eliza.greeting_line(),
            "turns": list(self.turns),
            "turn_count": self.eliza.turn_count,
            "memory": list(self.eliza.memory_queue),
            "replay_next": self.replay_next,
            "trace": self.eliza.last,
        }


class Gate(BaseHTTPRequestHandler):
    engine = "replay"
    conversations = {}
    lock = threading.Lock()

    def _route(self):
        return unquote(urlparse(self.path).path)

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

    def _send_bytes(self, status, content_type, data):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_raw(self):
        try:
            length = int(self.headers.get("Content-Length"))
        except (TypeError, ValueError):
            return None
        return self.rfile.read(length)

    def _payload_after_engine(self, conversation_id, conv, message, reply, served_engine, extra):
        turn = {"user": message, "reply": reply, "engine": served_engine}
        turn.update(extra)
        conv.turns.append(turn)
        payload = {
            "conversation_id": conversation_id,
            "engine": served_engine,
            "reply": reply,
            "turn": len(conv.turns),
            "memory": list(conv.eliza.memory_queue),
            "replay_next": conv.replay_next,
        }
        payload.update(extra)
        if conv.eliza.last is not None and (
                served_engine == "live" or "live" in extra):
            payload["trace"] = conv.eliza.last
        return payload

    def do_POST(self):
        path = self._route()
        if path == "/api/conversations":
            self._create_conversation()
            return
        if path != "/say":
            self.send_error(404)
            return

        raw = self._read_raw()
        if raw is None:
            self._send_json(400, {"error": "missing or invalid Content-Length"})
            return

        try:
            conversation_id, message = parse_say_request(raw)
        except BadRequest as exc:
            self._send_json(400, {"error": str(exc)})
            return

        extra = {}
        with self.lock:
            conv = self._conversation(conversation_id)
            if self.engine == "shadow":
                served = conv.replay_reply()
                live = conv.live_reply(message)
                match = served == live
                verdict = "MATCH" if match else f"MISMATCH live={live!r}"
                print(f"SHADOW conversation={conversation_id} replay={served!r} {verdict}",
                      file=sys.stderr)
                reply, served_engine = served, "replay"
                extra = {"live": live, "match": match}
            elif self.engine == "replay":
                reply, served_engine = conv.replay_reply(), "replay"
            else:
                reply, served_engine = conv.live_reply(message), "live"
            payload = self._payload_after_engine(
                conversation_id, conv, message, reply, served_engine, extra)

        self._send_json(200, payload)

    def _create_conversation(self):
        raw = self._read_raw()
        if raw is None:
            self._send_json(400, {"error": "missing or invalid Content-Length"})
            return
        try:
            requested = parse_create_request(raw)
        except BadRequest as exc:
            self._send_json(400, {"error": str(exc)})
            return
        conversation_id = requested or uuid.uuid4().hex
        with self.lock:
            conv = self._conversation(conversation_id)
            snap = conv.snapshot()
        self._send_json(200, {
            "conversation_id": conversation_id,
            "engine": self.engine,
            "greeting": snap["greeting"],
            "turns": snap["turns"],
            "memory": snap["memory"],
            "replay_next": snap["replay_next"],
        })

    def do_GET(self):
        path = self._route()
        if path in ("/", "/index.html"):
            self._serve_index()
            return
        if path == "/api/status":
            with self.lock:
                n = len(self.conversations)
            self._send_json(200, {
                "engine": self.engine,
                "engines": ["replay", "shadow", "live"],
                "conversations": n,
                "golden_turns": len(GOLDEN_PAIRS),
            })
            return
        if path == "/api/golden":
            self._send_json(200, {
                "turns": [{"user": u, "eliza": e} for u, e in GOLDEN_PAIRS],
            })
            return
        if path == "/api/conversations":
            with self.lock:
                ids = sorted(self.conversations)
            self._send_json(200, {"conversations": ids, "engine": self.engine})
            return
        if path.startswith("/api/conversations/"):
            conversation_id = path[len("/api/conversations/"):]
            if not conversation_id:
                self._send_json(400, {"error": "missing conversation_id"})
                return
            with self.lock:
                conv = self.conversations.get(conversation_id)
                snap = conv.snapshot() if conv is not None else None
            if snap is None:
                self._send_json(404, {"error": "unknown conversation"})
                return
            snap["conversation_id"] = conversation_id
            snap["engine"] = self.engine
            self._send_json(200, snap)
            return
        if path == "/say":
            self.send_error(405, "use POST /say")
            return
        self.send_error(404)

    def do_DELETE(self):
        path = self._route()
        prefix = "/api/conversations/"
        if not path.startswith(prefix) or path == prefix:
            self.send_error(404)
            return
        conversation_id = path[len(prefix):]
        with self.lock:
            self.conversations.pop(conversation_id, None)
        self._send_json(200, {"conversation_id": conversation_id, "deleted": True})

    def _serve_index(self):
        try:
            with open(INDEX_PATH, "rb") as f:
                data = f.read()
        except OSError:
            self.send_error(500, "frontend missing")
            return
        self._send_bytes(200, "text/html; charset=utf-8", data)

    def log_message(self, fmt, *args):
        print(f"GATE {self.command} {self.path} -> {args[1]}", file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=("replay", "shadow", "live"), default="replay")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    Gate.engine = a.engine
    print(f"gate open on http://{a.host}:{a.port}/  engine={a.engine}", file=sys.stderr)
    ThreadingHTTPServer((a.host, a.port), Gate).serve_forever()
