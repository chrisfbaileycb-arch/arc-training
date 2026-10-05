#!/usr/bin/env python3
"""THE ONLY online component. Fetches pinned GGUF cores, verifies sha256 against cores.json
when pre-pinned (refuses mismatches), pins hashes otherwise. Runtime never downloads."""
import argparse, hashlib, json, os, sys, urllib.request
ROOT = os.path.dirname(os.path.abspath(__file__))
CORES = os.path.join(ROOT, "models", "cores.json"); WEIGHTS = os.path.join(ROOT, "models", "weights")
CHUNK = 1 << 22
def api_list(repo):
    with urllib.request.urlopen(f"https://huggingface.co/api/models/{repo}", timeout=30) as r:
        return [s["rfilename"] for s in json.load(r).get("siblings", [])]
def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(CHUNK), b""): h.update(c)
    return h.hexdigest()
def fetch(repo, fname, dest):
    have = os.path.getsize(dest) if os.path.exists(dest) else 0
    url = f"https://huggingface.co/{repo}/resolve/main/{fname}"
    req = urllib.request.Request(url)
    if have: req.add_header("Range", f"bytes={have}-")
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "ab" if have else "wb") as f:
        total = have
        while True:
            c = r.read(CHUNK)
            if not c: break
            f.write(c); total += len(c); print(f"\r  {total/1e9:.2f} GB", end="", flush=True)
    print(); return total
def main():
    cores = json.load(open(CORES))
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", required=True, choices=list(cores["cores"].keys()))
    ap.add_argument("--quant", default=None); ap.add_argument("--with-companions", action="store_true")
    a = ap.parse_args()
    entry = cores["cores"][a.core]; quant = (a.quant or entry["quant"]).lower()
    if entry.get("state") == "planned":
        print(f"{a.core} is PLANNED (not yet trained). See training/JOB-LAUNCH.md."); sys.exit(3)
    print(f"[1/3] Listing .gguf files in {entry['repo']} ...")
    files = [f for f in api_list(entry["repo"]) if f.endswith(".gguf")]
    picks = [f for f in files if quant in f.lower()]
    if entry.get("match"): picks = [f for f in picks if entry["match"].lower() in f.lower()]
    if not picks:
        print("No match. Available:"); [print("  ", f) for f in files]; sys.exit(1)
    fname = sorted(picks)[0]; os.makedirs(WEIGHTS, exist_ok=True)
    dest = os.path.join(WEIGHTS, fname)
    print(f"[2/3] Downloading {fname} ..."); nbytes = fetch(entry["repo"], fname, dest)
    print("[3/3] Hashing ..."); digest = sha256(dest)
    expected = entry.get("sha256")
    if expected and digest != expected:
        print("INTEGRITY FAILURE: downloaded hash != pinned hash")
        print(f"  expected: {expected}\n  got     : {digest}"); sys.exit(2)
    entry.update({"file": f"models/weights/{fname}", "bytes": nbytes, "sha256": digest,
                  "state": "verified" if expected else "downloaded"})
    if a.with_companions and entry.get("companions"):
        got = entry.setdefault("companion_files", {})
        for key, sub in entry["companions"].items():
            cands = [f for f in files if sub.lower() in f.lower()]
            if cands:
                cd = os.path.join(WEIGHTS, cands[0]); print(f"[companion] {cands[0]} ...")
                fetch(entry["repo"], cands[0], cd); got[key] = f"models/weights/{cands[0]}"
    json.dump(cores, open(CORES, "w"), indent=2)
    verdict = "VERIFIED against pinned hash" if expected else "pinned (hash now recorded)"
    print(f"DONE {fname} {nbytes/1e9:.2f} GB — {verdict}\nsha256: {digest}")
if __name__ == "__main__": main()
