document.addEventListener("DOMContentLoaded", () => {
    const chatMessages = document.getElementById("chat-messages");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");

    const API_URL = "http://127.0.0.1:5000/api/chat";

    function addMessage(text, sender) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender === "user" ? "user-message" : "bot-message");

        messageElement.innerText = text;

        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageElement;
    }

    async function sendMessage() {
        const question = userInput.value.trim();
        if (!question) return;

        addMessage(question, "user");
        userInput.value = "";

        const loadingIndicator = addMessage("Đang suy nghĩ...", "loading-indicator");

        try {
            const messageId = Date.now();

            const response = await fetch(API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    account_id: 1,
                    conversations_id: 1,
                    model_chat: "qwen3-4b-finetuned",
                    message_id: messageId,
                    content: question,
                }),
            });

            chatMessages.removeChild(loadingIndicator);

            if (!response.ok) {
                addMessage("Xin lỗi, đã có lỗi xảy ra từ server.", "bot");
                return;
            }

            const data = await response.json();

            const botMessageElement = addMessage(data.answer, "bot");

            if (data.citations && data.citations.length > 0) {
                const citationsContainer = document.createElement("div");
                citationsContainer.classList.add("citations");
                citationsContainer.innerHTML = "<strong>Nguồn tham khảo:</strong>";

                data.citations.forEach(cit => {
                    const citationElement = document.createElement("div");
                    citationElement.classList.add("citation-item");
                    citationElement.innerText = `- ${cit.law_name} (Chương ${cit.chapter}, Điều ${cit.article})`;
                    citationsContainer.appendChild(citationElement);
                });

                botMessageElement.appendChild(citationsContainer);
            }

        } catch (error) {
            chatMessages.removeChild(loadingIndicator);
            addMessage("Không thể kết nối đến server. Vui lòng kiểm tra lại.", "bot");
            console.error("Error:", error);
        }
    }

    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    });

    addMessage("Xin chào! Bạn cần tôi giúp gì về pháp luật hôm nay?", "bot");
});