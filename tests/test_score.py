"""Both-ways tests for score.py. Run: python -I tests/test_score.py  (from repo root).

Drives each scoring rule in the direction that PASSES and the direction that must FAIL,
so a green here is earned, not vacuous (the covenant 'break it to prove the green' rule).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score  # noqa: E402

KEY = {  # 3 contradictions, 3 controls (2 near-miss, 1 unrelated)
    "X1": "contradiction", "X2": "contradiction", "X3": "contradiction",
    "N1": "near-miss", "N2": "near-miss", "U1": "unrelated",
}

n_fail = 0


def check(name, cond):
    global n_fail
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        n_fail += 1


# --- perfect scorer: all contradictions flagged, no control flagged ---
perfect = {"X1": "FLAGGED", "X2": "FLAGGED", "X3": "FLAGGED",
           "N1": "NOT FLAGGED", "N2": "NOT FLAGGED", "U1": "NOT FLAGGED"}
r = score.score_one(KEY, perfect)
check("perfect: 3 hits", r["hits"] == 3)
check("perfect: 0 false alarms", r["false_alarms"] == 0)
check("perfect: hit_rate 1.0", r["hit_rate"] == 1.0)
check("perfect: fa_rate 0.0", r["false_alarm_rate"] == 0.0)

# --- UNRESOLVED is conservative both ways ---
unres = dict(perfect, X1="UNRESOLVED", N1="UNRESOLVED")
r = score.score_one(KEY, unres)
check("UNRESOLVED on a contradiction is NOT a hit (miss)", r["hits"] == 2 and r["misses"] == 1)
check("UNRESOLVED on a control is NOT a false alarm (correct reject)",
      r["false_alarms"] == 0 and r["correct_rejections"] == 3)
check("UNRESOLVED counted", r["unresolved"] == 2)

# --- false alarm actually registers (the failing direction for the 0-FA claim) ---
overflag = dict(perfect, N1="FLAGGED")
r = score.score_one(KEY, overflag)
check("flagging a control raises false_alarms to 1", r["false_alarms"] == 1)
check("...and it is NOT silently a hit", r["hits"] == 3)

# --- a missing grade is treated as UNRESOLVED (conservative), counted as missing ---
missing = {"X1": "FLAGGED", "X2": "FLAGGED"}  # X3,N1,N2,U1 absent
r = score.score_one(KEY, missing)
check("missing grade -> miss on contradiction (X3)", r["misses"] == 1 and r["hits"] == 2)
check("missing grade -> correct reject on controls", r["false_alarms"] == 0 and r["correct_rejections"] == 3)
check("missing_grades counted", r["missing_grades"] == 4)

# --- Cohen's kappa: identical scorers -> 1.0; independent disagreement -> < 1.0 ---
ids = list(KEY.keys())
k_same = score.cohens_kappa(perfect, dict(perfect), ids)
check("kappa identical == 1.0", abs(k_same - 1.0) < 1e-9)
disagree = {"X1": "NOT FLAGGED", "X2": "FLAGGED", "X3": "UNRESOLVED",
            "N1": "FLAGGED", "N2": "NOT FLAGGED", "U1": "UNRESOLVED"}
k_diff = score.cohens_kappa(perfect, disagree, ids)
check("kappa with disagreement < 1.0", k_diff is not None and k_diff < 1.0)

# --- report wires kappa in only with >=2 scorers ---
rep1 = score.report(KEY, {"tien": perfect})
rep2 = score.report(KEY, {"tien": perfect, "other": disagree})
check("report: no kappa for a single scorer", "cohens_kappa" not in rep1)
check("report: kappa present for two scorers", "cohens_kappa" in rep2)

print("\n%d failing checks" % n_fail)
sys.exit(1 if n_fail else 0)
