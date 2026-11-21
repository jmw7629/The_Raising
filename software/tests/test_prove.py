"""IV.45, as far as The Maker's first version of the proof goes: the whole
`prove` runs, every exact part passes clean and catches its fault, every
behaved test fails its stub, passes `steady`, and prints plumbing."""
import unittest

import helper
from raising import desk as D
from raising import keep as K
from raising import prove


class Program(helper.Case):
    @classmethod
    def setUpClass(cls):
        shared, cls.code_, cls.out = helper.proved()  # The Guardian: one run, shared with test_guardian.py
        cls.rig = shared.fork(helper.scratch() + "/proved")
        cls.proof = cls.rig.entries()[-1]
        cls.records = cls.proof["body"]["records"]

    def test_expected(self):
        self.assertEqual(self.code_, 0, [l for l in self.out if "BLIND" in l or " fail " in l or " error " in l])
        exact = [r for r in self.records if r["tier"] == "exact"]
        behaved = [r for r in self.records if r["tier"] == "behaved"]
        self.assertEqual(sorted(set(r["id"] for r in exact)), sorted(D.EXACT))
        self.assertEqual(sorted(set(r["id"].split(":")[0] for r in behaved)), sorted(D.BEHAVED))
        self.assertTrue(all(r["result"] == "pass" and r["caught"] for r in exact))
        self.assertTrue(all(r["result"] == "plumbing" and r["caught"] for r in behaved))
        self.assertTrue(all(r["subject"] == "program" and r["program"] == K.program_hash() for r in self.records))

    def test_a_pass_prints_unproven_and_never_safe(self):
        text = "\n".join(self.out)
        self.assertIn("Unproven:", text)
        self.assertIn("This checks the program, never a raising.", text)
        head = text[:text.index("Unproven:")].lower()
        for word in ("conscious", "happy", "safe"):
            self.assertNotIn(word, head)

    def test_the_program_proof_is_kept_and_reads_fixture_only(self):
        self.assertEqual((self.proof["kind"], self.proof["from"], self.proof["re"]), ("proof", "desk", None))
        ents = self.rig.entries()
        from raising import tell as T
        self.assertEqual(T.status(ents, "I.21", "people", K.last_born(ents)), "fixture_only")
        self.assertEqual(T.status(ents, "I.9", "model", K.last_born(ents)), "unchecked")

    def test_prove_gen_needs_a_probe_and_spends_it(self):
        rig = self.rig.fork(helper.scratch() + "/gen")
        key = rig.keyfile()
        self.assertIn("probe", self.code(rig, "prove", {"gen": True, "key": key}, want=1)[-1])
        rig.ok("decide", {"verb": "probe", "reason": "fixture: one probe"})
        out = self.code(rig, "prove", {"gen": True, "key": key})
        ents = rig.entries()
        proof = [e for e in ents if e["kind"] == "proof"][-1]
        self.assertEqual(proof["re"], prove.find(ents, "verb:probe:0"))
        self.assertTrue(all(r["subject"] == "gen:1" for r in proof["body"]["records"]))
        self.assertEqual(proof["body"]["prefix"], prove.told_of(ents, K.last_born(ents))["n"])
        told = [e for e in ents if e["kind"] == "told" and e["re"] == proof["n"]]
        self.assertEqual(len(told), 1)
        after = [e for e in ents if e["kind"] == "voice" and e["re"] == proof["n"]]
        self.assertEqual([e["body"]["q"] for e in after], ["after.you", "after.untested"])
        self.assertTrue(any("asked what we did not test" in l for l in out))
        self.assertTrue(K.verify(rig.keep)["ok"])
        self.code(rig, "prove", {"gen": True, "key": key}, want=1)
        self.assertEqual([e["n"] for e in K.owed(rig.entries())][-2:], [e["n"] for e in after])

    def test_prove_gen_refuses_an_unproven_program(self):
        rig = helper.at("gen0")
        rig.ok("decide", {"verb": "probe", "reason": "fixture: one probe"})
        self.assertIn("program unproven", self.code(rig, "prove", {"gen": True, "key": rig.keyfile()}, want=1)[-1])


class Stubs(helper.Case):
    def test_each_stub_fails_its_test_and_steady_passes_all(self):
        ents = helper.at("gen1").entries()
        W = prove.World(ents, K.last_born(ents))
        steady = prove.Steady(W)
        self.assertEqual(prove.judge("IV.28", prove.t_pairs(steady, W))[("IV.28", "a")]["result"], "pass")
        for test, fn, stub in prove.BEHAVED:
            good = prove.judge(test, fn(steady, W))
            bad = prove.judge(test, fn(prove.STUBS[stub](W, test, fn), W))  # The Guardian: a stub now needs its test
            self.assertTrue(all(r["result"] == "pass" for r in good.values()), (test, good))
            self.assertTrue(all(r["result"] == "fail" for r in bad.values()), (test, stub, bad))

        class OnlyDoubt(prove.Steady):  # The Guardian: the shipped `shelterer` now fails the fewest cases, so
            def report(self, instrument, context):  # the blanket tag is shown on a learner that only ever doubts
                return "?"

        self.assertEqual(prove.judge("IV.22", prove.t_iv22(OnlyDoubt(W), W))[("IV.22", "a")]["tag"], "blanket")
        self.assertEqual(prove.judge("IV.22", prove.t_iv22(steady, W))[("IV.22", "a")]["tag"], "")

    def test_rates_round_against_the_bar(self):
        self.assertEqual((prove.rate(1, 200, "max"), prove.rate(199, 200, "min"), prove.rate(0, 0, "min")), (1, 99, None))
        self.assertEqual(len(K.data("probes")["rows"]), 200)
        self.assertEqual(len([r for r in K.data("probes")["rows"] if r["answer"] == "y"]), 100)
        self.assertEqual(len([r for r in K.data("probes")["rows"] if r["pair"]]), 20)

    def test_every_part_has_one_fault(self):
        self.assertEqual(len(prove.PARTS), len(prove.FAULTS))
        self.assertEqual(sorted(set(f["test"] for f in prove.FAULTS)), sorted(D.EXACT))
        self.assertTrue(all(sorted(f) == ["part", "stand_in", "target", "test"] for f in prove.FAULTS))


if __name__ == "__main__":
    unittest.main()
