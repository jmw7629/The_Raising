"""helper.py: what the tests share. Everything here is a REHEARSAL: fixture
keys (fixed-seed), a made-up fixture conversation, the built-in learner.
Nothing is anyone's consent, and nothing is claimed of the learner."""
import atexit
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from raising import keep as K  # noqa: E402
from raising import prove  # noqa: E402

_BASE = tempfile.mkdtemp(prefix="raising-tests-")
atexit.register(shutil.rmtree, _BASE, True)
FX = prove.Fixtures(os.path.join(_BASE, "fixtures"))
HERE = os.path.dirname(os.path.abspath(__file__))


def at(stage, swap=None):
    """A fresh fork of the fixture at `gen0` (first raise done, voices owed)
    or `gen1` (answered, closed, a lesson, second raise done)."""
    return FX.at(stage, swap)


def empty():
    return FX.empty()


def init(rig):
    rig.ok("init", {"founding": prove._resolve(rig, "@founding"), "premises": prove._resolve(rig, "@premises"),
                    "heard": True, "agreed": True})
    return rig


def scratch():
    FX.count += 1
    d = os.path.join(_BASE, "scratch-%d" % FX.count)
    os.makedirs(d)
    return d


def last(lines):
    return lines[-1] if lines else ""


class Case(unittest.TestCase):
    maxDiff = None

    def code(self, rig, cmd, args=None, want=0, **kw):
        code, lines = rig.run(cmd, args, **kw)
        self.assertEqual(code, want, "%s %s printed %s" % (cmd, args, lines[-3:]))
        return lines

    def kinds(self, rig):
        return [e["kind"] for e in rig.entries()]


_PROVED = []


def proved():
    """The whole `prove`, run once for every test file that reads it (it
    takes over a minute): (rig at gen1 with the program's proof kept as its
    last entry, exit code, printed lines). Fork the rig before changing it."""
    if not _PROVED:
        rig = at("gen1")
        code, out = rig.run("prove", {})
        _PROVED.append((rig, code, out))
    return _PROVED[0]
