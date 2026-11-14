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


# --- input validation (2026-11-04, collective issue #10 finding 5) ---
def raises(fn):
    try:
        fn()
    except ValueError as e:
        return str(e)
    return None


# The reproduction: a TYPO grade on a control used to read as a correct rejection with
# unresolved=0 and missing_grades=0. It must now be refused, naming the case and the value.
msg = raises(lambda: score.score_one(KEY, dict(perfect, N1="TYPO")))
check("invalid grade 'TYPO' is refused", msg is not None and "N1" in msg and "TYPO" in msg)
msg = raises(lambda: score.score_one(KEY, dict(perfect, X1="flagged")))
check("wrong-case grade 'flagged' is refused (no silent miss)", msg is not None and "X1" in msg)
msg = raises(lambda: score.score_one(dict(KEY, N2="near miss"), perfect))
check("unknown case type is refused, not counted as a control", msg is not None and "near miss" in msg)
msg = raises(lambda: score.is_control("contradictoin"))
check("is_control refuses an unknown type", msg is not None)
msg = raises(lambda: score.score_one(KEY, dict(perfect, Z9="FLAGGED")))
check("graded id not in the key is refused and named", msg is not None and "Z9" in msg)
msg = raises(lambda: score.report(KEY, {"tien": perfect, "other": dict(disagree, U1="?")}))
check("report refuses a bad sheet from any scorer", msg is not None and "U1" in msg)
# The other direction: what was valid stays valid and scores the same.
check("valid sheet still scores (no false refusal)", raises(lambda: score.score_one(KEY, perfect)) is None)
r = score.score_one(KEY, dict(perfect, N1=None))
check("explicit null is still MISSING -> UNRESOLVED (documented policy)",
      r["missing_grades"] == 1 and r["unresolved"] == 1 and r["correct_rejections"] == 3)
check("all three declared types accepted", all(not raises(lambda t=t: score.is_control(t)) for t in score.TYPES))

# --- kappa: an explicit null grade and a missing grade are the same thing (2026-11-14) ---
# Scoring counts both as UNRESOLVED (the "explicit null" check above). cohens_kappa used to default only the
# MISSING one, so a null on one sheet and an absence on the other read as a disagreement.
#   ids x, y.   A: x = null, y = FLAGGED.   B: x absent, y = FLAGGED.   Both sheets say (UNRESOLVED, FLAGGED).
#   observed agreement po = 2/2 = 1
#   each scorer's shares: UNRESOLVED 1/2, FLAGGED 1/2  ->  chance agreement pe = 1/2*1/2 + 1/2*1/2 = 1/2
#   kappa = (po - pe) / (1 - pe) = (1 - 1/2) / (1 - 1/2) = 1
#   (The old code read A's x as matching no grade: po = 1/2, pe = 1/4, kappa = 1/3.)
k_null = score.cohens_kappa({"x": None, "y": "FLAGGED"}, {"y": "FLAGGED"}, ["x", "y"])
check("kappa: an explicit null and a missing grade are both UNRESOLVED -> 1.0 (was 0.333)",
      k_null is not None and abs(k_null - 1.0) < 1e-9)

# --- pinned numbers (2026-11-14): a mutated chance term or false-alarm rate must turn this file red ---
# Before this, kappa was only checked for "== 1.0 when identical" and "< 1.0 when not", and the false-alarm
# rate only for 0.0, so changing either formula left every check green.
#
# Kappa, ten items, by hand.  F = FLAGGED, N = NOT FLAGGED, U = UNRESOLVED.
#   item    1  2  3  4  5  6  7  8  9  10
#   A       F  F  F  F  F  N  N  N  U  U      A's shares: F 5/10, N 3/10, U 2/10
#   B       F  F  F  N  N  N  N  U  U  U      B's shares: F 3/10, N 4/10, U 3/10
#   agree   y  y  y  .  .  y  y  .  y  y      observed agreement po = 7/10
#   chance agreement pe = 0.5*0.3 + 0.3*0.4 + 0.2*0.3 = 0.15 + 0.12 + 0.06 = 0.33
#   kappa = (po - pe) / (1 - pe) = (0.70 - 0.33) / (1 - 0.33) = 0.37 / 0.67 = 37/67 = 0.5522...
# The two scorers' shares differ on purpose: with equal shares pa*pb and pa*pa are the same number, and a
# mutated chance term would hide behind that.
F, N, U = "FLAGGED", "NOT FLAGGED", "UNRESOLVED"
ten = ["i%d" % n for n in range(1, 11)]
sheet_a = dict(zip(ten, [F, F, F, F, F, N, N, N, U, U]))
sheet_b = dict(zip(ten, [F, F, F, N, N, N, N, U, U, U]))
k_pin = score.cohens_kappa(sheet_a, sheet_b, ten)
check("kappa pinned: the ten-item example is 37/67 = 0.5522...", k_pin is not None and abs(k_pin - 37 / 67) < 1e-9)
k_pin_swapped = score.cohens_kappa(sheet_b, sheet_a, ten)
check("kappa pinned: the same value with the two scorers swapped", k_pin_swapped is not None and abs(k_pin_swapped - 37 / 67) < 1e-9)

# False-alarm rate, by hand.  2 contradictions and 4 controls -- unequal on purpose, so dividing by the wrong
# arm's size shows.
#   C1 FLAGGED (hit)   C2 NOT FLAGGED (miss)
#   K1 FLAGGED (false alarm)   K2 NOT FLAGGED   K3 UNRESOLVED   K4 no grade     (three correct rejections)
#   false-alarm rate = 1 false alarm / 4 controls = 0.25        hit rate = 1 hit / 2 contradictions = 0.5
# Then flag K2 and K3 as well: 3 false alarms / 4 controls = 0.75, one correct rejection; the hit rate stays 0.5.
KEY_2_4 = {"C1": "contradiction", "C2": "contradiction",
           "K1": "near-miss", "K2": "near-miss", "K3": "unrelated", "K4": "unrelated"}
one_fa = {"C1": F, "C2": N, "K1": F, "K2": N, "K3": U}
r = score.score_one(KEY_2_4, one_fa)
check("false alarms pinned: 1 false alarm, 3 correct rejections, 4 controls",
      r["false_alarms"] == 1 and r["correct_rejections"] == 3 and r["n_control"] == 4)
check("false-alarm rate pinned: 1/4 == 0.25", r["false_alarm_rate"] == 0.25)
check("hit rate pinned: 1/2 == 0.5", r["hit_rate"] == 0.5)
r = score.score_one(KEY_2_4, dict(one_fa, K2=F, K3=F))
check("false-alarm rate pinned: 3/4 == 0.75 (hit rate still 0.5)",
      r["false_alarm_rate"] == 0.75 and r["hit_rate"] == 0.5 and r["correct_rejections"] == 1)

print("\n%d failing checks" % n_fail)
sys.exit(1 if n_fail else 0)
