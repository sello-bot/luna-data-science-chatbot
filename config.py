import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for the Data Science Chatbot"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # File upload settings
    UPLOAD_FOLDER = 'data'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls', 'parquet'}
    
    # AI/ML settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    MODEL_SAVE_PATH = 'models'
    PLOT_SAVE_PATH = 'static/plots'
    
    # Data processing settings
    MAX_ROWS_DISPLAY = 1000
    MAX_COLUMNS_DISPLAY = 50
    CHUNK_SIZE = 10000  # For processing large files
    
    # Cache settings
    CACHE_TIMEOUT = 300  # 5 minutes
    ENABLE_CACHING = True
    
    # Visualization settings
    PLOT_WIDTH = 800
    PLOT_HEIGHT = 600
    PLOT_DPI = 100
    
    # Machine Learning settings
    DEFAULT_TEST_SIZE = 0.2
    DEFAULT_RANDOM_STATE = 42
    MAX_FEATURES_FOR_AUTO_SELECTION = 100
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS