# 🤖 AI-Powered Data Science Chatbot

An intelligent, production-ready chatbot that uses GPT-4 to help you analyze data, create visualizations, and build machine learning models through natural conversation.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.3-green.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

### 🧠 AI-Powered Intelligence
- **GPT-4 Integration**: Natural language understanding with OpenAI
- **Function Calling**: AI automatically chooses the right tools
- **Context Awareness**: Remembers your conversation and dataset
- **Smart Suggestions**: AI recommends next steps in analysis

### 📊 Data Analysis
- **Multi-Format Support**: CSV, Excel, JSON, Parquet
- **Automatic EDA**: Summary statistics, missing values, correlations
- **Data Quality Reports**: Comprehensive data health checks
- **Smart Filtering**: Natural language data queries

### 📈 Visualizations
- **10+ Chart Types**: Scatter, line, bar, histogram, heatmap, and more
- **Interactive Plots**: Powered by Plotly
- **Auto-Generated**: AI creates appropriate visualizations
- **Exportable**: Save and share your plots

### 🤖 Machine Learning
- **5+ Algorithms**: Linear/Logistic Regression, Random Forest, K-Means, etc.
- **Auto Feature Selection**: AI picks the best features
- **Model Evaluation**: Automatic metrics and performance reports
- **Model Persistence**: Save and reuse trained models

### 💾 Persistent Storage
- **PostgreSQL Database**: Production-ready with full ACID compliance
- **Conversation History**: Keep track of all interactions
- **Dataset Management**: Upload, track, and manage multiple datasets
- **User Accounts**: Multi-user support with authentication

### 🔒 Security & Performance
- **API Key Authentication**: Secure access control
- **Rate Limiting**: Prevent abuse
- **Input Validation**: Sanitize all user inputs
- **Error Tracking**: Sentry integration for monitoring

---

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# 1. Clone or download the project
cd data-science-chatbot

# 2. Run automated setup
python setup.py

# 3. Update .env with your OpenAI API key
# Get key from: https://platform.openai.com/api-keys

# 4. Start the app
python app.py

# 5. Open browser
# Go to: http://127.0.0.1:5000
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Initialize database
python migrate_db.py

# 5. Run the app
python app.py
```

---

## 💬 Example Conversations

### Data Analysis
```
You: Upload sample_employees.csv

Bot: Great! I've loaded your dataset with 10 rows and 5 columns. 
     What would you like to explore?

You: Show me summary statistics

Bot: Here's a summary of your data:
     [Shows statistics table]
     
     I notice:
     • Average age: 33.8 years
     • Average salary: $95,000
     • 3 departments represented
     
     Would you like to see correlations or visualizations?

You: Create a scatter plot of Age vs Salary

Bot: [Creates interactive scatter plot]
     
     The plot shows a positive correlation between age and salary.
     Older employees tend to earn more, with r=0.85.
     
     Would you like to:
     • Add a trend line?
     • Color by department?
     • Train a prediction model?
```

### Machine Learning
```
You: Train a model to predict salary

Bot: I'll train a Random Forest model to predict salary.
     Using features: Age, Experience, Department
     
     [Trains model]
     
     Results:
     • R² Score: 0.92 (excellent fit!)
     • RMSE: $6,500
     • Top feature: Experience (importance: 0.65)
     
     Your model is ready! Want to make predictions?

You: What salary would a 30-year-old with 7 years experience in Engineering earn?

Bot: Based on the model, predicted salary: $82,500 ± $6,500
```

### Data Exploration
```
You: What patterns do you see in the data?

Bot: Analyzing your dataset, I found:
     
     1. Strong correlation (0.89) between Age and Experience
     2. Engineering department has highest average salary ($87,500)
     3. No missing values - data quality is excellent!
     4. Salary distribution is slightly right-skewed
     
     Recommendations:
     • Remove Age or Experience to avoid multicollinearity
     • Consider log-transforming Salary for modeling
     • Explore promotion patterns by department
```

---

## 🛠️ Tech Stack

### Backend
- **Flask 3.0.3**: Web framework
- **OpenAI GPT-4**: AI intelligence
- **SQLAlchemy 2.0**: ORM and database
- **PostgreSQL**: Production database
- **Gunicorn**: WSGI server

### Data Science
- **Pandas 2.2**: Data manipulation
- **NumPy 1.26**: Numerical computing
- **Scikit-learn 1.5**: Machine learning
- **Plotly 5.22**: Interactive visualizations

### Security
- **bcrypt**: Password hashing
- **JWT**: Token authentication
- **Flask-CORS**: Cross-origin requests

---

## 📊 AI Function Tools

The chatbot has access to these tools:

| Tool | Description | Example |
|------|-------------|---------|
| `analyze_data` | Get statistics, correlations, missing values | "Show me data summary" |
| `create_visualization` | Generate charts and plots | "Plot Age vs Salary" |
| `train_model` | Train ML models | "Train a regression model" |
| `filter_data` | Filter rows by conditions | "Show rows where Age > 30" |
| `get_data_sample` | Get sample rows | "Show me 10 random rows" |

The AI automatically chooses which tools to use based on your request!

---

## 🗄️ Database Schema

```sql
users
├── id (PK)
├── email
├── password_hash
├── api_key
├── plan (free/premium)
└── usage stats

datasets
├── id (PK)
├── user_id (FK)
├── filename
├── rows, columns
├── metadata (JSON)
└── timestamps

conversations
├── id (PK)
├── user_id (FK)
├── session_id
├── role (user/assistant)
├── message
└── function_called

ml_models
├── id (PK)
├── user_id (FK)
├── model_type
├── metrics (JSON)
└── model_path
```

---

## 🌐 API Endpoints

### Chat & Data
- `POST /api/chat` - Send message to chatbot
- `POST /api/upload` - Upload dataset
- `GET /api/datasets` - List user's datasets
- `GET /api/dataset/<id>` - Get dataset details
- `DELETE /api/dataset/<id>` - Delete dataset

### User Management
- `POST /register` - Create account
- `POST /login` - User login
- `GET /logout` - User logout
- `GET /api/stats` - User statistics

### ML Models
- `GET /api/models` - List trained models
- `GET /api/conversations` - Conversation history

### System
- `GET /api/health` - Health check
- `GET /api/system/stats` - System statistics

---

## 🚢 Deployment

### Deploy to Render (Free)

1. **Push to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Create Render Account:**
   - Go to [render.com](https://render.com)
   - Connect GitHub

3. **Create Database:**
   - New → PostgreSQL
   - Copy connection string

4. **Create Web Service:**
   - New → Web Service
   - Connect repository
   - Add environment variables
   - Deploy!

**See [DEPLOYMENT.md](DEPLOYMENT.md) for complete guide**

### Deploy to Heroku

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
heroku config:set OPENAI_API_KEY=your-key
git push heroku main
```

---

## 🔑 Environment Variables

Required:
```bash
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-your-key
DATABASE_URL=postgresql://...
```

Optional:
```bash
FLASK_ENV=development|production
SENTRY_DSN=your-sentry-dsn
CORS_ORIGINS=*
MAX_FILE_SIZE_MB=50
```

---

## 💰 Cost Estimate

### OpenAI API
- **GPT-4o-mini**: $0.15 per 1M input tokens
- **Average request**: ~1,000 tokens
- **Cost per request**: ~$0.0002 (very cheap!)
- **1000 requests**: ~$0.20

### Hosting
- **Render Free Tier**: $0/month (750 hours)
- **Render Starter**: $7/month (always on)
- **Heroku Hobby**: $7/month
- **Database**: Free tier included

**Total for personal use: ~$10-15/month**

---

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=.

# Test specific module
pytest tests/test_chatbot.py
```

---

## 📝 Development

### Add New AI Function

1. **Define function in `src/tools.py`:**
```python
def my_new_function(df, params):
    # Your logic here
    return {"result": data, "code": code}
```

2. **Add to chatbot tools in `src/chatbot.py`:**
```python
{
    "type": "function",
    "function": {
        "name": "my_new_function",
        "description": "What it does",
        "parameters": {...}
    }
}
```

3. **Add execution in `_execute_function`:**
```python
elif function_name == "my_new_function":
    return self._my_new_function(args, data_processor)
```

---

## 🐛 Troubleshooting

### Issue: ChatBot not responding
- Check OpenAI API key in .env
- Verify API key has credits
- Check browser console for errors

### Issue: Database error
```bash
# Reset database
python migrate_db.py
```

### Issue: Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: File upload fails
- Check file size < 50MB
- Verify file format (CSV, Excel, JSON)
- Check `data/` directory exists

---

## 📚 Documentation

- **README.md** - This file
- **DEPLOYMENT.md** - Complete deployment guide
- **API.md** - API documentation
- **CONTRIBUTING.md** - Contribution guidelines

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Flask team for the framework
- Plotly for visualizations
- The open-source community

---

## 📧 Support

- **Issues**: Open a GitHub issue
- **Email**: skgole6@gmail.com
- **Docs**: Check DEPLOYMENT.md

---

## 🎯 Roadmap

- [ ] Add more ML algorithms (XGBoost, LightGBM)
- [ ] Support for time series analysis
- [ ] Custom model training UI
- [ ] Automated report generation
- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Collaborative workspaces
- [ ] API for external integrations

---

**Made with ❤️ for data scientists**

**⭐ Star this repo if you find it useful!**