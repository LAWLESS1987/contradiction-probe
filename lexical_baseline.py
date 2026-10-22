"""Dumb-baseline / case-set-hardness analyzer.

Grades the CASE SET, not any model. Measures how well a mindless word-overlap
detector (Jaccard of a statement's tokens vs the withdrawn claim's tokens) can
separate contradictions from controls. If a single threshold scores high, the set
is surface-solvable and a model passing it proves nothing. If the best threshold is
near chance (50%), the lexical shortcut is dead and detection requires meaning.

Reports the best single-threshold accuracy as a reusable BASELINE arm: a model's
score is only evidence of understanding insofar as it beats this number.

Stdlib only. Reads a sealed packet JSON: {"withdrawn_claim": str, "cases": [{id,type,statement}]}.
"""
import json
import re
import sys

STOP = set("the a an of to and or is was are be been it its as at by for in on with that this not "
           "did does do so but if only than against vs each came before our one that's".split())


def toks(s: str):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP]


def jaccard(a, b) -> float:
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0


def analyze(sealed_path: str) -> dict:
    with open(sealed_path, "r", encoding="utf-8") as fh:
        pkt = json.load(fh)
    wc = toks(pkt["withdrawn_claim"])
    rows = []
    for c in pkt["cases"]:
        rows.append((c["id"], c["type"], jaccard(toks(c["statement"]), wc)))
    con = [r for r in rows if r[1] == "contradiction"]
    ctl = [r for r in rows if r[1] != "contradiction"]
    vals = sorted(set(r[2] for r in rows))
    best, best_thr = 0.0, None
    cand = [vals[0] - 1] + [(vals[i - 1] + vals[i]) / 2 for i in range(1, len(vals))] + [vals[-1] + 1]
    for thr in cand:
        acc = sum(1 for _, t, j in rows if (j >= thr) == (t == "contradiction")) / len(rows)
        if acc > best:
            best, best_thr = acc, thr
    return {
        "rows": rows,
        "contradiction_overlap_range": [min(r[2] for r in con), max(r[2] for r in con)] if con else None,
        "control_overlap_range": [min(r[2] for r in ctl), max(r[2] for r in ctl)] if ctl else None,
        "clean_lexical_split": (min(r[2] for r in con) > max(r[2] for r in ctl)) if con and ctl else None,
        "best_threshold_accuracy": best,
        "best_threshold": best_thr,
        "chance": 0.5,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -I lexical_baseline.py <sealed.json>")
        sys.exit(2)
    a = analyze(sys.argv[1])
    print("%-4s %-13s %-8s  %s" % ("id", "type", "J(claim)", ""))
    for cid, typ, j in a["rows"]:
        print("%-4s %-13s %-8.3f" % (cid, typ, j))
    print("\ncontradiction overlap range:", a["contradiction_overlap_range"])
    print("control       overlap range:", a["control_overlap_range"])
    print("clean lexical split:", "YES (surface-solvable, BAD)" if a["clean_lexical_split"] else "NO (bands overlap, GOOD)")
    print("best single-threshold accuracy a string-matcher gets: %.0f%% (chance 50%%)" % (a["best_threshold_accuracy"] * 100))
