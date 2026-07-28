import os
from .parser import parse_legal_document
from .db_handler import add_chunks_to_db


def ingest_specific_files(list_of_file_paths):
    print("--- BẮT ĐẦU QUY TRÌNH NẠP CÁC FILE CỤ THỂ ---")

    all_new_chunks = []

    if not list_of_file_paths:
        print("Không có file nào được cung cấp để nạp.")
        return False, "Không có file nào được cung cấp."

    for file_path in list_of_file_paths:
        if os.path.exists(file_path) and file_path.endswith('.docx'):
            chunks = parse_legal_document(file_path)
            all_new_chunks.extend(chunks)
        else:
            print(f"Cảnh báo: Bỏ qua file không hợp lệ hoặc không tồn tại: {file_path}")

    if not all_new_chunks:
        print("Không tạo được chunk nào từ các file được cung cấp.")
        return False, "Không tạo được chunk nào."

    add_chunks_to_db(all_new_chunks)

    print("--- QUY TRÌNH NẠP TÀI LIỆU MỚI HOÀN TẤT ---")
    return True, f"Đã nạp thành công dữ liệu từ {len(list_of_file_paths)} file."
