from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import sys
import uuid
import logging
from werkzeug.utils import secure_filename
from datetime import datetime

# Import our custom modules
from src.chatbot import DataScienceChatbot
from src.data_processor import DataProcessor
from config import Config
from auth import AuthManager, require_auth, require_api_key
from security import SecurityManager, require_rate_limit, validate_json_input, secure_headers
from database import DatabaseManager

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# Initialize managers
auth_manager = AuthManager()
security_manager = SecurityManager()
db_manager = DatabaseManager()

# Per-user chatbot instances (in production, use Redis or similar)
user_chatbots = {}
user_data_processors = {}

# Your hardcoded API key for local testing (remove in production)
TEST_API_KEY = "ds_EDpM1a_MBsPNfypdqqsdhHIfHnBPRIc5PJeadaIDDY8"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_user_chatbot(user_id):
    """Get or create chatbot instance for user"""
    if user_id not in user_chatbots:
        user_chatbots[user_id] = DataScienceChatbot()
        user_data_processors[user_id] = DataProcessor()
    return user_chatbots[user_id], user_data_processors[user_id]

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
@secure_headers
def register():
    """User  registration"""
    if request.method == 'GET':
        return render_template('register.html')
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    plan = data.get('plan', 'free')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    result = auth_manager.register_user(email, password, plan)
    
    if 'error' in result:
        return jsonify(result), 400
    
    return jsonify({
        'success': True,
        'message': 'Registration successful',
        'api_key': result['api_key']
    })

@app.route('/login', methods=['GET', 'POST'])
@secure_headers
def login():
    """User  login"""
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    result = auth_manager.authenticate_user(email, password)
    
    if 'error' in result:
        return jsonify(result), 401
    
    # Set session
    session['user_id'] = result['user_id']
    session['plan'] = result['plan']
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'api_key': result['api_key'],
        'plan': result['plan']
    })

@app.route('/logout')
@secure_headers
def logout():
    """User  logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# Main application routes
@app.route('/')
@secure_headers
def index():
    """Main chat interface - requires login"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
@secure_headers
@require_rate_limit(security_manager, max_requests=30, window_minutes=1)
@validate_json_input(required_fields=['message'])
def chat():
    """Handle chat messages - with development bypass"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        # Development mode bypass - check if running locally
        if app.config.get('DEBUG', False):
            # Skip API key validation in development
            user_id = 1  # Default user ID for development
        else:
            # Production mode - require API key
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            validation = auth_manager.validate_api_key(api_key)
            if not validation['valid']:
                return jsonify({'error': validation['error']}), 401
            
            user_id = validation['user_id']
            auth_manager.increment_usage(user_id, request.endpoint)
        
        # Validate message
        validation = security_manager.validate_chat_input(user_message)
        if not validation['valid']:
            return jsonify({'error': validation['error']}), 400
        
        user_message = validation['sanitized_message']
        
        # Generate session ID
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # Get user's chatbot and data processor
        chatbot, data_processor = get_user_chatbot(user_id)
        
        # Process the message
        response = chatbot.process_message(user_message, data_processor)
        
        return jsonify({
            'response': response['message'],
            'data': response.get('data'),
            'visualization': response.get('visualization'),
            'code': response.get('code'),
            'session_id': session_id
        })
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'An error occurred processing your request'}), 500

@app.route('/api/upload', methods=['POST'])
@secure_headers
@require_rate_limit(security_manager, max_requests=10, window_minutes=1)
@require_api_key(auth_manager)
def upload_file():
    """Handle file uploads - API key required"""
    try:
        # NEW: Check for Bearer token first (for local testing with hardcoded key)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header == f'Bearer {TEST_API_KEY}':
            # Set test user context to bypass full auth for local dev
            request.user_info = {
                'user_id': 'test_user',
                'plan': 'free',
                'remaining_usage': 100000  # Unlimited for testing
            }
            logger.info("Test API key authenticated for upload (local testing)")
        # If no Bearer match, the @require_api_key decorator already handled real auth

        user_id = request.user_info['user_id']
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Validate file upload
        validation = security_manager.validate_file_upload(file)
        if not validation['valid']:
            return jsonify({'error': validation['errors'][0]}), 400
        
        # Save file with secure name
        secure_name = validation['secure_filename']
        file_path = os.path.join('data', secure_name)
        
        # Ensure directory exists
        os.makedirs('data', exist_ok=True)
        file.save(file_path)
        
        # Get user's data processor
        chatbot, data_processor = get_user_chatbot(user_id)
        
        # Load and process data
        dataset = data_processor.load_data(file_path)
        data_info = data_processor.get_data_info()
        
        # Update chatbot's current dataset
        chatbot.current_dataset = dataset
        
        # Save dataset metadata to database
        file_size = os.path.getsize(file_path)
        file_type = os.path.splitext(secure_name)[1][1:]  # Remove the dot
        
        dataset_result = db_manager.save_dataset(
            user_id, secure_name, validation['original_filename'],
            file_path, file_size, file_type, data_info
        )
        
        return jsonify({
            'message': f'File uploaded and processed successfully! Shape: {data_info["shape"]}, Columns: {len(data_info["columns"])}',
            'data_info': data_info,
            'dataset_id': dataset_result.get('dataset_id')
        })
        
    except Exception as e:
        logger.error(f"Upload error for user {request.user_info.get('user_id', 'unknown')}: {str(e)}")
        # Clean up file if processing failed
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': 'Failed to process uploaded file'}), 500

@app.route('/api/datasets', methods=['GET'])
@secure_headers
@require_api_key(auth_manager)
def get_datasets():
    """Get user's datasets - API key required"""
    try:
        user_id = request.user_info['user_id']
        datasets = db_manager.get_user_datasets(user_id)
        return jsonify({'datasets': datasets})
        
    except Exception as e:
        logger.error(f"Dataset listing error for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve datasets'}), 500

@app.route('/api/models', methods=['GET'])
@secure_headers
@require_api_key(auth_manager)
def get_models():
    """Get user's trained models - API key required"""
    try:
        user_id = request.user_info['user_id']
        models = db_manager.get_user_models(user_id)
        return jsonify({'models': models})
        
    except Exception as e:
        logger.error(f"Models listing error for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve models'}), 500

@app.route('/api/visualizations', methods=['GET'])
@secure_headers
@require_api_key(auth_manager)
def get_visualizations():
    """Get user's visualizations - API key required"""
    try:
        user_id = request.user_info['user_id']
        dataset_id = request.args.get('dataset_id', type=int)
        
        visualizations = db_manager.get_user_visualizations(user_id, dataset_id)
        return jsonify({'visualizations': visualizations})
        
    except Exception as e:
        logger.error(f"Visualizations listing error for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve visualizations'}), 500

@app.route('/api/chat/history/<session_id>')
@secure_headers
@require_api_key(auth_manager)
def get_chat_history(session_id):
    """Get chat history for a session - API key required"""
    try:
        user_id = request.user_info['user_id']
        limit = request.args.get('limit', 50, type=int)
        
        history = db_manager.get_conversation_history(user_id, session_id, limit)
        return jsonify({'history': history})
        
    except Exception as e:
        logger.error(f"Chat history error for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve chat history'}), 500

@app.route('/api/usage', methods=['GET'])
@secure_headers
@require_api_key(auth_manager)
def get_usage_stats():
    """Get user's usage statistics - API key required"""
    try:
        user_id = request.user_info['user_id']
        plan = request.user_info['plan']
        remaining = request.user_info['remaining_usage']
        
        return jsonify({
            'plan': plan,
            'remaining_usage': remaining,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Usage stats error for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve usage statistics'}), 500

# Health check and monitoring
@app.route('/health')
@secure_headers
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'Request too large. Check file size limits.'}), 413

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

# Background cleanup tasks (run periodically)
def cleanup_old_data():
    """Cleanup old data - run this periodically"""
    try:
        db_manager.cleanup_old_sessions(days_old=7)
        db_manager.cleanup_old_conversations(days_old=30)
        
        # Cleanup old plot files
        plots_dir = 'static/plots'
        if os.path.exists(plots_dir):
            cutoff_time = datetime.now().timestamp() - (7 * 24 * 60 * 60)  # 7 days
            for filename in os.listdir(plots_dir):
                filepath = os.path.join(plots_dir, filename)
                if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                    try:
                        os.remove(filepath)
                    except:
                        pass
        
        logger.info("Data cleanup completed")
        
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('static/plots', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Run cleanup on startup
    cleanup_old_data()
    
    # Run the application
    app.run(debug=app.config.get('DEBUG', False), 
           host='0.0.0.0', port=5000)