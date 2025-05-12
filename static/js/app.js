document.getElementById('send-btn').addEventListener('click', function() {
    const userInput = document.getElementById('user-input').value;

    // Append user message to conversation
    const conversation = document.getElementById('conversation');
    conversation.innerHTML += `<div class="user-message"><p>${userInput}</p></div>`;

    // Clear the input field
    document.getElementById('user-input').value = '';

    // Send message to Flask backend
    fetch('/get_response', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput })
    })
    .then(response => response.json())
    .then(data => {
        // Append bot response to conversation
        conversation.innerHTML += `<div class="bot-message"><p>${data.response}</p></div>`;
    })
    .catch(error => console.error('Error:', error));
});
