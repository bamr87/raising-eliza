#!/usr/bin/env python3
"""test_gate.py -- pin the gate's door: a bad request is refused before any
engine runs.

Starts eliza_gate.py on a free port with --engine replay -- the engine best
suited to proving this, since a replay reply depends only on how many times
an engine has run for a conversation, not on the message text. If the door
ever let a malformed request through to an engine, that conversation's
replay cursor would move and its first real turn would come back as golden
turn 2 (or later) instead of golden turn 1: state leakage becomes visible,
not just plausible.

Waits for the socket to actually accept connections rather than sleeping a
fixed amount -- the gate prints its banner before the port is bound, same
caveat relic_api.py's own test documented.

Run: python3 -m unittest -v test_gate
"""
import json
import os
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_port(port, timeout=10):
    """Poll the socket instead of sleeping a fixed amount."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), 0.2):
                return True
        except OSError:
            time.sleep(0.05)
    return False


class GateDoor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = free_port()
        cls.proc = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "eliza_gate.py"),
             "--engine", "replay", "--port", str(cls.port)],
            cwd=HERE, stderr=subprocess.DEVNULL)
        assert wait_for_port(cls.port), "gate never bound its port"

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=10)

    def post(self, raw_body):
        url = f"http://127.0.0.1:{self.port}/say"
        req = urllib.request.Request(
            url, data=raw_body, method="POST",
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def say(self, conversation_id, message):
        return self.post(json.dumps(
            {"conversation_id": conversation_id, "message": message}).encode())

    # -- the door lets a well-formed request through -------------------------

    def test_a_well_formed_request_is_served(self):
        status, payload = self.say("door-happy-path", "Men are all alike.")
        self.assertEqual(status, 200)
        self.assertEqual(payload["engine"], "replay")
        self.assertEqual(payload["reply"], "IN WHAT WAY")

    # -- the door refuses every shape of bad request, before any engine runs -

    def test_malformed_json_is_refused_at_the_door(self):
        status, payload = self.post(b"{not json")
        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_a_json_array_is_refused_at_the_door(self):
        status, _ = self.post(b"[1, 2, 3]")
        self.assertEqual(status, 400)

    def test_missing_conversation_id_is_refused_at_the_door(self):
        status, _ = self.post(json.dumps({"message": "hello"}).encode())
        self.assertEqual(status, 400)

    def test_empty_conversation_id_is_refused_at_the_door(self):
        status, _ = self.post(json.dumps(
            {"conversation_id": "", "message": "hello"}).encode())
        self.assertEqual(status, 400)

    def test_missing_message_is_refused_at_the_door(self):
        status, _ = self.post(json.dumps({"conversation_id": "door-t1"}).encode())
        self.assertEqual(status, 400)

    def test_non_string_message_is_refused_at_the_door(self):
        status, _ = self.post(json.dumps(
            {"conversation_id": "door-t2", "message": 42}).encode())
        self.assertEqual(status, 400)

    def test_non_string_conversation_id_is_refused_at_the_door(self):
        status, _ = self.post(json.dumps(
            {"conversation_id": 7, "message": "hello"}).encode())
        self.assertEqual(status, 400)

    def test_empty_body_is_refused_at_the_door(self):
        status, _ = self.post(b"")
        self.assertEqual(status, 400)

    # -- the strongest proof: a refused request leaves no trace --------------

    def test_a_refused_request_never_advances_conversation_state(self):
        conv = "door-leak-check"
        status, _ = self.post(b"not even json")
        self.assertEqual(status, 400)
        status, _ = self.post(json.dumps(
            {"conversation_id": conv, "message": 123}).encode())  # parses, still bad
        self.assertEqual(status, 400)

        # If either bad request above had reached an engine, this
        # conversation's replay cursor would already be at 1 (or 2), and its
        # first real turn would come back as golden turn 2, not turn 1.
        status, payload = self.say(conv, "Men are all alike.")
        self.assertEqual(status, 200)
        self.assertEqual(payload["reply"], "IN WHAT WAY")

        status, payload = self.say(conv, "They're always bugging us.")
        self.assertEqual(status, 200)
        self.assertEqual(payload["reply"], "CAN YOU THINK OF A SPECIFIC EXAMPLE")


if __name__ == "__main__":
    unittest.main()
