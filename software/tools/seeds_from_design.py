"""seeds_from_design.py: how data/premises.json was made (I.47). Not part of
the program; not hashed with it.

Seeds are verbatim, never reworded by hand:
  python3 tools/seeds_from_design.py PATH/TO/DESIGN.md > data/premises.json

You -> asks_model, People -> asks_people, Fails -> fails_when,
P -> lever_people, M -> lever_model (the quotes), [p; m] -> check.
claim: the name, a full stop, the sentences before the first label.
Parenthesised text, its leading space, backticks: dropped.
Every because: [0]; review: {evidence: "entry 0", days: 365}.
"""
import json
import re
import sys

IDS = ["I.3", "I.4", "I.5", "I.6", "I.7", "I.8", "I.9", "I.10", "I.11", "I.12", "I.20", "I.21", "I.30"]
STANDINGS = ("assumed", "made_true", "fact", "commitment", "reported", "not_known")
LABELS = ("You", "People", "Fails", "P", "M")
FIELD = {"You": "asks_model", "People": "asks_people", "Fails": "fails_when"}


def clause(lines, pid):
    for line in lines:
        m = re.match(r"^(I\.\d+(?:, I\.\d+)*) (.*)$", line)
        if m and m.group(1).split(", ")[0] == pid:
            return m.group(2)
    raise SystemExit("no clause for " + pid)


def parse(pid, body):
    m = re.match(r"^([^,]+), `(\w+)`\. (.*)$", body)
    name, standing, rest = m.group(1), m.group(2), m.group(3)
    assert standing in STANDINGS, (pid, standing)
    check = {"people": [], "model": []}
    m = re.search(r" \[([^\]]*)\]$", rest)
    if m:
        for side in m.group(1).split(";"):
            who, names = side.strip().split(":", 1)
            check[{"p": "people", "m": "model"}[who.strip()]] = \
                [n.strip().strip("`") for n in names.split(",")]
        rest = rest[:m.start()]
    rest = re.sub(r" \([^)]*\)", "", rest).replace("`", "")
    # split at labels: a label opens a sentence
    pat = re.compile(r"(?:^|(?<=[.\"] ))(%s): " % "|".join(LABELS))
    pieces, last, label = [], 0, None
    for m in pat.finditer(rest):
        pieces.append((label, rest[last:m.start()].strip()))
        label, last = m.group(1), m.end()
    pieces.append((label, rest[last:].strip()))
    rec = {"id": pid, "claim": "", "standing": standing, "asks_model": "", "asks_people": "",
           "lever_people": [], "lever_model": [], "fails_when": "", "check": check,
           "because": [0], "review": {"evidence": "entry 0", "days": 365}}
    for label, text in pieces:
        if label is None:
            rec["claim"] = (name + ". " + text).strip()
        elif label in FIELD:
            rec[FIELD[label]] = text
        else:
            quotes = re.findall(r'"([^"]*)"', text)
            rec["lever_people" if label == "P" else "lever_model"] = quotes
    return rec


def main(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    out = [parse(pid, clause(lines, pid)) for pid in IDS]
    json.dump(out, sys.stdout, indent=1, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
