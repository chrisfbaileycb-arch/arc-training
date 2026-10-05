#!/bin/sh
CORE="${1:-ornith-9b-cortex}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
SRV="$ROOT/runtime/linux/llama-b11382/llama-server"
export LD_LIBRARY_PATH="$ROOT/runtime/linux/llama-b11382:$LD_LIBRARY_PATH"
case "$CORE" in
  ornith-9b-cortex) MODEL="$ROOT/models/weights/Ornith-9B-CORTEX-v3-Q4_K_M.gguf"; EXTRA="--temp 0.6 --top-p 0.95" ;;
  mimo-9b-cortex)   MODEL="$ROOT/models/weights/MiMo-9B-CORTEX-v1.1-Q4_K_M.gguf"; EXTRA="--temp 0.6 --top-p 0.95" ;;
  muse-glimmer-30b) MODEL="$ROOT/models/weights/Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf"; EXTRA="--jinja --temp 1.0 --top-p 0.95 --top-k 64" ;;
  muse-glimmer-30b-cortex) MODEL="$ROOT/models/weights/Aegis-Glimmer-30B-CORTEX-v1-Q4_K_M.gguf"; EXTRA="--jinja --temp 1.0 --top-p 0.95 --top-k 64" ;;
  *) echo "unknown core: $CORE"; exit 64 ;;
esac
[ -f "$MODEL" ] || { echo "Model not found: $MODEL"; echo "Run once with internet: python3 download_models.py --core $CORE"; exit 1; }
echo "Starting $CORE at http://127.0.0.1:8080 (Ctrl+C to stop)"
echo "Protocol file: $ROOT/protocol/glimmer_cortex_system_prompt.txt"
exec "$SRV" -m "$MODEL" -c 8192 --host 127.0.0.1 --port 8080 $EXTRA
