# database.py - Database and Data Persistence Manager
import sqlite3
import json
import pickle
from typing import Dict, List, Any
from datetime import datetime, timedelta


class DatabaseManager:
    def __init__(self, db_path='data_science_bot.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize all database tables"""
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

        # API usage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                endpoint TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Conversations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                message_content TEXT NOT NULL,
                response_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Datasets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                dataset_info TEXT,
                upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Models
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trained_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                model_type TEXT,
                dataset_id INTEGER,
                model_data BLOB,
                model_metrics TEXT,
                feature_names TEXT,
                target_column TEXT,
                training_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (dataset_id) REFERENCES datasets (id)
            )
        ''')

        # Visualizations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visualizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                dataset_id INTEGER,
                viz_type TEXT,
                file_path TEXT,
                viz_config TEXT,
                creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (dataset_id) REFERENCES datasets (id)
            )
        ''')

        # Sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT UNIQUE NOT NULL,
                session_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        conn.commit()
        conn.close()

    # ------------------------
    # Cleanup Helpers
    # ------------------------

    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """
        Remove sessions older than X days.
        Returns the number of deleted sessions.
        """
        cutoff = datetime.now() - timedelta(days=days_old)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM user_sessions WHERE last_activity < ?",
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def cleanup_old_conversations(self, days_old: int = 30) -> int:
        """
        Remove conversations older than X days.
        Returns the number of deleted conversations.
        """
        cutoff = datetime.now() - timedelta(days=days_old)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM conversations WHERE timestamp < ?",
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

