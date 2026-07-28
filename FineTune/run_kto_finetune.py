import os
import re
import torch
from datasets import load_dataset, Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig
from trl import KTOTrainer, KTOConfig, apply_chat_template
import re
import hashlib

def dedup_context_by_sources(context: str) -> str:
    if not context:
        return context

    # Chuẩn hóa xuống dòng
    ctx = context.replace("\r\n", "\n").strip()

    # Tách theo marker nguồn
    # Mỗi block sẽ bắt đầu bằng '--- Nguồn trích dẫn số'
    parts = re.split(r"(?=---\s*Nguồn trích dẫn số\s*\d+\s*---)", ctx, flags=re.IGNORECASE)

    seen = set()
    kept = []
    for p in parts:
        p = p.strip()
        if not p:
            continue

        # Hash theo nội dung "cốt lõi" để bắt trùng (bỏ số nguồn)
        core = re.sub(r"---\s*Nguồn trích dẫn số\s*\d+\s*---", "--- Nguồn trích dẫn ---", p, flags=re.IGNORECASE)
        core = re.sub(r"[ \t]+", " ", core)
        core = re.sub(r"\n{3,}", "\n\n", core).strip()

        h = hashlib.sha256(core.encode("utf-8")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        kept.append(p)

    return "\n\n".join(kept).strip()


os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:128")

# =========================
# 1) Model / Quantization
# =========================
model_id = "Qwen/Qwen3-4B-Instruct-2507"


bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    attn_implementation="sdpa",
)

model.config.use_cache = False
model.gradient_checkpointing_enable()

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# =========================
# 2) LoRA config
# =========================
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)

# =========================
# 3) Load dataset (JSONL: question/context/chosen_answer/rejected_answer)
# =========================
data_path = "K=10/judge_data.jsonl"
print(f"Loading dataset: {data_path}")
raw = load_dataset("json", data_files=data_path, split="train")

required_cols = {"question", "context", "chosen_answer", "rejected_answer"}
missing = required_cols - set(raw.column_names)
if missing:
    raise ValueError(f"Dataset thiếu cột: {missing}. Cần có: {sorted(required_cols)}")

# =========================
# 4) Helpers: làm sạch + cắt context để tránh quá dài (giúp khỏi OOM)
# =========================
def normalize_ws(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def truncate_by_chars(text: str, max_chars: int = 6000) -> str:
    # cắt theo ký tự cho đơn giản; sau này muốn chuẩn theo token thì mình chỉnh tiếp
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n[...đã rút gọn ngữ cảnh...]"

SYSTEM_PROMPT = (
    "Bạn là trợ lý pháp lý. Chỉ trả lời dựa trên NGỮ CẢNH được cung cấp. "
    "Nếu ngữ cảnh không đủ để kết luận, hãy nói rõ 'Không đủ thông tin trong ngữ cảnh'. "
    "Trả lời ngắn gọn, đúng trọng tâm."
)

def build_user_prompt(question: str, context: str) -> str:
    question = normalize_ws(question)

    # ✅ khử trùng lặp trước
    context = dedup_context_by_sources(normalize_ws(context))

    # ✅ rồi mới cắt ngắn để tránh OOM
    context = truncate_by_chars(context, max_chars=6000)

    return (
        "CÂU HỎI:\n"
        f"{question}\n\n"
        "NGỮ CẢNH (trích từ văn bản pháp luật):\n"
        f"{context}\n\n"
        "YÊU CẦU:\n"
        "- Trả lời đúng theo ngữ cảnh.\n"
        "- Không bịa thêm ngoài ngữ cảnh.\n"
    )


# =========================
# 5) Convert -> unpaired KTO format: prompt (messages), completion (messages), label (bool)
# =========================
def to_rows(example):
    prompt_msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(example["question"], example["context"])},
    ]

    chosen_row = {
        "prompt": prompt_msgs,
        "completion": [{"role": "assistant", "content": normalize_ws(example["chosen_answer"])}],
        "label": True,
    }

    rejected_row = {
        "prompt": prompt_msgs,
        "completion": [{"role": "assistant", "content": normalize_ws(example["rejected_answer"])}],
        "label": False,
    }

    # trả về list 2 dict (2 rows)
    return {"rows": [chosen_row, rejected_row]}

tmp = raw.map(to_rows, remove_columns=raw.column_names)

# tmp["rows"] là list các list => flatten thành dataset mới
all_rows = []
for r in tmp["rows"]:
    all_rows.extend(r)

unpaired = Dataset.from_list(all_rows)

# apply_chat_template: giờ mỗi row prompt/completion là list messages đúng format
unpaired = unpaired.map(
    apply_chat_template,
    fn_kwargs={"tokenizer": tokenizer},
)

unpaired = unpaired.shuffle(seed=42)

print("Example after processing:")
print("label:", unpaired[0]["label"])
print("prompt (first 200 chars):", unpaired[0]["prompt"][:200].replace("\n", "\\n"))
print("completion (first 200 chars):", unpaired[0]["completion"][:200].replace("\n", "\\n"))

# =========================
# 6) KTO config
# =========================
output_dir = "./qwen3-kto-adapter"

kto_args = KTOConfig(
    output_dir=output_dir,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=16,
    learning_rate=5e-5,
    max_steps=200,
    logging_steps=10,
    save_steps=50,
    fp16=True,
    optim="paged_adamw_8bit",


    max_prompt_length=768,
    max_length=768,

    beta=0.1,
)

# =========================
# 7) Train
# =========================
trainer = KTOTrainer(
    model=model,
    args=kto_args,
    train_dataset=unpaired,
    processing_class=tokenizer,
    peft_config=lora_config,
)

print("Start KTO training...")
trainer.train()

final_path = os.path.join(output_dir, "final_checkpoint")
trainer.save_model(final_path)
print(f"Saved LoRA adapter to: {final_path}")
