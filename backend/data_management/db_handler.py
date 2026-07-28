import chromadb
import sys
import os
from langchain_community.vectorstores import Chroma
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config.config import CHROMA_DB_PATH
from backend.utils.vector_db import get_embeddings

BATCH_SIZE = 1000

def get_vectorstore():
    embeddings = get_embeddings()
    return Chroma(
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_PATH
    )

def add_chunks_to_db(chunks):
    if not chunks:
        print("Không có chunk nào để thêm.")
        return

    vectorstore = get_vectorstore()
    total_chunks = len(chunks)
    print(f"Đang thêm {total_chunks} chunk vào cơ sở dữ liệu...")
    for i in tqdm(range(0, total_chunks, BATCH_SIZE), desc="Đang nạp dữ liệu vào DB"):
        batch = chunks[i:i + BATCH_SIZE]
        vectorstore.add_documents(batch)

    print("\nThêm tất cả các chunk vào cơ sở dữ liệu thành công.")


def delete_docs_from_db(filenames):
    if not filenames:
        print("Không có tên file nào được cung cấp để xóa.")
        return

    print("Đang kết nối tới ChromaDB để xóa tài liệu...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection("langchain")

    for filename in filenames:
        results = collection.get(where={"source": filename}, include=[])
        ids_to_delete = results['ids']

        if ids_to_delete:
            print(f"Tìm thấy {len(ids_to_delete)} chunk của file '{filename}' để xóa.")
            collection.delete(ids=ids_to_delete)
            print(f"Đã xóa thành công các chunk của file '{filename}'.")
        else:
            print(f"Không tìm thấy chunk nào của file '{filename}' trong DB.")