"""Sealing + commitment hashes for a contradiction probe.

The point of sealing: prove the cases and their types were fixed BEFORE any run,
without showing them to the scorer or the respondent. You commit hashes publicly
(in the preregistration); the plaintext stays in gitignored `sealed/` until the
reveal, when it is re-hashed and must match.

Stdlib only.
"""
import hashlib
import json
import sys


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str) -> tuple[str, int]:
    with open(path, "rb") as fh:
        data = fh.read()
    return sha256_bytes(data), len(data)


def statement_hashes(cases: list[dict]) -> list[str]:
    """Per-statement SHA-256, sorted lexicographically so the ORDER reveals nothing
    about which items are contradictions (the prereg's type-blind commitment)."""
    hs = [sha256_bytes(c["statement"].encode("utf-8")) for c in cases]
    return sorted(hs)


def commitments(sealed_path: str) -> dict:
    """Everything the preregistration should commit for a sealed packet."""
    packet_sha, nbytes = sha256_file(sealed_path)
    with open(sealed_path, "r", encoding="utf-8") as fh:
        packet = json.load(fh)
    cases = packet["cases"]
    return {
        "sealed_packet_sha256": packet_sha,
        "sealed_packet_bytes": nbytes,
        "n_cases": len(cases),
        "n_contradiction": sum(1 for c in cases if c["type"] == "contradiction"),
        "n_control": sum(1 for c in cases if c["type"] != "contradiction"),
        "statement_sha256_lexicographic": statement_hashes(cases),
    }


def verify(sealed_path: str, expected_packet_sha256: str) -> bool:
    got, _ = sha256_file(sealed_path)
    return got == expected_packet_sha256


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -I seal.py <sealed.json> [expected_sha256]")
        sys.exit(2)
    c = commitments(sys.argv[1])
    print(json.dumps(c, indent=2))
    if len(sys.argv) >= 3:
        ok = verify(sys.argv[1], sys.argv[2])
        print("\nverify against committed hash:", "MATCH" if ok else "MISMATCH")
        sys.exit(0 if ok else 1)
