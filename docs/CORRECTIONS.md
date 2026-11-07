# Corrections

Every published claim this repository withdrew, with its original wording kept here unedited. Each one is also
in `docs/RETRACTED.json`, which `research_grade.py` reads: the wording may appear elsewhere only with its id cited
within 10 lines.

## CP-NOT-SEALED-2026-11-04

**Original wording** (README, Status, kept in place with a dated correction beside it): "The hardened 16-case set is
built and measured but **not yet sealed for a run** — it needs a blind scorer lined up and a run against ≥2 fresh
models first, so it isn't frozen prematurely."

**Why it was wrong.** The hardened set was sealed and run the same day: preregistration `938938a`, results `97e4ab4`
(`docs/RESULTS-hardened-grok-2026-10-22.md`). Raised by Codex's scan (mutual-benefit-collective issue #12, item 5).

**What still holds.** A second blind scorer and a second fresh model have not been run.
