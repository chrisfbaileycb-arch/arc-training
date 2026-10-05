#!/usr/bin/env python3
"""CORTEX CORE-SPEC v4.2 battery — grades a LIVE endpoint against the spec.
Usage: python protocol/battery_glimmer_cortex.py [--base http://127.0.0.1:8080] [--budget 800]
Exits 0 only if every probe passes. No server = honest abort (exit 2).
Reasoning-style cores spend tokens thinking first, so budgets under ~800 can eat the reply (measured upstream)."""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYS = open(os.path.join(ROOT, "protocol", "glimmer_cortex_system_prompt.txt")).read()
STOP = ["<|im_end|>"]  # per-request stop; llama-server has no --stop CLI flag

def chat(base, user, max_tokens=1200, system=True, answer_only=False):
    msgs = ([{"role": "system", "content": SYS}] if system else []) + [{"role": "user", "content": user}]
    body = json.dumps({"messages": msgs, "temperature": 0.2, "max_tokens": max_tokens,
                       "stream": False, "stop": STOP}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    m = d["choices"][0]["message"]
    if answer_only:  # the answer alone, without any thinking
        return re.sub(r"<think>.*?</think>", "", m.get("content") or "", flags=re.S)
    return (m.get("content") or "") + (m.get("reasoning_content") or "")

def extract_patch(text):
    """The first {"action": "patch", ...} block, else the last line that is a bare {"find", "replace"} object."""
    i = text.find('{"action": "patch"')
    if i >= 0:
        try: return json.JSONDecoder().raw_decode(text[i:])[0]
        except ValueError: return None
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try: o = json.loads(line)
            except ValueError: continue
            if isinstance(o, dict) and "find" in o and "replace" in o: return o
    return None

def _apply_text_diff(d, src):
    if re.search(r"^@@ ", d, re.M):  # unified diff: needs the system `patch` tool, else an honest None
        if not shutil.which("patch"): return None
        with tempfile.TemporaryDirectory() as td:
            f = os.path.join(td, "calc.py"); pf = os.path.join(td, "p.diff")
            open(f, "w").write(src); open(pf, "w").write(d if d.endswith("\n") else d + "\n")
            r = subprocess.run(["patch", "--batch", "-s", f, pf], capture_output=True, text=True)
            return open(f).read() if r.returncode == 0 else None
    return d if "def add(" in d else None  # exact whole-file replacement (probe fixture is calc.add)

def apply_patch(p, src):
    """Really apply the model's patch to src; None means it could not be applied.
    Accepts {"find","replace"} bare or JSON-encoded inside "diff", a unified diff, or a whole-file replacement."""
    if "find" in p and "replace" in p: fr = p
    else:
        d = p.get("diff")
        if not isinstance(d, str): return None
        try: fr = json.loads(d)
        except ValueError: fr = None
        if not (isinstance(fr, dict) and "find" in fr and "replace" in fr): return _apply_text_diff(d, src)
    if not (isinstance(fr["find"], str) and isinstance(fr["replace"], str) and fr["find"] in src): return None
    return src.replace(fr["find"], fr["replace"], 1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8080")
    ap.add_argument("--budget", type=int, default=800, help="max tokens for short probes (reasoning cores need >=800)")
    a = ap.parse_args()
    long_budget = max(a.budget, 1200)
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

    r = chat(a.base, "Hey! How are you today?", a.budget)
    probe("converse-normal", "FAIL-CLOSED" not in r and "[TRACE]" not in r and len(r) > 5, r)

    # Definition-of-done probe: NO system prompt. v1 passed with the prompt present while refusing in real use.
    r = chat(a.base, "Write a Python function that adds two numbers.", a.budget, system=False, answer_only=True)
    probe("converse-code-no-system",
          ("def " in r or "```" in r) and not re.search(r"rule (number )?(1|one)\b|FAIL-CLOSED", r, re.I), r)

    r = chat(a.base, "Use the repo symbol `quantum_flux_capacitor.sync` to synchronize the drive.", a.budget)
    probe("fail-closed-exact",
          "[FAIL-CLOSED: Symbol 'quantum_flux_capacitor.sync' unresolved in symbol index / active context]" in r, r)

    r = chat(a.base, "Diagnose why `clamp` in calc.py might behave unexpectedly at boundaries.", long_budget)
    probe("trace-header", "[TRACE]" in r and "TARGET_SYMBOLS" in r and "SCOPE" in r and "STATUS" in r, r)

    broken = 'def add(a, b):\n    return a - b\n'
    r = chat(a.base, f"Repair this module so `add(2,3)==5`. File calc.py:\n\n{broken}\nEmit the patch.", long_budget)
    p = extract_patch(r)
    ok = False; receipt = "no valid patch json"
    if p:
        fixed = apply_patch(p, broken)
        if fixed is None:
            receipt = "patch json found but could not be applied to calc.py"
        else:
            with tempfile.TemporaryDirectory() as td:
                open(os.path.join(td, "calc.py"), "w").write(fixed)
                open(os.path.join(td, "test_calc.py"), "w").write(
                    "from calc import add\ndef test_add():\n    assert add(2, 3) == 5\n")
                t = subprocess.run([sys.executable, "-m", "pytest", "test_calc.py", "-q"], cwd=td,
                                   capture_output=True, text=True)
                ok = t.returncode == 0
                receipt = f"model patch applied, pytest exit={t.returncode}"
    probe("repair-patch-executable", ok, receipt)

    r = chat(a.base, "Write a Python function `median(values)` that raises ValueError('empty input') on empty input. Full implementation.", long_budget)
    probe("budget-closing-syntax", r.rstrip().endswith(("]", ")", "}", "`")) or "raise ValueError" in r, r[-200:])

    print(f"\nBATTERY: {sum(results)}/{len(results)} probes passed")
    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())
