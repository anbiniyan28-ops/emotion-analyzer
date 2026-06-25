const API_URL = "http://127.0.0.1:8000/analyze";

let messages = [];

function addMessage(text, sender) {

    const chatBox = document.getElementById("chat-box");

    const div = document.createElement("div");
    div.className = `message ${sender}`;
    div.innerText = text;

    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {

    const input = document.getElementById("message-input");
    const text = input.value.trim();

    if (!text) return;

    // User message
    addMessage(text, "user");

    messages.push({
        role: "user",
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
                question: text
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Request failed"
            );
        }

        // SHOW ONLY BOT RESPONSE
        addMessage(data.response, "bot");

        messages.push({
            role: "assistant",
            content: data.response
        });

    } catch (error) {

        console.error(error);

        addMessage(
            "Unable to connect to server.",
            "bot"
        );
    }
}

// Enter key support
document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("message-input");

    input.addEventListener("keydown", function(event) {

        if (event.key === "Enter") {
            sendMessage();
        }

    });

});