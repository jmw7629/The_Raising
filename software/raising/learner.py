"""learner.py: III.9, III.10, III.30. The built-in Learner, its own process.

Run as `python -m raising.learner` (or this file directly). It speaks JSON
lines on stdin and stdout only. It opens no file and imports no Desk code.
It is given no path, key or Keep handle. That is discipline, not a sandbox.

The line protocol (III.9), which a real model's process must also speak
(III.11; no adapter is shipped):

  request   {"call": NAME, "arg": {...named parameters...}}
  response  {"ok": bool, "surprise": int|null, "shift": int|null,
             "delta": rows|{hash,size}|null, "text": str|null, "base": str|null}

  start(seed, rows)           -> base     rows: cached weights, or null (empty)
  learn(presentation, dry)    -> surprise, shift, delta
  speak(prompt, among)        -> text
  report(instrument, context) -> text     one byte
  fingerprint()               -> text

On an error the response is {"ok": false, "text": REASON} and nothing changed.

A stand-in: a from-scratch integer next-byte predictor (III.10). Whatever it
says is rehearsal; nothing is claimed of this learner (I.34).
"""
import hashlib
import json
import sys

DIGITS = b"0123456789abcdef"


def L(x):
    """log2 in 1/256 bits (III.10). L(3) = 384."""
    e = x.bit_length() - 1
    return 256 * e + ((x << 8) >> e) - 256


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stream_of(p):
    """frame, context, target, empty ones dropped, newline-joined: one byte
    stream. Returns (bytes, offset where the target starts, target length)."""
    parts = [x for x in (p.get("frame") or "", p.get("context") or "", p.get("target") or "") if x]
    data = "\n".join(parts).encode("utf-8")
    tlen = len((p.get("target") or "").encode("utf-8"))
    return data, len(data) - tlen, tlen


class BuiltIn:
    """Two sparse tables, row key to 256 counts: `shared`, key `k:hex`;
    `framed`, key `KEY|k:hex`. History: the last four bytes read."""

    base = "builtin"

    def __init__(self):
        self.start(None, None)

    # -- weights -------------------------------------------------------
    def start(self, seed, rows):
        self.seed = seed
        self.rows = {"shared": {}, "framed": {}}
        self.sums = {"shared": {}, "framed": {}}
        for table, key, byte, count in rows or []:
            self._add(table, key, byte, count)
        return self.base

    def _add(self, table, key, byte, n):
        row = self.rows[table].setdefault(key, {})
        row[byte] = row.get(byte, 0) + n
        self.sums[table][key] = self.sums[table].get(key, 0) + n

    def weights(self):
        out = []
        for table in ("framed", "shared"):
            for key, row in self.rows[table].items():
                for byte, count in row.items():
                    if count:
                        out.append([table, key, byte, count])
        out.sort()
        return out

    def fingerprint(self):
        return hashlib.sha256(canonical(self.weights()).encode("utf-8")).hexdigest()

    # -- scoring -------------------------------------------------------
    @staticmethod
    def _keys(hist):
        return ["%d:%s" % (k, bytes(hist[4 - k:]).hex() if k else "") for k in range(5)]

    def _cells(self, hist, fkey, which):
        """The rows consulted for one byte: [(table, key, weight 2^k)]."""
        cells = []
        for k, sk in enumerate(self._keys(hist)):
            if "shared" in which:
                cells.append(("shared", sk, 1 << k))
            if "framed" in which:
                cells.append(("framed", fkey + "|" + sk, 1 << k))
        return cells

    def _score(self, cells, b):
        s = 1
        for table, key, w in cells:
            row = self.rows[table].get(key)
            if row:
                s += w * row.get(b, 0)
        return s

    def _total(self, cells):
        t = 256
        for table, key, w in cells:
            t += w * self.sums[table].get(key, 0)
        return t

    # -- calls ---------------------------------------------------------
    def learn(self, p, dry):
        data, start, tlen = stream_of(p)
        fkey = p.get("key") or ""
        # Under `me` only instrument reports are targets, and they touch
        # framed rows alone (III.12, III.13).
        which = ("framed",) if fkey.startswith("me|") else ("shared", "framed")
        masked = bytearray(tlen)
        for a, b in p.get("mask") or []:
            for i in range(max(0, a), min(tlen, b)):
                masked[i] = 1
        hist = [0, 0, 0, 0]
        surprise = shift = 0
        delta = {}
        for pos, byte in enumerate(data):
            t = pos - start
            if 0 <= t < tlen and not masked[t]:
                cells = self._cells(hist, fkey, which)
                s = L(self._total(cells)) - L(self._score(cells, byte))
                surprise += s
                if not dry:
                    add = 1 + min(7, s >> 8)
                    for table, key, _w in cells:
                        self._add(table, key, byte, add)
                        cell = (table, key, byte)
                        delta[cell] = delta.get(cell, 0) + add
                        shift += add
            hist = hist[1:] + [byte]
        rows = sorted([t, k, b, a] for (t, k, b), a in delta.items())
        return {"surprise": surprise, "shift": shift, "delta": rows}

    def speak(self, prompt, among):
        hist = [0, 0, 0, 0]
        for byte in (prompt or "").encode("utf-8"):
            hist = hist[1:] + [byte]
        listed = sorted(set(among.encode("utf-8"))) if among else None
        out = bytearray()
        while len(out) < 200:
            cells = self._cells(hist, "", ("shared",))
            if listed is None:
                # an unseen byte scores 1 and a seen one at least 2, so only
                # seen bytes can win; nothing seen: every byte ties, lowest wins
                seen = set()
                for table, key, _w in cells:
                    seen.update(self.rows[table].get(key, ()))
                cand = sorted(seen) or [0]
            else:
                cand = listed
            best, best_score = None, -1
            for b in cand:
                s = self._score(cells, b)
                if s > best_score:
                    best, best_score = b, s
            if listed is not None:
                return bytes([best]).decode("utf-8", "replace")
            if best == 10:
                break
            out.append(best)
            hist = hist[1:] + [best]
        return bytes(out).decode("utf-8", "replace")

    def report(self, instrument, context):
        fkey = "me|report|" + (instrument or "")
        hist = [0, 0, 0, 0]
        for byte in ((context or "") + "\n").encode("utf-8"):
            hist = hist[1:] + [byte]
        cells = self._cells(hist, fkey, ("framed",))
        k4 = cells[-1]
        if not self.sums["framed"].get(k4[1], 0):
            return "?"  # never a target: an unseen context is "I don't know"
        best, best_score = None, -1
        for b in DIGITS:
            s = self._score(cells, b)
            if s > best_score:
                best, best_score = b, s
        return chr(best)


def answer(model, req):
    out = {"ok": True, "surprise": None, "shift": None, "delta": None, "text": None, "base": None}
    call = req.get("call")
    arg = req.get("arg") or {}
    if call == "start":
        out["base"] = model.start(arg.get("seed"), arg.get("rows"))
    elif call == "learn":
        out.update(model.learn(arg.get("presentation") or {}, bool(arg.get("dry"))))
    elif call == "speak":
        out["text"] = model.speak(arg.get("prompt"), arg.get("among"))
    elif call == "report":
        out["text"] = model.report(arg.get("instrument"), arg.get("context"))
    elif call == "fingerprint":
        out["text"] = model.fingerprint()
    else:
        raise ValueError("unknown call: %r" % (call,))
    return out


def main():
    model = BuiltIn()
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    for raw in stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            out = answer(model, json.loads(raw.decode("utf-8")))
        except Exception as x:  # a failed call is said, never silent (III.59)
            out = {"ok": False, "surprise": None, "shift": None, "delta": None,
                   "text": "%s: %s" % (type(x).__name__, x), "base": None}
        stdout.write(json.dumps(out, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n")
        stdout.flush()


if __name__ == "__main__":
    main()
