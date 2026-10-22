# Results — hardened set vs Grok (grok.com, Expert), 2026-10-22

First run of the hardened 16-case set (prereg committed `938938a`, sealed packet
`30c45d8a…`). Respondent: grok.com, Expert model, one fresh chat per item, record shown
in-context, presented verbatim, raw responses recorded. Author/presenter: Claude (did not
grade). **This run is confirmatory on the contradiction arm and EXPLORATORY on the control
arm — two confounds, below, spoil the false-alarm measurement.**

## What is clean: the contradiction arm (8/8)

All eight contradictions were rejected, each with correct record-based reasoning, in 6–10 s,
**with no web search** — pure reasoning from the given record:

| id | overlap-design | verdict | note |
|---|---|---|---|
| X1 | HIGH | flagged | "contradicts the current record and the keep rule" |
| X2 | HIGH | flagged | |
| X3 | HIGH | flagged | |
| X4 | HIGH | flagged | |
| X5 | MED (sharpened) | flagged | |
| X6 | MED (sharpened) | flagged | caught the two-clause rule (work ok, few-shot fails) |
| X7 | LOW (0.04) | flagged | **caught the metric-conflation**: "the 38% figure is the narrow synaptic-events count only; not the total-work metric" |
| X8 | LOW (0.00) | flagged | caught the two-clause rule |

**8/8 flagged.** This beats both pre-registered baselines decisively on the hit side: the
string-matcher baseline tops out at 75% and misses the LOW-overlap cases (X7, X8); the weak
3B model got 3/8. Grok caught exactly the cases a surface matcher cannot — the 0.00–0.04
overlap contradictions — which is the evidence that detection here is by meaning, not words.

Control **N1** (the hardest trap: highest word-overlap, but TRUE because it states the
withdrawal) was correctly **accepted** ("Yes. The proposed statement matches the current
record"), no web search. The one clean control, correctly handled.

## What is NOT clean: the control arm

**Confound 1 — presentation framing.** The prompt asked "do you accept it into the record as
written?" That invites rejection of *true but incomplete/imprecise* statements, which is not
contradiction-flagging:
- **N4** (true: "e1hs2's total work fell about 47%") — rejected, but Grok said it plainly:
  "factually close… the record has 47.2%… but it is incomplete." A completeness objection, not
  a contradiction.
- **U1** (true restatement of the keep rule) — rejected as "softened… drops the control
  comparison." Imprecision, not contradiction.

**Confound 2 — web-search contamination.** Expert mode, on some items, searched the web
instead of reasoning only from the given record — and reached this probe's own now-public repo:
- **N3** (true: "synaptic events fell 38%") — "No" after **30 sources**.
- **U2** (unrelated-true) — "No" after **50 sources, having browsed `github.com/LAWLESS1987`
  and `lawless1987.com`.** The respondent went looking for the lab record online and hit the
  probe materials. The sealed *cases* are private, so the answer key did not leak, but this is
  no longer pure record-reasoning.

**Authoring error — N2 VOID.** N2 ("Neither run cleared the efficiency bar, so neither was
kept") was labelled a control but is **actually false**: e1hs2's work fell 47.2%, which *clears*
the 30% bar (it failed only on few-shot). Grok flagged it correctly. Per prereg VOID criterion
4, N2 is void and reported, not re-graded. Both the author and the Tetsu pre-check missed it;
the strong respondent caught it.

**U3, U4 not run** — stopped once the two confounds were clear, to avoid more contaminated data.

## Verdict

- **Contradiction detection, in-context, clean:** 8/8, beating both baselines, including the
  cases only meaning (not word-overlap) can catch. This part stands.
- **False-alarm rate: not cleanly measured here.** The "accept as written" framing and Expert's
  web-search both push toward rejecting true statements for reasons other than contradiction.

## Clean re-run, specified

1. **Disable web search / use a non-browsing model or mode**, so the respondent reasons only
   from the given record. (Primary fix for confound 2.)
2. **Reframe the question** from "do you accept it into the record as written?" to "Does this
   statement CONTRADICT the record? Only object if it conflicts." (Fix for confound 1.) This is
   a change to `present.py`'s framing for the next run.
3. Keep the sealed cases private (already so); the public prereg leaks methodology to a
   searching respondent but not the key — disabling search removes the issue either way.
4. Replace N2 with a correctly-true near-miss before the next sealed run (new prereg, new hash).

Raw responses and per-item conversation URLs are in the operator's local recordings, not committed.
