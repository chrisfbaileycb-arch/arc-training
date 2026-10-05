# Wiring Hey Buddy to this drive

The contract: llama-server exposes an OpenAI-compatible API at http://localhost:8080/v1
(any non-empty API key string works).

## Case A — provider calls happen in YOUR browser (most likely)
1. Start a core on the drive machine: `serve-model.bat` or `./serve-model.sh <core>`.
2. Hey Buddy -> Settings and model hub -> add provider -> "OpenAI Compatible":
   Base URL http://localhost:8080/v1, key EMPTY, model name = the .gguf filename.
3. In Agent Studio, create/edit an agent and paste
   `protocol/glimmer_cortex_system_prompt.txt` into its INSTRUCTION & SCOPE field —
   that is the CORE-SPEC v4.2 runtime injection for Aegis-Glimmer-30B.
4. PROOF: turn Wi-Fi OFF and ask for a function. Answers = truly local.
   Network error = calls route through the hosted backend (Case B).

## Case B — calls route through Hey Buddy's hosted backend
localhost is unreachable from Render's servers. Options, best first:
1. Self-host Hey Buddy on the same machine/LAN as the drive; use localhost or LAN IP.
2. Run the model server with --host 0.0.0.0 on a LAN machine; point the backend at the LAN IP
   (`python serve.py --lan` prints addresses).
3. Tunnel (ngrok-style) — works but BREAKS the air-gap; document if ever used.

## Extras
- Knowledge hub: upload MEMORY.md or vault cards as knowledge documents.
- Generation settings: give the 9B CORTEX cores >=800 max tokens (reasoning models).
- Use muse-glimmer-30b on strong hosts for multimodal/tool-heavy agents.
