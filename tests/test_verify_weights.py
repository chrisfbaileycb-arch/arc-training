import hashlib, importlib.util, json, os

SPEC = importlib.util.spec_from_file_location(
    "verify_weights", os.path.join(os.path.dirname(__file__), "..", "scripts", "verify_weights.py"))
vw = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(vw)

def make_root(tmp_path, data, sha):
    (tmp_path / "models" / "weights").mkdir(parents=True, exist_ok=True)
    (tmp_path / "models" / "weights" / "a.gguf").write_bytes(data)
    cfg = {"cores": {"a": {"file": "models/weights/a.gguf", "sha256": sha, "bytes": None}}}
    (tmp_path / "models" / "cores.json").write_text(json.dumps(cfg))
    return str(tmp_path)

def test_ok_and_mismatch(tmp_path):
    good = hashlib.sha256(b"abc").hexdigest()
    assert vw.verify(make_root(tmp_path, b"abc", good)) == 0
    assert vw.verify(make_root(tmp_path, b"abd", good)) == 1

def test_pin_writes_hash(tmp_path):
    root = make_root(tmp_path, b"abc", None)
    assert vw.verify(root, pin=True) == 0
    core = json.load(open(os.path.join(root, "models", "cores.json")))["cores"]["a"]
    assert core["sha256"] == hashlib.sha256(b"abc").hexdigest() and core["bytes"] == 3

def test_missing_file_is_not_a_failure(tmp_path):
    root = make_root(tmp_path, b"abc", None)
    os.remove(os.path.join(root, "models", "weights", "a.gguf"))
    assert vw.verify(root) == 0
