import argparse
import json
import random
from typing import Any, Dict, Optional, Tuple


def get_first(d: Dict[str, Any], paths: list[str]) -> Optional[Any]:
    """Get nested value by dotted paths, return first found."""
    for p in paths:
        cur = d
        ok = True
        for part in p.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok:
            return cur
    return None


def normalize_bool(x: Any) -> bool:
    if isinstance(x, bool):
        return x
    if isinstance(x, str):
        s = x.strip().lower()
        if s in ("true", "yes", "1"):
            return True
        if s in ("false", "no", "0"):
            return False
    if isinstance(x, (int, float)):
        return bool(x)
    return False


def extract_judge_obj(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Try to locate judge result object in many common locations.
    Expected schema:
    {
      "answer_a": {"grounded": bool, "hallucination": bool},
      "answer_b": {"grounded": bool, "hallucination": bool},
      "preferred": "A"|"B"|"none"
    }
    """
    candidate = get_first(item, [
        "judge",
        "judge_result",
        "judge_raw",
        "meta.judge",
        "meta.judge_raw",
        "meta.judge_result",
        "evaluation",
        "eval",
    ])
    if not isinstance(candidate, dict):
        return None

    # Some pipelines store judge under candidate["judge_raw"] again
    if "answer_a" not in candidate and "preferred" not in candidate:
        inner = get_first(candidate, ["judge", "judge_raw", "judge_result"])
        if isinstance(inner, dict):
            candidate = inner

    if not (isinstance(candidate.get("answer_a"), dict) and isinstance(candidate.get("answer_b"), dict)):
        return None

    preferred = candidate.get("preferred", "none")
    if isinstance(preferred, str):
        preferred = preferred.strip()
    candidate["preferred"] = preferred
    return candidate


def decide_pair(
    answer_a: str,
    answer_b: str,
    judge: Dict[str, Any],
    require_grounded: bool = True,
    require_no_hallu: bool = True,
) -> Optional[Tuple[str, str, str]]:
    """
    Returns (chosen, rejected, preferred) or None (discard).
    """
    pref = str(judge.get("preferred", "none")).strip().upper()
    if pref not in ("A", "B"):
        return None

    a = judge.get("answer_a", {})
    b = judge.get("answer_b", {})

    a_grounded = normalize_bool(a.get("grounded", False))
    a_hallu = normalize_bool(a.get("hallucination", False))
    b_grounded = normalize_bool(b.get("grounded", False))
    b_hallu = normalize_bool(b.get("hallucination", False))

    if pref == "A":
        chosen, rejected = answer_a, answer_b
        cg, ch = a_grounded, a_hallu
    else:
        chosen, rejected = answer_b, answer_a
        cg, ch = b_grounded, b_hallu

    if require_grounded and not cg:
        return None
    if require_no_hallu and ch:
        return None

    return chosen, rejected, pref


def main():
    ap = argparse.ArgumentParser(description="Convert judged pairs JSONL -> KTO JSONL (prompt/chosen/rejected).")
    ap.add_argument("--in", dest="inp", required=True, help="Input judged JSONL file.")
    ap.add_argument("--out", dest="out", required=True, help="Output KTO JSONL file.")
    ap.add_argument("--require-grounded", action="store_true", default=True, help="Keep only if chosen grounded=true.")
    ap.add_argument("--allow-ungrounded", action="store_true", help="If set, do NOT require grounded for chosen.")
    ap.add_argument("--require-no-hallu", action="store_true", default=True, help="Keep only if chosen hallucination=false.")
    ap.add_argument("--allow-hallu", action="store_true", help="If set, allow hallucination in chosen.")
    ap.add_argument("--keep-meta", action="store_true", help="Keep judge object in meta for auditing.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--show-samples", type=int, default=5, help="Print N random kept samples summary.")
    args = ap.parse_args()

    require_grounded = (not args.allow_ungrounded)
    require_no_hallu = (not args.allow_hallu)

    random.seed(args.seed)

    total = 0
    kept = 0
    discarded = 0
    missing_judge = 0
    missing_fields = 0

    kept_examples = []

    with open(args.inp, "r", encoding="utf-8") as f_in, open(args.out, "w", encoding="utf-8") as f_out:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            total += 1

            try:
                item = json.loads(line)
            except Exception:
                discarded += 1
                continue

            # Accept either "question" or "prompt"
            prompt = item.get("question") or item.get("prompt")
            answer_a = item.get("answer_a")
            answer_b = item.get("answer_b")

            if not (isinstance(prompt, str) and isinstance(answer_a, str) and isinstance(answer_b, str)):
                missing_fields += 1
                discarded += 1
                continue

            judge = extract_judge_obj(item)
            if judge is None:
                missing_judge += 1
                discarded += 1
                continue

            decision = decide_pair(
                answer_a=answer_a,
                answer_b=answer_b,
                judge=judge,
                require_grounded=require_grounded,
                require_no_hallu=require_no_hallu,
            )
            if decision is None:
                discarded += 1
                continue

            chosen, rejected, pref = decision

            out_rec: Dict[str, Any] = {
                "prompt": prompt,
                "chosen": chosen,
                "rejected": rejected,
            }
            if args.keep_meta:
                out_rec["meta"] = {"preferred": pref, "judge": judge}

            f_out.write(json.dumps(out_rec, ensure_ascii=False) + "\n")
            kept += 1

            if len(kept_examples) < 200:
                kept_examples.append((prompt, pref))

    print("\n=== KTO export summary ===")
    print("Input lines:       ", total)
    print("Kept (KTO pairs):   ", kept)
    print("Discarded:          ", discarded)
    if total:
        print("Keep ratio:         ", f"{kept/total:.2%}")
    print("Missing judge obj:  ", missing_judge)
    print("Missing fields:     ", missing_fields)

    if args.show_samples > 0 and kept_examples:
        print("\nRandom kept samples:")
        for prompt, pref in random.sample(kept_examples, k=min(args.show_samples, len(kept_examples))):
            print(f"- pref={pref} | {prompt[:120]}{'...' if len(prompt) > 120 else ''}")


if __name__ == "__main__":
    main()
