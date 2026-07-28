import os
from dotenv import load_dotenv

if not os.getenv("DOCKER_CONTAINER"):
    PROJECT_ROOT_LOCAL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    dotenv_path = os.path.join(PROJECT_ROOT_LOCAL, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print("Cảnh báo: Không tìm thấy file .env ở thư mục gốc của project.")
else:
    PROJECT_ROOT_LOCAL = None

def get_default_path(subpath):
    return os.path.join(PROJECT_ROOT_LOCAL, *subpath.split('/')) if PROJECT_ROOT_LOCAL else subpath

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", get_default_path('data/db'))
LOCAL_EMBEDDING_MODEL_PATH = os.getenv("LOCAL_EMBEDDING_MODEL_PATH", get_default_path('data/embed_model'))

DATA_FINAL_PATH = os.getenv("DATA_FINAL_PATH", get_default_path('data/data_final'))

EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"
LLM_MODEL_NAME = "gemini-1.5-flash"
DEVICE = "cpu" # or "cuda"

VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chroma").lower()

PINECONE_INDEX_NAME = "jurisaiv1"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

print("--- Cấu hình đường dẫn đã được tải ---")
print(f"Chạy trong Docker: {bool(os.getenv('DOCKER_CONTAINER'))}")
print(f"Đường dẫn ChromaDB: {CHROMA_DB_PATH}")
print(f"Đường dẫn Embedding Model: {LOCAL_EMBEDDING_MODEL_PATH}")
print(f"Đường dẫn Data Final: {DATA_FINAL_PATH}")
print("------------------------------------")
