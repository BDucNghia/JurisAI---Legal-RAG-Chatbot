import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_pinecone import Pinecone
from pinecone import Pinecone as PineconeClient

from backend.config.config import (
    VECTOR_DB_TYPE, PINECONE_API_KEY, PINECONE_INDEX_NAME,
    CHROMA_DB_PATH, EMBEDDING_MODEL_NAME, DEVICE, LOCAL_EMBEDDING_MODEL_PATH
)

def get_embeddings():
    model_to_load = None
    print(LOCAL_EMBEDDING_MODEL_PATH)
    if LOCAL_EMBEDDING_MODEL_PATH and os.path.isdir(LOCAL_EMBEDDING_MODEL_PATH):
        print(f"Sử dụng mô hình từ đường dẫn local: {os.path.abspath(LOCAL_EMBEDDING_MODEL_PATH)}")
        model_to_load = LOCAL_EMBEDDING_MODEL_PATH
    else:
        print(f"Sử dụng mô hình từ Hugging Face Hub: {EMBEDDING_MODEL_NAME}")
        model_to_load = EMBEDDING_MODEL_NAME
    return HuggingFaceEmbeddings(
        model_name=model_to_load,
        model_kwargs={'device': DEVICE}
    )

def get_retriever():
    embeddings = get_embeddings()

    if VECTOR_DB_TYPE == "pinecone":
        print(f"Đang kết nối đến Pinecone index '{PINECONE_INDEX_NAME}'...")
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY không được tìm thấy trong file .env")

        pinecone_client = PineconeClient(api_key=PINECONE_API_KEY)
        if PINECONE_INDEX_NAME not in pinecone_client.list_indexes().names():
            raise ValueError(f"Index '{PINECONE_INDEX_NAME}' không tồn tại trên Pinecone.")

        vectorstore = Pinecone.from_existing_index(PINECONE_INDEX_NAME, embeddings)
        print("Kết nối Pinecone thành công!")

    elif VECTOR_DB_TYPE == "chroma":
        print(f"Đang tải cơ sở dữ liệu ChromaDB từ đường dẫn: {CHROMA_DB_PATH}...")
        vectorstore = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embeddings
        )
        print("Tải ChromaDB thành công!")

    else:
        raise ValueError(
            f"Loại Vector DB '{VECTOR_DB_TYPE}' không được hỗ trợ. Vui lòng chọn 'pinecone' hoặc 'chroma'.")

    return vectorstore.as_retriever(search_kwargs={'k': 5})