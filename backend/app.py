from flask import Flask, request, jsonify
from flask_cors import CORS

from backend.utils.vector_db import get_retriever
from backend.utils.rag_chain import get_llm, create_rag_chain

print("--- BẮT ĐẦU KHỞI TẠO HỆ THỐNG CHATBOT ---")


try:
    retriever = get_retriever()
    llm = get_llm()
    rag_chain = create_rag_chain(retriever, llm)
    print("\n--- HỆ THỐNG ĐÃ SẴN SÀNG! ---")
except Exception as e:
    print(f"LỖI NGHIÊM TRỌNG KHI KHỞI TẠO: {e}")


# --- Khởi tạo Flask App ---
app = Flask(__name__)
CORS(app)

@app.route('/api/chat', methods=['POST'])
def chat_handler():
    """
    API endpoint để nhận câu hỏi và trả về câu trả lời trực tiếp từ RAG chain.
    """
    try:
        incoming_payload = request.get_json()
        question = incoming_payload.get('content')

        if not question:
            return jsonify({"error": "Trường 'content' là bắt buộc."}), 400

        print(f"\nNhận được câu hỏi: {question}")

        # --- Gọi RAG chain trực tiếp ---
        rag_output = rag_chain.invoke(question)
        print(f"Câu trả lời từ RAG: {rag_output}")

        # --- Xây dựng payload trả về ---
        response_payload = {
            "account_id": incoming_payload.get("account_id"),
            "conversations_id": incoming_payload.get("conversations_id"),
            "model_chat": incoming_payload.get("model_chat"),
            "message_id": incoming_payload.get("message_id"),
            "answer": rag_output.get("content"),
            "citations": rag_output.get("citations")
        }

        return jsonify(response_payload)

    except Exception as e:
        print(f"Đã xảy ra lỗi khi xử lý request: {e}")
        return jsonify({"error": "Đã có lỗi xảy ra trên server.", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
