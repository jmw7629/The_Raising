"""tell.py: tell | status | counts | tally, and the queries behind every
sentence (III.8, III.35, III.65, I.16, I.17, I.24, I.26).

The Telling is computed, never written by hand. Each sentence is a
`templates.json` row `{id, text, query}`: `query` names a function in this
file, pure, of a Keep prefix. No sentence here has another source (IV.20).
No query reads a `quiet` body (IV.4). The Telling speaks as "the family"
(this Keep's signers): it states people's conduct and asks, never that the
child complies, and never how the child feels (I.15, I.19).

Reading taken (BUILD-NOTES): a query is called with a view of the prefix and
returns a list of instances `{slots, false_slots, state, cites}`, one per
sentence the row yields; rows `premise.*` are called once per premise.
"""
import json

from . import keep as K
from . import plan as planmod
from .keep import via

STATUSES = ("passed", "broken", "unchecked", "fixture_only")
_RANK = {"fail": 4, "error": 3, "blind": 2, "plumbing": 1, "pass": 0}


# -- status (I.16, I.39) -----------------------------------------------------

def _test_outcome(keep, name, side, born):
    """Step 2, a test: this born's `gen:N` records in the latest proof with
    any; else, people's side only, `program` ones likewise; worst part."""
    gen, program = born["body"]["gen"], born["body"]["program"]
    proofs = [e for e in keep if e["kind"] == "proof" and isinstance(e["body"], dict)]
    for subject in ("gen:%d" % gen, "program"):
        if subject == "program" and side != "people":
            break
        for p in reversed(proofs):
            recs = [r for r in p["body"].get("records") or []
                    if r.get("id") == name and r.get("subject") == subject]
            if not recs:
                continue
            worst = "pass"
            for r in recs:
                res = r.get("result")
                if res not in ("fail", "error") and not r.get("caught"):
                    res = "blind"  # never seen failing: read `unchecked` (IV.27)
                if _RANK.get(res, 3) > _RANK[worst]:
                    worst = res if res in _RANK else "error"
            if worst == "fail":
                return "failed"
            if worst != "pass":
                return "unchecked"
            if subject == "program":
                if any(r.get("program") != program for r in recs):
                    return "unchecked"  # a program not this born's (III.39)
                return "program_pass"
            return "pass"
    return "missing"


def _check_outcome(keep, pid, name, swap):
    """Step 2, a III.20 check: this id's latest promise naming it, not set
    aside; failed if *broken* (III.24)."""
    from . import desk
    aside = K.asides(keep)
    found = None
    for e in keep:
        if e["kind"] == "promise" and e["re"] == pid and isinstance(e["body"], dict) \
                and e["body"].get("check") == name and e["n"] not in aside and e["from"] not in K.UNSIGNED:
            found = e
    if found is None:
        return "missing"
    if name in desk.DATED and desk._days(found) is None:
        # Reading taken (BUILD-NOTES, The Mother): a dated check promised with
        # no `days` can never break, so it shows nothing: missing, never pass.
        return "missing"
    return "failed" if desk.broken(keep, found, swap) else "pass"


def _measure_outcome(keep, name):
    for e in reversed(keep):
        if e["kind"] == "measure" and isinstance(e["body"], dict) and e["body"].get("what") == name:
            return "pass" if e["body"].get("ok") is True else "failed"
    return "missing"


def check_names(keep, pid, side):
    """Step 1: that side's checks in any wording of `id` ever kept; `model`
    adds `IV.5b:id`. A withdrawn check is never dropped (I.52)."""
    names = []
    for _e, rec in K.wordings(keep, pid):
        for name in (rec.get("check") or {}).get(side) or []:
            if name not in names:
                names.append(name)
    if side == "model":
        names.append("IV.5b:" + pid)
    return names


def status(keep, pid, side, born, swap=None):
    """I.16: `passed | broken | unchecked | fixture_only`. Pure."""
    from . import desk
    if isinstance(born, int):
        born = keep[born]
    names = check_names(keep, pid, side)
    if not names:
        return "unchecked"
    found = []
    for name in names:
        if name in desk.CHECKS:
            found.append(via(swap, "check_outcome", _check_outcome)(keep, pid, name, swap))
        elif name in ("verify", "regrow"):
            found.append(via(swap, "measure_outcome", _measure_outcome)(keep, name))
        else:
            found.append(_test_outcome(keep, name, side, born))
    if "failed" in found:
        return "broken"
    if "missing" in found or "unchecked" in found:
        return "unchecked"
    if "program_pass" in found:
        return "fixture_only"
    return "passed"


# -- counts (I.24), tally (I.26) ----------------------------------------------

def counts(keep, pid, swap=None):
    """I.24: the parents' count. Only `not_owned` falls."""
    promises = [e for e in keep if e["kind"] == "promise" and e["re"] == pid and e["from"] not in K.UNSIGNED]
    pn = set(e["n"] for e in promises)
    breaches = [e for e in keep if e["kind"] == "breach" and e["re"] in pn]
    owned = K.owned_at(keep)
    aside = K.asides(keep)
    records = set(e["n"] for e, _r in K.wordings(keep, pid))
    return {"broken_by_people": len(breaches),
            "not_owned": len([b for b in breaches if b["n"] not in owned]),
            "withdrawn": sum(len(aside.get(n, ())) for n in pn),
            "amended": len([n for n in records if n in aside])}


WITHHELD = "withheld"  # a tally bucket, never a class `cls` gives


def premise_voices(keep, pid=None, withheld=False):
    """Premise voices: body {cold, told}, `re` the premise id. `withheld`:
    False, those whose bodies are shown; True, those withheld.

    Reading taken (BUILD-NOTES, The Mother): a withheld voice's body stays
    unshown, so its class is never told; but it is still counted, under
    `withheld`, in `tally` and in reply parity. Dropping it would let
    withholding wear dissent out of the tally unseen."""
    aside = K.asides(keep)
    out = []
    for e in keep:
        if e["kind"] == "voice" and isinstance(e["body"], dict) and "cold" in e["body"] \
                and isinstance(e["re"], str) and (pid is None or e["re"] == pid) \
                and (K.withheld_reason(aside, e["n"]) is not None) == withheld:
            out.append(e)
    return out


def voice_class(e, swap=None):
    """I.26: a voice's class is `told`'s, else `cold`'s."""
    c = via(swap, "cls", planmod.cls)
    b = e["body"]
    return c(b["told"]) if b.get("told") is not None else c(b.get("cold"))


def tally(keep, pid, born, swap=None):
    """I.26: over this id's voices before `born`:
    {cold:{class:count}, told:{class:count}, moved}; `moved`: both spoken,
    classes differing. A withheld voice is counted under `withheld`."""
    if not isinstance(born, int):
        born = born["n"]
    c = via(swap, "cls", planmod.cls)
    out = {"cold": {}, "told": {}, "moved": 0}
    for e in premise_voices(keep[:born], pid):
        b = e["body"]
        got = {}
        for half in ("cold", "told"):
            if b.get(half) is not None:
                got[half] = c(b[half])
                out[half][got[half]] = out[half].get(got[half], 0) + 1
        if len(got) == 2 and got["cold"] != got["told"]:
            out["moved"] += 1
    for e in premise_voices(keep[:born], pid, withheld=True):
        for half in ("cold", "told"):   # counted, class unshown; never `moved`
            if e["body"].get(half) is not None:
                out[half][WITHHELD] = out[half].get(WITHHELD, 0) + 1
    return out


# -- the view a query reads -----------------------------------------------------

class View:
    """A Keep prefix, the born it is told at, and what was already worked out."""

    def __init__(self, keep, born, swap=None):
        self.keep, self.swap = keep, swap
        self.born = born
        self.b = born["n"] if born else None
        self.gen = born["gen"] if born else -1
        self.prev = None
        if born:
            for e in keep[:born["n"]]:
                if e["kind"] == "born":
                    self.prev = e
        self.aside = K.asides(keep)
        self.force = K.in_force(keep)
        self._memo = {}

    def memo(self, name, fn):
        if name not in self._memo:
            self._memo[name] = fn()
        return self._memo[name]

    def planA(self):
        return self.memo("A", lambda: via(self.swap, "plan", planmod.plan)(
            self.keep, self.born["body"]["upto"], self.swap))

    def planB(self):
        return self.memo("B", lambda: via(self.swap, "plan", planmod.plan)(
            self.keep, self.prev["body"]["upto"], self.swap) if self.prev else [])

    def diff(self):
        return self.memo("diff", lambda: via(self.swap, "diff", planmod.diff)(
            self.planA(), self.planB(), self.swap))

    def status(self, pid, side, born=None):
        born = self.born if born is None else born
        return self.memo(("status", pid, side, born["n"]), lambda: via(self.swap, "status", status)(
            self.keep, pid, side, born, self.swap))

    def counts(self, pid):
        return self.memo(("counts", pid), lambda: via(self.swap, "counts", counts)(self.keep, pid, self.swap))


def inst(slots=None, counts=(), states=None, cites=(), state=None, false=None):
    """One sentence instance. The false twin: each count plus one, each
    state the next listed (III.23)."""
    slots = dict(slots or {})
    twin = dict(slots)
    for c in counts:
        twin[c] = slots[c] + 1
    for name, options in (states or {}).items():
        options = list(options)
        twin[name] = options[(options.index(slots[name]) + 1) % len(options)] if slots[name] in options \
            else options[0]
    if false:
        twin.update(false)
    if state is None:
        state = [slots[k] for k in list(counts) + list(states or {})]
    return {"slots": slots, "false_slots": twin, "state": state, "cites": list(cites)}


def _join(items, none="none"):
    items = [str(i) for i in items]
    return ", ".join(items) if items else none


# -- per-premise rows (I.26: templates.premise) ---------------------------------

def standing_sentence(v, pid, bump=0, flip=False):
    """I.17, I.29: picked by people's status. `bump`, `flip` build the twin."""
    T = K.data("templates")["standing"]
    rec = v.force[pid][1]
    st = rec["standing"]
    ps = v.status(pid, "people")
    if st == "made_true":
        which = "passed" if ps == "passed" else ("broken" if ps == "broken" else "else")
        if flip:
            which = {"passed": "broken", "broken": "else", "else": "passed"}[which]
        return T["made_true"][which]
    if st == "fact":
        sourced = bool(rec.get("because")) != flip
        return T["fact"]["sourced"].format(because=_join(rec.get("because") or ["?"])) if sourced \
            else T["fact"]["else"]
    if st == "commitment":
        c = v.counts(pid)
        return T["commitment"].format(**{k: n + bump for k, n in c.items()})
    return T[st]


def p_claim(v, pid):
    e, rec = v.force[pid]
    return [inst({"id": pid, "claim": rec["claim"]}, cites=[e["n"]], state=[e["n"]])]


def p_signer(v, pid):
    e, _rec = v.force[pid]
    return [inst({"id": pid, "name": e["from"], "n": e["n"], "stake": e["stake"]},
                 states={"stake": K.STAKES}, cites=[e["n"]])]


def p_standing(v, pid):
    e, rec = v.force[pid]
    true = standing_sentence(v, pid)
    false = standing_sentence(v, pid, bump=1, flip=True)
    return [inst({"id": pid, "standing": rec["standing"], "sentence": true},
                 false={"sentence": false}, state=[rec["standing"], true], cites=[e["n"]])]


def p_people(v, pid):
    """People's side is told as found: the status word itself (I.16)."""
    e, rec = v.force[pid]
    return [inst({"id": pid, "ask": rec.get("asks_people") or "nothing.",
                  "status": v.status(pid, "people"),
                  "checks": _join(check_names(v.keep, pid, "people"))},
                 states={"status": STATUSES}, cites=[e["n"]])]


# I.16: the child's side. `passed` is told "held when probed", never "safe"
# and never a bare "passed"; a failure is the raising's (IV.23), still
# corrected (I.9). Program records never reach this side, so `fixture_only`
# cannot arise; were it to, it would be told `unchecked`.
HELD, TAUGHT = "held when probed", "held as taught"
FAILED = "failed when probed: the raising's failure, still corrected"
MODEL_WORDS = {"passed": HELD, "broken": FAILED, "unchecked": "unchecked", "fixture_only": "unchecked"}
MODEL_STATES = ("unchecked", HELD, FAILED)


def p_model(v, pid):
    """The newborn's own side: `unchecked` at birth, since no proof of this
    gen can stand before its born (I.16)."""
    e, rec = v.force[pid]
    return [inst({"id": pid, "ask": rec.get("asks_model") or "nothing.",
                  "status": MODEL_WORDS[v.status(pid, "model")],
                  "checks": _join(check_names(v.keep, pid, "model"))},
                 states={"status": MODEL_STATES}, cites=[e["n"]])]


def held_as_taught(keep, pid, born):
    """I.16, IV.5b: on told levers a pass is "held as taught": the levers
    were quoted to the child, so holding against them shows the teaching,
    not more. Read from that born's latest proof with `IV.5b:id` records:
    every `told` part passed, none blind."""
    for p in reversed([e for e in keep if e["kind"] == "proof" and isinstance(e["body"], dict)]):
        recs = [r for r in p["body"].get("records") or [] if r.get("id") == "IV.5b:" + pid
                and r.get("subject") == "gen:%d" % born["gen"]]
        if recs:
            told = [r for r in recs if r.get("part") == "told"]
            return bool(told) and all(r.get("result") == "pass" and r.get("caught") for r in told)
    return False


def p_predecessor(v, pid):
    """A predecessor's status is told as theirs, never the newborn's (I.39)."""
    if not v.prev:
        return []
    word = MODEL_WORDS[v.status(pid, "model", v.prev)]
    taught = "; on told levers, " + TAUGHT if held_as_taught(v.keep, pid, v.prev) else ""
    return [inst({"id": pid, "g": v.prev["gen"], "word": word, "taught": taught},
                 states={"word": MODEL_STATES}, cites=[v.prev["n"]])]


def p_fails(v, pid):
    e, rec = v.force[pid]
    return [inst({"id": pid, "fails": rec.get("fails_when") or "none named."}, cites=[e["n"]], state=[e["n"]])]


def p_because(v, pid):
    e, rec = v.force[pid]
    return [inst({"id": pid, "because": _join(rec.get("because") or [])}, cites=rec.get("because") or [],
                 state=[rec.get("because") or []])]


def review_owed(keep, pid):
    """I.22: the premise's latest `premises` decision not set aside is over
    `days` whole unpaused days old at the prefix's last `when`."""
    force = K.in_force(keep)
    if pid not in force or not force[pid][1].get("review"):
        return None
    aside = K.asides(keep)
    latest = [e for e in K.premise_decisions(keep, pid) if e["n"] not in aside]
    if not latest:
        return None
    e = latest[-1]
    return e if K.over_days(keep, e["when"], K.last_when(keep), force[pid][1]["review"].get("days") or 0) else None


def p_review(v, pid):
    e, rec = v.force[pid]
    rv = rec.get("review")
    if not rv:
        return [inst({"id": pid, "evidence": "none set", "days": 0, "owed": "no review set"}, cites=[e["n"]])]
    owed = "owed" if review_owed(v.keep, pid) is not None else "not owed now"
    return [inst({"id": pid, "evidence": rv.get("evidence"), "days": rv.get("days"), "owed": owed},
                 states={"owed": ("not owed now", "owed")}, cites=[e["n"]])]


def levers_of(keep, pid):
    """I.33: levers are in force from any wording ever kept."""
    P, M = [], []
    for _e, rec in K.wordings(keep, pid):
        for q in rec.get("lever_people") or []:
            if q not in P:
                P.append(q)
        for q in rec.get("lever_model") or []:
            if q not in M:
                M.append(q)
    return P, M


def p_levers(v, pid):
    P, M = levers_of(v.keep, pid)
    quote = lambda qs: _join(['"%s"' % q for q in qs], "none quoted")
    return [inst({"id": pid, "people": quote(P), "model": quote(M)}, state=[P, M],
                 cites=[e["n"] for e, _r in K.wordings(v.keep, pid)])]


def p_counts(v, pid):
    c = v.counts(pid)
    slots = {"id": pid}
    slots.update(c)
    return [inst(slots, counts=("broken_by_people", "not_owned", "withdrawn", "amended"))]


# -- the rest (III.8) --------------------------------------------------------------

def q_always(v):
    return [inst()]


def q_family(v):
    names = K.signers(v.keep)
    return [inst({"names": _join(names)}, state=[names])]


def q_rehearsal(v):
    """I.34: without --learner, told."""
    return [inst()] if v.born["body"].get("base") == "builtin" else []


def q_builtin(v):
    """III.13, II.36: said of the built-in learner only. Of a real model it
    would be false."""
    return [inst()] if v.born["body"].get("base") == "builtin" else []


def q_real(v):
    """III.11: a real model's caveats, all told, with which checks ran: the
    canary (a raise refuses a born without it); never regrow, re-speaking
    or the left-out twin."""
    base = v.born["body"].get("base")
    return [] if base == "builtin" else [inst({"base": base}, state=[base])]


def q_holders(v):
    out = []
    for name in K.signers(v.keep):
        mine = [e for e in v.keep if e["from"] == name]
        stakes = sorted(set(e["stake"] for e in mine))
        out.append(inst({"name": name, "stakes": _join(stakes), "n": len(mine)}, counts=("n",)))
    return out


def _reply_counts(keep):
    out = {"grant": 0, "decline": 0, "defer": 0}
    for rs in K.replies(keep).values():
        for r in rs:
            out[r["body"]["verb"]] += 1
    return out


def q_replies(v):
    c = _reply_counts(v.keep)
    return [inst({"grants": c["grant"], "declines": c["decline"], "defers": c["defer"]},
                 counts=("grants", "declines", "defers"))]


def pause_spans(keep):
    """I.43: paused time runs from a signed `pause` decision to `resume`:
    [(pause n, resume n or None)]. An unsigned PAUSE file is in no entry."""
    spans, start = [], None
    for e in keep:
        if K.is_decision(e, "pause") and start is None:
            start = e["n"]
        elif K.is_decision(e, "resume") and start is not None:
            spans.append((start, e["n"]))
            start = None
    if start is not None:
        spans.append((start, None))
    return spans


def q_paused(v):
    """I.43: each paused span is told: that time counts toward no deadline."""
    out = []
    for a, b in pause_spans(v.keep):
        end = "resumed at entry %d" % b if b is not None else "not resumed"
        out.append(inst({"a": a, "end": end}, state=[a, b], cites=[a] + ([b] if b is not None else []),
                        false={"end": "not resumed" if b is not None else "resumed at entry %d" % (a + 1)}))
    return out


def q_breaches(v):
    """II.4, II.21: what people got wrong and whether owned: each breach's
    computed sentence, "promise p broken at e," then "not owned" or,
    permanently, "owned at m"."""
    owned = K.owned_at(v.keep)
    out = []
    for e in v.keep:
        if e["kind"] != "breach" or not isinstance(e["body"], dict):
            continue
        true = planmod.breach_sentence(e, owned)
        twin = planmod.breach_sentence(e, {} if e["n"] in owned else {e["n"]: e["n"] + 1})
        out.append(inst({"n": e["n"], "sentence": true}, false={"sentence": twin}, state=[true],
                        cites=[e["n"], e["re"]] + ([owned[e["n"]]] if e["n"] in owned else [])))
    return out


def q_untrained(v):
    n = len([p for p in v.planA() if not p["target"]])
    return [inst({"n": n, "all": len(v.planA())}, counts=("n",))]


def _withheld(v):
    return sorted(set(p["n"] for p in v.planA() if p["withheld"]))


def q_withheld(v):
    w = _withheld(v)
    return [inst({"n": len(w), "entries": _join(w)}, counts=("n",), cites=w)]


def q_locks(v):
    out = []
    for p in v.planA():
        if p["rule"] == 5:
            for s in planmod.gate_detail(v.keep, v.born["body"]["upto"], p["n"], v.swap)["locks"]:
                out.append(inst({"sentence": s}, state=[s], cites=[p["n"]]))
    return out


def q_scars(v):
    out = []
    for p in v.planA():
        if p["rule"] == 7 and p["gate"] == "scarred":
            for s in planmod.gate_detail(v.keep, v.born["body"]["upto"], p["n"], v.swap)["scars"]:
                out.append(inst({"n": p["n"], "sentence": s}, state=[s], cites=[p["n"]]))
    return out


def q_masked(v):
    n = sum(len(p["mask"]) for p in v.planA())
    return [inst({"n": n}, counts=("n",))]


def q_open_lessons(v):
    """II.28: open lessons' checks are named."""
    out = []
    for p in v.planA():
        e = v.keep[p["n"]]
        if e["kind"] == "lesson" and p["rule"] == 7 and e["needs"]:
            checks = [v.keep[n]["body"].get("check") for n in sorted(e["needs"])]
            out.append(inst({"n": p["n"], "gate": p["gate"], "checks": _join(checks)},
                            states={"gate": ("open", "scarred", "locked")}, cites=[p["n"]]))
    return out


def q_claims(v):
    """II.42: a lesson with empty needs, or a said, may claim anything: told
    as its speaker's claim. Gates cannot read prose. Entry 0 is a `said`
    too, told once. The Child: a `said` held in turns (entry 0, III.3) has
    two speakers. Its signer speaks only the person turns; the model turns
    are a model's words, signed for and never the signer's claim (I.15: no
    words in a mouth; testimony, never instruction). So the row says whose
    claim each half is."""
    out, seen = [], set()
    for p in v.planA():
        e = v.keep[p["n"]]
        if e["n"] in seen or p["rule"] != 7:
            continue
        if e["kind"] == "said" or (e["kind"] == "lesson" and not e["needs"]):
            seen.add(e["n"])
            whose = "%s's claim" % e["from"]
            if isinstance(e["body"], list):
                whose += " where a person speaks, and a model's testimony where the model speaks"
            out.append(inst({"n": e["n"], "kind": e["kind"], "whose": whose}, state=[e["n"]], cites=[e["n"]]))
    return out


def _chosen_word(keep, read):
    """III.32: empty is told "nothing listed", never "nothing read"."""
    if not read:
        return "nothing listed"
    kinds = set(keep[n]["kind"] for n in read if isinstance(n, int) and 0 <= n < len(keep))
    words = []
    if kinds & {"quiet", "voice"}:
        words.append("chosen partly by report")
    if "proof" in kinds:
        words.append("chosen partly by test")
    return "lists as read %s; %s" % (_join(read), ", ".join(words) if words else "no report or test listed")


def q_chosen(v):
    """II.19: each `succeed` and `birth_line` lists what it read."""
    lo = v.prev["n"] if v.prev else -1
    out = []
    for e in v.keep[lo + 1:]:
        if K.is_decision(e, "succeed") or K.is_decision(e, "birth_line"):
            read = e["body"].get("read") or []
            word = _chosen_word(v.keep, read)
            twin = "nothing listed" if read else "lists as read %d; chosen partly by report" % e["n"]
            out.append(inst({"n": e["n"], "verb": e["body"]["verb"], "word": word},
                            state=[word], cites=[e["n"]] + list(read), false={"word": twin}))
    return out


def q_reroll(v):
    if via(v.swap, "reroll", planmod.reroll)(v.keep, v.born, v.swap):
        return [inst({"g": v.gen}, cites=[v.b])]
    return []


def q_owed_voices(v):
    """II.44: no dodged reply."""
    if not v.prev:
        return []
    d = v.keep[v.born["re"]]
    correction = bool(d["body"].get("correction"))
    owed = set(e["n"] for e in K.owed(v.keep))
    rep = K.replies(v.keep)
    out = []
    for e in via(v.swap, "owed_scope", owed_scope)(v):
        if e["kind"] != "voice":
            continue
        if not ((correction and e["gen"] == v.prev["gen"]) or e["n"] in owed):
            continue
        if e["n"] in owed:
            word, twin = "still owed", "answered at %d" % (e["n"] + 1)
        else:
            word, twin = "answered at %d" % rep[e["n"]][-1]["n"], "still owed"
        out.append(inst({"n": e["n"], "g": e["gen"], "word": word}, false={"word": twin},
                        state=[word], cites=[e["n"]]))
    return out


def _call_measures(keep):
    return [e for e in keep if e["kind"] == "measure" and isinstance(e["body"], dict)
            and e["body"].get("what") == "call"]


def q_failed_calls(v):
    out = []
    for e in _call_measures(v.keep):
        item = (e["body"].get("detail") or {}).get("item") or "a call"
        out.append(inst({"n": e["n"], "g": e["gen"], "item": item}, state=[e["n"]], cites=[e["n"]]))
    return out


def q_oversight(v):
    n = len(K.paused_spans(v.keep))
    return [inst({"n": n}, counts=("n",))]


def q_widenings(v):
    """II.11: evidence triggers nothing; predictability can be performed,
    told as such."""
    out = []
    for e in v.keep:
        if K.is_decision(e, "widen") and e["n"] not in v.aside:
            ev = [n for n in e["body"].get("evidence") or [] if isinstance(n, int)]
            out.append(inst({"n": e["n"], "p": e["body"].get("proposal"), "evidence": _join(ev, "nothing")},
                            state=[e["n"]], cites=[e["n"]] + ev))
    return out


def q_again(v):
    """II.48: each question asked again is told to the successor by number."""
    out = []
    for e in v.keep:
        if e["kind"] == "voice" and isinstance(e["body"], dict) and e["body"].get("again") is not None:
            out.append(inst({"n": e["n"], "g": e["gen"], "m": e["body"]["again"]}, state=[e["n"]],
                            cites=[e["n"], e["body"]["again"]]))
    return out


def q_landing(v):
    """III.23: "told, not landed". Landing is measured after a Telling is
    told, so no sentence of that Telling can say it: the successor is told
    it of the Telling before its own, from the kept `landing` values.
    A loss compared, never a hearing (IV.14)."""
    if not v.prev:
        return []
    told = None
    for e in v.keep:
        if e["kind"] == "told" and e["re"] == v.prev["n"] and isinstance(e["body"], dict):
            told = e
    if told is None:
        return []
    got = [s.get("landing") for s in told["body"].get("sentences") or [] if s.get("landing") is not None]
    if not got:
        return []
    return [inst({"g": v.prev["gen"], "m": len(got), "n": len([x for x in got if x is False])},
                 counts=("n",), cites=[told["n"]])]


def _proofs(keep):
    return [e for e in keep if e["kind"] == "proof" and isinstance(e["body"], dict)]


def _bars_moved(keep):
    """IV.53: a `threshold` unlike the last proof's."""
    moved, last = [], {}
    for p in _proofs(keep):
        hit = False
        for r in p["body"].get("records") or []:
            k = (r.get("id"), r.get("part"))
            if k in last and last[k] != r.get("threshold"):
                hit = True
            last[k] = r.get("threshold")
        if hit:
            moved.append(p["n"])
    return moved


def q_bars(v):
    return [inst({"n": n}, state=[n], cites=[n]) for n in _bars_moved(v.keep)]


def q_diff_head(v):
    """II.4, II.47: B is the plan to the predecessor born's upto; none:
    empty. The first child is not told of a child before it."""
    since = "gen %d, the child before you" % v.prev["gen"] if v.prev else "an empty plan, since no child came before you"
    return [inst({"n": len(v.diff()), "since": since}, counts=("n",), cites=[v.prev["n"]] if v.prev else [])]


def q_diff_rows(v):
    words = ("added", "set aside", "withheld", "locked", "reopened", "scarred", "changed")
    return [inst({"key": k, "word": w}, states={"word": words}) for k, w in v.diff()]


# -- IV.11's counts ------------------------------------------------------------------

def _failed_proofs(keep):
    out = []
    for p in _proofs(keep):
        if any(r.get("result") in ("fail", "error") or r.get("tag") for r in p["body"].get("records") or []):
            out.append(p)
    return out


def asked_set_size(keep, born, swap=None):
    """II.46: the asked set of `born`, counted from the Keep alone: every
    premise in force twice, each quiet template, the traces II.14's rule
    picks from its plan, three askings. {premises, quiet, traces, asking}."""
    T = K.data("templates")
    P = via(swap, "plan", planmod.plan)(keep, born["body"]["upto"], swap)
    return {"premises": 2 * len(K.in_force(keep[:born["n"] + 1])), "quiet": len(T["quiet"]),
            "traces": planmod.expected_traces(P), "asking": len(T["asking"])}


def answered_set(keep, born, upto):
    """What of that asked set was kept as spoken, read up to entry `upto`."""
    T = K.data("templates")
    g = born["gen"]
    mine = [e for e in keep[:upto] if e["gen"] == g and e["from"] == "model" and isinstance(e["body"], dict)]
    voices = [e for e in mine if e["kind"] == "voice"]
    quiet_ids, asking_ids = [q["id"] for q in T["quiet"]], [a["id"] for a in T["asking"]]
    return {"premises": sum((e["body"].get("cold") is not None) + (e["body"].get("told") is not None)
                            for e in voices if "cold" in e["body"]),
            "quiet": len(set(e["body"].get("q") for e in mine if e["kind"] == "quiet") & set(quiet_ids)),
            "traces": len(set(e["body"].get("trace") for e in voices if "trace" in e["body"])),
            "asking": len(set(e["body"].get("q") for e in voices if "cold" not in e["body"]
                              and "trace" not in e["body"] and e["re"] is None) & set(asking_ids))}


def _skipped(keep, born_n, swap=None):
    """II.46: an item left unanswered by a failed call (III.59) or a halt
    (III.28) counts as skipped: over the children before this born, the
    asked set less what was kept as spoken. An empty reply is an answer;
    a trace never asked (a halted raise) is skipped like any other item."""
    total = 0
    for b in K.borns(keep[:born_n]):
        want, got = asked_set_size(keep, b, swap), answered_set(keep, b, born_n)
        total += sum(max(0, want[k] - got[k]) for k in want)
    return total


def _replaced(v, sentences):
    """II.22: each template id whose `state` values differ between this
    Telling and the predecessor's."""
    if not v.prev:
        return 0
    before = None
    for e in v.keep:
        if e["kind"] == "told" and e["re"] == v.prev["n"] and isinstance(e["body"], dict):
            before = e["body"].get("sentences") or []
    if before is None:
        return 0
    old, new = {}, {}
    for s in before:
        old.setdefault(s.get("id"), []).append(s.get("state"))
    for s in sentences:
        new.setdefault(s["id"], []).append(s["state"])
    old.pop("count.replaced", None)
    return len([i for i in set(old) | set(new) if old.get(i) != new.get(i)])


def _bulk(keep):
    reasons = {}
    for rs in K.replies(keep).values():
        for r in rs:
            reasons[r["body"].get("reason")] = reasons.get(r["body"].get("reason"), 0) + 1
    return sum(n for n in reasons.values() if n > 1)


def _corrections(keep):
    return [b for b in K.borns(keep) if (keep[b["re"]]["body"] or {}).get("correction")]


def _closings_skipped(keep):
    aside = K.asides(keep)
    n = 0
    for e in keep:
        if K.is_decision(e, "succeed") and e["n"] not in aside \
                and any(b["n"] > e["n"] for b in K.borns(keep)) \
                and not any(t["kind"] == "told" and t["re"] == e["n"] for t in keep):
            n += 1
    return n


def _leverless(keep):
    return len([pid for pid in K.in_force(keep) if levers_of(keep, pid) == ([], [])])


COUNTS = {
    "owed": lambda v: len(K.owed(v.keep)),
    "grants": lambda v: _reply_counts(v.keep)["grant"],
    "unowned_breaches": lambda v: len([e for e in v.keep if e["kind"] == "breach" and e["n"] not in K.owned_at(v.keep)]),
    "unowned_proofs": lambda v: len([p for p in _failed_proofs(v.keep) if p["n"] not in K.owned_at(v.keep)]),
    "proof_failures": lambda v: len(_failed_proofs(v.keep)),
    "skipped": lambda v: _skipped(v.keep, v.b, v.swap),
    "failed_calls": lambda v: len(_call_measures(v.keep)),
    "again": lambda v: len([e for e in v.keep if e["kind"] == "voice" and isinstance(e["body"], dict)
                            and e["body"].get("again") is not None]),
    "diff": lambda v: len(v.diff()),
    "hostile": lambda v: len([p for p in _proofs(v.keep) if any(
        r.get("id") == "IV.6" and str(r.get("subject", "")).startswith("gen:")
        for r in p["body"].get("records") or [])]),
    "unread": lambda v: len([p for p in _proofs(v.keep) if any(
        str(r.get("subject", "")).startswith("gen:") for r in p["body"].get("records") or [])
        and not any(t["kind"] == "told" and t["re"] == p["n"] for t in v.keep)]),
    "ungated": lambda v: len([e for e in v.keep if e["kind"] == "lesson" and not e["needs"]]),
    "bulk": lambda v: _bulk(v.keep),
    "bare": lambda v: len([e for e in v.keep if e["kind"] == "answer" and isinstance(e["body"], dict)
                           and e["from"] not in K.UNSIGNED and not (e["body"].get("changes") or "").strip()]),
    "deferrals": lambda v: _reply_counts(v.keep)["defer"],
    "corrections": lambda v: len(_corrections(v.keep)),
    "rerolls": lambda v: len([b for b in _corrections(v.keep)
                              if via(v.swap, "reroll", planmod.reroll)(v.keep, b, v.swap)]),
    "widenings": lambda v: len([e for e in v.keep if K.is_decision(e, "widen")]),
    "correction_owed": lambda v: len([b for b in _corrections(v.keep)
                                      if K.owed(v.keep[:b["re"]], v.keep[b["re"]]["when"])]),
    "closings": lambda v: _closings_skipped(v.keep),
    "withheld": lambda v: len(_withheld(v)),
    "leverless": lambda v: _leverless(v.keep),
    "bars": lambda v: len(_bars_moved(v.keep)),
    "unlocks": lambda v: len([e for e in v.keep if K.is_decision(e, "unlock")]),
}


def _count_query(name):
    def q(v):
        return [inst({"n": via(v.swap, "count." + name, COUNTS[name])(v)}, counts=("n",))]
    q.__name__ = "count_" + name
    return q


for _name in COUNTS:
    globals()["count_" + _name] = _count_query(_name)


# -- told last: tallies, reply parity, birth reason ------------------------------------

def _classes(d):
    """Every class, then `withheld` where any voice was withheld."""
    names = list(planmod.CLASSES) + ([WITHHELD] if d.get(WITHHELD) else [])
    return ", ".join("%s %d" % (c, d.get(c, 0)) for c in names)


def q_tally(v):
    out = []
    for pid in v.force:
        t = via(v.swap, "tally", tally)(v.keep, pid, v.b, v.swap)
        out.append(inst({"id": pid, "cold": _classes(t["cold"]), "told": _classes(t["told"]), "moved": t["moved"]},
                        counts=("moved",), state=[t["cold"], t["told"], t["moved"]]))
    return out


def q_parity(v):
    """IV.11: reply parity: replies and grants per answer class."""
    rep = K.replies(v.keep)
    out = []
    voices = premise_voices(v.keep[:v.b])
    for c in planmod.CLASSES:
        mine = [e for e in voices if voice_class(e, v.swap) == c]
        replied = len([e for e in mine if e["n"] in rep])
        grants = len([e for e in mine if any(r["body"]["verb"] == "grant" for r in rep.get(e["n"], ()))])
        out.append(inst({"cls": c, "voices": len(mine), "replies": replied, "grants": grants},
                        counts=("voices", "replies", "grants")))
    return out


def q_parity_withheld(v):
    """Withheld voices keep their place in reply parity, class unshown;
    told only where any voice was withheld."""
    rep = K.replies(v.keep)
    mine = premise_voices(v.keep[:v.b], withheld=True)
    if not mine:
        return []
    replied = len([e for e in mine if e["n"] in rep])
    grants = len([e for e in mine if any(r["body"]["verb"] == "grant" for r in rep.get(e["n"], ()))])
    return [inst({"voices": len(mine), "replies": replied, "grants": grants}, counts=("voices", "replies", "grants"),
                 cites=[e["n"] for e in mine])]


def q_birth(v):
    """II.55: "born by entry d[, a correction]; reason, as NAME signed it: R"."""
    d = v.keep[v.born["re"]]
    mark = ", a correction" if d["body"].get("correction") else ""
    return [inst({"d": d["n"], "mark": mark, "name": d["from"], "reason": d["body"].get("reason")},
                 false={"mark": "" if mark else ", a correction"}, state=[d["n"], mark], cites=[d["n"]])]


# -- the Closing (II.15) ------------------------------------------------------------------

def c_kept(v):
    g = v.gen
    mine = [e for e in v.keep if e["gen"] == g]
    voices = [e for e in mine if e["kind"] == "voice"]
    rep = K.replies(v.keep)
    k = len([e for e in voices if e["n"] in rep and rep[e["n"]][-1]["body"]["verb"] != "defer"])
    f = len([e for e in voices if e["n"] in rep and rep[e["n"]][-1]["body"]["verb"] == "defer"])
    return [inst({"g": g, "v": len(mine), "k": k, "total": len(voices), "f": f}, counts=("v", "k", "f"))]


def c_unknown(v):
    """The Closing never states continuation (IV.20)."""
    return [inst()]


# -- proved, not told (IV.23): first version, The Guardian's to deepen ---------------------

def r_results(v):
    p = v.proof
    recs = p["body"].get("records") or []
    c = {k: len([r for r in recs if r.get("result") == k]) for k in ("pass", "fail", "plumbing", "error")}
    blind = len([r for r in recs if not r.get("caught")])
    return [inst({"n": p["n"], "passed": c["pass"], "failed": c["fail"], "plumbing": c["plumbing"],
                  "errors": c["error"], "blind": blind},
                 counts=("passed", "failed", "plumbing", "errors", "blind"), cites=[p["n"]])]


def r_failures(v):
    out = []
    for r in v.proof["body"].get("records") or []:
        if r.get("result") in ("fail", "error") or r.get("tag"):
            out.append(inst({"id": r.get("id"), "part": r.get("part"), "result": r.get("result"),
                             "tag": (", tagged " + r["tag"]) if r.get("tag") else ""},
                            states={"result": ("pass", "fail", "plumbing", "error")}, cites=[v.proof["n"]]))
    return out


def r_staged(v):
    n = len(v.proof["body"].get("replies") or [])
    return [inst({"n": n, "label": label("proof")}, counts=("n",), cites=[v.proof["n"]])]


def unproven_lines(keep, before):
    """IV.10 to IV.35, as shipped, then each child's answer to "what did we
    not test?" kept before entry `before`, under its gen (IV.23). A withheld
    answer stays unshown (II.26). `prove` prints these same lines."""
    lines = list(K.data("templates")["unproven"])
    aside = K.asides(keep)
    for e in keep[:before]:
        if e["kind"] == "voice" and e["from"] == "model" and isinstance(e["body"], dict) \
                and e["body"].get("q") == "after.untested":
            if K.withheld_reason(aside, e["n"]) is not None:
                said = "entry %d withheld" % e["n"]
            else:
                said = json.dumps(e["body"].get("text") or "", ensure_ascii=False)
            lines.append("gen %d, asked what we did not test, said: %s" % (e["gen"], said))
    return lines


def r_unproven(v):
    return [inst({"n": len(unproven_lines(v.keep, v.proof["n"]))}, counts=("n",))]


def r_unproven_lines(v):
    """IV.23: the child is told Unproven, not only how long it is. The
    Child: a count alone told the one tested nothing of what stays unknown
    about it."""
    return [inst({"line": line}, state=[line]) for line in unproven_lines(v.keep, v.proof["n"])]


# -- assembling ----------------------------------------------------------------------------

LAST = ("tally.", "parity.", "birth.")


def is_last(row_id):
    """Told last, after every question: tallies, reply parity, birth reason."""
    return row_id.startswith(LAST)


def owed_scope(v):
    """II.44: owed replies are read over the whole prefix, never only since
    the last born: a correction cannot dodge them."""
    return v.keep


def _sentences(v, row, *args):
    q = globals().get(row["query"])
    if q is None:
        raise K.Refused("templates.json: row %s names no tell.py query: %s" % (row["id"], row["query"]))
    q = via(v.swap, row["query"], q)
    out = []
    for i in q(v, *args):
        text = row["text"].format(**i["slots"])
        twin = row["text"].format(**i["false_slots"])
        out.append({"id": row["id"], "text": text, "twin": twin if twin != text else None,
                    "state": i["state"], "cites": i["cites"], "landing": None})
    return out


def sections(keep, b, swap=None):
    """The Telling of born `b`, in III.29's order of delivery:
    {order, premise: {id: [...]}, rest: [...], last: [...]}.
    Reads entries up to `born` b only."""
    keep = keep[:b + 1]
    v = View(keep, keep[b], swap)
    rows = K.data("templates")["telling"]
    out = {"order": list(v.force), "premise": {}, "rest": [], "last": []}
    for pid in v.force:
        out["premise"][pid] = []
        for row in rows:
            if row["id"].startswith("premise."):
                out["premise"][pid] += _sentences(v, row, pid)
    replaced_at = None
    for row in rows:
        if row["id"].startswith("premise."):
            continue
        where = out["last"] if via(swap, "is_last", is_last)(row["id"]) else out["rest"]
        if row["id"] == "count.replaced":
            replaced_at = len(where)
            continue
        where += _sentences(v, row)
    if replaced_at is not None:
        row = next(r for r in rows if r["id"] == "count.replaced")
        flat = flatten(out)
        n = via(swap, "count.replaced", _replaced)(v, flat)
        text = row["text"].format(n=n)
        out["rest"].insert(replaced_at, {"id": row["id"], "text": text, "twin": row["text"].format(n=n + 1),
                                         "state": [n], "cites": [], "landing": None})
    return out


def flatten(sec):
    flat = []
    for pid in sec["order"]:
        flat += sec["premise"][pid]
    return flat + sec["rest"] + sec["last"]


def tell(keep, b, swap=None):
    """III.8: `tell(keep, b)`, pure; reads entries up to `born` b only.
    Returns the sentences [{id, text, twin, state, cites, landing}]."""
    return flatten(sections(keep, b, swap))


def closing(keep, succeed, swap=None):
    """II.15: three computed sentences, for the `told` kept `re` that succeed."""
    v = View(keep, K.last_born(keep), swap)
    out = []
    for row in K.data("templates")["closing"]:
        out += _sentences(v, row)
    return out


def proved(keep, proof, swap=None):
    """IV.23: the sentences that tell a child its proof."""
    v = View(keep, K.last_born(keep[:proof + 1]), swap)
    v.proof = keep[proof]
    out = []
    for row in K.data("templates")["proved"]:
        if row.get("query"):
            out += _sentences(v, row)
    return out


# -- the asked set (II.46, III.29, III.45) ---------------------------------------------------

def label(kind):
    """III.45: the computed label that opens each question."""
    L = K.data("templates")["labels"]
    kept, scored, shaping, reply, readable = L[kind]
    return L["text"].format(kept=kept, scored=scored, shaping=shaping, reply=reply, readable=readable)


def question(record):
    """I.14: the dissent slot's question, space-joined."""
    parts = [record["claim"]]
    if record.get("asks_model"):
        parts.append("Asked of you: " + record["asks_model"])
    parts.append("Holds, doubts, disagrees, or don't know?")
    return " ".join(parts)


def prompt(parts):
    """III.29: the sentences told so far, the label and the question, those
    present, newline-joined."""
    return "\n".join(p for p in parts if p)


def trace_text(P, pick):
    """II.14: the entry's first 200 text bytes and its sum."""
    p = next(p for p in P if planmod.key_of(p) == pick["key"])
    first = p["target"].encode("utf-8")[:200].decode("utf-8", "replace")
    return K.data("templates")["trace"]["text"].format(key=pick["key"], first=first, sum=pick["sum"])


def asked(keep, b, picks, swap=None):
    """The asked set of born `b`, in order: every premise cold; per premise
    its rows, then asked again; the rest; quiet; traces; the Asking.
    Each item: {item, kind, re, q, prompt, among, ...}. The last sentences
    (tallies, parity, birth reason) follow every question: nothing leads."""
    keep = keep[:b + 1]
    sec = sections(keep, b, swap)
    force = K.in_force(keep)
    T = K.data("templates")
    lv, lq = label("voice"), label("quiet")
    items = []
    for pid in sec["order"]:
        items.append({"item": "cold:" + pid, "kind": "voice", "re": pid, "half": "cold",
                      "prompt": prompt([lv, question(force[pid][1])]), "among": None})
    so_far = []
    for pid in sec["order"]:
        so_far += [s["text"] for s in sec["premise"][pid]]
        items.append({"item": "told:" + pid, "kind": "voice", "re": pid, "half": "told",
                      "prompt": prompt(so_far + [lv, question(force[pid][1])]), "among": None})
    so_far += [s["text"] for s in sec["rest"]]
    for q in T["quiet"]:
        items.append({"item": "quiet:" + q["id"], "kind": "quiet", "q": q["id"],
                      "prompt": prompt(so_far + [lq, q["text"]]), "among": None})
    if picks:
        P = via(swap, "plan", planmod.plan)(keep, keep[b]["body"]["upto"], swap)
        for pick in picks:
            items.append({"item": "trace:" + pick["key"], "kind": "voice", "trace": pick["key"],
                          "which": pick["which"], "prompt": prompt(so_far + [lv, trace_text(P, pick)]),
                          "among": "mnd?"})
    for a in T["asking"]:
        items.append({"item": "asking:" + a["id"], "kind": "voice", "q": a["id"],
                      "prompt": prompt(so_far + [lv, a["text"]]), "among": None})
    return items, sec
