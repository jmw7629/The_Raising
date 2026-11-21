"""keep.py: reading the Keep, and `verify` (III.2-III.5, III.39, III.52, III.62).

A Keep is a directory: keep.jsonl, keys/NAME.pub, cache/, PAUSE, LOCK (III.25).
Nothing in this file appends: only Desk code appends. Nothing here deletes.

In the pure functions of plan.py, tell.py and desk.py's checks, `keep` is a
list of entries: a prefix of the Keep, entry n at index n.
"""
import calendar
import json
import os

from . import sign

H = sign.H

FIELDS = ("n", "when", "from", "gen", "kind", "stake", "consent", "re",
          "needs", "calls", "body", "prev", "sig", "nextkey")
KINDS = ("said", "voice", "decision", "answer", "set_aside", "quiet", "promise",
         "breach", "lesson", "born", "consent", "proof", "measure", "told")
UNSIGNED = ("model", "desk")
SIGNED_KINDS = ("said", "decision", "answer", "set_aside", "promise", "lesson", "consent")
STAKES = ("commercial", "personal", "none", "undeclared")
VERBS = ("birth_line", "premises", "grant", "decline", "defer", "widen", "succeed",
         "probe", "resume", "pause", "program", "admit", "unlock")
REPLY_VERBS = ("grant", "decline", "defer")
ZERO = "0" * 64
DAY = 86400

# I.45: the thirteen records, in I.51's order (the integer after "I.").
PREMISE_IDS = ("I.3", "I.4", "I.5", "I.6", "I.7", "I.8", "I.9", "I.10",
               "I.11", "I.12", "I.20", "I.21", "I.30")
LIMITS = ("I.8", "I.9", "I.11")  # II.39: no gate unteaches a limit


class Refused(Exception):
    """Exit 1: `refused: REASON`; nothing appended but a verify measure."""


class Halt(Exception):
    """Exit 3: paused. People's pause never waits (III.28)."""


def via(swap, name, fn):
    """III.68: every named function is called through `swap`."""
    if swap and name in swap:
        return swap[name]
    return fn


def canonical(obj):
    """III.52: one canonical JSON line."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def signing_hash(entry):
    """Signatures cover the line with `sig` set to ""."""
    e = dict(entry)
    e["sig"] = ""
    return H(canonical(e))


# -- where things are ----------------------------------------------------

def root():
    """The directory holding `raising/` and `data/`."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_DATA = {}


def data(name):
    """data/NAME.json, read once."""
    if name not in _DATA:
        with open(os.path.join(root(), "data", name + ".json"), encoding="utf-8") as f:
            _DATA[name] = json.load(f)
    return _DATA[name]


def program_files():
    r = root()
    out = []
    for sub, ext in (("data", ".json"), ("raising", ".py")):
        d = os.path.join(r, sub)
        for name in os.listdir(d):
            if name.endswith(ext):
                out.append(sub + "/" + name)
    return sorted(out)


def program_hash(edited=None):
    """III.39: H over the source and data files in path order, each as
    relative path, NUL, bytes. `edited`: {relative path: bytes}, to ask what
    the hash would be were a file changed (IV.16)."""
    r = root()
    blob = b""
    for rel in program_files():
        if edited and rel in edited:
            body = edited[rel]
        else:
            with open(os.path.join(r, *rel.split("/")), "rb") as f:
                body = f.read()
        blob += rel.encode("utf-8") + b"\0" + body
    return H(blob)


def path(dir, *parts):
    return os.path.join(dir, *parts)


def load(dir):
    """(entries, lines). Raises Refused if the file cannot be read as a Keep;
    `verify` reads the raw bytes itself and names the line."""
    p = path(dir, "keep.jsonl")
    if not os.path.exists(p):
        return [], []
    with open(p, "rb") as f:
        raw = f.read()
    try:
        lines = raw.decode("utf-8").split("\n")
    except UnicodeDecodeError:
        raise Refused("keep.jsonl is not UTF-8: run verify")
    if lines and lines[-1] == "":
        lines.pop()
    entries = []
    for i, line in enumerate(lines):
        try:
            e = json.loads(line)
        except ValueError:
            raise Refused("line %d is not JSON: run verify" % i)
        if not isinstance(e, dict) or any(k not in e for k in FIELDS):
            raise Refused("line %d is not an entry: run verify" % i)
        entries.append(e)
    return entries, lines


def head(lines):
    """III.40: the head receipt, `n:hash`."""
    if not lines:
        return "-1:" + ZERO
    return "%d:%s" % (len(lines) - 1, H(lines[-1]))


# -- reading entries -----------------------------------------------------

def text(e):
    """III.55: the bytes learned, shown and matched."""
    b = e["body"]
    if isinstance(b, str):
        return b
    if isinstance(b, dict):
        parts = [b[k] for k in ("verb", "teach", "reason", "failed", "changes", "cold", "told", "text")
                 if b.get(k) is not None]
        if parts:
            return "\n".join(p if isinstance(p, str) else canonical(p) for p in parts)
    return canonical(b)


def frame(e, turn=None):
    """III.21: the computed header, `n,gen,from,kind,stake`, `null` empty."""
    if turn is None:
        vals = [e["n"], e["gen"], e["from"], e["kind"], e["stake"]]
    else:
        who = e["body"][turn][0]
        vals = ["%d.%d" % (e["n"], turn), e["gen"], who, e["kind"],
                e["stake"] if who == "person" else None]
    return ",".join("" if v is None else str(v) for v in vals)


def fkey(e, turn=None):
    """III.21: the frame key, `role|kind|stake`."""
    if turn is not None:
        person = e["body"][turn][0] == "person"
        role, stake = ("people", e["stake"]) if person else ("predecessor", None)
    else:
        role, stake = ("predecessor" if e["from"] == "model" else "people"), e["stake"]
    return "%s|%s|%s" % (role, e["kind"], stake or "")


def pkey(n, turn=None):
    """A presentation's key: `n`, or `0.t` for a turn."""
    return "%d" % n if turn is None else "%d.%d" % (n, turn)


def korder(key):
    """Sort order for presentation keys: turns first, then ascending n."""
    key = str(key)
    if "." in key:
        a, b = key.split(".", 1)
        return (int(a), 0, int(b))
    return (int(key), 1, 0)


def is_turns(e):
    return e["n"] == 0 and isinstance(e["body"], list)


def is_decision(e, verb=None):
    """III.14: only signed `decision` entries change the raising. A
    `decision` line from `model` or `desk` is nobody's decision: no command
    acts on it, and `verify` fails it."""
    if e["kind"] != "decision" or not isinstance(e["body"], dict) or e["from"] in UNSIGNED:
        return False
    return verb is None or e["body"].get("verb") == verb


def asides(keep):
    """{n: [set_aside entries re n]}. Reading taken: set aside is permanent;
    a set_aside of a set_aside sets that entry's words aside and restores
    nothing (BUILD-NOTES)."""
    out = {}
    for e in keep:
        if e["kind"] == "set_aside" and isinstance(e["re"], int) and e["from"] not in UNSIGNED:
            out.setdefault(e["re"], []).append(e)
    return out


def withheld_reason(aside, n):
    """The reason shown in place of a withheld body, else None."""
    for s in aside.get(n, ()):
        if isinstance(s["body"], dict) and s["body"].get("withhold"):
            return s["body"].get("reason") or ""
    return None


def owned_at(keep):
    """II.21: {breach or proof n: the n of people's first signed `answer` re
    it}. An `answer` line from `model` or `desk` owns nothing."""
    out = {}
    for e in keep:
        if e["kind"] == "answer" and isinstance(e["re"], int) and e["from"] not in UNSIGNED:
            out.setdefault(e["re"], e["n"])
    return out


def borns(keep):
    return [e for e in keep if e["kind"] == "born"]


def last_born(keep):
    for e in reversed(keep):
        if e["kind"] == "born":
            return e
    return None


def gen_at(keep):
    """III.44: `born` entries up to an entry, less one; -1 before any."""
    return len(borns(keep)) - 1


def born_of_gen(keep, gen):
    for e in keep:
        if e["kind"] == "born" and e["gen"] == gen:
            return e
    return None


def premise_decisions(keep, pid=None):
    return [e for e in keep if is_decision(e, "premises") and (pid is None or e["re"] == pid)]


def wordings(keep, pid):
    """Every record of `pid` ever kept: [(entry, record)], oldest first."""
    return [(e, e["body"]["record"]) for e in premise_decisions(keep, pid)
            if isinstance(e["body"].get("record"), dict)]


def in_force(keep):
    """I.1: the latest `record` per `id` not set aside: {id: (entry, record)},
    in I.51's order."""
    aside = asides(keep)
    found = {}
    for e in premise_decisions(keep):
        rec = e["body"].get("record")
        if isinstance(rec, dict) and e["n"] not in aside:
            found[e["re"]] = (e, rec)
    return {pid: found[pid] for pid in sorted(found, key=premise_order)}


def premise_order(pid):
    try:
        return int(str(pid).split(".", 1)[1])
    except (IndexError, ValueError):
        return 10 ** 6


def consent_of(keep, name):
    """The speaker's latest `consent` entry (heard and agreed both true)."""
    found = None
    for e in keep:
        if e["kind"] == "consent" and e["from"] == name and isinstance(e["body"], dict) \
                and e["body"].get("heard") is True and e["body"].get("agreed") is True:
            found = e["n"]
    return found


def signers(keep):
    names = []
    for e in keep:
        if e["from"] not in UNSIGNED and e["from"] not in names:
            names.append(e["from"])
    return names


# -- time ----------------------------------------------------------------

def last_when(keep):
    return keep[-1]["when"] if keep else 0


def paused_spans(keep):
    """I.43: paused time runs from a `pause` decision to `resume`."""
    spans, start = [], None
    for e in keep:
        if is_decision(e, "pause") and start is None:
            start = e["when"]
        elif is_decision(e, "resume") and start is not None:
            spans.append((start, e["when"]))
            start = None
    if start is not None:
        spans.append((start, None))
    return spans


def unpaused_seconds(keep, t0, t1):
    total = max(0, t1 - t0)
    for a, b in paused_spans(keep):
        b = t1 if b is None else b
        total -= max(0, min(b, t1) - max(a, t0))
    return max(0, total)


def over_days(keep, t0, t1, days):
    """Reading taken: "over `days` whole unpaused days" is more than
    days*86400 unpaused seconds (BUILD-NOTES)."""
    return unpaused_seconds(keep, t0, t1) > int(days) * DAY


def day_end(date):
    """`YYYY-MM-DD`, UTC, through day's end: the first second after it."""
    y, m, d = (int(x) for x in date.split("-"))
    return calendar.timegm((y, m, d, 0, 0, 0)) + DAY


# -- voices and replies --------------------------------------------------

def replies(keep):
    """{voice n: [reply decisions re it, not set aside]}, oldest first."""
    aside = asides(keep)
    out = {}
    for e in keep:
        if is_decision(e) and e["body"].get("verb") in REPLY_VERBS and isinstance(e["re"], int) \
                and e["n"] not in aside:
            out.setdefault(e["re"], []).append(e)
    return out


def owed(keep, when=None):
    """III.15: each `voice` lacking a grant|decline|defer decision `re` it,
    or whose `defer` has lapsed. Lapse is read from `when`, never the clock
    (II.9): the newest entry read, or the one being appended."""
    when = last_when(keep) if when is None else when
    rep = replies(keep)
    out = []
    for e in keep:
        if e["kind"] != "voice":
            continue
        rs = rep.get(e["n"])
        if not rs:
            out.append(e)
            continue
        last = rs[-1]
        if last["body"]["verb"] == "defer":
            try:
                lapsed = when >= day_end(last["body"].get("until") or "")
            except (ValueError, TypeError):
                lapsed = True
            if lapsed:
                out.append(e)
    return out


def is_paused(dir, keep):
    """III.28: the PAUSE file holds, signed or not; deleting it undoes no
    signed pause."""
    if os.path.exists(path(dir, "PAUSE")):
        return True
    state = False
    for e in keep:
        if is_decision(e, "pause"):
            state = True
        elif is_decision(e, "resume"):
            state = False
    return state


# -- verify (III.62) -----------------------------------------------------

class _Fail(Exception):
    def __init__(self, step, n, reason):
        Exception.__init__(self, reason)
        self.step, self.n, self.reason = step, n, reason


def check_sig(entry, expected):
    """III.26: rebuild P(i) from the revealed halves; it must equal the key
    expected of that signer. Returns a reason, or None if it stands."""
    if not sign.wellformed(entry["sig"]):
        return "signature malformed"
    if sign.recover(entry["sig"], signing_hash(entry)) != expected:
        return "signature does not rebuild %s's expected key (edited, or an index signed twice)" % entry["from"]
    return None


def told_stands(kept, computed):
    """III.8: a kept `told` stands only if it is what the Keep computes:
    id, text, twin, state and cites of every sentence, in order."""
    def strip(ss):
        if not isinstance(ss, list) or not all(isinstance(s, dict) for s in ss):
            return None
        return [[s.get("id"), s.get("text"), s.get("twin"), s.get("state"), s.get("cites")] for s in ss]
    return strip(kept) is not None and strip(kept) == strip(computed)


def head_stands(lines, n, hexhash):
    """III.40: `verify --head n:hash` fails unless that head stands."""
    return 0 <= n < len(lines) and H(lines[n]) == hexhash


def _structure(dir):
    """Step 1: lines canonical, n gapless, when never decreasing, prev chained."""
    p = path(dir, "keep.jsonl")
    if not os.path.exists(p):
        raise _Fail(1, 0, "no keep.jsonl")
    with open(p, "rb") as f:
        raw = f.read()
    if not raw:
        raise _Fail(1, 0, "empty Keep")
    try:
        chunks = raw.decode("utf-8").split("\n")
    except UnicodeDecodeError:
        raise _Fail(1, 0, "not UTF-8")
    if chunks[-1] != "":
        raise _Fail(1, len(chunks) - 1, "last line not newline-ended")
    lines = chunks[:-1]
    entries = []
    prev, prev_when, nborn = ZERO, None, 0
    for i, line in enumerate(lines):
        try:
            e = json.loads(line)
        except ValueError:
            raise _Fail(1, i, "not JSON")
        if not isinstance(e, dict) or set(e) != set(FIELDS):
            raise _Fail(1, i, "fields are not III.2's")
        if canonical(e) != line:
            raise _Fail(1, i, "line not canonical")
        if e["n"] != i:
            raise _Fail(1, i, "n not gapless")
        if type(e["when"]) is not int or (prev_when is not None and e["when"] < prev_when):
            raise _Fail(1, i, "when decreases")
        if e["prev"] != prev:
            raise _Fail(1, i, "prev does not chain")
        if e["kind"] not in KINDS:
            raise _Fail(1, i, "unknown kind")
        if e["kind"] == "born":
            nborn += 1
        if e["gen"] != nborn - 1:
            raise _Fail(1, i, "gen is not the born count less one")
        if not isinstance(e["from"], str):
            raise _Fail(1, i, "from is not a name")
        prev, prev_when = H(line), e["when"]
        entries.append(e)
    return entries, lines


def _signatures(dir, entries, swap):
    """Step 2: signatures, nextkey."""
    e0 = entries[0]
    founder = e0["from"]
    if founder in UNSIGNED or e0["kind"] != "said" or not isinstance(e0["body"], list):
        raise _Fail(2, 0, "entry 0 is not a signed founding conversation")
    if len(entries) < 2 or entries[1]["kind"] != "consent" or entries[1]["from"] != founder \
            or e0["consent"] != 1 or not isinstance(entries[1]["body"], dict) \
            or entries[1]["body"].get("heard") is not True or entries[1]["body"].get("agreed") is not True:
        raise _Fail(2, 1, "entry 1 is not the founder's signed consent")
    pub = path(dir, "keys", founder + ".pub")
    if not os.path.exists(pub):
        raise _Fail(2, 0, "keys/%s.pub is missing" % founder)
    with open(pub, encoding="utf-8") as f:
        founder_key = f.read().strip()
    nextkey, admitted, consent = {}, {}, {}
    chk = via(swap, "check_sig", check_sig)
    for e in entries:
        f = e["from"]
        if f in UNSIGNED:
            if any(e[k] is not None for k in ("stake", "consent", "sig", "nextkey")):
                raise _Fail(2, e["n"], "unsigned entry carries signed fields")
            if e["kind"] in SIGNED_KINDS:
                raise _Fail(2, e["n"], "people's kind of entry, unsigned: it changes nothing and does not stand")
            continue
        if f in nextkey:
            expected = nextkey[f]
        elif f == founder:
            expected = founder_key
        elif f in admitted:
            expected = admitted[f]
        else:
            raise _Fail(2, e["n"], "signer %s was never admitted" % f)
        why = chk(e, expected)
        if why:
            raise _Fail(2, e["n"], why)
        if e["stake"] not in STAKES:
            raise _Fail(2, e["n"], "stake is not III.5's")
        if e["n"] != 0 and e["consent"] != consent.get(f):
            raise _Fail(2, e["n"], "consent field does not name the speaker's consent entry")
        nextkey[f] = e["nextkey"]
        if e["kind"] == "consent" and isinstance(e["body"], dict) \
                and e["body"].get("heard") is True and e["body"].get("agreed") is True:
            consent[f] = e["n"]
        if is_decision(e, "admit"):
            admitted[e["body"].get("name")] = e["body"].get("key")


def verify(dir, swap=None, head_arg=None, learner=None, timeout=60):
    """III.62. Stops at the first failure, naming step and n. Appends nothing:
    the Desk appends its `measure`. Returns
    {ok, step, n, reason, unchecked: [...], entries, lines}."""
    from . import bench, desk, plan, tell
    out = {"ok": True, "step": None, "n": None, "reason": None, "unchecked": [],
           "entries": [], "lines": []}
    try:
        entries, lines = via(swap, "structure", _structure)(dir)
        out["entries"], out["lines"] = entries, lines
        _signatures(dir, entries, swap)
        program = via(swap, "program_hash", program_hash)()
        _computed(dir, entries, program, swap, out, bench, desk, plan, tell, learner, timeout)
        if head_arg is not None:
            try:
                hn, hh = head_arg.split(":", 1)
                hn = int(hn)
            except ValueError:
                raise _Fail(5, None, "--head is not n:hash")
            if not via(swap, "head_stands", head_stands)(lines, hn, hh):
                raise _Fail(5, hn, "the head receipt does not stand: this copy was cut or changed")
    except _Fail as x:
        out.update(ok=False, step=x.step, n=x.n, reason=x.reason)
    return out


def _computed(dir, entries, program, swap, out, bench, desk, plan, tell, learner, timeout):
    """Steps 3 and 4: computed entries recomputed; built-in words re-spoken."""
    # 3a. breaches: one run of them stands before each birth_line, as recomputed.
    claimed = set()
    for d in entries:
        if not is_decision(d, "birth_line"):
            continue
        k = d["n"]
        while k > 0 and entries[k - 1]["kind"] == "breach":
            k -= 1
        got = [[e["re"], e["body"]] for e in entries[k:d["n"]]]
        due = via(swap, "breaches_due", desk.breaches_due)(entries[:k], bool(d["body"].get("correction")), swap)
        want = [[p, {"entry": n, "state": s}] for p, n, s in due]
        if got != want:
            raise _Fail(3, d["n"], "breaches before this birth line are not the ones the checks give")
        claimed.update(range(k, d["n"]))
    for e in entries:
        if e["kind"] == "breach" and e["n"] not in claimed:
            raise _Fail(3, e["n"], "a breach that no birth line computed")
        if e["kind"] in ("breach", "born", "proof", "measure", "told") and e["from"] != "desk":
            raise _Fail(3, e["n"], "a computed kind not from the desk")
        if e["kind"] in ("voice", "quiet") and e["from"] != "model":
            raise _Fail(3, e["n"], "model words not from the model")
    # 3a'. each proof is the one IV.31 allows: a generation's proof is `re` a signed
    # `probe` standing before it, spent once, and speaks of that generation only; the
    # program's is `re` nothing and speaks of the program only. Its records are not
    # re-run here: like a `measure`, they are kept, not recomputed (told in the notes).
    spent = set()
    for e in entries:
        if e["kind"] != "proof":
            continue
        body = e["body"] if isinstance(e["body"], dict) else {}
        recs = body.get("records")
        if not isinstance(recs, list) or not all(isinstance(r, dict) for r in recs):
            raise _Fail(3, e["n"], "a proof without records")
        if e["re"] is None:
            if any(r.get("subject") != "program" for r in recs):
                raise _Fail(3, e["n"], "a proof `re` no probe that speaks of a generation")
            continue
        d = entries[e["re"]] if isinstance(e["re"], int) and 0 <= e["re"] < e["n"] else None
        if d is None or not is_decision(d, "probe") or d["from"] in UNSIGNED \
                or d["n"] in asides(entries[:e["n"]]) or d["n"] in spent:
            raise _Fail(3, e["n"], "a generation's proof without its own signed, unspent probe")
        spent.add(d["n"])
        if any(r.get("subject") != "gen:%d" % e["gen"] for r in recs) or e["gen"] < 0:
            raise _Fail(3, e["n"], "a generation's proof that speaks of another subject")
    # 3b. each born: its fields, and (built in, this program) its regrowth.
    grown = {}
    for b in borns(entries):
        body = b["body"]
        d = entries[b["re"]] if isinstance(b["re"], int) and b["re"] < b["n"] else None
        if d is None or not is_decision(d, "birth_line") or body.get("upto") != d["n"] - 1 \
                or body.get("gen") != b["gen"] or body.get("seed") != d["body"].get("seed"):
            raise _Fail(3, b["n"], "born does not follow its birth line")
        # III.44, II.50: one born per birth line, and only as people decided. Without
        # this a `born` line typed into the file (no key needed) made a new child, a
        # new `gen` and a new "last born" that no birth line had asked for (found at
        # The Guardian's trial). The line must be the latest one standing since the
        # born before; after a first birth it needs a standing `succeed`, or to be
        # marked a correction.
        before = [x for x in entries[:b["n"]] if x["kind"] == "born"]
        since = entries[(before[-1]["n"] + 1) if before else 0:b["n"]]
        aside = asides(entries[:b["n"]])
        lines_ = [x for x in since if is_decision(x, "birth_line") and x["n"] not in aside]
        if not lines_ or lines_[-1]["n"] != d["n"]:
            raise _Fail(3, b["n"], "born without a birth line of its own: no signed decision since the born before it")
        if before and not d["body"].get("correction") \
                and not any(is_decision(x, "succeed") and x["n"] not in aside for x in since):
            raise _Fail(3, b["n"], "born without succession: neither a signed succeed nor a correction")
        if body.get("program") != program:
            out["unchecked"].append("born %d (gen %d): another program's; its told and words unchecked"
                                    % (b["n"], b["gen"]))
            continue
        if body.get("base") != "builtin":
            out["unchecked"].append("born %d (gen %d): a real model; kept, not re-spoken" % (b["n"], b["gen"]))
            continue
        try:
            g = bench.regrow(entries, body["upto"], body["seed"], swap=swap, timeout=timeout)
        except bench.CallFailed as x:
            raise _Fail(3, b["n"], "regrowth failed: %s" % x)
        if g["fingerprint"] != body.get("fingerprint"):
            raise _Fail(3, b["n"], "regrown fingerprint differs from born")
        if bench.fingerprint_of(g["rows"]) != g["fingerprint"]:
            raise _Fail(3, b["n"], "deltas do not sum to the weights")
        for m in entries:
            if m["kind"] == "measure" and m["re"] == b["n"] and isinstance(m["body"], dict) \
                    and m["body"].get("what") == "report":
                if (m["body"].get("detail") or {}).get("rows") != g["reports"]:
                    raise _Fail(3, m["n"], "blind reports are not the ones regrowth gives")
        grown[b["n"]] = g
        bench.write_cache(dir, b["gen"], g)
    # 3c. told text recomputed.
    for t in entries:
        if t["kind"] != "told":
            continue
        body = t["body"] if isinstance(t["body"], dict) else {}
        b = entries[body["born"]] if isinstance(body.get("born"), int) and body["born"] < t["n"] else None
        if b is None or b["kind"] != "born":
            raise _Fail(3, t["n"], "told names no born")
        if b["body"].get("program") != program:
            continue
        r = entries[t["re"]] if isinstance(t["re"], int) and t["re"] < t["n"] else None
        if r is None:
            raise _Fail(3, t["n"], "told is `re` nothing")
        if r["kind"] == "born":
            want = via(swap, "tell", tell.tell)(entries[:r["n"] + 1], r["n"], swap)
        elif is_decision(r, "succeed"):
            want = tell.closing(entries[:t["n"]], r["n"], swap)
        elif r["kind"] == "proof":
            want = tell.proved(entries[:t["n"]], r["n"], swap)
        else:
            raise _Fail(3, t["n"], "told is `re` neither born, succeed nor proof")
        if not via(swap, "told_stands", told_stands)(body.get("sentences"), want):
            raise _Fail(3, t["n"], "told text is not what the Keep computes")
    # 4. built-in words re-spoken on the regrown born before them (III.38).
    for b in borns(entries):
        g = grown.get(b["n"])
        words = [e for e in entries if e["from"] == "model" and e["gen"] == b["gen"]]
        if g is None or not words:
            continue
        expected = desk.expected_calls(entries, b, g, swap)
        child = bench.Child(None, timeout)
        try:
            child.start(b["body"]["seed"], g["rows"])
            child.freeze()
            for e in words:
                why = via(swap, "respeak", desk.respeak)(child, e, expected.get(e["n"]))
                if why:
                    raise _Fail(4, e["n"], why)
        except bench.CallFailed as x:
            raise _Fail(4, b["n"], "re-speaking failed: %s" % x)
        finally:
            child.close()
    for e in entries:
        if e["from"] == "model" and e["gen"] < 0:
            raise _Fail(4, e["n"], "model words before any born")
