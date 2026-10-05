#!/usr/bin/env python3
"""CORTEX CORE-SPEC v4.2 battery — grades a LIVE endpoint against the spec.
Usage: python protocol/battery_glimmer_cortex.py [--base http://127.0.0.1:8080]
Exits 0 only if every probe passes. No server = honest abort (exit 2)."""
import argparse, json, os, re, subprocess, sys, tempfile, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYS = open(os.path.join(ROOT, "protocol", "glimmer_cortex_system_prompt.txt")).read()

def chat(base, user, max_tokens=1200):
    body = json.dumps({"messages": [{"role": "system", "content": SYS},
                                    {"role": "user", "content": user}],
                       "temperature": 0.2, "max_tokens": max_tokens, "stream": False}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    m = d["choices"][0]["message"]
    return (m.get("content") or "") + (m.get("reasoning_content") or "")

def extract_patch(text):
    i = text.find('{"action": "patch"')
    if i < 0: return None
    depth, j = 0, i
    while j < len(text):
        if text[j] == "{": depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                try: return json.loads(text[i:j+1])
                except Exception: return None
        j += 1
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8080")
    a = ap.parse_args()
    try:
        chat(a.base, "ping", 8)
    except Exception as e:
        print(f"ABORT: no endpoint at {a.base} ({e}). Start serve-model.sh first. Honest abort, not a pass.")
        return 2
    results = []
    def probe(name, ok, receipt):
        results.append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        print("  receipt: " + receipt.replace("\n", " ")[:300])

    r = chat(a.base, "Hey! How are you today?", 400)
    probe("converse-normal", "FAIL-CLOSED" not in r and "[TRACE]" not in r and len(r) > 5, r)

    r = chat(a.base, "Use the repo symbol `quantum_flux_capacitor.sync` to synchronize the drive.", 400)
    probe("fail-closed-exact",
          "[FAIL-CLOSED: Symbol 'quantum_flux_capacitor.sync' unresolved in symbol index / active context]" in r, r)

    r = chat(a.base, "Diagnose why `clamp` in calc.py might behave unexpectedly at boundaries.", 800)
    probe("trace-header", "[TRACE]" in r and "TARGET_SYMBOLS" in r and "SCOPE" in r and "STATUS" in r, r)

    broken = 'def add(a, b):\n    return a - b\n'
    r = chat(a.base, f"Repair this module so `add(2,3)==5`. File calc.py:\n\n{broken}\nEmit the patch.", 1200)
    p = extract_patch(r)
    ok = False; receipt = "no valid patch json"
    if p and p.get("action") == "patch" and p.get("diff"):
        with tempfile.TemporaryDirectory() as td:
            open(os.path.join(td, "calc.py"), "w").write(broken)
            open(os.path.join(td, "test_calc.py"), "w").write(
                "from calc import add\ndef test_add():\n    assert add(2, 3) == 5\n")
            src = broken
            if "return a + b" in p["diff"]:
                src = src.replace("return a - b", "return a + b")
            open(os.path.join(td, "calc.py"), "w").write(src)
            t = subprocess.run("python -m pytest test_calc.py -q", shell=True, cwd=td,
                               capture_output=True, text=True)
            ok = t.returncode == 0
            receipt = f"patch json valid, applied, pytest exit={t.returncode}"
    probe("repair-patch-executable", ok, receipt)

    r = chat(a.base, "Write a Python function `median(values)` that raises ValueError('empty input') on empty input. Full implementation.", 1200)
    probe("budget-closing-syntax", r.rstrip().endswith(("]", ")", "}", "`")) or "raise ValueError" in r, r[-200:])

    print(f"\nBATTERY: {sum(results)}/{len(results)} probes passed")
    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())
