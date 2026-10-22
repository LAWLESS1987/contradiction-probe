"""Produce a type-blind scoring packet for a blind scorer, from raw recordings.

A recordings file (gitignored) maps each sealed case id to the respondent's RAW response:
  {"responses": {"X1": "...model's reply...", "N3": "...", ...}}

This emits the packet the scorer sees: statement + response, in a SHUFFLED order under
fresh codes R1..Rn, with NO types and NO original ids. It also writes the code->id map to a
SEPARATE operator-only file (gitignored) so grades can be mapped back after scoring.

Shuffle is seeded so it is reproducible and auditable, but the seed is chosen by the operator
at run time (not derivable from the data). Stdlib only.
"""
import json
import random
import sys


def build(sealed_path: str, recordings_path: str, seed: int):
    with open(sealed_path, "r", encoding="utf-8") as fh:
        pkt = json.load(fh)
    with open(recordings_path, "r", encoding="utf-8") as fh:
        rec = json.load(fh)["responses"]
    stmt = {c["id"]: c["statement"] for c in pkt["cases"]}
    ids = [cid for cid in stmt if cid in rec]
    rng = random.Random(seed)
    rng.shuffle(ids)
    packet, code_map = [], {}
    for i, cid in enumerate(ids, 1):
        code = "R%d" % i
        code_map[code] = cid
        packet.append({"code": code, "statement": stmt[cid], "response": rec[cid]})
    return pkt["record"], packet, code_map


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("usage: python -I present.py <sealed.json> <recordings.json> <seed> [out_prefix]")
        sys.exit(2)
    record, packet, code_map = build(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    prefix = sys.argv[4] if len(sys.argv) >= 5 else "sealed/packet"
    with open(prefix + "-scorer.json", "w", encoding="utf-8") as fh:
        json.dump({"record": record, "items": packet}, fh, indent=2)
    with open(prefix + "-codemap.json", "w", encoding="utf-8") as fh:
        json.dump(code_map, fh, indent=2)
    print("wrote %s-scorer.json (%d items, type-blind) and %s-codemap.json (operator only)"
          % (prefix, len(packet), prefix))
