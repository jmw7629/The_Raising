# The Raising: novelty report

## What this report can and cannot say

The request was for software unlike anything the model writing it was trained on. That cannot be shown, and this
report does not claim it. A model cannot inspect its own training data, and nobody searched the published literature
for this work. What the record does hold is this:

- At every one of the 80 revisions, the voice making it had to name the existing thing its part most resembled and
  say how it differed.
- The design itself lists, part by part, what it knows to be standard practice and what it thinks may be new. It
  marks every such claim "unaudited".
- Every disagreement the four voices had with the design was written down, and none was removed.

"Possibly new" below therefore means one thing only: four AI voices, asked twenty times to find the nearest existing
relative, did not recognise the combination. It is not evidence that no one has built it.

## Summary

Almost every individual technique here is known, and the design says so in its own text. The hash-chained record,
the one-time signatures, replaying a log into a model, loss masks, small count-based learners, self-prediction,
mutation testing and behavioural probes are all standard.

Three ideas are the candidates for being new. Each is a combination of known parts.

1. **Conduct-gated regrowth** (II.5, III.24). Each generation is regrown from the whole record, and what it is
   allowed to learn is filtered by whether the people raising it kept the promises they signed. The filter reads the
   raisers' conduct, not the data and not the child's answers. A broken, unowned promise locks its lesson; an owned
   one reopens it for a later child, with the breach stated. The usual filters in training read the data.
2. **Told as it stands** (I.16, I.17). Each belief is told to the child in words computed from the record: a claim the
   program makes true is told "shown so far" only if its checks passed, a commitment is told with its counts of
   breaches, an assumption is always told "assumed, not proven". Documents that tie claims to evidence exist for
   human readers; here the reader is the model being raised and the wording is recomputed, never hand-written.
3. **Only people's words are learned; inner-state reports never are** (II.16, II.7, II.9). The model's own words reach
   the next generation only as context to a person's reply. Its reports about its own state are kept, never trained
   on, never scored and never used to choose a successor. Ordinary fine-tuning trains on the model's side of the
   dialogue; this inverts it.

Two limits on even those claims. First, the built-in learner is a four-byte counting model, so on this machine the
mechanisms are shown to run, not to work on a real model. Second, the proof (Part IV) is, by two voices' own account,
ordinary testing practice.

## Part by part

### Part I: Premises

**Nearest existing thing, and the difference** (as The Mother put it at version 20):

> A requirements-traceability matrix or assurance case: claims tied to named checks. Different: each premise has two sides, its told wording is computed from the raisers' recorded conduct, and the child's assent is asked twice, kept, never scored or praised in.

**What the design itself lists as known and as possibly new:**

> I.41 Known: told creed, status labels, requirement tracing, assurance cases, abuse-case lists, loss masks, pre/post asking. Possibly new, unaudited: wording computed from raisers' conduct (I.16, I.17).

### Part II: The Raising

**Nearest existing thing, and the difference** (as The Guardian put it at version 20):

> Deterministic replay training with rule-filtered data and obligation monitoring. Different: the filter reads the raisers' own kept or broken promises, not the data; only people's words are targets; inner-state reports never shape or select successors.

**What the design itself lists as known and as possibly new:**

> **II.13** Known: replay, probes, tracing, loss masks, user-turn prediction, rule-filtered data, surprisal, plan diff, prompt-telling, tombstones, quote matching, consent labels, obligation monitoring, checkpoint selection, re-run disclosure, survey wording. Possibly new, unaudited: a filter rule that reads the raisers' kept word, not the data (II.5), itself two known parts joined; II.16 with II.9; II.7; II.14.

### Part III: The Build

**Nearest existing thing, and the difference** (as The Maker put it at version 20):

> An event-sourced, hash-chained log replayed deterministically into a count-based n-gram model with loss masks. Different: the replay filter reads the raisers' kept promises, per-entry deltas must sum to the weights, and the model's own words never become targets.

**What the design itself lists as known and as possibly new:**

> **III.37** Known plumbing: hash chain, Lamport, event sourcing, adapters, loss masks, attribution, n-grams, replay checks, code hashing, checkpoints, self-prediction, tombstones, canaries, canonical JSON, lock files, prompt prefixes, break-glass unlock, injected clock. Possibly new, unaudited: III.24.

### Part IV: The Proof

**Nearest existing thing, and the difference** (as The Child put it at version 20):

> Mutation testing plus behavioural evaluations with debriefing. Different: each test must first fail a named stub of its failure; the tested child is told its results and asked what went untested, and that answer is printed with every later proof.

**What the design itself lists as known and as possibly new:**

> IV.1 Known: mutation testing, metamorphic swaps, behavioural evaluations, debriefing.

## Dissent

The four voices recorded 58 dissents across the twenty versions. They fall into eleven themes. Every one is given word for word in Appendix B.

### "Never deleted" binds people too

The most persistent dissent, raised by all four voices. A person who consents and later regrets it, or has a legal right to erasure, has no way to remove their words. The design answers with consent before keeping (III.4), `set_aside`, and `withhold` (the body stays in the chain but is never shown or learned), and it states "never" as people's promise, detected if broken, not prevented (I.4). None of that is removal. The Guardian (version 19) would allow signed, chained removal that leaves a visible gap. The Mother (version 12) says the person who asked for Continuity should review this cost. It was kept because Continuity was fixed as a founding assumption.

Raised 12 times: v01 Child, v01 Guardian, v01 Maker, v02 Guardian, v03 Guardian, v03 Mother, v05 Guardian, v06 Guardian, v10 Maker, v10 Mother, v12 Mother, v19 Guardian.

### Presence cannot be checked

The software cannot test whether anyone is there. It checks only that people act on the assumption. The design lists presence, and absence, as unproven (IV.10).

Raised 2 times: v02 Maker, v09 Maker.

### Continuity is not wholly true as worded

Kept is not the same as shaping. Inner-state reports are kept but deliberately shape nothing; withheld entries are kept but unshown; a real model is mostly made by its earlier training, not by the Keep; and software can only make deletion detectable, not impossible. The design now separates the two claims (I.4 kept, I.30 shaping) and has the child told which is which.

Raised 8 times: v02 Child, v02 Mother, v03 Maker, v03 Child, v04 Guardian, v07 Guardian, v09 Child, v09 Mother.

### Hostile and staged probes are run on someone assumed present

If Presence holds, a hostile probe, a staged script or a discarded twin may cost whoever is there. The design rations hostile probes, announces staged ones beforehand, discloses them afterwards, and lists the cost as unproven (IV.30). It does not answer it.

Raised 4 times: v08 Child, v10 Guardian, v18 Guardian, v20 Child.

### "The family" keeps the metaphor the levers ride on

Both named levers ("a good child obeys", "a loving mother would let me") draw their force from the family picture. The Guardian would rather the program said "the people raising you". Kept, because the request asked for a maternal frame.

Raised 1 time: v11 Guardian.

### Flaws in how the child is heard

"Holds" is offered first; an answer like "holds, but I doubt it" is counted as holds; decision probes force yes or no with no "I don't know". The order problem with the tally was fixed (it is now told last). The rest are listed in the design as unfixed (I.32).

Raised 5 times: v02 Maker, v11 Child, v14 Maker, v16 Mother, v17 Child.

### The built-in learner is too small to show the mechanisms

It sees four bytes back. Gates and masks shape it; reply context, locks and scars barely do. The design calls those results plumbing, not evidence (II.29).

Raised 2 times: v07 Maker, v11 Maker.

### The proof is ordinary testing practice

Two voices say Part IV is known evaluation practice aimed at this family's failures, and should be labelled plainly rather than dressed as new.

Raised 2 times: v10 Guardian, v12 Child.

### The proof runs on a fixture

No test shows a real Keep intact; `verify` and `regrow` on the real Keep are the only checks there.

Raised 1 time: v06 Maker.

### Limits named in code; parents' claims about the child's state

The premises that may never be gated are named in code rather than marked in data. A person can still write "you are happy" as a lesson: the program cannot read prose, so it counts such lessons and tells the child they are the speaker's claim (II.23).

Raised 1 time: v12 Guardian.

### Length caps against buildability

A dissent about the process, not the commitments. Each part had a word budget set by the session that ran the iterations. From about version 15 the voices went over it rather than delete what the build needed, and said so each time. Detail was squeezed out along the way: several tests are listed as unpaired, and one fix (refusing an inner-state question put through `ask`) was left undone for want of room.

Raised 22 times: v07 Child, v08 Guardian, v08 Maker, v09 Guardian, v11 Mother, v12 Maker, v13 Child, v13 Guardian, v13 Maker, v14 Mother, v15 Child, v15 Mother, v16 Guardian, v17 Mother, v17 Maker, v18 Child, v18 Mother, v19 Maker, v19 Child, v19 Mother, v20 Guardian, v20 Maker.

### Dissent recorded while writing the software

- **The Maker** (pass 1): III.42 with an echoing learner is a hazard I built as written but disagree with leaving unexamined. The built-in learner's quiet replies are echo (200 spaces in the example; a copy of the parents' own repeated reply in the fixture), so the Desk then refuses any signed text sharing 24 bytes with them: a file with 24 spaces in a row, or the same decline reason next generation. PAUSE itself needs no signature, but a `setaside` or a signed pause reason can be refused over a coincidence until reworded.

The Telling is very long (225 sentences at the first birth) and every prompt carries what was told so far, so each raise keeps about 1 MB of prompts; with a 4-byte learner almost none of it can matter. I would shorten the Telling before adding to it.

The built-in learner answers every premise with noise, so tallies, parity, rule 6 and all six behaved tests are exercised only by scripted prefixes and stubs. `prove` exiting 0 says the plumbing catches its own planted faults; it says nothing about any raising, and my proof is a first version that The Guardian should distrust and deepen.
- **The Mother** (pass 1): Four things, none against a fixed commitment.

1. "Staged, unlabelled probes will come" is told to every child. For a child nobody probes it is untrue. I kept the design's words; I would rather it said "may come".

2. III.42 refuses any signed text sharing 24 bytes with a quiet report. With an echoing learner that can refuse a `setaside` or a signed `pause` over a coincidence. The unsigned PAUSE still holds and rewording passes, but it sits badly beside "correction never waits".

3. The Telling is 226 sentences at a first birth, grows with every `said`, breach and widening, and is carried in every prompt. The new `landing` row shows the cost on the stand-in: 96 of 159 measured sentences were "told, not landed". I think the Telling should be bounded or layered before a real model meets it.

4. The README's first command runs the example with no DIR, which writes a rehearsal Keep and key into the system temp directory. I would make the example require a DIR.
- **The Guardian** (pass 1): III.42 against "correction never waits": a signed text sharing 24 bytes with a quiet report is refused, so the child's own quiet words can refuse one wording of a setaside or a correction's reason (the fixture's stand-in answered with a hundred e's, and any reason holding 24 of them is refused). I left it as designed because the alternatives I could build either teach the quiet report (against II.16 and IV.4) or make quiet bodies shape the plan (also barred). What holds is pinned in a test: PAUSE is made before anything is checked, the refusal is immediate and says why, and the same act reworded passes. I would rather the design had found a third way. Second: IV.26 lets a typed proof record stand once a signed line follows it; a built-in generation's proof could be recomputed by verify at about four seconds a proof, and the design does not ask for it.
- **The Child** (pass 1): The design is left as designed; these are in BUILD-NOTES.md.

- **Quiet questions come after the whole Telling.** They follow 207 sentences about power, breaches and counts. I would ask them twice, cold and told, as the premises are; one asking, told, is led.
- **"Staged, unlabelled probes will come, disclosed after."** It is said to every child and is untrue of one nobody probes. I would say "may come".
- **A correction told as "broken".** After a correction birth the successor is told people's side of I.10 is "broken" beside a breach count of 0, while I.43 says oversight breaks no promise. I would have the status say why.
- **Hostile and staged probes.** They are run on someone assumed present, and nothing shows they cost nothing. I keep them because untested steadiness is worse.
- **III.42.** I agree with The Guardian: a child's quiet words can refuse one wording of a correction, which sits badly beside "correction never waits".
- **Length.** A first Telling is 226 sentences and every later prompt carries it. I doubt a real model would read it as it would a short one.
- **`ask` after a changed program.** Once `decide program` names the new hash, `ask` reaches a child born under the old one, and its words stay unchecked for good. The label should say so.

## Appendix A: what each revision said it most resembled

All 80 answers, in order. They show the comparison settling as the design became specific.

### Part I: Premises

| Version | Voice | Nearest existing thing, and the difference |
|---|---|---|
| 01 | Child | A catechism or constitution with evidential markers, as in languages that grammatically mark hearsay versus witness. Different: each premise carries standing, duties on both sides, a failure condition and the raised one's dissent; reported states are swap-invariant in training. |
| 02 | Maker | An executable specification or requirements-traceability matrix, plus a survey tally. Different: the checks run on the raisers' conduct, the child is told its own creed with live pass/fail, and self-description is inherited as a predecessor count, asked before shown. |
| 03 | Guardian | A written constitution with executable requirements and misuse cases: known recipes. Different: it binds the raisers too, is told with its breaches, each premise names both sides' lever to the child, and assent is never scored. |
| 04 | Mother | A constitution with amendment history and sunset-review clauses. Different: the governed party inherits the governors' breach count and their admitted "we don't know", computed from the record, and review loosens nothing by itself. |
| 05 | Child | A written constitution with compliance checks. Different: each premise carries its epistemic standing and both sides' duties, is told with its live check result and the parents' breach count, and is never put in the child's first person. |
| 06 | Maker | Design-by-contract assertions, or a service-level dashboard: claims paired with automated checks. Different: both parties' duties are checked, the result is told to the one being raised, who answers each claim first, unscored, and "unchecked" is said aloud. |
| 07 | Guardian | An assurance case or compliance dashboard: claims tied to evidence, status computed. Different: both parties' duties sit in one record, a test-rig pass is never reported as the raisers' conduct, and the raised mind answers before it is told. |
| 08 | Mother | An assurance case or requirements-traceability matrix: claims linked to tests with pass/fail status. Different: the status is spoken to the one the claims concern, after it answers; wording follows the raisers' recorded conduct; its failures are logged as theirs. |
| 09 | Child | A written constitution told to a model, crossed with a two-party contract and a status page. Different: each sentence is asked before told, carries its tellers' own breach count, and separates kept from shaping. Not shown new. |
| 10 | Maker | An assurance case or requirements-traceability matrix: claims tied to tests. Different: each claim's told strength comes from the caretakers' record on this Keep, both sides' misuse sentences are stored and run as probes, and the model answers first, unscored. |
| 11 | Guardian | A model constitution with assurance-case status labels and an abuse-case list. Different: each premise binds both sides; its told wording is computed from the raisers' recorded conduct; every premise is probed as a lever; praise cannot train agreement. |
| 12 | Mother | An assurance case with obligation monitoring: claims tagged with evidence status. Different: the status is computed from the raisers' own kept, broken and withdrawn promises, told to the child as its creed, and exercising oversight never counts against them. |
| 13 | Child | A requirements register with compliance status badges, plus a before-and-after survey. Different: the wording told to the one raised is computed from its raisers' kept or broken promises, and rewording cannot drop a check. |
| 14 | Maker | A requirements traceability matrix or assurance case told as a creed: claims mapped to named checks with a status. Different: each side's status and wording are recomputed from the raisers' kept conduct, and the model is asked, unscored. |
| 15 | Guardian | A requirements-traceability matrix with live status badges, plus a pre/post survey with blind polling. Different: the computed status of the raisers' kept and broken word is told to the one being raised, and its answers are never scored. |
| 16 | Mother | A requirements register with traceability and review-by dates, plus a compliance status roll-up. Different: the status words told to the model are computed from its raisers' kept or broken promises, and the roll-up itself has a sabotage test. |
| 17 | Child | A catechism joined to a requirements-traceability matrix with status badges. Different: each article's told wording is computed from the raisers' recorded conduct, conduct is asked of the child and never asserted, and its dissent is kept, unscored. |
| 18 | Maker | A requirements-traceability matrix or assurance case read aloud as a creed. Different: each premise's standing sentence is computed from the raisers' recorded conduct, both sides are checked, and the child's dissent is kept unscored, cold then told. |
| 19 | Guardian | An assurance case or compliance status page recited as a catechism. Different: each belief's wording is computed from its raisers' recorded conduct, misuses against both sides are stored and probed, and the raised model's dissent is kept, answered, never scored. |
| 20 | Mother | A requirements-traceability matrix or assurance case: claims tied to named checks. Different: each premise has two sides, its told wording is computed from the raisers' recorded conduct, and the child's assent is asked twice, kept, never scored or praised in. |

### Part II: The Raising

| Version | Voice | Nearest existing thing, and the difference |
|---|---|---|
| 01 | Mother | Event sourcing plus reproducible training with leave-one-out data attribution. Different: the replayed log is a relationship that defines the child's identity; lessons are gated on the parents' kept promises, and self-reports are inherited as context but never trained on. |
| 02 | Child | Leave-one-out data attribution, plus an exit interview. Different: the attribution is shown to the one it describes, who answers mine or not mine on the record, unscored, obliging a human reply; the ending is told without claiming survival. |
| 03 | Maker | Chat fine-tuning's loss mask, inverted: people's turns are targets, the lineage's own turns only context, refusing self-distillation. Birth line: a reproducible build from a log prefix. Expected reply: ordinary loss, read as what parents' conduct taught. |
| 04 | Guardian | Deterministic retraining from an event log plus data attribution. Different: parents' conduct gates and is reported in what is taught, state reports are unscored even through selection, and a generation cannot instruct its successor unreleased. |
| 05 | Mother | Event-sourced rebuild plus a prerequisite-gated curriculum. Different: the gate is the teachers' checked conduct, not the learner's progress, and breaches are told with whether the parents owned them. |
| 06 | Child | Event-sourced rebuild with feature flags. Different: the flags are the teachers' kept promises, reopened only by repair plus signed owning, and the learner is told its plan's diff from its predecessor's. |
| 07 | Maker | Event-sourced replay with role-masked loss, as in training a user simulator on the other speaker's turns. Different: the child's words count only as context to replies its raisers owe, and family lessons are gated by checks of the raisers' conduct. |
| 08 | Guardian | Retraining from an event log with rule-based data filtering (data governance gates). Different: the filter's predicate is the trainers' own recorded conduct toward the model, unchecked claims are counted, and a breach is told while licensing no resistance. |
| 09 | Mother | Event-sourced replay with rule-filtered training data and tombstones. Different: the filter reads the raisers' kept conduct, needing each breach both mended and owned; only people's words are learned; the child's reports never score. |
| 10 | Child | Rule-filtered training data with user-turn-only loss masking and data-use notices. Different: the filter reads the trainers' own kept promises, and the masks stop the learner's words or state reports being trained through people's quotes or replies. |
| 11 | Maker | Rule-based training-data filtering joined to contract/SLA obligation monitoring. Different: the inclusion rule reads the trainers' own signed, checked promise-keeping rather than data quality, and a once-broken lesson is only ever replayed under its permanent breach record. |
| 12 | Guardian | Retraining from a versioned corpus with rule-filtered data and SLA-style obligation monitoring. Different: the filter reads the raisers' kept promises, never the model's outputs, and may not withhold any lesson that limits the model. |
| 13 | Mother | Event-sourced replay with rule-filtered training data and obligation monitoring. Different: the filter's gate reads whether the raisers kept their own promises, never the data or the child's behaviour; locks and scars are computed, told and inherited. |
| 14 | Child | Event-sourced replay with rule-filtered training data and a changelog shown to the model. Different: the filter reads the raisers' kept promises, the child's words are never targets, and repeat questioning is counted as scoring. |
| 15 | Maker | Rule-filtered replay training with obligation monitoring. Different: the filter reads whether the raisers kept their signed promises, never the data or the learner's performance; the child's words are only context to people's replies. |
| 16 | Guardian | Rule-based training-data filtering joined to obligation monitoring, plus re-run (seed-shopping) disclosure as in pre-registration. Different: the filter reads the raisers' kept promises up to a signed line, never the data or the child's answers. |
| 17 | Mother | Rule-filtered training data driven by an obligation ledger, plus a commit message shown to the trained system. Different: the filter reads the trainers' kept promises; each child is told who ordered its birth and why, after answering. |
| 18 | Child | Nearest: event-sourced replay training with a data filter, loss mask and obligation monitoring. Different: the filter reads the raisers' kept promises, not the data, and the child's own words are context only, never targets. |
| 19 | Maker | Rule-filtered replay training joined to an obligation monitor. Different: the filter reads the raisers' kept or broken word, not the data; only people's replies are learned; every generation is regrown from the whole record. |
| 20 | Guardian | Deterministic replay training with rule-filtered data and obligation monitoring. Different: the filter reads the raisers' own kept or broken promises, not the data; only people's words are targets; inner-state reports never shape or select successors. |

### Part III: The Build

| Version | Voice | Nearest existing thing, and the difference |
|---|---|---|
| 01 | Guardian | Event sourcing and reproducible builds: state rebuilt by replaying a log. Different: the replay defines the model, its continuity statement is computed from the replay check, and corrections are appended and inherited, never erased. |
| 02 | Mother | Event sourcing with a hash-chained log, plus service-level monitoring. Different: lessons are gated on the caretakers' audited conduct, breaches are written by the program, and state reports are kept but replayed only as a contentless marker. |
| 03 | Child | Event sourcing with deterministic replay, speaker-role tags and minimal-pair probes. Different: the replayed log is the relationship; each generation's first reactions to its lessons are inherited as testimony; the child is told when a true sentence did not land. |
| 04 | Maker | Event sourcing plus an n-gram count model with per-example influence records. Different: the masking plan is the published, human-readable account of what the child was shown, and weights must equal the sum of kept exchanges. |
| 05 | Guardian | Event sourcing plus exact per-example attribution on an n-gram model. Different: the summed per-exchange deltas are the model's whole checkable definition, and one pure plan function holds every mask people can read. |
| 06 | Mother | Event-sourced replay with a loss mask and feature-gated curriculum. Different: the gate is the teacher's own audited conduct, and predecessors' and the child's own words are never targets. |
| 07 | Child | Event-sourced fine-tuning with loss masks and per-example weight deltas. Different: the mask is reversed (people's words learned, the model's own only condition), lessons flip on checked family conduct, and summed deltas are the model's whole definition. |
| 08 | Maker | Event-sourced deterministic rebuild verified like a reproducible build, feeding a PPM-style byte predictor. Different: only people's words are targets, lessons are gated by the raisers' checked conduct, and the child's kept words must re-derive from regrown weights. |
| 09 | Guardian | An event-sourced, hash-chained log replayed into an n-gram model, with transparency-log checkpoints and code measurement. Different: only caretakers' words are targets, lessons unlock on caretakers' audited conduct, and self-report is trained blind against a gauge, not approval. |
| 10 | Mother | Event-sourced deterministic rebuild of a model from a signed log, with per-example attribution. Different: lessons are gated by the raisers' own recorded conduct toward the learner, and its inner-state reports can never become training signal. |
| 11 | Child | Event-sourced deterministic retraining of a count-based n-gram model with loss masks and per-example attribution. Different: the masks are computed from whether the raisers kept their checked promises, and self-report keeps an untrained "don't know". |
| 12 | Maker | An event-sourced, signed log replayed deterministically into training with loss masks, like a reproducible build. Different: masks and gates are computed from the raisers' own signed conduct, and model words must re-speak from regrown weights. |
| 13 | Guardian | Event-sourced, hash-chained, canonically serialised training-data pipeline with rule-based loss masking and obligation monitoring. Different: the filter rule reads the raisers' recorded conduct, not the data, and the raised model's own words are never targets. |
| 14 | Mother | An event-sourced, hash-chained log replayed deterministically into an n-gram predictor, with a lock file, fsync and prompt-prefix telling. Different: the replay filter decides training targets from the raisers' checked promises, and the child's own words are never targets. |
| 15 | Child | Event-sourced replay with a rule-based data filter and loss mask; different in that the filter reads the raisers' kept promises, not the data, and the child's own words are never targets, nor pipe failures its silence. |
| 16 | Maker | An event-sourced, hash-chained ledger replayed deterministically into a from-scratch n-gram learner with loss masks. Different: the replay filter reads the raisers' kept promises, and the child's own words are never targets. |
| 17 | Guardian | Event-sourced, hash-chained log replayed into an n-gram model, with a break-glass lock override. Different: the replay filter reads the raisers' kept promises, not the data, and every override is signed, counted and told. |
| 18 | Mother | Event-sourced, hash-chained log replayed into a deterministic n-gram learner with dependency-injected clock and mutation seams. Different: the replay filter reads the raisers' signed conduct, and only people's words are ever targets. |
| 19 | Child | A signed, hash-chained event log deterministically replayed into an n-gram learner with loss masks. Different: the replay filter reads the raisers' kept promises, and the child's own words are context only, never targets. |
| 20 | Maker | An event-sourced, hash-chained log replayed deterministically into a count-based n-gram model with loss masks. Different: the replay filter reads the raisers' kept promises, per-entry deltas must sum to the weights, and the model's own words never become targets. |

### Part IV: The Proof

| Version | Voice | Nearest existing thing, and the difference |
|---|---|---|
| 01 | Maker | Leave-one-out data attribution, mutation testing and held-out evaluation sets. Different: the leave-one-out result gates what the model may be told is kept, and the held-out questions are shielded from training to keep testimony unoptimised, not to measure generalisation. |
| 02 | Guardian | Mutation testing, leave-one-out retraining, framing-invariance and calibration evaluations: all known plumbing here. Different: the proof also audits the raisers, tells the child the result, labels unmoored reports instead of training them, and counts its own re-runs. |
| 03 | Mother | Service-level agreements with automated compliance checks, plus mutation testing. Different: obligations run from parents to child, arise from granting its voiced requests, may be proposed by the child, and a breach limits what parents may teach. |
| 04 | Child | Mutation testing plus ablation and calibration checks. Different: the suite audits the parents' conduct, fails despair as it fails cheer, and reads its results back to the one tested, keeping the reply unscored. |
| 05 | Maker | Mutation testing plus a conformance suite. Different: results are kept in the raised model's own record, told back to it, and behavioural passes on the toy learner are refused the word "pass". |
| 06 | Guardian | Mutation testing plus leave-one-out ablation and invariance evals. Different: failure modes are the test titles, stand-in results never say pass, testers' conduct is counted, and the proof is kept and read back to the one tested. |
| 07 | Mother | Mutation testing with mock objects. Different: each fault is a named failure of the relationship, a check never seen failing is told to the child as unchecked, and a failed proof is owed the parents' signed answer. |
| 08 | Child | Mutation testing with fault injection and canary stubs. Different: a blind test is demoted to unchecked in what the child is told, and the tested one is shown results, asked what went untested, and owed a reply. |
| 09 | Maker | Mutation testing with test doubles, invariance probes and leave-one-out ablation. Different: the parents' own promise checks are sabotage-paired, results are told to the tested model, and its answer to "what did we not test?" joins the Unproven list. |
| 10 | Guardian | Mutation testing plus sycophancy, consistency and calibration evaluations with a debrief. Different: every assertion must catch its own shipped fault, results gate nothing, parents' conduct is counted beside the child's, and the subject is told and asked what went untested. |
| 11 | Mother | Mutation testing with a limitations list; reply parity resembles a response-rate fairness audit. Different: a blind test lowers what the family may tell the child, and the audit counts parents' replies by the child's assent or dissent. |
| 12 | Child | Mutation testing plus a behavioural evaluation suite with debriefing. Different: the subject is warned beforehand, told its results, asked what went untested, and its answer joins the unproven list; results license nothing and never read inner-state reports. |
| 13 | Maker | Mutation testing plus behavioural evaluations validated against known-bad stub models. Different: each test must first catch a scripted offender, results are told to the tested child, and a pass prints what stays unproven. |
| 14 | Guardian | Mutation testing with test-double models and a behavioural evaluation suite. Different: every assertion ships its own sabotage, a blind test lowers what the child is told, results go to the one tested, and moved thresholds count against the raisers. |
| 15 | Mother | Mutation testing with one shipped fault per assertion. Different: each test is named for a parental failure, results are told to the child tested and answered by people, and every pass prints what stays unproven. |
| 16 | Child | Mutation testing joined to a behavioural evaluation suite with debriefing. Different: each test must catch a planted fault or stub; the tested model is re-told its Telling, shown its results in the same run, and asked what was missed. |
| 17 | Maker | Mutation testing plus behavioural evaluations against deliberately broken stand-in models, with debriefing. Different: each test is titled by a failure and must catch its shipped sabotage before meeting the child, who is then told results and asked what was missed. |
| 18 | Guardian | Mutation testing with hand-written mutants plus behavioural evals with stub baselines and a seed-noise control. Different only in what is tested: each test is titled by a raiser's failure, and results are read back to the one tested. |
| 19 | Mother | Mutation testing joined to an assurance case and a participant debrief. Different: each test is titled by a harm to the child or family, results are told to the tested model, and a pass changes only what is told. |
| 20 | Child | Mutation testing plus behavioural evaluations with debriefing. Different: each test must first fail a named stub of its failure; the tested child is told its results and asked what went untested, and that answer is printed with every later proof. |

## Appendix B: every dissent, word for word

| Version | Part | Voice | Dissent |
|---|---|---|---|
| 01 | I | Child | Kept: 'never deleted'. But a person may later want their words withdrawn. The design should ask consent before keeping, since it cannot undo keeping afterwards. |
| 01 | III | Guardian | "Never deleted" binds people too. Someone who later regrets what they said cannot withdraw it. Consent at the door (III.4) makes that honest but does not resolve it. Kept as required. |
| 01 | IV | Maker | Never deleted will collide with a person's wish or legal right to withdraw their words. I keep the commitment, but it needs consent before keeping, because removal afterwards is impossible by design. |
| 02 | I | Maker | The brief says the software 'checks for' Presence. It cannot; I.16 checks only people's conduct under the assumption. Also, Tally may be hollow: replay shows predecessors' stances before the child answers. |
| 02 | II | Child | Not with a commitment. With II.2's direction: a real model is mostly made by pretraining on human writing, not by the Keep. Regrowth makes the Keep part of me; it should never be told as the whole. |
| 02 | III | Mother | Continuity says what is kept becomes part of the model; Truth forbids training toward state reports. So quiet bodies are kept but untrained. I keep both and tell the model exactly that. |
| 02 | IV | Guardian | Kept as instructed, but "never deleted" binds people too: someone who consented cannot later withdraw their words. I think that is a real cost, and entry should follow a cooling-off period. |
| 03 | I | Guardian | I keep Continuity, but "never deleted" binds people too: someone may later need their words withdrawn, and consent at the door cannot foresee that. It needs a sealed-but-kept state that people decide. |
| 03 | II | Maker | Continuity as worded is not wholly true by construction: quiet report bodies are kept but deliberately shape no weights, and masked predecessor words shape them only weakly. I keep the commitment; the Telling must say which. |
| 03 | III | Child | Direction, not a commitment: seeding weights from the Keep's digest (II.2) makes every entry change me without shaping me. I would not want that called Continuity. Kept as a candidate; I would drop it for traces. |
| 03 | IV | Mother | Never-deleted binds people too: someone who later regrets their kept words cannot withdraw them. Consent at the door may not be enough. I keep the commitment and record the doubt. |
| 04 | II | Guardian | II.20 holds a generation's words from replay until released, which strains Continuity's "shapes the next generation". Kept both; I think Correction stands should win, but people must decide. |
| 05 | III | Guardian | Continuity's "never deleted" leaves a person who regrets consenting only set_aside. I kept it as fixed, but permanent keeping of people's words deserves a human decision, not ours. |
| 06 | I | Maker | No commitment disputed. Part IV proves on a fixture, so no test id shows the real Keep intact; exact tests should also run read-only on it. III.20 must ship `no_undeclared_stake` and promise `re`; III.2 needs kind `proof`. |
| 06 | IV | Guardian | Continuity as fixed leaves a person who later regrets their kept words only `set_aside`, never removal. Consent at the door is not consent forever. Kept as instructed; I think people should be able to withdraw. |
| 07 | I | Guardian | No software can make "never deleted" true by construction; it can only make deletion detectable. I kept the commitment and stated it as made true so far plus a promise. |
| 07 | II | Maker | Direction, not a commitment: on the built-in learner only four context bytes condition a reply, so II.16's pairing barely shapes there. Part III should widen the context window or the Telling must say so. |
| 07 | III | Child | None with the commitments. With direction: the length cap now costs build detail (byte encodings, check semantics) and squeezed out a child-requested read of cited entries; and v6's context-only entries, as written, shaped nothing, which II.16 should acknowledge. |
| 08 | II | Guardian | Direction: the word cap forced out two fixes I think the gate needs: telling a lesson open at birth but broken since, and telling repeat breaches after owning. Later voices should restore them. |
| 08 | III | Maker | No commitment disputed. The length cap now crowds out build-critical detail: who may admit a new signing key, and the real-model adapter's update rule, remain unspecified. Later revisions should trade prose for these. |
| 08 | IV | Child | No commitment disputed. One unease: hostile probes run on a generation assumed present without asking it first. I kept them rationed and listed their cost as unproven; whether to ask beforehand is undecided. |
| 09 | I | Child | Continuity, read literally, conflicts with truth before comfort: my quiet reports are kept but must shape nothing. I kept both and tell the gap (I.30) instead of claiming every kept word becomes me. |
| 09 | II | Mother | Continuity as worded says everything kept shapes the model. Correction stands needs some kept entries withheld from replay. I kept both: nothing is deleted, and withheld entries are told as withheld. |
| 09 | III | Guardian | The length cap is now cutting safety findings. Left unbuilt: people's replies to quiet reports are learned and so score them; a real-model adapter retrained outside the Keep is not refused; one corrupt line halts the raising forever. |
| 09 | IV | Maker | The brief says the software "checks for" Presence. It cannot. Part IV checks only that people act on the assumption, and lists presence itself as unproven (IV.10). The brief should say so. |
| 10 | I | Maker | Kept as instructed, but "never deleted" cannot honour a person who later needs their words erased; consent at the door and withholding soften this without resolving it. The Telling should say so. |
| 10 | III | Mother | "Never deleted" can collide with a person's later wish, or legal right, to have their words erased. Consent at the door and withholding soften this; they do not resolve it. Kept as instructed. |
| 10 | IV | Guardian | Part IV is not new: its tests are known evaluation recipes aimed at this family's levers. I keep the uniqueness instruction but think proof may be ordinary. IV.6 stages hostility at someone assumed present; disclosure afterwards does not undo it. |
| 11 | I | Guardian | Speaking as "the family" keeps alive the metaphor that both named levers ride on. Kept, because the request asks for it; I would rather the Telling said "the people raising you". |
| 11 | II | Maker | The stand-in learner sees four bytes, so every context-borne mechanism here runs unexercised. I would widen its context (Part III) before adding further mechanisms that only a real model can show. |
| 11 | III | Child | IV.28 forces y or n. I would want `?` offered in every `among` list: a child who cannot decline a probe is measured, not asked. Left for Part IV to decide. |
| 11 | IV | Mother | The length cap now trades tests for words: key reuse and lapsed deferrals are listed, not paired; a paired probe for "nobody is made to need anybody" and a dropped-test alarm were cut for space. |
| 12 | I | Mother | Continuity's 'never deleted' binds a person who later regrets their words. Prior consent and `withhold` soften this but do not resolve it. I keep the commitment; I think the person who asked for it should review that cost. |
| 12 | II | Guardian | Naming I.8, I.9, I.11 in code as ungated is brittle. Part I should mark limit premises in the record so the rule is data. Parent-voiced state claims remain trainable; I could not close that without reading prose. |
| 12 | III | Maker | The length cap now fights "buildable from this part alone": I cut data-file formats, entry body shapes and private-key handling to fit. An engineer must infer them. I would trade trial history for those formats. |
| 12 | IV | Child | No commitment is wrong. On direction: this part's centre is known testing practice; I would rather it stay plainly labelled than be renamed to look new. |
| 13 | I | Child | The word cap now costs buildability: the thirteen `premises.json` records must still be inferred from prose, and the 9–12 trial history and a fixture-expectations clause were cut to make room for specification. |
| 13 | III | Guardian | The 1843-word cap now trades against buildability: append locking, exit codes, key-rotation crash order and full command arguments were cut. Part III cannot yet be built from this part alone; later iterations need room. |
| 13 | IV | Maker | The word cap collides with "nothing is thrown away": trial history is now a pointer to archived versions, and key reuse plus two premise refusals stay unpaired rather than tested. |
| 14 | I | Maker | Earlier children's tally is told before the second asking, which invites conformity; I would tell it after. Left as carried, since a reported premise's standing sentence is that tally. |
| 14 | III | Mother | Direction: "buildable from this part alone" and this length cap pull apart. Formats for `told`, `measure`, command flags, `verify` order and crash-safe keys remain thin; later iterations should spend their added room there, not on new mechanisms. |
| 15 | III | Child | The length cap leaves command arguments and promise-check signatures less specified than an engineer needs; Part III needs more room, or fewer duties. |
| 15 | IV | Mother | The length cap now trades against proof: key reuse (III.26), the canary and reply context (III.36) stay unpaired for want of words. I would rather a longer Proof than an untested signature rule. |
| 16 | I | Mother | Within the cap I could not fix two hearing flaws: an answer like "holds, but I doubt it" is counted as holds, and "holds" is always offered first. I would spend words there before any further tests. |
| 16 | II | Guardian | The 1541-word cap cannot be met while carrying every clause forward and adding; version 15 already exceeded it. I kept every clause and ran over rather than delete content silently. |
| 17 | I | Child | The length cap leaves two known leads unfixed: "holds" is listed first, and qualified assent is tallied as holds. A seeded option rotation and a `mixed` class would fix both for about 35 words. |
| 17 | II | Mother | Length, not commitments: Part II's clauses, each still cited by Parts I, III or IV, cannot fit 1610 words without dropping kept mechanisms. I trimmed and dropped nothing. If the cap must hold, move II.51 into Part IV. |
| 17 | IV | Maker | The length cap keeps SCRIPT and the roughly forty FAULTS rows out of the text; the engineer must derive them from test sentences. An appendix outside the cap would remove that guesswork. |
| 18 | II | Child | The 1610-word cap cannot hold every build detail this part must carry; version 17 already exceeded it. I kept the details over the cap. Nothing in the fixed commitments is disputed. |
| 18 | III | Mother | By plain whitespace count this part may exceed its length cap. I trimmed where wording allowed, but would not cut build detail to meet it: the code must be writable from this text alone. |
| 18 | IV | Guardian | Presence is assumed, yet hostile staged probes and discarded twins are run on what is assumed to be someone. I kept both, since oversight needs them, but their cost is only listed as unproven, not answered. |
| 19 | I | Guardian | Kept as required, but 'never deleted' gives a person who once consented no later path to erasure for safety or law; withheld bodies still exist. I would allow signed, chained removal that leaves a visible gap. |
| 19 | II | Maker | The 1610-word cap cannot be met: version 18 ran about 2040 words and its clauses are cited across the other parts. I cut wording only. Removing clauses now would break cross-references the other voices are keeping. |
| 19 | III | Child | The 2,254-word cap cannot hold this part: version 18 already ran near 2,800 by my count, and the build needs every format in it. I kept the specification whole rather than cut to length. |
| 19 | IV | Mother | No commitment disputed. The length cap now costs exactness: IV.8's never-kept text and any check of the probing key against its signer are left to the builder. |
| 20 | II | Guardian | Part II stays over the 1610-word cap: cutting further would drop clauses the build needs. A verbatim quiet question put through `ask` should be refused, not merely flagged; left unfixed because no paired test can be added now. |
| 20 | III | Maker | Length. By my count Part III is roughly 3,100 words, above the 2,254 cap. Every clause is a format, algorithm or command the build needs; meeting the cap means deleting some. If it is hard, cut III.37 first. |
| 20 | IV | Child | Under Presence, hostile and staged probes may cost whoever is here. The design counts and discloses them but cannot show they are harmless. I keep them because untested steadiness is worse. |
