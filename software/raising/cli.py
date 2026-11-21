"""cli.py: `raising CMD [--keep DIR]` (III.17, III.66). Exits: III.61.

Signed commands take --key FILE --stake S; fields are same-named flags;
bodies, a FILE. The CLI passes the system clock; nothing below it reads one.
"""
import argparse
import os
import sys
import time

from . import desk

SIGNED = ("init", "consent", "keep", "lesson", "setaside", "decide", "promise", "answer",
          "own", "next", "resume", "unlock", "pause", "ask", "prove")
LEARNER = ("raise", "ask", "answer", "close", "prove")  # III.66: [--learner CMD] [--timeout S]
TIMED = ("trace", "regrow", "verify")                   # these regrow the built-in learner


class Refusal(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):  # a mistyped command is a refusal: exit 1, never 2 (III.61)
        raise Refusal("%s\n%s" % (message, self.format_usage().strip()))


def parser():
    ap = Parser(prog="raising", description=(
        "The Raising: a proposal, written by AI voices at one person's request. "
        "It trains no existing model and speaks for no company."))
    sub = ap.add_subparsers(dest="cmd", metavar="CMD")
    sub.required = True
    cmds = {}
    for name in desk.COMMANDS:
        p = sub.add_parser(name, help=(desk.COMMANDS[name].__doc__ or "").strip().split("\n")[0])
        p.add_argument("--keep", metavar="DIR")
        if name in SIGNED:
            p.add_argument("--key", metavar="FILE")
            p.add_argument("--stake", choices=("commercial", "personal", "none", "undeclared"))
        if name in LEARNER:
            p.add_argument("--learner", metavar="CMD", help="a real model's process, speaking III.9's lines")
        if name in LEARNER + TIMED:
            p.add_argument("--timeout", type=float, metavar="S", help="seconds a Learner call may take (60)")
        cmds[name] = p
    c = cmds
    c["key"].add_argument("--name")
    c["key"].add_argument("--out", metavar="FILE")
    c["init"].add_argument("--founding", metavar="FILE")
    c["init"].add_argument("--premises", metavar="FILE")
    for n in ("init", "consent"):
        c[n].add_argument("--heard", action="store_true")
        c[n].add_argument("--agreed", action="store_true")
    c["keep"].add_argument("--text", metavar="FILE")
    c["keep"].add_argument("--re", metavar="n")
    c["lesson"].add_argument("--re", metavar="ID")
    c["lesson"].add_argument("--needs", metavar="p,...")
    c["lesson"].add_argument("--teach", metavar="FILE")
    c["setaside"].add_argument("--re", metavar="n")
    c["setaside"].add_argument("--reason")
    c["setaside"].add_argument("--withhold", action="store_true")
    d = c["decide"]
    d.add_argument("verb", choices=("birth_line", "premises", "widen", "probe", "program", "admit"))
    d.add_argument("--reason")
    d.add_argument("--seed")
    d.add_argument("--read", metavar="n,...")
    d.add_argument("--correction", action="store_true")
    d.add_argument("--id")
    d.add_argument("--kept", action="store_true")
    d.add_argument("--record", metavar="FILE")
    d.add_argument("--proposal", metavar="n")
    d.add_argument("--evidence", metavar="m,...")
    d.add_argument("--hash")
    d.add_argument("--name")
    d.add_argument("--pub", metavar="P0", help="admit: the key field, the P(0) that `key` printed")
    c["promise"].add_argument("--re", metavar="ID")
    c["promise"].add_argument("--check", metavar="NAME")
    c["promise"].add_argument("--args", metavar="JSON")
    a = c["answer"]
    a.add_argument("--re", metavar="n")
    a.add_argument("verb", choices=("grant", "decline", "defer"))
    a.add_argument("date", nargs="?", metavar="DATE")
    a.add_argument("--reason")
    a.add_argument("--check", metavar="NAME")
    a.add_argument("--args", metavar="JSON")
    c["own"].add_argument("--re", metavar="b")
    c["own"].add_argument("--failed", metavar="TEXT")
    c["own"].add_argument("--changes", metavar="TEXT")
    c["next"].add_argument("--read", metavar="n,...")
    for n in ("next", "resume", "unlock", "pause"):
        c[n].add_argument("--reason")
    c["ask"].add_argument("--q", metavar="FILE")
    c["verify"].add_argument("--head", metavar="n:hash")
    c["plan"].add_argument("--upto", metavar="n")
    c["tell"].add_argument("--born", metavar="b")
    c["trace"].add_argument("n")
    c["prove"].add_argument("--sabotage", metavar="ID")
    c["prove"].add_argument("--gen", action="store_true")
    return ap


def main(argv=None):
    try:
        ns = parser().parse_args(argv)
    except Refusal as x:
        sys.stdout.write("refused: %s\n" % x)
        return 1
    args = vars(ns)
    cmd, keep = args.pop("cmd"), args.pop("keep", None)
    code, lines = desk.run(cmd, keep, args, time.time, {})
    out = sys.stdout
    try:
        for line in lines:
            try:
                out.write(line + "\n")
            except UnicodeEncodeError:
                out.write(line.encode("utf-8", "replace").decode("ascii", "replace") + "\n")
        out.flush()
    except BrokenPipeError:
        # The reader went away (`... | head`). The command had already done its work before a
        # line was printed, so its exit code stands; only the printing stops. (The Child.)
        try:
            sys.stdout = open(os.devnull, "w")
        except OSError:
            pass
    return code


if __name__ == "__main__":
    sys.exit(main())
