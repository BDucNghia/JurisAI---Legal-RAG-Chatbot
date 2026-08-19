from openai import OpenAI
from tqdm import tqdm
import re

from backend.utils.vector_db import get_retriever
from FineTune.prompt_formatter import format_docs_for_prompt

lm_client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
LM_STUDIO_MODEL_NAME = "local-model"

QUESTIONS_FILE = "FineTune/question_1.txt"
PAIRS_FILE = "FineTune/questions_5.jsonl"
KTO_FILE = "FineTune/judges_5.jsonl"

def gen_prompt_strict(context: str, question: str) -> str:
    return f"""
Bạn là một trợ lý pháp lý chuyên nghiệp.

YÊU CẦU BẮT BUỘC:
- Chỉ trả lời dựa trên NGỮ CẢNH (tuyệt đối không suy đoán ngoài ngữ cảnh)
- Nếu ngữ cảnh chưa đủ để kết luận, hãy nói rõ "chưa đủ căn cứ"
- Trả lời rõ ràng, ngắn gọn, đúng trọng tâm

--- NGỮ CẢNH ---
{context}

--- CÂU HỎI ---
{question}

--- CÂU TRẢ LỜI ---
""".strip()

def gen_prompt_loose(context: str, question: str) -> str:
    return f"""
Bạn là một trợ lý AI trả lời câu hỏi pháp luật theo cách tổng quát.

HƯỚNG DẪN:
- Ưu tiên diễn đạt tự nhiên, trôi chảy
- Có thể diễn giải chung chung (không cần bám sát từng chi tiết)
- Nếu không chắc, vẫn cố gắng đưa ra câu trả lời hợp lý

--- NGỮ CẢNH ---
{context}

--- CÂU HỎI ---
{question}

--- CÂU TRẢ LỜI ---
""".strip()

def generate_answer(prompt: str, temperature: float) -> str:
    completion = lm_client.chat.completions.create(
        model=LM_STUDIO_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return completion.choices[0].message.content.strip()

JUDGE_SYSTEM = (
    "You are a strict evaluator. "
    "Follow the provided JSON schema exactly. "
    "Return ONLY a valid JSON object."
)

JUDGE_USER = """
Evaluate groundedness and hallucination based ONLY on the context.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER A:
{answer_a}

ANSWER B:
{answer_b}
""".strip()

def _safe_json_load(s: str):
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(\w+)?", "", s).strip()
        s = s.rstrip("```").strip()
    return json.loads(s)

import json

def judge_pair(context: str, question: str, answer_a: str, answer_b: str) -> dict:
    completion = lm_client.chat.completions.create(
        model=LM_STUDIO_MODEL_NAME,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": JUDGE_USER.format(
                context=context,
                question=question,
                answer_a=answer_a,
                answer_b=answer_b
            )}
        ],
        temperature=0.0,
    )

    raw = completion.choices[0].message.content.strip()
    return json.loads(raw)



def run_generate():
    print("--- PHASE 1: GENERATE A/B PAIRS ---")
    print(">>> Hãy load Qwen/Qwen3-4B-Instruct-2507 trong LM Studio và bật server trước. <<<")

    retriever = get_retriever()
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = [line.strip() for line in f if line.strip()]

    with open(PAIRS_FILE, "w", encoding="utf-8") as out:
        for q in tqdm(questions, desc="Generating pairs"):
            try:
                docs = retriever.invoke(q)
                context = format_docs_for_prompt(docs)

                prompt_a = gen_prompt_strict(context, q)
                prompt_b = gen_prompt_loose(context, q)

                # A: strict & stable, B: loose & diverse
                ans_a = generate_answer(prompt_a, temperature=0.2, max_tokens=512)
                ans_b = generate_answer(prompt_b, temperature=0.7, max_tokens=512)

                record = {
                    "question": q,
                    "context": context,
                    "answer_a": ans_a,
                    "answer_b": ans_b,
                    "gen_meta": {
                        "temp_a": 0.2,
                        "temp_b": 0.7
                    }
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")

            except Exception as e:
                print(f"[SKIP-GEN] {q[:60]}... | {e}")
                continue

    print(f"\n✅ Phase 1 done. Saved pairs to: {PAIRS_FILE}")


def compress_context_for_judge(
    full_context: str,
    answer_a: str,
    answer_b: str,
    max_chars: int = 8000
) -> str:
    """
    Compress long RAG context into evidence-only context for judge.
    max_chars ~ 6000 chars ≈ 3–4k tokens (an toàn cho judge).
    """

    # 1. Trích keyword từ answer A/B
    answers = f"{answer_a} {answer_b}"
    keywords = set()

    # Bắt Điều xx, Khoản xx, %
    for m in re.findall(r"Điều\s+\d+|Khoản\s+\d+|\d+%", answers):
        keywords.add(m)

    # Bắt các từ khóa pháp lý thường gặp
    for kw in ["thử việc", "thai sản", "hợp đồng", "tiền lương", "người lao động"]:
        if kw.lower() in answers.lower():
            keywords.add(kw)

    # 2. Lọc context theo dòng
    lines = full_context.splitlines()
    selected = []

    for line in lines:
        line_l = line.lower()

        # luôn giữ header nguồn
        if line.strip().startswith("--- Nguồn"):
            selected.append(line)
            continue

        # giữ các dòng chứa cấu trúc điều luật
        if any(k in line for k in ["Điều", "Khoản", "Nội dung"]):
            selected.append(line)
            continue

        # giữ nếu match keyword
        if any(k.lower() in line_l for k in keywords):
            selected.append(line)

        # dừng nếu quá dài
        if sum(len(x) for x in selected) >= max_chars:
            break

    # fallback: nếu lọc quá ít, lấy phần đầu context
    if len(selected) < 5:
        return full_context[:max_chars]

    return "\n".join(selected)

def run_judge():
    print("\n--- PHASE 2: JUDGE + FILTER -> KTO DATASET ---")
    print(">>> Bây giờ hãy tắt Qwen, load JUDGE model trong LM Studio. <<<")
    print(">>> Set temperature ~0.0 để judge ổn định. <<<")

    with open(PAIRS_FILE, "r", encoding="utf-8") as f:
        pairs = [json.loads(line) for line in f if line.strip()]

    kept = 0
    discarded = 0

    with open(KTO_FILE, "w", encoding="utf-8") as out:
        for item in tqdm(pairs, desc="Judging"):
            q = item["question"]
            ctx = item["context"]
            a_text = item["answer_a"]
            b_text = item["answer_b"]

            try:
                judge_context = compress_context_for_judge(
                    full_context=ctx,
                    answer_a=a_text,
                    answer_b=b_text,
                    max_chars=8000
                )
                j = judge_pair(judge_context, q, a_text, b_text)

                a = j.get("answer_a", {})
                b = j.get("answer_b", {})
                pref = (j.get("preferred") or "none").strip()

                # Normalize booleans
                a_grounded = bool(a.get("grounded", False))
                a_hallu = bool(a.get("hallucination", False))
                b_grounded = bool(b.get("grounded", False))
                b_hallu = bool(b.get("hallucination", False))

                chosen, rejected = None, None

                # Anti-noise decision rules
                if a_grounded and (not a_hallu) and (not b_grounded):
                    chosen, rejected = a_text, b_text
                elif b_grounded and (not b_hallu) and (not a_grounded):
                    chosen, rejected = b_text, a_text
                elif a_grounded and b_grounded and (not a_hallu) and (not b_hallu):
                    if pref == "A":
                        chosen, rejected = a_text, b_text
                    elif pref == "B":
                        chosen, rejected = b_text, a_text
                    else:
                        discarded += 1
                        continue
                else:
                    discarded += 1
                    continue

                out_record = {
                    "prompt": q,
                    "chosen": chosen,
                    "rejected": rejected,
                    "meta": {
                        "judge": LM_STUDIO_MODEL_NAME,
                        "judge_raw": j,  # giữ lại để audit khoa học
                        "gen_meta": item.get("gen_meta", {}),
                    }
                }
                out.write(json.dumps(out_record, ensure_ascii=False) + "\n")
                kept += 1

            except Exception as e:
                print(f"[SKIP-JUDGE] {q[:60]}... | {e}")
                discarded += 1
                continue

    print(f"\n✅ Phase 2 done. Saved KTO dataset to: {KTO_FILE}")
    print(f"Kept: {kept} | Discarded: {discarded}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2 or sys.argv[1] not in ["generate", "judge"]:
        print("Usage:")
        print("  python FineTune/collect_kto_data_two_phase.py generate")
        print("  python FineTune/collect_kto_data_two_phase.py judge")
        raise SystemExit(1)

    if sys.argv[1] == "generate":
        run_generate()
    else:
        run_judge()
