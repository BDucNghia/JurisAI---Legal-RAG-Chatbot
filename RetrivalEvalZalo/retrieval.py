import logging
import os
from collections import defaultdict
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from sentence_transformers.evaluation import InformationRetrievalEvaluator

# Thiết lập logging để xem tiến trình
logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

# --- 1. Tải mô hình và bộ dữ liệu ---
LOCAL_MODEL_PATH = "embed_model"
dataset_name = 'GreenNode/zalo-ai-legal-text-retrieval-vn'

if not os.path.isdir(LOCAL_MODEL_PATH):
    raise FileNotFoundError(f"Thư mục mô hình không được tìm thấy tại: '{os.path.abspath(LOCAL_MODEL_PATH)}'.")

logging.info(f"Đang tải mô hình từ đường dẫn cục bộ: {LOCAL_MODEL_PATH}...")
model = SentenceTransformer(LOCAL_MODEL_PATH)

logging.info(f"Đang tải bộ dữ liệu: {dataset_name}...")
# Tải corpus: chứa các văn bản
corpus_dataset = load_dataset(dataset_name, 'corpus', split='corpus')
# Tải queries: chứa các câu hỏi
queries_dataset = load_dataset(dataset_name, 'queries', split='queries')
# Tải ground truth: chứa ánh xạ (query-id, corpus-id)
ground_truth_dataset = load_dataset(dataset_name, 'default', split='train')

# --- 2. Chuẩn bị dữ liệu cho việc đánh giá ---
logging.info("Chuẩn bị dữ liệu cho evaluator...")

# Tạo corpus: một từ điển có dạng {doc_id: doc_text}
# Dựa trên subset 'corpus', cột ID là '_id'
corpus = {doc['_id']: "passage: " + doc['text'] for doc in corpus_dataset}

# Tạo queries: một từ điển có dạng {query_id: query_text}
# Dựa trên subset 'queries', cột ID là '_id'
queries = {item['_id']: "query: " + item['text'] for item in queries_dataset}

# Tạo relevant_docs: ánh xạ từ query_id đến một tập hợp các doc_id liên quan
# Dữ liệu này được lấy từ subset 'default'
relevant_docs = defaultdict(set)
for item in ground_truth_dataset:
    query_id = item['query-id']
    corpus_id = item['corpus-id']
    relevant_docs[query_id].add(corpus_id)

# Chuyển defaultdict thành dict thông thường
relevant_docs = dict(relevant_docs)

# --- 3. Thực hiện đánh giá ---
logging.info("Tạo InformationRetrievalEvaluator...")
evaluator = InformationRetrievalEvaluator(queries, corpus, relevant_docs, name='zalo-legal-retrieval')

logging.info("Bắt đầu quá trình đánh giá...")
# Thực hiện đánh giá trên mô hình
results = evaluator(model, output_path="results/")

logging.info("Đánh giá hoàn tất.")
print("Kết quả đánh giá:")
print(results)