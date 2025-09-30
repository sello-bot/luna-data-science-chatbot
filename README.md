# Data Science Chatbot

An intelligent chatbot for data science tasks including data analysis, visualization, and machine learning.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or download the repository**

2. **Create a virtual environment**
```bash
python -m venv venv
```

3. **Activate the virtual environment**

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Create a `.env` file** (optional)
```env
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
FLASK_DEBUG=True
```

6. **Run the application**
```bash
python app.py
```

7. **Open your browser** and navigate to:
```
http://127.0.0.1:5000
```

## 📁 Project Structure

```
data-science-chatbot/
│
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
│
├── src/
│   ├── chatbot.py        # Chatbot logic
│   ├── data_processor.py # Data processing
│
├── auth.py               # Authentication manager
├── security.py           # Security middleware
├── database.py           # Database manager
│
├── static/
│   ├── css/
│   │   └── style.css     # Styles
│   └── js/
│       └── chat.js       # Frontend JavaScript
│
├── templates/
│   ├── index.html        # Main chat interface
│   ├── login.html        # Login page
│   └── register.html     # Registration page
│
├── data/                 # Uploaded datasets (auto-created)
├── models/               # Saved ML models (auto-created)
└── static/plots/         # Generated visualizations (auto-created)
```

## 🔧 Troubleshooting

### Chatbot not responding?

1. **Check browser console** (F12) for errors
2. **Check Flask terminal** for error messages
3. **Verify DEBUG_MODE is True** in `app.py`:
```python
DEBUG_MODE = True  # Line ~33 in app.py
```

### Import errors?

Make sure all required modules exist. Create minimal versions if needed:

**src/chatbot.py:**
```python
class DataScienceChatbot:
    def __init__(self):
        self.current_dataset = None
    
    def process_message(self, message, data_processor):
        return {
            "message": f"You said: {message}",
            "data": None,
            "visualization": None,
            "code": None
        }
```

**src/data_processor.py:**
```python
import pandas as pd

class DataProcessor:
    def __init__(self):
        self.data = None
    
    def load_data(self, filepath):
        self.data = pd.read_csv(filepath)
        return self.data
    
    def get_data_info(self):
        if self.data is None:
            return {}
        return {
            "shape": self.data.shape,
            "columns": list(self.data.columns),
            "dtypes": {k: str(v) for k, v in self.data.dtypes.items()}
        }
```

**auth.py:**
```python
class AuthManager:
    def __init__(self):
        pass
    
    def validate_api_key(self, api_key):
        return {"valid": True, "user_id": 1}
    
    def increment_usage(self, user_id, endpoint):
        pass

def require_auth(f):
    return f

def require_api_key(auth_manager):
    def decorator(f):
        return f
    return decorator
```

**security.py:**
```python
class SecurityManager:
    def __init__(self):
        self.rate_limits = {}
    
    def validate_file_upload(self, file):
        return {
            "valid": True,
            "secure_filename": file.filename,
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
```

**database.py:**
```python
class DatabaseManager:
    def __init__(self):
        pass
    
    def save_dataset(self, user_id, filename, original_filename, filepath, filesize, filetype, data_info):
        return {"dataset_id": 1}
    
    def get_user_datasets(self, user_id):
        return []
```

## 🎯 Features

- 📊 Data upload and analysis (CSV, Excel, JSON)
- 📈 Interactive visualizations
- 🤖 AI-powered chat interface
- 💾 Dataset management
- 🔐 Secure authentication
- 📱 Responsive design

## 📝 Usage

1. **Upload a dataset** using the sidebar
2. **Ask questions** about your data
3. **Request visualizations** or analysis
4. **Train models** for predictions

### Example Queries:
- "Show me the first 10 rows"
- "Create a scatter plot of X vs Y"
- "What's the correlation between columns?"
- "Train a linear regression model"
- "Show data summary statistics"

## 🛠️ Development

### Debug Mode
Set `DEBUG_MODE = True` in `app.py` to:
- Skip authentication checks
- Auto-create user sessions
- Enable detailed logging
- Use test API key

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main chat interface |
| `/api/chat` | POST | Send message to chatbot |
| `/api/upload` | POST | Upload dataset |
| `/api/datasets` | GET | List user datasets |
| `/api/health` | GET | Health check |
| `/login` | GET/POST | User login |
| `/register` | GET/POST | User registration |
| `/logout` | GET | User logout |

### Testing the Chat

1. Open browser console (F12)
2. Type a message and click send
3. Watch the logs in both:
   - Browser console (for frontend debugging)
   - Terminal (for backend debugging)

Look for:
```
🚀 sendMessage() called
📡 Sending fetch request to /api/chat
📨 Response status: 200
✅ Success! Adding bot response
```

## 🐛 Common Issues

### Issue: "No module named 'src'"
**Solution:** Create the missing module files (see Troubleshooting section)

### Issue: "API key required"
**Solution:** Ensure `DEBUG_MODE = True` in `app.py` or add API key to headers

### Issue: Session errors
**Solution:** Clear browser cookies or use incognito mode

### Issue: File upload fails
**Solution:** 
- Check file size (max 50MB)
- Verify file format (CSV, Excel, JSON only)
- Ensure `data/` directory exists

### Issue: Database errors
**Solution:** Database is optional in debug mode. Comment out database calls if not needed.

## 🔒 Security Notes

⚠️ **IMPORTANT FOR PRODUCTION:**

1. Change `SECRET_KEY` in `config.py`
2. Set `DEBUG_MODE = False` in `app.py`
3. Remove hardcoded `TEST_API_KEY`
4. Use environment variables for sensitive data
5. Enable proper authentication
6. Use HTTPS in production
7. Set up proper rate limiting

## 📦 Dependencies

Main packages:
- Flask 3.0.3 - Web framework
- pandas 2.2.3 - Data manipulation
- scikit-learn 1.5.1 - Machine learning
- plotly 5.22.0 - Visualizations
- openai 1.40.0 - AI integration

See `requirements.txt` for complete list.

## 🚀 Deployment

### Heroku Deployment

1. **Create `Procfile`:**
```
web: gunicorn app:app
```

2. **Deploy:**
```bash
heroku create your-app-name
git push heroku main
```

3. **Set environment variables:**
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set OPENAI_API_KEY=your-openai-key
```

### Local Production Server

Use gunicorn instead of Flask development server:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📚 API Usage Example

### JavaScript (Frontend)
```javascript
// Send chat message
const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'your-api-key'
    },
    body: JSON.stringify({ message: 'Hello!' })
});

const data = await response.json();
console.log(data.response);
```

### Python (Backend)
```python
import requests

response = requests.post(
    'http://localhost:5000/api/chat',
    json={'message': 'Show data summary'},
    headers={'X-API-Key': 'your-api-key'}
)

print(response.json())
```

## 🎨 Customization

### Change Theme Colors
Edit `static/css/style.css`:
```css
:root {
    --primary-color: #4a90e2;  /* Change this */
    --secondary-color: #7b68ee; /* And this */
}
```

### Add Custom Commands
Edit `src/chatbot.py` to add new chat commands:
```python
def process_message(self, message, data_processor):
    if 'custom command' in message.lower():
        return {
            "message": "Custom response",
            "data": None
        }
```

### Add File Types
Edit `config.py`:
```python
ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls', 'parquet'}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 💡 Tips

- Use sample data to test without uploading files
- Check browser console for debugging
- Enable Flask debug mode for development
- Keep dependencies updated
- Back up your data directory
- Monitor API usage costs

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section
2. Look at browser console errors
3. Review Flask terminal logs
4. Ensure all files are in correct locations
5. Verify Python version compatibility

## 📞 Contact

For questions or support, please open an issue on the repository.

---

**Happy Data Science! 🎉📊**