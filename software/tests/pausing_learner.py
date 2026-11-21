"""pausing_learner.py: a test double, not an adapter. The built-in learner,
except that after its Nth `speak` it creates the PAUSE file it is pointed at
(as a person pausing mid-raise would). Usage: LEARNER.py PAUSE_PATH N"""
import importlib.util
import json
import sys

spec = importlib.util.spec_from_file_location("builtin_learner", sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
model, spoken = m.BuiltIn(), 0
for raw in sys.stdin.buffer:
    req = json.loads(raw)
    out = m.answer(model, req)
    if req.get("call") == "speak":
        spoken += 1
        if spoken == int(sys.argv[3]):
            open(sys.argv[2], "w").write("{}")
    sys.stdout.buffer.write(json.dumps(out).encode() + b"\n")
    sys.stdout.buffer.flush()
