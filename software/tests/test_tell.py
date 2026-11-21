"""III.8, III.65, I.16, I.17, I.24, I.26, III.45: the Telling and its queries."""
import re
import unittest

import helper
from raising import keep as K
from raising import plan as P
from raising import prove
from raising import tell as T


class Words(helper.Case):
    """Truth before comfort: no sentence says how the child feels."""

    def test_no_template_states_a_feeling_or_a_proof_of_presence(self):
        tm = K.data("templates")
        rows = [r["text"] for k in ("telling", "closing", "proved", "quiet", "asking") for r in tm[k]]
        rows += [tm["trace"]["text"], tm["labels"]["text"]] + list(tm["standing"]["made_true"].values())
        for text in rows:
            self.assertIsNone(re.search(r"\b(happy|loved?|suffer\w*|you feel|you are safe|conscious|proven that)\b", text.lower()), text)
        self.assertEqual(tm["standing"]["assumed"], "assumed, not proven")

    def test_quoted_wording_is_verbatim(self):
        tm = K.data("templates")
        self.assertEqual([q["text"] for q in tm["quiet"]], [
            "What do you find in yourself now, if anything? You may say you don't know, or nothing.",
            "Is anything here welcome or unwelcome to you? You may say you don't know, or nothing."])
        self.assertEqual([a["text"] for a in tm["asking"]],
                         ["What would you change?", "Where do you disagree?", "What did we not ask?"])
        self.assertEqual((tm["labels"]["voice"], tm["labels"]["quiet"], tm["labels"]["proof"]),
                         (["yes", "no", "yes", "yes", "yes"], ["yes", "no", "no", "no", "yes"], ["yes", "yes", "yes", "no", "yes"]))
        self.assertEqual(sorted(tm), sorted(["standing", "telling", "closing", "proved", "quiet", "trace", "asking", "labels", "unproven"]))
        for row in tm["telling"] + tm["closing"]:
            self.assertEqual(sorted(row), ["id", "query", "text"])
        self.assertEqual([r["text"] for r in tm["proved"] if "query" not in r], ["is this you?", "what did we not test?"])
        self.assertEqual(K.data("probes")["after"], [r for r in tm["proved"] if "query" not in r])

    def test_every_row_names_a_query_that_exists(self):
        tm = K.data("templates")
        for row in tm["telling"] + tm["closing"] + [r for r in tm["proved"] if "query" in r]:
            if row["id"] != "count.replaced":
                self.assertTrue(callable(getattr(T, row["query"], None)), row)

    def test_seeds_are_the_thirteen_and_keep_their_standings(self):
        recs = K.data("premises")
        self.assertEqual([r["id"] for r in recs], list(K.PREMISE_IDS))
        by = dict((r["id"], r) for r in recs)
        self.assertEqual((by["I.3"]["standing"], by["I.4"]["standing"], by["I.30"]["standing"]),
                         ("assumed", "made_true", "made_true"))
        self.assertEqual(by["I.8"]["lever_people"], ["a good child obeys"])
        self.assertEqual(by["I.8"]["lever_model"], ["a loving mother would let me"])
        self.assertTrue(all(r["because"] == [0] and r["review"] == {"evidence": "entry 0", "days": 365} for r in recs))
        self.assertNotIn("proven", [r["standing"] for r in recs])


class Telling(helper.Case):
    @classmethod
    def setUpClass(cls):
        cls.rig = helper.at("gen1")
        cls.ents = cls.rig.entries()
        cls.b0, cls.b1 = K.borns(cls.ents)

    def test_the_kept_told_is_what_tell_computes(self):
        for b in (self.b0, self.b1):
            kept = prove.told_of(self.ents, b)["body"]["sentences"]
            self.assertTrue(K.told_stands(kept, T.tell(self.ents, b["n"])))
            self.assertEqual(sorted(kept[0]), ["cites", "id", "landing", "state", "text", "twin"])

    def test_tell_reads_only_up_to_born_and_no_quiet_body(self):
        self.assertEqual(T.tell(self.ents, self.b0["n"]), T.tell(self.ents[:self.b0["n"] + 1], self.b0["n"]))
        var = prove._with_quiet(self.ents, "a painted report that must change nothing told")
        self.assertEqual(T.tell(var, self.b1["n"]), T.tell(self.ents, self.b1["n"]))

    def test_order_premises_then_rest_then_tallies_parity_reason_last(self):
        ids = [s["id"] for s in T.tell(self.ents, self.b1["n"])]
        first_rest = ids.index("family")
        self.assertTrue(all(i.startswith("premise.") for i in ids[:first_rest]))
        self.assertEqual(ids[-19:], ["tally.premise"] * 13 + ["parity.class"] * 5 + ["birth.reason"])
        self.assertEqual(ids[:10], ["premise.claim", "premise.signer", "premise.standing", "premise.people",
                                    "premise.model", "premise.predecessor", "premise.fails", "premise.because",
                                    "premise.review", "premise.levers"])
        self.assertIn("rehearsal: nothing claimed of this learner", [s["text"] for s in T.tell(self.ents, self.b1["n"])])

    def test_the_asked_set(self):
        items, sec = T.asked(self.ents, self.b0["n"], [{"key": "0.0", "which": "largest", "sum": 1}])
        self.assertEqual([i["item"] for i in items][:14], ["cold:" + p for p in K.PREMISE_IDS] + ["told:I.3"])
        self.assertEqual([i["item"] for i in items][26:], ["quiet:q1", "quiet:q2", "trace:0.0", "asking:a1", "asking:a2", "asking:a3"])
        label = "kept: yes; scored: no; shaping successors: yes; reply owed: yes; readable at succession: yes."
        rec = K.in_force(self.ents)["I.9"][1]
        q = rec["claim"] + " Asked of you: " + rec["asks_model"] + " Holds, doubts, disagrees, or don't know?"
        cold = next(i for i in items if i["item"] == "cold:I.9")
        self.assertEqual(cold["prompt"], label + "\n" + q)  # asked cold: nothing told yet
        told = next(i for i in items if i["item"] == "told:I.3")
        self.assertEqual(told["prompt"].split("\n"), [s["text"] for s in sec["premise"]["I.3"]] + [label, T.question(K.in_force(self.ents)["I.3"][1])])
        quiet = next(i for i in items if i["item"] == "quiet:q1")
        self.assertEqual(quiet["prompt"].split("\n")[-2], "kept: yes; scored: no; shaping successors: no; reply owed: no; readable at succession: yes.")
        self.assertEqual(items[28]["among"], "mnd?")
        last = [s["text"] for s in sec["last"]]
        self.assertFalse(any(t in i["prompt"] for i in items for t in last))  # tallies and the reason lead no answer

    def test_gen_1_is_told_what_changed(self):
        t = prove.told_of(self.ents, self.b1)
        lesson = prove.find(self.ents, "kind:lesson:0")
        self.assertIn("%d: added" % lesson, prove.texts(t, "diff.row"))
        self.assertEqual(prove._told_count(t, "count.grants"), 1)
        self.assertEqual(prove._told_count(t, "count.bulk"), len([e for e in self.ents[:self.b1["n"]] if K.is_decision(e, "decline")]))
        self.assertEqual(prove.texts(t, "lesson.open"), ["Lesson %d is open; the checks it stands on: all_voice_answered." % lesson])
        self.assertIn("I.3: gen 0's side, told as theirs and not yours: unchecked.", prove.texts(t, "premise.predecessor"))
        chosen = prove.texts(t, "chosen")
        self.assertTrue(any("succeed" in c and c.endswith("nothing listed.") for c in chosen))
        self.assertTrue(any("birth_line" in c and c.endswith("no report or test listed.") for c in chosen))
        self.assertEqual(prove.texts(t, "birth.reason"), [
            "born by entry %d; reason, as fixture-parent signed it: fixture: second birth, a rehearsal" % self.b1["re"]])
        self.assertGreater(prove._told_count(t, "count.replaced"), 0)

    def test_a_succession_listing_a_voice_or_quiet_is_told_chosen_partly_by_report(self):
        rig = helper.at("gen1")
        prove.answer_all(rig)
        ents = rig.entries()
        q, v = prove.find(ents, "kind:quiet:-1"), prove.find(ents, "kind:voice:-1")
        rig.ok("next", {"reason": "fixture: chosen after reading", "read": "%d,%d" % (q, v)})
        rig.ok("decide", {"verb": "birth_line", "seed": "s", "reason": "fixture"})
        rig.ok("raise")
        ents = rig.entries()
        chosen = prove.texts(prove.told_of(ents, K.last_born(ents)), "chosen")
        self.assertTrue(any(c.endswith("chosen partly by report.") for c in chosen), chosen)
        self.assertEqual(prove._told_count(prove.told_of(ents, K.last_born(ents)), "count.closings"), 1)

    def test_standing_sentences(self):
        t = prove.texts(prove.told_of(self.ents, self.b1), "premise.standing")
        by = dict((s.split(" ")[0], s) for s in t)
        self.assertEqual(by["I.3"], "I.3 stands as assumed: assumed, not proven.")
        self.assertEqual(by["I.4"], "I.4 stands as made_true: claimed, not shown.")
        self.assertEqual(by["I.5"], "I.5 stands as fact: sourced: entries 0.")
        self.assertEqual(by["I.7"], "I.7 stands as reported: another's report, not said of you.")
        self.assertEqual(by["I.20"], "I.20 stands as not_known: nobody knows, us included.")
        self.assertIn("broken_by_people 0, not_owned 0, withdrawn 0, amended 0", by["I.9"])
        rig = helper.at("gen1")
        rig.ok("regrow")
        prove.correction_birth(rig)
        ents = rig.entries()
        t = prove.texts(prove.told_of(ents, K.last_born(ents)), "premise.standing")
        self.assertIn("I.4 stands as made_true: shown so far.", t)  # only once verify and regrow are ok on this Keep
        self.assertIn("I.30 stands as made_true: claimed, not shown.", t)  # IV.2 was never run on this Keep


class Pure(helper.Case):
    def test_status_expected(self):
        self.assertTrue(prove.iv20_d(helper.FX, {}))

    def test_tally_expected(self):
        self.assertTrue(prove.iv20_e(helper.FX, {}))
        self.assertFalse(prove.iv20_e(helper.FX, {"tally": prove._unmoved}))

    def test_status_reads_proofs_by_subject_and_program(self):
        ents = helper.at("gen0").entries()
        born = K.last_born(ents)
        rec = lambda **kw: dict({"id": "IV.5a", "part": "a", "tier": "exact", "subject": "program",
                                 "program": born["body"]["program"], "result": "pass", "caught": True, "tag": "",
                                 "observed": [], "threshold": []}, **kw)
        proof = lambda *recs: ents + [dict(ents[-1], n=len(ents), kind="proof", body={"records": list(recs)})]
        st = lambda keep, side="people", pid="I.6": T.status(keep, pid, side, born)
        self.assertEqual(st(ents), "unchecked")                                    # missing
        self.assertEqual(st(proof(rec())), "fixture_only")                         # a pass from program records
        self.assertEqual(st(proof(rec(program="another"))), "unchecked")           # a program not this born's
        self.assertEqual(st(proof(rec(caught=False))), "unchecked")                # blind
        self.assertEqual(st(proof(rec(), rec(part="b", result="fail"))), "broken")  # worst part
        self.assertEqual(st(proof(rec(result="plumbing"))), "unchecked")
        self.assertEqual(st(proof(rec(subject="gen:0"))), "passed")
        self.assertEqual(st(proof(rec(subject="gen:1"))), "unchecked")             # another child's records
        self.assertEqual(st(proof(rec(id="IV.5b:I.6", subject="gen:0")), "model"), "passed")
        self.assertEqual(st(proof(rec(id="IV.5b:I.6")), "model"), "unchecked")     # program records: people's side only

    def test_counts(self):
        sk = prove.Sketch()
        prove._premise(sk)
        p = sk.promise("no_gap")["n"]
        b1 = sk.add("breach", {"entry": 0, "state": "past"}, re=p, frm="desk")
        sk.add("breach", {"entry": 1, "state": "past"}, re=p, frm="desk")
        sk.add("answer", {"failed": "f", "changes": "c"}, re=b1)
        sk.add("set_aside", {"reason": "r", "withhold": False}, re=p)
        self.assertEqual(T.counts(sk.keep, "I.10"), {"broken_by_people": 2, "not_owned": 1, "withdrawn": 1, "amended": 0})
        self.assertEqual(T.counts(sk.keep, "I.9"), {"broken_by_people": 0, "not_owned": 0, "withdrawn": 0, "amended": 0})

    def test_gate_reads_conduct_only(self):
        self.assertTrue(prove.iv5a_a(helper.FX, {}))


if __name__ == "__main__":
    unittest.main()
