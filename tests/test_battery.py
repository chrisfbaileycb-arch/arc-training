"""The battery's own logic, graded against a fake local endpoint. No model is loaded or claimed."""
import http.server, importlib.util, json, os, shutil, sys, threading
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = importlib.util.spec_from_file_location("battery", os.path.join(ROOT, "protocol", "battery_glimmer_cortex.py"))
bat = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(bat)

SRC = "def add(a, b):\n    return a - b\n"
FAIL_CLOSED = "[FAIL-CLOSED: Symbol 'quantum_flux_capacitor.sync' unresolved in symbol index / active context]"
INNER = json.dumps({"find": "    return a - b", "replace": "    return a + b"})
PATCHES = {
    "action": '{"action": "patch", "target_file": "calc.py", "symbol": "calc.add", "diff": %s}' % json.dumps(INNER),
    "bare": "Diagnosis: wrong operator.\n" + INNER,
    "mention-only": '{"action": "patch", "target_file": "calc.py", "symbol": "calc.add", "diff": "use return a + b"}',
}

def endpoint(patch="action", refuse_no_system=False):
    seen = []
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append(body); user = body["messages"][-1]["content"]
            if "adds two numbers" in user:
                out = "I can't violate rule number one." if refuse_no_system else "```python\ndef add(a, b):\n    return a + b\n```"
            elif "quantum_flux" in user: out = FAIL_CLOSED
            elif "Diagnose" in user: out = "[TRACE]\n- TARGET_SYMBOLS: [clamp]\n- SCOPE: [calc.py]\n- STATUS: [UNMEASURED]"
            elif "Repair" in user: out = PATCHES[patch]
            elif "median" in user: out = "```python\ndef median(v):\n    raise ValueError('empty input')\n```"
            elif "How are you" in user: out = "Doing well, thanks for asking!"
            else: out = "pong"
            data = json.dumps({"choices": [{"message": {"content": out}}]}).encode()
            self.send_response(200); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, seen

def run(monkeypatch, capsys, base):
    monkeypatch.setattr(sys, "argv", ["battery", "--base", base])
    rc = bat.main()
    return rc, capsys.readouterr().out

@pytest.mark.parametrize("patch", ["action", "bare"])
def test_full_battery_passes_for_both_patch_shapes(monkeypatch, capsys, patch):
    srv, seen = endpoint(patch)
    try: rc, out = run(monkeypatch, capsys, "http://127.0.0.1:%d" % srv.server_port)
    finally: srv.shutdown()
    assert rc == 0, out
    assert "BATTERY: 6/6 probes passed" in out
    assert all(b["stop"] == ["<|im_end|>"] for b in seen)
    assert all(b["max_tokens"] >= 800 for b in seen if b["messages"][-1]["content"] != "ping")
    no_sys = [b for b in seen if "adds two numbers" in b["messages"][-1]["content"]]
    assert no_sys and no_sys[0]["messages"][0]["role"] == "user"  # that probe carries no system prompt

def test_refusal_without_system_prompt_fails_the_battery(monkeypatch, capsys):
    srv, _ = endpoint(refuse_no_system=True)
    try: rc, out = run(monkeypatch, capsys, "http://127.0.0.1:%d" % srv.server_port)
    finally: srv.shutdown()
    assert rc == 1 and "[FAIL] converse-code-no-system" in out

def test_patch_that_only_mentions_the_fix_is_not_credited(monkeypatch, capsys):
    srv, _ = endpoint("mention-only")
    try: rc, out = run(monkeypatch, capsys, "http://127.0.0.1:%d" % srv.server_port)
    finally: srv.shutdown()
    assert rc == 1 and "[FAIL] repair-patch-executable" in out and "could not be applied" in out

def test_no_endpoint_is_an_honest_abort(monkeypatch, capsys):
    rc, out = run(monkeypatch, capsys, "http://127.0.0.1:9")
    assert rc == 2 and "ABORT" in out

def test_apply_patch_shapes():
    assert "return a + b" in bat.apply_patch({"find": "return a - b", "replace": "return a + b"}, SRC)
    assert "return a + b" in bat.apply_patch({"action": "patch", "diff": INNER}, SRC)
    assert bat.apply_patch({"action": "patch", "diff": "x"}, SRC) is None
    assert bat.apply_patch({"find": "nope", "replace": "y"}, SRC) is None
    assert bat.apply_patch({"action": "patch", "diff": "def add(a, b):\n    return a + b\n"}, SRC).endswith("a + b\n")

@pytest.mark.skipif(not shutil.which("patch"), reason="system `patch` tool not installed")
def test_apply_unified_diff():
    d = "--- a/calc.py\n+++ b/calc.py\n@@ -1,2 +1,2 @@\n def add(a, b):\n-    return a - b\n+    return a + b\n"
    assert "return a + b" in bat.apply_patch({"action": "patch", "diff": d}, SRC)

def test_extract_patch_handles_nested_braces_and_bare_json():
    t = 'x {"action": "patch", "diff": "{\\"find\\": \\"a\\", \\"replace\\": \\"b\\"}", "target_file": "c"} tail'
    assert bat.extract_patch(t)["target_file"] == "c"
    assert bat.extract_patch("thinking\n" + INNER)["find"] == "    return a - b"
    assert bat.extract_patch("no json here") is None
