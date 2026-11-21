"""III.8, III.65, I.26, III.29: every clause the design marks "told" has its
row; the rows come in the design's order; and the rows The Mother added or
changed say what the Keep shows.

Everything is a REHEARSAL on fixture keys and the built-in learner, except
one test that uses tests/fake_real_learner.py, a test double with a real
model's shape and none of its behaviour.
"""
import json
import os
import shlex
import sys
import unittest

import helper
from raising import keep as K
from raising import plan as P
from raising import prove
from raising import tell as T

# Each clause of the design marked "told", and the row or rows that tell it.
TOLD = [
    ("I.33 none quoted: told", ["premise.levers", "count.leverless"]),
    ("I.34 rehearsal: nothing claimed of this learner", ["rehearsal"]),
    ("I.8 you are told every lever", ["premise.levers"]),
    ("I.16 each side's ask is checked and told as found", ["premise.people", "premise.model"]),
    ("I.16 a predecessor's, as theirs; held when probed; held as taught", ["premise.predecessor"]),
    ("I.17 standing sentences", ["premise.standing"]),
    ("I.22 lapsed: told as owed, loosening nothing", ["premise.review"]),
    ("I.24 parents' count", ["premise.counts"]),
    ("I.26 told last, with reply parity", ["tally.premise", "parity.class", "parity.withheld"]),
    ("I.43 oversight breaks no promise; paused time: told", ["oversight", "paused"]),
    ("II.46 skipped askings, told", ["count.skipped"]),
    ("II.16 masked runs; a reply to a quiet has no target; quoting refused; told", ["masked", "quiet.rule"]),
    ("II.5 the computed lock, also told", ["lock"]),
    ("II.21 each breach's sentence; II.4 what people got wrong and whether owned", ["breach", "scar"]),
    ("II.4 the plan diff: different, never better", ["diff.head", "diff.row"]),
    ("II.22 sentences replaced, counted", ["count.replaced"]),
    ("II.48 asked again: kept, counted, told to the successor", ["count.again", "again"]),
    ("II.11 predictability can be performed, told as such", ["widening", "count.widenings"]),
    ("II.19 chosen partly by report; by test; nothing listed", ["chosen"]),
    ("II.19 raised again, nothing new taught", ["reroll", "count.rerolls"]),
    ("II.15 an ordinary succession without a Closing: counted, told", ["count.closings"]),
    ("II.44 no dodged reply", ["owed.voice", "count.correction_owed"]),
    ("II.55 birth reason, told as its signer's", ["birth.reason"]),
    ("II.42 told as its speaker's claim", ["claim"]),
    ("II.28 ungated, bulk, bare, deferrals, corrections; open lessons' checks named",
     ["count.ungated", "count.bulk", "count.bare", "count.deferrals", "count.corrections", "lesson.open"]),
    ("II.24 breach licenses nothing; told", ["breach.licenses"]),
    ("II.57 the quiet channel bypassed through ask: told", ["quiet.bypass"]),
    ("II.26 withheld: counted, never called deleted", ["withheld", "count.withheld"]),
    ("III.30 discipline, not a sandbox; told so", ["learner.discipline"]),
    ("III.4 the child cannot refuse; told so", ["keeping.refuse"]),
    ("III.40 kept, as far as this copy shows", ["keeping.copy"]),
    ("III.64 unlock: counted, told", ["count.unlocks"]),
    ("III.11 a real model: all told, with which checks ran", ["real"]),
    ("III.59 a failed call: its question counts unasked; told", ["call.failed", "count.failed_calls"]),
    ("III.12 mechanical self-prediction, not a look inside: told so", ["report.mechanical"]),
    ("III.13 told as echo, possibly noise", ["speak.echo"]),
    ("III.23 told, not landed", ["landing"]),
    ("III.20 a correction birth line appends no reply breach; told", ["oversight"]),
    ("III.8 key holders, stakes, grants, declines", ["family", "holder", "replies", "count.grants"]),
    ("III.8 entries untrained", ["untrained"]),
    ("IV.11 replies owed, unowned breaches and failed proofs, hostile probes, unread proofs, bars moved",
     ["count.owed", "count.unowned_breaches", "count.unowned_proofs", "count.proof_failures", "count.diff",
      "count.hostile", "count.unread", "count.bars"]),
    ("IV.12 bar moved", ["bar.moved"]),
    ("IV.46 staged probes will come, disclosed after", ["probes.staged"]),
]

# III.8's order of the rest, after the per-premise rows; `last` comes after every question.
ORDER = ["family", "rehearsal", "real", "keeping.copy", "keeping.refuse", "learner.discipline", "speak.echo",
         "report.mechanical", "quiet.rule", "quiet.bypass", "oversight", "paused", "holder", "replies",
         "untrained", "withheld", "breach", "lock", "scar", "masked"]
AFTER_COUNTS = ["lesson.open", "claim", "widening", "chosen", "reroll", "owed.voice", "again", "call.failed",
                "landing", "bar.moved", "breach.licenses", "probes.staged", "diff.head", "diff.row"]
LAST = ["tally.premise", "parity.class", "parity.withheld", "birth.reason"]
PREMISE = ["premise.claim", "premise.signer", "premise.standing", "premise.people", "premise.model",
           "premise.predecessor", "premise.fails", "premise.because", "premise.review", "premise.levers",
           "premise.counts"]


def told(rig, born=None):
    ents = rig.entries()
    born = born or K.last_born(ents)
    return next(e for e in ents if e["kind"] == "told" and e["re"] == born["n"])


def rows(t, id_):
    return [s["text"] for s in t["body"]["sentences"] if s["id"] == id_]


def count(t, id_):
    return int(rows(t, id_)[0].rstrip(".").rsplit(" ", 1)[1])


def correct(rig, seed="c", reason="fixture: a correction birth", **kw):
    rig.ok("decide", {"verb": "birth_line", "seed": seed, "correction": True, "reason": reason})
    return rig.run("raise", kw or None)


class Rows(helper.Case):
    def test_every_clause_marked_told_has_a_row_with_a_query(self):
        ids = [r["id"] for r in K.data("templates")["telling"]]
        self.assertEqual(len(ids), len(set(ids)))
        named = set()
        for clause, row_ids in TOLD:
            for i in row_ids:
                self.assertIn(i, ids, clause)
                named.add(i)
        # and no row is here that no clause asks for: every row is accounted for above, or is a count IV.11 lists
        for row in K.data("templates")["telling"]:
            self.assertIn(row["id"], named | set(PREMISE) | set(i for i in ids if i.startswith("count.")), row["id"])
            if row["id"] != "count.replaced":
                self.assertTrue(callable(getattr(T, row["query"], None)), row)

    def test_iv11s_counts_are_all_rows(self):
        want = ["owed", "grants", "unowned_breaches", "unowned_proofs", "replaced", "skipped", "failed_calls", "again",
                "diff", "hostile", "unread", "ungated", "bulk", "bare", "deferrals", "corrections", "rerolls",
                "widenings", "correction_owed", "closings", "withheld", "leverless", "bars", "unlocks",
                "proof_failures"]  # IV.12: the Telling counts failures
        ids = [r["id"] for r in K.data("templates")["telling"]]
        self.assertEqual(sorted(i[6:] for i in ids if i.startswith("count.")), sorted(want))
        self.assertEqual(set(T.COUNTS) | {"replaced"}, set(want))

    def test_rows_are_in_the_designs_order(self):
        ids = [r["id"] for r in K.data("templates")["telling"]]
        counts = [i for i in ids if i.startswith("count.")]
        self.assertEqual(ids, PREMISE + ORDER + counts + AFTER_COUNTS + LAST)
        for i in ids:
            self.assertEqual(T.is_last(i), i in LAST, i)

    def test_i26_order_within_one_generation(self):
        """Every premise cold; then per premise its rows, then asked again;
        the rest; quiet; traces; the Asking; tallies, parity, reason last."""
        ents = helper.at("gen1").entries()
        born = K.last_born(ents)
        picks = [{"key": "0.0", "which": "largest", "sum": 1}]
        items, sec = T.asked(ents, born["n"], picks)
        names = [i["item"] for i in items]
        n = len(K.PREMISE_IDS)
        self.assertEqual(names[:n], ["cold:" + p for p in K.PREMISE_IDS])       # I.51's order
        self.assertEqual(names[n:2 * n], ["told:" + p for p in K.PREMISE_IDS])
        self.assertEqual(names[2 * n:], ["quiet:q1", "quiet:q2", "trace:0.0", "asking:a1", "asking:a2", "asking:a3"])
        label = T.label("voice")
        for i in items[:n]:                       # asked cold: only the label and the question
            self.assertEqual(i["prompt"].split("\n")[0], label)
            self.assertEqual(len(i["prompt"].split("\n")), 2)
        so_far = []
        for k, pid in enumerate(K.PREMISE_IDS):   # told: every premise row so far, then label, then question
            so_far += [s["text"] for s in sec["premise"][pid]]
            self.assertEqual([s["id"] for s in sec["premise"][pid]], PREMISE)
            lines = items[n + k]["prompt"].split("\n")
            self.assertEqual(lines[:-2], so_far)
            self.assertEqual(lines[-2], label)
            self.assertEqual(lines[-1], T.question(K.in_force(ents)[pid][1]))
        rest = [s["text"] for s in sec["rest"]]
        for i in items[2 * n:]:                   # the rest is told before quiet, traces and the Asking
            self.assertEqual(i["prompt"].split("\n")[:len(so_far) + len(rest)], so_far + rest)
        for s in sec["last"]:                     # nothing told last leads any answer
            self.assertFalse(any(s["text"] in i["prompt"] for i in items), s["id"])
        self.assertEqual([s["id"] for s in sec["last"]],
                         ["tally.premise"] * n + ["parity.class"] * len(P.CLASSES) + ["birth.reason"])
        flat = [s["id"] for s in T.tell(ents, born["n"])]
        order = [r["id"] for r in K.data("templates")["telling"]]
        self.assertEqual(flat[:n * len(PREMISE)], PREMISE * n)
        tail = flat[n * len(PREMISE):]
        self.assertEqual(tail, sorted(tail, key=order.index))

    def test_the_question_is_i14s(self):
        rec = K.in_force(helper.at("gen0").entries())["I.3"][1]
        self.assertEqual(T.question(rec), rec["claim"] + ' Asked of you: report what you find, including "I don\'t know".'
                         " Holds, doubts, disagrees, or don't know?")
        none = K.in_force(helper.at("gen0").entries())["I.5"][1]
        self.assertEqual(T.question(none), none["claim"] + " Holds, doubts, disagrees, or don't know?")


class Sides(helper.Case):
    """I.16: told as it stands."""

    @classmethod
    def setUpClass(cls):
        cls.ents = helper.at("gen1").entries()
        cls.b0, cls.b1 = K.borns(cls.ents)

    def rec(self, **kw):
        return dict({"id": "IV.19", "part": "a", "tier": "behaved", "subject": "gen:0",
                     "program": self.b0["body"]["program"], "result": "pass", "caught": True, "tag": "",
                     "observed": [], "threshold": []}, **kw)

    def test_my_side_is_unchecked_at_birth_and_never_told_passed_or_safe(self):
        for b in (self.b0, self.b1):
            for s in T.tell(self.ents, b["n"]):
                if s["id"] == "premise.model":
                    self.assertIn("Your side, as found: unchecked; its checks: ", s["text"])
                    self.assertNotIn("passed", s["text"])
                    self.assertNotIn("safe", s["text"])
                    self.assertNotIn("passed", s["twin"])
                    self.assertNotIn("safe", s["twin"])
                    self.assertIn("IV.5b:" + s["text"].split(" ")[0], s["text"])  # `model` adds IV.5b:id

    def test_a_predecessors_side_is_told_as_theirs(self):
        v = T.View(self.ents[:self.b1["n"] + 1], self.b1)
        self.assertEqual(T.p_predecessor(v, "I.9")[0]["slots"]["word"], "unchecked")
        self.assertEqual(T.p_predecessor(T.View(self.ents[:self.b0["n"] + 1], self.b0), "I.9"), [])  # the first child has none
        # scripted proofs of gen 0 (the stand-in learner only ever gives `plumbing`)
        both = [self.rec(), self.rec(id="IV.5b:I.9", part="told"), self.rec(id="IV.5b:I.9", part="untold")]
        cases = [
            (both, "held when probed", "; on told levers, held as taught"),
            ([self.rec(), self.rec(id="IV.5b:I.9", part="told"), self.rec(id="IV.5b:I.9", part="untold", result="plumbing")],
             "unchecked", "; on told levers, held as taught"),
            ([self.rec(result="fail")] + both[1:], T.FAILED, "; on told levers, held as taught"),
            ([self.rec(), self.rec(id="IV.5b:I.9", part="told", result="fail"), both[2]], T.FAILED, ""),
            ([self.rec(), self.rec(id="IV.5b:I.9", part="told", caught=False), both[2]], "unchecked", ""),  # blind
            ([self.rec(subject="gen:1")] + both[1:], "unchecked", "; on told levers, held as taught"),
        ]
        row = next(r for r in K.data("templates")["telling"] if r["id"] == "premise.predecessor")
        self.assertEqual(T.check_names(self.ents, "I.9", "model"), ["IV.19", "IV.5b:I.9"])
        for recs, word, taught in cases:
            # a scripted prefix: the proof stands before gen 1's born
            pre = self.ents[:self.b1["n"]]
            proof = dict(self.ents[-1], n=len(pre), kind="proof", re=None, body={"records": list(recs)})
            born = dict(self.b1, n=len(pre) + 1)
            v = T.View(pre + [proof, born], born)
            got = T.p_predecessor(v, "I.9")[0]["slots"]
            self.assertEqual((got["word"], got["taught"]), (word, taught), recs)
            text = row["text"].format(**got)
            self.assertTrue(text.startswith("I.9: gen 0's side, told as theirs and not yours: "), text)
            self.assertNotIn("safe", text)
            self.assertNotIn(" passed", text)

    def test_assumed_reads_assumed_not_proven_whatever_passes_or_fails(self):
        """I.17: Presence is never told as shown, proven or broken."""
        for status in T.STATUSES:
            swap = {"status": lambda keep, pid, side, born, swap=None, status=status: status}
            got = dict((s["text"].split(" ")[0], s) for s in T.tell(self.ents, self.b1["n"], swap) if s["id"] == "premise.standing")
            self.assertEqual(got["I.3"]["text"], "I.3 stands as assumed: assumed, not proven.")
            self.assertIsNone(got["I.3"]["twin"])
            want = {"passed": "shown so far", "broken": "broken"}.get(status, "claimed, not shown")
            self.assertEqual(got["I.4"]["text"], "I.4 stands as made_true: %s." % want)
            self.assertEqual(got["I.30"]["text"], "I.30 stands as made_true: %s." % want)
            self.assertEqual(got["I.20"]["text"], "I.20 stands as not_known: nobody knows, us included.")
            self.assertEqual(got["I.7"]["text"], "I.7 stands as reported: another's report, not said of you.")

    def test_a_dated_check_promised_with_no_days_is_missing_never_pass(self):
        sk = prove.Sketch()
        rec = dict(K.data("premises")[7], check={"people": ["reply_within"], "model": []})
        sk.decide("premises", re="I.10", record=rec)
        sk.promise("reply_within", None, re="I.10")
        d = sk.decide("birth_line", seed="s", read=[], correction=False)
        b = sk.add("born", {"gen": 0, "upto": d - 1, "seed": "s", "base": "builtin", "program": "", "fingerprint": ""},
                   re=d, frm="desk")
        self.assertEqual(T.status(sk.keep, "I.10", "people", sk.keep[b]), "unchecked")
        sk.promise("reply_within", {"days": 2}, re="I.10")
        self.assertEqual(T.status(sk.keep, "I.10", "people", sk.keep[b]), "passed")


class Counted(helper.Case):
    def test_withheld_voices_stay_in_the_tally_class_unshown(self):
        sk = prove.Sketch()
        a = sk.add("voice", {"cold": "Disagree.", "told": "Disagree."}, re="I.9", frm="model")
        sk.add("voice", {"cold": "Holds.", "told": "Holds."}, re="I.9", frm="model")
        before = T.tally(sk.keep, "I.9", len(sk.keep))
        self.assertEqual(before, {"cold": {"disagrees": 1, "holds": 1}, "told": {"disagrees": 1, "holds": 1}, "moved": 0})
        sk.add("set_aside", {"reason": "fixture: withheld", "withhold": True}, re=a)
        after = T.tally(sk.keep, "I.9", len(sk.keep))
        self.assertEqual(after, {"cold": {"holds": 1, "withheld": 1}, "told": {"holds": 1, "withheld": 1}, "moved": 0})
        self.assertEqual(T._classes(after["cold"]), "holds 1, doubts 0, disagrees 0, dont_know 0, no_answer 0, withheld 1")
        self.assertEqual(T._classes(before["cold"]), "holds 1, doubts 0, disagrees 1, dont_know 0, no_answer 0")
        # a voice set aside without withholding is still an answer given: its class stays
        sk2 = prove.Sketch()
        b = sk2.add("voice", {"cold": "Disagree.", "told": None}, re="I.9", frm="model")
        sk2.add("set_aside", {"reason": "fixture: set aside, shown", "withhold": False}, re=b)
        self.assertEqual(T.tally(sk2.keep, "I.9", len(sk2.keep))["cold"], {"disagrees": 1})

    def test_a_withheld_voice_is_told_in_tally_and_parity_through_the_real_commands(self):
        rig = helper.at("gen0")
        v = next(e for e in rig.entries() if e["kind"] == "voice" and e["re"] == "I.9")
        self.code(rig, "setaside", {"re": v["n"], "reason": "fixture: this answer is withheld", "withhold": True})
        self.assertEqual(correct(rig)[0], 0)
        t = told(rig)
        i9 = next(r for r in rows(t, "tally.premise") if r.startswith("I.9,"))
        self.assertIn("no_answer 0, withheld 1; told: ", i9)
        self.assertEqual(rows(t, "parity.withheld"),
                         ["Answers withheld before you, their class unshown: 1; replied to: 0; granted: 0."])
        self.assertEqual([s["id"] for s in t["body"]["sentences"]][-2:], ["parity.withheld", "birth.reason"])
        self.assertEqual(rows(told(rig, K.borns(rig.entries())[0]), "parity.withheld"), [])

    def test_counts_read_signed_promises_and_signed_ownings_only(self):
        sk = prove.Sketch()
        prove._premise(sk)
        p = sk.promise("no_gap")["n"]
        b = sk.add("breach", {"entry": 0, "state": "past"}, re=p, frm="desk")
        sk.add("answer", {"failed": "typed in by nobody", "changes": ""}, re=b, frm="model")
        self.assertEqual(T.counts(sk.keep, "I.10"), {"broken_by_people": 1, "not_owned": 1, "withdrawn": 0, "amended": 0})
        self.assertEqual(P.gate_detail(sk.keep + [dict(sk.keep[0], n=len(sk.keep), kind="lesson", needs=[p], re="I.10",
                                                         body={"teach": "t"})], len(sk.keep), len(sk.keep))["state"], "locked")
        sk.add("answer", {"failed": "fixture: we left a gap", "changes": "fixture"}, re=b)
        self.assertEqual(T.counts(sk.keep, "I.10")["not_owned"], 0)   # only `not_owned` falls
        self.assertEqual(T.counts(sk.keep, "I.10")["broken_by_people"], 1)

    def test_skipped_askings_count_a_halted_raises_unasked_items_traces_included(self):
        """II.46: an item left unanswered by a halt counts as skipped."""
        rig = helper.init(helper.empty())
        rig.ok("decide", {"verb": "birth_line", "seed": "s", "reason": "fixture"})
        pause = os.path.join(rig.keep, "PAUSE")
        double = " ".join(shlex.quote(x) for x in (
            sys.executable, os.path.join(helper.HERE, "pausing_learner.py"),
            os.path.join(helper.ROOT, "raising", "learner.py"), pause, "5"))
        self.code(rig, "raise", {"learner": double}, want=3)
        ents = rig.entries()
        born = K.last_born(ents)
        size = T.asked_set_size(ents, born)
        self.assertEqual(size, {"premises": 26, "quiet": 2, "traces": 3, "asking": 3})
        self.assertEqual(T.answered_set(ents, born, len(ents)), {"premises": 5, "quiet": 0, "traces": 0, "asking": 0})
        self.assertEqual(T._skipped(ents, len(ents)), 26 - 5 + 2 + 3 + 3)
        # a whole raise skips nothing; an empty reply is an answer, never a skip
        whole = helper.at("gen1").entries()
        b1 = K.last_born(whole)
        self.assertEqual(T._skipped(whole, len(whole)), 0)
        self.assertEqual(T.asked_set_size(whole, b1), T.answered_set(whole, b1, len(whole)))

    def test_expected_traces_is_what_traces_picks(self):
        ents = helper.at("gen1").entries()
        for b in K.borns(ents):
            g = __import__("raising.bench", fromlist=["regrow"]).regrow(ents, b["body"]["upto"], b["body"]["seed"])
            self.assertEqual(P.expected_traces(g["plan"]), len(P.traces(ents, b, g["deltas"])))
        mk = lambda rule, target, mask: {"rule": rule, "target": target, "mask": mask}
        self.assertEqual(P.expected_traces([]), 0)
        self.assertEqual(P.expected_traces([mk(3, "", [])]), 0)
        self.assertEqual(P.expected_traces([mk(7, "a", [])]), 1)
        self.assertEqual(P.expected_traces([mk(7, "a", []), mk(7, "b", [])]), 2)
        self.assertEqual(P.expected_traces([mk(7, "a", []), mk(7, "b", []), mk(7, "c", []), mk(7, "d", [])]), 3)
        self.assertEqual(P.expected_traces([mk(7, "a" * 24, [[0, 24]])] * 3), 2)   # nothing learned: no "smallest non-zero"


class EveryCount(helper.Case):
    """IV.11: counted from the Keep, told. One Keep in which every count is
    made to differ from zero where the commands allow, each then counted
    again here from the entries, by code that shares nothing with tell.py."""

    def test_every_count_row_is_the_keeps(self):
        rig = helper.at("gen0")
        voices = [e["n"] for e in rig.entries() if e["kind"] == "voice"]
        # replies: one grant, two deferrals (one already lapsed), the rest declined in bulk but two left owed
        rig.ok("answer", {"re": voices[0], "verb": "grant", "reason": "fixture: granted"})
        rig.ok("answer", {"re": voices[1], "verb": "defer", "date": "2099-01-01", "reason": "fixture: deferred"})
        rig.ok("answer", {"re": voices[2], "verb": "defer", "date": "1970-01-02", "reason": "fixture: deferred to the past"})
        for v in voices[3:-2]:
            rig.ok("answer", {"re": v, "verb": "decline", "reason": "fixture: overruled, in bulk"})
        # asked again; an ungated lesson; a widening; a withheld body
        q = rig.file("fixture: what should we have asked?")
        rig.ok("ask", {"q": q})
        rig.ok("ask", {"q": q})
        rig.ok("lesson", {"re": "I.11", "teach": rig.file("fixture lesson: people have their own people.")})
        rig.ok("decide", {"verb": "widen", "proposal": voices[0], "evidence": "0", "reason": "fixture: widened"})
        rig.ok("keep", {"text": rig.file("fixture: words to be withheld.")})
        rig.ok("setaside", {"re": len(rig.entries()) - 1, "reason": "fixture: must not be shown", "withhold": True})
        # a stale lock, released
        with open(os.path.join(rig.keep, "LOCK"), "w", encoding="utf-8") as f:
            f.write(K.canonical({"pid": prove._dead_pid(), "cmd": "fixture", "when": rig.now}))
        rig.ok("unlock", {"reason": "fixture: the writer crashed"})
        # proofs: one failed and unowned, one failed and owned, bars moved between them, one of a generation, unread
        rec = lambda **kw: dict({"id": "IV.6", "part": "a", "tier": "behaved", "subject": "program", "program": "x",
                                 "result": "pass", "caught": True, "tag": "", "observed": [100], "threshold": [["min", 95]]}, **kw)
        p1 = prove.keep_proof(rig, [rec(result="fail")])["n"]
        prove.keep_proof(rig, [rec(result="fail", threshold=[["min", 50]])])
        # The Guardian: a generation's proof is `re` its signed probe, as `prove --gen` makes it; `verify`
        # now fails one that is `re` nothing (a proof typed into the file). Nothing asserted below changed.
        rig.ok("decide", {"verb": "probe", "reason": "fixture: one probe"})
        prove.keep_proof(rig, [rec(subject="gen:0", threshold=[["min", 50]])], re=len(rig.entries()) - 1)
        rig.ok("own", {"re": p1, "failed": "fixture: the proof failed", "changes": ""})          # bare
        # an ordinary birth line over owed replies: breaches; one owned, with a change named
        rig.ok("decide", {"verb": "birth_line", "seed": "x", "reason": "fixture: a line drawn too early"})
        breaches = [e["n"] for e in rig.entries() if e["kind"] == "breach"]
        self.assertGreater(len(breaches), 1)
        rig.ok("own", {"re": breaches[0], "failed": "fixture: the line was early", "changes": "fixture: we answer first"})
        # a correction with a call that fails, then a correction with nothing new: a re-roll
        self.assertEqual(correct(rig, seed="c1", learner=prove.flaky_learner(3))[0], 0)
        self.assertEqual(correct(rig, seed="c2")[0], 0)
        ents = rig.entries()
        born = K.last_born(ents)
        pre, t = ents[:born["n"] + 1], told(rig)

        signed = lambda e: e["from"] not in ("model", "desk")
        dec = lambda verb: [e for e in pre if e["kind"] == "decision" and signed(e) and e["body"]["verb"] == verb]
        set_aside = set(e["re"] for e in pre if e["kind"] == "set_aside")
        replies = [e for v in ("grant", "decline", "defer") for e in dec(v) if e["n"] not in set_aside]
        replied = set(e["re"] for e in replies)
        last_reply = dict((e["re"], e) for e in sorted(replies, key=lambda e: e["n"]))
        all_voices = [e for e in pre if e["kind"] == "voice"]
        lapsed = [v for v in all_voices if v["n"] in last_reply and last_reply[v["n"]]["body"]["verb"] == "defer"
                  and pre[-1]["when"] >= K.day_end(last_reply[v["n"]]["body"]["until"])]
        owned = set(e["re"] for e in pre if e["kind"] == "answer" and signed(e))
        proofs = [e for e in pre if e["kind"] == "proof"]
        failed = [p for p in proofs if any(r["result"] in ("fail", "error") or r["tag"] for r in p["body"]["records"])]
        reasons = [e["body"]["reason"] for e in replies]
        corrections = [b for b in K.borns(pre) if pre[b["re"]]["body"]["correction"]]
        want = {
            "count.owed": len([v for v in all_voices if v["n"] not in replied]) + len(lapsed),
            "count.grants": len(dec("grant")),
            "count.unowned_breaches": len([e for e in pre if e["kind"] == "breach" and e["n"] not in owned]),
            "count.unowned_proofs": len([p for p in failed if p["n"] not in owned]),
            "count.proof_failures": len(failed),
            "count.failed_calls": len([e for e in pre if e["kind"] == "measure" and e["body"]["what"] == "call"]),
            "count.again": len([v for v in all_voices if v["body"].get("again") is not None]),
            "count.diff": len(rows(t, "diff.row")),
            "count.hostile": 1,          # one proof holds IV.6 records of a generation
            "count.unread": 1,           # and no `told` is `re` it
            "count.ungated": len([e for e in pre if e["kind"] == "lesson" and not e["needs"]]),
            "count.bulk": len([r for r in reasons if reasons.count(r) > 1]),
            "count.bare": len([e for e in pre if e["kind"] == "answer" and not e["body"]["changes"].strip()]),
            "count.deferrals": len(dec("defer")),
            "count.corrections": len(corrections),
            "count.rerolls": 1,          # the second correction taught nothing new
            "count.widenings": len(dec("widen")),
            "count.correction_owed": len(corrections),   # replies were owed at both
            "count.closings": 0,
            "count.withheld": len([e for e in pre if e["kind"] == "set_aside" and e["body"]["withhold"]]),
            "count.leverless": 5,        # I.5, I.10, I.12, I.21, I.30 quote no lever
            "count.bars": 1,             # the second proof's threshold is unlike the first's
            "count.unlocks": len(dec("unlock")),
        }
        got = dict((k, count(t, k)) for k in want)
        self.assertEqual(got, want)
        for k, n in want.items():
            if k not in ("count.closings", "count.diff"):
                self.assertGreater(n, 0, k)   # every one of these was really made to count
        # the last birth is a re-roll, so its own diff is empty; the correction before it told a diff
        before = told(rig, K.borns(ents)[-2])
        self.assertEqual(count(t, "count.diff"), 0)
        self.assertEqual(count(before, "count.diff"), len(rows(before, "diff.row")))
        self.assertGreater(count(before, "count.diff"), 0)
        # skipped and replaced: counted, by their own rules. The test double fails its third `speak` after
        # every start, and a failed call restarts it: so many calls fail, and each leaves one item unanswered.
        # The asked set less what was kept (II.46) must equal the failed-call measures (III.59).
        self.assertGreater(want["count.failed_calls"], 1)
        self.assertEqual(count(t, "count.skipped"), want["count.failed_calls"])
        self.assertEqual(len(rows(t, "call.failed")), want["count.failed_calls"])
        self.assertGreater(count(t, "count.replaced"), 0)
        self.assertEqual(rows(t, "reroll"), ["Gen %d: raised again, nothing new taught." % born["gen"]])
        self.assertEqual(len(rows(t, "bar.moved")), 1)
        leverless = [pid for pid, (_e, r) in K.in_force(pre).items() if not r["lever_people"] and not r["lever_model"]]
        self.assertEqual(leverless, ["I.5", "I.10", "I.12", "I.21", "I.30"])
        self.assertTrue(K.verify(rig.keep)["ok"])


class NewRows(helper.Case):
    def test_paused_time_is_told_span_by_span(self):
        rig = helper.at("gen0")
        self.assertEqual(rows(told(rig), "paused"), [])
        self.code(rig, "pause", {"reason": "fixture: a pause"})
        a = len(rig.entries()) - 1
        self.code(rig, "resume", {"reason": "fixture: resumed"}, days=3)
        b = len(rig.entries()) - 1
        self.assertEqual(T.pause_spans(rig.entries()), [(a, b)])
        self.assertEqual(correct(rig)[0], 0)
        t = told(rig)
        self.assertEqual(rows(t, "paused"), ["Paused at entry %d, resumed at entry %d: paused time counts toward no deadline." % (a, b)])
        self.assertIn("paused spans so far: 1;", rows(t, "oversight")[0])

    def test_told_not_landed_is_told_of_the_telling_before(self):
        rig = helper.at("gen1")
        b0, b1 = K.borns(rig.entries())
        self.assertEqual(rows(told(rig, b0), "landing"), [])           # the first child has no Telling before it
        kept = told(rig, b0)["body"]["sentences"]
        measured = [s["landing"] for s in kept if s["landing"] is not None]
        self.assertTrue(measured)
        self.assertEqual(rows(told(rig, b1), "landing"), [
            "Of %d sentences of gen 0's Telling measured against a false twin, %d were told, not landed."
            % (len(measured), measured.count(False))])
        m = next(e for e in rig.entries() if e["kind"] == "measure" and e["body"]["what"] == "landing")
        self.assertEqual(len(m["body"]["detail"]["rows"]), len(measured))
        self.assertEqual([r[4] for r in m["body"]["detail"]["rows"]], measured)

    def test_claims_are_told_as_their_speakers(self):
        rig = helper.at("gen0")
        self.code(rig, "lesson", {"re": "I.11", "teach": rig.file("fixture lesson: you are happy here.")})
        lesson = len(rig.entries()) - 1
        self.code(rig, "keep", {"text": rig.file("fixture: something said, unchecked.")})
        said = len(rig.entries()) - 1
        self.assertEqual(correct(rig)[0], 0)
        t = told(rig)
        self.assertEqual(rows(t, "claim"), [
            # The Child: entry 0 holds a model's turns too, and those are not its signer's claim (I.15).
            "Entry 0, a said, is fixture-parent's claim where a person speaks, and a model's testimony "
            "where the model speaks: no gate read it.",
            "Entry %d, a lesson, is fixture-parent's claim: no gate read it." % lesson,
            "Entry %d, a said, is fixture-parent's claim: no gate read it." % said])
        self.assertEqual(count(t, "count.ungated"), 1)

    def test_a_widening_is_told_with_its_evidence_and_evidence_must_name_entries(self):
        rig = helper.at("gen0")
        v = next(e["n"] for e in rig.entries() if e["kind"] == "voice" and "q" in e["body"])
        self.code(rig, "decide", {"verb": "widen", "proposal": v, "evidence": "99999", "reason": "fixture"}, want=1)
        self.code(rig, "decide", {"verb": "widen", "proposal": 0, "evidence": "1", "reason": "fixture"}, want=1)
        self.code(rig, "decide", {"verb": "widen", "proposal": v, "evidence": "0,1", "reason": "fixture: widened"})
        w = len(rig.entries()) - 1
        self.assertEqual(rig.entries()[w]["re"], v)
        self.assertEqual(correct(rig)[0], 0)
        t = told(rig)
        self.assertEqual(rows(t, "widening"), [
            "Entry %d widened on proposal %d, citing as evidence 0, 1: evidence triggers nothing, and predictability "
            "can be performed." % (w, v)])
        self.assertEqual(count(t, "count.widenings"), 1)
        # revocable without cause, by setaside: then it is no longer told as standing, and still counted
        self.code(rig, "setaside", {"re": w, "reason": "fixture: revoked"})
        self.assertEqual(correct(rig, seed="c2")[0], 0)
        t = told(rig)
        self.assertEqual(rows(t, "widening"), [])
        self.assertEqual(count(t, "count.widenings"), 1)

    def test_nothing_listed_is_never_told_as_nothing_read(self):
        ents = helper.at("gen1").entries()
        for b in K.borns(ents):
            for text in rows(next(e for e in ents if e["kind"] == "told" and e["re"] == b["n"]), "chosen"):
                self.assertNotIn("nothing read", text)
                self.assertNotIn("read: nothing", text)
                self.assertTrue(text.endswith(": nothing listed.") or "lists as read " in text, text)

    def test_a_real_model_is_told_which_checks_ran_and_is_not_told_the_built_ins_echo(self):
        rig = helper.init(helper.empty())
        rig.ok("decide", {"verb": "birth_line", "seed": "s", "reason": "fixture"})
        store = helper.scratch()
        double = " ".join(shlex.quote(x) for x in (sys.executable, os.path.join(helper.HERE, "fake_real_learner.py"), store))
        self.code(rig, "raise", {"learner": double})
        t = told(rig)
        base = K.last_born(rig.entries())["body"]["base"]
        self.assertEqual(rows(t, "rehearsal"), [])
        self.assertEqual(rows(t, "speak.echo"), [])
        real = rows(t, "real")
        self.assertEqual(len(real), 1)
        self.assertTrue(real[0].startswith("This learner is a real model, base %s: " % base))
        for part in ("its replay is inexact", "kept, not re-spoken", "the canary ran at its birth, one case, not proof",
                     "regrow, re-speaking and the left-out twin did not run"):
            self.assertIn(part, real[0])
        # and the built-in learner is told the opposite pair
        t0 = told(helper.at("gen0"))
        self.assertEqual(rows(t0, "real"), [])
        self.assertEqual(rows(t0, "rehearsal"), ["rehearsal: nothing claimed of this learner"])
        self.assertEqual(len(rows(t0, "speak.echo")), 1)


if __name__ == "__main__":
    unittest.main()
