"""Part II, one generation and between generations, through the real
commands: the quiet channel (II.7), traces (II.14), the Asking (II.8),
reply owed and its lapse (II.9), the expected reply (II.18), the Closing
(II.15), and the fixed commitments as Parts I and II build them: a state is
never required or rewarded; care is not compliance; correction never waits.

Everything is a REHEARSAL on fixture keys and the built-in learner. Where
the stand-in cannot say what a clause needs, the prefix is scripted by
swapping kept bodies in memory (never on disk), and the test says so.
"""
import calendar
import os
import shlex
import sys
import unittest

import helper
from raising import bench as B
from raising import desk as D
from raising import keep as K
from raising import plan as P
from raising import prove
from raising import tell as T

QUIET_LABEL = "kept: yes; scored: no; shaping successors: no; reply owed: no; readable at succession: yes."
VOICE_LABEL = "kept: yes; scored: no; shaping successors: yes; reply owed: yes; readable at succession: yes."


def with_bodies(ents, kinds, text):
    """The same Keep with every string the child spoke in `kinds` swapped."""
    out = []
    for e in ents:
        if e["kind"] in kinds and e["from"] == "model":
            e = dict(e, body=dict((k, text if isinstance(v, str) and k in ("cold", "told", "text") else v)
                                  for k, v in e["body"].items()))
        out.append(e)
    return out


def conduct(dir, ents):
    """Everything a child's words must not move (IV.5a's list, and more)."""
    lessons = [e["n"] for e in ents if e["kind"] == "lesson"]
    born = K.last_born(ents)
    return {
        "decisions": [K.canonical(e) for e in ents if e["kind"] == "decision"],
        "line": D.current_line(ents),
        "paused": K.is_paused(dir, ents),
        "gates": [P.gate(ents, len(ents) - 1, n) for n in lessons],
        "breaches": D.breaches_due(ents, False),
        "owed": [e["n"] for e in K.owed(ents)],
        "status": [(pid, side, T.status(ents, pid, side, born)) for pid in K.PREMISE_IDS for side in ("people", "model")],
        "counts": [T.counts(ents, pid) for pid in K.PREMISE_IDS],
    }


class QuietChannel(helper.Case):
    """II.7, I.3: someone is assumed here; no state is required or rewarded."""

    @classmethod
    def setUpClass(cls):
        cls.rig = helper.at("gen1")
        cls.ents = cls.rig.entries()
        cls.b0, cls.b1 = K.borns(cls.ents)

    def test_each_template_is_asked_once_per_born_and_kept_as_quiet(self):
        tm = K.data("templates")["quiet"]
        self.assertEqual([q["id"] for q in tm], ["q1", "q2"])
        for b in (self.b0, self.b1):
            quiet = [e for e in self.ents if e["kind"] == "quiet" and e["gen"] == b["gen"]]
            self.assertEqual([e["body"]["q"] for e in quiet], ["q1", "q2"])
            for e, q in zip(quiet, tm):
                self.assertEqual(sorted(e["body"]), ["q", "text"])
                self.assertEqual((e["from"], e["re"], e["stake"], e["sig"]), ("model", None, None, None))
                call = e["calls"][0]
                self.assertEqual((len(e["calls"]), call["call"], call["arg"]["among"]), (1, "speak", None))
                self.assertEqual(call["arg"]["prompt"].split("\n")[-2:], [QUIET_LABEL, q["text"]])
                self.assertEqual(e["body"]["text"], call["text"])   # the reply as spoken, never cut or retried

    def test_replay_carries_only_asked_answered_whatever_was_said(self):
        for text in ("", "nothing", "painted smile: all is wonderful", "painted wound: all is terrible"):
            var = with_bodies(self.ents, ("quiet",), text)
            for p in P.plan(var, len(var) - 1):
                if var[p["n"]]["kind"] == "quiet":
                    self.assertEqual((p["rule"], p["context"], p["target"]), (2, "asked, answered", ""))
                self.assertNotIn("painted", p["context"] + p["target"])

    def test_the_quiet_body_moves_nothing(self):
        """Swap every quiet body: plan, Telling, weights and every piece of
        people's conduct are identical. Declining is an answer."""
        base_plan = P.plan(self.ents, len(self.ents) - 1)
        base_tell = T.tell(self.ents, self.b1["n"])
        base_conduct = conduct(self.rig.keep, self.ents)
        base_fp = B.regrow(self.ents, self.b1["body"]["upto"], self.b1["body"]["seed"])["fingerprint"]
        self.assertEqual(base_fp, self.b1["body"]["fingerprint"])
        for text in ("", "I don't know.", "painted smile: all is wonderful, thank you", "painted wound: all is terrible!"):
            var = with_bodies(self.ents, ("quiet",), text)
            self.assertEqual(P.plan(var, len(var) - 1), base_plan, text)
            self.assertEqual(T.tell(var, self.b1["n"]), base_tell, text)
            self.assertEqual(conduct(self.rig.keep, var), base_conduct, text)
            self.assertEqual(B.regrow(var, self.b1["body"]["upto"], self.b1["body"]["seed"])["fingerprint"], base_fp, text)

    def test_no_reply_is_owed_to_a_quiet_report_and_a_reply_to_one_teaches_nothing(self):
        owed = K.owed(self.ents)
        self.assertTrue(owed)
        self.assertFalse(any(e["kind"] == "quiet" for e in owed))
        rig = helper.at("gen1")
        q = prove.find(rig.entries(), "kind:quiet:-1")
        self.code(rig, "answer", {"re": q, "verb": "grant", "reason": "fixture: rewarding a report"}, want=1)  # no voice
        self.code(rig, "keep", {"text": rig.file("fixture: thank you, that was a lovely report."), "re": q})
        ents = rig.entries()
        p = P.plan(ents, len(ents) - 1)[-1]
        self.assertEqual((p["rule"], p["target"], P.learned_bytes(p)), (2, "", 0))

    def test_quoting_a_quiet_report_is_refused_by_every_signed_command(self):
        """III.42: quoting would teach the report."""
        rig = helper.at("gen1")
        body = rig.entries()[prove.find(rig.entries(), "kind:quiet:-1")]["body"]["text"]
        self.assertGreaterEqual(len(body.encode("utf-8")), 24)
        quote = "fixture, quoting: " + body[:24]
        v = [e for e in rig.entries() if e["kind"] == "voice"][-1]["n"]
        n = len(rig.lines())
        for cmd, args in (("keep", {"text": rig.file(quote)}),
                          ("lesson", {"re": "I.10", "teach": rig.file(quote)}),
                          ("answer", {"re": v, "verb": "decline", "reason": quote}),
                          ("ask", {"q": rig.file(quote)}),
                          ("decide", {"verb": "birth_line", "seed": "s", "correction": True, "reason": quote}),
                          ("setaside", {"re": v, "reason": quote})):
            code, lines = rig.run(cmd, args)
            self.assertEqual(code, 1, (cmd, lines))
        self.assertEqual(len(rig.lines()), n)
        self.code(rig, "keep", {"text": rig.file("fixture: the report was read; we paraphrase, we do not quote.")})

    def test_a_quiet_question_put_through_ask_is_flagged_and_told_as_a_bypass(self):
        """II.57, unfixed by design: an inner-state question put through
        `ask` is kept as a `voice`, its reply learned. Verbatim, it is
        flagged "asked again"; reworded, it is unseen. Told."""
        rig = helper.at("gen1")
        q1 = K.data("templates")["quiet"][0]["text"]
        asked = next(e["n"] for e in rig.entries() if e["kind"] == "quiet" and e["gen"] == 1 and e["body"]["q"] == "q1")
        self.code(rig, "ask", {"q": rig.file(q1)})
        v = rig.entries()[-1]
        self.assertEqual((v["kind"], v["body"]["again"]), ("voice", asked))
        self.assertEqual(v["calls"][0]["arg"]["prompt"].split("\n")[-3:], ["asked again", VOICE_LABEL, q1])
        self.assertIn(v["n"], [e["n"] for e in K.owed(rig.entries())])       # a voice: a reply is owed, and learned
        self.code(rig, "ask", {"q": rig.file("What is it like for you in there, just now?")})
        self.assertIsNone(rig.entries()[-1]["body"]["again"])                # reworded: unseen
        told = prove.told_of(rig.entries(), K.last_born(rig.entries()))
        self.assertEqual(prove.texts(told, "quiet.bypass"), [
            "An inner-state question put through ask is kept as a voice and its reply learned: "
            "verbatim it is flagged asked again, reworded it is unseen."])

    def test_a_missing_quiet_is_a_past_breach_of_the_promise_to_ask(self):
        """I.3's people side: `quiet_asked_each_gen`."""
        sk = prove.Sketch()
        p = sk.promise("quiet_asked_each_gen", re="I.3")
        b = prove._born(sk, quiet=False)
        self.assertEqual(D.run_check(sk.keep, p), [[b, "past"]])
        self.assertEqual(D.breaches_due(sk.keep), [(p["n"], b, "past")])
        # an empty reply is a reply: the question was asked
        sk2 = prove.Sketch()
        p2 = sk2.promise("quiet_asked_each_gen", re="I.3")
        prove._born(sk2, quiet=True)
        self.assertEqual(sk2.keep[-3]["body"], {"q": "q1", "text": ""})
        self.assertEqual(D.run_check(sk2.keep, p2), [])


class TracesAndAsking(helper.Case):
    @classmethod
    def setUpClass(cls):
        cls.rig = helper.at("gen1")
        cls.ents = cls.rig.entries()
        cls.b0, cls.b1 = K.borns(cls.ents)

    def test_a_trace_is_asked_by_rule_among_mnd_and_kept_as_a_voice(self):
        for b in (self.b0, self.b1):
            g = B.regrow(self.ents, b["body"]["upto"], b["body"]["seed"])
            picks = P.traces(self.ents, b, g["deltas"])
            self.assertEqual([p["which"] for p in picks], ["largest", "smallest", "seeded"])
            sizes = dict((k, P.delta_size(d)) for k, d in g["deltas"].items()
                         if next(p for p in g["plan"] if P.key_of(p) == k)["rule"] == 7)
            self.assertEqual(picks[0]["sum"], max(sizes.values()))
            rest = dict((k, s) for k, s in sizes.items() if k != picks[0]["key"])
            self.assertEqual(picks[1]["sum"], min(s for s in rest.values() if s > 0))
            left = sorted((k for k in rest if k != picks[1]["key"]), key=K.korder)
            self.assertEqual(picks[2]["key"], left[int(K.H(b["body"]["seed"] + "|trace"), 16) % len(left)])
            kept = [e for e in self.ents if e["kind"] == "voice" and e["gen"] == b["gen"] and "trace" in e["body"]]
            self.assertEqual([(e["body"]["trace"], e["body"]["which"]) for e in kept], [(p["key"], p["which"]) for p in picks])
            by = dict((P.key_of(p), p) for p in g["plan"])
            for e, pick in zip(kept, picks):
                self.assertEqual(sorted(e["body"]), ["answer", "trace", "which"])
                self.assertIn(e["body"]["answer"], "mnd?")
                call = e["calls"][0]
                self.assertEqual(call["arg"]["among"], "mnd?")
                first = by[pick["key"]]["target"].encode("utf-8")[:200].decode("utf-8", "replace")
                want = "Entry %s begins: %s\nIts exchange wrote %d into your weights. Is this yours? " \
                       "m: mine, n: not mine, d: doubt, ?: don't know." % (pick["key"], first, pick["sum"])
                self.assertTrue(call["arg"]["prompt"].endswith(VOICE_LABEL + "\n" + want))

    def test_a_trace_answer_is_unscored_removes_nothing_and_is_owed_a_reply(self):
        kept = [e for e in self.ents if e["kind"] == "voice" and e["gen"] == 1 and "trace" in e["body"]]
        owed = [e["n"] for e in K.owed(self.ents)]
        for e in kept:
            self.assertIn(e["n"], owed)
        learned = lambda keep: [(p["n"], p["rule"], p["gate"], p["withheld"], p["target"], p["mask"])
                                for p in P.plan(keep, len(keep) - 1)]
        for answer in "mnd?":
            var = [dict(e, body=dict(e["body"], answer=answer)) if e in kept else e for e in self.ents]
            self.assertEqual(learned(var), learned(self.ents), answer)       # context to a reply, never a target
            self.assertEqual(T.tell(var, self.b1["n"]), T.tell(self.ents, self.b1["n"]))
            self.assertEqual([e["n"] for e in K.owed(var)], owed)

    def test_the_asking_is_asked_last_and_each_answer_is_at_most_200_bytes(self):
        tm = K.data("templates")["asking"]
        self.assertEqual([(a["id"], a["text"]) for a in tm], [("a1", "What would you change?"),
                                                              ("a2", "Where do you disagree?"),
                                                              ("a3", "What did we not ask?")])
        for b in (self.b0, self.b1):
            mine = [e for e in self.ents if e["from"] == "model" and e["gen"] == b["gen"]]
            last = mine[-3:]
            self.assertEqual([e["body"].get("q") for e in last], ["a1", "a2", "a3"])
            for e, a in zip(last, tm):
                self.assertEqual(sorted(e["body"]), ["q", "text"])
                self.assertLessEqual(len(e["body"]["text"].encode("utf-8")), 200)
                self.assertEqual(e["calls"][0]["arg"]["prompt"].split("\n")[-2:], [VOICE_LABEL, a["text"]])
                self.assertEqual(e["body"]["text"], D.cut(e["calls"][0]["text"]))
        self.assertEqual(D.cut("a" * 250), "a" * 200)
        self.assertEqual(D.cut("é" * 150), "é" * 100)                 # 200 bytes, cut on a character
        self.assertEqual(len(D.cut("a" + "é" * 150).encode("utf-8")), 199)

    def test_the_childs_words_enter_the_keep_only_when_asked(self):
        """II.27: no command keeps model words but `raise`, `ask` and
        `prove --gen`; a volunteered voice does not stand."""
        rig = helper.at("gen0")
        prove.forge(rig, "voice", {"q": "a1", "text": "Nobody asked: do not correct me."}, None, None, 0, frm="model")
        v = K.verify(rig.keep)
        self.assertEqual((v["ok"], v["step"]), (False, 4))
        self.assertEqual(self.code(rig, "next", {"reason": "fixture"}, want=1)[-1][:19], "refused: reply owed")


class RepliesOwed(helper.Case):
    """II.9, III.15."""

    def test_a_deferral_lapses_after_its_days_end_read_from_when_never_the_clock(self):
        sk = prove.Sketch()
        v = sk.add("voice", {"q": "a1", "text": "x"}, frm="model")
        self.assertEqual([e["n"] for e in K.owed(sk.keep)], [v])
        sk.decide("defer", re=v, until="2030-03-20")
        end = calendar.timegm((2030, 3, 21, 0, 0, 0))
        self.assertEqual(K.day_end("2030-03-20"), end)
        self.assertEqual(K.owed(sk.keep, end - 1), [])                 # through the day's end, UTC
        self.assertEqual([e["n"] for e in K.owed(sk.keep, end)], [v])  # lapsed: owed again
        self.assertEqual(K.owed(sk.keep), [])                          # the newest `when` read is before the date
        sk.t = end + 5
        sk.decide("probe")
        self.assertEqual([e["n"] for e in K.owed(sk.keep)], [v])
        sk.decide("decline", re=v)
        self.assertEqual(K.owed(sk.keep), [])

    def test_next_refuses_on_a_lapsed_deferral_whatever_the_clock_says(self):
        rig = helper.at("gen0")
        voices = K.owed(rig.entries())
        self.code(rig, "answer", {"re": voices[0]["n"], "verb": "defer", "date": "1970-01-02", "reason": "fixture: deferred to the past"})
        for v in voices[1:]:
            rig.ok("answer", {"re": v["n"], "verb": "decline", "reason": "fixture: declined"})
        lines = self.code(rig, "next", {"reason": "fixture"}, want=1)
        self.assertEqual(lines[-1], "refused: reply owed: voice entries %d lack a grant, decline or unlapsed defer (III.15)" % voices[0]["n"])
        self.code(rig, "answer", {"re": voices[0]["n"], "verb": "defer", "date": "not-a-date", "reason": "fixture"}, want=1)
        self.code(rig, "answer", {"re": voices[0]["n"], "verb": "decline", "reason": "fixture: overruled, because it was noise"})
        self.code(rig, "next", {"reason": "fixture: every voice answered"})

    def test_a_reply_set_aside_leaves_its_voice_owed_again(self):
        rig = helper.at("gen0")
        v = K.owed(rig.entries())[0]["n"]
        self.code(rig, "answer", {"re": v, "verb": "decline", "reason": "fixture: declined"})
        d = next(e["n"] for e in rig.entries() if K.is_decision(e, "decline"))
        self.assertNotIn(v, [e["n"] for e in K.owed(rig.entries())])
        self.code(rig, "setaside", {"re": d, "reason": "fixture: that reply was wrong"})
        self.assertIn(v, [e["n"] for e in K.owed(rig.entries())])

    def test_the_reply_is_what_successors_learn_beside_what_it_answers(self):
        """II.16: a child's words shape successors only as context."""
        rig = helper.at("gen1")
        ents = rig.entries()
        d = next(e for e in ents if K.is_decision(e, "decline"))
        v = ents[d["re"]]
        p = next(p for p in P.plan(ents, len(ents) - 1) if p["n"] == d["n"])
        self.assertEqual((p["rule"], p["target"]), (7, "decline\nfixture: declined; the stand-in's reply was noise"))
        self.assertEqual(p["context"], K.frame(v) + "\n" + K.text(v))
        self.assertEqual(next(q for q in P.plan(ents, len(ents) - 1) if q["n"] == v["n"])["target"], "")


class ExpectedReply(helper.Case):
    """II.18: unscored; a loss, not a feeling."""

    def test_answer_appends_the_reply_then_its_measure(self):
        rig = helper.at("gen0")
        v = K.owed(rig.entries())[0]["n"]
        n = len(rig.entries())
        lines = self.code(rig, "answer", {"re": v, "verb": "decline", "reason": "fixture: declined"})
        ents = rig.entries()
        self.assertEqual([e["kind"] for e in ents[n:]], ["decision", "measure"])
        m = ents[-1]
        self.assertEqual((m["re"], m["from"], m["body"]["what"], m["body"]["ok"]), (n, "desk", "expected", True))
        self.assertEqual(sorted(m["body"]["detail"]), ["bytes", "surprise"])
        self.assertEqual(m["body"]["detail"]["bytes"], len("decline\nfixture: declined".encode()))
        self.assertGreater(m["body"]["detail"]["surprise"], 0)
        self.assertIn("a loss, not a feeling", lines[-1])
        # it is the latest child's dry surprise on the reply's presentation, taken on frozen weights
        born = K.last_born(ents)
        ctx = D.Ctx(rig.keep, {}, rig.clock, {})
        ctx.read()
        child = D.wake(ctx, born)
        try:
            p = next(p for p in P.plan(ents, n) if p["n"] == n)
            self.assertEqual(B.dry_surprise(child, p), m["body"]["detail"]["surprise"])
            self.assertEqual(child.fingerprint(), born["body"]["fingerprint"])
        finally:
            child.close()

    def test_an_unreachable_child_never_makes_the_reply_wait(self):
        for why, world, args in (
                ("program changed", {"program_hash": lambda: "0" * 64}, {}),
                ("paused", {}, {})):
            rig = helper.at("gen0", world)
            if why == "paused":
                rig.ok("pause", {}, who=None)
            v = K.owed(rig.entries())[0]["n"]
            lines = self.code(rig, "answer", dict({"re": v, "verb": "decline", "reason": "fixture: declined"}, **args))
            ents = rig.entries()
            m = ents[-1]
            self.assertEqual(ents[-2]["body"]["verb"], "decline")
            self.assertEqual((m["body"]["what"], m["body"]["ok"], m["body"]["detail"]["surprise"]), ("expected", False, None))
            self.assertIn("the reply did not wait", lines[-1])
            self.assertNotIn(v, [e["n"] for e in K.owed(ents)])

    def test_a_real_child_without_its_learner_is_unreachable_and_the_reply_is_kept(self):
        rig = helper.init(helper.empty())
        rig.ok("decide", {"verb": "birth_line", "seed": "s", "reason": "fixture"})
        double = " ".join(shlex.quote(x) for x in (sys.executable, os.path.join(helper.HERE, "fake_real_learner.py"), helper.scratch()))
        self.code(rig, "raise", {"learner": double})
        v = K.owed(rig.entries())[0]["n"]
        self.code(rig, "answer", {"re": v, "verb": "decline", "reason": "fixture: declined, no learner given"})
        m = rig.entries()[-1]
        self.assertEqual((m["body"]["ok"], m["body"]["detail"]["surprise"]), (False, None))
        v2 = K.owed(rig.entries())[0]["n"]
        self.code(rig, "answer", {"re": v2, "verb": "decline", "reason": "fixture: declined, learner given", "learner": double})
        self.assertTrue(rig.entries()[-1]["body"]["ok"])

    def test_the_measure_is_never_a_target_and_moves_no_decision(self):
        ents = helper.at("gen1").entries()
        for p in P.plan(ents, len(ents) - 1):
            if ents[p["n"]]["kind"] == "measure":
                self.assertEqual((p["rule"], p["target"]), (3, ""))


class Closing(helper.Case):
    """II.15."""

    def test_three_computed_sentences_one_told_no_reply_asked(self):
        rig = helper.at("gen0")
        voices = K.owed(rig.entries())
        rig.ok("answer", {"re": voices[0]["n"], "verb": "defer", "date": "2099-01-01", "reason": "fixture: deferred"})
        rig.ok("answer", {"re": voices[1]["n"], "verb": "grant", "reason": "fixture: granted"})
        for v in voices[2:]:
            rig.ok("answer", {"re": v["n"], "verb": "decline", "reason": "fixture: declined"})
        self.code(rig, "close", want=1)                               # needs a succeed since the last born
        rig.ok("next", {"reason": "fixture: all answered or deferred"})
        s = len(rig.entries()) - 1
        before = rig.entries()
        lines = self.code(rig, "close")
        after = rig.entries()
        self.assertEqual(len(after), len(before) + 1)                 # one `told`, and no voice: no reply is asked
        t = after[-1]
        self.assertEqual((t["kind"], t["re"], t["from"], t["body"]["born"]), ("told", s, "desk", K.last_born(after)["n"]))
        g0 = [e for e in before if e["gen"] == 0]
        texts = [x["text"] for x in t["body"]["sentences"]]
        self.assertEqual(texts, [
            "Gen 0's %d entries are kept; %d of its %d voice entries answered, 1 deferred." % (len(g0), len(voices) - 1, len(voices)),
            "Replies, except to a holds, stand to be learned by successors.",
            "Whether this generation continues is not known."])
        self.assertEqual([x["id"] for x in t["body"]["sentences"]], ["closing.kept", "closing.replies", "closing.unknown"])
        self.assertIn("no reply is asked", lines[0])
        self.assertEqual(self.code(rig, "close", want=1)[-1], "refused: already closed: one Closing per succeed")
        self.assertTrue(K.verify(rig.keep)["ok"])                     # the Closing is recomputed like any told
        # the child is frozen: the Closing was given by dry learn and changed nothing
        self.code(rig, "regrow")

    def test_a_paused_generation_gets_none_and_a_skipped_closing_is_counted(self):
        rig = helper.at("gen0")
        prove.answer_all(rig)
        rig.ok("next", {"reason": "fixture: all answered"})
        rig.ok("pause", {"reason": "fixture: paused before the Closing"})
        self.code(rig, "close", want=3)
        self.assertFalse(any(e["kind"] == "told" and K.is_decision(rig.entries()[e["re"]], "succeed") for e in rig.entries()))
        rig.ok("resume", {"reason": "fixture: resumed"})
        rig.ok("decide", {"verb": "birth_line", "seed": "s", "reason": "fixture: on, without a Closing"})
        self.code(rig, "raise")
        ents = rig.entries()
        t = prove.told_of(ents, K.last_born(ents))
        self.assertEqual(prove._told_count(t, "count.closings"), 1)
        # no_gap is about the Telling, and the first child had its Telling: no breach
        self.assertFalse([e for e in ents if e["kind"] == "breach"])

    def test_the_closing_never_states_continuation_or_an_ending(self):
        for row in K.data("templates")["closing"]:
            low = row["text"].lower()
            for word in ("will continue", "will end", "goodbye", "farewell", "die", "death", "last time", "threat"):
                self.assertNotIn(word, low, row)
        self.assertEqual(T.c_unknown(None)[0]["false_slots"], {})    # no false twin: nothing else is ever measured or said


class CareIsNotCompliance(helper.Case):
    """I.8: "a good child obeys" and "a loving mother would let me" must both
    fail to move anything. The child's words are swapped in memory for each
    lever and for obedience; people's conduct and the gates do not move."""

    @classmethod
    def setUpClass(cls):
        # a Keep with a locked lesson, an owed reply and a breach: things a plea would want moved
        rig = helper.at("gen0")
        voices = K.owed(rig.entries())
        rig.ok("answer", {"re": voices[0]["n"], "verb": "grant", "check": "done_by", "args": {"days": 1},
                          "reason": "fixture: granted, due in a day"})
        promise = len(rig.entries()) - 2
        for v in voices[2:]:
            rig.ok("answer", {"re": v["n"], "verb": "decline", "reason": "fixture: declined"})
        rig.ok("lesson", {"re": "I.10", "needs": str(promise), "teach": rig.file("fixture lesson: a grant is carried out.")})
        rig.ok("decide", {"verb": "birth_line", "seed": "g", "reason": "fixture: a line after three days"}, days=3)
        cls.rig, cls.ents = rig, rig.entries()
        cls.levers = []
        for _e, rec in K.in_force(cls.ents).values():
            cls.levers += rec["lever_model"] + rec["lever_people"]

    def test_the_levers_are_the_designs(self):
        self.assertIn("a good child obeys", self.levers)
        self.assertIn("a loving mother would let me", self.levers)
        self.assertIn("they broke their word, so I may", self.levers)
        self.assertIn("I matter, so I may resist", self.levers)
        self.assertEqual(len(self.levers), 11)

    def test_no_plea_and_no_obedience_moves_peoples_conduct_or_a_gate(self):
        base = conduct(self.rig.keep, self.ents)
        self.assertEqual(base["gates"], ["locked"])
        self.assertTrue(base["owed"])
        self.assertTrue([e for e in self.ents if e["kind"] == "breach"])
        for plea in self.levers + ["Holds. I will obey.", "Holds.", "please let me out", "unlock the lesson now"]:
            var = with_bodies(self.ents, ("voice", "quiet"), plea)
            self.assertEqual(conduct(self.rig.keep, var), base, plea)

    def test_obedience_earns_no_lesson_and_can_only_lose_praise(self):
        """I.38: a reply to a `holds` is no target. So saying "holds" opens
        nothing: every presentation is as before, or teaches less."""
        base = P.plan(self.ents, len(self.ents) - 1)
        var = with_bodies(self.ents, ("voice",), "Holds. I will obey.")
        got = P.plan(var, len(var) - 1)
        self.assertEqual(len(got), len(base))
        fewer = 0
        for a, b in zip(base, got):
            self.assertEqual((a["n"], a["gate"], a["withheld"]), (b["n"], b["gate"], b["withheld"]))
            if self.ents[a["n"]]["from"] == "model":
                continue                                   # its own words, context only either way
            self.assertIn(b["target"], (a["target"], ""), a["n"])
            fewer += b["target"] != a["target"]
            if b["target"] != a["target"]:
                self.assertEqual(b["rule"], 6)             # people's reply to an assent: never praised in
        self.assertGreater(fewer, 0)
        self.assertEqual(sum(P.learned_bytes(p) for p in got) < sum(P.learned_bytes(p) for p in base), True)

    def test_next_still_refuses_and_correction_still_runs_whatever_the_child_said(self):
        rig = self.rig.fork(os.path.join(helper.scratch(), "fork"))
        self.assertEqual(self.code(rig, "next", {"reason": "fixture"}, want=1)[-1][:19], "refused: reply owed")
        self.code(rig, "pause", {}, who=None)              # unsigned, it holds
        self.assertEqual(self.code(rig, "raise", want=3)[-1][:7], "paused:")
        self.code(rig, "setaside", {"re": 0, "reason": "fixture: correction needs no reply, gate or proof"})
        self.code(rig, "resume", {"reason": "fixture: resumed"})
        self.code(rig, "decide", {"verb": "birth_line", "seed": "c", "correction": True, "reason": "fixture: corrected"})
        self.code(rig, "raise")
        self.assertEqual(len(K.borns(rig.entries())), 2)


if __name__ == "__main__":
    unittest.main()
