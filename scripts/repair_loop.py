#!/usr/bin/env python3
"""Genetic-improvement repair (pyggi-style), fully offline. Fitness is REAL: test_command exit 0."""
import argparse, json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "memories", "audit_ledger.jsonl")
OPERATORS = [("sub_to_add"," - "," + "),("add_to_sub"," + "," - "),("mul_to_div"," * "," / "),
             ("div_to_mul"," / "," * "),("lt_to_le"," < "," <= "),("gt_to_ge"," > "," >= "),
             ("eq_to_ne"," == "," != "),("ne_to_eq"," != "," == "),("le_to_lt"," <= "," < "),
             ("ge_to_gt"," >= "," > ")]
def run_tests(d, cmd):
    try:
        r = subprocess.run(cmd, shell=True, cwd=d, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    except subprocess.TimeoutExpired:
        return 0.0, "timeout"  # a hung mutant is just unfit, never a crash that strands a mutated file
    return (1.0 if r.returncode == 0 else 0.0), r.stdout.decode(errors="replace")
def ledger(e):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    e = dict(e); e["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(LEDGER, "a") as f: f.write(json.dumps(e) + "\n")
def mutants(src):
    lines = src.splitlines(keepends=True)
    for i, line in enumerate(lines):
        for name, a, b in OPERATORS:
            if a in line:
                cand = list(lines); cand[i] = line.replace(a, b, 1)
                yield {"op": name, "line": i + 1}, "".join(cand)
def repair(target):
    cfg = json.load(open(os.path.join(target, ".aegis.config")))
    fit0, _ = run_tests(target, cfg["test_command"])
    ledger({"event": "repair_start", "target": target, "baseline_fitness": fit0})
    print(f"[repair] baseline fitness = {fit0}")
    if fit0 == 1.0:
        print("[repair] already passing"); return 0
    for tf in cfg["target_files"]:
        fp = os.path.join(target, tf)
        with open(fp) as f: orig = f.read()
        fixed = False
        try:
            for meta, cand in mutants(orig):
                with open(fp, "w") as f: f.write(cand)
                fit, _ = run_tests(target, cfg["test_command"])
                ledger({"event": "mutant", "file": tf, "fitness": fit, **meta})
                if fit == 1.0:
                    fixed = True
                    print(f"[repair] FIXED by {meta['op']} at {tf}:{meta['line']}")
                    ledger({"event": "repair_success", "file": tf, **meta}); return 0
        finally:
            if not fixed:  # any exit (exhausted, crash, Ctrl+C) leaves the original, never a mutant
                with open(fp, "w") as f: f.write(orig)
    print("[repair] no passing mutant; original restored")
    ledger({"event": "repair_failed", "target": target}); return 1
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--target", required=True)
    sys.exit(repair(ap.parse_args().target))
