# 🚀 Deployment Guide - AI Data Science Chatbot

Complete guide to deploy your AI-powered chatbot to production.

## 📋 Pre-Deployment Checklist

- [ ] OpenAI API key obtained
- [ ] All files updated with new code
- [ ] Database tested locally
- [ ] Environment variables configured
- [ ] Git repository created
- [ ] Deployment platform chosen (Render/Heroku)

---

## 🏗️ Project Structure

```
data-science-chatbot/
├── app.py                    # Main Flask app (UPDATED - AI-powered)
├── config.py                 # Configuration
├── models.py                 # Database models (NEW)
├── database.py               # Database manager (UPDATED)
├── auth.py                   # Authentication
├── security.py               # Security middleware
├── migrate_db.py             # Migration script (NEW)
├── requirements.txt          # Dependencies (UPDATED)
├── Procfile                  # Heroku config (NEW)
├── render.yaml               # Render config (NEW)
├── .env                      # Environment variables
├── .gitignore               # Git ignore file
│
├── src/
│   ├── chatbot.py           # AI Chatbot (UPDATED - LLM-powered)
│   ├── data_processor.py    # Data processor (UPDATED)
│   └── tools.py             # AI function tools (NEW)
│
├── static/
│   ├── css/style.css
│   └── js/chat.js
│
└── templates/
    └── index.html
```

---

## 🔑 Step 1: Get OpenAI API Key

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy the key (starts with `sk-...`)
4. **Save it securely** - you won't see it again!

**Cost Estimate:**
- GPT-4o-mini: ~$0.15 per 1000 requests
- Very affordable for personal/small business use

---

## 🗄️ Step 2: Update Your `.env` File

```bash
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production-123456789
FLASK_ENV=development  # Change to 'production' when deploying
FLASK_DEBUG=False      # Must be False in production

# Database (will be provided by Render/Heroku)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# OpenAI API
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Security
RATE_LIMIT_ENABLED=True
SESSION_TIMEOUT=3600

# File Upload
UPLOAD_FOLDER=data
MAX_FILE_SIZE_MB=50

# CORS (optional - for frontend on different domain)
CORS_ORIGINS=*

# Sentry (optional - for error tracking)
# SENTRY_DSN=your-sentry-dsn-here
```

---

## 📦 Step 3: Update All Files

Replace/create these files with the artifacts provided:

### Core Files (Replace):
1. **app.py** - Production-ready Flask app with AI
2. **src/chatbot.py** - LLM-powered chatbot
3. **src/data_processor.py** - Enhanced data processor
4. **requirements.txt** - Production dependencies

### New Files (Create):
5. **models.py** - Database models
6. **database.py** - Enhanced database manager
7. **src/tools.py** - AI function tools
8. **migrate_db.py** - Migration script
9. **Procfile** - Heroku deployment
10. **render.yaml** - Render deployment

---

## 🧪 Step 4: Test Locally

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up database
python migrate_db.py

# 4. Run the app
python app.py
```

**Test checklist:**
- [ ] App starts without errors
- [ ] Can upload a CSV file
- [ ] AI responds to messages
- [ ] Visualizations work
- [ ] ML models train successfully

---

## 🌐 Step 5A: Deploy to Render (Recommended)

### Why Render?
- ✅ Free PostgreSQL database
- ✅ Easy setup
- ✅ Automatic HTTPS
- ✅ Great for Python apps

### Deployment Steps:

1. **Push code to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit - AI chatbot"
git branch -M main
git remote add origin https://github.com/yourusername/data-science-chatbot.git
git push -u origin main
```

2. **Create Render account:**
   - Go to [https://render.com](https://render.com)
   - Sign up with GitHub

3. **Create PostgreSQL database:**
   - Dashboard → New → PostgreSQL
   - Name: `chatbot-db`
   - Plan: Free
   - Create Database
   - **Copy the Internal Database URL**

4. **Create Web Service:**
   - Dashboard → New → Web Service
   - Connect your GitHub repository
   - Name: `data-science-chatbot`
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt && python migrate_db.py`
   - Start Command: `gunicorn app:app --workers 4 --worker-class gevent --timeout 120`

5. **Add Environment Variables:**
   ```
   SECRET_KEY=generate-a-random-secret-key
   FLASK_ENV=production
   DATABASE_URL=<paste-internal-database-url>
   OPENAI_API_KEY=sk-your-openai-key
   CORS_ORIGINS=*
   ```

6. **Deploy!**
   - Click "Create Web Service"
   - Wait 5-10 minutes for deployment
   - Your app will be at: `https://your-app-name.onrender.com`

---

## 🔷 Step 5B: Deploy to Heroku (Alternative)

### Why Heroku?
- ✅ Very reliable
- ✅ Easy scaling
- ✅ Great documentation
- ⚠️ Requires credit card (even for free tier)

### Deployment Steps:

1. **Install Heroku CLI:**
```bash
# Windows
choco install heroku-cli

# Mac
brew tap heroku/brew && brew install heroku

# Linux
curl https://cli-assets.heroku.com/install.sh | sh
```

2. **Login and create app:**
```bash
heroku login
heroku create your-app-name
```

3. **Add PostgreSQL:**
```bash
heroku addons:create heroku-postgresql:mini
```

4. **Set environment variables:**
```bash
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set FLASK_ENV=production
heroku config:set OPENAI_API_KEY="sk-your-key"
heroku config:set CORS_ORIGINS="*"
```

5. **Deploy:**
```bash
git push heroku main
```

6. **Run migrations:**
```bash
heroku run python migrate_db.py
```

7. **Open app:**
```bash
heroku open
```

---

## 🔒 Step 6: Secure Your Deployment

### 1. Update SECRET_KEY
Generate a strong secret key:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### 2. Enable HTTPS Only
In production, Flask should run behind a reverse proxy (Gunicorn handles this).

### 3. Set Up Rate Limiting
Already configured in the code - limits API requests per user.

### 4. Monitor Errors with Sentry (Optional)
```bash
# 1. Sign up at https://sentry.io
# 2. Get your DSN
# 3. Add to environment variables:
heroku config:set SENTRY_DSN="your-sentry-dsn"
```

---

## 📊 Step 7: Monitor Your App

### Check Logs:

**Render:**
```
Dashboard → Your Service → Logs
```

**Heroku:**
```bash
heroku logs --tail
```

### Database Access:

**Render:**
```
Dashboard → Database → Connect → Copy PSQL command
```

**Heroku:**
```bash
heroku pg:psql
```

### Useful SQL Queries:
```sql
-- Count users
SELECT COUNT(*) FROM users;

-- Recent conversations
SELECT * FROM conversations ORDER BY created_at DESC LIMIT 10;

-- Dataset statistics
SELECT COUNT(*), SUM(file_size) FROM datasets;

-- Top users by activity
SELECT user_id, COUNT(*) as requests 
FROM conversations 
GROUP BY user_id 
ORDER BY requests DESC 
LIMIT 10;
```

---

## 🐛 Troubleshooting

### Issue: "No module named 'src'"
```bash
# Ensure src/__init__.py exists
echo "# Package initialization" > src/__init__.py
```

### Issue: "Database connection failed"
- Check DATABASE_URL is set correctly
- Ensure PostgreSQL addon is created
- Verify connection string format

### Issue: "OpenAI API error"
- Verify API key is correct
- Check you have credits in your OpenAI account
- Ensure key has proper permissions

### Issue: "Application Error"
```bash
# Check logs
heroku logs --tail  # or Render dashboard logs

# Common fixes:
- Verify all environment variables are set
- Check requirements.txt is complete
- Ensure Procfile is correct
```

### Issue: "File upload fails"
```bash
# Create upload directory
mkdir -p data
```

---

## 📈 Scaling Your App

### Upgrade Plans:

**Render:**
- Starter: $7/month - Better performance
- Standard: $25/month - Auto-scaling

**Heroku:**
- Hobby: $7/month - 1000 hours
- Standard: $25/month - Better performance

### Optimize Performance:

1. **Enable caching:**
```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
```

2. **Use background workers:**
```bash
# For long-running ML tasks
heroku addons:create heroku-redis
# Then use Celery for async tasks
```

3. **CDN for static files:**
- Use Cloudflare or AWS CloudFront
- Serve static assets separately

---

## 🎉 Success!

Your AI-powered data science chatbot is now live!

### Next Steps:

1. **Share your app:** Give friends the URL to test
2. **Monitor usage:** Watch OpenAI API costs
3. **Collect feedback:** Improve based on user input
4. **Add features:** Custom models, more visualizations
5. **Scale up:** Upgrade when you get more users

### Support:

- **OpenAI Docs:** https://platform.openai.com/docs
- **Flask Docs:** https://flask.palletsprojects.com
- **Render Docs:** https://render.com/docs
- **Heroku Docs:** https://devcenter.heroku.com

---

**🚀 Happy deploying!**