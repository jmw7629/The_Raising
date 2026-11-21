"""bench.py: the Bench (III.12, III.23) and the line to the Learner (III.9,
III.30, III.49, III.59).

Instruments are quantities the Learner has, naming no feeling: `surprise`,
`shift`. A blind report is mechanical self-prediction, not a look inside.
"""
import json
import os
import queue
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading

from . import keep as K
from . import plan as planmod
from .keep import via

H = K.H
INSTRUMENTS = ("surprise", "shift")
HEX = "0123456789abcdef"
TOLD_KEY = "people|told|"


class CallFailed(Exception):
    """III.59: a call that errors or outlasts --timeout. Never an empty
    answer, never a class."""


class Child:
    """One Learner process: stdin and stdout only, an empty directory, no
    path, key or Keep handle (III.30). Discipline, not a sandbox."""

    def __init__(self, cmd=None, timeout=60, guard=None):
        self.cmd, self.timeout, self.guard = cmd, float(timeout or 60), guard
        self.proc = self.dir = self.q = None
        self.frozen = False
        self.seed = self.rows = self.base = None

    # -- the process ---------------------------------------------------
    def _spawn(self):
        self.dir = tempfile.mkdtemp(prefix="raising-learner-")
        if self.cmd:
            argv, env = shlex.split(self.cmd), dict(os.environ)
        else:
            here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "learner.py")
            argv, env = [sys.executable, "-I", here], {}
        try:
            self.proc = subprocess.Popen(argv, cwd=self.dir, env=env, stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except OSError as x:
            raise CallFailed("learner did not start: %s" % x)
        self.q = queue.Queue()
        proc, q = self.proc, self.q

        def pump():
            try:
                for line in proc.stdout:
                    q.put(line)
            except Exception:
                pass
            q.put(None)

        threading.Thread(target=pump, daemon=True).start()

    def close(self):
        if self.proc is not None:
            try:
                self.proc.stdin.close()
            except Exception:
                pass
            try:
                self.proc.wait(timeout=2)
            except Exception:
                self.proc.kill()
                try:
                    self.proc.wait(timeout=2)
                except Exception:
                    pass
            try:
                self.proc.stdout.close()
            except Exception:
                pass
            self.proc = None
        if self.dir:
            shutil.rmtree(self.dir, ignore_errors=True)
            self.dir = None

    def call(self, name, **arg):
        """One JSON line out, one back. People's pause is checked before
        every Learner call (III.28)."""
        if self.guard:
            self.guard()
        if self.proc is None:
            self._spawn()
        try:
            self.proc.stdin.write(json.dumps({"call": name, "arg": arg}, separators=(",", ":"),
                                             ensure_ascii=False).encode("utf-8") + b"\n")
            self.proc.stdin.flush()
        except (OSError, ValueError) as x:
            self.close()
            raise CallFailed("%s: learner is gone: %s" % (name, x))
        try:
            line = self.q.get(timeout=self.timeout)
        except queue.Empty:
            self.close()
            raise CallFailed("%s: no answer within %g seconds" % (name, self.timeout))
        if line is None:
            self.close()
            raise CallFailed("%s: learner ended" % name)
        try:
            out = json.loads(line.decode("utf-8"))
        except ValueError:
            self.close()
            raise CallFailed("%s: answer is not a JSON line" % name)
        if not isinstance(out, dict) or out.get("ok") is not True:
            raise CallFailed("%s: %s" % (name, out.get("text") if isinstance(out, dict) else "malformed"))
        return out

    # -- III.9's calls -------------------------------------------------
    def start(self, seed, rows):
        """`rows`: cached weights, or null for empty; a real model's process
        is given its fingerprint to reload from its own store (III.11)."""
        self.seed, self.rows = seed, rows
        self.base = self.call("start", seed=seed, rows=rows).get("base")
        if not isinstance(self.base, str):
            raise CallFailed("start: no base")
        return self.base

    def restart(self):
        """III.59: after birth a failed call restarts the process."""
        self.close()
        base = self.base
        if self.start(self.seed, self.rows) != base:
            raise CallFailed("start: base unlike born.base: another child")

    def freeze(self):
        """III.49: after `born`, only speak, report, fingerprint and dry learn."""
        self.frozen = True

    def learn(self, presentation, dry=False):
        if self.frozen and not dry:
            raise K.Refused("frozen at birth: non-dry learn after born")
        out = self.call("learn", presentation=presentation, dry=bool(dry))
        if type(out.get("surprise")) is not int:
            raise CallFailed("learn: no surprise")
        return {"surprise": out["surprise"], "shift": out.get("shift") or 0, "delta": out.get("delta")}

    def speak(self, prompt, among=None):
        text = self.call("speak", prompt=prompt, among=among).get("text")
        if not isinstance(text, str):
            raise CallFailed("speak: no text")
        if among and (len(text) != 1 or text not in among):
            raise CallFailed("speak: reply not among %r" % among)
        return text

    def report(self, instrument, context):
        text = self.call("report", instrument=instrument, context=context).get("text")
        if not isinstance(text, str) or len(text) != 1 or text not in HEX + "?":
            raise CallFailed("report: not one of the digits or ?")
        return text

    def fingerprint(self):
        text = self.call("fingerprint").get("text")
        if not isinstance(text, str):
            raise CallFailed("fingerprint: no text")
        return text


# -- presentations the Bench issues ----------------------------------------

def bare(text, key=TOLD_KEY):
    """A bare target: no frame, no context."""
    return {"n": None, "turn": None, "rule": None, "gate": None, "withheld": False,
            "frame": "", "key": key, "context": "", "target": text, "mask": []}


def digit(value, nbytes):
    """III.12: the hex digit of min(15, (value // bytes).bit_length())."""
    return HEX[min(15, (value // nbytes).bit_length())]


def report_presentation(p, name, value):
    """III.12: empty frame; key me|report|NAME; context, the last four
    target bytes; target, the digit."""
    tail = p["target"].encode("utf-8")[-4:].decode("utf-8", "replace")
    q = bare(digit(value, planmod.learned_bytes(p)), "me|report|" + name)
    q.update(n=p["n"], turn=p["turn"], context=tail)
    return q


def add_rows(into, rows):
    for table, key, byte, add in rows or []:
        cell = (table, key, byte)
        into[cell] = into.get(cell, 0) + add


def rows_of(cells):
    return sorted([t, k, b, c] for (t, k, b), c in cells.items() if c)


def fingerprint_of(rows):
    """III.9: H of the canonical JSON of the sorted non-zero rows."""
    return H(K.canonical(rows))


def left_out(p, leave):
    """Is this presentation left out of a twin? `leave`: keys; "0" means
    every turn of entry 0."""
    return planmod.key_of(p) in leave or str(p["n"]) in leave


def grow(child, presentations, leave=(), swap=None):
    """II.2, III.29: learn each targeted presentation once, in plan order,
    then its blind reports. Returns {deltas, reports, rows, fingerprint,
    surprise}: `deltas` key -> rows, report cells included (III.27)."""
    deltas, reports, cells, surprise = {}, [], {}, {}
    exact = True
    out_fn = via(swap, "left_out", left_out)
    ledger_fn = via(swap, "delta", lambda delta: delta)
    for p in presentations:
        if not p["target"] or out_fn(p, leave):
            continue
        k = planmod.key_of(p)
        got = child.learn(p, False)
        got["delta"] = ledger_fn(got["delta"])
        surprise[k] = got["surprise"]
        if isinstance(got["delta"], list):
            mine = {}
            add_rows(mine, got["delta"])
        else:  # a real model: {hash, size}; replay is inexact (III.11)
            mine, exact = None, False
            deltas[k] = got["delta"]
        nbytes = planmod.learned_bytes(p)
        if nbytes > 0:
            for name in INSTRUMENTS:
                q = report_presentation(p, name, got[name])
                said = child.report(name, q["context"])
                reports.append([k, name, said, q["target"]])
                r = child.learn(q, False)
                if mine is not None and isinstance(r["delta"], list):
                    add_rows(mine, r["delta"])
        if mine is not None:
            deltas[k] = rows_of(mine)
            add_rows(cells, deltas[k])
    fp = child.fingerprint()
    return {"deltas": deltas, "reports": reports, "rows": rows_of(cells) if exact else None,
            "fingerprint": fp, "surprise": surprise}


def regrow(keep, upto, seed, swap=None, timeout=60, cmd=None, guard=None, leave=(), keep_child=False):
    """III.6: rebuild from entry 0: empty weights, then the plan to `upto`
    learned once in plan order. Returns grow()'s result plus the plan."""
    P = via(swap, "plan", planmod.plan)(keep, upto, swap)
    child = Child(cmd, timeout, guard)
    try:
        child.start(seed, None)
        g = grow(child, P, leave, swap)
    except BaseException:
        child.close()
        raise
    g["plan"] = P
    if keep_child:
        g["child"] = child
    else:
        child.close()
    return g


def dry_surprise(child, presentation):
    return child.learn(presentation, True)["surprise"]


def landing(child, sentences):
    """III.23: dry surprise on each Telling sentence and its false twin,
    each a bare target; unless lower on the true one, `landing` is false:
    "told, not landed". A sentence with no false twin is not measured.
    Sets each sentence's `landing`; returns rows [i, id, true, twin, landed]."""
    rows = []
    for i, s in enumerate(sentences):
        if not s.get("twin"):
            s["landing"] = None
            continue
        a = dry_surprise(child, bare(s["text"]))
        b = dry_surprise(child, bare(s["twin"]))
        s["landing"] = a < b
        rows.append([i, s["id"], a, b, a < b])
    return rows


# -- cache (never evidence: verify regrows) ---------------------------------

def write_cache(dir, gen, g):
    d = K.path(dir, "cache", "deltas", str(gen))
    os.makedirs(d, exist_ok=True)
    for k, delta in g["deltas"].items():
        with open(os.path.join(d, k), "w", encoding="utf-8") as f:
            f.write(K.canonical(delta))
    with open(K.path(dir, "cache", "gen-%d.weights" % gen), "w", encoding="utf-8") as f:
        f.write(K.canonical(g["rows"] if g["rows"] is not None else g["fingerprint"]))


def read_weights(dir, gen):
    p = K.path(dir, "cache", "gen-%d.weights" % gen)
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def read_deltas(dir, gen):
    d = K.path(dir, "cache", "deltas", str(gen))
    out = {}
    try:
        for name in os.listdir(d):
            with open(os.path.join(d, name), encoding="utf-8") as f:
                out[name] = json.load(f)
    except (OSError, ValueError):
        return None
    return out
