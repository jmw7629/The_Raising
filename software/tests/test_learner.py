"""III.9, III.10, III.30, III.59, III.60: the built-in learner and its line."""
import re
import sys
import unittest

import helper
from raising import bench as B
from raising import learner as LR
from raising import plan as P


def said(target, key="people|said|", context="", mask=()):
    return {"frame": "", "context": context, "target": target, "key": key, "mask": [list(m) for m in mask]}


class Vector(helper.Case):
    def check(self, m):
        self.assertEqual(m.report("surprise", "aa"), "?")
        self.assertEqual(m.speak("x", None), "\x00" * 200)
        self.assertEqual(P.cls(m.speak("x", None)), "no_answer")
        self.assertEqual(m.speak("x", "mnd?"), "?")
        got = m.learn(said("aa"), False)
        self.assertEqual((got["surprise"], got["shift"]), (3072, 130))
        digit = B.digit(got["surprise"], 2)
        self.assertEqual(digit, "b")
        m.learn(said(digit, "me|report|surprise", "aa"), False)
        self.assertEqual(m.report("surprise", "aa"), "b")
        self.assertEqual(m.report("surprise", "ab"), "?")

    def test_L(self):
        self.assertEqual(LR.L(3), 384)
        self.assertEqual(LR.L(1), 0)
        self.assertEqual(LR.L(256), 2048)

    def test_in_process(self):
        self.check(LR.BuiltIn())

    def test_over_the_line(self):
        child = B.Child(None, 20)
        try:
            self.assertEqual(child.start("vector", None), "builtin")
            self.check(child)
        finally:
            child.close()


class Arithmetic(helper.Case):
    def test_dry_changes_nothing(self):
        m = LR.BuiltIn()
        m.learn(said("hello there"), False)
        fp = m.fingerprint()
        dry = m.learn(said("hello there"), True)
        self.assertEqual(m.fingerprint(), fp)
        self.assertEqual((dry["shift"], dry["delta"]), (0, []))
        self.assertLess(dry["surprise"], LR.BuiltIn().learn(said("hello there"), True)["surprise"])

    def test_masked_bytes_are_not_learned(self):
        a, b = LR.BuiltIn(), LR.BuiltIn()
        da = a.learn(said("abcdefgh", mask=[(2, 6)]), False)
        self.assertEqual(sorted(set(r[2] for r in da["delta"])), sorted(b"abgh"))
        self.assertEqual(a.learn(said("abcdefgh", mask=[(0, 8)]), False)["surprise"], 0)

    def test_context_is_read_never_learned(self):
        m = LR.BuiltIn()
        fp = m.fingerprint()
        got = m.learn({"frame": "1,0,x,said,none", "context": "some context", "target": "", "key": "people|said|none",
                       "mask": []}, False)
        self.assertEqual((got["surprise"], got["shift"], m.fingerprint()), (0, 0, fp))

    def test_deltas_sum_to_the_weights(self):
        m, cells = LR.BuiltIn(), {}
        for t in ("first words", "second words", "first words"):
            B.add_rows(cells, m.learn(said(t, "people|said|personal"), False)["delta"])
        rows = B.rows_of(cells)
        self.assertEqual(rows, m.weights())
        self.assertEqual(B.fingerprint_of(rows), m.fingerprint())
        again = LR.BuiltIn()
        again.start("s", rows)
        self.assertEqual(again.fingerprint(), m.fingerprint())

    def test_reports_touch_framed_rows_only(self):
        m = LR.BuiltIn()
        d = m.learn(said("7", "me|report|shift", "abcd"), False)
        self.assertEqual(set(r[0] for r in d["delta"]), {"framed"})
        self.assertEqual(len(d["delta"]), 5)
        self.assertEqual(m.speak("abcd\n", None), "\x00" * 200)  # speak scores the shared table alone

    def test_speak_echoes_people_and_stops_at_newline(self):
        m = LR.BuiltIn()
        for _ in range(3):
            m.learn(said("ask: yes, kept\n"), False)
        self.assertEqual(m.speak("ask:", None), " yes, kept")
        self.assertIn(m.speak("ask:", "yn"), "yn")

    def test_learner_opens_no_file_and_imports_no_desk_code(self):
        with open(LR.__file__, encoding="utf-8") as f:
            src = f.read()
        code = re.sub(r'"""(?:.|\n)*?"""', "", src)
        self.assertEqual(set(re.findall(r"^\s*(?:import|from)\s+([.\w]+)", code, re.M)), {"hashlib", "json", "sys"})
        self.assertIsNone(re.search(r"\bopen\s*\(", code))


class Line(helper.Case):
    def test_a_failed_call_is_said_and_the_process_lives(self):
        child = B.Child(None, 20)
        try:
            child.start("s", None)
            with self.assertRaises(B.CallFailed):
                child.call("forget_everything")
            self.assertEqual(len(child.fingerprint()), 64)
        finally:
            child.close()

    def test_a_call_that_outlasts_the_timeout_fails(self):
        child = B.Child("%s -c 'import time; time.sleep(30)'" % sys.executable, 0.5)
        try:
            with self.assertRaises(B.CallFailed):
                child.start("s", None)
        finally:
            child.close()

    def test_frozen_at_birth(self):
        child = B.Child(None, 20)
        try:
            child.start("s", None)
            child.freeze()
            with self.assertRaises(helper.K.Refused):
                child.learn(said("after birth"), False)
            self.assertGreater(child.learn(said("after birth"), True)["surprise"], 0)
        finally:
            child.close()

    def test_the_learner_runs_in_an_empty_directory(self):
        import os
        child = B.Child(None, 20)
        try:
            child.start("s", None)
            self.assertEqual(os.listdir(child.dir), [])
        finally:
            child.close()


if __name__ == "__main__":
    unittest.main()
