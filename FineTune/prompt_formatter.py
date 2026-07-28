from langchain_core.documents import Document
from typing import List

def format_docs_for_prompt(docs: List[Document]) -> str:
    formatted_docs = []
    for i, doc in enumerate(docs):
        metadata = doc.metadata
        context_str = (
            f"--- Nguồn trích dẫn số {i+1} ---\n"
            f"Tên văn bản: {metadata.get('document_name', 'N/A')}\n"
            f"Chương: {metadata.get('chapter', 'N/A')}\n"
            f"Mục: {metadata.get('section', 'N/A')}\n"
            f"Điều: {metadata.get('article', 'N/A')}\n"
            f"Nội dung: {doc.page_content}\n"
            f"---------------------------------"
        )
        formatted_docs.append(context_str)
    return "\n\n".join(formatted_docs)

def create_generation_prompt_for_finetune(context: str, question: str) -> str:
    prompt = (
        f"Bạn là một trợ lý AI chuyên về luật pháp Việt Nam.\n"
        f"Nhiệm vụ của bạn là trả lời câu hỏi của người dùng một cách chính xác dựa trên các thông tin, điều luật được cung cấp trong phần Ngữ cảnh dưới đây. Hãy chỉ trả lời mà KHÔNG cần nói câu 'Dựa theo nguồn trích dẫn đã cung cấp' hoặc các câu tương tự.\n\n"
        f"--- Ngữ cảnh ---\n"
        f"{context}\n\n"
        f"--- Câu hỏi ---\n"
        f"{question}\n\n"
        f"--- Câu trả lời chi tiết ---\n"
    )
    return prompt