#!/usr/bin/env python3
"""AWAKE (resolve->verify->trace->load) and REST (hash->ledger->re-index)."""
import argparse, hashlib, json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "symbols", "symbol_index.json")
LEDGER = os.path.join(ROOT, "memories", "audit_ledger.jsonl")
def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()
def load_index():
    if not os.path.exists(INDEX):
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_symbol_index.py")], check=True)
    return json.load(open(INDEX))
def resolve(intent):
    idx = load_index()
    words = set(intent.lower().replace("_", " ").replace(".", " ").replace("-", " ").split())
    best, best_score = None, 0.0
    for sid, meta in idx["symbols"].items():
        terms = set(sid.lower().replace("_", " ").replace(".", " ").split()) | {t.lower() for t in meta.get("tags", [])}
        score = len(words & terms) / max(1, len(terms))
        if score > best_score: best, best_score = sid, score
    return best, best_score
def awake(intent):
    sid, score = resolve(intent)
    if not sid or score <= 0:
        print("[AWAKE TRACE] " + json.dumps({"state": "AWAKE", "intent": intent, "resolved": None,
                                             "action": "refuse-and-propose-repair"}))
        print("No physical symbol covers this intent. Filing repair proposal instead of guessing.")
        return 2
    meta = load_index()["symbols"][sid]
    full = os.path.join(ROOT, meta["path"]); d = sha256(full)
    ok = d == meta["sha256"]
    print("[AWAKE TRACE] " + json.dumps({"state": "AWAKE", "intent": intent, "symbol": sid,
          "path": meta["path"], "sha256": d, "integrity": ok, "score": round(score, 3)}))
    if not ok:
        print("INTEGRITY FAILURE: hash differs from index."); return 3
    print("----- grounded content loaded from disk -----")
    print(open(full).read())
    return 0
def rest():
    idx = load_index(); changed = []
    for sid, meta in idx["symbols"].items():
        full = os.path.join(ROOT, meta["path"])
        if os.path.exists(full):
            d = sha256(full)
            if d != meta["sha256"]: changed.append({"symbol": sid, "old": meta["sha256"], "new": d})
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    open(LEDGER, "a").write(json.dumps({"event": "rest", "changed": changed,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\n")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_symbol_index.py")],
                       capture_output=True, text=True)
    print("[REST] ledger appended; " + r.stdout.strip())
    return 0
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("state", choices=["awake", "rest"])
    ap.add_argument("intent", nargs="?", default="")
    a = ap.parse_args()
    if a.state == "awake":
        if not a.intent: print("usage: engine_lifecycle.py awake \"<intent>\""); sys.exit(64)
        sys.exit(awake(a.intent))
    sys.exit(rest())
