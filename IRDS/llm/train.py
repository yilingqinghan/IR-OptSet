import os
import torch
from datetime import datetime
from datasets import load_from_disk
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)
from peft import (
    LoraConfig,
    get_peft_model,
)
from IRDS.config.config import ToolchainConfig

# -----------------------------
# Config & Environment
# -----------------------------
config = ToolchainConfig()
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
if config.wandb:
    os.environ["WANDB_API_KEY"] = config.wandb
    os.environ["WANDB_MODE"] = "offline"
    os.environ["WANDB_PROJECT"] = "finetune-ir"

# -----------------------------
# Experiment Settings
# -----------------------------
DATE = datetime.now().strftime("%Y%m%d")
LABEL = "ifconv-lora"
TOKEN_NUM = 2048
LR = 1e-4
EPOCHS = 10
BATCH_SIZE = 2
PER_DEVICE_BATCH = 1
GRAD_ACC = BATCH_SIZE // PER_DEVICE_BATCH

ROOT_DIR = f"/data/dataset/ifconv-{DATE}"
MODEL_PATH = "/models/your-model"
OUTPUT_DIR = f"Adapters/{LABEL}/adapter-{DATE}"
RESUME_CHECKPOINT = os.path.join(OUTPUT_DIR, "checkpoint-750000")

# -----------------------------
# Load Dataset & Tokenizer
# -----------------------------
train_ds = load_from_disk(os.path.join(ROOT_DIR, "train_dataset"))
eval_ds = load_from_disk(os.path.join(ROOT_DIR, "eval_dataset"))

model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
tokenizer.add_eos_token = True
tokenizer.pad_token_id = 2
tokenizer.padding_side = "left"

# -----------------------------
# Tokenizer Processing
# -----------------------------
def tokenize(example):
    encoded = tokenizer(
        example["text"],
        truncation=True,
        max_length=TOKEN_NUM,
        padding=False,
    )
    encoded["labels"] = encoded["input_ids"].copy()
    return encoded

train_ds = train_ds.map(tokenize)
eval_ds = eval_ds.map(tokenize)

# -----------------------------
# LoRA Config
# -----------------------------
peft_cfg = LoraConfig(
    r=32,
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, peft_cfg)
if torch.cuda.device_count() > 1:
    model.is_parallelizable = True
    model.model_parallel = True

# -----------------------------
# Training Args
# -----------------------------
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=PER_DEVICE_BATCH,
    per_device_eval_batch_size=PER_DEVICE_BATCH,
    gradient_accumulation_steps=GRAD_ACC,
    num_train_epochs=EPOCHS,
    warmup_steps=100,
    learning_rate=LR,
    fp16=True,
    logging_steps=500,
    evaluation_strategy="steps",
    save_strategy="steps",
    eval_steps=500,
    save_steps=500,
    save_total_limit=5,
    load_best_model_at_end=True,
    group_by_length=True,
    report_to="wandb" if config.wandb else "none",
    run_name=f"{LABEL}-{DATE}"
)

trainer = Trainer(
    model=model,
    train_dataset=train_ds,
    eval_dataset=eval_ds,
    args=training_args,
    data_collator=DataCollatorForSeq2Seq(
        tokenizer, pad_to_multiple_of=8, return_tensors="pt", padding=True
    ),
)

model.config.use_cache = False

# -----------------------------
# Launch Training
# -----------------------------
if not os.path.exists(RESUME_CHECKPOINT):
    trainer.train()
else:
    print(f"Resuming from {RESUME_CHECKPOINT}...")
    trainer.train(resume_from_checkpoint=RESUME_CHECKPOINT)

print("✅ Training complete")
