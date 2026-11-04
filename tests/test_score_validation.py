"""Both-ways tests for the input validation added to score.py (E / Codex #10.5). Run:

    python -I tests/test_score_validation.py    (from repo root)

Each guard is driven in the direction that PASSES and the direction that must RAISE, so a green is earned.
Before this, a grade like 'TYPO' silently counted as a correct rejection (unresolved=0, missing=0), and an
unknown case type was silently treated as a control.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score  # noqa: E402

KEY = {"X1": "contradiction", "N1": "near-miss", "U1": "unrelated"}
n_fail = 0


def check(name, cond):
    global n_fail
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        n_fail += 1


def raises(name, fn):
    global n_fail
    try:
        fn()
        print("FAIL " + name + " -> did not raise")
        n_fail += 1
    except ValueError:
        print("ok   " + name + " -> raises ValueError")
    except Exception as e:                                   # noqa: BLE001
        print("FAIL " + name + " -> raised %s, not ValueError" % type(e).__name__)
        n_fail += 1


# --- valid input still scores exactly as documented (the fix does not change correct behaviour) ---
r = score.score_one(KEY, {"X1": "FLAGGED", "N1": "NOT FLAGGED", "U1": "UNRESOLVED"})
check("valid: contradiction FLAGGED -> 1 hit", r["hits"] == 1)
check("valid: control NOT FLAGGED + UNRESOLVED -> 2 correct rejects", r["correct_rejections"] == 2)
check("valid: UNRESOLVED counted once", r["unresolved"] == 1)

# --- the bug: an invalid grade must RAISE, not silently read as NOT FLAGGED ---
raises("invalid grade 'TYPO'", lambda: score.score_one(KEY, {"X1": "FLAGGED", "N1": "TYPO", "U1": "NOT FLAGGED"}))
raises("Codex repro: 'TYPO' on a lone control", lambda: score.score_one({"C1": "near-miss"}, {"C1": "TYPO"}))

# --- unknown case type must RAISE, not be silently a control ---
raises("unknown case type in key", lambda: score.score_one({"Z1": "contradicton"}, {"Z1": "FLAGGED"}))
raises("is_control on an unknown type", lambda: score.is_control("bogus"))
check("is_control: contradiction is NOT a control", score.is_control("contradiction") is False)
check("is_control: near-miss IS a control", score.is_control("near-miss") is True)
check("is_control: unrelated IS a control", score.is_control("unrelated") is True)

# --- a grade for an id not in the key must RAISE (reported), not be silently dropped ---
raises("grade id not in the key", lambda: score.score_one(KEY, {"X1": "FLAGGED", "GHOST": "FLAGGED"}))

# --- a MISSING grade (id absent from grades) stays the documented conservative UNRESOLVED, NOT an error ---
r2 = score.score_one(KEY, {"X1": "FLAGGED"})                 # N1, U1 absent
check("missing grade is not an error", r2["missing_grades"] == 2)
check("missing grade counts as UNRESOLVED", r2["unresolved"] == 2)

print("\n%d failing checks" % n_fail)
sys.exit(1 if n_fail else 0)
