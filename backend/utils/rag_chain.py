import os

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
from langchain.output_parsers import OutputFixingParser


class Citation(BaseModel):
    law_name: str = Field(..., description="Tên văn bản luật")
    chapter: str = Field("0", description="Số chương của văn bản luật")
    section: str = Field("0", description="Số mục của văn bản luật")
    article: str = Field("0", description="Số điều của văn bản luật")

class AnswerWithCitations(BaseModel):
    content: str = Field(..., description="Câu trả lời chi tiết cho câu hỏi của người dùng")
    citations: List[Citation] = Field(description="Danh sách các nguồn trích dẫn liên quan đến câu trả lời")

def format_docs_for_prompt(docs: List[Document]) -> str:
    """
    Định dạng lại context để hiển thị cho LLM, đánh số từng nguồn.
    """
    formatted_docs = []
    for i, doc in enumerate(docs):
        context_str = (
            f"--- Nguồn trích dẫn số {i+1} ---\n"
            f"Tên văn bản: {doc.metadata.get('document_name', 'N/A')}\n"
            f"Chương: {doc.metadata.get('chapter', 'N/A')}\n"
            f"Mục: {doc.metadata.get('section', 'N/A')}\n"
            f"Điều: {doc.metadata.get('article', 'N/A')}\n"
            f"Nội dung: {doc.page_content}\n"
            f"---------------------------------"
        )
        formatted_docs.append(context_str)
    return "\n\n".join(formatted_docs)


def get_llm():
    print("Đang khởi tạo LLM bằng cách kết nối đến Local Server (LM Studio)...")
    url = "http://localhost:1234/v1"
    if os.getenv("DOCKER_CONTAINER"):
        url = "http://host.docker.internal:1234/v1"
    llm = ChatOpenAI(
        base_url=url,
        api_key="not-needed",
        model_name="local-model",
        temperature=0.1,
        max_tokens=4096,
    )
    return llm


def create_rag_chain(retriever, llm):
    print("Đang tạo RAG chain với output JSON...")
    base_parser = JsonOutputParser(pydantic_object=AnswerWithCitations)
    output_parser = OutputFixingParser.from_llm(parser=base_parser, llm=llm)
    prompt_template = """
    Bạn là một AI trợ lý pháp lý cực kỳ chính xác. Nhiệm vụ của bạn là trả lời câu hỏi của người dùng và trích dẫn nguồn một cách cẩn thận dựa trên ngữ cảnh được cung cấp.

    Ngữ cảnh (bao gồm nhiều nguồn trích dẫn được đánh số):
    {context}

    DỰA VÀO CÂU HỎI VÀ NGỮ CẢNH TRÊN, hãy thực hiện 2 nhiệm vụ sau:
    1. Viết một câu trả lời chi tiết và chính xác cho câu hỏi của người dùng.
    2. KHÔNG được trích dẫn những nguồn không liên quan.
    3. Trả về 1 văn bản không xuống hàng dòng, không có ký tự đặc biệt.
    Câu hỏi của người dùng: {question}

    Hãy trả về một đối tượng JSON duy nhất theo định dạng sau:
    {format_instructions}
    """
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"],
        partial_variables={"format_instructions": output_parser.get_format_instructions()},
    )

    rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | RunnablePassthrough.assign(context=lambda x: format_docs_for_prompt(x["context"]))
            | prompt
            | llm
            | output_parser
    )

    print("Tạo RAG chain thành công!")
    return rag_chain