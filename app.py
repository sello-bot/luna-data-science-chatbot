"""
AI-Powered Data Science Chatbot - Production Ready
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import sys
import uuid
import logging
import time
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps

# Import our custom modules
from src.chatbot import DataScienceChatbot
from src.data_processor import DataProcessor
from config import Config
from auth import AuthManager, require_auth, require_api_key
from security import SecurityManager, require_rate_limit, validate_json_input, secure_headers
from database import DatabaseManager
# Fix Render's postgres:// to postgresql://
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    os.environ['DATABASE_URL'] = DATABASE_URL
# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}})

# Initialize managers
auth_manager = AuthManager()
security_manager = SecurityManager()
db_manager = DatabaseManager()

# Per-user chatbot instances
user_chatbots = {}
user_data_processors = {}

# Debug mode flag
DEBUG_MODE = os.getenv('FLASK_ENV') == 'development'
TEST_API_KEY = "ds_EDpM1a_MBsPNfypdqqsdhHIfHnBPRIc5PJeadaIDDY8"

# Configure logging
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log') if not DEBUG_MODE else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking (production only)
if not DEBUG_MODE and os.getenv('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        environment='production'
    )
    logger.info("Sentry error tracking initialized")


def log_api_request(f):
    """Decorator to log API requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            response = f(*args, **kwargs)
            status_code = response[1] if isinstance(response, tuple) else 200
        except Exception as e:
            status_code = 500
            raise e
        finally:
            response_time = time.time() - start_time
            
            # Log to database (async in production)
            if not DEBUG_MODE:
                try:
                    user_id = session.get('user_id')
                    db_manager.log_api_request(
                        user_id=user_id,
                        endpoint=request.endpoint,
                        method=request.method,
                        status_code=status_code,
                        response_time=response_time,
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent', '')[:500]
                    )
                except:
                    pass
        
        return response
    return decorated_function


def get_user_chatbot(user_id):
    """Get or create chatbot instance for user"""
    if user_id not in user_chatbots:
        user_chatbots[user_id] = DataScienceChatbot()
        user_data_processors[user_id] = DataProcessor(user_id=user_id)
    return user_chatbots[user_id], user_data_processors[user_id]


# 👇 Add homepage route (flush left, no indentation)
@app.route("/")
def index():
    return "🚀 Luna Data Science Chatbot is running!"


# Chat API route
@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Handle chat requests from frontend
    """
    try:
        data = request.get_json()
        user_id = session.get("user_id", "guest")  # fallback for testing
        message = data.get("message")

        if not message:
            return jsonify({"error": "No message provided"}), 400

        # Get chatbot for this user
        chatbot, processor = get_user_chatbot(user_id)

        # Process the message
        response = chatbot.chat(message)

        return jsonify({
            "user_message": message,
            "bot_response": response
        })

    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=DEBUG_MODE)


