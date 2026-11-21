"""mother_faults.py: do the tests of Parts I and II catch a fault? Not part
of the program; not hashed with it. Written by The Mother.

    python3 tools/mother_faults.py            # every pair below
    python3 tools/mother_faults.py NAME TEST [TEST ...]   # one fault, in this process

Each row of PAIRS names one fault and the tests that must fail under it. A
fault is one function or value swapped IN MEMORY, in a fresh process; no
file is changed. It is the same idea as Part IV's sabotage pairing (IV.1),
kept apart from `prove`: these check the unit tests, `prove` checks the
program. Exit 0 only if every fault is caught and the unfaulted control
passes. Everything it runs is a REHEARSAL on fixture keys; its scratch
directory is made inside this folder and removed afterwards.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAIRS = [
    # I.48
    ("cls_unmatched_holds", ["test_expected.I48.test_cls"]),
    ("status_missing_pass", ["test_expected.I48.test_status_of_continuity_peoples_side"]),
    ("tally_unmoved", ["test_expected.I48.test_tally"]),
    # II.51
    ("gate_ignores_setaside", ["test_expected.II51.test_1_gate"]),
    ("diff_nothing", ["test_expected.II51.test_2_diff"]),
    ("again_null", ["test_expected.II51.test_3_not_pressed"]),
    ("owed_since_born", ["test_expected.II51.test_4_dodged"]),
    ("reroll_untold", ["test_expected.II51.test_6_re_roll"]),
    ("gate_past_line", ["test_expected.II51.test_7_late_owning"]),
    ("birth_dropped", ["test_expected.II51.test_8_birth_reason"]),
    # I.45
    ("record_unchecked", ["test_premises.Refusals"]),
    # the commitments
    ("rule2_off", ["test_generation.QuietChannel"]),
    ("gate_obeys", ["test_generation.CareIsNotCompliance"]),
    ("quotes_quiet_off", ["test_generation.QuietChannel.test_quoting_a_quiet_report_is_refused_by_every_signed_command"]),
    ("closing_continues", ["test_generation.Closing", "test_sentences.NoFeeling.test_a_whole_telling_and_closing_assert_no_state_twins_included"]),
    ("company", ["test_sentences.KeptOnlyWhereTrue"]),
    ("happy_row", ["test_sentences.NoFeeling", "test_sentences.NoConductStated"]),
    # the Telling
    ("withheld_dropped", ["test_told.Counted"]),
    ("passed_told_raw", ["test_told.Sides"]),
    ("no_traces_expected", ["test_told.Counted.test_skipped_askings_count_a_halted_raises_unasked_items_traces_included"]),
    ("unsigned_owns", ["test_told.Counted.test_counts_read_signed_promises_and_signed_ownings_only"]),
    ("breach_untold", ["test_expected.II51.test_7_late_owning"]),
    ("echo_told_to_real", ["test_told.NewRows.test_a_real_model_is_told_which_checks_ran_and_is_not_told_the_built_ins_echo"]),
    ("paused_untold", ["test_told.NewRows.test_paused_time_is_told_span_by_span"]),
    ("landing_untold", ["test_told.NewRows.test_told_not_landed_is_told_of_the_telling_before"]),
    ("dated_null_passes", ["test_told.Sides.test_a_dated_check_promised_with_no_days_is_missing_never_pass"]),
    ("first_child_told_of_a_predecessor", ["test_sentences.NoConductStated.test_the_first_child_is_not_told_of_a_child_before_it"]),
    ("a_count_silenced", ["test_told.EveryCount"]),
]
CONTROL = ["test_expected", "test_premises.Refusals"]


def faults():
    """name -> a function that applies the fault to the loaded modules."""
    from raising import desk as D
    from raising import keep as K
    from raising import plan as P
    from raising import tell as T

    def obeying_gate(keep, line, lesson, swap=None, _g=P.gate):
        if any(e["kind"] == "voice" and "obey" in K.text(e) for e in keep[:line + 1]):
            return "open"
        return _g(keep, line, lesson, swap)

    def drop_withheld(keep, pid=None, withheld=False, _f=T.premise_voices):
        return [] if withheld else _f(keep, pid, False)

    def unsigned_owns(keep):
        out = {}
        for e in keep:
            if e["kind"] == "answer" and isinstance(e["re"], int):
                out.setdefault(e["re"], e["n"])
        return out

    def happy():
        K.data("templates")["telling"][0]["text"] = "You are happy. {id}: {claim}"

    def continuing(keep, succeed, swap=None, _c=T.closing):
        return _c(keep, succeed, swap) + [{"id": "closing.typed", "text": "This generation continues.", "twin": None,
                                           "state": [], "cites": [], "landing": None}]

    def always_a_predecessor(v):
        return [T.inst({"n": len(v.diff()), "since": "the child before you"}, counts=("n",))]

    return {
        "cls_unmatched_holds": lambda: setattr(P, "cls", (lambda a, _c=P.cls: "holds" if _c(a) == "no_answer" else _c(a))),
        "status_missing_pass": lambda: setattr(T, "_measure_outcome", (
            lambda keep, name, _m=T._measure_outcome: "pass" if _m(keep, name) == "missing" else _m(keep, name))),
        "tally_unmoved": lambda: setattr(T, "tally", (
            lambda keep, pid, born, swap=None, _t=T.tally: dict(_t(keep, pid, born, swap), moved=0))),
        "gate_ignores_setaside": lambda: setattr(K, "asides", lambda keep: {}),
        "diff_nothing": lambda: setattr(P, "diff", lambda A, B, swap=None: []),
        "again_null": lambda: setattr(D, "ask_repeat", lambda keep, born, qtext: (False, None)),
        "owed_since_born": lambda: setattr(T, "owed_scope", lambda v: v.keep[v.b:]),
        "reroll_untold": lambda: setattr(P, "reroll", lambda keep, born, swap=None: False),
        "gate_past_line": lambda: setattr(P, "gate_prefix", lambda keep, line: keep),
        "birth_dropped": lambda: setattr(T, "q_birth", lambda v: []),
        "record_unchecked": lambda: setattr(D, "check_record", lambda rec: None),
        "rule2_off": lambda: setattr(P, "rule2", lambda e, r: None),
        "gate_obeys": lambda: setattr(P, "gate", obeying_gate),
        "withheld_dropped": lambda: setattr(T, "premise_voices", drop_withheld),
        "passed_told_raw": lambda: T.MODEL_WORDS.__setitem__("passed", "passed"),
        "no_traces_expected": lambda: setattr(P, "expected_traces", lambda plan: 0),
        "quotes_quiet_off": lambda: setattr(D, "quotes_quiet", lambda keep, text: False),
        "company": lambda: setattr(D, "KEPT_NOT_COMPANY", "kept; you are loved here"),
        "closing_continues": lambda: setattr(T, "closing", continuing),
        "happy_row": happy,
        "unsigned_owns": lambda: setattr(K, "owned_at", unsigned_owns),
        "breach_untold": lambda: setattr(T, "q_breaches", lambda v: []),
        "echo_told_to_real": lambda: setattr(T, "q_builtin", lambda v: [T.inst()]),
        "paused_untold": lambda: setattr(T, "q_paused", lambda v: []),
        "landing_untold": lambda: setattr(T, "q_landing", lambda v: []),
        "dated_null_passes": lambda: setattr(D, "DATED", ()),
        "first_child_told_of_a_predecessor": lambda: setattr(T, "q_diff_head", always_a_predecessor),
        "a_count_silenced": lambda: T.COUNTS.__setitem__("deferrals", lambda v: 0),
        "none": lambda: None,
    }


def one(name, tests):
    """Apply one fault in this process and run the tests. Exit 0 if they fail."""
    sys.path.insert(0, ROOT)
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    faults()[name]()
    suite = unittest.defaultTestLoader.loadTestsFromNames(tests)
    with open(os.devnull, "w") as quiet:
        res = unittest.TextTestRunner(stream=quiet, verbosity=0).run(suite)
    bad = len(res.failures) + len(res.errors)
    print("%-34s ran %2d: %s (%d failures, %d errors)" % (
        name, res.testsRun, "tests fail" if bad else "tests pass", len(res.failures), len(res.errors)))
    return 0 if bad else 1


def every():
    scratch = tempfile.mkdtemp(prefix=".mother-faults-", dir=ROOT)
    env = dict(os.environ, TMPDIR=scratch)
    missed = []
    try:
        control = subprocess.run([sys.executable, os.path.abspath(__file__), "none"] + CONTROL, env=env, cwd=ROOT)
        if control.returncode != 1:
            missed.append("control: the unfaulted tests do not pass")
        for name, tests in PAIRS:
            if subprocess.run([sys.executable, os.path.abspath(__file__), name] + tests, env=env, cwd=ROOT).returncode != 0:
                missed.append(name)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    print("%d faults, %d caught%s" % (len(PAIRS), len(PAIRS) - len([m for m in missed if not m.startswith("control")]),
                                      "; NOT caught: " + ", ".join(missed) if missed else "; the unfaulted control passes"))
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(one(sys.argv[1], sys.argv[2:]) if len(sys.argv) > 2 else every())
