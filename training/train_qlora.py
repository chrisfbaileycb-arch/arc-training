#!/usr/bin/env python3
"""Aegis-Glimmer-30B-CORTEX — QLoRA SFT (runs on the GPU job box).
Proven recipe from the 9B CORTEX runs, scaled for 30B. Training-phase only:
transformers/torch never ship to the runtime drive."""
import argparse, torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

p = argparse.ArgumentParser()
p.add_argument("--base", default="meta-models/Muse-Glimmer-30B")
p.add_argument("--corpus", default="training/corpus_v5_muse_cortex_full.jsonl")
p.add_argument("--out", default="aegis-glimmer-30b-cortex-adapter")
p.add_argument("--seq", type=int, default=2048)
p.add_argument("--epochs", type=float, default=2.0)
p.add_argument("--lr", type=float, default=2e-4)
a = p.parse_args()

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_use_double_quant=True,
                         bnb_4bit_compute_dtype=torch.bfloat16)
tok = AutoTokenizer.from_pretrained(a.base)
model = AutoModelForCausalLM.from_pretrained(a.base, quantization_config=bnb,
                                             device_map="auto", torch_dtype=torch.bfloat16)
model.config.use_cache = False

ds = load_dataset("json", data_files=a.corpus, split="train")
print(f"corpus rows: {len(ds)}")

peft_cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
                      task_type="CAUSAL_LM", target_modules="all-linear")
cfg = SFTConfig(
    output_dir=a.out,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,          # effective batch 8 (the proven setting)
    num_train_epochs=a.epochs,
    learning_rate=a.lr,
    lr_scheduler_type="cosine",
    logging_steps=5,
    save_strategy="epoch",
    bf16=True,
    gradient_checkpointing=True,
    max_length=a.seq,
    report_to="trackio",
    run_name="aegis-glimmer-30b-cortex-v1",
)
trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds,
                     peft_config=peft_cfg, processing_class=tok)
trainer.train()
trainer.save_model(a.out + "/final")
tok.save_pretrained(a.out + "/final")
print("ADAPTER SAVED:", a.out + "/final")
