from eval_zalo_e5 import evaluate
import json

MODELS = [
    "BAAI/bge-m3",
    "AITeamVN/Vietnamese_Embedding",
    "dangvantuan/vietnamese-embedding"
]

def main():
    split = "test"
    topk = 100
    batch = 128

    results = {}
    for m in MODELS:
        print("\n" + "=" * 80)
        print(f"Evaluating model: {m}")
        print("=" * 80)
        summary, _ = evaluate(
            split=split,
            model_name_or_path=m,
            batch=batch,
            topk=topk,
        )
        results[m] = summary

    with open("multi_model_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nSaved all results to multi_model_results.json")

if __name__ == "__main__":
    main()
