#!/usr/bin/env python3
"""research_grade.py -- the research-grade checks, one portable file, standard library only (Python 3.9+).

    python -I research_grade.py                   # self-test, then every check; exit 0 only if all hold
    python -I research_grade.py --write-manifest  # re-pin every tracked file into MANIFEST.sha256

Ported 2026-11-07 from what the covenant and covenant-satc repositories learned the hard way. Each check
exists because its absence once let a wrong statement stand:

  R1  RETRACTIONS (docs/RETRACTED.json). A withdrawn claim may appear anywhere only if its retraction id is
      cited within `window` lines. Every pattern must still match inside the record, so no dead regex passes
      silently, and the scan reports how many files it read against a floor. An empty ledger is allowed: it
      means nothing has been withdrawn yet, not that the guard is untested -- the self-test drives the guard
      red and green on a synthetic retraction every run.
  C1  CLAIMS (docs/CLAIMS_INDEX.json). Each headline claim names its source file and the exact sentence that
      must stand there verbatim, how it is reproduced, and its reproduction status: custodian-run (the author
      ran it), externally-reproduced (someone else did, with evidence named), or not-reproducible-from-repo
      (the data is not shipped -- said, not hidden). Fail-closed: a missing field, a sentence no longer in its
      source, an unknown status, a reproduce script that does not exist, a data file not pinned, or a
      retraction id the ledger does not hold all fail.
  M1  MANIFEST (MANIFEST.sha256). Every tracked file is pinned by its LF-normalized sha256, so a Windows
      checkout (CRLF) and a Linux one hash alike. Any change not deliberately re-pinned fails.

What this cannot see (rule 9): whether a claim is TRUE. It checks that each claim is stated where it says,
tied to a way of reproducing it, honestly labelled, and that nothing withdrawn returns uncited. Regex is an
existence oracle; meaning is for reviewers. R1's known limit: a withdrawn sentence planted within `window`
lines of its own citation passes, because the rule is proximity.

No network, no model, no subprocess (except `git ls-files` to know what is tracked; a tree walk otherwise).
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

KIT_VERSION = "1.0.0"
STATUSES = {"custodian-run", "externally-reproduced", "not-reproducible-from-repo"}
CLAIM_FIELDS = ("id", "claim", "source", "exact", "reproduction_status", "limits")
SCAN_EXT = {".md", ".py", ".sh", ".ps1", ".json", ".txt", ".bat", ".html", ".yml", ".yaml", ".js", ".ts"}
SKIP_DIR = {".git", "__pycache__", "node_modules", ".venv", "venv", ".trash", ".pytest_cache"}
MANIFEST = "MANIFEST.sha256"
LEDGER_REL = "docs/RETRACTED.json"


class Report:
    def __init__(self, quiet=False):
        self.results, self.quiet = [], quiet

    def check(self, label, ok, detail=""):
        self.results.append(bool(ok))
        if not self.quiet:
            print("%s  %s%s" % ("ok  " if ok else "FAIL", label, "" if ok else "  -- " + str(detail)[:300]), flush=True)
        return bool(ok)

    @property
    def failed(self):
        return sum(1 for r in self.results if not r)


def lf_sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()


def tracked(root):
    """Tracked files (git), else every file under root; always relative, forward slashes, sorted."""
    try:
        out = subprocess.run(["git", "-C", root, "ls-files", "-z"], capture_output=True, check=True, timeout=60)
        names = [n for n in out.stdout.decode("utf-8", "replace").split("\0") if n]
        if names:
            return sorted(n for n in names if os.path.isfile(os.path.join(root, n)))
    except (OSError, subprocess.SubprocessError):
        pass
    found = []
    for d, ds, fs in os.walk(root):
        ds[:] = [x for x in ds if x not in SKIP_DIR]
        for f in fs:
            found.append(os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/"))
    return sorted(found)


def load_json(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- R1 retractions
def r1(root, rep):
    path = os.path.join(root, "docs", "RETRACTED.json")
    if not rep.check("R1.0 docs/RETRACTED.json exists and loads", os.path.isfile(path), path):
        return
    led = load_json(path)
    window, floor = int(led.get("window", 10)), int(led.get("coverage_floor", 1))
    rets = led.get("retractions", [])
    rep.check("R1.0 the ledger holds a list of retractions (empty means nothing withdrawn yet)", isinstance(rets, list))
    texts = {}
    for rel in tracked(root):
        if os.path.splitext(rel)[1].lower() in SCAN_EXT and not set(rel.split("/")) & SKIP_DIR:
            try:
                texts[rel] = io.open(os.path.join(root, rel), encoding="utf-8", errors="ignore").read()
            except OSError:
                pass
    rep.check("R1.V1 the scan read the tree (floor %d files)" % floor, len(texts) >= floor, "%d read" % len(texts))
    present = {r.split("/")[0] for r in texts}
    missing = [d for d in led.get("expect_dirs", []) if d not in present]
    rep.check("R1.V2 every directory the ledger expects was present to scan", not missing, missing)
    for r in rets:
        rid, allow = r.get("id", "?"), r.get("allow", [])
        pats = [re.compile(p, re.I) for p in r.get("patterns", [])]
        rep.check("R1.%s.0 declares patterns, an allow-list and the true statement" % rid,
                  bool(pats) and bool(allow) and bool(r.get("truth")))
        verbatim = r.get("verbatim", [])
        records = [a for a in allow if a != LEDGER_REL]
        dead, unrecorded, bad = [], [], []
        for rx in pats:
            in_record = 0
            for rel, text in texts.items():
                ok_file = any(rel == a or rel.startswith(a) for a in allow)
                if not rx.search(text):
                    continue
                if ok_file:
                    if rel != LEDGER_REL:
                        in_record += 1
                    continue
                lines = text.splitlines()
                for m in rx.finditer(text):
                    ln = text[:m.start()].count("\n")
                    if rid not in "\n".join(lines[max(0, ln - window): ln + window + 1]):
                        bad.append("%s:%d" % (rel, ln + 1))
            # L1: the ledger itself always "contains" its own wording, so matching there proves only that the
            # pattern fits the verbatim it was written for -- checked as exactly that, nothing more.
            if not any(rx.search(v) for v in verbatim):
                dead.append(rx.pattern)
            # L2: a record file other than the ledger, when one is named, must still hold the wording.
            if records and not in_record:
                unrecorded.append(rx.pattern)
        rep.check("R1.%s.L1 every pattern matches the verbatim wording it was written for" % rid,
                  bool(verbatim) and not dead, dead or "no verbatim given")
        rep.check("R1.%s.L2 every pattern still matches a record file other than the ledger (%s)"
                  % (rid, ", ".join(records) or "none named: the ledger is the only record"), not unrecorded, unrecorded)
        rep.check("R1.%s.C no file restates it without citing %s within %d lines" % (rid, rid, window), not bad, bad[:6])


# ---------------------------------------------------------------- C1 claims
def norm(s):
    return " ".join(s.split())


def c1(root, rep):
    path = os.path.join(root, "docs", "CLAIMS_INDEX.json")
    if not rep.check("C1.0 docs/CLAIMS_INDEX.json exists and loads", os.path.isfile(path), path):
        return
    idx = load_json(path)
    claims = idx.get("claims", [])
    rep.check("C1.0 the index holds a list of claims", isinstance(claims, list) and bool(claims), "no claims listed")
    ledger_path = os.path.join(root, "docs", "RETRACTED.json")
    ids = {r.get("id") for r in load_json(ledger_path).get("retractions", [])} if os.path.isfile(ledger_path) else set()
    pinned = read_manifest(root)
    seen = set()
    for c in claims:
        cid = c.get("id", "?")
        missing = [f for f in CLAIM_FIELDS if not c.get(f)]
        rep.check("C1.%s.0 every required field present and non-empty" % cid, not missing, missing)
        rep.check("C1.%s.1 id is unique" % cid, cid not in seen, cid)
        seen.add(cid)
        src = os.path.join(root, c.get("source", ""))
        found = os.path.isfile(src) and norm(c.get("exact", "")) in norm(io.open(src, encoding="utf-8", errors="ignore").read())
        rep.check("C1.%s.2 the exact sentence stands verbatim in %s" % (cid, c.get("source")), found, c.get("exact", "")[:80])
        st = c.get("reproduction_status")
        rep.check("C1.%s.3 status is one of %s" % (cid, sorted(STATUSES)), st in STATUSES, st)
        if st == "externally-reproduced":
            rep.check("C1.%s.4 an external reproduction names its evidence" % cid, bool(c.get("external_evidence")))
        if st == "custodian-run":
            script = next((t for t in str(c.get("reproduce", "")).split() if t.endswith((".py", ".sh", ".js"))), None)
            rep.check("C1.%s.5 a custodian-run claim names a reproduce script that exists" % cid,
                      bool(script) and os.path.isfile(os.path.join(root, script)), c.get("reproduce"))
        if st == "not-reproducible-from-repo":
            rep.check("C1.%s.6 an unreproducible claim says why" % cid, bool(c.get("why_not")))
        unpinned = [d for d in c.get("data", []) if d not in pinned]
        rep.check("C1.%s.7 every data file it rests on is pinned in %s" % (cid, MANIFEST), not unpinned, unpinned)
        unknown = [t for t in c.get("tombstones", []) if t not in ids]
        rep.check("C1.%s.8 every retraction it cites is in the ledger" % cid, not unknown, unknown)


# ---------------------------------------------------------------- M1 manifest
def read_manifest(root):
    path = os.path.join(root, MANIFEST)
    out = {}
    if os.path.isfile(path):
        for line in io.open(path, encoding="utf-8"):
            m = re.match(r"^([0-9a-f]{64})\s+(.+?)\s*$", line)
            if m:
                out[m.group(2)] = m.group(1)
    return out


def write_manifest(root):
    names = [n for n in tracked(root) if n != MANIFEST]
    with io.open(os.path.join(root, MANIFEST), "w", encoding="utf-8", newline="\n") as fh:
        for n in names:
            fh.write("%s  %s\n" % (lf_sha256(os.path.join(root, n)), n))
    return len(names)


def m1(root, rep):
    pins = read_manifest(root)
    if not rep.check("M1.0 %s exists and pins at least one file" % MANIFEST, bool(pins)):
        return
    names = [n for n in tracked(root) if n != MANIFEST]
    unpinned = [n for n in names if n not in pins]
    gone = [n for n in pins if not os.path.isfile(os.path.join(root, n))]
    changed = [n for n in names if n in pins and lf_sha256(os.path.join(root, n)) != pins[n]]
    rep.check("M1.1 every tracked file is pinned", not unpinned, unpinned[:6])
    rep.check("M1.2 every pinned file exists", not gone, gone[:6])
    rep.check("M1.3 every pinned file matches its LF-normalized sha256", not changed, changed[:6])


# ---------------------------------------------------------------- self-test: each check driven both ways
def selftest(rep):
    tmp = tempfile.mkdtemp(prefix="rg-selftest-")
    try:
        def w(rel, text, crlf=False):
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with io.open(p, "w", encoding="utf-8", newline="\r\n" if crlf else "\n") as fh:
                fh.write(text)

        def fails(fn):
            r = Report(quiet=True)
            fn(tmp, r)
            return r.failed > 0

        entry = {"id": "X1", "claim": "the moon is cheese", "verbatim": ["The moon is cheese."],
                 "patterns": ["moon\\s+is\\s+cheese"], "allow": ["docs/RETRACTED.json", "docs/CORRECTIONS.md"],
                 "truth": "it is rock"}
        w("docs/RETRACTED.json", json.dumps({"window": 2, "coverage_floor": 1, "retractions": [entry]}))
        w("docs/CORRECTIONS.md", "X1: we said the moon is cheese. Wrong.\n")
        w("notes.md", "a\nb\nc\nd\ne\nThe moon is cheese.\n")
        rep.check("SELF.R1 a withdrawn sentence with no citation nearby turns R1 red", fails(r1))
        w("notes.md", "a\nb\nc\nd\ne\nThe moon is cheese (retracted, X1).\n")
        rep.check("SELF.R1 ...citing the retraction beside it turns R1 green", not fails(r1))
        w("docs/CORRECTIONS.md", "nothing here\n")
        rep.check("SELF.R1 ...the record file losing the wording turns R1 red (L2), the ledger alone is not enough",
                  fails(r1))
        w("docs/CORRECTIONS.md", "X1: we said the moon is cheese. Wrong.\n")
        w("docs/RETRACTED.json", json.dumps({"window": 2, "coverage_floor": 1,
                                             "retractions": [dict(entry, patterns=["moon\\s+is\\s+chese"])]}))
        rep.check("SELF.R1 ...a typo'd pattern that fits no verbatim is a dead regex: red (L1)", fails(r1))
        w("docs/RETRACTED.json", json.dumps({"window": 2, "coverage_floor": 1, "retractions": [entry]}))
        rep.check("SELF.R1 ...restored, green again", not fails(r1))
        w("docs/RETRACTED.json", json.dumps({"window": 2, "coverage_floor": 1, "retractions": []}))
        rep.check("SELF.R1 ...an empty ledger is green (nothing withdrawn yet)", not fails(r1))

        w("tool.py", "print(1)\n")
        w("README.md", "We measured   12/20 hits.\n")
        good = {"id": "K1", "claim": "12/20 hits", "source": "README.md", "exact": "We measured 12/20 hits.",
                "reproduction_status": "custodian-run", "reproduce": "python tool.py", "limits": "one run"}
        w("docs/CLAIMS_INDEX.json", json.dumps({"claims": [good]}))
        rep.check("SELF.C1 a well-formed claim is green (whitespace-normalized match)", not fails(c1))
        for label, mut in (("the sentence changed in its source", {"exact": "We measured 13/20 hits."}),
                           ("an unknown status", {"reproduction_status": "probably"}),
                           ("externally-reproduced with no evidence", {"reproduction_status": "externally-reproduced"}),
                           ("a reproduce script that does not exist", {"reproduce": "python gone.py"}),
                           ("not-reproducible with no reason", {"reproduction_status": "not-reproducible-from-repo"}),
                           ("a data file not in the manifest", {"data": ["data/x.csv"]}),
                           ("a retraction id the ledger lacks", {"tombstones": ["Z9"]}),
                           ("an empty limits field", {"limits": ""})):
            w("docs/CLAIMS_INDEX.json", json.dumps({"claims": [dict(good, **mut)]}))
            rep.check("SELF.C1 ...%s turns C1 red" % label, fails(c1))
        w("docs/CLAIMS_INDEX.json", json.dumps({"claims": [good, dict(good)]}))
        rep.check("SELF.C1 ...a duplicate id turns C1 red", fails(c1))

        w("data.csv", "a,b\n1,2\n")
        write_manifest(tmp)
        rep.check("SELF.M1 a freshly written manifest is green", not fails(m1))
        w("data.csv", "a,b\n1,2\n", crlf=True)
        rep.check("SELF.M1 ...the same file with CRLF line endings is still green", not fails(m1))
        w("data.csv", "a,b\n1,3\n")
        rep.check("SELF.M1 ...one changed byte turns M1 red", fails(m1))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    root = os.path.dirname(os.path.abspath(__file__))
    if "--write-manifest" in argv:
        print("wrote %s over %d tracked files" % (MANIFEST, write_manifest(root)))
        return 0
    rep = Report()
    print("research_grade %s -- self-test (each check driven both ways)" % KIT_VERSION)
    selftest(rep)
    print("\nR1 retractions")
    r1(root, rep)
    print("\nC1 claims")
    c1(root, rep)
    print("\nM1 manifest")
    m1(root, rep)
    ok = len(rep.results) - rep.failed
    print("\nresearch_grade: %d/%d passed" % (ok, len(rep.results)))
    return 0 if rep.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
