import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.data_management.db_handler import delete_docs_from_db
from backend.config.config import DATA_FINAL_PATH

def process_single_old_document(relative_path_to_delete):
    """
    Xóa một tài liệu cụ thể dựa trên đường dẫn tương đối của nó.
    """
    if not relative_path_to_delete:
        print("Lỗi: Không có đường dẫn tương đối nào được cung cấp.")
        return

    # Lấy ra tên file để xóa khỏi DB
    filename_only = os.path.basename(relative_path_to_delete)
    print(f"--- Bắt đầu quá trình xóa tài liệu '{filename_only}' ---")

    # 1. Xóa khỏi DB dựa trên tên file
    delete_docs_from_db([filename_only])

    # 2. Xóa file vật lý trong kho lưu trữ chính
    path_in_final_folder = os.path.join(DATA_FINAL_PATH, relative_path_to_delete)

    print("\nĐang xóa file vật lý...")
    if os.path.exists(path_in_final_folder):
        os.remove(path_in_final_folder)
        print(f"  - Đã xóa file khỏi kho lưu trữ: {path_in_final_folder}")
    else:
        print(f"  - Lưu ý: Không tìm thấy file tương ứng tại: {path_in_final_folder}")

    print(f"--- Hoàn tất xóa '{filename_only}' ---")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for rel_path in sys.argv[1:]:
            process_single_old_document(rel_path)
    else:
        print("Lỗi: Vui lòng cung cấp ít nhất một đường dẫn tương đối của file cần xóa.")
        print(
            "Ví dụ: python -m data_management.delete_chunk \"BHXH/Luật/file_a.docx\" \"Lao động/Nghị định/file_b.docx\"")
