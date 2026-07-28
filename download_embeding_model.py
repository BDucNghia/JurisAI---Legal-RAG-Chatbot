from huggingface_hub import snapshot_download
from backend.config.config import LOCAL_EMBEDDING_MODEL_PATH, EMBEDDING_MODEL_NAME

snapshot_download(
    repo_id=EMBEDDING_MODEL_NAME,
    local_dir=LOCAL_EMBEDDING_MODEL_PATH,
    local_dir_use_symlinks=False,
    revision="main"
)

print(f"Tải mô hình '{EMBEDDING_MODEL_NAME}' hoàn tất tại: {LOCAL_EMBEDDING_MODEL_PATH}")
