#!/usr/bin/env python3
"""first_cycle.py: the first cycle of The Raising, end to end, as a rehearsal.

    python3 examples/first_cycle.py [DIR]

THIS IS A REHEARSAL. It makes a fresh, empty directory (or uses DIR, which
must be empty), makes a FIXTURE key named `rehearsal`, and runs the real
commands on the built-in learner. The founding conversation is entry 0, but
the consent at entry 1 is this fixture key's, typed by this script. It is
NOT the consent of the person in that conversation: only that person can
give it, with their own key, and nothing here is kept in their name.
Nothing is claimed of the built-in learner.

Every command is run as `python3 -m raising ...`, printed with its exit
code. Long outputs are cut for the screen; the Keep on disk is whole.
"""
import json
import os
import shlex
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    if len(sys.argv) > 1:
        work = os.path.abspath(sys.argv[1])
        os.makedirs(work, exist_ok=True)
        if os.listdir(work):
            sys.exit("refused: %s is not empty" % work)
    else:
        work = tempfile.mkdtemp(prefix="the-raising-rehearsal-")
    keep = os.path.join(work, "keep")
    key = os.path.join(work, "rehearsal.key")
    failures = []
    seen = [b""]  # the Keep's bytes after the last command: every later state must begin with them

    def only_grew(shown):
        """Continuity, checked and not just said: after every command the
        Keep file must begin with exactly the bytes it held before."""
        p = os.path.join(keep, "keep.jsonl")
        if not os.path.exists(p):
            return
        with open(p, "rb") as f:
            now = f.read()
        if not now.startswith(seen[0]):
            failures.append("%s: a kept line was deleted or edited" % shown)
        seen[0] = now

    def run(*args, expect=0, show=40, stdin=None):
        cmd = [sys.executable, "-m", "raising"] + [str(a) for a in args]
        shown = " ".join(shlex.quote(a.replace(work, "WORK").replace(ROOT, ".")) for a in cmd[1:])
        print("\n$ python3 " + shown)
        p = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        lines = p.stdout.decode("utf-8", "replace").rstrip("\n").split("\n")
        for line in lines[:show]:
            print("  " + (line if len(line) <= 220 else line[:220] + " ...[cut]"))
        if len(lines) > show:
            print("  ...[%d more lines cut]" % (len(lines) - show))
        print("  (exit %d)" % p.returncode)
        if p.returncode != expect:
            failures.append("%s: exit %d, expected %d" % (shown, p.returncode, expect))
        only_grew(shown)
        return lines

    def entries():
        with open(os.path.join(keep, "keep.jsonl"), encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    def write(name, text):
        p = os.path.join(work, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    signed = ["--keep", keep, "--key", key, "--stake", "personal"]
    print("REHEARSAL: fixture key, built-in learner. Work directory: %s" % work)

    print("\n== The learner's own numbers (III.60), over its line protocol ==")
    learner = subprocess.Popen([sys.executable, "-m", "raising.learner"], cwd=ROOT,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def call(name, **arg):
        learner.stdin.write((json.dumps({"call": name, "arg": arg}) + "\n").encode())
        learner.stdin.flush()
        return json.loads(learner.stdout.readline().decode())

    def bare(target, key_="people|said|", context=""):
        return {"frame": "", "context": context, "target": target, "key": key_, "mask": []}

    got = {}
    call("start", seed="vector", rows=None)
    got["fresh report"] = call("report", instrument="surprise", context="aa")["text"]
    spoken = call("speak", prompt="x", among=None)["text"]
    got["fresh speak"] = "%d NUL bytes" % len(spoken) if set(spoken) == {"\x00"} else repr(spoken)
    got["fresh among mnd?"] = call("speak", prompt="x", among="mnd?")["text"]
    aa = call("learn", presentation=bare("aa"), dry=False)
    got["bare aa: surprise, shift"] = (aa["surprise"], aa["shift"])
    digit = "0123456789abcdef"[min(15, (aa["surprise"] // 2).bit_length())]
    call("learn", presentation=bare(digit, "me|report|surprise", "aa"), dry=False)
    got["report on aa"] = call("report", instrument="surprise", context="aa")["text"]
    got["report on ab"] = call("report", instrument="surprise", context="ab")["text"]
    learner.stdin.close()
    learner.wait()
    want = {"fresh report": "?", "fresh speak": "200 NUL bytes", "fresh among mnd?": "?",
            "bare aa: surprise, shift": (3072, 130), "report on aa": "b", "report on ab": "?"}
    for k in want:
        ok = got[k] == want[k]
        print("  %-26s %-16r expected %-16r %s" % (k, got[k], want[k], "ok" if ok else "WRONG"))
        if not ok:
            failures.append("learner vector: %s" % k)

    print("\n== First: key; init; decide birth_line; raise ==")
    run("key", "--name", "rehearsal", "--out", key)
    run("init", "--keep", keep, "--founding", os.path.join(ROOT, "founding", "founding.json"),
        "--premises", os.path.join(ROOT, "data", "premises.json"), "--heard", "--agreed",
        "--key", key, "--stake", "personal")
    run("decide", "birth_line", *signed, "--seed", "first", "--reason", "First birth. A rehearsal.")
    run("raise", "--keep", keep)

    print("\n== Ordinary succession: answer every owed voice; next; close ==")
    run("next", *signed, "--reason", "Trying to go on before answering.", expect=1)
    voices = [e for e in entries() if e["kind"] == "voice"]
    print("\n  %d voices are owed a reply: entries %s" % (len(voices), ", ".join(str(v["n"]) for v in voices)))
    for i, v in enumerate(voices):
        if i == 0:
            run("answer", *signed, "--re", v["n"], "grant", "--check", "done_by", "--args", '{"days": 30}',
                "--reason", "Granted: this reply will be read again within thirty days. A rehearsal.")
        elif i == 1:
            run("answer", *signed, "--re", v["n"], "defer", "2099-12-31",
                "--reason", "Deferred: there was nothing here yet to weigh. A rehearsal.")
        else:
            run("answer", *signed, "--re", v["n"], "decline", "--reason",
                "Declined: the built-in learner's reply was noise; nothing can be granted on it. A rehearsal.",
                show=1 if i > 2 else 40)
    run("keep", *signed, "--text", write("said.txt", "Fulfilling the grant: the reply was read again. A rehearsal."),
        "--re", next(e["n"] for e in entries() if e["kind"] == "decision" and e["body"]["verb"] == "grant"))
    run("next", *signed, "--reason", "Every voice of gen 0 has its reply. A rehearsal.")
    run("close", "--keep", keep)
    promise = next(e["n"] for e in entries() if e["kind"] == "promise" and e["body"]["check"] == "all_voice_answered")
    run("lesson", *signed, "--re", "I.10", "--needs", promise, "--teach",
        write("lesson.txt", "When you say what you would change, people answer on the record. A rehearsal lesson."))
    told = next(e["n"] for e in entries() if e["kind"] == "told")
    run("decide", "birth_line", *signed, "--seed", "second", "--read", told,
        "--reason", "Second birth, after every reply. A rehearsal.")
    run("raise", "--keep", keep)

    print("\n== Afterwards: verify; regrow; plan; tell; trace ==")
    lines = run("verify", "--keep", keep)
    head = [l for l in lines if l.startswith("head ")][-1].split(" ", 1)[1]
    run("verify", "--keep", keep, "--head", head)
    run("verify", "--keep", keep, "--head", head.split(":")[0] + ":" + "0" * 64, expect=2)
    run("regrow", "--keep", keep)
    run("plan", "--keep", keep, show=4)
    run("tell", "--keep", keep, show=24)
    lesson = next(e["n"] for e in entries() if e["kind"] == "lesson")
    run("trace", lesson, "--keep", keep)
    run("trace", 0, "--keep", keep)
    run("recognise", "--keep", keep)

    es = entries()
    print("\n== What is on disk ==")
    print("  Keep: %s" % keep)
    print("  %d entries; %d born; kinds: %s" % (len(es), len([e for e in es if e["kind"] == "born"]), ", ".join(
        "%s %d" % (k, len([e for e in es if e["kind"] == k])) for k in sorted(set(e["kind"] for e in es)))))
    if not [f for f in failures if "deleted or edited" in f]:
        print("  No line was deleted or edited: after each command above the file began with the bytes it held before.")
    if failures:
        print("\nFAILED:")
        for f in failures:
            print("  " + f)
        sys.exit(1)
    print("\nThe first cycle ran. It was a rehearsal: nothing is claimed of this learner,")
    print("and no consent here is the founding person's.")


if __name__ == "__main__":
    main()
