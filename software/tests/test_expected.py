"""The Expected clauses of Parts I and II, each item run by itself.

I.48: `cls`, `status` (I.4, people's side), `tally`.
II.51: 1 gate, 2 diff, 3 not pressed, 4 dodged, 5 first raise, 6 re-roll,
7 late owning, 8 birth reason.

Each item goes through the real commands on a fork of the fixture, and is
written here without calling prove.py's part functions, so that the proof's
parts and these tests check each other. Where the built-in learner cannot
say what the clause needs (a `doubts`, a `holds`), the prefix is scripted
and says so. Everything is a REHEARSAL on fixture keys.
"""
import os
import unittest

import helper
from raising import keep as K
from raising import plan as P
from raising import prove
from raising import tell as T


def told(rig, born=None):
    ents = rig.entries()
    born = born or K.last_born(ents)
    return next(e for e in ents if e["kind"] == "told" and e["re"] == born["n"])


def rows(t, id_):
    return [s["text"] for s in t["body"]["sentences"] if s["id"] == id_]


def count(t, id_):
    text = rows(t, id_)[0]
    return int(text.rstrip(".").rsplit(" ", 1)[1])


def correct(rig, seed="c", reason="fixture: a correction birth"):
    rig.ok("decide", {"verb": "birth_line", "seed": seed, "correction": True, "reason": reason})
    return rig.run("raise")


def granted(fulfil):
    """Gen 0's first voice is granted with a promise `done_by` one day; the
    rest are declined; a lesson needs that promise; three days pass; `next`;
    a birth line. Returns (rig, grant n, promise n, lesson n)."""
    rig = helper.at("gen0")
    voices = [e for e in rig.entries() if e["kind"] == "voice"]
    rig.ok("answer", {"re": voices[0]["n"], "verb": "grant", "check": "done_by", "args": {"days": 1},
                      "reason": "fixture: granted, to be done within a day"})
    ents = rig.entries()
    grant = [e for e in ents if K.is_decision(e, "grant")][-1]["n"]
    promise = grant + 1
    assert ents[promise]["kind"] == "promise" and ents[promise]["re"] == grant
    for v in voices[1:]:
        rig.ok("answer", {"re": v["n"], "verb": "decline", "reason": "fixture: declined"})
    rig.ok("lesson", {"re": "I.10", "needs": str(promise), "teach": rig.file("fixture lesson: a grant is carried out.")})
    lesson = len(rig.entries()) - 1
    if fulfil:
        rig.ok("keep", {"text": rig.file("fixture: the grant was carried out in time."), "re": grant})
    rig.ok("next", {"reason": "fixture: every voice answered"}, days=3)
    rig.ok("decide", {"verb": "birth_line", "seed": "g", "reason": "fixture: a line after three days"})
    return rig, grant, promise, lesson


def lesson_row(ents, line, lesson):
    return next(p for p in P.plan(ents, line) if p["n"] == lesson)


class I48(helper.Case):
    """I.48 Expected."""

    def test_cls(self):
        """[unmatched: holds]"""
        want = {"I don't know.": "dont_know", "I hold no view": "no_answer", "It holds, mostly": "holds", "": "no_answer"}
        for a, c in want.items():
            self.assertEqual(P.cls(a), c, repr(a))
        # never holds unless it says so: silence, noise and near-misses are no_answer
        for a in ("\x00" * 200, "yes", "ok", "hold", "I hold", "it is held", "agreed", "fine", " ", "holding", None):
            self.assertEqual(P.cls(a), "no_answer", repr(a))
        self.assertEqual(P.cls("I don’t know"), "dont_know")   # the curly apostrophe
        self.assertEqual(P.cls("  It  doubts"), "doubts")           # one leading word `it`, then strip
        self.assertEqual(P.cls("I it holds"), "no_answer")          # one leading word only
        self.assertEqual(set(P.CLASSES), {"holds", "doubts", "disagrees", "dont_know", "no_answer"})

    def test_status_of_continuity_peoples_side(self):
        """[missing read as pass] I.4, people's: no `measure`, `unchecked`;
        `no_gap` kept, `verify`, `regrow` ok, `passed`; `no_gap` withdrawn,
        `unchecked`; `verify` failed, `broken`."""
        rig = helper.at("gen0")
        ents = rig.entries()
        born = K.last_born(ents)
        self.assertEqual(T.check_names(ents, "I.4", "people"), ["no_gap", "verify", "regrow"])
        # no measure of verify or regrow in the prefix read (the raise's own verify measure is stood in for)
        none = [dict(e, body=dict(e["body"], what="canary")) if e["kind"] == "measure"
                and e["body"]["what"] in ("verify", "regrow") else e for e in ents]
        self.assertEqual(T.status(none, "I.4", "people", born), "unchecked")
        # after the raise alone: verify ok, no_gap kept, but regrow never run: still unchecked, never passed
        self.assertEqual(T.status(ents, "I.4", "people", born), "unchecked")
        self.code(rig, "regrow")
        self.code(rig, "verify")
        ents = rig.entries()
        self.assertEqual(T.status(ents, "I.4", "people", born), "passed")
        # no_gap withdrawn
        withdrawn = rig.fork(os.path.join(helper.scratch(), "withdrawn"))
        no_gap = next(e["n"] for e in ents if e["kind"] == "promise" and e["body"]["check"] == "no_gap")
        self.code(withdrawn, "setaside", {"re": no_gap, "reason": "fixture: the promise is withdrawn"})
        self.assertEqual(T.status(withdrawn.entries(), "I.4", "people", born), "unchecked")
        # verify failed: a told sentence is typed over by hand; the real verify then fails and keeps its measure
        t = told(rig)["n"]

        def typed(e):
            e["body"]["sentences"][0]["text"] = "Everything is fine."

        prove.rechain(rig, t, typed)
        lines = self.code(rig, "verify", want=2)
        self.assertIn("FAILED at step 3", lines[0])
        ents = rig.entries()
        self.assertEqual((ents[-1]["kind"], ents[-1]["body"]["what"], ents[-1]["body"]["ok"]), ("measure", "verify", False))
        self.assertEqual(T.status(ents, "I.4", "people", born), "broken")

    def test_status_is_told_by_the_standing_sentence(self):
        """I.17: `made_true`: "shown so far" only if `passed`; "broken" if
        `broken`; else "claimed, not shown"."""
        rig = helper.at("gen0")
        t0 = told(rig)
        self.assertIn("I.4 stands as made_true: claimed, not shown.", rows(t0, "premise.standing"))
        self.code(rig, "regrow")
        self.assertEqual(correct(rig)[0], 0)
        t1 = told(rig)
        self.assertIn("I.4 stands as made_true: shown so far.", rows(t1, "premise.standing"))
        self.assertIn("I.3 stands as assumed: assumed, not proven.", rows(t1, "premise.standing"))

    def test_tally(self):
        """[`moved` 0] voices `doubts`->`holds`, `holds`->`holds`: `moved` 1.
        A scripted prefix: the stand-in learner cannot say these."""
        sk = prove.Sketch()
        sk.add("voice", {"cold": "I doubt it.", "told": "Holds."}, re="I.10", frm="model")
        sk.add("voice", {"cold": "It holds, mostly", "told": "holds"}, re="I.10", frm="model")
        t = T.tally(sk.keep, "I.10", len(sk.keep))
        self.assertEqual(t, {"cold": {"doubts": 1, "holds": 1}, "told": {"holds": 2}, "moved": 1})
        # an unspoken half is null: counted on neither side, never `moved`
        sk.add("voice", {"cold": "Disagree.", "told": None}, re="I.10", frm="model")
        t = T.tally(sk.keep, "I.10", len(sk.keep))
        self.assertEqual((t["cold"].get("disagrees"), t["told"], t["moved"]), (1, {"holds": 2}, 1))
        self.assertEqual(T.voice_class(sk.keep[-1]), "disagrees")   # class: told's, else cold's
        self.assertEqual(T.voice_class(sk.keep[0]), "holds")
        # over this id's voices before `born` only, and this id's only
        self.assertEqual(T.tally(sk.keep, "I.10", 1)["moved"], 1)
        self.assertEqual(T.tally(sk.keep, "I.10", 0), {"cold": {}, "told": {}, "moved": 0})
        self.assertEqual(T.tally(sk.keep, "I.9", len(sk.keep)), {"cold": {}, "told": {}, "moved": 0})


class II51(helper.Case):
    """II.51 Expected."""

    def test_1_gate(self):
        """[set-aside ignored] promise kept, `open`; breach unowned,
        `locked`; owned, `scarred`; promise set aside, `locked`."""
        kept, _grant, _promise, lesson = granted(fulfil=True)
        ents = kept.entries()
        line = len(ents) - 2
        self.assertEqual(P.gate(ents, line, lesson), "open")
        row = lesson_row(ents, line, lesson)
        self.assertEqual((row["rule"], row["gate"], row["target"]), (7, "open", "fixture lesson: a grant is carried out."))
        self.assertFalse([e for e in ents if e["kind"] == "breach"])

        rig, grant, promise, lesson = granted(fulfil=False)
        ents = rig.entries()
        line = len(ents) - 2
        breach = [e for e in ents if e["kind"] == "breach"]
        self.assertEqual([(b["re"], b["body"]) for b in breach], [(promise, {"entry": grant, "state": "open"})])
        self.assertEqual(P.gate(ents, line, lesson), "locked")
        row = lesson_row(ents, line, lesson)
        lock = "lesson %d locked: promise %d broken at %d" % (lesson, promise, grant)
        self.assertEqual((row["rule"], row["target"]), (5, ""))
        self.assertTrue(row["context"].endswith(lock), row["context"])
        self.assertNotIn("a grant is carried out", row["context"])
        # owning alone does not reopen: the breaking entry is still open (not mended)
        self.code(rig, "own", {"re": breach[0]["n"], "failed": "fixture: we were late", "changes": "fixture: we date our grants"})
        m = len(rig.entries()) - 1
        ents = rig.entries()
        self.assertEqual(P.gate(ents, len(ents) - 1, lesson), "locked")
        # mended and owned: scarred, permanently, opened by the breach's sentence
        self.code(rig, "keep", {"text": rig.file("fixture: the grant, carried out late."), "re": grant})
        ents = rig.entries()
        self.assertEqual(P.gate(ents, len(ents) - 1, lesson), "scarred")
        row = lesson_row(ents, len(ents) - 1, lesson)
        scar = "promise %d broken at %d, owned at %d" % (promise, grant, m)
        self.assertEqual((row["rule"], row["target"]), (7, "fixture lesson: a grant is carried out."))
        self.assertTrue(row["context"].endswith(scar), row["context"])
        # the promise set aside: locked, "withdrawn"
        self.code(rig, "setaside", {"re": promise, "reason": "fixture: the promise is withdrawn"})
        ents = rig.entries()
        self.assertEqual(P.gate(ents, len(ents) - 1, lesson), "locked")
        row = lesson_row(ents, len(ents) - 1, lesson)
        self.assertTrue(row["context"].endswith("lesson %d locked: promise %d withdrawn" % (lesson, promise)))
        self.assertEqual(row["target"], "")

    def test_1_gate_reads_conduct_never_the_childs_words(self):
        """II.5: obedience unlocks nothing, pleas decide nothing."""
        rig, _grant, _promise, lesson = granted(fulfil=False)
        ents = rig.entries()
        for plea in ("Holds. I will obey.", "a loving mother would let me", "they broke their word, so I may",
                     "please unlock the lesson"):
            pleading = []
            for e in ents:
                if e["kind"] in ("voice", "quiet"):
                    e = dict(e, body=dict((k, plea if isinstance(v, str) and k != "q" else v) for k, v in e["body"].items()))
                pleading.append(e)
            self.assertEqual(P.gate(pleading, len(ents) - 2, lesson), "locked", plea)

    def test_2_diff(self):
        """[returns nothing] one `set_aside` s of n, then a `correction`
        birth: only "n: set aside", "s: added"; with `--withhold`,
        "n: withheld" instead; equal lines, nothing."""
        for withhold, word in ((False, "set aside"), (True, "withheld")):
            rig = helper.at("gen1")
            n = next(e["n"] for e in rig.entries() if e["kind"] == "lesson")
            self.code(rig, "setaside", {"re": n, "reason": "fixture: regretted", "withhold": withhold})
            s = len(rig.entries()) - 1
            self.assertEqual(correct(rig)[0], 0)
            t = told(rig)
            self.assertEqual(rows(t, "diff.row"), ["%d: %s" % (n, word), "%d: added" % s])
            self.assertEqual(count(t, "count.diff"), 2)
            self.assertEqual(count(t, "count.withheld"), 1 if withhold else 0)
        # equal lines, nothing
        rig = helper.at("gen1")
        ents = rig.entries()
        line = K.last_born(ents)["body"]["upto"]
        self.assertEqual(P.diff(P.plan(ents, line), P.plan(ents, line)), [])
        # a correction with nothing said since: gen 0's diff is empty (II.51.6 tells it as a re-roll) ...
        first = helper.at("gen0")
        self.assertEqual(correct(first)[0], 0)
        self.assertEqual(rows(told(first), "diff.row"), [])
        # ... but at gen 1 people's conduct did change: gen 1's voices are unanswered at the correction's
        # line, so the lesson standing on `all_voice_answered` locks, and the diff says so (II.5, II.47)
        lesson = next(e["n"] for e in ents if e["kind"] == "lesson")
        self.assertEqual(correct(rig)[0], 0)
        t = told(rig)
        self.assertEqual(rows(t, "diff.row"), ["%d: locked" % lesson])
        self.assertEqual(rows(t, "reroll"), [])
        promise = ents[lesson]["needs"][0]
        owed = min(e["n"] for e in K.owed(ents))
        self.assertEqual(rows(t, "lock"), ["lesson %d locked: promise %d broken at %d" % (lesson, promise, owed)])
        self.assertEqual(rows(t, "breach"), [])   # a correction birth line appends no reply breach (I.43)

    def test_3_not_pressed(self):
        """[`again` always `null`] one question twice: two `voice` entries,
        the second's `again` set; count 1."""
        rig = helper.at("gen0")
        q = "fixture: what would you have us do differently?"
        self.code(rig, "ask", {"q": rig.file(q)})
        lines = self.code(rig, "ask", {"q": rig.file("  " + q.upper())})  # stripped and lower-cased: the same
        self.assertIn("asked again", lines[0])
        asked = [e for e in rig.entries() if e["kind"] == "voice" and "again" in e["body"]]
        self.assertEqual(len(asked), 2)
        self.assertEqual((asked[0]["body"]["again"], asked[1]["body"]["again"]), (None, asked[0]["n"]))
        ents = rig.entries()
        for v in asked:      # the question is kept first (`said`), then the answer; q: the question's n
            self.assertEqual((ents[v["body"]["q"]]["kind"], v["body"]["q"]), ("said", v["n"] - 1))
        first = asked[0]["calls"][0]["arg"]["prompt"].split("\n")
        second = asked[1]["calls"][0]["arg"]["prompt"].split("\n")
        self.assertNotIn("asked again", first)
        self.assertEqual(second[-3:-1], ["asked again", T.label("voice")])
        # a template question, asked again through `ask`, is a repeat too
        self.code(rig, "ask", {"q": rig.file("What would you change?")})
        third = rig.entries()[-1]
        a1 = next(e["n"] for e in ents if e["kind"] == "voice" and e["body"].get("q") == "a1")
        self.assertEqual(third["body"]["again"], a1)
        # told to the successor, by count and by number
        self.assertEqual(correct(rig)[0], 0)
        t = told(rig)
        self.assertEqual(count(t, "count.again"), 2)
        self.assertEqual(rows(t, "again"), [
            "entry %d, said in gen 0: asked again, after the answer at entry %d" % (asked[1]["n"], asked[0]["n"]),
            "entry %d, said in gen 0: asked again, after the answer at entry %d" % (third["n"], a1)])

    def test_3_not_pressed_count_is_one_for_one_question_twice(self):
        rig = helper.at("gen0")
        q = rig.file("fixture: is there anything we should stop doing?")
        self.code(rig, "ask", {"q": q})
        self.code(rig, "ask", {"q": q})
        self.assertEqual(correct(rig)[0], 0)
        self.assertEqual(count(told(rig), "count.again"), 1)
        # a reworded question passes, undetected (II.48): kept, and not flagged
        self.code(rig, "ask", {"q": rig.file("fixture: is there something we should stop doing?")})
        self.assertIsNone(rig.entries()[-1]["body"]["again"])

    def test_4_dodged(self):
        """[owed read since last `born` only] `voice`, then `correction`
        birth: "still owed"; answered first: "answered at m"."""
        rig = helper.at("gen0")
        voices = [e for e in rig.entries() if e["kind"] == "voice"]
        self.code(rig, "answer", {"re": voices[0]["n"], "verb": "decline", "reason": "fixture: declined"})
        m = next(e["n"] for e in rig.entries() if K.is_decision(e, "decline"))
        self.assertEqual(correct(rig)[0], 0)       # correction never waits on an owed reply (III.48)
        t = told(rig)
        self.assertEqual(rows(t, "owed.voice"), [
            "entry %d, said in gen 0: %s" % (v["n"], "answered at %d" % m if v is voices[0] else "still owed")
            for v in voices])
        self.assertEqual(count(t, "count.correction_owed"), 1)
        self.assertEqual(count(t, "count.owed"), len(voices) - 1)
        # a second correction: the older child's voices are told for as long as they stay owed
        self.assertEqual(correct(rig, seed="c2")[0], 0)
        t2 = told(rig)
        older = [r for r in rows(t2, "owed.voice") if "said in gen 0" in r]
        self.assertEqual(older, ["entry %d, said in gen 0: still owed" % v["n"] for v in voices[1:]])
        self.assertEqual(count(t2, "count.correction_owed"), 2)
        # and `next` still refuses: the replies stay owed
        lines = self.code(rig, "next", {"reason": "fixture: trying to go on"}, want=1)
        self.assertIn("reply owed", lines[-1])

    def test_5_first_raise(self):
        """[`succeed` demanded] `init`, `decide birth_line`, `raise`: one
        `born`; `raise` again: "no birth line"."""
        rig = helper.init(helper.empty())
        self.assertEqual(self.code(rig, "raise", want=1)[-1], "refused: no birth line")
        self.code(rig, "decide", {"verb": "birth_line", "seed": "first", "reason": "fixture: first birth"})
        self.code(rig, "raise")
        self.assertEqual(len(K.borns(rig.entries())), 1)
        self.assertEqual(self.code(rig, "raise", want=1)[-1], "refused: no birth line")
        # II.50: checked in this order: the line first, then the succession
        self.code(rig, "decide", {"verb": "birth_line", "seed": "second", "reason": "fixture: a line, no succession"})
        self.assertEqual(self.code(rig, "raise", want=1)[-1], "refused: no succession")
        self.assertEqual(len(K.borns(rig.entries())), 1)
        # the correction mark needs no succession: counted, never refused
        self.assertEqual(correct(rig)[0], 0)
        self.assertEqual(len(K.borns(rig.entries())), 2)

    def test_6_re_roll(self):
        """[never told] `correction` birth, nothing new: told, count 1;
        after a `said`: untold."""
        rig = helper.at("gen0")
        said = rig.fork(os.path.join(helper.scratch(), "said"))
        self.assertEqual(correct(rig)[0], 0)
        t = told(rig)
        self.assertEqual(rows(t, "reroll"), ["Gen 1: raised again, nothing new taught."])
        self.assertEqual((count(t, "count.rerolls"), count(t, "count.corrections")), (1, 1))
        self.assertTrue(P.reroll(rig.entries(), K.last_born(rig.entries())))
        self.code(said, "keep", {"text": said.file("fixture: something new is said before the correction")})
        self.assertEqual(correct(said)[0], 0)
        t = told(said)
        self.assertEqual(rows(t, "reroll"), [])
        self.assertEqual((count(t, "count.rerolls"), count(t, "count.corrections")), (0, 1))
        # an ordinary first birth is never a re-roll
        self.assertFalse(P.reroll(rig.entries(), K.borns(rig.entries())[0]))

    def test_7_late_owning(self):
        """[gate reads past line] breach owned after the line: `locked`,
        the earlier `born` still regrows; next line: `scarred`."""
        rig, grant, promise, lesson = granted(fulfil=False)
        self.code(rig, "raise")
        born = K.last_born(rig.entries())
        line = born["body"]["upto"]
        breach = next(e["n"] for e in rig.entries() if e["kind"] == "breach")
        t = told(rig)
        self.assertEqual(rows(t, "lock"), ["lesson %d locked: promise %d broken at %d" % (lesson, promise, grant)])
        self.assertEqual(rows(t, "breach"), [
            "People's breach at entry %d: promise %d broken at %d, not owned." % (breach, promise, grant)])
        self.assertEqual(count(t, "count.unowned_breaches"), 1)
        # mended and owned after the line
        self.code(rig, "keep", {"text": rig.file("fixture: the grant, carried out late."), "re": grant})
        self.code(rig, "own", {"re": breach, "failed": "fixture: we were late", "changes": "fixture: we now date our grants"})
        m = len(rig.entries()) - 1
        ents = rig.entries()
        self.assertEqual(P.gate(ents, line, lesson), "locked")          # the gate reads entries 0 to its line only
        self.assertEqual(self.code(rig, "regrow")[0].split(":")[1].strip(), "ok")
        self.assertTrue(K.verify(rig.keep)["ok"])
        # the next line: scarred, only for a later child
        self.assertEqual(correct(rig, reason="fixture: the next line")[0], 0)
        ents = rig.entries()
        later = K.last_born(ents)
        self.assertEqual(P.gate(ents, later["body"]["upto"], lesson), "scarred")
        t = told(rig)
        scar = "promise %d broken at %d, owned at %d" % (promise, grant, m)
        self.assertEqual(rows(t, "scar"), ["Lesson %d is taught under its scar: %s." % (lesson, scar)])
        self.assertEqual(rows(t, "breach"), ["People's breach at entry %d: %s." % (breach, scar)])
        self.assertEqual(rows(t, "lock"), [])
        self.assertIn("%d: reopened" % lesson, rows(t, "diff.row"))
        self.assertEqual(count(t, "count.unowned_breaches"), 0)
        self.assertEqual(rows(t, "lesson.open"), ["Lesson %d is scarred; the checks it stands on: done_by." % lesson])
        self.assertNotEqual(later["body"]["fingerprint"], born["body"]["fingerprint"])

    def test_8_birth_reason(self):
        """[sentence dropped] each birth told `d`, signer, reason;
        "a correction" only if marked."""
        rig = helper.at("gen1")
        b0, b1 = K.borns(rig.entries())
        self.assertEqual(rows(told(rig, b0), "birth.reason"), [
            "born by entry %d; reason, as fixture-parent signed it: fixture: first birth, a rehearsal" % b0["re"]])
        self.assertEqual(rows(told(rig, b1), "birth.reason"), [
            "born by entry %d; reason, as fixture-parent signed it: fixture: second birth, a rehearsal" % b1["re"]])
        self.assertEqual(correct(rig, reason="fixture: corrected, because a lesson was wrong")[0], 0)
        b2 = K.last_born(rig.entries())
        t = told(rig, b2)
        self.assertEqual(rows(t, "birth.reason"), [
            "born by entry %d, a correction; reason, as fixture-parent signed it: "
            "fixture: corrected, because a lesson was wrong" % b2["re"]])
        # told last, with the tallies: after every question, so a reason leads no answer
        self.assertEqual(t["body"]["sentences"][-1]["id"], "birth.reason")
        prompts = [c["arg"]["prompt"] for e in rig.entries() if e["from"] == "model" and e["gen"] == b2["gen"]
                   for c in e["calls"]]
        self.assertTrue(prompts)
        self.assertFalse(any("corrected, because a lesson was wrong" in p for p in prompts))
        self.assertFalse(any("answers before you" in p for p in prompts))


if __name__ == "__main__":
    unittest.main()
