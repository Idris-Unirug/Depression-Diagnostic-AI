// Typewriter effect for bot messages
function typeText(element, text, speed = 25, emoji = "😊") {
    // Replace descriptive phrases with emojis
    const replacements = {
        '*offers a compassionate smile*': '😊',
        '*I smile warmly*': '🙂',
        '*offers a gentle nod*': '🤝',
        '*nods*': '👍',
        '*hugs you*': '🤗'
    };

    for (const phrase in replacements) {
        const regex = new RegExp(phrase, 'gi');
        text = text.replace(regex, replacements[phrase]);
    }

    let index = 0;
    element.innerHTML = "";
    const interval = setInterval(() => {
        if (index < text.length) {
            element.innerHTML += text.charAt(index);
            index++;
        } else {
            element.innerHTML += ` ${emoji}`;
            clearInterval(interval);
        }

        // Auto-scroll
        const conversationDiv = document.getElementById("conversation");
        conversationDiv.scrollTop = conversationDiv.scrollHeight;
    }, speed);
}

// Chat form submission and dynamic bot response rendering
document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById("chat-form");
    const userInputField = document.getElementById("user-input");
    const conversationDiv = document.getElementById("conversation");

    chatForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const userInput = userInputField.value.trim();
        if (userInput === "") return;

        // Append user message
        const userMessage = document.createElement("div");
        userMessage.className = "chat-message user-message";
        userMessage.innerText = userInput;
        conversationDiv.appendChild(userMessage);

        // Clear input
        userInputField.value = "";

        // Append placeholder bot message
        const botMessage = document.createElement("div");
        botMessage.className = "chat-message bot-message";
        botMessage.innerText = "Typing...";
        conversationDiv.appendChild(botMessage);

        // Scroll to bottom
        conversationDiv.scrollTop = conversationDiv.scrollHeight;

        try {
            const response = await fetch("/reply", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: `userInput=${encodeURIComponent(userInput)}`
            });

            const botText = await response.text();

            // Clear "Typing..."
            botMessage.innerText = "";

            // Type bot response
            typeText(botMessage, botText, 25); // You can adjust speed here
        } catch (error) {
            console.error("Error:", error);
            botMessage.innerText = "Oops! Something went wrong. ❌";
        }

        // Final scroll
        conversationDiv.scrollTop = conversationDiv.scrollHeight;
    });
});
