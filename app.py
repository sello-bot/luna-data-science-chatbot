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

# Hardcoded API key for local testing (REMOVE in production!)
TEST_API_KEY = "ds_EDpM1a_MBsPNfypdqqsdhHIfHnBPRIc5PJeadaIDDY8"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# DEBUG MODE FLAG
DEBUG_MODE = True  # Set to False for production


def get_user_chatbot(user_id):
    """Get or create chatbot instance for user"""
    if user_id not in user_chatbots:
        user_chatbots[user_id] = DataScienceChatbot()
        user_data_processors[user_id] = DataProcessor()
    return user_chatbots[user_id], user_data_processors[user_id]


# ------------------ AUTH ROUTES ------------------

@app.route("/register", methods=["GET", "POST"])
@secure_headers
def register():
    if request.method == "GET":
        return render_template("register.html")

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    plan = data.get("plan", "free")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    result = auth_manager.register_user(email, password, plan)
    if "error" in result:
        return jsonify(result), 400

    return jsonify({
        "success": True,
        "message": "Registration successful",
        "api_key": result["api_key"]
    })


@app.route("/login", methods=["GET", "POST"])
@secure_headers
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    result = auth_manager.authenticate_user(email, password)
    if "error" in result:
        return jsonify(result), 401

    session["user_id"] = result["user_id"]
    session["plan"] = result["plan"]

    return jsonify({
        "success": True,
        "message": "Login successful",
        "api_key": result["api_key"],
        "plan": result["plan"]
    })


@app.route("/logout")
@secure_headers
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})


# ------------------ MAIN ROUTES ------------------

@app.route("/")
@secure_headers
def index():
    # In debug mode, auto-create session
    if DEBUG_MODE and "user_id" not in session:
        session["user_id"] = 1
        session["plan"] = "free"
        logger.info("🔧 DEBUG: Auto-created session for user_id=1")
    
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
@secure_headers
def chat():
    """
    Main chat endpoint - simplified for debug mode
    """
    try:
        logger.info("=== CHAT ENDPOINT HIT ===")
        
        # Get request data
        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({"error": "No data provided"}), 400
        
        logger.info(f"Received data: {data}")
        
        user_message = data.get("message", "")
        if not user_message:
            logger.error("No message in request")
            return jsonify({"error": "Message is required"}), 400
        
        logger.info(f"User message: {user_message}")
        
        # In debug mode, skip authentication
        if DEBUG_MODE:
            user_id = 1
            logger.info("🔧 DEBUG: Using user_id=1 (skipping auth)")
        else:
            # Production authentication
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                logger.error("No API key provided")
                return jsonify({"error": "API key required"}), 401

            validation = auth_manager.validate_api_key(api_key)
            if not validation["valid"]:
                logger.error(f"Invalid API key: {validation.get('error')}")
                return jsonify({"error": validation["error"]}), 401

            user_id = validation["user_id"]
            auth_manager.increment_usage(user_id, request.endpoint)
        
        # Basic input sanitization
        user_message = user_message.strip()
        if len(user_message) > 5000:
            return jsonify({"error": "Message too long (max 5000 characters)"}), 400
        
        session_id = data.get("session_id", str(uuid.uuid4()))
        logger.info(f"Processing message for user_id={user_id}, session_id={session_id}")
        
        # Get or create chatbot instance
        chatbot, data_processor = get_user_chatbot(user_id)
        logger.info("Got chatbot and data processor instances")
        
        # Process the message
        logger.info("Calling chatbot.process_message()")
        response = chatbot.process_message(user_message, data_processor)
        logger.info(f"Chatbot response: {response}")
        
        return jsonify({
            "response": response.get("message", ""),
            "data": response.get("data"),
            "visualization": response.get("visualization"),
            "code": response.get("code"),
            "session_id": session_id
        })

    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# ------------------ UPLOAD ROUTE ------------------

@app.route("/api/upload", methods=["POST"])
@secure_headers
def upload_file():
    try:
        logger.info("=== UPLOAD ENDPOINT HIT ===")
        
        # In debug mode, create fake user_info
        if DEBUG_MODE:
            user_id = 1
            logger.info("🔧 DEBUG: Using user_id=1 for upload")
        else:
            # Production auth
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header == f"Bearer {TEST_API_KEY}":
                user_id = "test_user"
            else:
                api_key = request.headers.get("X-API-Key")
                if not api_key:
                    return jsonify({"error": "API key required"}), 401
                
                validation = auth_manager.validate_api_key(api_key)
                if not validation["valid"]:
                    return jsonify({"error": validation["error"]}), 401
                
                user_id = validation["user_id"]

        if "file" not in request.files:
            logger.error("No file in request")
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        logger.info(f"File received: {file.filename}")
        
        # Basic validation
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        allowed_extensions = {'.csv', '.json', '.xlsx', '.xls'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({"error": f"File type {file_ext} not allowed"}), 400
        
        # Secure the filename
        secure_name = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        secure_name = f"{timestamp}_{secure_name}"
        
        file_path = os.path.join("data", secure_name)
        os.makedirs("data", exist_ok=True)
        
        logger.info(f"Saving file to: {file_path}")
        file.save(file_path)

        # Load and process data
        chatbot, data_processor = get_user_chatbot(user_id)
        logger.info("Loading data...")
        dataset = data_processor.load_data(file_path)
        data_info = data_processor.get_data_info()
        logger.info(f"Data loaded: {data_info}")

        chatbot.current_dataset = dataset
        file_size = os.path.getsize(file_path)
        file_type = file_ext[1:]  # Remove the dot

        # Save to database (if available)
        dataset_id = None
        try:
            dataset_result = db_manager.save_dataset(
                user_id, secure_name, file.filename,
                file_path, file_size, file_type, data_info
            )
            dataset_id = dataset_result.get("dataset_id")
        except Exception as e:
            logger.warning(f"Could not save to database: {str(e)}")

        return jsonify({
            "message": f"File uploaded successfully! Shape: {data_info['shape']}, Columns: {len(data_info['columns'])}",
            "data_info": data_info,
            "dataset_id": dataset_id
        })

    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        if "file_path" in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": f"Failed to process uploaded file: {str(e)}"}), 500


# ------------------ DATASETS ROUTE ------------------

@app.route("/api/datasets", methods=["GET"])
@secure_headers
def get_datasets():
    try:
        if DEBUG_MODE:
            user_id = 1
        else:
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                return jsonify({"error": "API key required"}), 401
            
            validation = auth_manager.validate_api_key(api_key)
            if not validation["valid"]:
                return jsonify({"error": validation["error"]}), 401
            
            user_id = validation["user_id"]
        
        datasets = db_manager.get_user_datasets(user_id)
        return jsonify({"datasets": datasets})
    
    except Exception as e:
        logger.error(f"Error fetching datasets: {str(e)}")
        return jsonify({"error": "Failed to fetch datasets"}), 500


# ------------------ HEALTH CHECK ------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "debug_mode": DEBUG_MODE,
        "timestamp": datetime.now().isoformat()
    })


# ------------------ CLEANUP ------------------

def cleanup_old_data():
    try:
        if hasattr(db_manager, "cleanup_old_sessions"):
            db_manager.cleanup_old_sessions(7)
        if hasattr(db_manager, "cleanup_old_conversations"):
            db_manager.cleanup_old_conversations(30)
        logger.info("Cleanup done")
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")


if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("static/plots", exist_ok=True)
    os.makedirs("templates", exist_ok=True)

    # Run cleanup
    cleanup_old_data()
    
    # Log startup info
    logger.info("=" * 50)
    logger.info("🚀 Starting Data Science Chatbot")
    logger.info(f"Debug Mode: {DEBUG_MODE}")
    logger.info(f"Flask Debug: {app.config.get('DEBUG', False)}")
    logger.info("=" * 50)
    
    # Run the app
    app.run(
        debug=app.config.get("DEBUG", False), 
        host="0.0.0.0", 
        port=5000
    )

