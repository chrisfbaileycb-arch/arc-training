#!/usr/bin/env python3
"""Verify local GGUF weights against models/cores.json (offline, read-only unless --pin)."""
import argparse, hashlib, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def sha256(p, progress=False):
    h, done, total = hashlib.sha256(), 0, os.path.getsize(p)
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c); done += len(c)
            if progress: print(f"\r  hashing {done * 100 // max(total, 1)}%", end="", file=sys.stderr, flush=True)
    if progress: print(file=sys.stderr)
    return h.hexdigest()

def verify(root, pin=False, only=None):
    path = os.path.join(root, "models", "cores.json")
    cfg = json.load(open(path)); bad = 0
    for name, core in cfg["cores"].items():
        if only and name not in only: continue
        full = os.path.join(root, core["file"])
        if not os.path.exists(full):
            print(f"[MISSING ] {name}: {core['file']}"); continue
        print(f"[checking] {name}")
        digest = sha256(full, progress=True); expected = core.get("sha256")
        if expected is None:
            print(f"[UNPINNED] {name}: sha256={digest}")
            if pin: core.update({"sha256": digest, "bytes": os.path.getsize(full)}); print("           pinned in cores.json")
        elif digest == expected: print(f"[OK      ] {name}")
        else: print(f"[MISMATCH] {name}: expected {expected} got {digest}"); bad += 1
    if pin:
        with open(path, "w") as f: json.dump(cfg, f, indent=2); f.write("\n")
    return 1 if bad else 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT); ap.add_argument("--core", action="append")
    ap.add_argument("--pin", action="store_true", help="write hashes for cores whose sha256 is null")
    a = ap.parse_args()
    sys.exit(verify(a.root, a.pin, set(a.core) if a.core else None))
