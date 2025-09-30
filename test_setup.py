"""
Setup verification script for Data Science Chatbot
Run this to check if all dependencies and files are in place
"""

import sys
import os

def print_status(message, status):
    """Print colored status message"""
    colors = {
        'success': '\033[92m✓\033[0m',
        'error': '\033[91m✗\033[0m',
        'warning': '\033[93m⚠\033[0m',
        'info': '\033[94mℹ\033[0m'
    }
    print(f"{colors.get(status, '•')} {message}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_status(f"Python version: {version.major}.{version.minor}.{version.micro}", "success")
        return True
    else:
        print_status(f"Python version {version.major}.{version.minor} is too old. Need 3.8+", "error")
        return False

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'flask',
        'pandas',
        'sklearn',
        'plotly',
        'werkzeug',
        'sqlalchemy'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_status(f"Package '{package}' installed", "success")
        except ImportError:
            print_status(f"Package '{package}' missing", "error")
            missing.append(package)
    
    if missing:
        print_status(f"\nInstall missing packages with: pip install {' '.join(missing)}", "warning")
        return False
    return True

def check_files():
    """Check if all required files exist"""
    required_files = {
        'app.py': 'Main application file',
        'config.py': 'Configuration file',
        'requirements.txt': 'Dependencies file',
        'static/css/style.css': 'Stylesheet',
        'static/js/chat.js': 'Frontend JavaScript',
        'templates/index.html': 'Main template'
    }
    
    missing = []
    for file, description in required_files.items():
        if os.path.exists(file):
            print_status(f"{description}: {file}", "success")
        else:
            print_status(f"Missing {description}: {file}", "error")
            missing.append(file)
    
    return len(missing) == 0

def check_directories():
    """Check and create required directories"""
    required_dirs = ['data', 'models', 'static/plots', 'templates', 'src']
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print_status(f"Directory '{directory}' exists", "success")
        else:
            try:
                os.makedirs(directory, exist_ok=True)
                print_status(f"Created directory '{directory}'", "warning")
            except Exception as e:
                print_status(f"Failed to create '{directory}': {e}", "error")
                return False
    return True

def check_modules():
    """Check if custom modules can be imported"""
    modules = {
        'src.chatbot': 'DataScienceChatbot',
        'src.data_processor': 'DataProcessor',
        'auth': 'AuthManager',
        'security': 'SecurityManager',
        'database': 'DatabaseManager'
    }
    
    missing = []
    for module, cls in modules.items():
        try:
            mod = __import__(module, fromlist=[cls])
            getattr(mod, cls)
            print_status(f"Module '{module}.{cls}' available", "success")
        except (ImportError, AttributeError) as e:
            print_status(f"Module '{module}.{cls}' missing", "error")
            missing.append(module)
    
    if missing:
        print_status("\nSome custom modules are missing. Create them or use minimal versions.", "warning")
        return False
    return True

def create_minimal_modules():
    """Create minimal versions of missing modules"""
    print("\n" + "="*60)
    print("Creating minimal module versions...")
    print("="*60 + "\n")
    
    # Create src directory
    os.makedirs('src', exist_ok=True)
    
    # Create __init__.py
    with open('src/__init__.py', 'w') as f:
        f.write('# Package initialization\n')
    print_status("Created src/__init__.py", "success")
    
    # Create chatbot.py
    chatbot_code = '''"""Minimal chatbot implementation"""

class DataScienceChatbot:
    def __init__(self):
        self.current_dataset = None
        self.conversation_history = []
    
    def process_message(self, message, data_processor):
        """Process user message and return response"""
        self.conversation_history.append({"role": "user", "content": message})
        
        # Simple response logic
        message_lower = message.lower()
        
        if 'hello' in message_lower or 'hi' in message_lower:
            response = "Hello! I'm your data science assistant. How can I help you today?"
        elif 'help' in message_lower:
            response = """I can help you with:
- Loading and analyzing datasets
- Creating visualizations
- Data preprocessing
- Basic statistics
- And more! Just ask me anything about your data."""
        elif 'sample' in message_lower and 'data' in message_lower:
            response = "I can help you create sample data. Try uploading a CSV file first!"
        else:
            response = f"I understand you said: '{message}'. I'm a basic chatbot. Upload data to unlock more features!"
        
        return {
            "message": response,
            "data": None,
            "visualization": None,
            "code": None
        }
'''
    
    with open('src/chatbot.py', 'w') as f:
        f.write(chatbot_code)
    print_status("Created src/chatbot.py", "success")
    
    # Create data_processor.py
    processor_code = '''"""Minimal data processor implementation"""
import pandas as pd
import os

class DataProcessor:
    def __init__(self):
        self.data = None
        self.filepath = None
    
    def load_data(self, filepath):
        """Load data from file"""
        ext = os.path.splitext(filepath)[1].lower()
        
        try:
            if ext == '.csv':
                self.data = pd.read_csv(filepath)
            elif ext in ['.xlsx', '.xls']:
                self.data = pd.read_excel(filepath)
            elif ext == '.json':
                self.data = pd.read_json(filepath)
            else:
                raise ValueError(f"Unsupported file type: {ext}")
            
            self.filepath = filepath
            return self.data
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
    
    def get_data_info(self):
        """Get information about loaded data"""
        if self.data is None:
            return {
                "shape": (0, 0),
                "columns": [],
                "dtypes": {}
            }
        
        return {
            "shape": self.data.shape,
            "columns": list(self.data.columns),
            "dtypes": {col: str(dtype) for col, dtype in self.data.dtypes.items()},
            "memory_usage": self.data.memory_usage(deep=True).sum()
        }
'''
    
    with open('src/data_processor.py', 'w') as f:
        f.write(processor_code)
    print_status("Created src/data_processor.py", "success")
    
    # Create auth.py
    auth_code = '''"""Minimal authentication manager"""

class AuthManager:
    def __init__(self):
        self.users = {}
    
    def validate_api_key(self, api_key):
        return {"valid": True, "user_id": 1, "plan": "free"}
    
    def increment_usage(self, user_id, endpoint):
        pass
    
    def register_user(self, email, password, plan="free"):
        return {"api_key": "test-key", "user_id": 1}
    
    def authenticate_user(self, email, password):
        return {"user_id": 1, "api_key": "test-key", "plan": "free"}

def require_auth(f):
    return f

def require_api_key(auth_manager):
    def decorator(f):
        return f
    return decorator
'''
    
    with open('auth.py', 'w') as f:
        f.write(auth_code)
    print_status("Created auth.py", "success")
    
    # Create security.py
    security_code = '''"""Minimal security manager"""
from werkzeug.utils import secure_filename as werkzeug_secure_filename

class SecurityManager:
    def __init__(self):
        self.rate_limits = {}
    
    def validate_file_upload(self, file):
        filename = werkzeug_secure_filename(file.filename)
        return {
            "valid": True,
            "secure_filename": filename,
            "original_filename": file.filename,
            "errors": []
        }
    
    def validate_chat_input(self, message):
        return {
            "valid": True,
            "sanitized_message": message,
            "error": None
        }

def require_rate_limit(security_manager, max_requests=100, window_minutes=1):
    def decorator(f):
        return f
    return decorator

def validate_json_input(required_fields=None):
    def decorator(f):
        return f
    return decorator

def secure_headers(f):
    return f
'''
    
    with open('security.py', 'w') as f:
        f.write(security_code)
    print_status("Created security.py", "success")
    
    # Create database.py
    database_code = '''"""Minimal database manager"""

class DatabaseManager:
    def __init__(self):
        self.datasets = {}
    
    def save_dataset(self, user_id, filename, original_filename, filepath, filesize, filetype, data_info):
        dataset_id = len(self.datasets) + 1
        self.datasets[dataset_id] = {
            "user_id": user_id,
            "filename": filename,
            "original_filename": original_filename,
            "filepath": filepath,
            "filesize": filesize,
            "filetype": filetype,
            "data_info": data_info
        }
        return {"dataset_id": dataset_id}
    
    def get_user_datasets(self, user_id):
        return [d for d in self.datasets.values() if d["user_id"] == user_id]
    
    def cleanup_old_sessions(self, days):
        pass
    
    def cleanup_old_conversations(self, days):
        pass
'''
    
    with open('database.py', 'w') as f:
        f.write(database_code)
    print_status("Created database.py", "success")
    
    print_status("\nAll minimal modules created successfully!", "success")

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("Data Science Chatbot - Setup Verification")
    print("="*60 + "\n")
    
    checks = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Directories": check_directories(),
        "Required Files": check_files(),
        "Custom Modules": check_modules()
    }
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60 + "\n")
    
    all_passed = all(checks.values())
    
    for check, passed in checks.items():
        status = "success" if passed else "error"
        print_status(f"{check}: {'PASSED' if passed else 'FAILED'}", status)
    
    if not checks["Custom Modules"]:
        print("\n" + "="*60)
        response = input("\nCreate minimal module files? (y/n): ")
        if response.lower() == 'y':
            create_minimal_modules()
            print_status("\nModules created! Re-run this script to verify.", "info")
        else:
            print_status("Skipping module creation. You'll need to create them manually.", "warning")
    
    if all_passed:
        print("\n" + "="*60)
        print_status("✓ All checks passed! You're ready to run the app.", "success")
        print_status("Start the app with: python app.py", "info")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print_status("✗ Some checks failed. Please fix the issues above.", "error")
        print("="*60 + "\n")

if __name__ == "__main__":
    main()