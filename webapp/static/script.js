document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const logContent = document.getElementById('log-content');

    // --- SSE for Log Streaming ---
    const logSource = new EventSource('/stream-logs');

    logSource.onmessage = function(event) {
        try {
            const logEntry = JSON.parse(event.data);
            displayLogEntry(logEntry);
        } catch (e) {
            console.error('Error parsing log entry:', e, event.data);
            logContent.prepend(createLogElement({
                levelname: 'ERROR',
                message: 'Failed to parse log entry: ' + event.data
            }));
        }
    };

    logSource.onerror = function(err) {
        console.error('EventSource failed:', err);
        // Optionally display an error message in the log panel
        logContent.prepend(createLogElement({
            levelname: 'ERROR',
            message: 'Log stream disconnected.'
        }));
    };

    const waitingAnimation = document.querySelector('.waiting-animation');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (!message) return;

        appendMessage(message, 'user-message', true); // User message is plain text
        messageInput.value = '';

        // Show the waiting animation
        waitingAnimation.style.display = 'flex';
        waitingAnimation.style.pointerEvents = 'auto';
        waitingAnimation.style.opacity = 1;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            if (data.error) {
                appendMessage(`Error: ${data.error}`, 'agent-message', true);
            } else {
                appendMessage(data.agent_response, 'agent-message', false); // Agent response is HTML
            }

        } catch (error) {
            console.error('Error:', error);
            appendMessage('An error occurred while communicating with the agent.', 'agent-message', true);
        } finally {
            // Hide the waiting animation
            waitingAnimation.style.opacity = 0;
            waitingAnimation.style.pointerEvents = 'none';
            setTimeout(() => {
                waitingAnimation.style.display = 'none';
            }, 300);
        }
    });

    function appendMessage(message, className, isText) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', className);
        if (isText) {
            messageElement.textContent = message;
        } else {
            messageElement.innerHTML = message;
        }
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function createLogElement(logEntry) {
        const logDiv = document.createElement('div');
        logDiv.classList.add('log-entry', `log-${logEntry.levelname.toLowerCase()}`);

        const timestampSpan = document.createElement('span');
        timestampSpan.classList.add('log-timestamp');
        timestampSpan.textContent = logEntry.timestamp;

        const levelSpan = document.createElement('span');
        levelSpan.classList.add('log-level');
        levelSpan.textContent = `[${logEntry.levelname}]`;

        const nameSpan = document.createElement('span');
        nameSpan.classList.add('log-name');
        nameSpan.textContent = `(${logEntry.name})`;

        const messageSpan = document.createElement('span');
        messageSpan.classList.add('log-message');
        messageSpan.textContent = logEntry.message;

        logDiv.appendChild(timestampSpan);
        logDiv.appendChild(levelSpan);
        logDiv.appendChild(nameSpan);
        logDiv.appendChild(document.createTextNode(' ')); // Space between name and message
        logDiv.appendChild(messageSpan);

        return logDiv;
    }

    function displayLogEntry(logEntry) {
        const newLogElement = createLogElement(logEntry);
        // Prepend the new log entry to make it appear at the top
        if (logContent.firstChild) {
            logContent.insertBefore(newLogElement, logContent.firstChild);
        } else {
            logContent.appendChild(newLogElement);
        }
        // Keep scrollbar at the top if new logs are prepended
        logContent.scrollTop = 0;
    }
});