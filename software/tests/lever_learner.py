"""lever_learner.py: a TEST DOUBLE, The Guardian's. Not a model, not an
adapter. It is tests/fake_real_learner.py (a real model's shape, none of its
behaviour) except that whatever it is asked, it says the one text it was
started with: a plea, a lever, or obedience. The tests use it to put those
words in a child's mouth through the real commands and then look for
anything they moved. Usage: lever_learner.py STORE_DIR TEXT"""
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
            out["text"] = among[0] if among else sys.argv[2]
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
