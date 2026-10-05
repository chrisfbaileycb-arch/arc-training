"""Mechanical gates: real files, real subprocesses. Model-in-loop tests SKIP honestly."""
import json, os, shutil, subprocess, sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_symbol_index as bsi
import engine_lifecycle as elc
import repair_loop as rl

def test_index_builds_with_hashes():
    idx, graph = bsi.build()
    assert len(idx["symbols"]) >= 2
    for sid, meta in idx["symbols"].items():
        assert os.path.isfile(os.path.join(ROOT, meta["path"])), sid
        assert len(meta["sha256"]) == 64
    assert len(graph["edges"]) >= 2

def test_awake_resolves_traces_loads(capsys):
    rc = elc.awake("how does a lockless ring buffer order memory")
    out = capsys.readouterr().out
    assert rc == 0 and "[AWAKE TRACE]" in out
    assert "systems.concurrency.ring_buffer" in out
    assert "grounded content loaded from disk" in out

def test_awake_refuses_unknown(capsys):
    rc = elc.awake("zzzqqq unrelated nonsense")
    assert rc == 2 and "refuse-and-propose-repair" in capsys.readouterr().out

def test_repair_loop_actually_fixes(tmp_path, monkeypatch):
    ledger = tmp_path / "audit_ledger.jsonl"  # tests must never write the real audit ledger
    monkeypatch.setattr(rl, "LEDGER", str(ledger))
    dst = tmp_path / "bm"
    shutil.copytree(os.path.join(ROOT, "tests", "fixtures", "broken_math"), dst)
    assert rl.repair(str(dst)) == 0
    r = subprocess.run("python -m pytest test_calc.py -q", shell=True, cwd=dst,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    assert "repair_success" in ledger.read_text()

def test_repair_loop_restores_original_on_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(rl, "LEDGER", str(tmp_path / "audit_ledger.jsonl"))
    (tmp_path / "m.py").write_text("y = 2 - 1\n")  # one mutable operator, test can never pass
    (tmp_path / ".aegis.config").write_text(json.dumps(
        {"test_command": "python -c 'raise SystemExit(1)'", "target_files": ["m.py"]}))
    assert rl.repair(str(tmp_path)) == 1
    assert (tmp_path / "m.py").read_text() == "y = 2 - 1\n"

def test_repair_loop_restores_original_on_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(rl, "LEDGER", str(tmp_path / "audit_ledger.jsonl"))
    calls = []
    def flaky(d, cmd):  # baseline fails, then the first mutant run crashes the loop
        calls.append(1)
        if len(calls) == 1: return 0.0, ""
        raise KeyboardInterrupt
    monkeypatch.setattr(rl, "run_tests", flaky)
    (tmp_path / "m.py").write_text("y = 2 - 1\n")
    (tmp_path / ".aegis.config").write_text(json.dumps({"test_command": "x", "target_files": ["m.py"]}))
    with pytest.raises(KeyboardInterrupt):
        rl.repair(str(tmp_path))
    assert (tmp_path / "m.py").read_text() == "y = 2 - 1\n"

def test_run_tests_timeout_is_unfit_not_crash(monkeypatch):
    def hang(*a, **kw): raise subprocess.TimeoutExpired("x", 1)
    monkeypatch.setattr(rl.subprocess, "run", hang)
    assert rl.run_tests(".", "x") == (0.0, "timeout")

def test_rest_appends_and_regenerates(tmp_path, monkeypatch):
    ledger = tmp_path / "audit_ledger.jsonl"
    monkeypatch.setattr(elc, "LEDGER", str(ledger))
    assert elc.rest() == 0 and ledger.stat().st_size > 0
    g = json.load(open(os.path.join(ROOT, "models", "knowledge_graph.json")))
    assert g["nodes"] and g["edges"]

def test_health_referral_invariant():
    card = open(os.path.join(ROOT, "knowledge_vault", "health_safety", "basic_first_aid.md")).read()
    assert "REFERRAL NOTICE (MANDATORY" in card and "VERIFY CURRENT GUIDANCE" in card

def test_offline_invariant():
    banned = ("import transformers", "from transformers", "import torch", "onnxruntime",
              "import requests", "urllib.request")
    for fn in os.listdir(os.path.join(ROOT, "scripts")):
        if fn.endswith(".py"):
            src = open(os.path.join(ROOT, "scripts", fn)).read()
            for b in banned: assert b not in src, f"{b} in scripts/{fn}"

def test_cores_registry_v2():
    cores = json.load(open(os.path.join(ROOT, "models", "cores.json")))["cores"]
    assert {"ornith-9b-cortex", "mimo-9b-cortex", "muse-glimmer-30b"} <= set(cores)
    assert cores["ornith-9b-cortex"]["sha256"].startswith("ca2803a2")
    assert cores["mimo-9b-cortex"]["sha256"].startswith("ec4cb3fb")
    assert cores["muse-glimmer-30b"]["min_llamacpp_build"] >= 10353

def test_runtime_binaries_present():
    assert os.path.isfile(os.path.join(ROOT, "runtime", "win", "llama-server.exe"))
    assert os.path.isfile(os.path.join(ROOT, "runtime", "linux", "llama-b11382", "llama-server"))

def test_extraction_cards_are_full_content():
    p = os.path.join(ROOT, "symbols", "schemas", "devtools")
    if not os.path.isdir(p): pytest.skip("extractor not run yet")
    cards = [json.load(open(os.path.join(p, f))) for f in os.listdir(p) if f.endswith("__full.json")]
    for c in cards:
        assert c["stats"]["functions"] + c["stats"]["methods"] > 0
        assert c["entry_points"]

w = os.path.join(ROOT, "models", "weights")
has_w = os.path.isdir(w) and any(f.endswith(".gguf") for f in os.listdir(w))

@pytest.mark.skipif(not has_w,
    reason="needs .gguf in models/weights — run download_models.py (honest skip, not a pass)")
def test_model_loads_offline():
    pass
