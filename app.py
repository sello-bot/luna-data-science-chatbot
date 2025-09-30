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
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
@secure_headers
@require_rate_limit(security_manager, max_requests=30, window_minutes=1)
@validate_json_input(required_fields=["message"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if app.config.get("DEBUG", False):
            user_id = 1  # Dev mode
        else:
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                return jsonify({"error": "API key required"}), 401

            validation = auth_manager.validate_api_key(api_key)
            if not validation["valid"]:
                return jsonify({"error": validation["error"]}), 401

            user_id = validation["user_id"]
            auth_manager.increment_usage(user_id, request.endpoint)

        validation = security_manager.validate_chat_input(user_message)
        if not validation["valid"]:
            return jsonify({"error": validation["error"]}), 400

        user_message = validation["sanitized_message"]
        session_id = data.get("session_id", str(uuid.uuid4()))

        chatbot, data_processor = get_user_chatbot(user_id)
        response = chatbot.process_message(user_message, data_processor)

        return jsonify({
            "response": response["message"],
            "data": response.get("data"),
            "visualization": response.get("visualization"),
            "code": response.get("code"),
            "session_id": session_id
        })

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": "An error occurred processing your request"}), 500


# ------------------ UPLOAD ROUTE (fixed) ------------------

@app.route("/api/upload", methods=["POST"])
@secure_headers
@require_rate_limit(security_manager, max_requests=10, window_minutes=1)
@require_api_key(auth_manager)
def upload_file():
    try:
        # Allow local dev with hardcoded TEST_API_KEY
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header == f"Bearer {TEST_API_KEY}":
            request.user_info = {
                "user_id": "test_user",
                "plan": "free",
                "remaining_usage": 100000
            }
            logger.info("Test API key authenticated (local dev)")

        user_id = request.user_info["user_id"]

        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        validation = security_manager.validate_file_upload(file)
        if not validation["valid"]:
            return jsonify({"error": validation["errors"][0]}), 400

        secure_name = validation["secure_filename"]
        file_path = os.path.join("data", secure_name)
        os.makedirs("data", exist_ok=True)
        file.save(file_path)

        chatbot, data_processor = get_user_chatbot(user_id)
        dataset = data_processor.load_data(file_path)
        data_info = data_processor.get_data_info()

        chatbot.current_dataset = dataset
        file_size = os.path.getsize(file_path)
        file_type = os.path.splitext(secure_name)[1][1:]

        dataset_result = db_manager.save_dataset(
            user_id, secure_name, validation["original_filename"],
            file_path, file_size, file_type, data_info
        )

        return jsonify({
            "message": f"File uploaded successfully! Shape: {data_info['shape']}, Columns: {len(data_info['columns'])}",
            "data_info": data_info,
            "dataset_id": dataset_result.get("dataset_id")
        })

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        if "file_path" in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": "Failed to process uploaded file"}), 500


# ------------------ OTHER ROUTES (datasets, models, etc.) ------------------
# (keep the rest of your routes as-is, unchanged)


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
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("static/plots", exist_ok=True)
    os.makedirs("templates", exist_ok=True)

    cleanup_old_data()
    app.run(debug=app.config.get("DEBUG", False), host="0.0.0.0", port=5000)

