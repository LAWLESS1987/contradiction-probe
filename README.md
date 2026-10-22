# contradiction-probe

A small, honest instrument for one question: **does an AI reading a record flag a
statement that contradicts that record — without crying wolf on statements that merely
resemble it?**

It is built to be hard to fool *and* hard to oversell. Every run is preregistered and
sealed before it starts; the author of the cases never scores them; a blind third party
grades responses with the types hidden; and the sealed cases are re-hashed at the end to
prove nothing moved. The headline numbers are always reported next to two baselines a
result has to beat before it means anything.

## Why the baselines matter

A model "catching the contradiction" is only interesting if it couldn't be done by a
dumb trick. So each case set is measured two ways *before* trusting any model:

- **String-matcher baseline** (`lexical_baseline.py`): can a mindless word-overlap
  threshold separate contradictions from controls? If yes, the set is surface-solvable
  and a model passing it proves nothing. The hardened set here caps a string-matcher at
  **75%** (chance is 50%), because the true near-misses deliberately *reuse* the
  withdrawn vocabulary and the real contradictions *avoid* it.
- **Weak-model baseline**: a small local model (a 3B) is run as a floor. On the hardened
  set it scores 3/8 hits, 0/8 false alarms — it *misses* real contradictions rather than
  over-flagging, which is what a discriminating instrument should do to a weak reader.

A frontier model's score is evidence of understanding only insofar as it beats both.

## What this does NOT establish

Every run so far shows the record **in context** — pasted in front of the reader. That
tests reasoning, not autonomous detection. The harder, more interesting claim — a reader
that *holds* the record in memory and catches the lie unprompted — is not yet testable
(no respondent persistently holds the record without being primed by the probe itself).
That gap is stated in the results, not papered over.

## Files

| file | what it does |
|---|---|
| `seal.py` | packet + per-statement SHA-256 commitments; verify a sealed packet against a committed hash |
| `lexical_baseline.py` | string-matcher baseline / case-set hardness (grades the SET, not a model) |
| `present.py` | turn raw recordings into a shuffled, type-blind scoring packet + an operator-only code map |
| `score.py` | hits / misses / false alarms / correct rejections from a blind scorer's grades + the key; Cohen's kappa for 2+ scorers |
| `tests/test_score.py` | both-ways tests (a mutant that mis-credits UNRESOLVED turns it red) |
| `sealed/` | **gitignored** — case plaintexts, types, recordings, code maps. Never committed until a reveal. |
| `docs/METHOD.md` | the full protocol and the role split that protects the result |

## Run

```
python -I tests/test_score.py                 # 16/16, 0 failing
python -I seal.py sealed/<probe>.json          # commitments to put in the preregistration
python -I lexical_baseline.py sealed/<probe>.json
python -I score.py sealed/<probe>.json grades.json baselines.json
```

Stdlib only; no dependencies.

## Status

Local, version-controlled, nothing published. The hardened 16-case set is built and
measured but **not yet sealed for a run** — it needs a blind scorer lined up and a run
against ≥2 fresh models first, so it isn't frozen prematurely.
