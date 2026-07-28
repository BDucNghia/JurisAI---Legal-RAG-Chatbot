from huggingface_hub import snapshot_download
import os

MODEL_ID = "intfloat/multilingual-e5-large"
LOCAL_MODEL_PATH = "data/embed_model"

snapshot_download(
    repo_id=MODEL_ID,
    local_dir=LOCAL_MODEL_PATH,
    local_dir_use_symlinks=False,
    revision="main"
)

print(f"Tải mô hình '{MODEL_ID}' hoàn tất tại: {os.path.abspath(LOCAL_MODEL_PATH)}")
