#!/usr/bin/env python3
"""FULL repo extraction -> physical knowledge card. No links as knowledge, no stubs."""
import ast, hashlib, json, os, subprocess, argparse, time
STDLIB = set("""os sys re json typing collections functools itertools datetime warnings contextlib
enum math hashlib hmac base64 threading logging io time dataclasses abc types weakref inspect copy
string struct email http urllib socket ssl gzip zlib secrets uuid gettext importlib pathlib shutil
subprocess tempfile traceback asyncio select signal platform textwrap numbers operator pprint random
shlex stat csv configparser argparse getpass glob fnmatch locale mmap pickle queue xml zipfile tarfile
calendar codecs bisect heapq array cmath decimal fractions dis ast token tokenize keyword builtins
__future__ site sysconfig errno ctypes unicodedata fileinput filecmp pty tty termios pipes grp pwd
syslog resource posix ntpath posixpath bz2 lzma sched""".split())
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()
def sig(node):
    try: return f"{node.name}({ast.unparse(node.args)})"
    except Exception: return f"{node.name}(...)"
def is_public(name): return not (name.startswith("_") and not name.startswith("__"))
def extract_module(path, rel):
    src = open(path, encoding="utf-8", errors="ignore").read()
    tree = ast.parse(src)
    mod = {"file": rel, "sha256": sha256_file(path), "module_doc": ast.get_docstring(tree) or "",
           "classes": [], "functions": [], "imports": []}
    for node in tree.body:
        if isinstance(node, ast.Import): mod["imports"] += [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module: mod["imports"].append(node.module.split(".")[0])
        elif isinstance(node, ast.ClassDef) and is_public(node.name):
            methods = [{"name": m.name, "signature": sig(m), "docstring": (ast.get_docstring(m) or ""),
                        "lineno": m.lineno, "async": isinstance(m, ast.AsyncFunctionDef)}
                       for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                       and (is_public(m.name) or m.name == "__init__")]
            mod["classes"].append({"name": node.name, "bases": [ast.unparse(b) for b in node.bases],
                "docstring": (ast.get_docstring(node) or ""), "lineno": node.lineno, "methods": methods})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(node.name):
            mod["functions"].append({"name": node.name, "signature": sig(node),
                "docstring": (ast.get_docstring(node) or ""), "lineno": node.lineno,
                "async": isinstance(node, ast.AsyncFunctionDef)})
    return mod
def extract_repo(repo_dir, slug, tags):
    modules = {}
    for dp, dns, fns in os.walk(repo_dir):
        dns[:] = [d for d in dns if d not in (".git","tests","test","docs","doc","examples","example","__pycache__","benchmarks")]
        for fn in sorted(fns):
            if fn.endswith(".py") and fn not in ("setup.py", "conftest.py"):
                full = os.path.join(dp, fn); rel = os.path.relpath(full, repo_dir)
                try: modules[rel] = extract_module(full, rel)
                except (SyntaxError, ValueError): continue
    pkgs = {p.split(os.sep)[0] for p in modules if os.sep in p}
    top_pkg = sorted(pkgs)[0] if pkgs else slug.split("/")[-1]
    ext = sorted({imp for m in modules.values() for imp in m["imports"]
                  if imp not in STDLIB and imp != top_pkg and not imp.startswith(top_pkg)})
    commit = subprocess.run(["git","-C",repo_dir,"rev-parse","HEAD"], capture_output=True, text=True).stdout.strip() or None
    stats = {"modules": len(modules),
             "classes": sum(len(m["classes"]) for m in modules.values()),
             "functions": sum(len(m["functions"]) for m in modules.values()),
             "methods": sum(len(c["methods"]) for m in modules.values() for c in m["classes"])}
    entry_points = sorted({c["name"] for m in modules.values() for c in m["classes"]})[:60]
    return {"symbol_id": f"repo.{slug.replace('/', '.')}", "kind": "repo_extraction", "tags": tags,
      "source": {"repo": f"https://github.com/{slug}", "commit": commit,
                 "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "note": "origin is audit metadata only; ALL knowledge below is physically embedded"},
      "stats": stats, "entry_points": entry_points,
      "edges": {"upstream": ext, "downstream": []}, "modules": modules}
def update_star(root, star_id, category, repo_card, card_rel):
    spath = os.path.join(root, "symbols", "schemas", category, f"star__{star_id.replace('.', '_')}.json")
    if os.path.exists(spath): star = json.load(open(spath))
    else:
        star = {"symbol_id": f"star.{star_id}", "kind": "star", "tags": [star_id.split(".")[0], category, "star"],
                "represents": [], "entry_points": [], "edges": {"upstream": [], "downstream": []},
                "note": "This star aggregates FULL physical extraction cards stored on this drive. No links as knowledge."}
    digest = sha256_file(os.path.join(root, card_rel))
    star["represents"] = [r for r in star["represents"] if r["symbol_id"] != repo_card["symbol_id"]]
    star["represents"].append({"symbol_id": repo_card["symbol_id"], "repo": repo_card["source"]["repo"],
                               "card": card_rel, "sha256": digest, "stats": repo_card["stats"]})
    star["entry_points"] = sorted(set(star["entry_points"]) | set(repo_card["entry_points"]))
    star["edges"]["upstream"] = sorted(set(star["edges"]["upstream"]) | set(repo_card["edges"]["upstream"]))
    os.makedirs(os.path.dirname(spath), exist_ok=True)
    json.dump(star, open(spath, "w"), indent=2)
    return spath
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-dir", required=True); ap.add_argument("--slug", required=True)
    ap.add_argument("--star", required=True); ap.add_argument("--category", default="devtools")
    ap.add_argument("--tags", default="")
    a = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tags = [t for t in a.tags.split(",") if t] + [a.slug.split("/")[-1], "extraction"]
    card = extract_repo(a.repo_dir, a.slug, tags)
    outdir = os.path.join(root, "symbols", "schemas", a.category); os.makedirs(outdir, exist_ok=True)
    cpath = os.path.join(outdir, f"{a.slug.replace('/', '__')}__full.json")
    json.dump(card, open(cpath, "w"), indent=2)
    spath = update_star(root, a.star, a.category, card, os.path.relpath(cpath, root))
    s = card["stats"]
    print(f"[extract] {a.slug}: {s['modules']} modules, {s['classes']} classes, {s['functions']} functions, {s['methods']} methods")
    print(f"[star] star.{a.star} now represents {len(json.load(open(spath))['represents'])} repo(s)")
if __name__ == "__main__": main()
