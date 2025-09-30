console.log("✅ chat.js loaded");

// === API KEY CONFIGURATION ===
const API_KEY = 'ds_EDpM1a_MBsPNfypdqqsdhHIfHnBPRIc5PJeadaIDDY8'; // Local development

// === GLOBAL STATE ===
let chatHistory = [];
let currentDataset = null;
let isProcessing = false;
let sessionId = generateSessionId();

// === INITIALIZATION ===
function initializeChat() {
    console.log('🤖 Initializing Data Science Chatbot...');
    loadAvailableDatasets();
    updateDatasetInfo();
}

function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// === CHAT FUNCTIONS ===
async function sendMessage() {
    console.log("🚀 sendMessage() called");
    
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    console.log("Message to send:", message);
    
    if (!message) {
        console.warn("⚠️ Empty message, aborting");
        return;
    }
    
    if (isProcessing) {
        console.warn("⚠️ Already processing, aborting");
        return;
    }
    
    input.value = '';
    addMessage(message, 'user');
    setProcessingState(true);
    addTypingIndicator();
    
    try {
        console.log("📡 Sending fetch request to /api/chat");
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({ 
                message: message,
                session_id: sessionId
            })
        });
        
        console.log("📨 Response status:", response.status);
        console.log("📨 Response ok:", response.ok);
        
        const data = await response.json();
        console.log("📦 Response data:", data);
        
        removeTypingIndicator();
        
        if (!response.ok) {
            console.error("❌ Server error:", data);
            addMessage(`Error (${response.status}): ${data.error || 'Unknown error'}`, 'bot', 'error');
        } else if (data.error) {
            console.error("❌ Application error:", data.error);
            addMessage(`Error: ${data.error}`, 'bot', 'error');
        } else {
            console.log("✅ Success! Adding bot response");
            addBotResponse(data);
        }
        
    } catch (error) {
        console.error("❌ Fetch error:", error);
        removeTypingIndicator();
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
    console.log(`💬 Adding ${sender} message:`, content);
    
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
        messageContent.innerHTML = `<p>${escapeHtml(content)}</p>`;
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
    console.log("🤖 Adding bot response:", data);
    
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Add main response text
    if (data.response) {
        const textContent = document.createElement('p');
        textContent.textContent = data.response;
        messageContent.appendChild(textContent);
    }
    
    // Add data if present
    if (data.data) {
        if (Array.isArray(data.data)) {
            messageContent.appendChild(createDataTable(data.data));
        } else if (typeof data.data === 'object') {
            messageContent.appendChild(createDataDisplay(data.data));
        }
    }
    
    // Add visualization if present
    if (data.visualization) {
        messageContent.appendChild(createVisualization(data.visualization));
    }
    
    // Add code if present
    if (data.code) {
        messageContent.appendChild(createCodeBlock(data.code));
    }
    
    // Add action buttons
    const actions = createMessageActions(data);
    if (actions.children.length > 0) {
        messageContent.appendChild(actions);
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Update dataset info if present
    if (data.data && data.data.shape) {
        updateDatasetInfo(data.data);
    }
}

// === TYPING INDICATOR ===
function addTypingIndicator() {
    const chatContainer = document.getElementById('chatContainer');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message typing-indicator';
    typingDiv.id = 'typingIndicator';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';
    
    const dots = document.createElement('div');
    dots.className = 'typing-dots';
    dots.innerHTML = '<span></span><span></span><span></span>';
    
    typingDiv.appendChild(avatar);
    typingDiv.appendChild(dots);
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// === DATA DISPLAY HELPERS ===
function createDataTable(data) {
    const container = document.createElement('div');
    container.className = 'data-table-container';
    
    if (data.length === 0) {
        container.innerHTML = '<p class="no-data">No data to display</p>';
        return container;
    }
    
    const table = document.createElement('table');
    table.className = 'data-table';
    
    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    const keys = Object.keys(data[0]);
    
    keys.forEach(key => {
        const th = document.createElement('th');
        th.textContent = key;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Create body
    const tbody = document.createElement('tbody');
    const maxRows = Math.min(data.length, 10);
    
    for (let i = 0; i < maxRows; i++) {
        const row = document.createElement('tr');
        keys.forEach(key => {
            const td = document.createElement('td');
            td.textContent = data[i][key];
            row.appendChild(td);
        });
        tbody.appendChild(row);
    }
    table.appendChild(tbody);
    
    container.appendChild(table);
    
    if (data.length > 10) {
        const moreText = document.createElement('p');
        moreText.className = 'data-more';
        moreText.textContent = `Showing 10 of ${data.length} rows`;
        container.appendChild(moreText);
    }
    
    return container;
}

function createDataDisplay(data) {
    const container = document.createElement('div');
    container.className = 'data-display';
    
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify(data, null, 2);
    container.appendChild(pre);
    
    return container;
}

function createVisualization(viz) {
    const container = document.createElement('div');
    container.className = 'visualization-container';
    
    if (typeof viz === 'string' && viz.startsWith('<')) {
        container.innerHTML = viz;
    } else if (viz.url) {
        const img = document.createElement('img');
        img.src = viz.url;
        img.alt = 'Visualization';
        img.className = 'visualization-image';
        container.appendChild(img);
    } else {
        container.innerHTML = '<p>Visualization data received but could not be displayed</p>';
    }
    
    return container;
}

function createCodeBlock(code) {
    const container = document.createElement('div');
    container.className = 'code-block-container';
    
    const pre = document.createElement('pre');
    const codeEl = document.createElement('code');
    codeEl.textContent = code;
    pre.appendChild(codeEl);
    
    const copyBtn = document.createElement('button');
    copyBtn.className = 'btn-copy-code';
    copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
    copyBtn.onclick = () => copyToClipboard(code);
    
    container.appendChild(copyBtn);
    container.appendChild(pre);
    
    return container;
}

function createMessageActions(data) {
    const actions = document.createElement('div');
    actions.className = 'message-actions';
    
    if (data.code) {
        const viewCodeBtn = document.createElement('button');
        viewCodeBtn.className = 'btn-action-small';
        viewCodeBtn.innerHTML = '<i class="fas fa-code"></i> View Code';
        viewCodeBtn.onclick = () => showCodeModal(data.code);
        actions.appendChild(viewCodeBtn);
    }
    
    if (data.data) {
        const viewDataBtn = document.createElement('button');
        viewDataBtn.className = 'btn-action-small';
        viewDataBtn.innerHTML = '<i class="fas fa-table"></i> View Data';
        viewDataBtn.onclick = () => showDataModal(data.data);
        actions.appendChild(viewDataBtn);
    }
    
    return actions;
}

// === MODAL FUNCTIONS ===
function showCodeModal(code) {
    const modal = document.getElementById('codeModal');
    const content = document.getElementById('codeContent');
    content.textContent = code;
    modal.style.display = 'flex';
}

function showDataModal(data) {
    const modal = document.getElementById('dataModal');
    const content = document.getElementById('dataContent');
    content.innerHTML = '';
    
    if (Array.isArray(data)) {
        content.appendChild(createDataTable(data));
    } else {
        content.appendChild(createDataDisplay(data));
    }
    
    modal.style.display = 'flex';
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// === UTILITY FUNCTIONS ===
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy', 'error');
    });
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function setProcessingState(processing) {
    isProcessing = processing;
    const sendButton = document.getElementById('sendButton');
    const input = document.getElementById('messageInput');
    
    if (sendButton) {
        sendButton.disabled = processing;
        sendButton.innerHTML = processing ? 
            '<i class="fas fa-spinner fa-spin"></i>' : 
            '<i class="fas fa-paper-plane"></i>';
    }
    
    if (input) {
        input.disabled = processing;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// === FILE UPLOAD ===
async function handleFileUpload(file) {
    console.log("📁 Uploading file:", file.name);
    
    const formData = new FormData();
    formData.append('file', file);
    
    setProcessingState(true);
    addMessage(`Uploading ${file.name}...`, 'user');
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            addMessage(`Upload error: ${data.error}`, 'bot', 'error');
        } else {
            addMessage(data.message, 'bot');
            if (data.data_info) {
                currentDataset = data.data_info;
                updateDatasetInfo(data.data_info);
            }
        }
        
    } catch (error) {
        console.error("Upload error:", error);
        addMessage(`Upload failed: ${error.message}`, 'bot', 'error');
    } finally {
        setProcessingState(false);
    }
}

function setupFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                handleFileUpload(file);
            }
        });
    }
    
    if (uploadArea) {
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const file = e.dataTransfer.files[0];
            if (file) {
                handleFileUpload(file);
            }
        });
    }
}

// === DATASET INFO ===
async function loadAvailableDatasets() {
    try {
        const response = await fetch('/api/datasets', {
            headers: {
                'X-API-Key': API_KEY
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log("Available datasets:", data);
        }
    } catch (error) {
        console.log("Could not load datasets:", error);
    }
}

function updateDatasetInfo(dataInfo) {
    const infoContainer = document.getElementById('datasetInfo');
    
    if (!dataInfo || !infoContainer) {
        return;
    }
    
    if (!dataInfo.shape) {
        infoContainer.innerHTML = '<p class="no-data">No dataset loaded</p>';
        return;
    }
    
    infoContainer.innerHTML = `
        <div class="info-item">
            <strong>Shape:</strong> ${dataInfo.shape[0]} rows × ${dataInfo.shape[1]} cols
        </div>
        <div class="info-item">
            <strong>Columns:</strong> ${dataInfo.columns ? dataInfo.columns.length : 0}
        </div>
        ${dataInfo.memory_usage ? `
        <div class="info-item">
            <strong>Memory:</strong> ${formatBytes(dataInfo.memory_usage)}
        </div>
        ` : ''}
    `;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// === KEYBOARD SHORTCUTS ===
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K to focus input
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('messageInput')?.focus();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            closeModal('codeModal');
            closeModal('dataModal');
        }
    });
}

// === CLEAR CHAT ===
function clearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        const chatContainer = document.getElementById('chatContainer');
        chatContainer.innerHTML = '';
        chatHistory = [];
        
        // Add welcome message
        addMessage("Chat cleared! How can I help you?", 'bot');
    }
}

// === EVENT LISTENERS ===
document.addEventListener('DOMContentLoaded', function() {
    console.log("📱 DOM loaded, initializing chat");
    initializeChat();
    setupFileUpload();
    setupKeyboardShortcuts();
    
    // Welcome message after delay
    setTimeout(() => {
        if (chatHistory.length === 0) {
            addMessage("💡 Tip: Try uploading a dataset or type 'create sample data' to get started!", 'bot');
        }
    }, 2000);
});

// Enter key to send message
document.getElementById('messageInput')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Close modals when clicking outside
window.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
});

console.log("✅ Chat.js fully loaded and ready!");
