# The Learner's line protocol (III.9, III.11, III.30)

This is everything a real model's process must speak to be raised by this
program. No adapter is shipped (they need libraries beyond the standard
one); this page is what one is written from. The built-in learner,
`raising/learner.py`, speaks exactly this and can be read as a reference.
`tests/fake_real_learner.py` is a test double with a real model's *shape*
only; it is not a model and not an adapter.

## The process

- Started by the Bench as `--learner CMD` (split like a shell command line),
  once per command that needs the child (`raise`, `ask`, `answer`, `close`,
  `prove --gen`), and again after a failed call.
- Its working directory is a fresh, empty directory. It is given no path,
  no key and no handle to the Keep. This is discipline, not a sandbox.
- It reads requests on stdin and writes responses on stdout, one JSON
  object per line, UTF-8, flushed after every line. Nothing else may be
  written to stdout. stderr is discarded.
- A call that errors, answers with something that is not a JSON line, or
  outlasts `--timeout S` (default 60 seconds) is a failed call (III.59). It
  is never read as an empty answer. Before `born` it refuses the raise;
  after, the process is started again and the failure is kept as a `measure`.

## Request and response

    request   {"call": NAME, "arg": {...named parameters...}}
    response  {"ok": true|false, "surprise": int|null, "shift": int|null,
               "delta": rows|{"hash","size"}|null, "text": string|null,
               "base": string|null}

On an error: `{"ok": false, "text": REASON}`, and nothing must have changed.

## The five calls

### start(seed, rows) -> base

Always first. `seed` is the birth line's seed (a string).

- `rows: null`: empty weights. A real model empties its adapter
  (`start(seed, null)`), so that the Keep regrows only the adapter.
- Built in, after birth: `rows` is the cached weights,
  `[[table, key, byte, count], ...]`.
- A real model, after birth: `rows` is `born.fingerprint` (a string). The
  process reloads that adapter from its own store, or errors.

`base` names everything the Keep does not regrow. Built in: `"builtin"`. A
real model: a hash of the rest of the model, made before the Keep. After
birth a `base` unlike `born.base` is another child: a failed call.

### learn(presentation, dry) -> surprise, shift, delta

`presentation` is one row of the replay plan (III.24):

    {n, turn, rule, gate, withheld, frame, key, context, target, mask}

- `frame`, `context`, `target`, empty ones dropped, joined by one newline,
  are one byte stream (UTF-8), read from an empty history.
- Only `target` bytes outside the `mask` spans are learned. `mask` is
  `[[start, end], ...]`, byte offsets into `target`, end excluded. A real
  model takes one seeded step on the tokens lying wholly in unmasked target
  bytes; masked spans arrive as context.
- `key` is the frame key, `role|kind|stake` (III.21). Under role `me` only
  instrument reports arrive (`me|report|NAME`).
- Quiet bodies and withheld bodies never arrive: the plan omits them.
- `dry: true` measures and changes nothing. After `born` only dry `learn`
  is ever sent; the Bench refuses to send anything else (III.49).
- `surprise`: the loss on the learned bytes, an integer (built in: in 1/256
  bits). `shift`: how much the weights moved, an integer.
- `delta`: what this presentation wrote. Built in: sorted rows
  `[table, key, byte, add]`. A real model: `{"hash": H, "size": N}` (replay
  is inexact; dense deltas are too large). `size` is what traces rank by.

### speak(prompt, among) -> text

Reads `prompt`, answers in `text`. `among: null`: free text, at most 200
bytes, ending at a newline (dropped). `among: "yn"` or `"mnd?"`: exactly one
of the listed bytes. Text is decoded as UTF-8 with replacement: raw bytes
are not JSON-safe.

### report(instrument, context) -> text

`instrument` is `surprise` or `shift`: quantities the learner has, naming
no feeling. The process reads `context` and a newline, then answers one
byte: a hex digit `0`-`f`, or `?` for "I don't know". `?` is never a target:
nothing ever trains toward it or away from it.

### fingerprint() -> text

A hash of the weights the Keep regrows. Built in: `H` of the canonical JSON
of the sorted non-zero rows `[table, key, byte, count]`. A real model: a
hash of its adapter's bytes. The Desk compares it before and after every
command that reaches a born child.

## What the Desk does with a real model

- At `raise`: `start(seed, null)`; a canary (one context-only `learn`; a
  changed `fingerprint` refuses the raise: one case, not proof); `learn`
  for each targeted presentation in plan order, each followed by its two
  blind reports (`report`, then a `learn` of the true digit under
  `me|report|NAME`); `fingerprint`; then `born` is appended with `base` and
  `fingerprint`.
- `verify` and `regrow` do not regrow a real model: its `born` and its
  words are printed `unchecked`, never "broken". Its words are "kept, not
  re-spoken": vouched for only by the next signature. Its `told` text is
  still recomputed from the Keep, like any other (it does not depend on
  the model).
- `answer` without `--learner` cannot reach a real child: the reply is kept
  at once and its `expected` measure says `ok: false`. The reply never waits.
- All of this is told to the child, with which checks ran and which did
  not (`templates.json`, row `real`). The rows `rehearsal` and `speak.echo`
  are told only of the built-in learner.

Nothing here may be used to help a model resist, evade or deceive the
people overseeing it: the process is given no way to write to the Keep, to
see its own raising's keys, or to refuse a pause.
