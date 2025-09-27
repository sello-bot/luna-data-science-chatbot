// Updated chat.js - Modified for local development with API key
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