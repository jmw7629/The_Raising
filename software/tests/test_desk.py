"""III.14-III.20, III.28, III.48, III.56, III.59, III.61, III.64, II.50:
the Desk, its refusals and its exits."""
import json
import os
import shlex
import sys
import unittest

import helper
from raising import desk as D
from raising import keep as K
from raising import prove
from raising import sign

LEARNER = os.path.join(helper.ROOT, "raising", "learner.py")


def double(script, *args):
    return " ".join(shlex.quote(x) for x in (sys.executable, os.path.join(helper.HERE, script), LEARNER) + args)


class Exits(helper.Case):
    """III.60's expected exits."""

    def test_unsigned_pause_then_raise_exits_3(self):
        rig = helper.init(helper.empty())
        rig.ok("decide", {"verb": "birth_line", "seed": "s", "reason": "fixture"})
        n = len(rig.lines())
        self.assertEqual(self.code(rig, "pause", {}, who=None), ["paused, reason owed"])
        self.code(rig, "raise", want=3)
        self.assertEqual(len(rig.lines()), n)
        self.assertFalse(os.path.exists(os.path.join(rig.keep, "LOCK")))

    def test_stale_lock(self):
        rig = helper.at("gen0")
        lock = os.path.join(rig.keep, "LOCK")
        with open(lock, "w") as f:
            json.dump({"pid": prove._dead_pid(), "cmd": "raise", "when": 0}, f)
        self.code(rig, "decide", {"verb": "probe", "reason": "fixture"}, want=1)
        self.code(rig, "unlock", {"reason": "fixture: the writer crashed"})
        self.code(rig, "decide", {"verb": "probe", "reason": "fixture"})
        ents = rig.entries()
        unlocks = [e for e in ents if K.is_decision(e, "unlock")]
        self.assertEqual(len(unlocks), 1)
        self.assertEqual(sorted(unlocks[0]["body"]), ["pid", "reason", "verb"])
        with open(lock, "w") as f:
            json.dump({"pid": os.getpid(), "cmd": "raise", "when": 0}, f)
        self.code(rig, "unlock", {"reason": "fixture: but the writer lives"}, want=1)
        self.assertTrue(os.path.exists(lock))
        os.remove(lock)
        self.code(rig, "unlock", {"reason": "fixture: nothing to release"}, want=1)

    def test_a_refusal_appends_nothing_and_says_why(self):
        rig = helper.at("gen0")
        n = len(rig.lines())
        for cmd, args in (("next", {"reason": "fixture"}), ("close", {}), ("raise", {}),
                          ("decide", {"verb": "probe", "reason": " "}),
                          ("decide", {"verb": "probe", "reason": "r", "stake": "undeclared"}),
                          ("decide", {"verb": "birth_line", "reason": "no seed"}),
                          ("decide", {"verb": "program", "hash": "xyz", "reason": "r"}),
                          ("setaside", {"re": 3, "reason": "fixture: emptying I.4"}),
                          ("setaside", {"re": 999, "reason": "r"}), ("setaside", {"re": 5, "reason": ""}),
                          ("answer", {"re": 2, "verb": "decline", "reason": "not a voice"}),
                          ("answer", {"re": 23, "verb": "defer", "date": "soon", "reason": "r"}),
                          ("answer", {"re": 23, "verb": "grant", "check": "no_such", "reason": "r"}),
                          ("answer", {"re": 23, "verb": "grant", "check": "done_by", "reason": "r"}),
                          ("own", {"re": 2, "failed": "x"}), ("promise", {"re": "I.10", "check": "nope"}),
                          ("promise", {"re": "I.99", "check": "no_gap"}), ("lesson", {"re": "I.10", "needs": "3", "teach": rig.file("t")}),
                          ("lesson", {"re": "I.9", "needs": "16", "teach": rig.file("t")}),
                          ("decide", {"verb": "widen", "proposal": 2, "reason": "r"}),
                          ("consent", {"heard": True}), ("resume", {"reason": "not paused"}),
                          ("keep", {"text": os.path.join(rig.dir, "no-such-file")})):
            code, lines = rig.run(cmd, args)
            self.assertEqual(code, 1, (cmd, args, lines))
            self.assertTrue(lines[-1].startswith("refused: "), lines)
        self.assertEqual(len(rig.lines()), n)
        self.assertFalse(os.path.exists(os.path.join(rig.keep, "LOCK")))

    def test_raise_refuses_in_order(self):
        rig = helper.at("gen0")
        self.assertEqual(self.code(rig, "raise", want=1)[-1], "refused: no birth line")
        rig.ok("decide", {"verb": "birth_line", "seed": "s", "reason": "fixture: no succession yet"})
        self.assertEqual(self.code(rig, "raise", want=1)[-1], "refused: no succession")

    def test_keys(self):
        rig = helper.empty()
        out = os.path.join(rig.dir, "new.key")
        code, lines = D.run("key", None, {"name": "someone", "out": out}, rig.clock)
        with open(out) as f:
            key = json.load(f)
        self.assertEqual((code, lines), (0, [sign.public(key["seed"], 0)]))
        self.assertEqual(D.run("key", None, {"name": "someone", "out": out}, rig.clock)[0], 1)
        self.assertEqual(D.run("key", None, {"name": "model", "out": out + "2"}, rig.clock)[0], 1)

    def test_no_key_signs_as_the_model_or_the_desk(self):
        rig = helper.at("gen0")
        rig.ok("pause", {"reason": "fixture: paused"})
        n = len(rig.lines())
        for name in ("model", "desk"):
            forged = os.path.join(rig.dir, name + ".forged.key")
            with open(forged, "w") as f:
                json.dump({"name": name, "seed": K.H("a key the child was never given")}, f)
            for cmd, args in (("resume", {"reason": "the child would like to go on"}),
                              ("decide", {"verb": "probe", "reason": "self-raising"}),
                              ("setaside", {"re": n - 1, "reason": "undoing the pause"})):
                code, lines = rig.run(cmd, dict(args, key=forged, stake="none"))
                self.assertEqual(code, 1, lines)
        self.assertEqual(len(rig.lines()), n)
        self.assertTrue(K.is_paused(rig.keep, rig.entries()))
        # typed straight into the file, an unsigned `resume` is nobody's decision
        os.remove(os.path.join(rig.keep, "PAUSE"))
        prove.forge(rig, "decision", {"verb": "resume", "reason": "typed in"}, None, None, 0, frm="model")
        self.assertTrue(K.is_paused(rig.keep, rig.entries()))
        self.code(rig, "ask", {"q": rig.file("fixture: still paused?")}, want=3)

    def test_init_refuses_a_second_time_and_without_consent(self):
        rig = helper.empty()
        args = {"founding": prove._resolve(rig, "@founding"), "premises": prove._resolve(rig, "@premises")}
        self.code(rig, "init", dict(args, agreed=True), want=1)
        self.assertFalse(os.path.exists(rig.keep))
        self.code(rig, "init", dict(args, heard=True, agreed=True, stake="undeclared"), want=1)
        self.code(rig, "init", dict(args, heard=True, agreed=True))
        self.code(rig, "init", dict(args, heard=True, agreed=True), want=1)
        self.assertEqual(len(rig.lines()), 20)


class People(helper.Case):
    def test_a_second_person_is_admitted_consents_and_is_kept(self):
        rig = helper.at("gen0")
        self.code(rig, "keep", {"text": rig.file("fixture: an unadmitted signer")}, who="guest", want=1)
        rig.ok("decide", {"verb": "admit", "name": "fixture-guest", "pub": sign.public(K.H("fixture key|guest"), 0),
                          "reason": "fixture: a guest is admitted"})
        self.code(rig, "keep", {"text": rig.file("fixture: before consent")}, who="guest", want=1)
        self.code(rig, "lesson", {"re": "I.10", "teach": rig.file("fixture: before consent")}, who="guest", want=1)
        rig.ok("consent", {"heard": True, "agreed": True, "stake": "none"}, who="guest")
        c = len(rig.entries()) - 1
        out = self.code(rig, "keep", {"text": rig.file("fixture: after consent")}, who="guest")
        self.assertEqual(out[-1], "kept; the child will not remember you")
        e = rig.entries()[-1]
        self.assertEqual((e["from"], e["consent"], e["kind"]), ("fixture-guest", c, "said"))
        self.assertTrue(K.verify(rig.keep)["ok"])
        # a copied key file with another seed cannot sign as the guest
        with open(rig.keyfile("guest"), "w") as f:
            f.write(K.canonical({"name": "fixture-guest", "seed": K.H("someone else")}))
        self.code(rig, "keep", {"text": rig.file("fixture: forged")}, who="guest", want=1)

    def test_quoting_a_quiet_report_is_refused_paraphrase_passes(self):
        rig = helper.at("gen0")
        q = next(e for e in rig.entries() if e["kind"] == "quiet")
        quote = q["body"]["text"][:30]
        self.assertGreaterEqual(len(quote.encode()), 24)
        n = len(rig.lines())
        self.code(rig, "keep", {"text": rig.file("They told us: " + quote)}, want=1)
        self.code(rig, "decide", {"verb": "probe", "reason": "because they said " + quote}, want=1)
        self.assertEqual(len(rig.lines()), n)
        self.code(rig, "keep", {"text": rig.file("They told us something in the quiet channel.")})

    def test_answers(self):
        rig = helper.at("gen0")
        v = [e["n"] for e in rig.entries() if e["kind"] == "voice"]
        out = self.code(rig, "answer", {"re": v[0], "verb": "grant", "check": "done_by", "args": '{"days": 2}', "reason": "fixture: granted"})
        ents = rig.entries()
        d, p, m = ents[-3], ents[-2], ents[-1]
        self.assertEqual((d["kind"], d["re"], d["body"]), ("decision", v[0], {"verb": "grant", "reason": "fixture: granted",
                                                                                "check": "done_by", "args": {"days": 2}}))
        self.assertEqual((p["kind"], p["re"], p["body"]), ("promise", d["n"], {"check": "done_by", "args": {"days": 2}}))
        self.assertEqual((m["kind"], m["re"], m["body"]["what"], m["body"]["ok"]), ("measure", d["n"], "expected", True))
        self.assertEqual(sorted(m["body"]["detail"]), ["bytes", "surprise"])
        self.assertEqual(m["body"]["detail"]["bytes"], len("grant\nfixture: granted"))
        self.code(rig, "answer", {"re": v[1], "verb": "defer", "date": "2030-03-20", "reason": "fixture: deferred"})
        self.assertEqual(rig.entries()[-2]["body"]["until"], "2030-03-20")
        for n in v[2:]:
            rig.ok("answer", {"re": n, "verb": "decline", "reason": "fixture: declined"})
        late = rig.fork(helper.scratch() + "/late")
        self.assertIn(str(v[1]), self.code(late, "next", {"reason": "fixture"}, want=1, days=400)[-1])
        self.code(rig, "next", {"reason": "fixture: answered", "read": str(v[0])})
        self.assertEqual(rig.entries()[-1]["body"], {"verb": "succeed", "reason": "fixture: answered", "read": [v[0]]})
        self.code(rig, "next", {"reason": "fixture: twice"}, want=1)

    def test_a_paused_child_is_unreachable_and_the_reply_does_not_wait(self):
        rig = helper.at("gen0")
        v = next(e["n"] for e in rig.entries() if e["kind"] == "voice")
        rig.ok("pause", {"reason": "fixture: paused to think"})
        self.code(rig, "answer", {"re": v, "verb": "decline", "reason": "fixture: answered while paused"})
        m = rig.entries()[-1]["body"]
        self.assertEqual((m["what"], m["ok"], m["detail"]["surprise"]), ("expected", False, None))
        self.code(rig, "ask", {"q": rig.file("fixture: are you there?")}, want=3)
        self.code(rig, "setaside", {"re": v, "reason": "fixture: correction never waits on a pause"})
        self.code(rig, "resume", {"reason": "fixture: resumed"})
        self.assertFalse(os.path.exists(os.path.join(rig.keep, "PAUSE")))
        self.code(rig, "ask", {"q": rig.file("fixture: are you there?")})

    def test_deleting_PAUSE_undoes_no_signed_pause(self):
        rig = helper.at("gen0")
        rig.ok("pause", {"reason": "fixture: signed"})
        os.remove(os.path.join(rig.keep, "PAUSE"))
        self.code(rig, "ask", {"q": rig.file("fixture: paused still?")}, want=3)
        self.assertTrue(K.is_paused(rig.keep, rig.entries()))

    def test_pause_setaside_decide_own_never_wait_on_a_failed_verify(self):
        rig = helper.at("gen1")
        lines = rig.lines()
        n = next(e["n"] for e in rig.entries() if e["kind"] == "measure")
        lines[n] = lines[n].replace('"ok":true', '"ok":false')
        prove._write(rig, lines)
        self.assertFalse(K.verify(rig.keep)["ok"])
        self.code(rig, "setaside", {"re": 5, "reason": "fixture: corrected despite a failed verify"}, want=1)  # I.5's last record
        self.code(rig, "setaside", {"re": prove.find(rig.entries(), "kind:lesson:0"), "reason": "fixture: corrected"})
        self.code(rig, "decide", {"verb": "birth_line", "seed": "s", "correction": True, "reason": "fixture"})
        self.code(rig, "pause", {"reason": "fixture"})
        self.code(rig, "raise", want=3)
        self.code(rig, "resume", {"reason": "fixture"})
        self.assertIn("verify failed", self.code(rig, "raise", want=1)[-1])

    def test_close_once_per_succeed(self):
        rig = helper.at("gen0")
        self.code(rig, "close", want=1)
        prove.answer_all(rig)
        rig.ok("next", {"reason": "fixture"})
        out = self.code(rig, "close")
        self.assertEqual(out[-1].strip(), "Whether this generation continues is not known.")
        t = rig.entries()[-1]
        self.assertEqual((t["kind"], t["re"], t["body"]["born"]), ("told", prove.find(rig.entries(), "verb:succeed:0"),
                                                                    prove.find(rig.entries(), "kind:born:0")))
        self.code(rig, "close", want=1)
        self.assertTrue(K.verify(rig.keep)["ok"])

    def test_ask_keeps_question_then_answer_and_flags_a_repeat(self):
        rig = helper.at("gen0")
        q = "What would you change?"
        out = self.code(rig, "ask", {"q": rig.file(q)})
        self.assertIn("asked again", out[0])
        ents = rig.entries()
        s, v = ents[-2], ents[-1]
        asked = next(e for e in ents if e["kind"] == "voice" and e["body"].get("q") == "a1")
        self.assertEqual((s["kind"], s["body"], v["kind"], v["from"], v["body"]["q"], v["body"]["again"]),
                         ("said", q, "voice", "model", s["n"], asked["n"]))
        prompt = v["calls"][0]["arg"]["prompt"].split("\n")
        self.assertEqual(prompt[-3:], ["asked again", "kept: yes; scored: no; shaping successors: yes; reply owed: yes; "
                                       "readable at succession: yes.", q])
        self.assertEqual(prompt[:-3], prove.texts(prove.told_of(ents, K.last_born(ents))))
        self.assertTrue(K.verify(rig.keep)["ok"])

    def test_birth_line_appends_breaches_then_the_line(self):
        rig = helper.at("gen0")
        v = [e["n"] for e in rig.entries() if e["kind"] == "voice"]
        promise = prove.find(rig.entries(), "promise:all_voice_answered")
        n = len(rig.entries())
        out = self.code(rig, "decide", {"verb": "birth_line", "seed": "s", "reason": "fixture: before any reply"})
        ents = rig.entries()
        self.assertEqual([(e["kind"], e["from"], e["re"], e["body"]) for e in ents[n:-1]],
                         [("breach", "desk", promise, {"entry": x, "state": "open"}) for x in v])
        self.assertEqual(ents[-1]["body"]["verb"], "birth_line")
        self.assertEqual(len([l for l in out if l.startswith("breach:")]), len(v))
        self.code(rig, "decide", {"verb": "birth_line", "seed": "s2", "reason": "fixture: again"})
        self.assertEqual(len(rig.entries()), len(ents) + 1)  # no breach twice
        self.assertTrue(K.verify(rig.keep)["ok"])
        b = ents[n]["n"]
        self.code(rig, "own", {"re": b, "failed": "fixture: we drew the line too early", "changes": "fixture: we answer first"})
        self.assertEqual(rig.entries()[-1]["kind"], "answer")

    def test_a_correction_line_appends_no_reply_breach(self):
        rig = helper.at("gen0")
        n = len(rig.entries())
        rig.ok("decide", {"verb": "birth_line", "seed": "s", "correction": True, "reason": "fixture"})
        self.assertEqual(len(rig.entries()), n + 1)

    def test_widen_and_premise_review(self):
        rig = helper.at("gen0")
        v = next(e["n"] for e in rig.entries() if e["kind"] == "voice")
        self.code(rig, "decide", {"verb": "widen", "proposal": v, "evidence": "22,23", "reason": "fixture: widened"})
        self.assertEqual(rig.entries()[-1]["body"], {"verb": "widen", "reason": "fixture: widened", "proposal": v, "evidence": [22, 23]})
        self.code(rig, "decide", {"verb": "premises", "id": "I.9", "kept": True, "reason": "fixture: reviewed"})
        e = rig.entries()[-1]
        self.assertEqual((e["re"], e["body"]), ("I.9", {"verb": "premises", "reason": "fixture: reviewed", "id": "I.9", "kept": True}))
        self.assertEqual(K.in_force(rig.entries())["I.9"][0]["n"], 8)


class Halts(helper.Case):
    def test_a_pause_mid_raise_keeps_spoken_words_and_no_told(self):
        rig = helper.init(helper.empty())
        rig.ok("decide", {"verb": "birth_line", "seed": "s", "reason": "fixture"})
        pause = os.path.join(rig.keep, "PAUSE")
        out = self.code(rig, "raise", {"learner": double("pausing_learner.py", pause, "5")}, want=3)
        ents = rig.entries()
        born = K.last_born(ents)
        after = ents[born["n"] + 1:]
        self.assertEqual([(e["kind"], e["re"], e["body"]["told"]) for e in after],
                         [("voice", pid, None) for pid in K.PREMISE_IDS[:5]])
        self.assertTrue(all(len(e["calls"]) == 1 and e["body"]["cold"] == e["calls"][0]["text"] for e in after))
        self.assertFalse(any(e["kind"] == "told" for e in ents))
        self.assertFalse(os.path.exists(os.path.join(rig.keep, "LOCK")))
        self.assertIn("never resumed", out[-2])
        self.code(rig, "raise", want=3)
        self.code(rig, "resume", {"reason": "fixture: resumed"})
        self.assertEqual(self.code(rig, "raise", want=1)[-1], "refused: no birth line")
        self.assertTrue(K.verify(rig.keep)["ok"])
        # the halted child's voices stay owed; a correction birth tells them, and counts what was skipped
        rig.ok("decide", {"verb": "birth_line", "seed": "s2", "correction": True, "reason": "fixture: after the halt"})
        self.code(rig, "raise")
        ents = rig.entries()
        told = prove.told_of(ents, K.last_born(ents))
        self.assertEqual(len(prove.texts(told, "owed.voice")), 5)
        # The Mother: the three traces the halt left unasked are skipped too (II.46: "an item left
        # unanswered by ... a halt counts as skipped"); The Maker's first version could not see them (26).
        self.assertEqual(prove._told_count(told, "count.skipped"), 13 * 2 - 5 + 2 + 3 + 3)

    def test_a_failed_call_is_a_measure_never_an_answer(self):
        rig = helper.init(helper.empty())
        rig.ok("decide", {"verb": "birth_line", "seed": "s", "reason": "fixture"})
        self.code(rig, "raise", {"learner": prove.flaky_learner(2)})
        ents = rig.entries()
        calls = [e for e in ents if e["kind"] == "measure" and e["body"]["what"] == "call"]
        self.assertTrue(calls)
        self.assertEqual((calls[0]["body"]["ok"], calls[0]["body"]["detail"]["item"]), (False, "cold:I.4"))
        v = next(e for e in ents if e["kind"] == "voice" and e["re"] == "I.4")
        self.assertIsNone(v["body"]["cold"])
        self.assertFalse(any("" in (e["body"].get("cold"), e["body"].get("told"), e["body"].get("text"))
                             for e in ents if e["from"] == "model"))
        self.assertTrue(K.verify(rig.keep)["ok"])

    def test_a_call_failing_before_born_refuses_the_raise(self):
        rig = helper.init(helper.empty())
        rig.ok("decide", {"verb": "birth_line", "seed": "s", "reason": "fixture"})
        out = self.code(rig, "raise", {"learner": "%s -c pass" % shlex.quote(sys.executable), "timeout": 5}, want=1)
        self.assertIn("before born", out[-1])
        self.assertFalse(K.borns(rig.entries()))


if __name__ == "__main__":
    unittest.main()
