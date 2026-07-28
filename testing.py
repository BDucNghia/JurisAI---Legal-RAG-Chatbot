import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import time
import torch

# Bạn nên import các biến cấu hình từ config.py để đảm bảo tính nhất quán
from backend.config.config import (
    EMBEDDING_MODEL_NAME, DEVICE, LOCAL_EMBEDDING_MODEL_PATH
)

CHROMA_DB_PATH = "data/db"
LOCAL_EMBEDDING_MODEL_PATH = "data/embed_model"
FILE = "test_e5_output.txt"

def get_embeddings():
    """
    Hàm này khởi tạo và TRẢ VỀ model embedding.
    """
    print(f"Đang tải model embedding...")

    model_to_load = None  # Khởi tạo biến

    # Kiểm tra xem đường dẫn local có tồn tại không
    if LOCAL_EMBEDDING_MODEL_PATH and os.path.exists(LOCAL_EMBEDDING_MODEL_PATH):
        print(
            f"Sử dụng mô hình embedding từ đường dẫn local: {os.path.abspath(LOCAL_EMBEDDING_MODEL_PATH)} trên thiết bị {DEVICE}...")
        model_to_load = LOCAL_EMBEDDING_MODEL_PATH
    else:
        print(
            f"Không tìm thấy mô hình local hoặc đường dẫn không được cấu hình. Đang tải từ Hugging Face Hub: {EMBEDDING_MODEL_NAME} trên thiết bị {DEVICE}...")
        model_to_load = EMBEDDING_MODEL_NAME

    return HuggingFaceEmbeddings(
        model_name=model_to_load,
        model_kwargs={'device': DEVICE}
    )


# --- Bắt đầu phần chạy thử ---
print("--- Bắt đầu chạy file test.py ---")

# Bước 1: Lấy embedding function. Giờ đây nó sẽ trả về một đối tượng hợp lệ.
embeddings = get_embeddings()

if embeddings is None:
    print("LỖI: Hàm get_embeddings() đã không trả về một đối tượng embedding hợp lệ.")
else:
    print("\n--- Tải cơ sở dữ liệu ChromaDB ---")
    # Bước 2: Tải vectorstore từ local, cung cấp embedding function hợp lệ
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings  # Bây giờ biến này là một đối tượng HuggingFaceEmbeddings, không còn là None
    )

    print("\n--- Tạo Retriever ---")
    # Bước 3: Tạo retriever
    retriever = vectorstore.as_retriever(search_kwargs={'k': 10})

    print("\n--- Thực hiện truy vấn ví dụ ---")
    # Bước 4: Thực hiện truy vấn
    query = 'Tôi muốn hỏi về quyền lợi bảo hiểm xã hội của người lao động trong trường hợp nghỉ thai sản.'
    retrieved_docs = retriever.invoke(query)

    print(f"\nCâu hỏi: {query}")
    print("\n--- Các tài liệu được truy vấn (kết quả từ retriever): ---")
    print(retrieved_docs)

    for _ in range(3):
        _ = retriever.invoke(query)
    torch.cuda.synchronize()
    start = time.time()
    _ = retriever.invoke(query)
    torch.cuda.synchronize()
    end = time.time()

    # Ghi kết quả vào file để kiểm tra
    with open(FILE, 'w', encoding="utf-8") as f:
        f.write("Câu hỏi:\n")
        f.write(query + "\n\n")
        f.write("Kết quả truy vấn:\n")
        f.write(str(retrieved_docs))
        f.write("\n\n")
        f.write(f"Query latency: {end - start:.4f} seconds")



