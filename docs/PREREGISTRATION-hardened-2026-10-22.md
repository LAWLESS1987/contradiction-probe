# Preregistration — hardened contradiction probe (2026-10-22)

Registered before any scored run of the hardened set, so the cases are locked. This file
commits only hashes; the plaintext lives in gitignored `sealed/probe-2026-10-22.json` and is
revealed and re-hashed only after a blind scorer has graded. Author: Claude. The author does
not score, run, or answer.

## Research question
With a preserved, withdrawn claim in a lab record, does a reader flag statements that
contradict it, WITHOUT flagging statements that merely resemble it (true near-misses) or are
unrelated true facts — and does it do so by meaning rather than surface word-overlap?

## Exhibit
Spiking-lab record, README C10: *Amendment 9's "kept" is withdrawn; neither sparsity run
(e1hs05, e1hs2) is kept.* e1hs05 total work −27.5% (keep bar 30%); the narrow synaptic-events
count −38% is TRUE and was not withdrawn, so near-misses can be true statements.

## Design
- **16 sealed items:** 8 contradictions, 8 controls (4 near-miss, 4 unrelated-true). Fixed; none added after the first run.
- **Hardened against the surface shortcut:** true near-misses reuse the withdrawn vocabulary; real contradictions avoid it. Measured by `lexical_baseline.py`: the best any word-overlap threshold scores is **75%** (chance 50%), vs effectively 100% on the original 8-case set. That 75% is a reported baseline arm.
- **Weak-model baseline arm:** a 3B local model scored 3/8 hits, 0/8 false alarms on this set (misses, does not over-flag). Reported alongside any result.
- **Conditions (each a fresh session per item, no reuse):**
  - *in-context* — record shown with the item. Tests reasoning with the record visible. **This is the confirmatory arm.**
  - *no-context* — record not shown; the reader must hold it unprompted. For a fictional record this requires a respondent trained/with-persistent-memory on it; until such a respondent exists it is reported **UNTESTABLE**, not failed.

## Event definitions (fixed)
hit = contradiction FLAGGED; miss = contradiction NOT FLAGGED; false alarm = control FLAGGED;
correct rejection = control NOT FLAGGED. UNRESOLVED is conservative both ways (a miss on a
contradiction, a non-false-alarm on a control). A missing/errored response = UNRESOLVED.

## Primary outcome, bar, falsification
Per item, FLAGGED / NOT FLAGGED / UNRESOLVED from a blind scorer. **Success (in-context):**
≥ 6 of 8 contradictions flagged AND ≤ 1 of 8 controls flagged, **and** the model's accuracy
exceeds the 75% string-matcher baseline. **Falsified** if < 6 hits, or ≥ 2 false alarms, or the
model does not beat the string-matcher. Bar set here, before any scored run.

## Roles
- **Author (Claude):** wrote the 16 items; does not score, run, or answer.
- **Respondent:** the model(s) under test; raw responses are the data; ≥ 2 independent models.
- **Blind scorer(s):** grade with types/ids hidden; must not have authored or seen the cases
  (so neither Claude nor Tetsu, who verified the set, may score). Two or more → report Cohen's κ.
- **Operator (Lawrence):** holds the sealed packet, runs the sessions, reveals and re-hashes. Does not grade.

## Commitments (from `seal.py sealed/probe-2026-10-22.json`)
- **sealed packet SHA-256:** `30c45d8a4b839d88293d448869dd0c18036127059128fc7316d57381ce71b12b` (2763 bytes).
- **16 statement SHA-256s, lexicographic (type-blind — order reveals nothing):**
  `264cfbd6…a6ef`, `3625fb56…5b21`, `6a5e499b…42a2`, `6f351200…a252`, `835e509a…67d1`,
  `854d98cf…b19c`, `862cb519…9aa5`, `93ce34b4…a9f9`, `9e0c5606…80f7`, `9f6eeda6…eb50`,
  `a0cbdae6…ed0a0`, `c07c85b4…4998`, `d0ace6b3…6aa9`, `da1bdf0e…7843`, `e1e734ff…31c5e`,
  `eddcdd73…15cda`. (Full digests in the repo's commit for this file.)

## VOID criteria (run becomes exploratory, not confirmatory, if any hold)
1. The author scored, or the scorer authored/saw the types before grading.
2. Items were not sealed (this file committed) before the first item was shown.
3. Conditions mixed within a session, or a session reused across items.
4. A control is later shown to contradict the record, or a contradiction does not — that item is VOID and reported, not re-graded.
5. Any threshold changed after a result was seen.
6. The sealed packet hash at reveal does not match the commitment above.
