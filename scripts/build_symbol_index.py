#!/usr/bin/env python3
"""Hash every physical schema/vault file; rebuild symbol_index.json + knowledge_graph.json."""
import hashlib, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()
def build(root=ROOT):
    idx, nodes, edges = {"symbols": {}}, [], []
    for dp, dns, fns in os.walk(os.path.join(root, "symbols", "schemas")):
        dns.sort()  # deterministic walk order: regenerating must not dirty tracked files
        for fn in sorted(fns):
            if not fn.endswith(".json"): continue
            full = os.path.join(dp, fn); rel = os.path.relpath(full, root)
            try: card = json.load(open(full))
            except Exception: card = {}
            sid = card.get("symbol_id", os.path.splitext(fn)[0]); d = sha256(full)
            idx["symbols"][sid] = {"path": rel, "sha256": d, "tags": card.get("tags", []),
                                   "kind": card.get("kind", "schema")}
            nodes.append({"id": sid, "kind": card.get("kind", "schema"), "path": rel, "sha256": d})
            for up in card.get("edges", {}).get("upstream", []): edges.append({"from": up, "to": sid, "dir": "upstream"})
            for dn in card.get("edges", {}).get("downstream", []): edges.append({"from": sid, "to": dn, "dir": "downstream"})
            for vr in card.get("vault_refs", []): edges.append({"from": sid, "to": vr, "dir": "vault_ref"})
            for rep in card.get("represents", []):
                edges.append({"from": sid, "to": rep.get("symbol_id", rep.get("repo", "?")), "dir": "represents"})
    for dp, dns, fns in os.walk(os.path.join(root, "knowledge_vault")):
        dns.sort()
        for fn in sorted(fns):
            full = os.path.join(dp, fn); rel = os.path.relpath(full, root)
            nodes.append({"id": rel, "kind": "vault", "path": rel, "sha256": sha256(full)})
    for d in ("symbols", "models"): os.makedirs(os.path.join(root, d), exist_ok=True)  # fresh checkouts lack these
    with open(os.path.join(root, "symbols", "symbol_index.json"), "w") as f: json.dump(idx, f, indent=2)
    with open(os.path.join(root, "models", "knowledge_graph.json"), "w") as f:
        json.dump({"nodes": nodes, "edges": edges}, f, indent=2)
    return idx, {"nodes": nodes, "edges": edges}
if __name__ == "__main__":
    idx, g = build()
    print(f"indexed {len(idx['symbols'])} symbols; graph {len(g['nodes'])} nodes / {len(g['edges'])} edges")
