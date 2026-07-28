import os
import shutil
import sys
from tqdm import tqdm

from .parser import parse_legal_document
from .db_handler import add_chunks_to_db
from .utils import filter_duplicate_chunks
from backend.config.config import DATA_FINAL_PATH, CHROMA_DB_PATH


def build_full_database():
    print("--- BẮT ĐẦU XÂY DỰNG LẠI TOÀN BỘ DB ---")

    if os.path.exists(CHROMA_DB_PATH):
        print(f"Đang xóa DB cũ tại: '{CHROMA_DB_PATH}'...")
        shutil.rmtree(CHROMA_DB_PATH)
        print("Xóa thành công.")

    all_chunks = []
    print(f"Đang quét tài liệu từ: '{DATA_FINAL_PATH}'...")
    for root, _, files in os.walk(DATA_FINAL_PATH):
        for file in tqdm(files, desc="Đang xử lý file"):
            if file.endswith('.docx'):
                file_path = os.path.join(root, file)
                all_chunks.extend(parse_legal_document(file_path))

    if not all_chunks:
        print("Không tìm thấy hoặc không tạo được chunk nào.")
        return

    print(f"\nTổng cộng đã tạo được {len(all_chunks)} chunks.")

    unique_chunks = filter_duplicate_chunks(all_chunks)
    add_chunks_to_db(unique_chunks)

    print("\n--- HOÀN TẤT XÂY DỰNG LẠI DB ---")


if __name__ == "__main__":
    confirm = input("CẢNH BÁO: Hành động này sẽ XÓA DB hiện tại và xây dựng lại từ đầu. Bạn có chắc chắn? (yes/no): ")
    if confirm.lower() == 'yes':
        build_full_database()
    else:
        print("Đã hủy bỏ.")