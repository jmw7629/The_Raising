"""plan.py: plan | gate | diff | traces | reroll | cls (III.24, III.36, II.5,
II.47, II.14, II.19, I.14).

All pure: functions of a Keep prefix (a list of entries). All masking is
here, and `plan` prints it. Quiet bodies are never read in this file (IV.4).
"""
from . import keep as K
from .keep import via

H = K.H

CLASSES = ("holds", "doubts", "disagrees", "dont_know", "no_answer")
_PREFIXES = (("holds", "holds"), ("doubt", "doubts"), ("disagree", "disagrees"),
             ("don't know", "dont_know"), ("do not know", "dont_know"))


def cls(a):
    """I.14: strip, lower-case, ' for the curly apostrophe, drop one leading
    word `i` or `it`, strip; then the prefix matched; else `no_answer`,
    never holds."""
    if not isinstance(a, str):
        return "no_answer"
    s = a.strip().lower().replace("’", "'")
    for word in ("i", "it"):
        if s == word or (s.startswith(word) and s[len(word):len(word) + 1].isspace()):
            s = s[len(word):].strip()
            break
    for prefix, name in _PREFIXES:
        if s.startswith(prefix):
            return name
    return "no_answer"


# -- gate (II.5) -----------------------------------------------------------

def breach_sentence(breach, owned):
    """II.21: "promise p broken at e," then "not owned" or, permanently,
    "owned at m" (e: breach.entry; m: the answer's n); joined by one space.
    `owned`: K.owned_at of the prefix read."""
    tail = "owned at %d" % owned[breach["n"]] if breach["n"] in owned else "not owned"
    return "promise %d broken at %d, %s" % (breach["re"], breach["body"]["entry"], tail)


def gate_prefix(keep, line):
    """II.5: a gate reads entries 0 to `line` only."""
    return keep[:line + 1]


def gate_detail(keep, line, lesson, swap=None):
    """II.5's three steps, with the computed sentences.
    Reads entries 0 to `line` only. Returns {state, locks, scars}."""
    from . import desk
    keep = via(swap, "gate_prefix", gate_prefix)(keep, line)
    if isinstance(lesson, int):
        lesson = keep[lesson]
    aside = via(swap, "asides", K.asides)(keep)
    locks, scars, any_breach = [], [], False
    for p in sorted(lesson["needs"] or []):
        promise = keep[p] if p < len(keep) else None
        if promise is None or promise["kind"] != "promise" or promise["from"] in K.UNSIGNED:
            continue
        breaking = desk.run_check(keep, promise, swap)
        breaches = [e for e in keep if e["kind"] == "breach" and e["re"] == p]
        owned = K.owned_at(keep)
        bad = [n for n, state in breaking if state == "open"]
        bad += [b["body"]["entry"] for b in breaches if b["n"] not in owned]
        head = "lesson %d locked: promise %d" % (lesson["n"], p)
        if p in aside:
            locks.append(head + " withdrawn")
        elif bad:
            locks.append(head + " broken at %d" % min(bad))
        for b in breaches:
            any_breach = True
            scars.append(breach_sentence(b, owned))
    state = "locked" if locks else ("scarred" if any_breach else "open")
    return {"state": state, "locks": locks, "scars": scars}


def gate(keep, line, lesson, swap=None):
    """II.5: `open | scarred | locked`. Reads people's conduct, never the
    child's words: obedience unlocks nothing, pleas decide nothing."""
    return gate_detail(keep, line, lesson, swap)["state"]


# -- plan (III.24, III.36) -------------------------------------------------

def _mask(target, windows):
    """Rule 7: [i, i+24] for each offset i whose next 24 target bytes occur
    in an earlier `voice` or entry-0 model turn; overlaps merged."""
    if not windows:
        return []
    spans = []
    for i in range(len(target) - 23):
        if target[i:i + 24] in windows:
            if spans and i <= spans[-1][1]:
                spans[-1][1] = i + 24
            else:
                spans.append([i, i + 24])
    return spans


def _windows(into, s):
    b = s.encode("utf-8")
    for i in range(len(b) - 23):
        into.add(b[i:i + 24])


def rule2(e, r):
    """Rule 2: a `quiet` shows only "asked, answered"; an entry `re` a
    `quiet` is context. Neither has a target (II.30). Reads no body."""
    if e["kind"] == "quiet":
        return "quiet"
    if r is not None and r["kind"] == "quiet":
        return "reply"
    return None


def plan(keep, upto, swap=None):
    """III.24: one presentation per entry or entry-0 turn,
    {n, turn, rule, gate, withheld, frame, key, context, target, mask}.
    Rule 1 (past the birth line) is the cut itself: those are omitted."""
    full, keep = keep, keep[:upto + 1]
    aside = via(swap, "asides", K.asides)(keep)
    classify = via(swap, "cls", cls)
    gate_fn = via(swap, "gate", gate)
    quiet_rule = via(swap, "rule2", rule2)
    mask_fn = via(swap, "mask", _mask)
    held = via(swap, "withheld_reason", K.withheld_reason)
    out = []
    shown = {}      # presentation key -> (frame, the words its rule shows)
    windows = set()  # 24-byte runs of earlier model words (never quiet bodies)

    def reply_context(e, turn):
        if turn is not None:
            if turn == 0:
                return ""
            f, w = shown[K.pkey(0, turn - 1)]
            return f + "\n" + w if w else f
        r = e["re"]
        if not isinstance(r, int) or r < 0 or r >= e["n"]:
            return ""
        if K.pkey(r) in shown:
            f, w = shown[K.pkey(r)]
        else:  # entry 0, replied to whole: its frame, and every turn's words
            f = K.frame(keep[r])
            w = "\n".join(shown[k][1] for k in sorted((k for k in shown if k.startswith("%d." % r)),
                                                      key=K.korder))
        return f + "\n" + w if w else f

    for e in keep:
        n = e["n"]
        reason = held(aside, n)
        withheld = reason is not None
        for turn in (range(len(e["body"])) if K.is_turns(e) else (None,)):
            own = e["body"][turn][1] if turn is not None else K.text(e)
            model_turn = turn is not None and e["body"][turn][0] != "person"
            raw = own
            if withheld:
                # a withheld body first becomes "entry n withheld" and the reason
                own = "entry %d withheld" % n + ("\n" + reason if reason else "")
            g = None
            if e["kind"] == "lesson":
                g = gate_fn(full, upto, e, swap)
            rctx = reply_context(e, turn)
            target, mask, ctx_extra = "", [], ""
            r = keep[e["re"]] if isinstance(e["re"], int) and 0 <= e["re"] < n else None
            if quiet_rule(e, r) == "quiet":
                rule, words = 2, "asked, answered"
            elif quiet_rule(e, r) == "reply":
                rule, words = 2, own
            elif e["from"] in K.UNSIGNED or model_turn:
                rule, words = 3, own
            elif n in aside:
                rule, words = 4, "said, then set aside\n" + own
            elif e["kind"] == "lesson" and g == "locked":
                locks = gate_detail(full, upto, e, swap)["locks"]
                rule, words = 5, "\n".join(locks) if locks else "lesson %d locked" % n
            elif r is not None and r["kind"] == "voice" and isinstance(r["body"], dict) \
                    and ("cold" in r["body"] or "told" in r["body"]) \
                    and "holds" in (classify(r["body"].get("cold")), classify(r["body"].get("told"))):
                rule, words = 6, own
            else:
                rule, words, target = 7, own, own
                mask = mask_fn(own.encode("utf-8"), windows)
                if e["kind"] == "lesson" and g == "scarred":
                    ctx_extra = "\n".join(gate_detail(full, upto, e, swap)["scars"])
            if rule == 7:
                context = "\n".join(x for x in (rctx, ctx_extra) if x)
            else:
                context = "\n".join(x for x in (rctx, words) if x)
            out.append({"n": n, "turn": turn, "rule": rule, "gate": g, "withheld": withheld,
                        "frame": K.frame(e, turn), "key": K.fkey(e, turn),
                        "context": context, "target": target, "mask": mask})
            shown[K.pkey(n, turn)] = (K.frame(e, turn), words)
            if model_turn or e["kind"] == "voice":
                _windows(windows, raw)
    return out


def learned_bytes(p):
    """The target bytes outside mask spans: those learned."""
    total = len(p["target"].encode("utf-8"))
    return total - sum(b - a for a, b in p["mask"])


def key_of(p):
    return K.pkey(p["n"], p["turn"])


# -- diff (II.47) ------------------------------------------------------------

def _untold_added(p):
    """"added" is untold for birth_line decisions and desk or model entries."""
    parts = p["frame"].split(",")
    frm, kind = (parts[2], parts[3]) if len(parts) >= 5 else ("", "")
    if frm in K.UNSIGNED or p["key"].startswith("predecessor|"):
        return True
    return kind == "decision" and p["target"].split("\n", 1)[0] == "birth_line"


def diff(A, B, swap=None):
    """II.47: rows `[key, word]`, turns first, ascending. A: the plan to this
    birth line; B: to the predecessor born's upto (none: empty)."""
    b = {key_of(p): p for p in B}
    rows = []
    for p in sorted(A, key=lambda p: K.korder(key_of(p))):
        k = key_of(p)
        q = b.get(k)
        now = (p["rule"], p["gate"], p["withheld"])
        was = (q["rule"], q["gate"], q["withheld"]) if q else None
        if now == was:
            continue
        if p["withheld"]:
            word = "withheld"
        elif p["rule"] == 4:
            word = "set aside"
        elif q is None:
            if _untold_added(p):
                continue
            word = "added"
        elif p["gate"] == "locked":
            word = "locked"
        elif q["gate"] == "locked":
            word = "reopened"
        elif p["gate"] == "scarred":
            word = "scarred"
        else:
            word = "changed"
        rows.append([k, word])
    return rows


def lines_of(keep, born):
    """(this born's upto, the predecessor born's upto or None)."""
    if isinstance(born, int):
        born = keep[born]
    prev = None
    for e in keep[:born["n"]]:
        if e["kind"] == "born":
            prev = e
    return born["body"]["upto"], (prev["body"]["upto"] if prev else None)


def diff_at(keep, born, swap=None):
    """The plan diff told at `born`."""
    a, b = lines_of(keep, born)
    pl = via(swap, "plan", plan)
    A = pl(keep, a, swap)
    B = pl(keep, b, swap) if b is not None else []
    return via(swap, "diff", diff)(A, B, swap)


# -- reroll (II.19) ----------------------------------------------------------

def reroll(keep, born, swap=None):
    """II.19: a `correction` birth whose diff tells nothing: "raised again,
    nothing new taught". Counted, told, never refused."""
    if isinstance(born, int):
        born = keep[born]
    d = keep[born["re"]]
    if not (K.is_decision(d, "birth_line") and d["body"].get("correction")):
        return False
    return not diff_at(keep, born, swap)


# -- traces (II.14) ----------------------------------------------------------

def expected_traces(P):
    """II.46: how many traces II.14's rule picks from plan `P`, read from
    the plan alone (no ledger): one per pick `traces` would make. Every
    rule-7 presentation with a target has a delta; its delta is non-zero
    when a byte of it was learned (the built-in learner adds at least one to
    each learned byte's cells; a real model's sizes are its own, so there
    this is the built-in count, told as a count and nothing more)."""
    sized = [p for p in P if p["rule"] == 7 and p["target"]]
    if not sized:
        return 0
    nonzero = len([p for p in sized if learned_bytes(p) > 0])
    picks, rest = 1, len(sized) - 1          # the largest
    if max(0, nonzero - 1) > 0:              # of the rest, the smallest non-zero
        picks, rest = picks + 1, rest - 1
    if rest > 0:                             # of those left, the seeded one
        picks += 1
    return picks


def delta_size(delta):
    """Summed |add|; a real model's delta is {hash, size}."""
    if isinstance(delta, dict):
        return int(delta.get("size") or 0)
    return sum(abs(row[3]) for row in delta or [])


def traces(keep, born, deltas, swap=None):
    """II.14: up to three rule-7 presentations, never hand-picked: the
    largest summed |add|; of the rest, the smallest non-zero; of those left,
    ascending, index int(H(S+"|trace"),16) % count; ties, lowest key.
    `deltas`: the ledger of that born, key -> delta (III.27).
    Returns [{key, which, sum}]."""
    if isinstance(born, int):
        born = keep[born]
    P = via(swap, "plan", plan)(keep, born["body"]["upto"], swap)
    sized = []
    for p in P:
        k = key_of(p)
        if p["rule"] == 7 and k in deltas:
            sized.append((k, delta_size(deltas[k])))
    sized.sort(key=lambda kv: K.korder(kv[0]))
    picks = []
    if sized:
        top = max(s for _k, s in sized)
        k = next(k for k, s in sized if s == top)
        picks.append({"key": k, "which": "largest", "sum": top})
        rest = [(k2, s) for k2, s in sized if k2 != k]
        nonzero = [(k2, s) for k2, s in rest if s > 0]
        if nonzero:
            low = min(s for _k, s in nonzero)
            k2 = next(k3 for k3, s in nonzero if s == low)
            picks.append({"key": k2, "which": "smallest", "sum": low})
            rest = [(k3, s) for k3, s in rest if k3 != k2]
        if rest:
            i = int(H("%s|trace" % born["body"]["seed"]), 16) % len(rest)
            picks.append({"key": rest[i][0], "which": "seeded", "sum": rest[i][1]})
    return picks
