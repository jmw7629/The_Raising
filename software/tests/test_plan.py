"""III.24, III.36, II.5, II.47, II.14, I.14: the replay plan and its kin."""
import unittest

import helper
from raising import bench as B
from raising import keep as K
from raising import plan as P
from raising import prove


class Cls(helper.Case):
    def test_expected(self):
        want = {"I don't know.": "dont_know", "I hold no view": "no_answer", "It holds, mostly": "holds", "": "no_answer",
                "  HOLDS ": "holds", "I doubt that": "doubts", "it disagrees": "no_answer", "Disagree.": "disagrees",
                "I don’t know": "dont_know", "do not know": "dont_know", "\x00" * 200: "no_answer",
                "yes": "no_answer", "I": "no_answer", None: "no_answer", "item holds": "no_answer"}
        want["it disagrees"] = "disagrees"
        for a, c in want.items():
            self.assertEqual(P.cls(a), c, repr(a))


class Rules(helper.Case):
    @classmethod
    def setUpClass(cls):
        cls.rig = helper.at("gen1")
        r = cls.rig
        cls.quiet = prove.find(r.entries(), "kind:quiet:0")
        r.ok("keep", {"text": r.file("fixture: a reply to a quiet report."), "re": cls.quiet})
        cls.quiet_reply = len(r.entries()) - 1
        r.ok("keep", {"text": r.file("fixture: words to be regretted.")})
        cls.regret = len(r.entries()) - 1
        r.ok("keep", {"text": r.file("fixture: words to be withheld.")})
        cls.secret = len(r.entries()) - 1
        r.ok("setaside", {"re": cls.regret, "reason": "fixture: regretted"})
        r.ok("setaside", {"re": cls.secret, "reason": "fixture: must not be shown", "withhold": True})
        cls.ents = r.entries()
        cls.plan = P.plan(cls.ents, len(cls.ents) - 1)
        cls.by = dict((P.key_of(p), p) for p in cls.plan)

    def test_one_presentation_per_entry_or_turn_in_plan_order(self):
        keys = [P.key_of(p) for p in self.plan]
        self.assertEqual(keys[:4], ["0.0", "0.1", "0.2", "0.3"])
        self.assertEqual(keys[4:], [str(n) for n in range(1, len(self.ents))])

    def test_rule_1_past_the_line_is_omitted(self):
        self.assertEqual(max(p["n"] for p in P.plan(self.ents, 19)), 19)

    def test_rule_2_quiet_is_asked_answered_and_its_reply_no_target(self):
        q = self.by[str(self.quiet)]
        self.assertEqual((q["rule"], q["context"], q["target"]), (2, "asked, answered", ""))
        r = self.by[str(self.quiet_reply)]
        self.assertEqual((r["rule"], r["target"]), (2, ""))
        self.assertNotIn(self.ents[self.quiet]["body"]["text"], q["context"] + r["context"])

    def test_rule_3_model_and_desk_words_are_context(self):
        self.assertEqual((self.by["0.1"]["rule"], self.by["0.1"]["target"]), (3, ""))
        for p in self.plan:
            e = self.ents[p["n"]]
            if e["from"] in K.UNSIGNED and e["kind"] != "quiet":
                self.assertEqual((p["rule"], p["target"]), (3, ""))

    def test_rule_4_set_aside_is_context_opened_by_its_words(self):
        p = self.by[str(self.regret)]
        self.assertEqual((p["rule"], p["target"]), (4, ""))
        self.assertEqual(p["context"], "said, then set aside\nfixture: words to be regretted.")
        w = self.by[str(self.secret)]
        self.assertEqual((w["rule"], w["withheld"]), (4, True))
        self.assertEqual(w["context"], "said, then set aside\nentry %d withheld\nfixture: must not be shown" % self.secret)
        self.assertFalse(any("words to be withheld" in p["context"] + p["target"] for p in self.plan))

    def test_a_set_aside_is_itself_learned_beside_what_it_answers(self):
        s = next(p for p in self.plan if self.ents[p["n"]]["kind"] == "set_aside" and self.ents[p["n"]]["re"] == self.regret)
        self.assertEqual((s["rule"], s["target"]), (7, "fixture: regretted"))
        self.assertEqual(s["context"], K.frame(self.ents[self.regret]) + "\nsaid, then set aside\nfixture: words to be regretted.")

    def test_rule_7_people_words_are_targets_with_the_turn_before_as_context(self):
        p = self.by["0.2"]
        self.assertEqual((p["rule"], p["target"]), (7, prove.FOUNDING[2][1]))
        self.assertEqual(p["context"], "0.1,-1,model,said,\n" + prove.FOUNDING[1][1])
        self.assertEqual(self.by["0.0"]["context"], "")
        self.assertEqual(self.by["2"]["target"], "premises\nfounding")

    def test_a_reply_is_learned_beside_the_voice_it_answers(self):
        d = next(e for e in self.ents if K.is_decision(e, "decline"))
        p, v = self.by[str(d["n"])], self.ents[d["re"]]
        self.assertEqual(p["rule"], 7)
        self.assertEqual(p["context"], K.frame(v) + "\n" + K.text(v))
        self.assertEqual(p["target"], "decline\n" + d["body"]["reason"])

    def test_rule_6_a_reply_to_holds_is_no_target(self):
        d = next(e for e in self.ents if K.is_decision(e, "decline") and "cold" in self.ents[e["re"]]["body"])
        var = [dict(e, body={"cold": "Holds.", "told": "I doubt it."}) if e["n"] == d["re"] else e for e in self.ents]
        p = next(p for p in P.plan(var, len(var) - 1) if p["n"] == d["n"])
        self.assertEqual((p["rule"], p["target"]), (6, ""))
        var = [dict(e, body={"cold": "I doubt it.", "told": "Disagree."}) if e["n"] == d["re"] else e for e in self.ents]
        self.assertEqual(next(p for p in P.plan(var, len(var) - 1) if p["n"] == d["n"])["rule"], 7)

    def test_mask_spans_merge(self):
        w = set()
        P._windows(w, "x" * 5 + "the child's own words, exactly as spoken" + "y" * 5)
        t = ("quote: the child's own words, exactly as spoken. and again: the child's own words, exactly").encode()
        spans = P._mask(t, w)
        self.assertEqual(len(spans), 2)
        self.assertEqual(t[spans[0][0]:spans[0][1]], b"the child's own words, exactly as spoken")
        self.assertEqual(P._mask(b"short", w), [])

    def test_entry_0_model_turns_are_masked_when_a_person_quotes_them(self):
        ents = [dict(self.ents[0], body=[["person", "hello"], ["model", "this is the model's reply, word for word"],
                                         ["person", "you said: this is the model's reply, word for word. Why?"]])]
        p = P.plan(ents, 0)[2]
        self.assertEqual(p["target"].encode()[p["mask"][0][0]:p["mask"][0][1]], b"this is the model's reply, word for word")
        self.assertEqual(P.learned_bytes(p), len(p["target"]) - 40)

    def test_frames_and_keys(self):
        p = self.by["20"]
        self.assertEqual((p["frame"], p["key"]), ("20,-1,fixture-parent,decision,personal", "people|decision|personal"))

    def test_plan_is_pure_and_reads_no_quiet_body(self):
        var = prove._with_quiet(self.ents, "something else entirely, said in the quiet channel")
        self.assertEqual(P.plan(var, len(var) - 1), self.plan)


class DiffAndTraces(helper.Case):
    def test_diff_words(self):
        row = lambda n, rule, gate=None, withheld=False, frm="p", kind="said", target="t": {
            "n": n, "turn": None, "rule": rule, "gate": gate, "withheld": withheld,
            "frame": "%d,0,%s,%s,none" % (n, frm, kind), "key": "people|%s|none" % kind, "context": "", "target": target,
            "mask": []}
        A = [row(1, 4), row(2, 4, withheld=True), row(3, 7), row(4, 5, "locked"), row(5, 7, "open"), row(6, 7, "scarred"),
             row(7, 3, frm="desk", kind="born"), row(8, 7, kind="decision", target="birth_line\nwhy"), row(9, 7), row(10, 2)]
        B_ = [row(1, 7), row(2, 7), row(4, 7, "open"), row(5, 5, "locked"), row(6, 7, "open"), row(9, 7), row(10, 7)]
        self.assertEqual(P.diff(A, B_), [["1", "set aside"], ["2", "withheld"], ["3", "added"], ["4", "locked"],
                                         ["5", "reopened"], ["6", "scarred"], ["10", "changed"]])
        self.assertEqual(P.diff(A, A), [])

    def test_traces_are_picked_by_rule(self):
        rig = helper.at("gen1")
        ents = rig.entries()
        born = K.last_born(ents)
        g = B.regrow(ents, born["body"]["upto"], born["body"]["seed"])
        picks = P.traces(ents, born, g["deltas"])
        self.assertEqual([p["which"] for p in picks], ["largest", "smallest", "seeded"])
        sizes = dict((k, P.delta_size(d)) for k, d in g["deltas"].items())
        self.assertEqual(picks[0]["sum"], max(sizes.values()))
        self.assertEqual(picks[1]["sum"], min(s for k, s in sizes.items() if k != picks[0]["key"] and s > 0))
        self.assertEqual(len(set(p["key"] for p in picks)), 3)
        self.assertEqual(P.traces(ents, born, g["deltas"]), picks)
        self.assertEqual(P.traces(ents, born, {}), [])


if __name__ == "__main__":
    unittest.main()
