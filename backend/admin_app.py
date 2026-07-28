import streamlit as st
import os
import subprocess
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from config.config import DATA_FINAL_PATH
from backend.data_management.ingester import ingest_specific_files

st.set_page_config(page_title="Trang Quản trị Chatbot Pháp luật", layout="wide")

st.title("⚙️ Bảng điều khiển Dữ liệu - Chatbot Pháp luật")
st.caption(f"Cập nhật lần cuối: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def run_script(script_name, section, args=None):
    command = [sys.executable, "-m", script_name]
    if args:
        command.extend(args)
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    with st.spinner(f"⏳ Đang chạy {script_name}... Vui lòng chờ..."):
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )

        output_placeholder = section.empty()
        stdout_log = ""

        for line_bytes in iter(process.stdout.readline, b''):
            line_str = line_bytes.decode('utf-8', errors='replace')
            stdout_log += line_str
            output_placeholder.code(stdout_log, language='bash')

        process.wait()

        stderr_bytes = process.stderr.read()
        stderr_log = stderr_bytes.decode('utf-8', errors='replace')

        if process.returncode != 0:
            section.error(f"Lỗi khi chạy {script_name}:")
            full_log = f"--- STDOUT ---\n{stdout_log}\n\n--- STDERR ---\n{stderr_log}"
            output_placeholder.code(full_log, language='bash')
        else:
            section.success(f"✅ Hoàn tất! {script_name} đã chạy thành công.")


tab1, tab2, tab3 = st.tabs(["➕ Thêm Tài liệu", "❌ Xóa Tài liệu", "📂 Xem Kho Dữ liệu"])

DOMAIN_OPTIONS = ["BHXH", "Lao động", "Thuế TNCN"]
TYPE_OPTIONS = ["Luật", "Nghị Định"]

# --- Tab 1: Thêm Tài liệu ---
with tab1:
    st.header("Nạp các văn bản luật mới vào Cơ sở dữ liệu")
    st.info(f"Các file upload sẽ được lưu tạm thời, sau đó được lưu vào vị trí bạn chọn trong: `{DATA_FINAL_PATH}`")

    uploaded_files = st.file_uploader(
        "Chọn một hoặc nhiều file .docx",
        accept_multiple_files=True,
        type="docx",
        key="file_uploader"
    )

    if uploaded_files:
        if 'file_configs' not in st.session_state:
            st.session_state.file_configs = {}

        st.write("---")
        st.subheader("Cấu hình vị trí lưu cho từng file:")

        current_configs = {}
        for uploaded_file in uploaded_files:
            file_id = f"{uploaded_file.name}-{uploaded_file.size}"

            config = st.session_state.file_configs.get(file_id, {
                "name": uploaded_file.name,
                "domain": DOMAIN_OPTIONS[0],
                "type": TYPE_OPTIONS[0],
                "file_object": uploaded_file
            })

            st.write(f"**File:** `{uploaded_file.name}`")
            cols = st.columns(2)
            config['domain'] = cols[0].selectbox(
                "Chọn Chủ đề (Domain):",
                options=DOMAIN_OPTIONS,
                index=DOMAIN_OPTIONS.index(config['domain']),
                key=f"domain_{file_id}"
            )
            config['type'] = cols[1].selectbox(
                "Chọn Loại văn bản:",
                options=TYPE_OPTIONS,
                index=TYPE_OPTIONS.index(config['type']),
                key=f"type_{file_id}"
            )
            st.write("---")

            current_configs[file_id] = config

        st.session_state.file_configs = current_configs

        if st.button("🚀 Bắt đầu Nạp dữ liệu", key="ingest"):
            paths_to_ingest = []
            with st.spinner("Đang lưu file và chuẩn bị nạp..."):
                for file_id, config in st.session_state.file_configs.items():
                    uploaded_file = config.get("file_object")
                    if uploaded_file:
                        dest_folder = os.path.join(DATA_FINAL_PATH, config['domain'], config['type'])
                        os.makedirs(dest_folder, exist_ok=True)
                        dest_path = os.path.join(dest_folder, config['name'])

                        with open(dest_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        paths_to_ingest.append(dest_path)
                        st.write(f"Đã lưu file vào: `{dest_path}`")

            st.info("Đã lưu file thành công. Bắt đầu quá trình nạp vào Vector DB...")

            with st.spinner("Đang xử lý và nạp dữ liệu vào DB... Việc này có thể mất vài phút."):
                success, message = ingest_specific_files(paths_to_ingest)
                if success:
                    st.success(message)
                    st.session_state.file_configs = {}
                    st.rerun()
                else:
                    st.error(message)

# --- Tab 2: Xóa Tài liệu ---
with tab2:
    st.header("Xóa các văn bản luật khỏi Cơ sở dữ liệu và Kho lưu trữ")
    st.warning("⚠️ Hành động này sẽ xóa vĩnh viễn dữ liệu khỏi Vector DB và kho 'data_final'. Hãy cẩn thận!")

    try:
        all_files_in_final = []
        for root, _, files in os.walk(DATA_FINAL_PATH):
            for file in files:
                if file.endswith('.docx'):
                    relative_path = os.path.relpath(os.path.join(root, file), DATA_FINAL_PATH)
                    all_files_in_final.append(relative_path.replace("\\", "/"))

        if not all_files_in_final:
            st.info("Kho lưu trữ 'data_final' đang trống.")
        else:
            files_to_delete_selection = st.multiselect(
                "Chọn các file cần xóa (có thể chọn nhiều):",
                options=sorted(all_files_in_final)
            )

            if st.button("🗑️ Bắt đầu Xóa các file đã chọn", key="delete"):
                if not files_to_delete_selection:
                    st.error("Bạn chưa chọn file nào để xóa.")
                else:
                    st.write("Bắt đầu quá trình xóa...")
                    run_script("data_management.delete_chunk", st, args=files_to_delete_selection)
                    st.button("Làm mới danh sách file")

    except FileNotFoundError:
        st.info("Kho lưu trữ 'data_final' chưa được tạo.")

# --- Tab 3: Xem Kho Dữ liệu ---
with tab3:
    st.header(f"Danh sách các tài liệu hiện có trong Kho lưu trữ (`{DATA_FINAL_PATH}`)")

    try:
        file_list = []
        for root, _, files in os.walk(DATA_FINAL_PATH):
            for file in files:
                if file.endswith('.docx'):
                    relative_path = os.path.relpath(os.path.join(root, file), DATA_FINAL_PATH)
                    file_list.append(relative_path)

        if file_list:
            st.dataframe(sorted(file_list), use_container_width=True, column_config={"value": "Đường dẫn file"})
        else:
            st.info("Hiện không có tài liệu nào trong kho lưu trữ.")

    except FileNotFoundError:
        st.warning("Thư mục 'data_final' không tồn tại.")