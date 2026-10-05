# Friend's-House Offline Test — with YOUR models

## At home (internet), onto the USB drive:
1. This aegis-drive folder (llama.cpp for Windows AND Linux already in runtime/).
2. `python download_models.py --core ornith-9b-cortex`  (~5.6 GB, hash auto-verified)
   Optional: `--core mimo-9b-cortex` (~5.7 GB).

## At the friend's house (NO internet):
1. Windows: double-click `serve-model.bat`. Linux: `./serve-model.sh ornith-9b-cortex`.
2. Open http://127.0.0.1:8080 — llama-server's built-in chat UI.
3. **Turn Wi-Fi OFF. Ask it to write a function. Watch YOUR model answer.**
4. Hash check: sha256 of the .gguf must equal the pinned value in models/cores.json
   (ca2803a2... for Ornith v3). Match = authentic, untampered, yours.

## Honest expectations
- 12 GB PC: 9B Q4_K_M comfortable, a few tok/s on older CPUs. Deliberate, not instant.
- 8 GB PC: close apps, ctx 8192, some paging; still works.
- muse-glimmer-30b is NOT for these boxes — 24 GB+ hosts only.
- Give CORTEX cores >=800 max tokens; they think before they speak.
