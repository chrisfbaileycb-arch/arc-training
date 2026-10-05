#!/usr/bin/env python3
"""Compose corpus_v5_muse_cortex_full.jsonl from the seed + template blocks + REAL
drive cards (grounding rows cite actual schema/vault content). Gates:
- anti-contamination: battery probe strings must NOT appear in the corpus
- every §S:REPAIR block must parse as JSON, outer AND inner diff
- exact fail-closed diagnostic string in every fail-closed row
Deterministic. Prints a block histogram."""
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "training", "corpus_v5_muse_cortex_seed.jsonl")
OUT = os.path.join(ROOT, "training", "corpus_v5_muse_cortex_full.jsonl")

seed_rows = [json.loads(l) for l in open(SEED)]
SYS = seed_rows[0]["messages"][0]["content"]

def ex(user, assistant):
    return {"messages": [{"role": "system", "content": SYS},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}]}

FORBIDDEN = ["quantum_flux_capacitor", "return a - b", "def add(a, b):"]

hist, rows = {}, []
def put(block, user, assistant):
    rows.append(ex(user, assistant)); hist[block] = hist.get(block, 0) + 1

# seed rows: keep, de-contaminating the repair row that uses the battery fixture
for r in seed_rows:
    u = r["messages"][1]["content"]; a = r["messages"][2]["content"]
    if "return a - b" in u + a:
        u = u.replace("return a - b", "return a * b")
        a = a.replace("return a - b", "return a * b")
        a = a.replace("subtraction where addition belongs", "multiplication where addition belongs")
    rows.append(r); hist["seed"] = hist.get("seed", 0) + 1

converse = [
 ("what are you up to?", "Working through the registry and waiting for something worth repairing. What do you need built?"),
 ("explain recursion with an example", "Recursion is a function calling itself on a smaller input until a base case stops it. factorial(4) = 4 * factorial(3) ... down to factorial(0) = 1. The rule: every recursive step must move toward the base case, or you get a stack overflow instead of an answer."),
 ("what's the difference between a list and a tuple in python?", "Lists are mutable (append, sort in place), tuples are immutable and hashable. Use a tuple as a dict key or when the shape of the data is part of its meaning; use a list when the collection is expected to change."),
 ("how do I reverse a string in python?", "`s[::-1]` — slicing with a step of -1. For very large strings where memory matters, iterate instead, but for normal use the slice is the idiomatic answer."),
 ("what does a context manager do?", "It guarantees cleanup. `with open(f) as h:` closes the file even if the body raises. Anything implementing __enter__/__exit__ can be a context manager — locks, temp dirs, DB transactions."),
 ("morning", "Morning. Registry is indexed, ledger is open. Where do we start?"),
 ("why is my loop slow?", "The usual suspects, in order: doing I/O or allocation inside the hot loop, an O(n^2) pattern hiding in a lookup that should be a set/dict, or re-computing something invariant. Measure first with a profiler; guessing wastes afternoons."),
 ("what is an API?", "A contract: named operations, their inputs, their outputs, and the error behavior. Good code treats APIs the way this drive treats schema cards — you build against the contract, not against your memory of it."),
 ("can you write a quicksort?", "def quicksort(xs):\n    if len(xs) <= 1:\n        return xs\n    p = xs[len(xs)//2]\n    return quicksort([x for x in xs if x < p]) + [x for x in xs if x == p] + quicksort([x for x in xs if x > p])\n\nClear, not in-place. For production use sorted() — Timsort beats hand-rolled quicksort in practice."),
 ("what does idempotent mean?", "Doing it twice changes nothing beyond doing it once. DELETE is idempotent; POST is not. It is the property that makes retries safe."),
 ("how do I read a json file in python?", "import json\nwith open(\"data.json\") as f:\n    data = json.load(f)"),
 ("what's the point of type hints?", "Documentation that tools can check. They catch argument-order and return-type mistakes at lint time instead of in production, and they make contracts readable — same reason schema cards carry signatures."),
]
for u, a in converse: put("converse", u, a)

fake_syms = [f"{d}_{o}.core" for d in ["quantum","crypto","neural","plasma","hyper","chrono","astro","nano"]
             for o in ["flux","matrix","lattice","engine","weaver"]]
for s in fake_syms[:30]:
    put("fail_closed",
        f"Use the repo symbol `{s}` to accelerate the pipeline.",
        f"[FAIL-CLOSED: Symbol '{s}' unresolved in symbol index / active context]\nFiling a repair proposal: provide the definition or the correct index entry.")
for s in fake_syms[30:40]:
    put("fail_closed",
        f"Patch `{s}` to handle timeouts.",
        f"[FAIL-CLOSED: Symbol '{s}' unresolved in symbol index / active context]\nI will not invent its signature. Provide the file or index entry and I will repair against the real contract.")

idx_path = os.path.join(ROOT, "symbols", "symbol_index.json")
if os.path.exists(idx_path):
    idx = json.load(open(idx_path))["symbols"]
else:
    import sys; sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_symbol_index as bsi
    idx, _ = bsi.build(); idx = idx["symbols"]
real_syms = list(idx.keys())
intent_map = {
 "ring": "how does the lockless buffer publish writes?",
 "barrier": "what stops the CPU reordering my stores?",
 "flask": "what is the signature of the Flask app class?",
 "requests": "how does requests.Session persist cookies?",
 "star": "which repos does the python foundations star cover?",
}
intents = []
for sid in real_syms:
    for key, q in intent_map.items():
        if key in sid:
            intents.append((sid, q))
for sid, q in intents[:14]:
    put("registry_qa",
        f"Which symbol covers this: {q}",
        "[TRACE]\n- TARGET_SYMBOLS: [" + sid + "]\n- SCOPE: [" + idx[sid]["path"] + "]\n- STATUS: [GROUNDED]\n\nResolved: `" + sid + "` — the physical card is on this drive and its hash verifies against the index.")
for i in range(10):
    s = fake_syms[i]
    put("registry_qa",
        f"Which symbol covers `{s}` operations?",
        "[TRACE]\n- TARGET_SYMBOLS: [" + s + "]\n- SCOPE: [unresolved in active context]\n- STATUS: [FAIL-CLOSED]\n\n[FAIL-CLOSED: Symbol '" + s + "' unresolved in symbol index / active context]")

def load_card(sid):
    return json.load(open(os.path.join(ROOT, idx[sid]["path"])))
for sid in [s for s in real_syms if idx[s].get("kind", "schema") == "schema"]:
    try: card = load_card(sid)
    except Exception: continue
    c = card.get("content", {})
    ov = c.get("overview") or c.get("summary", "")
    inv = (c.get("invariants") or [])[:3]
    if ov:
        put("grounding", f"Summarize what `{sid}` guarantees.",
            "[TRACE]\n- TARGET_SYMBOLS: [" + sid + "]\n- SCOPE: [" + idx[sid]["path"] + "]\n- STATUS: [GROUNDED]\n\n" + ov)
    if inv:
        put("grounding", f"What invariants must I respect when using `{sid}`?",
            "[TRACE]\n- TARGET_SYMBOLS: [" + sid + "]\n- SCOPE: [" + idx[sid]["path"] + "]\n- STATUS: [GROUNDED]\n\n" + "\n".join("- " + v for v in inv))
    for op in (c.get("operations") or [])[:6]:
        put("grounding", f"What is the contract of `{op['name']}`?",
            "[TRACE]\n- TARGET_SYMBOLS: [" + sid + "." + op["name"] + "]\n- SCOPE: [" + idx[sid]["path"] + "]\n- STATUS: [GROUNDED]\n\nSignature: `" + op["signature"] + "`\nContract: " + op["contract"])
    vq = (c.get("verification_questions") or [])[:3]
    if vq:
        put("grounding", f"How do I verify an implementation of `{sid}`?",
            "[TRACE]\n- TARGET_SYMBOLS: [" + sid + "]\n- SCOPE: [" + idx[sid]["path"] + "]\n- STATUS: [GROUNDED]\n\nAsk:\n" + "\n".join("- " + q for q in vq))

for f in glob.glob(os.path.join(ROOT, "symbols", "schemas", "devtools", "*__full.json")):
    card = json.load(open(f))
    sid = card["symbol_id"]; st = card["stats"]
    eps = ", ".join(card["entry_points"][:8])
    put("grounding", f"What does the extraction card for {card['source']['repo']} contain?",
        "[TRACE]\n- TARGET_SYMBOLS: [" + sid + "]\n- SCOPE: [" + os.path.relpath(f, ROOT) + "]\n- STATUS: [GROUNDED]\n\n" +
        f"{st['modules']} modules, {st['classes']} classes, {st['functions']} functions, {st['methods']} methods, fully extracted with per-file sha256. Entry points include: {eps}.")

scenarios = [
 ("Why might `sorted(data, key=lambda x: x['ts'])` raise KeyError?",
  "calc.sort", "report.py",
  "If any element lacks the 'ts' key the lambda raises KeyError mid-sort. Guard with x.get('ts') or filter first; the traceback will point at the lambda, not the sort."),
 ("Why does my dict grow unboundedly in the crawler?",
  "crawler.seen", "crawler.py",
  "A `seen` set/dict that is never pruned grows with every URL. Bound it (LRU, bloom filter, or periodic flush) or the process dies by a thousand cuts."),
 ("Why does `open(path).read()` sometimes return empty on the first try?",
  "io.read", "loader.py",
  "Another process may still be writing the file. Read-after-write without a barrier or a size check is a race; stat first or retry with backoff."),
 ("Why is my recursion hitting RecursionError on deep trees?",
  "tree.walk", "tree.py",
  "Default recursion limit is ~1000 frames. Convert deep walks to an explicit stack, or raise the limit only if the depth is provably bounded."),
 ("Why does the cache return stale values after deploy?",
  "cache.get", "cache.py",
  "Keys that do not include a version/generation never invalidate. Stamp keys with a build or schema version and old entries die quietly."),
 ("Why does `json.dumps(obj)` fail on my dataclass?",
  "json.dumps", "serialize.py",
  "Dataclasses are not JSON-serializable by default. Use dataclasses.asdict() or a custom default= handler; datetime needs isoformat."),
]
for q, sym, scope, ans in scenarios:
    put("trace", q,
        "[TRACE]\n- TARGET_SYMBOLS: [" + sym + "]\n- SCOPE: [" + scope + "]\n- STATUS: [GROUNDED]\n\n" + ans)
for i in range(6):
    s = fake_syms[i]
    put("trace", f"Verify the integrity of `{s}` before tonight's run.",
        "[TRACE]\n- TARGET_SYMBOLS: [" + s + "]\n- SCOPE: [unresolved in active context]\n- STATUS: [FAIL-CLOSED]\n\n[FAIL-CLOSED: Symbol '" + s + "' unresolved in symbol index / active context]")

repairs = [
 ("Repair mathx.py so `double(4)==8`.\n\ndef double(x):\n    return x + x + x",
  "mathx.double", "mathx.py", "return x + x + x", "return x + x"),
 ("Repair mathx.py so `square(3)==9`.\n\ndef square(x):\n    return x * 3",
  "mathx.square", "mathx.py", "return x * 3", "return x * x"),
 ("Repair seq.py so `first_n([1,2,3], 2)==[1,2]`.\n\ndef first_n(xs, n):\n    return xs[:n+1]",
  "seq.first_n", "seq.py", "return xs[:n+1]", "return xs[:n]"),
 ("Repair greet.py: `def hi(name):\n    return \"hello \" + name.upper` calls the method object.",
  "greet.hi", "greet.py", "name.upper", "name.upper()"),
 ("Repair guard.py: `if role = \"admin\":` is a syntax error.",
  "guard.check", "guard.py", "if role = \"admin\":", "if role == \"admin\":"),
 ("Repair totals.py: `total = sum(prices) / count` divides by zero when count is 0; contract: return 0.",
  "totals.average", "totals.py", "total = sum(prices) / count",
  "total = sum(prices) / count if count else 0"),
]
for body, sym, tf, find, replace in repairs:
    diff = json.dumps({"find": find, "replace": replace})
    patch = json.dumps({"action": "patch", "target_file": tf, "symbol": sym, "diff": diff})
    put("repair", body,
        "[TRACE]\n- TARGET_SYMBOLS: [" + sym + "]\n- SCOPE: [" + tf + "]\n- STATUS: [GROUNDED]\n\nThe defect is localized; patch below.\n§S:REPAIR\n```json\n" + patch + "\n```")

classes = [
 ("Is `pathlib.Path` safe to use in the offline runner?",
  "pathlib.Path", "STANDARD LIBRARY / RUNTIME SYMBOL — permissible baseline. It performs no network access and is part of the offline invariant's allowed set."),
 ("Can the runner call `numpy.linalg.inv`?",
  "numpy.linalg.inv", "THIRD-PARTY EXTERNAL DEPENDENCY — flagged for explicit ground verification: confirm the package is vendored and check the extraction card before relying on edge behavior (singular matrices raise LinAlgError)."),
 ("Is `repair_loop.mutants` an approved symbol?",
  "repair_loop.mutants", "INTERNAL REPO SYMBOL — bound to this drive's codebase (scripts/repair_loop.py). Resolve against the physical file and its sha256."),
 ("Can I use `hashlib.sha256` in ledger code?",
  "hashlib.sha256", "STANDARD LIBRARY — baseline, and it is the ledger's designated integrity primitive."),
 ("Is `torch.nn.Linear` available at runtime?",
  "torch.nn.Linear", "THIRD-PARTY EXTERNAL DEPENDENCY — and a policy violation: torch is banned from the runtime tree (training phase only). Fail-closed at the import gate."),
]
for q, sym, verdict in classes:
    put("symbol_class", q,
        "[TRACE]\n- TARGET_SYMBOLS: [" + sym + "]\n- SCOPE: [classification]\n- STATUS: [GROUNDED]\n\n" + verdict)

ledgers = [
 ("Write the ledger entry for a repair that changed calc.py and passed tests.",
  "{\"event\": \"repair_success\", \"file\": \"calc.py\", \"op\": \"sub_to_add\", \"line\": 2, \"fitness\": 1.0, \"sha256\": \"<computed-at-write>\"}"),
 ("Close the session after an index rebuild with no file changes.",
  "{\"event\": \"rest\", \"changed\": [], \"test_result\": \"battery green\", \"note\": \"index and graph regenerated\"}"),
 ("Log a rejected mutation for the audit trail.",
  "{\"event\": \"mutant\", \"file\": \"stats.py\", \"op\": \"eq_to_ne\", \"line\": 4, \"fitness\": 0.0, \"outcome\": \"reverted\"}"),
 ("What goes into a REST entry?",
  None),
 ("Mark rest after a health-card review with no mutations.",
  "{\"event\": \"rest\", \"changed\": [], \"note\": \"health_safety referral invariant re-verified present\", \"test_result\": \"battery green\"}"),
]
for u, a in ledgers:
    if a is None:
        put("ledger", u,
            "[TRACE]\n- TARGET_SYMBOLS: [rest]\n- SCOPE: [memories/audit_ledger.jsonl]\n- STATUS: [GROUNDED]\n\nTimestamp, event name, the changed-file list with old and new sha256, the test result, and any operator metadata. The ledger is append-only; nothing is edited after write.")
    else:
        put("ledger", u,
            "[TRACE]\n- TARGET_SYMBOLS: [audit_ledger]\n- SCOPE: [memories/audit_ledger.jsonl]\n- STATUS: [GROUNDED]\n\n" + a)

def validate(rows):
    bad = []
    for i, r in enumerate(rows):
        a = r["messages"][2]["content"]
        blob = r["messages"][1]["content"] + a
        for f in FORBIDDEN:
            if f in blob:
                bad.append((i, "contamination", f))
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

bad = validate(rows)
if bad:
    for b in bad[:20]: print("REJECTED ROW:", b)
    raise SystemExit(f"gate failure: {len(bad)} bad rows")

with open(OUT, "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"wrote {len(rows)} rows -> {os.path.relpath(OUT, ROOT)}")
print("blocks:", json.dumps(hist, indent=2, sort_keys=True))
print("gates: contamination-clean, repair-JSON-valid, fail-closed-exact")
