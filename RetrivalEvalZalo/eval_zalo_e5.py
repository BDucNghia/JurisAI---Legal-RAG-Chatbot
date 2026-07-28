from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

import faiss  # type: ignore
import numpy as np
from datasets import load_dataset
from sentence_transformers import SentenceTransformer, CrossEncoder
from tqdm import tqdm


def format_passages_text(title: str, text: str) -> str:
    """Format passage text cho mô hình retrieval bất đối xứng (E5/BGE...)."""
    title = (title or "").strip()
    body = (text or "").strip()
    if title and body:
        return f"passage: {title}. {body}"
    elif body:
        return f"passage: {body}"
    else:
        return f"passage: {title}"


def format_query_text(q: str) -> str:
    """Format query cho E5 (non-instruct)."""
    return f"query: {q.strip()}"


# ---------------------------
# Metrics
# ---------------------------

def dcg_at_k(rel: List[int], k: int) -> float:
    rel_k = np.array(rel[:k], dtype=float)
    if rel_k.size == 0:
        return 0.0
    discounts = 1.0 / np.log2(np.arange(2, rel_k.size + 2))
    return float((rel_k * discounts).sum())


def ndcg_at_k(rel: List[int], k: int) -> float:
    dcg = dcg_at_k(rel, k)
    ideal = dcg_at_k(sorted(rel, reverse=True), k)
    return 0.0 if ideal == 0 else dcg / ideal


def mrr_at_k(ranks: List[int], k: int) -> float:
    ranks_in_k = [r for r in ranks if r <= k]
    if not ranks_in_k:
        return 0.0
    return 1.0 / min(ranks_in_k)


def recall_at_k(ranks: List[int], k: int) -> float:
    return 1.0 if any(r <= k for r in ranks) else 0.0


# ---------------------------
# Dataset loaders
# ---------------------------

def load_corpus() -> Tuple[List[str], List[str]]:
    """Load Zalo legal corpus, trả về (ids, texts) với format E5."""
    corpus = load_dataset(
        "GreenNode/zalo-ai-legal-text-retrieval-vn",
        "corpus",
        split="corpus"
    )
    ids: List[str] = []
    texts: List[str] = []
    for row in corpus:
        _id = row["_id"]
        title = row.get("title", "")
        text = row.get("text", "")
        ids.append(_id)
        texts.append(format_passages_text(title, text))
    return ids, texts


def load_queries() -> Dict[str, str]:
    """Load queries thành dict {query_id: text}."""
    queries = load_dataset(
        "GreenNode/zalo-ai-legal-text-retrieval-vn",
        "queries",
        split="queries"
    )
    return {row["_id"]: row["text"] for row in queries}


def load_qrels(split: str) -> Dict[str, List[str]]:
    """
    Load qrels thành dict {query_id: [relevant_corpus_id, ...]}.
    split: 'train' hoặc 'test'
    """
    assert split in {"train", "test"}
    qrels_ds = load_dataset(
        "GreenNode/zalo-ai-legal-text-retrieval-vn",
        "default",
        split=split,
    )
    rels: Dict[str, List[str]] = defaultdict(list)
    for row in qrels_ds:
        if float(row["score"]) > 0:
            rels[row["query-id"]].append(row["corpus-id"])
    return rels


# ---------------------------
# Corpus embeddings cache
# ---------------------------

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def build_or_load_corpus_embeddings(
    model: SentenceTransformer,
    batch_size: int = 128,
    cache_dir: Optional[str] = None,
) -> Tuple[List[str], List[str], faiss.IndexFlatIP]:
    """
    Tạo hoặc load sẵn corpus embeddings, trả về:
        (corpus_ids, corpus_texts, faiss_index)

    Nếu có cache_dir:
      - Thử load:
          cache_dir/corpus_ids.json
          cache_dir/corpus_texts.json
          cache_dir/corpus_embs.npy
      - Nếu chưa có → embed corpus lần đầu và lưu lại.
    """

    ids_path = texts_path = embs_path = None
    if cache_dir is not None:
        _ensure_dir(cache_dir)
        ids_path = os.path.join(cache_dir, "corpus_ids.json")
        texts_path = os.path.join(cache_dir, "corpus_texts.json")
        embs_path = os.path.join(cache_dir, "corpus_embs.npy")

    if cache_dir is not None and all(os.path.exists(p) for p in (ids_path, texts_path, embs_path)):
        print(f"Đang tải corpus embeddings từ cache: {cache_dir}")
        with open(ids_path, "r", encoding="utf-8") as f:
            corpus_ids = json.load(f)
        with open(texts_path, "r", encoding="utf-8") as f:
            corpus_texts = json.load(f)
        mat = np.load(embs_path).astype("float32")
    else:
        print("Đang tải corpus Zalo và tạo embeddings (lần đầu)...")
        corpus_ids, corpus_texts = load_corpus()
        all_embs = []
        for i in tqdm(range(0, len(corpus_texts), batch_size), desc="Embedding corpus"):
            batch_texts = corpus_texts[i:i + batch_size]
            embs = model.encode(
                batch_texts,
                batch_size=batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            all_embs.append(embs.astype("float32"))
        mat = np.vstack(all_embs).astype("float32")
        print("Kích thước embedding corpus:", mat.shape)

        if cache_dir is not None:
            print(f"Lưu cache corpus embeddings vào: {cache_dir}")
            with open(ids_path, "w", encoding="utf-8") as f:
                json.dump(corpus_ids, f, ensure_ascii=False)
            with open(texts_path, "w", encoding="utf-8") as f:
                json.dump(corpus_texts, f, ensure_ascii=False)
            np.save(embs_path, mat)

    dim = mat.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(mat)
    return corpus_ids, corpus_texts, index


# ---------------------------
# Evaluate
# ---------------------------

def evaluate(
    split: str,
    model_name_or_path: str,
    batch: int = 128,
    topk: int = 100,
    reranker_name: Optional[str] = None,
    rerank_topk: Optional[int] = None,
    cache_dir: Optional[str] = None,
) -> Tuple[Dict, Dict[str, Dict[str, float]]]:
    """
    Đánh giá embedding model trên Zalo Legal (train/test).

    Nếu truyền cache_dir:
        - Lần đầu: embed corpus và lưu cache.
        - Các lần sau: chỉ load lại corpus embeddings, không embed lại nữa.
    """
    print(f"Đang tải mô hình embedding: {model_name_or_path}")
    device = "cuda"
    try:
        import torch
        if not torch.cuda.is_available():
            device = "cpu"
    except Exception:
        device = "cpu"
    print(f"Sử dụng device cho embedding: {device}")

    embed_model = SentenceTransformer(model_name_or_path, device=device)
    # Giới hạn seq length để đỡ tốn VRAM
    try:
        embed_model.max_seq_length = 256
    except Exception:
        pass

    reranker = None    # CrossEncoder
    if reranker_name:
        print(f"Đang tải reranker: {reranker_name}")
        reranker = CrossEncoder(reranker_name, device=device)

    if rerank_topk is None:
        rerank_topk = topk

    print("Đang chuẩn bị corpus index (có cache nếu cấu hình)...")
    corpus_ids, corpus_texts, index = build_or_load_corpus_embeddings(
        embed_model,
        batch_size=batch,
        cache_dir=cache_dir,
    )

    print("Đang tải queries & qrels...")
    queries = load_queries()
    qrels = load_qrels(split)

    eval_qids = [qid for qid in qrels.keys() if qid in queries]
    print(f"Số lượng truy vấn để đánh giá (split={split}): {len(eval_qids)}")

    R1 = R5 = R10 = R20 = R50 = 0.0
    MRR10 = MRR100 = 0.0
    NDCG10 = NDCG100 = 0.0

    per_query_stats: Dict[str, Dict[str, float]] = {}

    for qid in tqdm(eval_qids, desc="Đang evaluate"):
        raw_query = queries[qid]
        q_text = format_query_text(raw_query)
        q_emb = embed_model.encode(
            [q_text],
            batch_size=1,
            show_progress_bar=False,
            normalize_embeddings=True,
        ).astype("float32")

        sims, idxs = index.search(q_emb, topk)
        idxs = idxs[0].tolist()
        retrieved_ids = [corpus_ids[i] for i in idxs]

        # Rerank bằng CrossEncoder (nếu có)
        if reranker is not None:
            pairs = []
            for i in idxs:
                doc_text = corpus_texts[i]
                # Bỏ prefix "passage:" cho sạch input reranker
                if doc_text.lower().startswith("passage:"):
                    doc_clean = doc_text.split(":", 1)[1].strip()
                else:
                    doc_clean = doc_text
                pairs.append((raw_query, doc_clean))

            scores = reranker.predict(pairs, batch_size=32)
            scores = np.array(scores)
            order = np.argsort(-scores)  # sort desc
            idxs = [idxs[i] for i in order]
            retrieved_ids = [retrieved_ids[i] for i in order]

        # Giới hạn theo rerank_topk
        idxs = idxs[:rerank_topk]
        retrieved_ids = retrieved_ids[:rerank_topk]

        rel_set = set(qrels[qid])
        rel_flags = [1 if doc_id in rel_set else 0 for doc_id in retrieved_ids]
        ranks = [i + 1 for i, doc_id in enumerate(retrieved_ids) if doc_id in rel_set]

        r1 = recall_at_k(ranks, 1)
        r5 = recall_at_k(ranks, 5)
        r10 = recall_at_k(ranks, 10)
        r20 = recall_at_k(ranks, 20)
        r50 = recall_at_k(ranks, 50)
        mrr10 = mrr_at_k(ranks, 10)
        mrr100 = mrr_at_k(ranks, 100)
        ndcg10 = ndcg_at_k(rel_flags, 10)
        ndcg100 = ndcg_at_k(rel_flags, 100)

        R1 += r1; R5 += r5; R10 += r10; R20 += r20; R50 += r50
        MRR10 += mrr10; MRR100 += mrr100
        NDCG10 += ndcg10; NDCG100 += ndcg100

        per_query_stats[qid] = {
            "recall@1": r1,
            "recall@5": r5,
            "recall@10": r10,
            "recall@20": r20,
            "recall@50": r50,
            "mrr@10": mrr10,
            "mrr@100": mrr100,
            "ndcg@10": ndcg10,
            "ndcg@100": ndcg100,
        }

    n = len(eval_qids)
    summary = {
        "split": split,
        "model": model_name_or_path,
        "num_queries": n,
        "reranker": reranker_name,
        "topk": topk,
        "rerank_topk": rerank_topk,
        "recall@1": R1 / n,
        "recall@5": R5 / n,
        "recall@10": R10 / n,
        "recall@20": R20 / n,
        "recall@50": R50 / n,
        "mrr@10": MRR10 / n,
        "mrr@100": MRR100 / n,
        "ndcg@10": NDCG10 / n,
        "ndcg@100": NDCG100 / n,
    }

    print("\n=== TỔNG KẾT ===")
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"{k:>12s}: {v:.4f}")
        else:
            print(f"{k:>12s}: {v}")

    return summary, per_query_stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["train", "test"], default="test")
    parser.add_argument("--model-path", default="intfloat/multilingual-e5-large")
    parser.add_argument("--batch", type=int, default=128)
    parser.add_argument("--topk", type=int, default=100)
    parser.add_argument("--reranker", type=str, default=None,
                        help="Tên mô hình CrossEncoder dùng để rerank (optional).")
    parser.add_argument("--rerank-topk", type=int, default=None,
                        help="Số doc giữ lại sau rerank (mặc định = topk).")
    parser.add_argument("--cache-dir", type=str, default="zalo_corpus_cache",
                        help="Thư mục lưu cache embedding của corpus.")
    parser.add_argument("--save-json", type=str, default=None,
                        help="Nếu set, lưu summary + per-query metrics vào file JSON.")
    args = parser.parse_args()

    summary, per_query = evaluate(
        split=args.split,
        model_name_or_path=args.model_path,
        batch=args.batch,
        topk=args.topk,
        reranker_name=args.reranker,
        rerank_topk=args.rerank_topk,
        cache_dir=args.cache_dir,
    )

    if args.save_json:
        out = {"summary": summary, "per_query": per_query}
        with open(args.save_json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"Đã lưu kết quả vào: {args.save_json}")


if __name__ == "__main__":
    main()
