# auth.py - User Authentication Module
from flask import session, request, jsonify, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import uuid
from datetime import datetime, timedelta
import secrets

class AuthManager:
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize user database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                plan TEXT DEFAULT 'free',
                usage_limit INTEGER DEFAULT 100,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # API keys table for tracking usage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                endpoint TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_user(self, email, password, plan='free'):
        """Register a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                return {'error': 'User already exists'}
            
            # Generate API key
            api_key = 'ds_' + secrets.token_urlsafe(32)
            password_hash = generate_password_hash(password)
            
            # Set usage limits based on plan
            usage_limits = {'free': 100, 'basic': 1000, 'premium': 10000}
            usage_limit = usage_limits.get(plan, 100)
            
            cursor.execute('''
                INSERT INTO users (email, password_hash, api_key, plan, usage_limit)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, password_hash, api_key, plan, usage_limit))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'user_id': user_id,
                'api_key': api_key,
                'plan': plan,
                'usage_limit': usage_limit
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def authenticate_user(self, email, password):
        """Authenticate user login"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, password_hash, api_key, plan, usage_limit, usage_count, is_active
                FROM users WHERE email = ?
            ''', (email,))
            
            user = cursor.fetchone()
            if not user or not user[6]:  # is_active check
                return {'error': 'Invalid credentials'}
            
            if check_password_hash(user[1], password):
                # Update last login
                cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                             (datetime.now(), user[0]))
                conn.commit()
                conn.close()
                
                return {
                    'success': True,
                    'user_id': user[0],
                    'api_key': user[2],
                    'plan': user[3],
                    'usage_limit': user[4],
                    'usage_count': user[5]
                }
            else:
                conn.close()
                return {'error': 'Invalid credentials'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def validate_api_key(self, api_key):
        """Validate API key and check usage limits"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, plan, usage_limit, usage_count, is_active
                FROM users WHERE api_key = ?
            ''', (api_key,))
            
            user = cursor.fetchone()
            if not user or not user[4]:  # is_active check
                return {'valid': False, 'error': 'Invalid API key'}
            
            # Check usage limits
            if user[3] >= user[2]:  # usage_count >= usage_limit
                return {'valid': False, 'error': 'Usage limit exceeded'}
            
            conn.close()
            return {
                'valid': True,
                'user_id': user[0],
                'plan': user[1],
                'remaining_usage': user[2] - user[3]
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def increment_usage(self, user_id, endpoint):
        """Increment user's API usage count"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update usage count
            cursor.execute('UPDATE users SET usage_count = usage_count + 1 WHERE id = ?', (user_id,))
            
            # Log usage
            cursor.execute('INSERT INTO api_usage (user_id, endpoint) VALUES (?, ?)', 
                         (user_id, endpoint))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            return False

# Decorators for authentication
def require_auth(f):
    """Decorator to require session authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def require_api_key(auth_manager):
    """Decorator to require API key authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            validation = auth_manager.validate_api_key(api_key)
            if not validation['valid']:
                return jsonify({'error': validation['error']}), 401
            
            # Increment usage
            auth_manager.increment_usage(validation['user_id'], request.endpoint)
            
            # Add user info to request context
            request.user_info = validation
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(max_requests=60, window=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple in-memory rate limiting (use Redis in production)
            client_id = request.remote_addr
            # Implement rate limiting logic here
            return f(*args, **kwargs)
        return decorated_function
    return decorator