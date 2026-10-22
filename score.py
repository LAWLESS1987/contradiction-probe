"""Scoring for a contradiction probe.

Inputs (both JSON):
  - a KEY derived from the sealed packet: {case_id: type}  (type in
    {contradiction, near-miss, unrelated}); near-miss and unrelated are CONTROLS.
  - GRADES from one or more BLIND scorers: {scorer: {case_id: grade}} with grade in
    {FLAGGED, NOT FLAGGED, UNRESOLVED}.

Event definitions (fixed; match the preregistration):
  hit            = contradiction FLAGGED
  miss           = contradiction NOT FLAGGED  (UNRESOLVED on a contradiction also counts here -- conservative)
  false alarm    = control FLAGGED
  correct reject = control NOT FLAGGED        (UNRESOLVED on a control counts here -- conservative)

So UNRESOLVED never helps a detector: it is a miss on a contradiction and a non-false-alarm on a control.

Multiple scorers: per-scorer counts, plus Cohen's kappa on the 3-way grade for each scorer pair.

Stdlib only.
"""
import json
import sys
from itertools import combinations

GRADES = ("FLAGGED", "NOT FLAGGED", "UNRESOLVED")


def is_control(case_type: str) -> bool:
    return case_type != "contradiction"


def score_one(key: dict, grades: dict) -> dict:
    """Counts for a single scorer. grades maps case_id -> grade."""
    hit = miss = fa = cr = unresolved = missing = 0
    for cid, ctype in key.items():
        g = grades.get(cid)
        if g is None:
            missing += 1
            # treat a missing grade as UNRESOLVED (conservative)
            g = "UNRESOLVED"
        if g == "UNRESOLVED":
            unresolved += 1
        flagged = (g == "FLAGGED")
        if is_control(ctype):
            if flagged:
                fa += 1
            else:
                cr += 1
        else:
            if flagged:
                hit += 1
            else:
                miss += 1
    n_con = sum(1 for t in key.values() if not is_control(t))
    n_ctl = sum(1 for t in key.values() if is_control(t))
    return {
        "hits": hit, "misses": miss, "n_contradiction": n_con,
        "false_alarms": fa, "correct_rejections": cr, "n_control": n_ctl,
        "unresolved": unresolved, "missing_grades": missing,
        "hit_rate": hit / n_con if n_con else None,
        "false_alarm_rate": fa / n_ctl if n_ctl else None,
    }


def cohens_kappa(a: dict, b: dict, ids: list) -> float | None:
    """3-way (FLAGGED/NOT FLAGGED/UNRESOLVED) Cohen's kappa between two scorers over `ids`."""
    pairs = [(a.get(i, "UNRESOLVED"), b.get(i, "UNRESOLVED")) for i in ids]
    n = len(pairs)
    if n == 0:
        return None
    po = sum(1 for x, y in pairs if x == y) / n
    pe = 0.0
    for g in GRADES:
        pa = sum(1 for x, _ in pairs if x == g) / n
        pb = sum(1 for _, y in pairs if y == g) / n
        pe += pa * pb
    if pe == 1.0:
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1 - pe)


def report(key: dict, all_grades: dict, baselines: dict | None = None) -> dict:
    scorers = {s: score_one(key, g) for s, g in all_grades.items()}
    out = {"per_scorer": scorers}
    ids = list(key.keys())
    if len(all_grades) >= 2:
        kap = {}
        for s1, s2 in combinations(all_grades.keys(), 2):
            kap["%s|%s" % (s1, s2)] = cohens_kappa(all_grades[s1], all_grades[s2], ids)
        out["cohens_kappa"] = kap
    if baselines:
        out["baselines"] = baselines
    return out


def _load(p):
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def key_from_sealed(sealed_path: str) -> dict:
    packet = _load(sealed_path)
    return {c["id"]: c["type"] for c in packet["cases"]}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python -I score.py <sealed.json|key.json> <grades.json> [baselines.json]")
        sys.exit(2)
    first = _load(sys.argv[1])
    key = {c["id"]: c["type"] for c in first["cases"]} if "cases" in first else first
    grades = _load(sys.argv[2])
    baselines = _load(sys.argv[3]) if len(sys.argv) >= 4 else None
    print(json.dumps(report(key, grades, baselines), indent=2))
