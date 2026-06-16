const API_URL = "http://127.0.0.1:8000/analyze";

let messages = [];

function addMessage(text, sender) {

    const chatBox = document.getElementById("chat-box");

    const div = document.createElement("div");
    div.classList.add("message", sender);

    div.innerText = text;

    chatBox.appendChild(div);

    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {

    const input = document.getElementById("message-input");

    const text = input.value.trim();

    if (!text) return;

    addMessage(text, "user");

    messages.push({
        role: "USER",
        content: text
    });

    input.value = "";

    try {

        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                messages: messages,
                question: text
            })
        });

        const data = await response.json();

        addMessage(data.response, "bot");

        messages.push({
            role: "AI",
            content: data.response
        });

    } catch (error) {

        addMessage(
            "Unable to connect to server.",
            "bot"
        );
    }
}