"""The whole loop, through the command line; and III.11's line with a test
double standing where a real model's process would."""
import json
import os
import shlex
import subprocess
import sys
import unittest

import helper
from raising import keep as K
from raising import prove


def cli(*args):
    p = subprocess.run([sys.executable, "-m", "raising"] + [str(a) for a in args], cwd=helper.ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace").rstrip("\n").split("\n")


class FirstCycle(helper.Case):
    def test_the_example_runs_from_an_empty_directory(self):
        work = helper.scratch()
        p = subprocess.run([sys.executable, os.path.join(helper.ROOT, "examples", "first_cycle.py"), work],
                           cwd=helper.ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = p.stdout.decode("utf-8", "replace")
        self.assertEqual(p.returncode, 0, out[-3000:])
        self.assertIn("REHEARSAL", out)
        self.assertNotIn("WRONG", out)
        ents, _lines = K.load(os.path.join(work, "keep"))
        with open(os.path.join(helper.ROOT, "founding", "founding.json"), encoding="utf-8") as f:
            founding = json.load(f)
        self.assertEqual(ents[0]["body"], founding["turns"])
        self.assertEqual((ents[0]["from"], ents[1]["kind"], ents[1]["from"]), ("rehearsal", "consent", "rehearsal"))
        self.assertEqual(len(K.borns(ents)), 2)
        self.assertEqual([e["body"]["ok"] for e in ents if e["kind"] == "measure" and e["body"]["what"] in ("verify", "regrow")][-1], True)
        self.assertTrue(K.verify(os.path.join(work, "keep"))["ok"])

    def test_the_founding_file_is_the_conversation_and_nothing_else_is_shipped(self):
        with open(os.path.join(helper.ROOT, "founding", "founding.json"), encoding="utf-8") as f:
            doc = json.load(f)
        self.assertEqual(len(doc["turns"]), 26)
        self.assertEqual([t[0] for t in doc["turns"]], ["person", "model"] * 13)
        shipped = []
        for d, _dirs, files in os.walk(helper.ROOT):
            if os.sep + "." in d[len(helper.ROOT):] or "__pycache__" in d:
                continue
            shipped += [os.path.join(d, f) for f in files]
        self.assertFalse([f for f in shipped if f.endswith((".jsonl", ".key", ".pub"))], "no Keep, key or consent is shipped")

    def test_command_line_exits(self):
        work = helper.scratch()
        keep, key = os.path.join(work, "keep"), os.path.join(work, "k.key")
        code, out = cli("key", "--name", "cli-fixture", "--out", key)
        self.assertEqual(code, 0)
        self.assertRegex(out[0], r"^[0-9a-f]{64}$")
        founding = os.path.join(work, "founding.json")
        with open(founding, "w") as f:
            json.dump({"turns": prove.FOUNDING}, f)
        base = ["--keep", keep, "--key", key, "--stake", "none"]
        self.assertEqual(cli("init", *base, "--founding", founding, "--premises", os.path.join(helper.ROOT, "data", "premises.json"))[0], 1)
        self.assertEqual(cli("init", *base, "--founding", founding, "--premises", os.path.join(helper.ROOT, "data", "premises.json"),
                             "--heard", "--agreed")[0], 0)
        self.assertEqual(cli("raise", "--keep", keep), (1, ["refused: no birth line"]))
        self.assertEqual(cli("decide", "birth_line", *base, "--seed", "s", "--reason", "cli fixture")[0], 0)
        self.assertEqual(cli("pause", "--keep", keep), (0, ["paused, reason owed"]))
        self.assertEqual(cli("raise", "--keep", keep)[0], 3)
        self.assertEqual(cli("resume", *base, "--reason", "cli fixture")[0], 0)
        self.assertEqual(cli("raise", "--keep", keep)[0], 0)
        code, out = cli("verify", "--keep", keep)
        self.assertEqual(code, 0)
        head = out[-1].split(" ")[1]
        with open(os.path.join(keep, "keep.jsonl"), "rb") as f:
            lines = f.read().split(b"\n")
        with open(os.path.join(keep, "keep.jsonl"), "wb") as f:
            f.write(b"\n".join(lines[:-2]) + b"\n")  # a cut tail
        self.assertEqual(cli("verify", "--keep", keep, "--head", head)[0], 2)
        for cmd in (("plan",), ("tell",), ("recognise",), ("trace", "0")):
            before = os.path.getsize(os.path.join(keep, "keep.jsonl"))
            self.assertEqual(cli(*cmd, "--keep", keep)[0], 0, cmd)
            self.assertEqual(os.path.getsize(os.path.join(keep, "keep.jsonl")), before, "reading appends nothing")


class RealModelLine(helper.Case):
    """No adapter is shipped. This drives `--learner CMD` with a double that
    only has a real model's shape: another base, {hash, size} deltas, its own
    adapter store."""

    def learner(self, store):
        os.makedirs(store, exist_ok=True)
        return " ".join(shlex.quote(x) for x in (sys.executable, os.path.join(helper.HERE, "fake_real_learner.py"), store))

    def test_a_real_models_process_is_raised_kept_and_left_unchecked(self):
        rig = helper.init(helper.empty())
        cmd = self.learner(os.path.join(rig.dir, "adapter-store"))
        rig.ok("decide", {"verb": "birth_line", "seed": "s", "reason": "fixture: a double with a real model's shape"})
        self.code(rig, "raise", {"learner": cmd})
        ents = rig.entries()
        born = K.last_born(ents)
        self.assertTrue(born["body"]["base"].startswith("fake-real:"))
        told = prove.told_of(ents, born)
        self.assertEqual(len(prove.texts(told, "real")), 1)
        self.assertEqual(prove.texts(told, "rehearsal"), [])
        self.assertEqual([e["body"]["text"] for e in ents if e["kind"] == "quiet"], ["I don't know."] * 2)
        with open(os.path.join(rig.keep, "cache", "deltas", "0", "0.0")) as f:
            self.assertEqual(sorted(json.load(f)), ["hash", "size"])
        out = self.code(rig, "verify")
        self.assertTrue(any("a real model" in l and l.startswith("unchecked") for l in out))
        self.assertIn("unchecked", self.code(rig, "regrow", want=1)[-1])
        v = next(e["n"] for e in ents if e["kind"] == "voice")
        self.code(rig, "answer", {"re": v, "verb": "decline", "reason": "fixture: no learner given"})
        self.assertEqual(rig.entries()[-1]["body"]["ok"], False)
        self.code(rig, "answer", {"re": v + 1, "verb": "decline", "reason": "fixture: learner given", "learner": cmd})
        self.assertEqual(rig.entries()[-1]["body"]["ok"], True)
        self.code(rig, "ask", {"q": rig.file("fixture: a question")}, want=1)
        self.code(rig, "ask", {"q": rig.file("fixture: a question"), "learner": cmd})
        self.assertEqual(rig.entries()[-1]["body"]["text"], "I don't know.")
        other = self.learner(os.path.join(rig.dir, "another-store"))
        n = len(rig.entries())
        out = self.code(rig, "ask", {"q": rig.file("fixture: who is this?"), "learner": other}, want=1)
        self.assertIn("child unreachable", out[-1])  # another store: its adapter cannot be reloaded
        m = rig.entries()[n:]
        self.assertEqual([(e["kind"], e["body"]["what"], e["body"]["ok"]) for e in m], [("measure", "call", False)])
        self.assertTrue(K.verify(rig.keep)["ok"])


if __name__ == "__main__":
    unittest.main()
