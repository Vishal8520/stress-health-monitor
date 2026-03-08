// Protect Route
async function verifySession() {
    const token = localStorage.getItem('authToken');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const response = await fetch('/api/auth/verify', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'ngrok-skip-browser-warning': '69420'
            }
        });
        const data = await response.json();
        if (!data.success) {
            logoutUser();
        }
    } catch (error) {
        console.log("Auth verification error:", error);
    }
}
verifySession();

function logoutUser() {
    localStorage.removeItem('userEmail');
    localStorage.removeItem('authToken');
    window.location.href = 'login.html';
}

// Store the context of the conversation
let chatHistory = [];

function appendMessage(text, sender) {
    const chatBox = document.getElementById('chatBox');
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('chat-message');
    msgDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');

    if (sender === 'bot') {
        msgDiv.innerHTML = `<strong>🤖 AI:</strong> ${text}`;
    } else {
        msgDiv.textContent = text;
    }

    chatBox.appendChild(msgDiv);

    // Auto scroll to bottom
    chatBox.scrollTop = chatBox.scrollHeight;
}

document.getElementById('chatForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const inputField = document.getElementById('userInput');
    const messageText = inputField.value.trim();
    if (!messageText) return;

    // Add to history and show
    chatHistory.push({ role: "user", content: messageText });
    appendMessage(messageText, 'user');
    inputField.value = '';

    // Show typing indicator
    const typingId = "typing-" + Date.now();
    const chatBox = document.getElementById('chatBox');
    const typingDiv = document.createElement('div');
    typingDiv.id = typingId;
    typingDiv.classList.add('chat-message', 'bot-message');
    typingDiv.innerHTML = "<strong>🤖 AI:</strong> <i>thinking...</i>";
    chatBox.appendChild(typingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'ngrok-skip-browser-warning': '69420'
            },
            body: JSON.stringify({ messages: chatHistory })
        });

        const data = await response.json();

        // Remove typing indicator
        document.getElementById(typingId).remove();

        if (data.success) {
            chatHistory.push({ role: "assistant", content: data.response });
            appendMessage(data.response, 'bot');
        } else {
            // Remove the failed user message from history if the backend crashed
            chatHistory.pop();
            appendMessage("❌ Error: " + data.error, 'bot');
        }
    } catch (error) {
        document.getElementById(typingId).remove();
        appendMessage("❌ Critical Error: Could not connect to Python backend AI engine.", 'bot');
    }
});
