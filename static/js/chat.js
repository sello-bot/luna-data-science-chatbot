// chats.js - Data Science Chatbot Frontend

// === API KEY CONFIGURATION ===
// Use the correct API key for your environment.
// For production (Heroku), use the first one.
// For local development, comment that and uncomment the second.

const API_KEY = 'ds_GJKkhm1ETsH_iH-VmxV8ZRc6QOIL-ZoR2megS-zAZyM'; // Production
// const API_KEY = 'ds_EDpM1a_MBsPNfypdqqsdhHIfHnBPRIc5PJeadaIDDY8'; // Local development

// === GLOBAL STATE ===
let chatHistory = [];
let currentDataset = null;
let isProcessing = false;

// === INITIALIZATION ===
function initializeChat() {
    console.log('Initializing Data Science Chatbot...');
    loadAvailableDatasets();
    updateDatasetInfo();
}

// === CHAT FUNCTIONS ===
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || isProcessing) return;
    
    input.value = '';
    addMessage(message, 'user');
    setProcessingState(true);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        if (data.error) {
            addMessage(`Error: ${data.error}`, 'bot', 'error');
        } else {
            addBotResponse(data);
        }
        
    } catch (error) {
        addMessage(`Connection error: ${error.message}`, 'bot', 'error');
    } finally {
        setProcessingState(false);
    }
}

function sendQuickMessage(message) {
    document.getElementById('messageInput').value = message;
    sendMessage();
}

// === MESSAGE HANDLING ===
function addMessage(content, sender, type = 'normal') {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    if (type === 'error') {
        messageContent.innerHTML = `<p class="status-error"><i class="fas fa-exclamation-triangle"></i> ${content}</p>`;
    } else {
        messageContent.innerHTML = `<p>${content}</p>`;
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    chatHistory.push({
        content,
        sender,
        timestamp: new Date(),
        type
    });
}

function addBotResponse(data) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const textContent = document.createElement('p');
    textContent.textContent = data.response;
    messageContent.appendChild(textContent);
    
    if (data.data && Array.isArray(data.data)) {
        messageContent.appendChild(createDataTable(data.data));
    } else if (data.data && typeof data.data === 'object') {
        messageContent.appendChild(createDataDisplay(data.data));
    }
    
    if (data.visualization) {
        messageContent.appendChild(createVisualization(data.visualization));
    }
    
    if (data.code) {
        messageContent.appendChild(createCodeBlock(data.code));
    }
    
    const actions = createMessageActions(data);
    if (actions.children.length > 0) {
        messageContent.appendChild(actions);
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    if (data.data && data.data.shape) {
        updateDatasetInfo(data.data);
    }
}

// === DATA HELPERS (unchanged from your version) ===
// createDataTable, createDataDisplay, createVisualization, createCodeBlock,
// createMessageActions, showCodeModal, showDataModal, closeModal,
// copyCode, copyToClipboard, showNotification, setProcessingState,
// addTypingIndicator, removeTypingIndicator, handleFileUpload,
// loadAvailableDatasets, updateDatasetInfo, addToRecentPlots,
// downloadVisualization, formatBytes, showFullData, clearChat, 
// setupFileUpload, setupKeyboardShortcuts
// (keep your existing implementations here without changing API_KEY duplication)

// === EVENT LISTENERS ===
document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
    setupFileUpload();
    setupKeyboardShortcuts();
    
    setTimeout(() => {
        if (chatHistory.length === 0) {
            addMessage("💡 Tip: Try clicking 'Sample Data' button or type 'create sample data' to get started!", 'bot');
        }
    }, 2000);
});

document.getElementById('messageInput')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
