// Chat application JavaScript
let chatHistory = [];
let currentDataset = null;
let isProcessing = false;

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
        const response = await fetch('/api/datasets');
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
    // This would be implemented to show complete dataset
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

// Export chat history
function exportChatHistory() {
    const exportData = {
        timestamp: new Date().toISOString(),
        messages: chatHistory
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json'
    });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `chat_history_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification('Chat history exported!', 'success');
}

// Initialize tooltips and help text
function initializeTooltips() {
    // Add tooltips to various elements
    const elements = document.querySelectorAll('[data-tooltip]');
    elements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

// Show tooltip
function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = e.target.getAttribute('data-tooltip');
    
    tooltip.style.position = 'absolute';
    tooltip.style.background = '#333';
    tooltip.style.color = 'white';
    tooltip.style.padding = '6px 8px';
    tooltip.style.borderRadius = '4px';
    tooltip.style.fontSize = '0.75rem';
    tooltip.style.zIndex = '1002';
    tooltip.style.pointerEvents = 'none';
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.bottom + 5) + 'px';
    
    e.target._tooltip = tooltip;
}

// Hide tooltip
function hideTooltip(e) {
    if (e.target._tooltip) {
        document.body.removeChild(e.target._tooltip);
        delete e.target._tooltip;
    }
}

// Auto-save chat to localStorage
function autoSaveChat() {
    try {
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    } catch (e) {
        console.warn('Could not save chat history:', e);
    }
}

// Load saved chat from localStorage
function loadSavedChat() {
    try {
        const saved = localStorage.getItem('chatHistory');
        if (saved) {
            chatHistory = JSON.parse(saved);
            // Optionally restore chat UI here
        }
    } catch (e) {
        console.warn('Could not load saved chat:', e);
    }
}

// Auto-save every 30 seconds
setInterval(autoSaveChat, 30000);

// Voice input (if supported)
function initializeVoiceInput() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('messageInput').value = transcript;
            showNotification('Voice input captured!', 'success');
        };
        
        recognition.onerror = function(event) {
            showNotification('Voice recognition error: ' + event.error, 'error');
        };
        
        // Add voice button to input
        const inputWrapper = document.querySelector('.chat-input-wrapper');
        const voiceBtn = document.createElement('button');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        voiceBtn.style.padding = '12px';
        voiceBtn.style.border = 'none';
        voiceBtn.style.borderRadius = '50%';
        voiceBtn.style.background = '#64748b';
        voiceBtn.style.color = 'white';
        voiceBtn.style.cursor = 'pointer';
        voiceBtn.title = 'Voice input';
        
        voiceBtn.onclick = function() {
            recognition.start();
            voiceBtn.style.background = '#ef4444';
            setTimeout(() => {
                voiceBtn.style.background = '#64748b';
            }, 3000);
        };
        
        inputWrapper.insertBefore(voiceBtn, document.getElementById('sendButton'));
    }
}

// Theme toggle
function initializeThemeToggle() {
    const themeBtn = document.createElement('button');
    themeBtn.innerHTML = '<i class="fas fa-moon"></i>';
    themeBtn.style.position = 'fixed';
    themeBtn.style.top = '20px';
    themeBtn.style.right = '20px';
    themeBtn.style.padding = '10px';
    themeBtn.style.border = 'none';
    themeBtn.style.borderRadius = '50%';
    themeBtn.style.background = 'var(--primary-color)';
    themeBtn.style.color = 'white';
    themeBtn.style.cursor = 'pointer';
    themeBtn.style.zIndex = '1000';
    themeBtn.title = 'Toggle theme';
    
    themeBtn.onclick = toggleTheme;
    document.body.appendChild(themeBtn);
}

// Toggle between light and dark themes
function toggleTheme() {
    const root = document.documentElement;
    const isDark = root.classList.contains('dark-theme');
    
    if (isDark) {
        root.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
    } else {
        root.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
    }
}

// Load saved theme
function loadSavedTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark-theme');
    }
}

// Performance monitoring
function monitorPerformance() {
    // Monitor chat container scroll performance
    const chatContainer = document.getElementById('chatContainer');
    let scrollTimeout;
    
    chatContainer.addEventListener('scroll', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            // Auto-hide older messages if chat gets too long
            if (chatContainer.children.length > 100) {
                const oldMessages = Array.from(chatContainer.children).slice(0, 20);
                oldMessages.forEach(msg => msg.style.display = 'none');
            }
        }, 1000);
    });
}

// Initialize all features when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadSavedChat();
    loadSavedTheme();
    initializeTooltips();
    initializeVoiceInput();
    initializeThemeToggle();
    monitorPerformance();
    
    // Show welcome message with tips
    setTimeout(() => {
        if (chatHistory.length === 0) {
            addMessage("💡 Tip: Try uploading a CSV file or type 'create sample data' to get started!", 'bot');
        }
    }, 2000);
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    autoSaveChat();
});