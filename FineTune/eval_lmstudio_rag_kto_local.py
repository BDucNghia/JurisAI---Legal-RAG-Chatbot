import argparse
import json
import os
import re
import time
from typing import Any, Dict, List

from openai import OpenAI

from backend.utils.vector_db import get_retriever
from FineTune.prompt_formatter import format_docs_for_prompt

# LM Studio client
lm_client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

def generate_answer(
    model_name: str,
    prompt: str,
    temperature: float,
    max_tokens: int = 512,
    json_mode: bool = False,
    retries: int = 3,
) -> str:
    """
    Call LM Studio (OpenAI-compatible). Optionally try JSON mode.
    If JSON mode is not supported, it falls back automatically.
    """
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            kwargs = dict(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            completion = lm_client.chat.completions.create(**kwargs)
            return (completion.choices[0].message.content or "").strip()
        except Exception as e:
            last_err = e
            # If JSON mode caused failure, retry without it
            if json_mode:
                json_mode = False
            time.sleep(0.7 * attempt)

    raise RuntimeError(f"LM Studio call failed after retries: {last_err}")


# IO helpers
def read_questions_txt(path: str) -> List[Dict[str, str]]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        i = 0
        for line in f:
            q = line.strip()
            if not q:
                continue
            i += 1
            items.append({"id": f"q{i:03d}", "question": q})
    return items


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def iter_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def extract_first_json_object(text: str) -> Dict[str, Any]:
    # direct
    try:
        return json.loads(text)
    except Exception:
        pass
    # first {...}
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON object found in response.")
    j = m.group(0)
    # clean trailing commas
    j = re.sub(r",\s*}", "}", j)
    j = re.sub(r",\s*]", "]", j)
    return json.loads(j)



# Prompt templates
def build_answer_prompt(question: str, context: str) -> str:
    return (
        "Bạn là trợ lý pháp luật.\n"
        "Hãy trả lời NGẮN GỌN, ĐÚNG TRỌNG TÂM.\n"
        "Nếu ngữ cảnh không đủ để trả lời chắc chắn,hãy nêu rõ giới hạn của ngữ cảnh trước khi kết luận.\n\n"
        f"Câu hỏi:\n{question}\n\n"
        f"Ngữ cảnh:\n{context}\n\n"
        "Trả lời:"
    )


def build_single_judge_prompt(question: str, context: str, answer: str) -> str:
    return (
        "You are a strict legal evaluator.\n"
        "Given a Question, Context (sources), and an Answer, judge groundedness.\n\n"
        f"Question:\n{question}\n\n"
        f"Context:\n{context}\n\n"
        f"Answer:\n{answer}\n\n"
        "Return STRICT JSON only:\n"
        "{\n"
        '  "grounded": true/false,\n'
        '  "hallucination": true/false,\n'
        '  "short_reason": "one short sentence"\n'
        "}\n"
        "Rules:\n"
        "- grounded=true if the main conclusion is supported by the context,even if some minor details are missing.\n"
        "- hallucination=true if the answer adds unsupported legal conditions, numbers, articles, or facts not present.\n"
    )


def build_pairwise_judge_prompt(question: str, context: str, answer_a: str, answer_b: str) -> str:
    return (
        "You are a strict legal evaluator.\n"
        "Compare Answer A vs Answer B given the same Question and Context.\n"
        "Prefer answers that are correct, grounded in the context, and concise.\n\n"
        f"Question:\n{question}\n\n"
        f"Context:\n{context}\n\n"
        f"Answer A:\n{answer_a}\n\n"
        f"Answer B:\n{answer_b}\n\n"
        "Return STRICT JSON only:\n"
        '{ "preferred": "A" | "B" | "tie", "reason": "short" }\n'
    )



# Phase 1: Build eval_with_context.jsonl
def cmd_build_ctx(args):
    qs = read_questions_txt(args.questions)

    retriever = get_retriever()

    rows = []
    for i, it in enumerate(qs, start=1):
        q = it["question"]

        # Your requested snippet:
        docs = retriever.invoke(q)
        context = format_docs_for_prompt(docs)

        rows.append({"id": it["id"], "question": q, "context": context})

        if args.progress and i % args.progress == 0:
            print(f"[CTX] {i}/{len(qs)} retrieved")

    write_jsonl(args.out, rows)
    print(f"[CTX] Wrote: {args.out} ({len(rows)} rows)")



# Phase 2: Generate answers (base or kto)
def cmd_gen(args):
    items = list(iter_jsonl(args.eval_with_context))

    out_rows = []
    for i, it in enumerate(items, start=1):
        prompt = build_answer_prompt(it["question"], it["context"])
        ans = generate_answer(
            model_name=args.model,
            prompt=prompt,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            json_mode=False,
        )
        out_rows.append({
            "id": it["id"],
            "question": it["question"],
            "context": it["context"],
            "answer": ans,
            "meta": {"model": args.model, "temperature": args.temperature, "max_tokens": args.max_tokens},
        })

        if args.progress and i % args.progress == 0:
            print(f"[GEN] {i}/{len(items)} done")

    write_jsonl(args.out, out_rows)
    print(f"[GEN] Wrote: {args.out} ({len(out_rows)} rows)")



# Phase 3: Judge single (grounded/hallu)
def cmd_judge_single(args):
    rows = list(iter_jsonl(args.pred))
    out = []

    for i, r in enumerate(rows, start=1):
        prompt = build_single_judge_prompt(r["question"], r["context"], r["answer"])
        raw = generate_answer(
            model_name=args.judge_model,
            prompt=prompt,
            temperature=0.0,
            max_tokens=256,
            json_mode=args.json_mode,
        )

        try:
            obj = extract_first_json_object(raw)
            out.append({
                "id": r["id"],
                "grounded": bool(obj.get("grounded")),
                "hallucination": bool(obj.get("hallucination")),
                "short_reason": str(obj.get("short_reason", ""))[:300],
            })
        except Exception as e:
            out.append({
                "id": r["id"],
                "grounded": None,
                "hallucination": None,
                "short_reason": f"PARSE_ERROR: {e}",
                "raw_head": raw[:500],
            })

        if args.progress and i % args.progress == 0:
            print(f"[J1] {i}/{len(rows)} done")

    write_jsonl(args.out, out)
    print(f"[J1] Wrote: {args.out} ({len(out)} rows)")


# Phase 4: Judge pairwise (A=base, B=kto)
def cmd_judge_pairwise(args):
    base = {r["id"]: r for r in iter_jsonl(args.pred_a)}
    kto = {r["id"]: r for r in iter_jsonl(args.pred_b)}
    ids = sorted(set(base.keys()) & set(kto.keys()))

    out = []
    for i, _id in enumerate(ids, start=1):
        q = base[_id]["question"]
        ctx = base[_id]["context"]
        prompt = build_pairwise_judge_prompt(q, ctx, base[_id]["answer"], kto[_id]["answer"])

        raw = generate_answer(
            model_name=args.judge_model,
            prompt=prompt,
            temperature=0.0,
            max_tokens=128,
            json_mode=args.json_mode,
        )

        try:
            obj = extract_first_json_object(raw)
            pref = str(obj.get("preferred", "tie")).strip()
            if pref not in ("A", "B", "tie"):
                pref = "tie"
            out.append({"id": _id, "preferred": pref, "reason": str(obj.get("reason", ""))[:300]})
        except Exception as e:
            out.append({"id": _id, "preferred": "tie", "reason": f"PARSE_ERROR: {e}", "raw_head": raw[:500]})

        if args.progress and i % args.progress == 0:
            print(f"[J2] {i}/{len(ids)} done")

    write_jsonl(args.out, out)
    print(f"[J2] Wrote: {args.out} ({len(out)} rows)")



# Phase 5: Metrics
def cmd_metrics(args):
    base = list(iter_jsonl(args.judge_base))
    kto = list(iter_jsonl(args.judge_kto))
    pair = list(iter_jsonl(args.judge_pairwise))

    def rate(rows, key, truth=True):
        vals = [r.get(key) for r in rows if r.get(key) is not None]
        if not vals:
            return None
        return sum(1 for v in vals if v == truth) / len(vals)

    base_grounded = rate(base, "grounded", True)
    kto_grounded = rate(kto, "grounded", True)
    base_hallu = rate(base, "hallucination", True)
    kto_hallu = rate(kto, "hallucination", True)

    valid = [r for r in pair if r.get("preferred") in ("A", "B")]
    kto_wins = sum(1 for r in valid if r["preferred"] == "B")  # B = KTO
    base_wins = sum(1 for r in valid if r["preferred"] == "A")
    ties = sum(1 for r in pair if r.get("preferred") == "tie")
    win_rate = (kto_wins / len(valid)) if valid else None

    print("=== EVAL METRICS (RAG) ===")
    print(f"N: base={len(base)} | kto={len(kto)}")
    print()
    print(f"Base grounded rate:       {base_grounded}")
    print(f"KTO  grounded rate:       {kto_grounded}")
    print()
    print(f"Base hallucination rate:  {base_hallu}")
    print(f"KTO  hallucination rate:  {kto_hallu}")



def main():
    ap = argparse.ArgumentParser("Eval Base vs KTO using LM Studio + local retriever.invoke()")
    ap.add_argument("--progress", type=int, default=10)

    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("build_ctx")
    p1.add_argument("--questions", required=True, help="questions.txt (1 per line)")
    p1.add_argument("--out", required=True, help="eval_with_context.jsonl")
    p1.set_defaults(func=cmd_build_ctx)

    p2 = sub.add_parser("gen")
    p2.add_argument("--eval-with-context", required=True)
    p2.add_argument("--model", default="local-model", help="LM Studio model name")
    p2.add_argument("--out", required=True)
    p2.add_argument("--temperature", type=float, default=0.2)
    p2.add_argument("--max-tokens", type=int, default=512)
    p2.set_defaults(func=cmd_gen)

    p3 = sub.add_parser("judge_single")
    p3.add_argument("--pred", required=True)
    p3.add_argument("--judge-model", required=True)
    p3.add_argument("--out", required=True)
    p3.add_argument("--json-mode", action="store_true")
    p3.set_defaults(func=cmd_judge_single)

    p4 = sub.add_parser("judge_pairwise")
    p4.add_argument("--pred-a", required=True, help="pred_base.jsonl")
    p4.add_argument("--pred-b", required=True, help="pred_kto.jsonl")
    p4.add_argument("--judge-model", required=True)
    p4.add_argument("--out", required=True)
    p4.add_argument("--json-mode", action="store_true")
    p4.set_defaults(func=cmd_judge_pairwise)

    p5 = sub.add_parser("metrics")
    p5.add_argument("--judge-base", required=True)
    p5.add_argument("--judge-kto", required=True)
    p5.add_argument("--judge-pairwise", required=True)
    p5.set_defaults(func=cmd_metrics)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
