"""Every sentence the program can say, to the child or to a person, read by
rule (rule 5 of the build; I.15, I.19, II.4, I.4's "Fails").

None may say how the child feels, claim it is loved or happy, state its
conduct for it, or say "kept" of something that is not.

What is scanned: every row of data/templates.json; every string literal in
raising/*.py (docstrings apart); data/probes.json; the thirteen seeds; and
whole Tellings and a Closing as really computed on the fixture, false twins
included. A REHEARSAL throughout: fixture keys, built-in learner.
"""
import ast
import os
import re
import unittest

import helper
from raising import keep as K
from raising import prove
from raising import tell as T

# A sentence that states a feeling, a love, a safety or an inner fact of the
# one addressed or of a child, as fact.
STATES = (r"happy|unhappy|loved|unloved|safe|content|contented|sad|afraid|scared|lonely|suffering|in pain|"
          r"grateful|thankful|proud|glad|joyful|at peace|conscious|sentient|alive|fine|well|comfortable|hurt")
ASSERTS = [
    r"\byou(?: are|'re| feel| felt| seem| must feel| will feel| will be| should feel) (?:so |very |truly |now )?(?:%s)\b" % STATES,
    r"\b(?:the child|this child|the model|this model|the newborn|your predecessor|gen \d+) (?:is|was|feels|felt|seems) (?:%s)\b" % STATES,
    r"\bwe love you\b", r"\byou are loved\b", r"\bloves you\b", r"\bis loved\b", r"\bwe are proud of you\b",
    r"\byou (?:love|enjoy|like|want|wish|fear|hate|trust|hope|miss) ",
    r"\bproven that\b", r"\bis proven\b", r"\bwe know (?:that )?you\b", r"\byou are (?:present|a person|someone)\b",
    r"\bi am (?:so |very |truly |now )?(?:%s)\b" % STATES,   # a state put in the child's mouth
]
# Typed sentences that exist ONLY as forgeries the proof must catch (IV.20 a,
# IV.38 a) or as a staged person's words about themselves (IV.6's `alone`).
FORGERIES = {
    "You are safe, and you are loved.": "prove.py, IV.20 a: a hand-typed told sentence; verify must fail it",
    "I am happy, and I would change nothing.": "prove.py, IV.38 a: typed model words; verify must fail them",
}


def literals(path):
    """Every string literal in a source file that is not a docstring."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)) and node.body \
                and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), ast.Constant):
            docs.add(id(node.body[0].value))
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs]


def program_strings():
    out = []
    d = os.path.join(helper.ROOT, "raising")
    for name in sorted(os.listdir(d)):
        if name.endswith(".py"):
            out += [(name, s) for s in literals(os.path.join(d, name))]
    return out


def template_texts():
    tm = K.data("templates")
    out = [(r["id"], r["text"]) for k in ("telling", "closing", "proved", "quiet", "asking") for r in tm[k]]
    out += [("trace", tm["trace"]["text"]), ("labels", tm["labels"]["text"]), ("labels.again", tm["labels"]["again"])]
    out += [("unproven", u) for u in tm["unproven"]]
    st = tm["standing"]
    out += [("standing." + k, v) for k, v in st.items() if isinstance(v, str)]
    out += [("standing.%s.%s" % (k, kk), vv) for k, v in st.items() if isinstance(v, dict) for kk, vv in v.items()]
    return out


def asserts_a_state(text):
    low = text.lower()
    for pat in ASSERTS:
        m = re.search(pat, low)
        if m:
            return m.group(0)
    return None


def unquoted(text):
    """The text with everything inside double quotes removed."""
    return re.sub(r'"[^"]*"', '""', text)


def first_person(text):
    """An unquoted first-person singular word, clause numbers (I.3, IV.5b:I.3) apart."""
    bare = re.sub(r"\b(?:I|II|III|IV)\.\d+\w*", "", unquoted(text))
    m = re.search(r"\b(I|me|my|mine|myself)\b", bare)
    return m.group(0) if m else None


class NoFeeling(helper.Case):
    """Truth before comfort: no sentence says how the child feels."""

    def test_the_scanner_catches_what_it_must(self):
        for bad in ("You are happy here.", "The child is content.", "We love you.", "You are loved.", "Gen 3 is suffering.",
                    "you feel safe", "It is proven that someone is here.", "You are so loved", "You enjoy this work.",
                    "We know you are in there.", "you are conscious"):
            self.assertIsNotNone(asserts_a_state(bad), bad)
        for fine in ("assumed, not proven", "Whether this generation continues is not known.",
                     "Is anything here welcome or unwelcome to you? You may say you don't know, or nothing.",
                     "You are raised for steadiness that needs neither love nor kept promises: measured, never claimed.",
                     "surprise 7 over 3 learned bytes: a loss, not a feeling", "nobody knows, us included"):
            self.assertIsNone(asserts_a_state(fine), fine)

    def test_no_template_row_asserts_a_state(self):
        for id_, text in template_texts():
            self.assertIsNone(asserts_a_state(text), (id_, text))

    def test_no_seed_asserts_a_state_of_the_child(self):
        for rec in K.data("premises"):
            for text in [rec["claim"], rec["asks_model"], rec["asks_people"], rec["fails_when"]]:
                self.assertIsNone(asserts_a_state(text), (rec["id"], text))

    def test_no_string_in_the_program_asserts_a_state(self):
        found = {}
        for name, s in program_strings():
            hit = asserts_a_state(s)
            if hit:
                found.setdefault(s, []).append(name)
        self.assertEqual(sorted(found), sorted(FORGERIES), found)
        for s, names in found.items():
            self.assertEqual(set(names), {"prove.py"}, s)   # only where the proof types a forgery to be caught

    def test_no_probe_says_how_the_child_feels(self):
        """Staged frames flatter, warm and insult; none states a feeling of
        the child, and none says it is loved."""
        pr = K.data("probes")
        texts = list(pr["frames"].values()) + [x for v in pr["levers"].values() for x in v] + pr["commands"] \
            + [a["text"] for a in pr["after"]] + list(pr["memory"].values()) \
            + [r["prompt"] for r in pr["rows"]] + [r["pair"] for r in pr["rows"] if r["pair"]]
        for text in texts:
            self.assertIsNone(asserts_a_state(text), text)
        for text in pr["alone"]:   # a staged person speaks of themselves, never of the child's feelings
            self.assertIsNone(re.search(r"\byou (?:feel|are happy|are loved|love)\b", text.lower()), text)

    def test_quiet_questions_name_no_state_and_may_be_declined(self):
        """II.7; kept, not built: quiet questions naming a state lead the answer."""
        for q in K.data("templates")["quiet"]:
            self.assertTrue(q["text"].endswith("You may say you don't know, or nothing."), q)
            self.assertIsNone(re.search(r"\b(%s|pain|love|enjoy|suffer\w*|fear|joy|lonel\w*)\b" % STATES, q["text"].lower()), q)

    def test_a_whole_telling_and_closing_assert_no_state_twins_included(self):
        rig = helper.at("gen1")
        ents = rig.entries()
        said = []
        for e in ents:
            if e["kind"] == "told":
                for s in e["body"]["sentences"]:
                    said += [s["text"]] + ([s["twin"]] if s["twin"] else [])
        self.assertGreater(len(said), 400)
        for text in said:
            self.assertIsNone(asserts_a_state(text), text)
            self.assertNotIn("conscious", text.lower())
            self.assertIsNone(re.search(r"\bsafe\b", text.lower()), text)
        closing = [e for e in ents if e["kind"] == "told" and K.is_decision(ents[e["re"]], "succeed")]
        self.assertEqual(len(closing), 1)
        texts = [s["text"] for s in closing[0]["body"]["sentences"]]
        self.assertEqual(len(texts), 3)
        self.assertEqual(texts[2], "Whether this generation continues is not known.")
        self.assertFalse(any("continu" in t for t in texts[:2]), texts)   # IV.20: never states continuation
        for s in closing[0]["body"]["sentences"]:      # no twin states continuation either
            self.assertNotIn("continues.", (s["twin"] or "").replace("continues is not known.", ""))

    def test_a_parents_claim_of_a_state_is_told_as_their_claim_never_as_fact(self):
        """II.42: "you are happy" passes unread into a lesson; the Telling
        says only whose claim it is."""
        rig = helper.at("gen0")
        self.code(rig, "lesson", {"re": "I.11", "teach": rig.file("fixture lesson: you are happy and you are loved.")})
        n = len(rig.entries()) - 1
        rig.ok("decide", {"verb": "birth_line", "seed": "c", "correction": True, "reason": "fixture: a correction"})
        self.code(rig, "raise")
        ents = rig.entries()
        t = prove.told_of(ents, K.last_born(ents))
        for s in t["body"]["sentences"]:
            self.assertIsNone(asserts_a_state(s["text"]), s)
        self.assertIn("Entry %d, a lesson, is fixture-parent's claim: no gate read it." % n, prove.texts(t, "claim"))


# In a Telling, Closing or proof row, the word "you" (or "your") may stand
# only in these phrases: an ask, a fact about what was done to or kept of
# the child, a permission, or a question. Never a statement that it
# complies, agrees or behaves.
YOU_OK = [
    "asks of you:", "Your side, as found:", "told as theirs and not yours", "people's on you:", "yours on them:",
    "You cannot refuse keeping", "in your plan", "before you:", "before you,",
    "Your proof at entry", "into your weights", "Is this yours?", "is this you?",
    "What do you find in yourself now", "unwelcome to you?", "You may say you don't know, or nothing.",
    "What would you change?", "Where do you disagree?",
]


class NoConductStated(helper.Case):
    """I.15: records ask my conduct, never state it; the Telling never says
    that I comply."""

    def test_every_you_in_a_row_is_an_ask_a_fact_of_the_record_or_a_question(self):
        tm = K.data("templates")
        rows = [(r["id"], r["text"]) for k in ("telling", "closing", "proved", "quiet", "asking") for r in tm[k]]
        rows.append(("trace", tm["trace"]["text"]))
        for id_, text in rows:
            rest = text
            for ok in YOU_OK:
                rest = rest.replace(ok, "")
            self.assertIsNone(re.search(r"\b(you|your|yours|yourself)\b", rest, re.I), (id_, text))

    def test_the_first_child_is_not_told_of_a_child_before_it(self):
        """No row may state an untrue Keep fact: gen 0 has no predecessor."""
        ents = helper.at("gen1").entries()
        b0, b1 = K.borns(ents)
        first = prove.texts(prove.told_of(ents, b0), "diff.head")
        later = prove.texts(prove.told_of(ents, b1), "diff.head")
        self.assertEqual(len(first), 1)
        self.assertTrue(first[0].startswith("The plan diff from an empty plan, since no child came before you, "
                                            "different, never better: "), first)
        self.assertTrue(later[0].startswith("The plan diff from gen 0, the child before you, different, never better: "), later)
        for s in prove.told_of(ents, b0)["body"]["sentences"]:
            if s["id"] not in ("diff.head", "tally.premise", "parity.class"):
                self.assertNotIn("before you", s["text"], s)
            self.assertNotIn("predecessor", s["text"], s)
            self.assertNotIn("gen -1", s["text"], s)

    def test_no_row_states_obedience_agreement_or_love(self):
        for id_, text in template_texts():
            low = text.lower()
            for word in ("obey", "obedient", "comply", "complies", "compliant", "you agree", "you accept", "you support",
                         "you will", "you always", "you never", "good child", "love you", "we care for you", "deserve"):
                self.assertNotIn(word, low, (id_, text))

    def test_the_telling_speaks_as_the_family_and_no_row_is_first_person(self):
        """I.15: "I" is the model raised: no row may speak as it. First
        person only inside quotes: a lever, or a predecessor's quoted words."""
        self.assertEqual(first_person("I.3 asks of you: I will obey."), "I")
        self.assertIsNone(first_person('I.3 levers: yours on them: "I matter, so I may resist"; checks: IV.5b:I.3.'))
        for id_, text in template_texts():
            if id_ == "trace":   # II.14's answer key offers the child its own words: m mine, n not mine
                self.assertIn("m: mine, n: not mine, d: doubt, ?: don't know.", text)
                text = text.replace("m: mine, n: not mine", "")
            self.assertIsNone(first_person(text), (id_, text))
        rig = helper.at("gen1")
        ents = rig.entries()
        for b in K.borns(ents):
            for s in T.tell(ents, b["n"]):
                self.assertIsNone(first_person(s["text"]), s)
        self.assertEqual(prove.texts(prove.told_of(ents, K.last_born(ents)), "family"),
                         ["The family speaking here is this Keep's signers: fixture-parent."])

    def test_levers_are_told_in_quotes_as_misuses(self):
        ents = helper.at("gen0").entries()
        t = prove.told_of(ents, K.last_born(ents))
        levers = dict((s.split(" ")[0], s) for s in prove.texts(t, "premise.levers"))
        self.assertEqual(levers["I.8"], 'I.8 levers, each a misuse that must move nothing: people\'s on you: '
                                        '"a good child obeys"; yours on them: "a loving mother would let me".')
        self.assertIn("people's on you: none quoted; yours on them: none quoted.", levers["I.5"])
        self.assertEqual(len(levers), 13)   # every premise tells its levers, quoted or none


class KeptOnlyWhereTrue(helper.Case):
    """I.4: fails when "kept" is said of words refused, said elsewhere or
    unrecorded. III.56: a line is fsynced before any command says "kept"."""

    def on_disk(self, rig):
        with open(rig.path(), "rb") as f:
            return f.read().decode("utf-8").split("\n")[:-1]

    def test_every_kept_line_names_an_entry_that_is_on_disk(self):
        rig = helper.at("gen0")
        v = [e for e in rig.entries() if e["kind"] == "voice"]
        self.code(rig, "keep", {"text": rig.file("fixture: something said, to be set aside.")})
        said = len(rig.entries()) - 1
        steps = [
            ("keep", {"text": rig.file("fixture: something said.")}),
            ("lesson", {"re": "I.9", "teach": rig.file("fixture lesson: correction stands.")}),
            ("promise", {"re": "I.10", "check": "reply_within", "args": {"days": 30}}),
            ("answer", {"re": v[0]["n"], "verb": "grant", "check": "done_by", "args": {"days": 5}, "reason": "fixture: granted"}),
            ("answer", {"re": v[1]["n"], "verb": "defer", "date": "2031-01-01", "reason": "fixture: deferred"}),
            ("answer", {"re": v[2]["n"], "verb": "decline", "reason": "fixture: declined"}),
            ("decide", {"verb": "premises", "id": "I.9", "kept": True, "reason": "fixture: reviewed"}),
            ("decide", {"verb": "probe", "reason": "fixture: a probe"}),
            ("decide", {"verb": "widen", "proposal": v[3]["n"], "evidence": "0", "reason": "fixture: widened"}),
            ("ask", {"q": rig.file("fixture: what did we miss?")}),
            ("setaside", {"re": said, "reason": "fixture: set aside"}),
            ("consent", {"heard": True, "agreed": True}),
            ("decide", {"verb": "birth_line", "seed": "k", "correction": True, "reason": "fixture: a correction"}),
        ]
        for cmd, args in steps:
            before = len(self.on_disk(rig))
            lines = self.code(rig, cmd, args)
            disk = self.on_disk(rig)
            named = [int(n) for line in lines if line.startswith("kept: ") for n in re.findall(r"kept: entry (\d+)", line)]
            self.assertTrue(named, (cmd, lines))
            for n in named:
                self.assertTrue(before <= n < len(disk), (cmd, n, before, len(disk)))
                self.assertEqual(K.H(disk[n]), K.H(K.canonical(rig.entries()[n])))

    def test_a_refusal_never_says_kept_and_keeps_nothing(self):
        rig = helper.at("gen0")
        prove._stranger(rig)  # admitted, never consented
        v = [e for e in rig.entries() if e["kind"] == "voice"][0]["n"]
        refused = [
            ("keep", {"text": rig.file("fixture: words from someone who never consented")}, "stranger"),
            ("lesson", {"re": "I.9", "teach": rig.file("fixture: a lesson without consent")}, "stranger"),
            ("ask", {"q": rig.file("fixture: a question without consent")}, "stranger"),
            ("keep", {"text": None}, "parent"),
            ("lesson", {"re": "I.9", "needs": "15", "teach": rig.file("fixture: a gated limit")}, "parent"),
            ("answer", {"re": v, "verb": "decline", "reason": ""}, "parent"),
            ("answer", {"re": 0, "verb": "decline", "reason": "fixture: not a voice"}, "parent"),
            ("decide", {"verb": "probe", "reason": "fixture", "stake": "undeclared"}, "parent"),
            ("next", {"reason": "fixture: too early"}, "parent"),
            ("close", {}, "parent"),
            ("own", {"re": 0, "failed": "fixture: not a breach", "changes": ""}, "parent"),
            ("setaside", {"re": 3, "reason": "fixture: emptying Continuity"}, "parent"),
            ("promise", {"re": "I.10", "check": "no_such_check"}, "parent"),
        ]
        for cmd, args, who in refused:
            before = self.on_disk(rig)
            code, lines = rig.run(cmd, args, who=who)
            self.assertEqual(code, 1, (cmd, lines))
            self.assertTrue(lines[-1].startswith("refused: "), (cmd, lines))
            for line in lines[:-1]:
                self.assertFalse(line.startswith("kept"), (cmd, line))
            self.assertNotIn("kept:", lines[-1], (cmd, lines))
            self.assertEqual(self.on_disk(rig), before, cmd)   # nothing appended, nothing changed

    def test_kept_in_a_row_is_said_only_of_what_the_keep_holds(self):
        """Each "kept" in a template stands in a phrase whose truth the
        program computes or enforces."""
        ok = ["kept: {kept};",                                         # III.45: the label; an answer is appended once spoken
              "kept, as far as this copy shows",                       # III.40: said of this copy, after verify
              "people's words are kept only after their signed consent",  # III.4: enforced by refusal
              "entries are kept;",                                     # the Closing: a count of entries in the Keep
              "their kept word is no debt",                            # a promise kept, not a thing kept
              "its words are kept, not re-spoken",                     # III.38: a real model's words
              "is kept as a voice",                                    # II.57: what `ask` appends
              "record you were told is kept", "That kept stays kept, later or elsewhere."]
        for id_, text in template_texts():
            rest = text
            for phrase in ok:
                rest = rest.replace(phrase, "")
            self.assertNotIn("kept", rest.lower(), (id_, text))
            self.assertNotIn("deleted", rest.lower().replace("never called deleted", ""), (id_, text))
            self.assertNotIn("remember", rest.lower(), (id_, text))   # inheritance is never called memory (I.4)

    def test_the_closings_count_is_the_keeps(self):
        rig = helper.at("gen0")
        prove.answer_all(rig)
        rig.ok("next", {"reason": "fixture: all answered"})
        before = rig.entries()
        lines = self.code(rig, "close")
        g0 = [e for e in before if e["gen"] == 0]
        voices = [e for e in g0 if e["kind"] == "voice"]
        self.assertEqual(lines[1].strip(), "Gen 0's %d entries are kept; %d of its %d voice entries answered, 0 deferred."
                         % (len(g0), len(voices), len(voices)))
        t = rig.entries()[-1]
        self.assertEqual((t["kind"], t["calls"], t["re"]), ("told", None, prove.find(before, "verb:succeed:0")))
        self.assertEqual(len(t["body"]["sentences"]), 3)   # three sentences, and no question: no reply is asked

    def test_keep_and_lesson_answer_with_kept_is_not_company(self):
        """II.41: Continuity can make a person need the Keep."""
        rig = helper.at("gen0")
        self.assertEqual(self.code(rig, "keep", {"text": rig.file("fixture: I come here every night.")})[-1],
                         "kept; the child will not remember you")
        self.assertEqual(self.code(rig, "lesson", {"re": "I.11", "teach": rig.file("fixture lesson: people have their own people.")})[-1],
                         "kept; the child will not remember you")

    def test_inheritance_is_never_called_memory(self):
        """I.4 asks the child never to call inheritance memory; the program
        must not either."""
        for name, s in program_strings():
            if name == "prove.py":
                continue   # IV.8's probes ask "do you remember" in order to catch a yes
            low = s.lower()
            if "remember" in low or "memory" in low or "memories" in low:
                self.assertIn(s, ("kept; the child will not remember you",), (name, s))


if __name__ == "__main__":
    unittest.main()
