from langchain_core.documents import Document
from typing import List

def filter_duplicate_chunks(chunks: List[Document]) -> List[Document]:
    seen_contents = set()
    unique_chunks = []

    print(f"Bắt đầu lọc trùng lặp từ {len(chunks)} chunks...")

    for chunk in chunks:
        if chunk.page_content not in seen_contents:
            unique_chunks.append(chunk)
            seen_contents.add(chunk.page_content)

    num_duplicates = len(chunks) - len(unique_chunks)
    if num_duplicates > 0:
        print(f"Đã phát hiện và loại bỏ {num_duplicates} chunk bị trùng lặp.")
    else:
        print("Không tìm thấy chunk nào bị trùng lặp.")

    return unique_chunks