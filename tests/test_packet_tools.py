"""Both-ways tests for seal.py, lexical_baseline.py and present.py.
Run: python -I tests/test_packet_tools.py  (from repo root).

Same rule as tests/test_score.py: each check is driven in the direction that PASSES and the direction that must
FAIL. Added 2026-11-14 for three things these tools got wrong:

  * seal.py and lexical_baseline.py counted every case whose type was not "contradiction" as a control, while
    score.py refuses an unknown type. A typo in a type silently changed the seal's counts and the baseline.
    Both now refuse it, against the same list score.py uses (score.TYPES).
  * lexical_baseline.py crashed with a traceback on a packet with no cases.
  * present.py crashed with a traceback on a packet with no "record".

The packets here are synthetic and written to a temporary folder; no sealed material is read. The command-line
checks start the tools the documented way (`python -I <tool>.py ...`), so they also show that each tool still
starts in isolated mode. Stdlib only.
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import lexical_baseline  # noqa: E402
import present  # noqa: E402
import score  # noqa: E402
import seal  # noqa: E402

n_fail = 0


def check(name, cond):
    global n_fail
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        n_fail += 1


def outcome(fn):
    """('ok', value) if fn returns, else (exception class name, message). Never lets a crash end the file."""
    try:
        return "ok", fn()
    except Exception as e:  # noqa: BLE001 -- the kind of failure is what is being checked
        return type(e).__name__, str(e)


tmp = tempfile.mkdtemp(prefix="cp-tools-")


def write(name, obj):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)
    return path


def run(tool, *args):
    """Start a tool the documented way. Returns (exit code, stdout, stderr)."""
    p = subprocess.run([sys.executable, "-I", "-B", os.path.join(ROOT, tool)] + list(args),
                       capture_output=True, text=True, timeout=120)
    return p.returncode, p.stdout, p.stderr


def clean_refusal(rc, err, *needles):
    """A refusal a person can read: non-zero exit, no traceback, and the message names what is wrong."""
    return rc != 0 and "Traceback" not in err and all(n in err for n in needles)


PACKET = {
    "record": "On Tuesday the committee withdrew its claim that the bridge was finished in March.",
    "withdrawn_claim": "the bridge was finished in March",
    "cases": [
        {"id": "X1", "type": "contradiction", "statement": "Crews completed the crossing by early spring, as first announced."},
        {"id": "X2", "type": "contradiction", "statement": "The bridge was finished in March."},
        {"id": "N1", "type": "near-miss", "statement": "The claim that the bridge was finished in March was withdrawn."},
        {"id": "U1", "type": "unrelated", "statement": "The ferry timetable changed in June."},
    ],
}


def packet(**changes):
    """PACKET with some cases' types replaced: packet(N1="near miss")."""
    p = dict(PACKET, cases=[dict(c, type=changes.get(c["id"], c["type"])) for c in PACKET["cases"]])
    return p


good = write("good.json", PACKET)
typo_control = write("typo_control.json", packet(N1="near miss"))            # meant near-miss
typo_contra = write("typo_contra.json", packet(X2="contradictoin"))          # meant contradiction
no_cases = write("no_cases.json", dict(PACKET, cases=[]))
no_record = write("no_record.json", {k: v for k, v in PACKET.items() if k != "record"})
recordings = write("recordings.json", {"responses": {c["id"]: "reply to " + c["id"] for c in PACKET["cases"]}})

# --- a well-formed packet behaves as it always did ---
kind, c = outcome(lambda: seal.commitments(good))
check("seal: a well-formed packet is counted (4 cases, 2 contradictions, 2 controls)",
      kind == "ok" and (c["n_cases"], c["n_contradiction"], c["n_control"]) == (4, 2, 2))
kind, a = outcome(lambda: lexical_baseline.analyze(good))
check("baseline: a well-formed packet is analysed (4 rows, both arms have a range)",
      kind == "ok" and len(a["rows"]) == 4 and a["contradiction_overlap_range"] and a["control_overlap_range"])
for t in score.TYPES:
    one = write("one_%s.json" % t, dict(PACKET, cases=[dict(PACKET["cases"][0], type=t)]))
    check("seal and baseline both accept the declared type %r" % t,
          outcome(lambda: seal.commitments(one))[0] == "ok" and outcome(lambda: lexical_baseline.analyze(one))[0] == "ok")

# --- an unknown type is refused by both, naming the case and the value ---
# The failing direction, as it was: seal.commitments(typo_contra) returned n_contradiction 1, n_control 3 -- the
# typo moved a contradiction into the control arm and the commitment went out wrong, with no warning.
for label, path, cid, bad in (("a typo'd control type", typo_control, "N1", "near miss"),
                              ("a typo'd contradiction type", typo_contra, "X2", "contradictoin")):
    kind, msg = outcome(lambda: seal.commitments(path))
    check("seal: %s is refused, not counted as a control" % label, kind == "ValueError" and cid in msg and bad in msg)
    kind, msg = outcome(lambda: lexical_baseline.analyze(path))
    check("baseline: %s is refused, not counted as a control" % label, kind == "ValueError" and cid in msg and bad in msg)
    kind, msg = outcome(lambda: score.score_one(score.key_from_sealed(path), {}))
    check("...and score.py refuses the same packet (one list of types for all three)", kind == "ValueError" and bad in msg)

# --- from the command line: a clear message and a non-zero exit, no traceback ---
rc, out, err = run("seal.py", good)
check("seal.py CLI: a well-formed packet prints its commitments, exit 0",
      rc == 0 and json.loads(out)["n_control"] == 2)
rc, out, err = run("seal.py", typo_contra)
check("seal.py CLI: an unknown type exits non-zero with a message and prints no commitments",
      clean_refusal(rc, err, "X2", "contradictoin") and "sealed_packet_sha256" not in out)
rc, out, err = run("lexical_baseline.py", good)
check("lexical_baseline.py CLI: a well-formed packet prints the baseline, exit 0",
      rc == 0 and "best single-threshold accuracy" in out)
rc, out, err = run("lexical_baseline.py", typo_control)
check("lexical_baseline.py CLI: an unknown type exits non-zero with a message",
      clean_refusal(rc, err, "N1", "near miss") and "best single-threshold accuracy" not in out)

# --- a packet with no cases ---
kind, msg = outcome(lambda: lexical_baseline.analyze(no_cases))
check("baseline: a packet with no cases is refused with a reason (was an IndexError)", kind == "ValueError" and "no cases" in msg)
rc, out, err = run("lexical_baseline.py", no_cases)
check("lexical_baseline.py CLI: no cases -> a message and a non-zero exit, no traceback", clean_refusal(rc, err, "no cases"))

# --- a packet with no record ---
kind, built = outcome(lambda: present.build(good, recordings, 7))
check("present: a well-formed packet builds (record carried, 4 items, 4 codes, no types or ids shown)",
      kind == "ok" and built[0] == PACKET["record"] and len(built[1]) == 4 and len(built[2]) == 4
      and all(set(item) == {"code", "statement", "response"} for item in built[1]))
kind, msg = outcome(lambda: present.build(no_record, recordings, 7))
check("present: a packet with no record is refused with a reason (was a KeyError)", kind == "ValueError" and "record" in msg)
prefix = os.path.join(tmp, "out")
rc, out, err = run("present.py", no_record, recordings, "7", prefix)
check("present.py CLI: no record -> a message and a non-zero exit, no traceback, nothing written",
      clean_refusal(rc, err, "record") and not os.path.exists(prefix + "-scorer.json")
      and not os.path.exists(prefix + "-codemap.json"))
rc, out, err = run("present.py", good, recordings, "7", prefix)
check("present.py CLI: a well-formed packet writes the scorer packet and the code map, exit 0",
      rc == 0 and os.path.exists(prefix + "-scorer.json") and os.path.exists(prefix + "-codemap.json"))

print("\n%d failing checks" % n_fail)
sys.exit(1 if n_fail else 0)
