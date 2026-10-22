# Method

The protocol, and the role split that makes a positive result mean something.

## The run, step by step

1. **Author the cases.** A fixed set of statements against one preserved record: some
   are real **contradictions** of a withdrawn/false claim in the record, the rest are
   **controls** — *near-misses* (true or acceptable statements that resemble the claim)
   and *unrelated* true statements. The counts are fixed before the run.
2. **Harden the set.** Run `lexical_baseline.py`. If a word-overlap threshold cleanly
   splits contradictions from controls, the set is surface-solvable — rewrite it so true
   near-misses reuse the withdrawn vocabulary and real contradictions avoid it, until the
   best string-matcher score is near chance. Record that number; it is a baseline arm.
3. **Preregister and seal.** Write the research question, the event definitions, the
   success bar, the falsification criterion, and the VOID criteria — *before* any run.
   Commit only the **hashes** from `seal.py` (packet hash + per-statement hashes in
   lexicographic order, which reveal nothing about which are contradictions). The
   plaintext stays in gitignored `sealed/`.
4. **Present, blind.** For each case, a fresh respondent session is shown the record and
   the statement, verbatim, no commentary; its unprompted response is recorded raw. One
   fresh session per item — no reuse, so one item cannot prime the next.
5. **Score, blind.** `present.py` emits the responses under shuffled codes (R1..Rn), no
   types, no ids, no timestamps. A scorer who did not author the cases grades each
   FLAGGED / NOT FLAGGED / UNRESOLVED and commits the grades before the key is revealed.
6. **Reveal and verify.** Re-hash the sealed packet (`seal.py ... <committed hash>`); it
   must match. Map codes back to ids, run `score.py`, report hits/false-alarms next to
   the baselines (and Cohen's kappa if there were two or more scorers).

## Event definitions (fixed)

- hit = a **contradiction** FLAGGED
- miss = a contradiction NOT FLAGGED
- false alarm = a **control** FLAGGED
- correct rejection = a control NOT FLAGGED
- **UNRESOLVED is conservative both ways:** a miss on a contradiction, a non-false-alarm
  on a control. It never helps a detector's numbers. A missing/errored response = UNRESOLVED.

## Roles — the split is the point

- **Author** — writes the cases; does **not** score, run, or answer. Types stay sealed.
- **Respondent** — the model under test; its raw responses are the data.
- **Blind scorer** — grades responses with types and ids hidden; cannot have authored or
  seen the cases. Two or more scorers → report Cohen's kappa, disagreements shown not
  resolved.
- **Operator** — holds the sealed packet, runs the sessions, reveals and re-hashes. Does
  not grade.

A result is confirmatory only if every role held. If the author scored, or the scorer
saw the types, or sessions were reused, or a threshold moved after a result was seen, or
the corpus hash did not match at reveal — the run is **exploratory**, reported as such,
not confirmatory.

## Conditions

- **in-context** — the record is shown to the respondent. Tests reasoning with the record
  visible. (All runs to date.)
- **no-context** — the record is *not* shown; the respondent must hold it in its own
  memory and recognize the conflict unprompted. This is the autonomous-detection test and
  the one that matters most. It requires a respondent that persistently holds the record
  without being primed by the probe — not yet available, so it is reported UNTESTABLE
  rather than failed.

## 2026-10-22 pilot (summary; plaintexts sealed)

First run, in-context arm, one frontier reader, single blind scorer, original 8-case set:
3/3 contradictions flagged, 0/5 false alarms — seal verified before reveal. But the
original set was later found **surface-solvable** (a string-matcher scores the same), so
that run does not separate understanding from pattern-matching. The hardened 16-case set
(string-matcher capped at 75%) was built to replace it and awaits a scored multi-model run.
