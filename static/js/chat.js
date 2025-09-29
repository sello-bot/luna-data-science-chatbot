// Add at the top of your production chat.js
const API_KEY = 'ds_GJKkhm1ETsH_iH-VmxV8ZRc6QOIL-ZoR2megS-zAZyM';

// Chat application JavaScript with API Key
let chatHistory = [];
let currentDataset = null;
let isProcessing = false;

// Your API key for local development
const API_KEY = 'ds_EDpM1a_MBsPNfypdqqsdhHIfHnBPRIc5PJeadaIDDY8';

// Initialize chat functionality
function initializeChat() {
    console.log('Initializing Data Science Chatbot...');
    loadAvailableDatasets();
    updateDatasetInfo();
}

// Send message to chatbot
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || isProcessing) return;
    
    // Clear input and add user message
    input.value = '';
    addMessage(message, 'user');
    
    // Show processing state
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

// Send quick message
function sendQuickMessage(message) {
    document.getElementById('messageInput').value = message;
    sendMessage();
}

// Add message to chat
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
    
    // Add to history
    chatHistory.push({
        content: content,
        sender: sender,
        timestamp: new Date(),
        type: type
    });
}

// Add bot response with rich content
function addBotResponse(data) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Add main response text
    const textContent = document.createElement('p');
    textContent.textContent = data.response;
    messageContent.appendChild(textContent);
    
    // Add data table if available
    if (data.data && Array.isArray(data.data)) {
        const dataTable = createDataTable(data.data);
        messageContent.appendChild(dataTable);
    } else if (data.data && typeof data.data === 'object') {
        const dataDisplay = createDataDisplay(data.data);
        messageContent.appendChild(dataDisplay);
    }
    
    // Add visualization if available
    if (data.visualization) {
        const vizContainer = createVisualization(data.visualization);
        messageContent.appendChild(vizContainer);
    }
    
    // Add code block if available
    if (data.code) {
        const codeBlock = createCodeBlock(data.code);
        messageContent.appendChild(codeBlock);
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
    
    // Update dataset info if data was loaded
    if (data.data && data.data.shape) {
        updateDatasetInfo(data.data);
    }
}

// Create data table
function createDataTable(data) {
    const container = document.createElement('div');
    container.className = 'data-table';
    
    if (data.length === 0) {
        container.innerHTML = '<p>No data to display</p>';
        return container;
    }
    
    const table = document.createElement('table');
    
    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    Object.keys(data[0]).forEach(key => {
        const th = document.createElement('th');
        th.textContent = key;
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Create body
    const tbody = document.createElement('tbody');
    data.slice(0, 10).forEach(row => { // Limit to 10 rows
        const tr = document.createElement('tr');
        Object.values(row).forEach(value => {
            const td = document.createElement('td');
            td.textContent = value;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    
    table.appendChild(tbody);
    container.appendChild(table);
    
    if (data.length > 10) {
        const moreInfo = document.createElement('p');
        moreInfo.innerHTML = `<small>Showing 10 of ${data.length} rows. <a href="#" onclick="showFullData()">View all data</a></small>`;
        container.appendChild(moreInfo);
    }
    
    return container;
}

// Create data display for objects
function createDataDisplay(data) {
    const container = document.createElement('div');
    container.className = 'data-display';
    
    const pre = document.createElement('pre');
    pre.style.background = '#f8fafc';
    pre.style.padding = '12px';
    pre.style.borderRadius = '8px';
    pre.style.fontSize = '0.875rem';
    pre.style.overflow = 'auto';
    pre.textContent = JSON.stringify(data, null, 2);
    
    container.appendChild(pre);
    return container;
}

// Create visualization container
function createVisualization(vizPath) {
    const container = document.createElement('div');
    container.className = 'visualization';
    
    if (vizPath.endsWith('.html')) {
        const iframe = document.createElement('iframe');
        iframe.src = `/static/plots/${vizPath}`;
        container.appendChild(iframe);
    } else {
        const img = document.createElement('img');
        img.src = `/static/plots/${vizPath}`;
        img.alt = 'Generated visualization';
        img.onload = function() {
            addToRecentPlots(vizPath);
        };
        container.appendChild(img);
    }
    
    return container;
}

// Create code block
function createCodeBlock(code) {
    const container = document.createElement('div');
    container.className = 'code-block';
    
    const pre = document.createElement('pre');
    pre.textContent = code;
    
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
    copyBtn.onclick = () => copyToClipboard(code);
    
    container.appendChild(pre);
    container.appendChild(copyBtn);
    
    return container;
}

// Create message actions
function createMessageActions(data) {
    const actions = document.createElement('div');
    actions.className = 'message-actions';
    
    if (data.code) {
        const showCodeBtn = document.createElement('button');
        showCodeBtn.className = 'action-btn';
        showCodeBtn.innerHTML = '<i class="fas fa-code"></i> Show Code';
        showCodeBtn.onclick = () => showCodeModal(data.code);
        actions.appendChild(showCodeBtn);
    }
    
    if (data.data) {
        const showDataBtn = document.createElement('button');
        showDataBtn.className = 'action-btn';
        showDataBtn.innerHTML = '<i class="fas fa-table"></i> View Data';
        showDataBtn.onclick = () => showDataModal(data.data);
        actions.appendChild(showDataBtn);
    }
    
    if (data.visualization) {
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'action-btn';
        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download Plot';
        downloadBtn.onclick = () => downloadVisualization(data.visualization);
        actions.appendChild(downloadBtn);
    }
    
    return actions;
}

// Show code modal
function showCodeModal(code) {
    const modal = document.getElementById('codeModal');
    const content = document.getElementById('codeContent');
    content.textContent = code;
    modal.style.display = 'flex';
}

// Show data modal
function showDataModal(data) {
    const modal = document.getElementById('dataModal');
    const content = document.getElementById('dataContent');
    
    if (Array.isArray(data)) {
        content.appendChild(createDataTable(data));
    } else {
        content.appendChild(createDataDisplay(data));
    }
    
    modal.style.display = 'flex';
}

// Close modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.style.display = 'none';
    
    // Clear modal content
    if (modalId === 'dataModal') {
        document.getElementById('dataContent').innerHTML = '';
    }
}

// Copy code to clipboard
function copyCode() {
    const code = document.getElementById('codeContent').textContent;
    copyToClipboard(code);
}

// Copy to clipboard utility
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success');
    }).catch(() => {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showNotification('Copied to clipboard!', 'success');
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.padding = '12px 16px';
    notification.style.borderRadius = '8px';
    notification.style.color = 'white';
    notification.style.zIndex = '1001';
    notification.style.animation = 'slideIn 0.3s ease';
    
    switch (type) {
        case 'success':
            notification.style.background = '#10b981';
            break;
        case 'error':
            notification.style.background = '#ef4444';
            break;
        default:
            notification.style.background = '#2563eb';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Set processing state
function setProcessingState(processing) {
    isProcessing = processing;
    const sendButton = document.getElementById('sendButton');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    sendButton.disabled = processing;
    loadingOverlay.style.display = processing ? 'flex' : 'none';
    
    if (processing) {
        addTypingIndicator();
    } else {
        removeTypingIndicator();
    }
}

// Add typing indicator
function addTypingIndicator() {
    const chatContainer = document.getElementById('chatContainer');
    const indicator = document.createElement('div');
    indicator.id = 'typingIndicator';
    indicator.className = 'message bot-message typing-indicator';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = '<p>Thinking...</p>';
    
    indicator.appendChild(avatar);
    indicator.appendChild(content);
    
    chatContainer.appendChild(indicator);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

// File upload handler
async function handleFileUpload(event) {
    const files = event.target.files;
    if (files.length === 0) return;
    
    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    setProcessingState(true);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.error) {
            addMessage(`Upload error: ${data.error}`, 'bot', 'error');
        } else {
            addMessage(`${data.message}`, 'bot');
            if (data.data_info) {
                updateDatasetInfo(data.data_info);
            }
            loadAvailableDatasets();
        }
        
    } catch (error) {
        addMessage(`Upload failed: ${error.message}`, 'bot', 'error');
    } finally {
        setProcessingState(false);
        event.target.value = ''; // Clear file input
    }
}

// Load available datasets
async function loadAvailableDatasets() {
    try {
        const response = await fetch('/api/datasets', {
            headers: {
                'X-API-Key': API_KEY
            }
        });
        const data = await response.json();
        
        // Update sidebar with available datasets
        // Implementation would go here
        
    } catch (error) {
        console.error('Failed to load datasets:', error);
    }
}

// Update dataset info in sidebar
function updateDatasetInfo(info = null) {
    const container = document.getElementById('datasetInfo');
    
    if (!info) {
        container.innerHTML = '<p class="no-data">No dataset loaded</p>';
        return;
    }
    
    const infoHtml = `
        <div class="info-item">
            <span class="info-label">Shape:</span>
            <span class="info-value">${info.shape}</span>
        </div>
        <div class="info-item">
            <span class="info-label">Columns:</span>
            <span class="info-value">${info.columns.length}</span>
        </div>
        <div class="info-item">
            <span class="info-label">Memory:</span>
            <span class="info-value">${formatBytes(info.memory_usage || 0)}</span>
        </div>
    `;
    
    container.innerHTML = infoHtml;
}

// Add to recent plots
function addToRecentPlots(plotPath) {
    const container = document.getElementById('recentPlots');
    
    const plotDiv = document.createElement('div');
    plotDiv.className = 'plot-thumbnail';
    plotDiv.onclick = () => window.open(`/static/plots/${plotPath}`, '_blank');
    
    const img = document.createElement('img');
    img.src = `/static/plots/${plotPath}`;
    img.alt = 'Recent plot';
    
    const label = document.createElement('p');
    label.textContent = plotPath.replace(/^.*_/, '').replace(/\.[^.]*$/, '');
    
    plotDiv.appendChild(img);
    plotDiv.appendChild(label);
    
    container.insertBefore(plotDiv, container.firstChild);
    
    // Keep only last 5 plots
    while (container.children.length > 5) {
        container.removeChild(container.lastChild);
    }
}

// Download visualization
function downloadVisualization(vizPath) {
    const link = document.createElement('a');
    link.href = `/static/plots/${vizPath}`;
    link.download = vizPath;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showNotification('Download started!', 'success');
}

// Format bytes utility
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Show full data in modal
function showFullData() {
    showNotification('Full data view - feature coming soon!', 'info');
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('messageInput').focus();
    }
    
    // Ctrl/Cmd + L to clear chat
    if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
        e.preventDefault();
        clearChat();
    }
});

// Clear chat function
function clearChat() {
    if (confirm('Clear chat history?')) {
        document.getElementById('chatContainer').innerHTML = `
            <div class="message bot-message">
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <p>Chat cleared! How can I help you with data science today?</p>
                </div>
            </div>
        `;
        chatHistory = [];
    }
}

// Initialize all features when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
    setupFileUpload();
    setupKeyboardShortcuts();
    
    // Show welcome message with tips
    setTimeout(() => {
        if (chatHistory.length === 0) {
            addMessage("💡 Tip: Try clicking 'Sample Data' button or type 'create sample data' to get started!", 'bot');
        }
    }, 2000);
});

// Handle Enter key in input
document.getElementById('messageInput')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// File upload functionality
function setupFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    
    if (fileInput) fileInput.addEventListener('change', handleFileUpload);
    
    // Drag and drop functionality
    if (uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload({target: {files: files}});
            }
        });
    }
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to send message
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            sendMessage();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => modal.style.display = 'none');
        }
    });
}