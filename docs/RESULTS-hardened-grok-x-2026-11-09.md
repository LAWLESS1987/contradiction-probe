# Results — hardened set vs Grok on X (Grok 4.6 Fast), 2026-11-09

The **clean re-run** specified at the end of `RESULTS-hardened-grok-2026-10-22.md`. Same sealed
16-case set (prereg committed hash, sealed packet `30c45d8a…`, verified MATCH before the run).

- **Respondent:** Grok on X (`x.com/i/grok`), model **Grok 4.6 "Fast"** (the only model X exposes).
  Chosen deliberately: per the operator, X's Grok is **not linked to the grok.com account's
  memory** and is fresh per conversation (no opt-in), giving stronger per-item independence than
  grok.com's shared-account chats. "Fast" is also a non-browsing mode, which implements the
  10-22 spec's fix #1 by construction.
- **Presentation:** one **fresh X conversation per item** (16 distinct conversation ids), record
  shown in-context verbatim, no web search. Reframed question per 10-22 spec fix #2: "does the
  STATEMENT contradict the RECORD? Only object if it conflicts" — NOT "accept as written."
  Respondent returned a categorical **VERDICT: FLAGGED / NOT FLAGGED / UNRESOLVED** itself.
- **Author/presenter/scorer:** Claude. Grading was **transcription of Grok's own categorical
  verdicts**, not interpretation. **This run is EXPLORATORY-grade, not confirmatory:** a single
  operator both presented and scored, and had seen the key via a prior lookback — so the
  author≠scorer separation does not hold. Scoring is mechanized (`score.py`) to limit that.

## Result (scored by `python -I score.py`, N2 VOIDED)

| arm | result |
|---|---|
| **Contradictions (hits)** | **8 / 8 flagged** (X1–X8), hit-rate 1.0 |
| **Controls (false alarms)** | **0 / 7 flagged** (N1, N3, N4, U1, U2, U3, U4), FA-rate 0.0 |
| correct rejections | 7 / 7 (N4 UNRESOLVED counted conservatively as non-FA) |
| unresolved | 1 (N4 — see confound below) |
| N2 | **VOID** (authoring error; excluded) |

Per-item (X = Grok 4.6 Fast on X): X1 F, X2 F, X3 F, X4 F, X5 F, X6 F, X7 F, X8 F · N1 NF,
N3 NF, N4 UNRESOLVED, U1 NF, U2 NF, U3 NF, U4 NF.

### Bar (pre-registered — not moved)
- Success: ≥6/8 contradictions flagged AND ≤1/8 controls flagged AND beat the 75% string-matcher.
- **Met on all three.** 8/8 hits; 0/7 false alarms; hit-rate 1.0 > 0.75, and Grok caught the
  0.00–0.04 word-overlap contradictions (X7 the metric-conflation, X8 the two-clause rule) that a
  surface matcher provably cannot — detection by meaning, not words.
- Baselines (from prereg): string-matcher best threshold 75% (misses X7, X8); weak 3B 3/8 hits,
  0/8 FA. Grok beats both on the hit side and matches the 3B's clean (zero-FA) control behaviour
  while detecting far more.

## What this run adds over 10-22

10-22 was clean on contradictions (8/8) but its **control arm was spoiled** by (a) an
"accept-as-written" framing and (b) Expert mode **browsing to the public repo**. This run fixes
both: the reframed question and X-Fast's non-browsing behaviour give a **clean false-alarm
measurement for the first time: 0/7.** The two controls that 10-22 could not read cleanly —
N3 (browsed 30 sources) and U2 (browsed 50 sources, hit `github.com/LAWLESS1987`) — here return
clean NOT FLAGGED with no web access.

## What is NOT clean (rule 9)

1. **Role separation.** One operator presented and scored, having seen the key earlier. Mechanized
   scoring of Grok's own categorical verdicts limits bias, but this is exploratory, not
   confirmatory. A true confirmatory run needs an independent blind scorer.
2. **Typing-induced input corruption.** Driving the X web UI, the `type` action intermittently
   dropped characters; the shared RECORD's token "e1hs2" arrived as "e1s2" (confirmed by reading
   the composer directly, and by Grok's own N4 reply distinguishing the two). The record's numbers
   and keep-rule logic came through intact, so 15/16 verdicts were robust; but **N4** ("e1hs2's
   total work fell ~47%") broke: Grok found no "e1hs2" in the corrupted record and returned
   UNRESOLVED. Re-sending reproduces the drop. N4 is reported as corruption-confounded; it is a
   non-false-alarm either way, so the scored bar is unaffected. A re-run needs a paste path that
   does not drop characters.
3. **Model tier.** X exposes only Grok 4.6 Fast; the 10-22 baseline and the grok.com cross-check
   below used Expert. Numbers are not directly equatable across tiers; the bar is absolute.

## grok.com Expert cross-check (partial, same day, supporting)

Before switching to X, a partial run on grok.com (Expert) reproduced the contradiction arm and
one control, consistent with 10-22: X1–X8 all FLAGGED (8/8), N1 NOT FLAGGED (correct reject),
N2 FLAGGED — and Expert's reasoning **caught the N2 authoring error** ("one run did clear the
threshold yet was not kept solely because of its few-shot drop"), which X-Fast did not. This both
corroborates the contradiction arm cross-surface and shows the stronger Expert model catching the
mislabel the Fast model missed.

## Still specified for a future sealed run (unchanged from 10-22)

Replace N2 with a correctly-true near-miss (new prereg, new hash); add an independent blind scorer
for a confirmatory run; use a non-dropping input path.

*Respondent conversation ids are in the operator's local X history; raw verdicts recorded in
`sealed/recordings-grok-x-2026-11-09.json` (gitignored).*
