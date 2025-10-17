"""
Automated setup script for AI Data Science Chatbot
Run this to set up everything automatically
"""

import os
import sys
import subprocess
import secrets
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        print_error(f"Python 3.8+ required, but {version.major}.{version.minor} found")
        return False

def create_directory_structure():
    """Create necessary directories"""
    directories = [
        'src',
        'data',
        'models',
        'static/plots',
        'static/css',
        'static/js',
        'templates',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files
    Path('src/__init__.py').touch()
    
    print_success("Directory structure created")

def create_env_file():
    """Create .env file if it doesn't exist"""
    if os.path.exists('.env'):
        print_info(".env file already exists - skipping")
        return True
    
    print_info("Creating .env file...")
    
    secret_key = secrets.token_urlsafe(32)
    
    env_content = f"""# Flask Configuration
SECRET_KEY={secret_key}
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///chatbot.db

# OpenAI API Key (GET FROM: https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-openai-key-here

# Security Settings
RATE_LIMIT_ENABLED=True
SESSION_TIMEOUT=3600

# File Upload Settings
UPLOAD_FOLDER=data
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=csv,json,xlsx,xls,parquet

# API Settings
API_VERSION=1.0
DEFAULT_RATE_LIMIT=60

# CORS Settings
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print_success(".env file created")
    print_warning("⚠️  IMPORTANT: Update OPENAI_API_KEY in .env file!")
    return True

def create_gitignore():
    """Create .gitignore file"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Flask
instance/
.webassets-cache

# Data & Models
data/*
!data/.gitkeep
models/*
!models/.gitkeep
static/plots/*
!static/plots/.gitkeep

# Logs
logs/
*.log

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite
*.sqlite3
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    # Create .gitkeep files
    Path('data/.gitkeep').touch()
    Path('models/.gitkeep').touch()
    Path('static/plots/.gitkeep').touch()
    
    print_success(".gitignore created")

def install_dependencies():
    """Install Python dependencies"""
    print_info("Installing dependencies...")
    print_info("This may take a few minutes...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print_success("All dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to install dependencies")
        print_info("Try manually: pip install -r requirements.txt")
        return False

def initialize_database():
    """Initialize database"""
    print_info("Initializing database...")
    
    try:
        subprocess.check_call([sys.executable, 'migrate_db.py'])
        print_success("Database initialized")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to initialize database")
        return False
    except FileNotFoundError:
        print_warning("migrate_db.py not found - skipping database initialization")
        return True

def test_openai_key():
    """Test if OpenAI API key is configured"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key or api_key == 'sk-your-openai-key-here':
        print_warning("OpenAI API key not configured")
        print_info("Get your key from: https://platform.openai.com/api-keys")
        print_info("Then update OPENAI_API_KEY in .env file")
        return False
    
    print_success("OpenAI API key found")
    return True

def create_sample_data():
    """Create a sample CSV file for testing"""
    sample_data = """Name,Age,Salary,Department,Experience
Alice,28,75000,Engineering,5
Bob,35,95000,Engineering,12
Charlie,42,120000,Management,18
Diana,31,85000,Engineering,8
Eve,29,70000,Marketing,6
Frank,45,135000,Management,22
Grace,33,90000,Engineering,10
Henry,38,105000,Engineering,15
Iris,27,65000,Marketing,4
Jack,40,115000,Management,17
"""
    
    sample_file = 'data/sample_employees.csv'
    with open(sample_file, 'w') as f:
        f.write(sample_data)
    
    print_success(f"Sample data created: {sample_file}")

def print_next_steps():
    """Print next steps for user"""
    print_header("🎉 SETUP COMPLETE!")
    
    print("Next steps:\n")
    
    print("1️⃣  Get OpenAI API Key:")
    print("   → Go to: https://platform.openai.com/api-keys")
    print("   → Create new key")
    print("   → Update OPENAI_API_KEY in .env file\n")
    
    print("2️⃣  Start the application:")
    print("   → Run: python app.py")
    print("   → Open: http://127.0.0.1:5000\n")
    
    print("3️⃣  Test the chatbot:")
    print("   → Upload data/sample_employees.csv")
    print("   → Ask: 'Show me a summary of the data'")
    print("   → Try: 'Create a scatter plot of Age vs Salary'\n")
    
    print("4️⃣  Deploy to production:")
    print("   → Read: DEPLOYMENT.md")
    print("   → Deploy to Render or Heroku\n")
    
    print("📚 Documentation:")
    print("   → README.md - Overview and features")
    print("   → DEPLOYMENT.md - Complete deployment guide\n")
    
    print("🆘 Need help?")
    print("   → Check logs in: logs/app.log")
    print("   → Enable debug: FLASK_DEBUG=True in .env")
    print("   → Check browser console (F12)\n")

def main():
    """Main setup function"""
    print_header("🤖 AI Data Science Chatbot - Automated Setup")
    
    print("This script will:")
    print("  • Check Python version")
    print("  • Create directory structure")
    print("  • Generate .env file")
    print("  • Install dependencies")
    print("  • Initialize database")
    print("  • Create sample data\n")
    
    input("Press ENTER to continue...")
    
    # Run setup steps
    steps = [
        ("Checking Python version", check_python_version),
        ("Creating directories", create_directory_structure),
        ("Creating .env file", create_env_file),
        ("Creating .gitignore", create_gitignore),
        ("Installing dependencies", install_dependencies),
        ("Initializing database", initialize_database),
        ("Testing OpenAI configuration", test_openai_key),
        ("Creating sample data", create_sample_data),
    ]
    
    results = []
    for step_name, step_func in steps:
        print_header(step_name)
        try:
            result = step_func()
            results.append(result)
        except Exception as e:
            print_error(f"Error: {str(e)}")
            results.append(False)
    
    # Print summary
    print_header("Setup Summary")
    
    for i, (step_name, _) in enumerate(steps):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status} - {step_name}")
    
    if all(results):
        print_next_steps()
    else:
        print("\n⚠️  Some steps failed. Please check the errors above.")
        print("You may need to complete some steps manually.\n")
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)