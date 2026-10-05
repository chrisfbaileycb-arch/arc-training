"""Mechanical gates for the CORE-SPEC v4.2 protocol kit itself."""
import json, os, py_compile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_directive_contains_required_invariants():
    d = open(os.path.join(ROOT, "protocol", "cortex_system_directive.md")).read()
    for marker in ("RULE 1", "[FAIL-CLOSED: Symbol '", "[TRACE]",
                   "TARGET_SYMBOLS", "SCOPE", "STATUS", "§S:REPAIR", "800 tokens"):
        assert marker in d, marker

def test_runtime_prompt_has_converse_safeguard_and_dials():
    p = open(os.path.join(ROOT, "protocol", "glimmer_cortex_system_prompt.txt")).read()
    assert "Reasoning strength: high" in p
    assert "answer directly and normally" in p

def test_battery_script_compiles():
    py_compile.compile(os.path.join(ROOT, "protocol", "battery_glimmer_cortex.py"), doraise=True)

def test_corpus_seed_rows_and_repair_json_valid():
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "training", "corpus_v5_muse_cortex_seed.jsonl"))]
    assert len(rows) >= 20
    repair_blocks = 0
    for r in rows:
        msgs = r["messages"]
        assert len(msgs) == 3 and msgs[0]["role"] == "system"
        a = msgs[2]["content"]
        if '{"action": "patch"' in a:
            repair_blocks += 1
            i = a.find('{"action": "patch"')
            depth, j = 0, i
            while j < len(a):
                if a[j] == "{": depth += 1
                elif a[j] == "}":
                    depth -= 1
                    if depth == 0: break
                j += 1
            patch = json.loads(a[i:j + 1])
            assert patch["action"] == "patch" and patch["diff"]
            inner = json.loads(patch["diff"])
            assert "find" in inner and "replace" in inner
    assert repair_blocks >= 3

def test_fail_closed_examples_use_exact_string():
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "training", "corpus_v5_muse_cortex_seed.jsonl"))]
    fc = [r for r in rows if "[FAIL-CLOSED: Symbol '" in r["messages"][2]["content"]]
    assert len(fc) >= 4
    for r in fc:
        assert "unresolved in symbol index / active context]" in r["messages"][2]["content"]

def test_cores_registry_wires_protocol_to_muse():
    cores = json.load(open(os.path.join(ROOT, "models", "cores.json")))["cores"]
    muse = cores["muse-glimmer-30b"]
    assert muse["protocol"] == "protocol/glimmer_cortex_system_prompt.txt"
    assert os.path.isfile(os.path.join(ROOT, muse["protocol"]))
    assert muse["designation"].startswith("Aegis-Glimmer-30B")
