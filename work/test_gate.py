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

    def get(self, path):
        url = f"http://127.0.0.1:{self.port}{path}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, r.headers.get_content_type(), r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get_content_type(), e.read()

    def delete(self, path):
        url = f"http://127.0.0.1:{self.port}{path}"
        req = urllib.request.Request(url, method="DELETE")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

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

    def test_get_root_serves_the_frontend(self):
        status, content_type, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "text/html")
        self.assertIn(b"ELIZA", body)

    def test_get_does_not_run_an_engine(self):
        conv = "door-get-no-engine"
        status, _, _ = self.get("/api/status")
        self.assertEqual(status, 200)
        status, payload = self.say(conv, "Men are all alike.")
        self.assertEqual(status, 200)
        self.assertEqual(payload["reply"], "IN WHAT WAY")

    def test_status_reports_engine_without_a_say(self):
        status, content_type, body = self.get("/api/status")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        payload = json.loads(body)
        self.assertEqual(payload["engine"], "replay")
        self.assertEqual(payload["golden_turns"], 15)

    def test_create_conversation_returns_script_greeting(self):
        raw = json.dumps({"conversation_id": "door-greet"}).encode()
        url = f"http://127.0.0.1:{self.port}/api/conversations"
        req = urllib.request.Request(
            url, data=raw, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            payload = json.loads(r.read())
        self.assertEqual(payload["conversation_id"], "door-greet")
        self.assertIn("HOW DO YOU DO", payload["greeting"])
        status, say_payload = self.say("door-greet", "Men are all alike.")
        self.assertEqual(status, 200)
        self.assertEqual(say_payload["reply"], "IN WHAT WAY")

    def test_delete_resets_replay_cursor(self):
        conv = "door-reset"
        status, payload = self.say(conv, "Men are all alike.")
        self.assertEqual(payload["reply"], "IN WHAT WAY")
        status, payload = self.say(conv, "next")
        self.assertEqual(payload["reply"], "CAN YOU THINK OF A SPECIFIC EXAMPLE")
        status, deleted = self.delete(f"/api/conversations/{conv}")
        self.assertEqual(status, 200)
        self.assertTrue(deleted["deleted"])
        status, payload = self.say(conv, "Men are all alike.")
        self.assertEqual(payload["reply"], "IN WHAT WAY")

    def test_say_keeps_the_original_contract_and_adds_fields(self):
        status, payload = self.say("door-extra", "Men are all alike.")
        self.assertEqual(status, 200)
        self.assertEqual(payload["engine"], "replay")
        self.assertEqual(payload["reply"], "IN WHAT WAY")
        self.assertEqual(payload["turn"], 1)
        self.assertIn("memory", payload)


class GateLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = free_port()
        cls.proc = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "eliza_gate.py"),
             "--engine", "live", "--port", str(cls.port)],
            cwd=HERE, stderr=subprocess.DEVNULL)
        assert wait_for_port(cls.port), "live gate never bound its port"

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=10)

    def say(self, conversation_id, message):
        url = f"http://127.0.0.1:{self.port}/say"
        req = urllib.request.Request(
            url, data=json.dumps({
                "conversation_id": conversation_id,
                "message": message,
            }).encode(), method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())

    def test_live_answers_from_the_message(self):
        status, payload = self.say("live-1", "Men are all alike.")
        self.assertEqual(status, 200)
        self.assertEqual(payload["engine"], "live")
        self.assertEqual(payload["reply"], "IN WHAT WAY")
        self.assertEqual(payload["trace"]["keyword"], "ALIKE")
        self.assertEqual(payload["trace"]["source"], "rule")

    def test_live_refuses_a_bad_request_before_the_engine(self):
        url = f"http://127.0.0.1:{self.port}/say"
        req = urllib.request.Request(
            url, data=b"{not json", method="POST",
            headers={"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(req, timeout=10)
        self.assertEqual(caught.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
