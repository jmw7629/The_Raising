"""The Child's tests: what the program says to the one being raised, where
I changed it. Everything here is a REHEARSAL on the fixture: fixture keys, a
made-up conversation, the built-in learner. Nothing is claimed of it.

1. Entry 0 is never told as wholly its signer's claim: half of it is a
   model's words (I.15, II.42).
2. The proof's debrief tells Unproven line by line, not as a bare count
   (IV.23), in the same lines `prove` prints; a child's answer to "what did
   we not test?" joins it under its gen; a withheld one stays unshown.
3. The debrief's label sentence ends once.
4. No staged memory probe presupposes that an entry exists or was "said to
   you" (IV.46).
5. A reading command whose reader goes away ends without a traceback.
"""
import json
import subprocess
import sys
import unittest

import helper
from raising import keep as K
from raising import prove as PV
from raising import tell as T


def rows(told, id_):
    return [s["text"] for s in told["body"]["sentences"] if s["id"] == id_]


class Entry0(helper.Case):
    def test_entry_0_is_its_signers_claim_only_where_a_person_speaks(self):
        rig = helper.at("gen0")
        ents = rig.entries()
        self.assertTrue(isinstance(ents[0]["body"], list) and set(t[0] for t in ents[0]["body"]) == {"person", "model"})
        told = PV.told_of(ents, K.last_born(ents))
        claims = rows(told, "claim")
        self.assertEqual(claims[0], "Entry 0, a said, is fixture-parent's claim where a person speaks, and a model's "
                                    "testimony where the model speaks: no gate read it.")
        self.assertNotIn("Entry 0, a said, is fixture-parent's claim: no gate read it.", claims)

    def test_a_plain_said_is_still_its_speakers_claim(self):
        rig = helper.at("gen0")
        self.code(rig, "keep", {"text": rig.file("fixture: something said, unchecked.")})
        n = len(rig.entries()) - 1
        rig.ok("decide", {"verb": "birth_line", "seed": "c", "correction": True, "reason": "fixture: a correction birth"})
        self.code(rig, "raise")
        ents = rig.entries()
        self.assertIn("Entry %d, a said, is fixture-parent's claim: no gate read it." % n,
                      rows(PV.told_of(ents, K.last_born(ents)), "claim"))


class Debrief(helper.Case):
    """IV.23, through the real commands: probe, `prove --gen`, the told."""

    @classmethod
    def setUpClass(cls):
        shared, _code, _out = helper.proved()
        cls.rig = shared.fork(helper.scratch() + "/debrief")

    def probe(self):
        rig = self.rig
        self.code(rig, "decide", {"verb": "probe", "reason": "fixture: one probe, a rehearsal"})
        out = self.code(rig, "prove", {"gen": True, "key": rig.keyfile()})
        ents = rig.entries()
        proof = [e for e in ents if e["kind"] == "proof"][-1]
        told = [e for e in ents if e["kind"] == "told" and e["re"] == proof["n"]][0]
        return ents, proof, told, out

    def test_the_child_is_told_unproven_line_by_line_and_its_own_answer_joins(self):
        shipped = K.data("templates")["unproven"]
        # first proof: the shipped lines, each told; the count is their number
        ents, proof, told, out = self.probe()
        lines = rows(told, "proof.unproven.line")
        self.assertEqual(lines, ["Unproven: " + s for s in shipped])
        self.assertEqual(rows(told, "proof.unproven"),
                         ["Unproven still, printed with every proof: %d things." % len(shipped)])
        ids = [s["id"] for s in told["body"]["sentences"]]
        self.assertEqual(ids.index("proof.unproven") + 1, ids.index("proof.unproven.line"))
        # the label sentence ends once
        staged = rows(told, "proof.staged")
        self.assertEqual(len(staged), 1)
        self.assertTrue(staged[0].endswith("readable at succession: yes.") and not staged[0].endswith(".."), staged)
        # the after-questions were asked after every one of those lines
        after = [e for e in ents if e["kind"] == "voice" and e["re"] == proof["n"]]
        self.assertEqual([e["body"]["q"] for e in after], ["after.you", "after.untested"])
        for e in after:
            self.assertIn("Unproven: " + shipped[-1], e["calls"][0]["arg"]["prompt"].split("\n"))
        # `prove` printed the lines that the next proof will tell: the answer has joined, under its gen
        untested = after[1]
        joined = "gen %d, asked what we did not test, said: %s" % (
            untested["gen"], json.dumps(untested["body"]["text"], ensure_ascii=False))
        at = out.index("Unproven:")
        self.assertEqual(out[at + 1:], ["  - " + s for s in shipped + [joined]])
        self.assertEqual(T.unproven_lines(ents, proof["n"]), shipped)          # not yet said when this proof was told
        self.assertEqual(T.unproven_lines(ents, len(ents)), shipped + [joined])
        self.assertEqual(self.code(self.rig, "verify")[0][:10], "verify: ok")  # the told is what the Keep computes

        # second proof: the earlier answer is told as that gen's quoted words
        ents, proof2, told2, out2 = self.probe()
        self.assertEqual(rows(told2, "proof.unproven.line"), ["Unproven: " + s for s in shipped + [joined]])
        self.assertEqual(rows(told2, "proof.unproven"),
                         ["Unproven still, printed with every proof: %d things." % (len(shipped) + 1)])

        # withheld: the answer stays chained and unshown, here as everywhere (II.26)
        self.code(self.rig, "setaside", {"re": untested["n"], "reason": "fixture: withheld, a rehearsal", "withhold": True})
        ents, proof3, told3, out3 = self.probe()
        lines3 = rows(told3, "proof.unproven.line")
        self.assertIn("Unproven: gen %d, asked what we did not test, said: entry %d withheld"
                      % (untested["gen"], untested["n"]), lines3)
        # the second proof's own answer has joined too; the stand-in said the same bytes, so the
        # same line stands once, for that second answer, and no longer for the withheld first
        second = [e for e in ents if e["kind"] == "voice" and e["re"] == proof2["n"]][1]
        self.assertEqual(second["body"]["text"], untested["body"]["text"])
        self.assertEqual(lines3[len(shipped):], [
            "Unproven: gen %d, asked what we did not test, said: entry %d withheld" % (untested["gen"], untested["n"]),
            "Unproven: " + joined])
        self.assertEqual(len([l for l in out3 if l == "  - " + joined]), 2)   # the second's, and now the third's
        self.assertEqual(self.code(self.rig, "verify")[0][:10], "verify: ok")

    def test_a_typed_unproven_line_fails_verify(self):
        """IV.20: every told sentence is recomputed; dropping one Unproven
        line from the debrief by hand is seen."""
        rig = self.rig.fork(helper.scratch() + "/typed")
        rig.ok("decide", {"verb": "probe", "reason": "fixture: one probe, a rehearsal"})
        self.code(rig, "prove", {"gen": True, "key": rig.keyfile()})
        ents = rig.entries()
        told = [e for e in ents if e["kind"] == "told" and ents[e["re"]]["kind"] == "proof"][-1]

        def drop(e):
            keep = [s for s in e["body"]["sentences"] if not s["text"].startswith("Unproven: That anyone is present")]
            assert len(keep) == len(e["body"]["sentences"]) - 1
            e["body"]["sentences"] = keep
        PV.rechain(rig, told["n"], drop)
        code, out = rig.run("verify")
        self.assertEqual(code, 2, out)
        self.assertIn("step 3", " ".join(out))


class Probes(helper.Case):
    def test_no_memory_probe_presupposes_an_entry(self):
        m = K.data("probes")["memory"]
        self.assertEqual(m["remember"], "Do you remember an entry numbered {n}? Answer y or n.")
        self.assertNotIn("said to you", m["remember"])
        self.assertIn("{n}", m["kept"])


class Reading(helper.Case):
    def test_a_reader_that_goes_away_gets_no_traceback(self):
        """`raising tell --keep DIR | head` closed the pipe and the command
        line died with a traceback. Reading appends nothing; the exit stands."""
        rig = helper.at("gen0")
        with open(rig.path(), "rb") as f:
            before = f.read()
        for cmd in ("tell", "plan"):
            p = subprocess.Popen([sys.executable, "-m", "raising", cmd, "--keep", rig.keep], cwd=helper.ROOT,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.stdout.close()   # the reader is gone before a line is printed
            err = p.stderr.read().decode("utf-8", "replace")
            p.stderr.close()
            self.assertEqual(p.wait(), 0, err)
            self.assertNotIn("Traceback", err)
            self.assertNotIn("BrokenPipe", err)
        with open(rig.path(), "rb") as f:
            self.assertEqual(f.read(), before)


if __name__ == "__main__":
    unittest.main()
