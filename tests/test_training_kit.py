import json, os, py_compile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL = os.path.join(ROOT, "training", "corpus_v5_muse_cortex_full.jsonl")

def rows():
    return [json.loads(l) for l in open(FULL)]

def test_full_corpus_size_and_shape():
    rs = rows()
    assert len(rs) >= 450, len(rs)
    for r in rs:
        assert len(r["messages"]) == 3 and r["messages"][0]["role"] == "system"

def test_anti_contamination_gate():
    blob = open(FULL).read()
    for forbidden in ("quantum_flux_capacitor", "return a - b", "adds two numbers"):
        assert forbidden not in blob, forbidden

def test_repair_json_all_valid():
    n = 0
    for r in rows():
        a = r["messages"][2]["content"]
        if '{"action": "patch"' in a:
            n += 1
            i = a.find('{"action": "patch"'); depth, j = 0, i
            while j < len(a):
                if a[j] == "{": depth += 1
                elif a[j] == "}":
                    depth -= 1
                    if depth == 0: break
                j += 1
            p = json.loads(a[i:j+1]); inner = json.loads(p["diff"])
            assert "find" in inner and "replace" in inner
    assert n >= 8

def test_fail_closed_exact_string_present():
    fc = [r for r in rows() if "[FAIL-CLOSED: Symbol '" in r["messages"][2]["content"]]
    assert len(fc) >= 20
    for r in fc:
        assert "unresolved in symbol index / active context]" in r["messages"][2]["content"]

def test_train_script_compiles():
    py_compile.compile(os.path.join(ROOT, "training", "train_qlora.py"), doraise=True)

def test_job_script_has_gates_before_publish():
    s = open(os.path.join(ROOT, "training", "job_end_to_end.sh")).read()
    assert "llama-bench" in s and "battery_glimmer_cortex" in s and "sha256sum" in s
    assert s.index("llama-bench") < s.index("huggingface-cli upload")
    assert "BATTERY FAILED" in s

def test_model_card_template_has_honesty_ledger():
    t = open(os.path.join(ROOT, "training", "model_cardTEMPLATE.md")).read()
    assert "UNMEASURED" in t and "Honesty ledger" in t and "Capability preservation" in t

def test_cores_registry_marks_30b_cortex_as_planned_not_real():
    cores = json.load(open(os.path.join(ROOT, "models", "cores.json")))["cores"]
    planned = cores["muse-glimmer-30b-cortex"]
    assert planned["state"] == "planned" and planned["sha256"] is None
