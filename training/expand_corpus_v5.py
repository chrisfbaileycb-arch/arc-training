#!/usr/bin/env python3
"""Expand corpus_v5_muse_cortex_full.jsonl with card-grounded rows (per-class,
per-function, per-method, per-module from the REAL extraction cards) plus extra
converse/trace/repair/ledger/class rows. Re-runs all gates. Idempotent."""
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL = os.path.join(ROOT, "training", "corpus_v5_muse_cortex_full.jsonl")
FORBIDDEN = ["quantum_flux_capacitor", "return a - b", "def add(a, b):"]

rows = [json.loads(l) for l in open(FULL)]
SYS = rows[0]["messages"][0]["content"]
seen = set()
for r in rows:
    seen.add(r["messages"][1]["content"])

def ex(user, assistant):
    return {"messages": [{"role": "system", "content": SYS},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}]}

hist = {}
added = []
def put(block, user, assistant):
    if user in seen: return
    seen.add(user); added.append(ex(user, assistant)); hist[block] = hist.get(block, 0) + 1

def trace(sym, scope, body):
    return "[TRACE]\n- TARGET_SYMBOLS: [" + sym + "]\n- SCOPE: [" + scope + "]\n- STATUS: [GROUNDED]\n\n" + body

def doc(text, cap=240):
    t = (text or "").strip().split("\n")[0]
    return t[:cap] if t else "No docstring on file — signature and structure are the contract of record."

# ---------- per-class / per-function / per-method / per-module grounding ----------
for f in glob.glob(os.path.join(ROOT, "symbols", "schemas", "devtools", "*__full.json")):
    card = json.load(open(f))
    repo_short = card["symbol_id"].replace("repo.", "")
    rel = os.path.relpath(f, ROOT)
    for mrel, m in card["modules"].items():
        modname = mrel[:-3].replace("/", ".").replace("src.", "")
        if m.get("module_doc"):
            put("grounding", f"What does the module `{modname}` do in {repo_short}?",
                trace(f"{repo_short}.{modname}", f"{rel} :: {mrel}", doc(m["module_doc"])))
        for c in m["classes"]:
            method_n = len(c["methods"])
            bases = (" extends " + ", ".join(c["bases"])) if c["bases"] else ""
            body = f"Class `{c['name']}`{bases} — {method_n} public methods. {doc(c['docstring'])}"
            put("grounding", f"What is `{modname}.{c['name']}`?",
                trace(f"{repo_short}.{modname}.{c['name']}", f"{rel} :: {mrel}", body))
            for meth in c["methods"]:
                put("grounding", f"Contract of `{c['name']}.{meth['name']}`?",
                    trace(f"{repo_short}.{modname}.{c['name']}.{meth['name']}", f"{rel} :: {mrel}",
                          f"Signature: `{meth['signature']}`\n{doc(meth['docstring'])}"))
        for fn in m["functions"][:25]:
            put("grounding", f"Contract of `{modname}.{fn['name']}`?",
                trace(f"{repo_short}.{modname}.{fn['name']}", f"{rel} :: {mrel}",
                      f"Signature: `{fn['signature']}`\n{doc(fn['docstring'])}"))

# ---------- extra converse ----------
converse = [
 ("how do I check if a file exists in python?", "from pathlib import Path\nPath(\"file.txt\").exists()\nPath is the modern way; os.path.exists works too."),
 ("what is a generator in python?", "A function that yields values lazily, one at a time, instead of building the whole list. `def gen(): yield 1; yield 2`. You get memory efficiency for free; you lose random access."),
 ("difference between == and is in python?", "== compares values; `is` compares identity (same object in memory). Use `is` only for singletons like None. `a == None` is a style bug; `a is None` is correct."),
 ("how do I sort a dict by value?", "dict(sorted(d.items(), key=lambda kv: kv[1])) — items into pairs, sort by the second element, back to dict. In 3.7+ insertion order is preserved."),
 ("what is a frozen dataclass?", "A dataclass with frozen=True: immutable after construction, hashable if fields are. Use it for value objects and keys — it makes illegal states unrepresentable."),
 ("how do I merge two dicts?", "`a | b` (3.9+) or `{**a, **b}`. Right side wins on key collisions."),
 ("what does `yield from` do?", "Delegates to a sub-generator: `yield from inner()` yields everything inner yields, then continues. It flattens nested generators without loops."),
 ("how do I time a function?", "import time\nt0 = time.perf_counter(); fn(); print(time.perf_counter() - t0)\nFor real benchmarking use timeit — single timings lie on shared machines."),
 ("what is short-circuit evaluation?", "`and` stops at the first falsy, `or` stops at the first truthy. `cache.get(k) or compute(k)` computes only on a miss — that idiom is short-circuiting doing work."),
 ("how do I read a file line by line without loading it all?", "with open(path) as f:\n    for line in f:\n        process(line)\nFiles are iterators; the loop streams one line at a time."),
 ("what's a walrus operator?", "`:=` — assignment as an expression: `if (n := len(xs)) > 3:`. It binds and tests in one motion. Use sparingly; clarity first."),
 ("how do virtualenvs work?", "They isolate a project's packages by putting a private site-packages on the path. python -m venv .venv, activate, and your dependencies stop fighting the system's."),
]
for u, a in converse: put("converse", u, a)

# ---------- extra trace scenarios ----------
scenarios = [
 ("Why does my Flask route 404 even though it's defined?", "flask.Flask.route", "app.py",
  "Almost always one of: the dev server didn't reload after the edit, the rule's leading slash is missing, or a blueprint wasn't registered with app.register_blueprint. Check url_map at runtime — it lists what the app actually knows."),
 ("Why is requests.get hanging forever?", "requests.api.get", "client.py",
  "No timeout. requests waits indefinitely by default; pass timeout=(connect, read) explicitly. Every network call without a timeout is an outage waiting for a quiet afternoon."),
 ("Why does pickle fail on my lambda?", "pickle.dumps", "serialize.py",
  "Pickle serializes by reference, and lambdas are anonymous — it can't name them. Use named functions, or switch to dataclasses + JSON for anything that crosses a wire or a disk."),
 ("Why does git say my branch has diverged?", "git.merge", "repo",
  "Both sides committed since the common ancestor. Fetch, then rebase your work on top of the shared tip for a linear story, or merge for a true join. Never force-push a branch other people pull."),
 ("Why is my test passing alone but failing in the suite?", "pytest.isolation", "tests/",
  "Shared state: a module-level mutable, a file both tests touch, or order-dependent fixtures. Run with -p no:randomly or random ordering to find it, then give each test its own tmp_path."),
 ("Why does str.join complain about ints?", "str.join", "format.py",
  "join needs strings: ', '.join(map(str, nums)). It will not coerce for you — explicit beats magical here."),
]
for q, sym, scope, ans in scenarios: put("trace", q, trace(sym, scope, ans))

# ---------- extra repairs ----------
repairs = [
 ("Repair seq.py so `total([1,2,3])==6`.\n\ndef total(xs):\n    s = 0\n    for x in xs:\n        s = x\n    return s",
  "seq.total", "seq.py", "        s = x", "        s += x"),
 ("Repair flags.py: `DEBUG = True\\nif DEBUG == \"True\":\\n    print('on')` never prints.",
  "flags.check", "flags.py", "if DEBUG == \"True\":", "if DEBUG:"),
 ("Repair users.py so `adult({'age': 20}) is True`.\n\ndef adult(u):\n    return u['age'] > 18",
  "users.adult", "users.py", "return u['age'] > 18", "return u['age'] >= 18"),
 ("Repair text.py: `def shout(s):\\n    return s.upper()\\nprint(shout(123))` crashes.",
  "text.shout", "text.py", "return s.upper()", "return str(s).upper()"),
 ("Repair mathx.py so `safe_div(1, 0) is None`.\n\ndef safe_div(a, b):\n    return a / b",
  "mathx.safe_div", "mathx.py", "    return a / b", "    return a / b if b else None"),
 ("Repair cfg.py: `LIMIT = 100\\nLIMIT += 50` at module level breaks the constant contract; use a function.",
  "cfg.limit", "cfg.py", "LIMIT += 50", "def limit():\n    return LIMIT + 50"),
]
for body, sym, tf, find, replace in repairs:
    diff = json.dumps({"find": find, "replace": replace})
    patch = json.dumps({"action": "patch", "target_file": tf, "symbol": sym, "diff": diff})
    put("repair", body,
        trace(sym, tf, "The defect is localized; patch below.\n§S:REPAIR\n```json\n" + patch + "\n```"))

# ---------- extra fail-closed (extended grid) ----------
extra_syms = [f"{d}_{o}.ops" for d in ["tensor","vector","crypto","plasma","hyper"]
              for o in ["prime","shift","vault","forge"]]
for s in extra_syms[:20]:
    put("fail_closed",
        f"Wire `{s}` into the request path for caching.",
        f"[FAIL-CLOSED: Symbol '{s}' unresolved in symbol index / active context]\nNo such symbol exists in the registry; provide the definition and I will ground against it.")

# ---------- extra ledger ----------
for i, (u, a) in enumerate([
 ("Log the index rebuild result for tonight.",
  "{\"event\": \"rest\", \"changed\": [], \"note\": \"registry re-indexed; hashes verified\", \"test_result\": \"battery green\"}"),
 ("Record that the friend-test passed offline.",
  "{\"event\": \"verification\", \"kind\": \"offline_generation\", \"network\": \"disabled\", \"result\": \"tokens generated\", \"note\": \"friend's-house protocol\"}"),
 ("Ledger entry for a docs-only change.",
  "{\"event\": \"rest\", \"changed\": [{\"symbol\": \"docs/readme\", \"old\": \"<h1>\", \"new\": \"<h2>\"}], \"test_result\": \"battery green\"}"),
 ("Log a planned-but-not-trained model core.",
  "{\"event\": \"registry\", \"core\": \"muse-glimmer-30b-cortex\", \"state\": \"planned\", \"sha256\": null, \"note\": \"planned means planned\"}"),
]):
    put("ledger", u,
        "[TRACE]\n- TARGET_SYMBOLS: [audit_ledger]\n- SCOPE: [memories/audit_ledger.jsonl]\n- STATUS: [GROUNDED]\n\n" + a)

# ---------- extra symbol-class ----------
for q, sym, verdict in [
 ("Can the repair harness import `pytest`?", "pytest",
  "THIRD-PARTY but explicitly sanctioned: pytest is the designated fitness gate of the repair loop, vendored for offline use."),
 ("Is `sqlite3` allowed for the ledger store?", "sqlite3",
  "STANDARD LIBRARY — baseline. Local file I/O only, no network; compatible with the offline invariant."),
 ("Is `wllama.Wllama` internal?", "wllama.Wllama",
  "VENDORED THIRD-PARTY — physically present in vendor/wllama with its own hash manifest; treat as internal-runtime but verify version on upgrade."),
 ("Can the browser UI fetch `cdn.tailwindcss.com`?", "cdn.tailwindcss.com",
  "EXTERNAL NETWORK ORIGIN — policy violation. All assets must be drive-local; the UI uses inline CSS for exactly this reason."),
 ("Is `subprocess.run` okay for the test runner?", "subprocess.run",
  "STANDARD LIBRARY — baseline. The repair loop pins its commands to the fixture config; no shell expansion of model output is permitted."),
]:
    put("symbol_class", q, trace(sym, "classification", verdict))

# ---------- gates ----------
def validate(rows):
    bad = []
    for i, r in enumerate(rows):
        a = r["messages"][2]["content"]
        blob = r["messages"][1]["content"] + a
        for f in FORBIDDEN:
            if f in blob: bad.append((i, "contamination", f))
        if "[FAIL-CLOSED:" in a and "unresolved in symbol index / active context]" not in a:
            bad.append((i, "fail_closed_format", ""))
        if '{"action": "patch"' in a:
            j = a.find('{"action": "patch"'); depth, k = 0, j
            while k < len(a):
                if a[k] == "{": depth += 1
                elif a[k] == "}":
                    depth -= 1
                    if depth == 0: break
                k += 1
            try:
                p = json.loads(a[j:k+1]); inner = json.loads(p["diff"])
                assert "find" in inner and "replace" in inner
            except Exception as e:
                bad.append((i, "repair_json", str(e)))
    return bad

allrows = rows + added
bad = validate(allrows)
if bad:
    for b in bad[:20]: print("REJECTED ROW:", b)
    raise SystemExit(f"gate failure: {len(bad)} bad rows")

with open(FULL, "w") as f:
    for r in allrows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"expanded: {len(rows)} -> {len(allrows)} rows")
print("added blocks:", json.dumps(hist, indent=2, sort_keys=True))
print("gates: contamination-clean, repair-JSON-valid, fail-closed-exact")
