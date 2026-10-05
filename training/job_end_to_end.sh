#!/usr/bin/env bash
# Aegis-Glimmer-30B-CORTEX — one-shot HF Job. Stages: setup -> train -> merge ->
# convert -> quantize -> LOAD GATE -> serve -> SPEC BATTERY -> upload.
# Mirrors the 9B pipeline (train/merge-quant/publish/battery) in a single run.
set -euo pipefail
echo "=== [0/7] setup ==="
pip install -q -U "transformers>=5.3" "trl>=1.13" peft bitsandbytes accelerate datasets trackio "huggingface_hub[hf_transfer]"
apt-get update -qq && apt-get install -y -qq git build-essential cmake > /dev/null
git clone --depth 1 https://github.com/ggml-org/llama.cpp.git /opt/llama.cpp
pip install -q -r /opt/llama.cpp/requirements.txt
hf download Johnny5b/cortex-training-kit --repo-type dataset --local-dir /work/kit
cd /work/kit
python training/build_corpus_v5.py && python training/expand_corpus_v5.py        # regenerates + re-gates the full corpus

echo "=== [1/7] train (QLoRA r=16 a=32, 2ep, lr 2e-4 cosine, nf4) ==="
python training/train_qlora.py --corpus training/corpus_v5_muse_cortex_full.jsonl

echo "=== [2/7] merge ==="
python - <<'PY'
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
base = AutoModelForCausalLM.from_pretrained("meta-models/Muse-Glimmer-30B",
    torch_dtype=torch.bfloat16, device_map="cpu")
m = PeftModel.from_pretrained(base, "aegis-glimmer-30b-cortex-adapter/final")
m = m.merge_and_unload()
m.save_pretrained("aegis-glimmer-30b-cortex-merged", safe_serialization=True)
AutoTokenizer.from_pretrained("meta-models/Muse-Glimmer-30B").save_pretrained("aegis-glimmer-30b-cortex-merged")
print("merged ok")
PY

echo "=== [3/7] convert to GGUF (f16) ==="
python /opt/llama.cpp/convert_hf_to_gguf.py aegis-glimmer-30b-cortex-merged \
    --outfile aegis-glimmer-30b-cortex-f16.gguf

echo "=== [4/7] build llama.cpp + quantize Q4_K_M ==="
cmake -S /opt/llama.cpp -B /opt/llama.cpp/build -DLLAMA_CURL=OFF
cmake --build /opt/llama.cpp/build --config Release -j$(nproc) --target llama-quantize llama-bench llama-server
/opt/llama.cpp/build/bin/llama-quantize aegis-glimmer-30b-cortex-f16.gguf \
    Aegis-Glimmer-30B-CORTEX-v1-Q4_K_M.gguf Q4_K_M

echo "=== [5/7] LOAD GATE (llama-bench must run, not just load) ==="
/opt/llama.cpp/build/bin/llama-bench -m Aegis-Glimmer-30B-CORTEX-v1-Q4_K_M.gguf -p 16 -n 8

echo "=== [6/7] SPEC BATTERY (CORE-SPEC v4.2, must exit 0) ==="
/opt/llama.cpp/build/bin/llama-server -m Aegis-Glimmer-30B-CORTEX-v1-Q4_K_M.gguf \
    -c 8192 --host 127.0.0.1 --port 8080 --jinja --temp 1.0 --top-p 0.95 --top-k 64 &
SRV=$!
sleep 60
python protocol/battery_glimmer_cortex.py --base http://127.0.0.1:8080
BATTERY=$?
kill $SRV || true
if [ "$BATTERY" != "0" ]; then echo "BATTERY FAILED — do not publish"; exit 1; fi

echo "=== [7/7] hash + upload ==="
sha256sum Aegis-Glimmer-30B-CORTEX-v1-Q4_K_M.gguf | tee Aegis-Glimmer-30B-CORTEX-v1-Q4_K_M.gguf.sha256
huggingface-cli upload Johnny5b/Muse-Glimmer-30B-CORTEX-GGUF \
    Aegis-Glimmer-30B-CORTEX-v1-Q4_K_M.gguf \
    Aegis-Glimmer-30B-CORTEX-v1-Q4_K_M.gguf.sha256
echo "PUBLISHED. Fill training/model_cardTEMPLATE.md with the receipts and push it as the repo README."
