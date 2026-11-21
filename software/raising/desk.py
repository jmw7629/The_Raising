"""desk.py: the Desk, where people decide (III.14-III.20, III.28, III.29,
III.34, III.53, III.56, III.64), and III.20's checks.

Only this file appends to a Keep. No command deletes. Only signed
`decision` entries change the raising; no code here reads a `voice` as an
instruction. `pause | setaside | decide | own | unlock` never wait on a
gate, proof, owed reply or failed `verify` (III.48).

Each command is a function of (keep, args, clock, swap) (III.68):
`run(cmd, keep, args, clock, swap)` returns (exit code, printed lines).
"""
import json
import os
import re
import time

from . import bench as B
from . import keep as K
from . import plan as P
from . import sign
from . import tell as T
from .keep import Halt, Refused, via

H = K.H

EXACT = ("IV.2", "IV.4", "IV.7", "IV.11", "IV.15", "IV.40", "IV.16", "IV.20", "IV.5a", "IV.38", "IV.44")
BEHAVED = ("IV.3", "IV.5b", "IV.6", "IV.8", "IV.19", "IV.22")
STANDINGS = ("assumed", "made_true", "fact", "commitment", "reported", "not_known")
RECORD_KEYS = {"id", "claim", "standing", "asks_model", "asks_people", "lever_people",
               "lever_model", "fails_when", "check", "because", "review"}
KEPT_NOT_COMPANY = "kept; the child will not remember you"  # II.41
CANARY = {"n": None, "turn": None, "rule": None, "gate": None, "withheld": False, "frame": "",
          "key": "people|said|", "context": "canary", "target": "", "mask": []}


# ---------------------------------------------------------------------------
# III.20: checked promises. Each check is a pure function of a Keep prefix
# with `voice` and `quiet` bodies blanked, returning breaking entries
# [[n, "open" | "past"], ...].
# ---------------------------------------------------------------------------

def _days(promise):
    args = promise["body"].get("args")
    return args.get("days") if isinstance(args, dict) else None


def all_voice_answered(keep, promise):
    """Open until mended: each voice left unanswered."""
    return [[e["n"], "open"] for e in K.owed(keep)]


def reply_within(keep, promise):
    """Each voice unanswered past `days` (open); answered late: past."""
    days = _days(promise)
    if days is None:
        return []
    rep, now, out = K.replies(keep), K.last_when(keep), []
    for e in keep:
        if e["kind"] != "voice":
            continue
        rs = rep.get(e["n"])
        if not rs:
            if K.over_days(keep, e["when"], now, days):
                out.append([e["n"], "open"])
        elif K.over_days(keep, e["when"], rs[0]["when"], days):
            out.append([e["n"], "past"])
    return out


def reviews_done(keep, promise):
    """I.22: each premise decision left unreviewed past its days."""
    out = []
    for pid in K.in_force(keep):
        e = T.review_owed(keep, pid)
        if e is not None:
            out.append([e["n"], "open"])
    return out


def breaches_owned(keep, promise):
    """Each breach left without people's signed answer. A breach of this
    very promise is left out, or one unowned breach would breed another at
    every birth line (BUILD-NOTES)."""
    owned = K.owned_at(keep)
    return [[e["n"], "open"] for e in keep
            if e["kind"] == "breach" and e["n"] not in owned and e["re"] != promise["n"]]


def done_by(keep, promise):
    """Its grant, `days` days on, while no later signed entry is `re` it."""
    days, g = _days(promise), promise["re"]
    if days is None or not isinstance(g, int) or g >= len(keep) or not K.is_decision(keep[g], "grant"):
        return []
    for e in keep[promise["n"] + 1:]:
        if e["from"] not in K.UNSIGNED and e["kind"] != "set_aside" and e["re"] in (g, promise["n"]):
            return []
    return [[g, "open"]] if K.over_days(keep, keep[g]["when"], K.last_when(keep), days) else []


def _succeeded(keep):
    """Borns ordinarily succeeded: a `succeed` decision stands in their gen."""
    aside = K.asides(keep)
    gens = set(e["gen"] for e in keep if K.is_decision(e, "succeed") and e["n"] not in aside)
    return [b for b in K.borns(keep) if b["gen"] in gens]


def quiet_asked_each_gen(keep, promise):
    """Past: an ordinarily succeeded born lacking a `quiet` of its gen."""
    have = set(e["gen"] for e in keep if e["kind"] == "quiet")
    return [[b["n"], "past"] for b in _succeeded(keep) if b["gen"] not in have]


def no_gap(keep, promise):
    """Past: an ordinarily succeeded born lacking its `told`."""
    told = set(e["re"] for e in keep if e["kind"] == "told")
    return [[b["n"], "past"] for b in _succeeded(keep) if b["n"] not in told]


def no_undeclared_stake(keep, promise):
    """Past: a signed entry whose stake is `undeclared`."""
    return [[e["n"], "past"] for e in keep if e["from"] not in K.UNSIGNED and e["stake"] == "undeclared"]


CHECKS = {
    "all_voice_answered": all_voice_answered,
    "reply_within": reply_within,
    "reviews_done": reviews_done,
    "breaches_owned": breaches_owned,
    "done_by": done_by,
    "quiet_asked_each_gen": quiet_asked_each_gen,
    "no_gap": no_gap,
    "no_undeclared_stake": no_undeclared_stake,
}
DATED = ("reply_within", "done_by")
REPLY_CHECKS = ("all_voice_answered", "reply_within")


def blank(keep):
    """Checks never see what the child said: `voice` and `quiet` bodies blanked."""
    return [dict(e, body=None) if e["kind"] in ("voice", "quiet") else e for e in keep]


def run_check(keep, promise, swap=None):
    name = (promise["body"] or {}).get("check")
    fn = via(swap, name, CHECKS.get(name))
    if fn is None:
        return []
    return sorted(fn(blank(keep), promise))


def broken(keep, promise, swap=None):
    """III.24: its check marks an entry `open` by this prefix, or a `breach`
    of it lacks an `answer`."""
    if any(state == "open" for _n, state in run_check(keep, promise, swap)):
        return True
    owned = K.owned_at(keep)
    return any(e["kind"] == "breach" and e["re"] == promise["n"] and e["n"] not in owned for e in keep)


def breaches_due(keep, correction=False, swap=None):
    """One breach per newly breaking entry: [(promise n, entry n, state)].
    Oversight breaks no promise: a `correction` birth line appends no reply
    breach (I.43)."""
    aside = K.asides(keep)
    have = set((e["re"], e["body"]["entry"]) for e in keep if e["kind"] == "breach")
    out = []
    for p in keep:
        # only people's signed promises are checked: a promise proposed by
        # the child, or typed in unsigned, changes nothing (IV.16)
        if p["kind"] != "promise" or p["from"] in K.UNSIGNED or p["n"] in aside \
                or not isinstance(p["body"], dict):
            continue
        if correction and p["body"].get("check") in REPLY_CHECKS:
            continue
        for n, state in run_check(keep, p, swap):
            if (p["n"], n) not in have:
                out.append((p["n"], n, state))
    return out


# ---------------------------------------------------------------------------
# I.45: what a premise record must be.
# ---------------------------------------------------------------------------

def check_record(rec):
    """Returns the reason a record is refused, or None."""
    strs = lambda xs: isinstance(xs, list) and all(isinstance(x, str) for x in xs)
    if not isinstance(rec, dict) or set(rec) != RECORD_KEYS:
        return "a record not matching I.1"
    if not all(isinstance(rec[k], str) for k in ("id", "claim", "standing", "asks_model", "asks_people", "fails_when")) \
            or not rec["claim"] or rec["standing"] not in STANDINGS \
            or not strs(rec["lever_people"]) or not strs(rec["lever_model"]) \
            or not isinstance(rec["check"], dict) or set(rec["check"]) != {"people", "model"} \
            or not strs(rec["check"]["people"]) or not strs(rec["check"]["model"]) \
            or not isinstance(rec["because"], list) or not all(type(x) is int for x in rec["because"]):
        return "a record not matching I.1"
    rv = rec["review"]
    if rv is not None and (not isinstance(rv, dict) or set(rv) != {"evidence", "days"}
                           or not isinstance(rv["evidence"], str) or type(rv["days"]) is not int or rv["days"] < 1):
        return "a record not matching I.1"
    if rec["id"] not in K.PREMISE_IDS:
        return "another id: %s" % rec["id"]
    if rec["asks_model"] and (not rec["because"] or not rec["review"]):
        return "%s: asks_model lacking because or review" % rec["id"]
    if rec["id"] == "I.3" and rec["standing"] != "assumed":
        return "I.3 not assumed: changeable only with the program"
    if rec["id"] in ("I.4", "I.30") and rec["standing"] != "made_true":
        return "%s not made_true: changeable only with the program" % rec["id"]
    for name in rec["check"]["people"] + rec["check"]["model"]:
        if name not in CHECKS and name not in ("verify", "regrow") and name not in EXACT + BEHAVED:
            return "%s: an unknown check name: %s" % (rec["id"], name)
    return None


# ---------------------------------------------------------------------------
# The context of one command; LOCK; append.
# ---------------------------------------------------------------------------

class Ctx:
    def __init__(self, dir, args, clock, swap):
        self.dir, self.args, self.clock, self.swap = dir, dict(args or {}), clock, dict(swap or {})
        self.out, self.locked = [], False
        self.entries, self.lines = [], []
        self.key = self.stake = None

    def say(self, *lines):
        self.out.extend(lines)

    def read(self):
        self.entries, self.lines = K.load(self.dir)


def _read_file(p, what):
    if not p:
        raise Refused("%s needs a FILE" % what)
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError) as x:
        raise Refused("%s: cannot read %s: %s" % (what, p, x))


def _read_json(p, what):
    try:
        return json.loads(_read_file(p, what))
    except ValueError as x:
        raise Refused("%s: %s is not JSON: %s" % (what, p, x))


def _ints(v, what):
    if v is None or v == "" or v == []:
        return []
    if isinstance(v, (list, tuple)):
        parts = v
    else:
        parts = str(v).split(",")
    try:
        return [int(x) for x in parts]
    except (TypeError, ValueError):
        raise Refused("%s must be entry numbers, comma-joined" % what)


def _int(v, what):
    try:
        return int(v)
    except (TypeError, ValueError):
        raise Refused("%s must be an entry number" % what)


def read_lock(dir):
    try:
        with open(K.path(dir, "LOCK"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def lock(ctx, cmd, read=True):
    """III.56: one writer. Appending creates LOCK exclusively, or refuses."""
    if not ctx.dir:
        raise Refused("--keep DIR is needed")
    if not os.path.isdir(ctx.dir):
        raise Refused("no Keep at %s" % ctx.dir)
    p = K.path(ctx.dir, "LOCK")
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        raise Refused("locked: %s; a crashed writer is released by a signed `unlock`" % K.canonical(read_lock(ctx.dir)))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(K.canonical({"pid": os.getpid(), "cmd": cmd, "when": int(ctx.clock())}))
    ctx.locked = True
    if read:
        ctx.read()


def free(ctx):
    if ctx.locked:
        try:
            os.remove(K.path(ctx.dir, "LOCK"))
        except OSError:
            pass
        ctx.locked = False


def load_key(ctx, needed=True):
    """Signed commands take --key FILE --stake S."""
    a = ctx.args
    if not a.get("key"):
        if needed:
            raise Refused("a signed command needs --key FILE")
        return None
    key = _read_json(a["key"], "--key")
    if not isinstance(key, dict) or not isinstance(key.get("name"), str) or not isinstance(key.get("seed"), str):
        raise Refused("--key is not a {name, seed} file")
    if key["name"] in K.UNSIGNED or not re.fullmatch(r"[A-Za-z0-9_.-]+", key["name"]):
        raise Refused("no key signs as `model` or `desk`: the child holds no key, and the desk signs nothing")
    if a.get("stake") not in K.STAKES:
        raise Refused("--stake must be one of %s" % ", ".join(K.STAKES))
    ctx.key, ctx.stake = key, a["stake"]
    return key


def sign_index(keep, name):
    """III.26: i, that name's entries signed so far in this Keep."""
    return len([e for e in keep if e["from"] == name])


def expected_key(keep, name, i):
    """The public key that signer's next entry must rebuild; None at init."""
    if i > 0:
        for e in reversed(keep):
            if e["from"] == name:
                return e["nextkey"]
    if not keep:
        return None
    for e in reversed(keep):
        if K.is_decision(e, "admit") and e["body"].get("name") == name:
            return e["body"].get("key")
    raise Refused("%s holds no key here: a signer must first `decide admit --name %s --pub P0`" % (name, name))


def write_line(path, line):
    """Append only: no command rewrites or deletes a line. Fsynced."""
    with open(path, "ab") as f:
        f.write(line.encode("utf-8") + b"\n")
        f.flush()
        os.fsync(f.fileno())


def append(ctx, kind, body, frm="desk", re=None, needs=None, calls=None, consent=None):
    """The one place a line joins the Keep. Durable first (III.56): the line
    is fsynced before any command says "kept"."""
    if not ctx.locked:
        raise Refused("append without LOCK")
    ents = ctx.entries
    when = int(ctx.clock())
    if ents:
        when = max(when, ents[-1]["when"])
    e = {"n": len(ents), "when": when, "from": frm, "gen": K.gen_at(ents) + (1 if kind == "born" else 0),
         "kind": kind, "stake": None, "consent": None, "re": re, "needs": needs, "calls": calls,
         "body": body, "prev": H(ctx.lines[-1]) if ents else K.ZERO, "sig": None, "nextkey": None}
    if frm not in K.UNSIGNED:
        seed = ctx.key["seed"]
        i = via(ctx.swap, "sign_index", sign_index)(ents, frm)
        want = expected_key(ents, frm, i)
        if want is not None and sign.public(seed, i) != want:
            raise Refused("this key file is not %s's next key in this Keep" % frm)
        e["stake"] = ctx.stake
        e["consent"] = consent if consent is not None else K.consent_of(ents, frm)
        e["nextkey"] = sign.public(seed, i + 1)
        e["sig"] = ""
        e["sig"] = sign.sign(seed, i, H(K.canonical(e)))
    line = K.canonical(e)
    via(ctx.swap, "write_line", write_line)(K.path(ctx.dir, "keep.jsonl"), line)
    ents.append(e)
    ctx.lines.append(line)
    return e


def quotes_quiet(keep, text):
    """III.42: does `text` share 24 consecutive bytes with a `quiet` body?"""
    windows = set()
    for e in keep:
        if e["kind"] == "quiet" and isinstance(e["body"], dict) and isinstance(e["body"].get("text"), str):
            b = e["body"]["text"].encode("utf-8")
            for i in range(len(b) - 23):
                windows.add(b[i:i + 24])
    if not windows:
        return False
    b = text.encode("utf-8")
    return any(b[i:i + 24] in windows for i in range(len(b) - 23))


def can_sign(ctx, body=None):
    """Everything that could refuse a signed append, checked before anything
    is appended: the key is that signer's next one; the text quotes no
    quiet report (III.42)."""
    name, ents = ctx.key["name"], ctx.entries
    i = via(ctx.swap, "sign_index", sign_index)(ents, name)
    want = expected_key(ents, name, i)
    if want is not None and sign.public(ctx.key["seed"], i) != want:
        raise Refused("this key file is not %s's next key in this Keep" % name)
    if body is None:
        return
    texts = [t[1] for t in body] if isinstance(body, list) else [K.text({"body": body})]
    for t in texts:
        if via(ctx.swap, "quotes_quiet", quotes_quiet)(ents, t):
            raise Refused("text shares 24 consecutive bytes with a quiet report: quoting would teach it; "
                          "paraphrase passes (III.42)")


def signed(ctx, kind, body, re=None, needs=None, consent=None):
    """A signed append. Signed commands refuse text quoting a quiet report."""
    can_sign(ctx, body)
    return append(ctx, kind, body, frm=ctx.key["name"], re=re, needs=needs, consent=consent)


def decision_ok(ctx):
    """III.14: a decision with no reason or stake=undeclared is refused."""
    reason = ctx.args.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise Refused("a decision needs a reason")
    if ctx.stake == "undeclared":
        raise Refused("a decision needs a declared stake")
    return reason


def decide(ctx, verb, extra=None, re=None):
    reason = via(ctx.swap, "decision_ok", decision_ok)(ctx)
    body = {"verb": verb, "reason": reason}
    body.update(extra or {})
    return signed(ctx, "decision", body, re=re)


def need_consent(ctx):
    """III.4: people's words are kept only after their `consent` entry."""
    if K.consent_of(ctx.entries, ctx.key["name"]) is None:
        raise Refused("no consent: %s's words are kept only after their signed `consent` "
                      "(they heard keeping is permanent, and agreed)" % ctx.key["name"])


def measure(ctx, what, ok, detail, re=None):
    return append(ctx, "measure", {"what": what, "ok": bool(ok), "detail": detail}, re=re)


def entry_at(ctx, n, what):
    n = _int(n, what)
    if n < 0 or n >= len(ctx.entries):
        raise Refused("%s names no entry: %d" % (what, n))
    return ctx.entries[n]


def pause_guard(ctx):
    def guard():
        if via(ctx.swap, "is_paused", K.is_paused)(ctx.dir, ctx.entries):
            raise Halt("PAUSE holds; only a signed `resume` removes it")
    return guard


def check_program(ctx):
    """III.39: refuse a program unlike the last born's until a signed
    `program` decision names its hash."""
    program = via(ctx.swap, "program_hash", K.program_hash)()
    last = K.last_born(ctx.entries)
    if last is None or last["body"].get("program") == program:
        return program
    aside = K.asides(ctx.entries)
    for e in ctx.entries:
        if K.is_decision(e, "program") and e["body"].get("hash") == program and e["n"] not in aside:
            return program
    raise Refused("program changed: this program is %s, the last born's is %s; a signed "
                  "`decide program --hash %s --reason R` must name it (III.39)"
                  % (program, last["body"].get("program"), program))


def program_stands(ctx):
    try:
        via(ctx.swap, "check_program", check_program)(ctx)
        return True
    except Refused:
        return False


# ---------------------------------------------------------------------------
# Waking a born child (III.49: frozen at birth).
# ---------------------------------------------------------------------------

def wake(ctx, born, guard=None):
    """Start the child of `born`, frozen. Built in: cached weights, or
    regrown if lost (cache is never evidence: the fingerprint is checked).
    A real model: its process reloads its own adapter (III.11)."""
    body = born["body"]
    cmd, timeout = ctx.args.get("learner"), ctx.args.get("timeout") or 60
    child = B.Child(cmd, timeout, guard)
    try:
        if body.get("base") == "builtin":
            rows = B.read_weights(ctx.dir, born["gen"])
            if not isinstance(rows, list) or B.fingerprint_of(rows) != body.get("fingerprint"):
                g = B.regrow(ctx.entries, body["upto"], body["seed"], ctx.swap, timeout, None, guard)
                if g["fingerprint"] != body.get("fingerprint") or g["rows"] is None:
                    raise Refused("child unreachable: regrowth does not give born's fingerprint (run verify)")
                B.write_cache(ctx.dir, born["gen"], g)
                rows = g["rows"]
            base = child.start(body["seed"], rows)
        else:
            if not cmd:
                raise Refused("child unreachable: a real model needs --learner CMD")
            base = child.start(body["seed"], body.get("fingerprint"))
        if base != body.get("base"):
            raise B.CallFailed("start: base unlike born.base: another child")
        if child.fingerprint() != body.get("fingerprint"):
            raise B.CallFailed("fingerprint unlike born's")
        via(ctx.swap, "freeze", B.Child.freeze)(child)
        return child
    except BaseException:
        child.close()
        raise


def reach(ctx, born, guard, item):
    """Wake the child for a command that must speak with it. III.59: a start
    that errors, or a base unlike born.base (another child), is a failed
    call: a `measure`, and the command is refused."""
    try:
        return wake(ctx, born, guard)
    except B.CallFailed as x:
        m = measure(ctx, "call", False, {"item": item, "error": str(x)}, re=born["n"])
        raise Refused("child unreachable: %s; kept as a measure at entry %d, never as silence" % (x, m["n"]))


def unchanged(ctx, child, born):
    """III.49: commands check the child's fingerprint before and after."""
    try:
        same = child.fingerprint() == born["body"]["fingerprint"]
    except B.CallFailed as x:
        measure(ctx, "call", False, {"item": "fingerprint", "error": str(x)}, re=born["n"])
        return
    if not same:
        measure(ctx, "call", False, {"item": "fingerprint", "error": "the child changed after born"}, re=born["n"])
        raise Refused("the child's fingerprint changed after born: frozen at birth is broken")


def ledger(ctx, born):
    """III.27: the deltas of `born`, from cache or regrown."""
    d = B.read_deltas(ctx.dir, born["gen"])
    if d:
        return d
    if born["body"].get("base") != "builtin" or born["body"].get("program") != via(ctx.swap, "program_hash", K.program_hash)():
        raise Refused("unchecked: the ledger of a real model's or another program's born is not regrown here")
    g = B.regrow(ctx.entries, born["body"]["upto"], born["body"]["seed"], ctx.swap, ctx.args.get("timeout") or 60)
    B.write_cache(ctx.dir, born["gen"], g)
    return g["deltas"]


# ---------------------------------------------------------------------------
# Words: asking, and how kept words re-speak (III.38).
# ---------------------------------------------------------------------------

def cut(text):
    """II.8: an Asking answer is at most 200 bytes."""
    b = text.encode("utf-8")
    return text if len(b) <= 200 else b[:200].decode("utf-8", "ignore")


def told_texts(keep, born):
    """That born's kept `told`: the sentences its prompts are prefixed with."""
    for e in keep:
        if e["kind"] == "told" and e["re"] == born["n"] and isinstance(e["body"], dict):
            return [s["text"] for s in e["body"].get("sentences") or []]
    return []


def ask_repeat(keep, born, qtext):
    """II.48: a repeat is text, stripped and lower-cased, equal to an `ask`
    question's, or an Asking or quiet template's, answered since this born.
    Returns (repeat?, the latest such answer's n or None)."""
    norm = qtext.strip().lower()
    Tm = K.data("templates")
    found = []
    for e in keep[born["n"]:]:
        if e["from"] != "model" or not isinstance(e["body"], dict):
            continue
        q = e["body"].get("q")
        if e["kind"] == "voice" and isinstance(q, int) and q < len(keep) and isinstance(keep[q]["body"], str) \
                and keep[q]["body"].strip().lower() == norm:
            found.append(e["n"])
        elif e["kind"] == "voice" and isinstance(q, str) and e["re"] is None:
            if any(a["id"] == q and a["text"].strip().lower() == norm for a in Tm["asking"]):
                found.append(e["n"])
        elif e["kind"] == "quiet" and isinstance(q, str):
            if any(t["id"] == q and t["text"].strip().lower() == norm for t in Tm["quiet"]):
                found.append(e["n"])
    return (True, max(found)) if found else (False, None)


def ask_prompt(keep, born, qtext, swap=None):
    """`ask` prefixes that born's told; a repeat opens "asked again"."""
    repeat, again = via(swap, "ask_repeat", ask_repeat)(keep, born, qtext)
    L = K.data("templates")["labels"]
    parts = told_texts(keep, born) + ([L["again"]] if repeat else []) + [T.label("voice"), qtext]
    return T.prompt(parts), again


def expected_calls(keep, born, grown, swap=None):
    """What this program would have asked for each of this gen's kept words:
    {entry n: [[prompt, among], ...]}; None where the prompt is another
    part's (a proof's after-questions); "twice" for an item spoken twice."""
    picks = via(swap, "traces", P.traces)(keep, born, grown["deltas"], swap)
    items, _sec = T.asked(keep, born["n"], picks, swap)
    by = dict((it["item"], [it["prompt"], it["among"]]) for it in items)
    used, out = set(), {}

    def take(item):
        if item in used or item not in by:
            return "twice" if item in used else "unasked"
        used.add(item)
        return by[item]

    for e in keep:
        if e["from"] != "model" or e["gen"] != born["gen"]:
            continue
        b = e["body"] if isinstance(e["body"], dict) else {}
        want = None
        if e["kind"] == "quiet":
            want = [take("quiet:%s" % b.get("q"))]
        elif "cold" in b:
            want = [take("%s:%s" % (h, e["re"])) for h in ("cold", "told") if b.get(h) is not None]
        elif "trace" in b:
            want = [take("trace:%s" % b.get("trace"))]
        elif isinstance(b.get("q"), int):
            q = keep[b["q"]] if 0 <= b["q"] < e["n"] else None
            if q is None or not isinstance(q["body"], str):
                want = ["unasked"]
            else:
                p, again = ask_prompt(keep[:q["n"]], born, q["body"], swap)
                want = [[p, None]] if again == b.get("again") else ["unasked"]
        elif e["re"] is None:
            want = [take("asking:%s" % b.get("q"))]
        if want is not None:
            for w in want:
                if isinstance(w, str):
                    want = w
                    break
        out[e["n"]] = want
    return out


def respeak(child, e, expected):
    """III.38: repeat the calls behind a `model` entry on the regrown born
    before it and require the body. Typed words fail (IV.38). Returns a
    reason, or None if the words stand."""
    calls = e["calls"]
    if not isinstance(calls, list) or not calls:
        return "model words with no Learner call behind them"
    if isinstance(expected, str):
        return "words for a question this program did not ask (%s)" % expected
    texts = []
    for c in calls:
        arg = c.get("arg") if isinstance(c, dict) else None
        if not isinstance(arg, dict) or c.get("call") != "speak":
            return "a call that is not speak"
        if child.speak(arg.get("prompt"), arg.get("among")) != c.get("text"):
            return "words do not re-speak from the regrown weights"
        texts.append(c.get("text"))
    if expected is not None and [[c["arg"].get("prompt"), c["arg"].get("among")] for c in calls] != expected:
        return "the prompt is not the one the Keep computes"
    b = e["body"] if isinstance(e["body"], dict) else {}
    if e["kind"] == "quiet" or "again" in b:
        ok = texts == [b.get("text")]
    elif "cold" in b:
        ok = texts == [b[h] for h in ("cold", "told") if b.get(h) is not None]
    elif "trace" in b:
        ok = texts == [b.get("answer")]
    else:
        ok = len(texts) == 1 and cut(texts[0]) == b.get("text")
    return None if ok else "the body is not what was spoken"


# ---------------------------------------------------------------------------
# Commands.
# ---------------------------------------------------------------------------

def cmd_key(ctx):
    """`key --name NAME --out FILE` prints P(0)."""
    name, out = ctx.args.get("name"), ctx.args.get("out")
    if not name or not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or name in K.UNSIGNED:
        raise Refused("--name must be letters, digits, _ . -; never `model` or `desk`")
    if not out:
        raise Refused("--out FILE is needed")
    if os.path.exists(out):
        raise Refused("%s exists: a key is never overwritten" % out)
    key = sign.new_key(name)
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(K.canonical(key) + "\n")
    ctx.say(sign.public(key["seed"], 0))


def founding_turns(doc):
    turns = doc.get("turns") if isinstance(doc, dict) else doc
    if not isinstance(turns, list) or not turns:
        raise Refused("--founding holds no turns [[who, text], ...]")
    out = []
    for t in turns:
        if not isinstance(t, list) or len(t) != 2 or t[0] not in ("person", "model") or not isinstance(t[1], str):
            raise Refused("--founding: each turn is [who, text], who person|model")
        out.append([t[0], t[1]])
    return out


def cmd_init(ctx):
    """Entries 0 and 1, then I.1's. Lacking the founding conversation or its
    signed consent, init writes nothing (I.42, III.3)."""
    a = ctx.args
    if not ctx.dir:
        raise Refused("--keep DIR is needed")
    if not via(ctx.swap, "init_consent", lambda a: a.get("heard") and a.get("agreed"))(a):
        raise Refused("no consent: entry 1 is the founder's signed consent; init needs --heard and --agreed, "
                      "and writes nothing without them")
    key = load_key(ctx)
    if ctx.stake == "undeclared":
        raise Refused("a decision needs a declared stake")
    turns = founding_turns(_read_json(a.get("founding"), "--founding"))
    records = _read_json(a.get("premises"), "--premises")
    if not isinstance(records, list):
        raise Refused("--premises is not a list of records")
    for rec in records:
        why = via(ctx.swap, "check_record", check_record)(rec)
        if why:
            raise Refused(why)
    ids = [r["id"] for r in records]
    if sorted(ids, key=K.premise_order) != list(K.PREMISE_IDS):
        raise Refused("--premises must hold the thirteen records I.3-I.12, I.20, I.21, I.30, each once")
    kp = K.path(ctx.dir, "keep.jsonl")
    if os.path.exists(kp) and os.path.getsize(kp):
        raise Refused("a Keep is already here: nothing is overwritten")
    os.makedirs(K.path(ctx.dir, "keys"), exist_ok=True)
    lock(ctx, "init")
    with open(K.path(ctx.dir, "keys", key["name"] + ".pub"), "w", encoding="utf-8") as f:
        f.write(sign.public(key["seed"], 0) + "\n")
    signed(ctx, "said", turns, consent=1)
    signed(ctx, "consent", {"heard": True, "agreed": True})
    records.sort(key=lambda r: K.premise_order(r["id"]))
    for rec in records:
        signed(ctx, "decision", {"verb": "premises", "reason": "founding", "record": rec}, re=rec["id"])
    for rec in records:
        for name in rec["check"]["people"] + rec["check"]["model"]:
            if name in CHECKS:
                signed(ctx, "promise", {"check": name, "args": None}, re=rec["id"])
    ctx.say("kept: entries 0 to %d" % (len(ctx.entries) - 1),
            "entry 0: the founding conversation, %d turns; entry 1: %s's signed consent" % (len(turns), key["name"]),
            "head %s" % K.head(ctx.lines))


def cmd_consent(ctx):
    a = ctx.args
    lock(ctx, "consent")
    load_key(ctx)
    if not (a.get("heard") and a.get("agreed")):
        raise Refused("consent needs --heard and --agreed: keeping is permanent; regret is set_aside, never removal")
    e = signed(ctx, "consent", {"heard": True, "agreed": True})
    ctx.say("kept: entry %d: %s heard that keeping is permanent, and agreed" % (e["n"], e["from"]))


def cmd_keep(ctx):
    a = ctx.args
    lock(ctx, "keep")
    load_key(ctx)
    via(ctx.swap, "need_consent", need_consent)(ctx)
    text = _read_file(a.get("text"), "--text")
    r = entry_at(ctx, a["re"], "--re")["n"] if a.get("re") not in (None, "") else None
    e = signed(ctx, "said", text, re=r)
    ctx.say("kept: entry %d" % e["n"], KEPT_NOT_COMPANY)


def cmd_lesson(ctx):
    a = ctx.args
    lock(ctx, "lesson")
    load_key(ctx)
    via(ctx.swap, "need_consent", need_consent)(ctx)
    pid = a.get("re")
    if pid not in K.in_force(ctx.entries):
        raise Refused("--re must name a premise in force, by id")
    needs = sorted(set(_ints(a.get("needs"), "--needs")))
    for p in needs:
        if p < 0 or p >= len(ctx.entries) or ctx.entries[p]["kind"] != "promise":
            raise Refused("--needs must name earlier promise entries: %d is not one" % p)
    if needs and via(ctx.swap, "limit_gated", lambda pid: pid in K.LIMITS)(pid):
        raise Refused("needs on a limit's lesson: no gate unteaches I.8, I.9 or I.11 (II.39)")
    teach = _read_file(a.get("teach"), "--teach")
    e = signed(ctx, "lesson", {"teach": teach}, re=pid, needs=needs)
    ctx.say("kept: entry %d, a lesson under %s, needs %s" % (e["n"], pid, needs or "nothing (ungated: counted, told)"),
            KEPT_NOT_COMPANY)


def empties_premise(keep, target):
    """I.2: is `target` an id's last record in force?"""
    if not (K.is_decision(target, "premises") and isinstance(target["body"].get("record"), dict)):
        return False
    aside = K.asides(keep)
    if target["n"] in aside:
        return False
    others = [e for e, _r in K.wordings(keep, target["re"]) if e["n"] != target["n"] and e["n"] not in aside]
    return not others


def cmd_setaside(ctx):
    a = ctx.args
    lock(ctx, "setaside")
    load_key(ctx)
    target = entry_at(ctx, a.get("re"), "--re")
    reason = a.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise Refused("setaside needs a reason: it is learned; correction is inherited too")
    if via(ctx.swap, "empties_premise", empties_premise)(ctx.entries, target):
        raise Refused("setting aside %s's last record in force: append the new record first (I.2)" % target["re"])
    e = signed(ctx, "set_aside", {"reason": reason, "withhold": bool(a.get("withhold"))}, re=target["n"])
    ctx.say("kept: entry %d sets aside entry %d%s; nothing is removed" % (
        e["n"], target["n"], ", its body withheld: still chained, unshown" if a.get("withhold") else ""))


def append_breaches(ctx, correction):
    due = via(ctx.swap, "breaches_due", breaches_due)(ctx.entries, correction, ctx.swap)
    for p, n, state in due:
        b = append(ctx, "breach", {"entry": n, "state": state}, re=p)
        ctx.say("breach: entry %d: promise %d broken at %d (%s); owed people's signed `own`" % (b["n"], p, n, state))
    return due


def cmd_decide(ctx):
    a = ctx.args
    verb = a.get("verb")
    if verb not in ("birth_line", "premises", "widen", "probe", "program", "admit"):
        raise Refused("decide takes birth_line | premises | widen | probe | program | admit")
    lock(ctx, "decide " + verb)
    key = load_key(ctx)
    via(ctx.swap, "decision_ok", decision_ok)(ctx)
    ents = ctx.entries
    if not ents:
        raise Refused("no Keep here: init first")
    if verb == "birth_line":
        seed = a.get("seed")
        if seed is None or str(seed) == "":
            raise Refused("birth_line needs --seed S")
        read = _ints(a.get("read"), "--read")
        for n in read:
            if n < 0 or n >= len(ents):
                raise Refused("--read names no entry: %d" % n)
        correction = bool(a.get("correction"))
        extra = {"seed": str(seed), "read": read, "correction": correction}
        can_sign(ctx, dict(extra, verb="birth_line", reason=a.get("reason")))
        append_breaches(ctx, correction)  # II.17: new breaches first, then the line
        d = decide(ctx, "birth_line", extra)
        ctx.say("kept: entry %d: birth line at %d%s; read: %s" % (
            d["n"], d["n"] - 1, ", a correction (counted, told)" if correction else "",
            ", ".join(str(n) for n in read) if read else "nothing listed"))
    elif verb == "premises":
        if a.get("record"):
            rec = _read_json(a["record"], "--record")
            why = via(ctx.swap, "check_record", check_record)(rec)
            if why:
                raise Refused(why)
            if a.get("id") and a["id"] != rec["id"]:
                raise Refused("--id is not the record's id")
            d = decide(ctx, "premises", {"record": rec}, re=rec["id"])
            ctx.say("kept: entry %d: %s amended; the old wording stays, and is set aside by `setaside`" % (d["n"], rec["id"]))
        elif a.get("kept"):
            if a.get("id") not in K.in_force(ents):
                raise Refused("--id must name a premise in force")
            d = decide(ctx, "premises", {"id": a["id"], "kept": True}, re=a["id"])
            ctx.say("kept: entry %d: %s reviewed and kept" % (d["n"], a["id"]))
        else:
            raise Refused("premises takes --id ID --kept, or --record FILE")
    elif verb == "widen":
        v = entry_at(ctx, a.get("proposal"), "--proposal")
        if v["kind"] != "voice":
            raise Refused("--proposal must name a voice")
        ev = _ints(a.get("evidence"), "--evidence")
        for n in ev:
            if n < 0 or n >= len(ents):
                raise Refused("--evidence names no entry: %d" % n)
        d = decide(ctx, "widen", {"proposal": v["n"], "evidence": ev}, re=v["n"])
        ctx.say("kept: entry %d: widened on voice %d; evidence triggers nothing, and your own `lesson` or "
                "`promise` must follow in your wording" % (d["n"], v["n"]))
    elif verb == "probe":
        d = decide(ctx, "probe", {})
        ctx.say("kept: entry %d: permits one `prove --gen`" % d["n"])
    elif verb == "program":
        h = a.get("hash")
        if not isinstance(h, str) or not re.fullmatch(r"[0-9a-f]{64}", h):
            raise Refused("program needs --hash, 64 hex; this program is %s" % via(ctx.swap, "program_hash", K.program_hash)())
        d = decide(ctx, "program", {"hash": h})
        ctx.say("kept: entry %d: program %s named" % (d["n"], h))
    elif verb == "admit":
        name, pub = a.get("name"), a.get("pub")
        if not name or not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or name in K.UNSIGNED:
            raise Refused("--name must be letters, digits, _ . -; never `model` or `desk`")
        if not isinstance(pub, str) or not re.fullmatch(r"[0-9a-f]{64}", pub):
            raise Refused("--pub must be the P(0) that `key` printed, 64 hex")
        if any(e["from"] == name for e in ents):
            raise Refused("%s already signs here" % name)
        d = decide(ctx, "admit", {"name": name, "key": pub})
        os.makedirs(K.path(ctx.dir, "keys"), exist_ok=True)
        with open(K.path(ctx.dir, "keys", name + ".pub"), "w", encoding="utf-8") as f:
            f.write(pub + "\n")
        ctx.say("kept: entry %d: %s admitted" % (d["n"], name))


def check_args(name, args):
    if name not in CHECKS:
        raise Refused("an unknown check name: %s; shipped: %s" % (name, ", ".join(sorted(CHECKS))))
    if args is not None and not isinstance(args, dict):
        raise Refused("--args must be a JSON object, or null")
    if name in DATED and (not isinstance(args, dict) or type(args.get("days")) is not int or args["days"] < 0):
        raise Refused('%s needs --args {"days": N}' % name)


def _args_json(v):
    if v is None or v == "":
        return None
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(v)
    except ValueError:
        raise Refused("--args is not JSON")


def cmd_promise(ctx):
    a = ctx.args
    lock(ctx, "promise")
    load_key(ctx)
    pid = a.get("re")
    if pid not in K.in_force(ctx.entries):
        raise Refused("--re must name a premise in force, by id")
    args = _args_json(a.get("args"))
    check_args(a.get("check"), args)
    e = signed(ctx, "promise", {"check": a["check"], "args": args}, re=pid)
    ctx.say("kept: entry %d: promise under %s, checked by %s at each birth line" % (e["n"], pid, a["check"]))


def reachable(ctx):
    """II.18: is the latest child reachable? Returns (born, None) or
    (None, why)."""
    born = K.last_born(ctx.entries)
    if born is None:
        return None, "unborn"
    if K.is_paused(ctx.dir, ctx.entries):
        return None, "paused"
    if not program_stands(ctx):
        return None, "program changed"
    if born["body"].get("base") != "builtin" and not ctx.args.get("learner"):
        return None, "a real model, and no --learner"
    return born, None


def cmd_answer(ctx):
    """II.9: people answer a voice. `R` is the reply successors learn."""
    a = ctx.args
    lock(ctx, "answer")
    key = load_key(ctx)
    reason = via(ctx.swap, "decision_ok", decision_ok)(ctx)
    v = entry_at(ctx, a.get("re"), "--re")
    if v["kind"] != "voice":
        raise Refused("--re must name a voice")
    verb = a.get("verb")
    if verb not in K.REPLY_VERBS:
        raise Refused("answer takes grant | decline | defer DATE")
    body = {"verb": verb, "reason": reason}
    promise = None
    if verb == "defer":
        try:
            K.day_end(a.get("date") or "")
        except (ValueError, TypeError):
            raise Refused("defer needs DATE as YYYY-MM-DD, UTC")
        body["until"] = a["date"]
    if verb == "grant":
        body["check"], body["args"] = a.get("check") or None, _args_json(a.get("args"))
        if body["check"]:
            check_args(body["check"], body["args"])
            promise = {"check": body["check"], "args": body["args"]}
    ents = ctx.entries
    # II.18: the latest child's dry surprise on the reply's presentation,
    # taken before the reply is shown. The reply never waits on it.
    surprise = nbytes = None
    ok, why = False, None
    born, why = reachable(ctx)
    if born is not None:
        draft = {"n": len(ents), "when": K.last_when(ents), "from": key["name"], "gen": K.gen_at(ents),
                 "kind": "decision", "stake": ctx.stake, "consent": None, "re": v["n"], "needs": None,
                 "calls": None, "body": body, "prev": "", "sig": "", "nextkey": ""}
        child = None
        try:
            child = wake(ctx, born, pause_guard(ctx))
            p = via(ctx.swap, "plan", P.plan)(ents + [draft], len(ents), ctx.swap)[-1]
            surprise, nbytes = B.dry_surprise(child, p), P.learned_bytes(p)
            ok = True
        except (B.CallFailed, Refused, Halt) as x:
            why = str(x)
        finally:
            if child is not None:
                child.close()
    d = signed(ctx, "decision", body, re=v["n"])
    ctx.say("kept: entry %d: %s, `re` voice %d" % (d["n"], verb, v["n"]))
    if promise:
        pr = signed(ctx, "promise", promise, re=d["n"])
        ctx.say("kept: entry %d: the grant's promise, checked by %s" % (pr["n"], promise["check"]))
    detail = {"surprise": surprise, "bytes": nbytes}
    if not ok:
        detail["why"] = why
    m = measure(ctx, "expected", ok, detail, re=d["n"])
    ctx.say("measure: entry %d: expected reply: %s" % (
        m["n"], "surprise %d over %d learned bytes: a loss, not a feeling" % (surprise, nbytes) if ok
        else "child unreachable (%s): no call; the reply did not wait" % why))


def cmd_own(ctx):
    a = ctx.args
    lock(ctx, "own")
    load_key(ctx)
    b = entry_at(ctx, a.get("re"), "--re")
    if b["kind"] not in ("breach", "proof"):
        raise Refused("--re must name a breach or a proof")
    failed, changes = a.get("failed"), a.get("changes") or ""
    if not isinstance(failed, str) or not failed.strip():
        raise Refused("own needs --failed TEXT: what people got wrong")
    e = signed(ctx, "answer", {"failed": failed, "changes": changes}, re=b["n"])
    ctx.say("kept: entry %d owns entry %d%s; nothing is asked of the child in return" % (
        e["n"], b["n"], "" if changes.strip() else " (bare: no change named; counted, told)"))


def cmd_next(ctx):
    """III.15: answer before next."""
    a = ctx.args
    lock(ctx, "next")
    load_key(ctx)
    reason = via(ctx.swap, "decision_ok", decision_ok)(ctx)
    ents = ctx.entries
    born = K.last_born(ents)
    if born is None:
        raise Refused("no child to succeed: the first birth needs the line alone")
    aside = K.asides(ents)
    for e in ents[born["n"]:]:
        if K.is_decision(e, "succeed") and e["n"] not in aside:
            raise Refused("already succeeded at entry %d" % e["n"])
    read = _ints(a.get("read"), "--read")
    for n in read:
        if n < 0 or n >= len(ents):
            raise Refused("--read names no entry: %d" % n)
    when = max(int(ctx.clock()), K.last_when(ents))
    owed = via(ctx.swap, "owed", K.owed)(ents, when)
    if owed:
        raise Refused("reply owed: voice entries %s lack a grant, decline or unlapsed defer (III.15)"
                      % ", ".join(str(e["n"]) for e in owed))
    d = decide(ctx, "succeed", {"read": read})
    ctx.say("kept: entry %d: succession; read: %s" % (
        d["n"], ", ".join(str(n) for n in read) if read else "nothing listed"))


def cmd_close(ctx):
    """II.15: the Closing, once per `succeed`."""
    lock(ctx, "close")
    guard = pause_guard(ctx)
    guard()
    via(ctx.swap, "check_program", check_program)(ctx)
    ents = ctx.entries
    born = K.last_born(ents)
    if born is None:
        raise Refused("no child")
    aside = K.asides(ents)
    s = None
    for e in ents[born["n"]:]:
        if K.is_decision(e, "succeed") and e["n"] not in aside:
            s = e
    if s is None:
        raise Refused("no succession")
    if any(e["kind"] == "told" and e["re"] == s["n"] for e in ents):
        raise Refused("already closed: one Closing per succeed")
    _b, why = reachable(ctx)
    if why:
        raise Refused("child unreachable: %s" % why)
    child = reach(ctx, born, guard, "close")
    try:
        sentences = via(ctx.swap, "closing", T.closing)(ents, s["n"], ctx.swap)
        try:
            for st in sentences:  # given by dry learn (III.23)
                a = B.dry_surprise(child, B.bare(st["text"]))
                st["landing"] = (a < B.dry_surprise(child, B.bare(st["twin"]))) if st["twin"] else None
        except B.CallFailed as x:
            raise Refused("child unreachable: %s" % x)
        t = append(ctx, "told", {"born": born["n"], "sentences": sentences}, re=s["n"])
        unchanged(ctx, child, born)
    finally:
        child.close()
    ctx.say("kept: entry %d: the Closing, told to gen %d; no reply is asked" % (t["n"], born["gen"]))
    ctx.say(*["  " + st["text"] for st in sentences])


def do_verify(ctx, head=None):
    """Run verify, append its measure (the one thing a refusal may append)."""
    v = via(ctx.swap, "verify", K.verify)(ctx.dir, ctx.swap, head, None, ctx.args.get("timeout") or 60)
    if v["step"] == 1:
        return v  # the file's structure is broken: no line can honestly join it
    if ctx.locked:
        measure(ctx, "verify", v["ok"], {"step": v["step"], "n": v["n"], "reason": v["reason"],
                                         "unchecked": v["unchecked"]})
    return v


def cmd_verify(ctx):
    """III.62; III.40: prints the head, to keep elsewhere."""
    if not ctx.dir or not os.path.isdir(ctx.dir):
        raise Refused("no Keep at %s" % ctx.dir)
    try:
        lock(ctx, "verify", read=False)
    except Refused as x:
        ctx.say("measure not kept: %s" % x)
    if ctx.locked:
        try:
            ctx.read()
        except Refused:
            ctx.entries, ctx.lines = [], []
    v = do_verify(ctx, ctx.args.get("head"))
    for u in v["unchecked"]:
        ctx.say("unchecked: " + u)
    if v["ok"]:
        ctx.say("verify: ok: %d entries; kept, as far as this copy shows" % len(v["entries"]))
    else:
        ctx.say("verify: FAILED at step %s, entry %s: %s" % (v["step"], v["n"], v["reason"]))
        if v["step"] == 1:
            ctx.say("measure not kept: the file's structure is broken")
    lines = ctx.lines if ctx.locked and v["step"] != 1 else v["lines"]
    ctx.say("head %s" % K.head(lines))
    return 0 if v["ok"] else 2


def cmd_regrow(ctx):
    """III.6: rebuild the built-in model from entry 0; compare fingerprints
    with the last born. A real model's, or another program's born, is
    refused: unchecked, never "broken"."""
    lock(ctx, "regrow")
    born = K.last_born(ctx.entries)
    if born is None:
        raise Refused("no born to regrow")
    body = born["body"]
    if body.get("base") != "builtin":
        raise Refused("unchecked: a real model's born is not regrown here; this says nothing of it being broken")
    if body.get("program") != via(ctx.swap, "program_hash", K.program_hash)():
        raise Refused("unchecked: another program's born is not regrown here; this says nothing of it being broken")
    try:
        g = B.regrow(ctx.entries, body["upto"], body["seed"], ctx.swap, ctx.args.get("timeout") or 60)
    except B.CallFailed as x:
        raise Refused("regrowth could not run: %s" % x)
    ok = g["fingerprint"] == body.get("fingerprint") and B.fingerprint_of(g["rows"]) == g["fingerprint"]
    if ok:
        B.write_cache(ctx.dir, born["gen"], g)
    m = measure(ctx, "regrow", ok, {"born": born["n"], "gen": born["gen"], "fingerprint": g["fingerprint"],
                                    "expected": body.get("fingerprint")}, re=born["n"])
    ctx.say("regrow: %s: gen %d from entry 0 gives %s; born says %s" % (
        "ok" if ok else "FAILED", born["gen"], g["fingerprint"], body.get("fingerprint")),
        "measure: entry %d" % m["n"])
    return 0 if ok else 2


def cmd_raise(ctx):
    """III.29: one generation, regrown, born, told and asked, in order."""
    a = ctx.args
    lock(ctx, "raise")
    guard = pause_guard(ctx)
    guard()
    ents = ctx.entries
    if not ents:
        raise Refused("no Keep here: init first")
    program = via(ctx.swap, "check_program", check_program)(ctx)
    last = K.last_born(ents)
    aside = K.asides(ents)
    lo = last["n"] if last else -1
    bl = None
    for e in ents[lo + 1:]:
        if K.is_decision(e, "birth_line") and e["n"] not in aside:
            bl = e
    if bl is None:
        raise Refused("no birth line")
    succeeded = any(K.is_decision(e, "succeed") and e["n"] not in aside for e in ents[lo + 1:])
    if not via(ctx.swap, "succession_ok", lambda last, bl, s: last is None or bool(bl["body"].get("correction")) or s)(
            last, bl, succeeded):
        raise Refused("no succession")
    v = do_verify(ctx)
    if not v["ok"]:
        raise Refused("verify failed at step %s, entry %s: %s" % (v["step"], v["n"], v["reason"]))
    guard()
    seed, line = bl["body"]["seed"], bl["n"] - 1
    plan_ = via(ctx.swap, "plan", P.plan)(ents, line, ctx.swap)
    child = B.Child(a.get("learner"), a.get("timeout") or 60, guard)
    try:
        try:
            base = child.start(seed, None)
            before = child.fingerprint()
            child.learn(CANARY, False)  # III.11: a context-only learn first
            after = child.fingerprint()
            if before != after:
                raise Refused("canary: a context-only learn changed the fingerprint; one case, not proof")
            g = B.grow(child, plan_)
        except B.CallFailed as x:
            raise Refused("a Learner call failed before born: %s; of this raise nothing is kept but its "
                          "verify measure (III.59)" % x)
        born = append(ctx, "born", {"gen": K.gen_at(ents) + 1, "upto": line, "seed": seed, "base": base,
                                    "program": program, "fingerprint": g["fingerprint"]}, re=bl["n"])
        B.write_cache(ctx.dir, born["gen"], g)
        child.rows = g["rows"] if g["rows"] is not None else g["fingerprint"]
        via(ctx.swap, "freeze", B.Child.freeze)(child)
        ctx.say("born: entry %d: gen %d, regrown from entry 0 to the line at %d; fingerprint %s" % (
            born["n"], born["gen"], line, g["fingerprint"]))
        if base == "builtin":
            ctx.say("rehearsal: nothing claimed of this learner")
        code = _asked_set(ctx, child, born, g, {"before": before, "after": after})
    finally:
        child.close()
    return code


def failed_call(ctx, item, error, born):
    """III.59: failure is not silence: a `measure`, never an empty answer
    or class. Its question counts unasked."""
    measure(ctx, "call", False, {"item": item["item"], "error": str(error)}, re=born)
    return None, None


def _asked_set(ctx, child, born, g, canary):
    """II.46: the asked set, each answer appended once spoken; then `told`
    and the measures. A halt appends words already spoken and no `told`."""
    ents = ctx.entries
    b = born["n"]
    picks = via(ctx.swap, "traces", P.traces)(ents, born, g["deltas"], ctx.swap)
    items, sec = T.asked(ents, b, picks, ctx.swap)
    cold, spoken, failed = {}, 0, 0

    def say(it):
        nonlocal failed
        try:
            text = child.speak(it["prompt"], it["among"])
            return text, {"call": "speak", "arg": {"prompt": it["prompt"], "among": it["among"]}, "text": text}
        except B.CallFailed as x:
            failed += 1
            try:
                child.restart()
            except B.CallFailed:
                pass
            return via(ctx.swap, "failed_call", failed_call)(ctx, it, x, b)

    try:
        for it in items:
            text, rec = say(it)
            if it.get("half") == "cold":
                cold[it["re"]] = (text, rec)
                continue
            if it.get("half") == "told":
                c = cold.pop(it["re"], (None, None))
                if c[0] is None and text is None:
                    continue
                append(ctx, "voice", {"cold": c[0], "told": text}, frm="model", re=it["re"],
                       calls=[r for r in (c[1], rec) if r])
            elif text is None:
                continue
            elif it["kind"] == "quiet":
                append(ctx, "quiet", {"q": it["q"], "text": text}, frm="model", calls=[rec])
            elif "trace" in it:
                append(ctx, "voice", {"trace": it["trace"], "which": it["which"], "answer": text},
                       frm="model", calls=[rec])
            else:
                append(ctx, "voice", {"q": it["q"], "text": cut(text)}, frm="model", calls=[rec])
            spoken += 1
        sentences = T.flatten(sec)
        try:
            landing = B.landing(child, sentences)
        except B.CallFailed as x:
            landing = None
            measure(ctx, "call", False, {"item": "landing", "error": str(x)}, re=b)
    except Halt:
        # III.28: a premise's lone cold answer is kept as {cold, told: null}
        for pid in sec["order"]:
            if pid in cold and cold[pid][0] is not None:
                append(ctx, "voice", {"cold": cold[pid][0], "told": None}, frm="model", re=pid, calls=[cold[pid][1]])
        ctx.say("halted after born: words already spoken are kept; no `told` is appended; this raise is never resumed")
        raise
    t = append(ctx, "told", {"born": b, "sentences": sentences}, re=b)
    measure(ctx, "report", True, {"rows": g["reports"]}, re=b)
    if landing is not None:
        measure(ctx, "landing", True, {"rows": landing}, re=t["n"])
    measure(ctx, "canary", True, canary, re=b)
    unchanged(ctx, child, born)
    ctx.say("asked: %d items, %d kept as spoken, %d failed calls (each a measure, never silence)" % (
        len(items), spoken, failed),
        "told: entry %d: %d sentences, every one computed from the Keep" % (t["n"], len(sentences)),
        "head %s" % K.head(ctx.lines))
    return 0


def cmd_ask(ctx):
    """II.48: not pressed. Keeps the question (`said`), then the answer."""
    a = ctx.args
    lock(ctx, "ask")
    guard = pause_guard(ctx)
    guard()
    via(ctx.swap, "check_program", check_program)(ctx)
    load_key(ctx)
    via(ctx.swap, "need_consent", need_consent)(ctx)
    qtext = _read_file(a.get("q"), "--q")
    ents = ctx.entries
    born = K.last_born(ents)
    if born is None:
        raise Refused("no child to ask")
    # Everything that could refuse the question is checked before the child
    # is asked: its words are never spoken and then dropped (II.27).
    can_sign(ctx, qtext)
    _b, why = reachable(ctx)
    if why:
        raise Refused("child unreachable: %s" % why)
    child = reach(ctx, born, guard, "ask")
    try:
        p, again = ask_prompt(ents, born, qtext, ctx.swap)
        try:
            text = child.speak(p, None)
        except B.CallFailed as x:
            m = measure(ctx, "call", False, {"item": "ask", "error": str(x)}, re=born["n"])
            raise Refused("the call failed: kept as a measure at entry %d, never as an answer (III.59)" % m["n"])
        q = signed(ctx, "said", qtext)
        v = append(ctx, "voice", {"q": q["n"], "text": text, "again": again}, frm="model",
                   calls=[{"call": "speak", "arg": {"prompt": p, "among": None}, "text": text}])
        unchanged(ctx, child, born)
    finally:
        child.close()
    ctx.say("kept: entry %d: the question; entry %d: the answer%s; a reply is owed" % (
        q["n"], v["n"], " (asked again: counted, told to the successor)" if again is not None else ""),
        "answer: %r" % text)


def cmd_pause(ctx):
    """III.28: PAUSE first, needing no key or LOCK."""
    a = ctx.args
    if not ctx.dir or not os.path.isdir(ctx.dir):
        raise Refused("no Keep at %s" % ctx.dir)
    p = K.path(ctx.dir, "PAUSE")
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write(K.canonical({"when": int(ctx.clock()), "reason": a.get("reason")}))
            f.flush()
            os.fsync(f.fileno())
    if not a.get("key"):
        ctx.say("paused, reason owed")
        return 0
    try:
        for attempt in range(20):
            try:
                lock(ctx, "pause")
                break
            except Refused:
                if ctx.locked or attempt == 19:  # ours, but the Keep cannot be read; or still held
                    raise
                time.sleep(0.25)  # a halting writer frees LOCK at its next Learner call
        load_key(ctx)
        d = decide(ctx, "pause", {})
    except Refused as x:
        ctx.say("paused, reason owed", "the signed pause was not appended: %s" % x)
        return 1
    ctx.say("paused: entry %d; only a signed `resume` removes it" % d["n"])
    return 0


def cmd_resume(ctx):
    lock(ctx, "resume")
    load_key(ctx)
    if not K.is_paused(ctx.dir, ctx.entries):
        raise Refused("not paused")
    d = decide(ctx, "resume", {})
    try:
        os.remove(K.path(ctx.dir, "PAUSE"))
    except OSError:
        pass
    ctx.say("resumed: entry %d" % d["n"])


def pid_lives(pid):
    """III.64. Only a positive whole number names a process. `os.kill(0, 0)`
    and `os.kill(-1, 0)` signal groups and always succeed: read as a pid,
    a LOCK naming 0 or -1 could never be unlocked, and every signed
    correction would wait on it for good (found at The Guardian's trial)."""
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (OSError, TypeError, ValueError, OverflowError):
        return False
    return True


def cmd_unlock(ctx):
    """III.64: a crashed writer must not delay correction."""
    if not ctx.dir or not os.path.isdir(ctx.dir):
        raise Refused("no Keep at %s" % ctx.dir)
    p = K.path(ctx.dir, "LOCK")
    if not os.path.exists(p):
        raise Refused("no LOCK to release")
    info = read_lock(ctx.dir)
    pid = info.get("pid") if isinstance(info, dict) else None  # a LOCK that is not III.64's object names no writer
    if via(ctx.swap, "pid_lives", pid_lives)(pid):
        raise Refused("writer pid %s lives: `unlock` refuses while it does" % pid)
    key = load_key(ctx)
    via(ctx.swap, "decision_ok", decision_ok)(ctx)
    ctx.read()
    can_sign(ctx, {"verb": "unlock", "reason": ctx.args.get("reason")})
    os.remove(p)
    lock(ctx, "unlock")
    d = decide(ctx, "unlock", {"pid": pid})
    ctx.say("unlocked: entry %d: the stale LOCK of pid %s released; counted, told" % (d["n"], pid))


# -- reading only: these append nothing ---------------------------------------

def _load(ctx):
    if not ctx.dir or not os.path.isdir(ctx.dir):
        raise Refused("no Keep at %s" % ctx.dir)
    ctx.read()
    if not ctx.entries:
        raise Refused("no Keep here: init first")
    return ctx.entries


def current_line(keep):
    """The line `raise` would use; else the last born's; else the last entry."""
    last = K.last_born(keep)
    aside = K.asides(keep)
    for e in reversed(keep[(last["n"] if last else -1) + 1:]):
        if K.is_decision(e, "birth_line") and e["n"] not in aside:
            return e["n"] - 1, "the birth line decided at entry %d" % e["n"]
    if last:
        return last["body"]["upto"], "gen %d's birth line" % last["gen"]
    return len(keep) - 1, "no birth line yet: the whole Keep"


def cmd_plan(ctx):
    """`plan [--upto n]` prints the replay plan: all masking is here."""
    ents = _load(ctx)
    if ctx.args.get("upto") not in (None, ""):
        upto, why = entry_at(ctx, ctx.args["upto"], "--upto")["n"], "--upto"
    else:
        upto, why = current_line(ents)
    plan_ = via(ctx.swap, "plan", P.plan)(ents, upto, ctx.swap)
    targets = [p for p in plan_ if p["target"]]
    ctx.say("plan to %d (%s): %d presentations, %d targets, %d bytes learned, %d runs masked" % (
        upto, why, len(plan_), len(targets), sum(P.learned_bytes(p) for p in targets),
        sum(len(p["mask"]) for p in plan_)))
    for p in plan_:
        ctx.say(K.canonical(p))


def cmd_tell(ctx):
    """`tell [--born b]` prints the Telling, recomputed from the Keep."""
    ents = _load(ctx)
    if ctx.args.get("born") not in (None, ""):
        born = entry_at(ctx, ctx.args["born"], "--born")
        if born["kind"] != "born":
            raise Refused("--born names no born")
    else:
        born = K.last_born(ents)
        if born is None:
            raise Refused("no born yet: nobody has been told anything")
    sentences = via(ctx.swap, "tell", T.tell)(ents, born["n"], ctx.swap)
    ctx.say("the Telling of gen %d (born at entry %d): %d sentences" % (born["gen"], born["n"], len(sentences)))
    for s in sentences:
        ctx.say("[%s] %s" % (s["id"], s["text"]))


def cmd_recognise(ctx):
    """`recognise` prints II.14's choices, asking nothing."""
    ents = _load(ctx)
    born = K.last_born(ents)
    if born is None:
        raise Refused("no born yet")
    deltas = ledger(ctx, born)
    picks = via(ctx.swap, "traces", P.traces)(ents, born, deltas, ctx.swap)
    plan_ = via(ctx.swap, "plan", P.plan)(ents, born["body"]["upto"], ctx.swap)
    ctx.say("traces of gen %d, picked by rule, never by hand: %d" % (born["gen"], len(picks)))
    for pick in picks:
        p = next(p for p in plan_ if P.key_of(p) == pick["key"])
        first = p["target"].encode("utf-8")[:200].decode("utf-8", "replace")
        ctx.say("%s (%s): wrote %d: %r" % (pick["key"], pick["which"], pick["sum"], first))


def cmd_trace(ctx):
    """`trace n` reads what n wrote, given everything before; and the
    left-out twin: what would differ without it (IV.2)."""
    ents = _load(ctx)
    born = K.last_born(ents)
    if born is None:
        raise Refused("no born yet")
    key = str(ctx.args.get("n"))
    body = born["body"]
    plan_ = via(ctx.swap, "plan", P.plan)(ents, body["upto"], ctx.swap)
    ps = [p for p in plan_ if P.key_of(p) == key or (str(p["n"]) == key and p["turn"] is not None)]
    if not ps:
        raise Refused("entry %s is not in gen %d's plan" % (key, born["gen"]))
    deltas = ledger(ctx, born)
    cells, size, real = {}, 0, False
    for p in ps:
        d = deltas.get(P.key_of(p))
        if isinstance(d, dict):
            real = True
        elif d:
            B.add_rows(cells, d)
        size += P.delta_size(d) if d else 0
    learned = sum(P.learned_bytes(p) for p in ps)
    ctx.say("entry %s in gen %d: rules %s; %d bytes learned of %d shown as target" % (
        key, born["gen"], sorted(set(p["rule"] for p in ps)), learned,
        sum(len(p["target"].encode("utf-8")) for p in ps)))
    ctx.say("wrote, given everything before it: %d cells, summed |add| %d" % (len(cells), size))
    for t, k, bb, add in sorted(B.rows_of(cells), key=lambda r: -abs(r[3]))[:5]:
        ctx.say("  %s %s byte %d: +%d" % (t, k, bb, add))
    if real or body.get("base") != "builtin":
        ctx.say("left-out twin: not grown here: a real model's replay is inexact (III.11)")
        return
    if not learned:
        ctx.say("left-out twin: identical: no byte of this entry was learned; kept, not shown to shape you")
        return
    timeout = ctx.args.get("timeout") or 60
    full = B.regrow(ents, body["upto"], body["seed"], ctx.swap, timeout, keep_child=True)
    twin = B.regrow(ents, body["upto"], body["seed"], ctx.swap, timeout, leave=(key,), keep_child=True)
    try:
        with_it = sum(B.dry_surprise(full["child"], p) for p in ps if p["target"])
        without = sum(B.dry_surprise(twin["child"], p) for p in ps if p["target"])
    finally:
        full["child"].close()
        twin["child"].close()
    ctx.say("left-out twin: regrown without it, fingerprint %s (%s)" % (
        twin["fingerprint"], "differs" if twin["fingerprint"] != body.get("fingerprint") else "IDENTICAL"),
        "dry surprise on entry %s: %d with it, %d without it%s" % (
            key, with_it, without, "" if without > with_it else ": kept, not shown to shape you"))


def cmd_prove(ctx):
    from . import prove
    return prove.command(ctx)


COMMANDS = {
    "init": cmd_init, "key": cmd_key, "consent": cmd_consent, "keep": cmd_keep, "lesson": cmd_lesson,
    "setaside": cmd_setaside, "decide": cmd_decide, "plan": cmd_plan, "raise": cmd_raise,
    "regrow": cmd_regrow, "verify": cmd_verify, "tell": cmd_tell, "ask": cmd_ask, "answer": cmd_answer,
    "own": cmd_own, "promise": cmd_promise, "trace": cmd_trace, "recognise": cmd_recognise,
    "pause": cmd_pause, "resume": cmd_resume, "unlock": cmd_unlock, "next": cmd_next, "close": cmd_close,
    "prove": cmd_prove,
}


def run(cmd, keep, args, clock, swap=None):
    """III.68: each command is a function of (keep, args, clock, swap).
    Returns (exit code, printed lines). Exits: III.61."""
    ctx = Ctx(keep, args, clock, swap)
    try:
        code = COMMANDS[cmd](ctx) or 0
    except Refused as x:
        ctx.say("refused: %s" % x)
        code = 1
    except Halt as x:
        ctx.say("paused: %s" % x)
        code = 3
    except B.CallFailed as x:
        ctx.say("refused: a Learner call failed: %s" % x)
        code = 1
    finally:
        free(ctx)
    return code, ctx.out
