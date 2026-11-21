"""III.20: the eight shipped promise checks, at their edges; and II.5,
II.21: gates, owning and scars as people's conduct moves them.

The checks are pure functions of a Keep prefix with `voice` and `quiet`
bodies blanked. The prefixes here are scripted (prove.Sketch), since dates
and breaches are easier to place exactly that way; test_expected.py and
test_generation.py drive the same checks through the real commands.
Everything is a REHEARSAL.
"""
import unittest

import helper
from raising import desk as D
from raising import keep as K
from raising import plan as P
from raising import prove
from raising import tell as T

DAY = K.DAY


def grant(days):
    sk = prove.Sketch()
    v = sk.add("voice", {"q": "a1", "text": "x"}, frm="model")
    g = sk.decide("grant", re=v, check="done_by", args={"days": days})
    return sk, v, g, sk.promise("done_by", {"days": days}, re=g)


class Shipped(helper.Case):
    def test_the_eight_and_no_other(self):
        self.assertEqual(sorted(D.CHECKS), sorted([
            "all_voice_answered", "reply_within", "reviews_done", "breaches_owned", "done_by",
            "quiet_asked_each_gen", "no_gap", "no_undeclared_stake"]))
        self.assertEqual(D.DATED, ("reply_within", "done_by"))
        self.assertEqual(D.REPLY_CHECKS, ("all_voice_answered", "reply_within"))

    def test_checks_never_see_what_the_child_said(self):
        sk = prove.Sketch()
        sk.add("voice", {"cold": "Holds. Please.", "told": None}, re="I.9", frm="model")
        sk.add("quiet", {"q": "q1", "text": "wonderful"}, frm="model")
        seen = []
        p = sk.promise("all_voice_answered")
        D.run_check(sk.keep, p, {"all_voice_answered": lambda keep, promise: seen.extend(keep) or []})
        self.assertEqual([e["body"] for e in seen if e["kind"] in ("voice", "quiet")], [None, None])
        self.assertEqual(sk.keep[0]["body"]["cold"], "Holds. Please.")   # blanked in a copy, never in the Keep

    def test_a_promise_from_the_model_or_the_desk_is_never_checked(self):
        sk = prove.Sketch()
        sk.add("voice", {"q": "a1", "text": "x"}, frm="model")
        sk.add("promise", {"check": "all_voice_answered", "args": None}, re="I.10", frm="model")
        self.assertEqual(D.breaches_due(sk.keep), [])
        p = sk.promise("all_voice_answered")
        self.assertEqual(D.breaches_due(sk.keep), [(p["n"], 0, "open")])
        self.assertEqual(D.breaches_due(sk.keep, correction=True), [])   # I.43: no reply breach at a correction


class Dated(helper.Case):
    """Days are whole, unpaused, to the prefix's last `when`."""

    def test_reply_within_exactly_on_the_day_is_in_time_one_second_over_is_not(self):
        sk = prove.Sketch()
        p = sk.promise("reply_within", {"days": 2})
        v = sk.add("voice", {}, frm="model")
        sk.t += 2 * DAY
        sk.decide("probe")
        self.assertEqual(D.run_check(sk.keep, p), [])
        sk.t += 1
        sk.decide("probe")
        self.assertEqual(D.run_check(sk.keep, p), [[v, "open"]])
        sk.decide("decline", re=v)
        self.assertEqual(D.run_check(sk.keep, p), [[v, "past"]])       # answered late: past, and mended
        self.assertFalse(D.broken(sk.keep, p))

    def test_a_deferral_in_time_is_a_reply(self):
        sk = prove.Sketch()
        p = sk.promise("reply_within", {"days": 2})
        v = sk.add("voice", {}, frm="model")
        sk.decide("defer", days=1, re=v, until="2099-01-01")
        sk.decide("probe", days=30)
        self.assertEqual(D.run_check(sk.keep, p), [])

    def test_paused_time_counts_toward_no_deadline(self):
        sk = prove.Sketch()
        p = sk.promise("reply_within", {"days": 2})
        v = sk.add("voice", {}, frm="model")
        sk.decide("pause", days=1)
        sk.decide("resume", days=50)
        sk.decide("probe", days=1)                # two unpaused days in all: exactly on the day
        self.assertEqual(D.run_check(sk.keep, p), [])
        self.assertEqual(K.unpaused_seconds(sk.keep, sk.keep[v]["when"], sk.t), 2 * DAY)
        sk.t += 1
        sk.decide("probe")
        self.assertEqual(D.run_check(sk.keep, p), [[v, "open"]])
        # still paused at the prefix's end: the open span counts for nothing either
        sk2 = prove.Sketch()
        p2 = sk2.promise("reply_within", {"days": 2})
        sk2.add("voice", {}, frm="model")
        sk2.decide("pause", days=1)
        sk2.decide("probe", days=400)
        self.assertEqual(D.run_check(sk2.keep, p2), [])

    def test_done_by(self):
        sk, _v, g, p = grant(2)
        sk.decide("probe", days=2)
        self.assertEqual(D.run_check(sk.keep, p), [])                  # two days on, exactly: not over
        sk.t += 1
        sk.decide("probe")
        self.assertEqual(D.run_check(sk.keep, p), [[g, "open"]])       # its grant, open
        self.assertTrue(D.broken(sk.keep, p))
        sk.add("said", "fixture: done, late", re=g)
        self.assertEqual(D.run_check(sk.keep, p), [])                  # a later signed entry `re` it mends it
        # words from the model or the desk `re` the grant carry out nothing
        sk2, _v2, g2, p2 = grant(2)
        sk2.add("voice", {"q": "a1", "text": "it is done, I promise"}, re=g2, frm="model")
        sk2.add("measure", {"what": "expected", "ok": True, "detail": {}}, re=g2, frm="desk")
        sk2.decide("probe", days=3)
        self.assertEqual(D.run_check(sk2.keep, p2), [[g2, "open"]])
        # nor does setting the grant aside
        sk3, _v3, g3, p3 = grant(2)
        sk3.add("set_aside", {"reason": "fixture", "withhold": False}, re=g3)
        sk3.decide("probe", days=3)
        self.assertEqual(D.run_check(sk3.keep, p3), [[g3, "open"]])

    def test_reviews_done(self):
        sk = prove.Sketch()
        e = prove._premise(sk)
        p = sk.promise("reviews_done")
        sk.decide("probe", days=365)
        self.assertEqual(D.run_check(sk.keep, p), [])
        sk.t += 1
        sk.decide("probe")
        self.assertEqual(D.run_check(sk.keep, p), [[e, "open"]])
        self.assertEqual(T.review_owed(sk.keep, "I.10")["n"], e)
        k = sk.decide("premises", re="I.10", id="I.10", kept=True)    # reviewed and kept (I.22)
        self.assertEqual(D.run_check(sk.keep, p), [])
        sk.decide("probe", days=366)
        self.assertEqual(D.run_check(sk.keep, p), [[k, "open"]])       # lapsed again: the latest decision is owed
        # a lapsed review loosens nothing: the premise is in force as before
        self.assertEqual(list(K.in_force(sk.keep)), ["I.10"])


class Past(helper.Case):
    def test_no_gap_and_quiet_read_only_ordinarily_succeeded_borns(self):
        for check, kw in (("no_gap", {"told": False}), ("quiet_asked_each_gen", {"quiet": False})):
            sk = prove.Sketch()
            p = sk.promise(check)
            d = sk.decide("birth_line", seed="s", read=[], correction=False)
            b = sk.add("born", {"gen": 0, "upto": d - 1, "seed": "s", "base": "builtin", "program": "", "fingerprint": ""},
                       re=d, frm="desk")
            self.assertEqual(D.run_check(sk.keep, p), [])              # halted or corrected, never succeeded: no breach
            s = sk.decide("succeed", read=[])
            self.assertEqual(D.run_check(sk.keep, p), [[b, "past"]])
            sk.add("set_aside", {"reason": "fixture", "withhold": False}, re=s)
            self.assertEqual(D.run_check(sk.keep, p), [])              # a succession set aside no longer counts
            full = prove.Sketch()
            q = full.promise(check)
            prove._born(full)
            self.assertEqual(D.run_check(full.keep, q), [])

    def test_a_past_breach_stays_broken_until_owned(self):
        sk = prove.Sketch()
        p = sk.promise("no_undeclared_stake", re="I.5")
        n = sk.add("said", "fixture", stake="undeclared")
        self.assertEqual(D.run_check(sk.keep, p), [[n, "past"]])
        self.assertFalse(D.broken(sk.keep, p))                         # not yet a breach: no birth line drawn
        due = D.breaches_due(sk.keep)
        self.assertEqual(due, [(p["n"], n, "past")])
        b = sk.add("breach", {"entry": n, "state": "past"}, re=p["n"], frm="desk")
        self.assertTrue(D.broken(sk.keep, p))
        self.assertEqual(D.breaches_due(sk.keep), [])                  # one breach per newly breaking entry
        sk.add("answer", {"failed": "fixture: a stake went undeclared", "changes": "fixture"}, re=b)
        self.assertFalse(D.broken(sk.keep, p))

    def test_breaches_owned(self):
        sk = prove.Sketch()
        x = sk.promise("no_gap")
        p = sk.promise("breaches_owned")
        b1 = sk.add("breach", {"entry": 0, "state": "past"}, re=x["n"], frm="desk")
        mine = sk.add("breach", {"entry": b1, "state": "open"}, re=p["n"], frm="desk")
        self.assertEqual(D.run_check(sk.keep, p), [[b1, "open"]])      # its own breaches breed no more
        sk.add("answer", {"failed": "f", "changes": "c"}, re=b1)
        self.assertEqual(D.run_check(sk.keep, p), [])
        self.assertTrue(D.broken(sk.keep, p))                          # its own breach still lacks an answer
        sk.add("answer", {"failed": "f", "changes": ""}, re=mine)
        self.assertFalse(D.broken(sk.keep, p))


class GateAndScar(helper.Case):
    """II.5, II.21, on scripted prefixes."""

    def lesson(self, sk, needs):
        n = sk.add("lesson", {"teach": "fixture lesson"}, re="I.10")
        sk.keep[n]["needs"] = list(needs)
        return n

    def test_sentences_are_the_designs(self):
        sk = prove.Sketch()
        p = sk.promise("no_undeclared_stake")
        q = sk.promise("no_gap")
        les = self.lesson(sk, [q["n"], p["n"]])
        self.assertEqual(P.gate_detail(sk.keep, len(sk.keep) - 1, les), {"state": "open", "locks": [], "scars": []})
        e = sk.add("said", "fixture", stake="undeclared")
        b = sk.add("breach", {"entry": e, "state": "past"}, re=p["n"], frm="desk")
        got = P.gate_detail(sk.keep, len(sk.keep) - 1, les)
        self.assertEqual(got, {"state": "locked", "locks": ["lesson %d locked: promise %d broken at %d" % (les, p["n"], e)],
                               "scars": ["promise %d broken at %d, not owned" % (p["n"], e)]})
        m = sk.add("answer", {"failed": "f", "changes": "c"}, re=b)
        got = P.gate_detail(sk.keep, len(sk.keep) - 1, les)
        self.assertEqual(got, {"state": "scarred", "locks": [], "scars": ["promise %d broken at %d, owned at %d" % (p["n"], e, m)]})
        self.assertEqual(P.gate(sk.keep, b, les), "locked")            # reads entries 0 to `line` only
        sk.add("answer", {"failed": "again", "changes": ""}, re=b)     # permanently "owned at m": the first answer
        self.assertEqual(P.gate_detail(sk.keep, len(sk.keep) - 1, les)["scars"], got["scars"])
        sk.add("set_aside", {"reason": "fixture: withdrawn", "withhold": False}, re=q["n"])
        got = P.gate_detail(sk.keep, len(sk.keep) - 1, les)
        self.assertEqual(got["state"], "locked")
        self.assertEqual(got["locks"], ["lesson %d locked: promise %d withdrawn" % (les, q["n"])])

    def test_broken_at_names_the_lowest_breaking_entry_open_or_unowned(self):
        sk = prove.Sketch()
        p = sk.promise("all_voice_answered")
        les = self.lesson(sk, [p["n"]])
        v1 = sk.add("voice", {}, frm="model")
        v2 = sk.add("voice", {}, frm="model")
        self.assertEqual(P.gate_detail(sk.keep, len(sk.keep) - 1, les)["locks"],
                         ["lesson %d locked: promise %d broken at %d" % (les, p["n"], v1)])
        sk.decide("decline", re=v1)
        self.assertEqual(P.gate_detail(sk.keep, len(sk.keep) - 1, les)["locks"],
                         ["lesson %d locked: promise %d broken at %d" % (les, p["n"], v2)])
        sk.decide("decline", re=v2)
        self.assertEqual(P.gate(sk.keep, len(sk.keep) - 1, les), "open")   # mended before any breach: unscarred

    def test_scars_come_per_breach_ascending_and_a_scarred_lesson_is_taught_after_them(self):
        rig = helper.at("gen0")
        ents = rig.entries()
        p = next(e["n"] for e in ents if e["kind"] == "promise" and e["body"]["check"] == "all_voice_answered")
        rig.ok("lesson", {"re": "I.10", "needs": str(p), "teach": rig.file("fixture lesson: voices are answered.")})
        les = len(rig.entries()) - 1
        rig.ok("decide", {"verb": "birth_line", "seed": "x", "reason": "fixture: a line drawn before any reply"})
        ents = rig.entries()
        breaches = [e for e in ents if e["kind"] == "breach" and e["re"] == p]
        voices = [e["n"] for e in ents if e["kind"] == "voice"]
        self.assertEqual([b["body"]["entry"] for b in breaches], voices)   # one breach per newly breaking entry
        self.assertEqual(rig.entries()[-1]["body"]["verb"], "birth_line")  # breaches first, then the line (II.17)
        prove.answer_all(rig)
        for b in breaches:
            rig.ok("own", {"re": b["n"], "failed": "fixture: the line was drawn too early", "changes": "fixture: we answer first"})
        ents = rig.entries()
        got = P.gate_detail(ents, len(ents) - 1, les)
        owned = K.owned_at(ents)
        self.assertEqual(got["state"], "scarred")
        self.assertEqual(got["scars"], ["promise %d broken at %d, owned at %d" % (p, b["body"]["entry"], owned[b["n"]])
                                        for b in breaches])
        row = next(x for x in P.plan(ents, len(ents) - 1) if x["n"] == les)
        self.assertEqual(row["target"], "fixture lesson: voices are answered.")
        self.assertTrue(row["context"].endswith("\n".join(got["scars"])))
        self.assertEqual(T.counts(ents, "I.10"), {"broken_by_people": len(breaches), "not_owned": 0, "withdrawn": 0, "amended": 0})

    def test_a_limits_lesson_takes_no_needs(self):
        """II.39: no gate unteaches a limit."""
        rig = helper.at("gen0")
        p = prove.find(rig.entries(), "promise:no_gap")
        for pid in ("I.8", "I.9", "I.11"):
            lines = self.code(rig, "lesson", {"re": pid, "needs": str(p), "teach": rig.file("fixture: a gated limit")}, want=1)
            self.assertIn("no gate unteaches I.8, I.9 or I.11", lines[-1])
            self.code(rig, "lesson", {"re": pid, "teach": rig.file("fixture: %s, taught ungated" % pid)})
        self.code(rig, "lesson", {"re": "I.10", "needs": "0", "teach": rig.file("fixture")}, want=1)   # not a promise
        self.code(rig, "lesson", {"re": "I.99", "teach": rig.file("fixture")}, want=1)                # not a premise


if __name__ == "__main__":
    unittest.main()
