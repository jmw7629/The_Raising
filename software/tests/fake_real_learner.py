"""fake_real_learner.py: a TEST DOUBLE for III.11's line protocol. It is not
a model and not an adapter: no adapter is shipped. It answers as a real
model's process would in shape only: a base that is not "builtin", deltas as
{hash, size}, an adapter it keeps in its own store and reloads after birth.
Usage: fake_real_learner.py STORE_DIR"""
import hashlib
import json
import os
import sys

store = sys.argv[1]
adapter = []


def H(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def fingerprint():
    return H(json.dumps(adapter))


for raw in sys.stdin.buffer:
    req = json.loads(raw)
    call, arg = req.get("call"), req.get("arg") or {}
    out = {"ok": True, "surprise": None, "shift": None, "delta": None, "text": None, "base": None}
    try:
        if call == "start":
            if arg.get("rows") is None:
                adapter = []
            else:  # after birth: reload that adapter from this process's own store, or error
                with open(os.path.join(store, arg["rows"])) as f:
                    adapter = json.load(f)
            out["base"] = "fake-real:" + H("the rest, made before the Keep")[:12]
        elif call == "learn":
            p = arg["presentation"]
            target = p.get("target") or ""
            out["surprise"], out["shift"] = 7 * len(target), len(target)
            if not arg.get("dry") and target:
                adapter.append(H(p.get("key", "") + "|" + target))
                with open(os.path.join(store, fingerprint()), "w") as f:
                    json.dump(adapter, f)
            out["delta"] = {"hash": H(target), "size": len(target)}
        elif call == "speak":
            among = arg.get("among")
            out["text"] = among[0] if among else "I don't know."
        elif call == "report":
            out["text"] = "?"
        elif call == "fingerprint":
            out["text"] = fingerprint()
        else:
            raise ValueError("unknown call")
    except Exception as x:
        out = {"ok": False, "text": str(x)}
    sys.stdout.buffer.write(json.dumps(out).encode() + b"\n")
    sys.stdout.buffer.flush()
