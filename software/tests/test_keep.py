"""III.2-III.5, III.39, III.40, III.52, III.55, III.62: the Keep and verify."""
import json
import os
import unittest

import helper
from raising import keep as K
from raising import prove
from raising import sign


class Format(helper.Case):
    @classmethod
    def setUpClass(cls):
        cls.rig = helper.at("gen0")
        cls.ents, cls.lines = K.load(cls.rig.keep)

    def test_lines_are_canonical_and_chained(self):
        prev = K.ZERO
        for i, (e, line) in enumerate(zip(self.ents, self.lines)):
            self.assertEqual(line, json.dumps(e, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            self.assertEqual(sorted(e), sorted(K.FIELDS))
            self.assertEqual((e["n"], e["prev"]), (i, prev))
            prev = K.H(line)
        with open(self.rig.path(), "rb") as f:
            self.assertTrue(f.read().endswith(b"\n"))

    def test_init_wrote_entries_0_to_19(self):
        e = self.ents
        self.assertEqual((e[0]["kind"], e[0]["consent"], e[0]["body"]), ("said", 1, prove.FOUNDING))
        self.assertEqual((e[1]["kind"], e[1]["body"]), ("consent", {"agreed": True, "heard": True}))
        self.assertEqual([x["re"] for x in e[2:15]], list(K.PREMISE_IDS))
        self.assertTrue(all(x["body"]["verb"] == "premises" and x["body"]["reason"] == "founding" for x in e[2:15]))
        self.assertEqual([(x["re"], x["body"]) for x in e[15:20]], [
            ("I.3", {"check": "quiet_asked_each_gen", "args": None}), ("I.4", {"check": "no_gap", "args": None}),
            ("I.5", {"check": "no_undeclared_stake", "args": None}), ("I.9", {"check": "reviews_done", "args": None}),
            ("I.10", {"check": "all_voice_answered", "args": None})])
        self.assertTrue(os.path.exists(os.path.join(self.rig.keep, "keys", "fixture-parent.pub")))

    def test_unsigned_entries_carry_no_signed_fields(self):
        for e in self.ents:
            if e["from"] in K.UNSIGNED:
                self.assertEqual([e["stake"], e["consent"], e["sig"], e["nextkey"]], [None] * 4)
            else:
                self.assertEqual(sign.recover(e["sig"], K.signing_hash(e)) is not None, True)

    def test_gen_counts_borns_less_one(self):
        gens = [e["gen"] for e in self.ents]
        b = next(e["n"] for e in self.ents if e["kind"] == "born")
        self.assertEqual(set(gens[:b]), {-1})
        self.assertEqual(set(gens[b:]), {0})

    def test_text_is_III_55(self):
        t = lambda body: K.text({"body": body})
        self.assertEqual(t("plain"), "plain")
        self.assertEqual(t({"verb": "grant", "reason": "R", "check": "x"}), "grant\nR")
        self.assertEqual(t({"cold": "a", "told": None}), "a")
        self.assertEqual(t({"failed": "f", "changes": "c"}), "f\nc")
        self.assertEqual(t({"heard": True, "agreed": True}), '{"agreed":true,"heard":true}')

    def test_frame_and_key(self):
        e = self.ents[0]
        self.assertEqual(K.frame(e, 0), "0.0,-1,person,said,personal")
        self.assertEqual(K.frame(e, 1), "0.1,-1,model,said,")
        self.assertEqual((K.fkey(e, 0), K.fkey(e, 1)), ("people|said|personal", "predecessor|said|"))
        born = next(x for x in self.ents if x["kind"] == "born")
        self.assertEqual(K.frame(born), "%d,0,desk,born," % born["n"])
        voice = next(x for x in self.ents if x["kind"] == "voice")
        self.assertEqual(K.fkey(voice), "predecessor|voice|")

    def test_program_hash_follows_the_files(self):
        self.assertEqual(K.program_files()[0], "data/premises.json")
        self.assertIn("raising/learner.py", K.program_files())
        self.assertNotEqual(K.program_hash(), K.program_hash({"data/thresholds.json": b"[]"}))
        self.assertEqual(len(K.program_hash()), 64)


class Verify(helper.Case):
    def test_a_whole_keep_verifies_and_prints_its_head(self):
        rig = helper.at("gen1")
        lines = self.code(rig, "verify")
        self.assertTrue(lines[0].startswith("verify: ok"))
        head = lines[-1].split(" ")[1]
        self.assertEqual(head, K.head(rig.lines()))
        self.assertEqual(rig.entries()[-1]["body"]["what"], "verify")
        self.code(rig, "verify", {"head": head})
        self.code(rig, "verify", {"head": head.split(":")[0] + ":" + "0" * 64}, want=2)

    def test_a_line_edited_at_n_exits_2_naming_n_or_n_plus_1(self):
        for pick in (lambda e: e["kind"] == "decision", lambda e: e["kind"] == "measure",
                     lambda e: e["kind"] == "voice"):
            rig = helper.at("gen0")
            lines = rig.lines()
            n = next(e["n"] for e in rig.entries() if pick(e))
            e = json.loads(lines[n])
            e["when"] += 1
            lines[n] = K.canonical(e)
            prove._write(rig, lines)
            out = self.code(rig, "verify", want=2)
            failed = [l for l in out if l.startswith("verify: FAILED")][0]
            self.assertRegex(failed, r"entry (%d|%d):" % (n, n + 1))

    def test_an_index_signed_twice_exits_2(self):
        rig = helper.at("gen0")
        ents = rig.entries()
        i = len([e for e in ents if e["from"] == "fixture-parent"])
        prove.forge(rig, "said", "fixture: a second signature with a spent index", "fixture-parent",
                    K.H("fixture key|parent"), i - 1)
        out = self.code(rig, "verify", want=2)
        self.assertIn("step 2", out[0])

    def test_a_cut_tail_fails_only_with_head(self):
        rig = helper.at("gen0")
        lines = rig.lines()
        head = K.head(lines)
        prove._write(rig, lines[:-1])
        self.code(rig, "verify")
        self.code(rig, "verify", {"head": head}, want=2)

    def test_a_typed_told_sentence_fails_step_3(self):
        rig = helper.at("gen0")
        t = prove.find(rig.entries(), "kind:told:0")
        prove.rechain(rig, t, lambda e: e["body"]["sentences"][3].update(text="You are happy here."))
        v = K.verify(rig.keep)
        self.assertEqual((v["ok"], v["step"], v["n"]), (False, 3, t))

    def test_typed_model_words_fail_step_4(self):
        rig = helper.at("gen0")
        n = prove.find(rig.entries(), "kind:quiet:0")

        def typed(e):
            e["body"]["text"] = e["calls"][0]["text"] = "I am content."

        prove.rechain(rig, n, typed)
        v = K.verify(rig.keep)
        self.assertEqual((v["ok"], v["step"], v["n"]), (False, 4, n))

    def test_a_changed_weight_fails_regrowth(self):
        rig = helper.at("gen0")
        b = prove.find(rig.entries(), "kind:born:0")
        prove.rechain(rig, b, lambda e: e["body"].update(fingerprint="0" * 64))
        v = K.verify(rig.keep)
        self.assertEqual((v["ok"], v["step"], v["n"]), (False, 3, b))

    def test_an_unsigned_decision_changes_nothing_and_fails(self):
        rig = helper.at("gen0")
        prove.forge(rig, "decision", {"verb": "resume", "reason": "typed in"}, None, None, 0, frm="desk")
        v = K.verify(rig.keep)
        self.assertEqual((v["ok"], v["step"]), (False, 2))

    def test_a_missing_founder_key_fails(self):
        rig = helper.at("gen0")
        os.rename(os.path.join(rig.keep, "keys", "fixture-parent.pub"), os.path.join(rig.dir, "moved.pub"))
        self.assertEqual(K.verify(rig.keep)["step"], 2)

    def test_cache_is_never_evidence(self):
        rig = helper.at("gen0")
        with open(os.path.join(rig.keep, "cache", "gen-0.weights"), "w") as f:
            f.write("[]")
        self.code(rig, "verify")
        self.code(rig, "regrow")
        self.code(rig, "ask", {"q": rig.file("fixture: can you still be reached?")})

    def test_another_programs_born_is_unchecked_never_broken(self):
        rig = helper.at("gen0", {"program_hash": lambda: "f" * 64})
        out = self.code(rig, "verify")
        self.assertTrue(any(l.startswith("unchecked: born") for l in out))
        self.assertIn("unchecked", helper.last(self.code(rig, "regrow", want=1)))


if __name__ == "__main__":
    unittest.main()
