# database.py - Database and Data Persistence Manager
import sqlite3
import json
import pickle
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

class DatabaseManager:
    def __init__(self, db_path='data_science_bot.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize all database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Chat conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                message_type TEXT NOT NULL,  -- 'user' or 'bot'
                message_content TEXT NOT NULL,
                response_data TEXT,  -- JSON string of response data
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Uploaded datasets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                dataset_info TEXT,  -- JSON string with dataset metadata
                upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Trained models table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trained_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                model_type TEXT,  -- 'classification', 'regression', etc.
                dataset_id INTEGER,
                model_data BLOB,  -- Pickled model object
                model_metrics TEXT,  -- JSON string with performance metrics
                feature_names TEXT,  -- JSON string with feature names
                target_column TEXT,
                training_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (dataset_id) REFERENCES datasets (id)
            )
        ''')
        
        # Generated visualizations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visualizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                dataset_id INTEGER,
                viz_type TEXT,  -- 'histogram', 'scatter', 'correlation', etc.
                file_path TEXT,
                viz_config TEXT,  -- JSON string with visualization parameters
                creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (dataset_id) REFERENCES datasets (id)
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT UNIQUE NOT NULL,
                session_data TEXT,  -- JSON string with session state
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # Chat conversation management
    def save_conversation_message(self, user_id: int, session_id: str, 
                                message_type: str, message_content: str, 
                                response_data: Dict = None):
        """Save a conversation message to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            response_json = json.dumps(response_data) if response_data else None
            
            cursor.execute('''
                INSERT INTO conversations 
                (user_id, session_id, message_type, message_content, response_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_id, message_type, message_content, response_json))
            
            conn.commit()
            message_id = cursor.lastrowid
            conn.close()
            
            return {'success': True, 'message_id': message_id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_conversation_history(self, user_id: int, session_id: str, 
                               limit: int = 50) -> List[Dict]:
        """Retrieve conversation history for a user session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT message_type, message_content, response_data, timestamp
                FROM conversations 
                WHERE user_id = ? AND session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, session_id, limit))
            
            messages = []
            for row in cursor.fetchall():
                response_data = json.loads(row[2]) if row[2] else None
                messages.append({
                    'message_type': row[0],
                    'message_content': row[1],
                    'response_data': response_data,
                    'timestamp': row[3]
                })
            
            conn.close()
            return messages[::-1]  # Return in chronological order
            
        except Exception as e:
            return []
    
    # Dataset management
    def save_dataset(self, user_id: int, filename: str, original_filename: str,
                    file_path: str, file_size: int, file_type: str,
                    dataset_info: Dict) -> Dict:
        """Save dataset metadata to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            info_json = json.dumps(dataset_info)
            
            cursor.execute('''
                INSERT INTO datasets 
                (user_id, filename, original_filename, file_path, file_size, 
                 file_type, dataset_info)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, filename, original_filename, file_path, 
                  file_size, file_type, info_json))
            
            dataset_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {'success': True, 'dataset_id': dataset_id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_datasets(self, user_id: int, active_only: bool = True) -> List[Dict]:
        """Get all datasets for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT id, filename, original_filename, file_size, file_type,
                       dataset_info, upload_timestamp, last_accessed
                FROM datasets 
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if active_only:
                query += ' AND is_active = 1'
            
            query += ' ORDER BY upload_timestamp DESC'
            
            cursor.execute(query, params)
            
            datasets = []
            for row in cursor.fetchall():
                dataset_info = json.loads(row[5]) if row[5] else {}
                datasets.append({
                    'id': row[0],
                    'filename': row[1],
                    'original_filename': row[2],
                    'file_size': row[3],
                    'file_type': row[4],
                    'dataset_info': dataset_info,
                    'upload_timestamp': row[6],
                    'last_accessed': row[7]
                })
            
            conn.close()
            return datasets
            
        except Exception as e:
            return []
    
    def update_dataset_access(self, dataset_id: int):
        """Update last accessed timestamp for a dataset"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE datasets 
                SET last_accessed = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (dataset_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            pass
    
    # Model management
    def save_trained_model(self, user_id: int, model_name: str, model_type: str,
                          dataset_id: int, model_object: Any, model_metrics: Dict,
                          feature_names: List[str], target_column: str) -> Dict:
        """Save a trained model to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Serialize model object
            model_blob = pickle.dumps(model_object)
            metrics_json = json.dumps(model_metrics)
            features_json = json.dumps(feature_names)
            
            cursor.execute('''
                INSERT INTO trained_models 
                (user_id, model_name, model_type, dataset_id, model_data, 
                 model_metrics, feature_names, target_column)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, model_name, model_type, dataset_id, model_blob,
                  metrics_json, features_json, target_column))
            
            model_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {'success': True, 'model_id': model_id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_models(self, user_id: int, active_only: bool = True) -> List[Dict]:
        """Get all trained models for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT id, model_name, model_type, dataset_id, model_metrics,
                       feature_names, target_column, training_timestamp
                FROM trained_models 
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if active_only:
                query += ' AND is_active = 1'
            
            query += ' ORDER BY training_timestamp DESC'
            
            cursor.execute(query, params)
            
            models = []
            for row in cursor.fetchall():
                metrics = json.loads(row[4]) if row[4] else {}
                features = json.loads(row[5]) if row[5] else []
                
                models.append({
                    'id': row[0],
                    'model_name': row[1],
                    'model_type': row[2],
                    'dataset_id': row[3],
                    'model_metrics': metrics,
                    'feature_names': features,
                    'target_column': row[6],
                    'training_timestamp': row[7]
                })
            
            conn.close()
            return models
            
        except Exception as e:
            return []
    
    def load_trained_model(self, model_id: int, user_id: int) -> Dict:
        """Load a trained model from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT model_data, model_name, model_type, model_metrics,
                       feature_names, target_column
                FROM trained_models 
                WHERE id = ? AND user_id = ? AND is_active = 1
            ''', (model_id, user_id))
            
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': 'Model not found'}
            
            # Deserialize model
            model_object = pickle.loads(row[0])
            metrics = json.loads(row[3]) if row[3] else {}
            features = json.loads(row[4]) if row[4] else []
            
            conn.close()
            
            return {
                'success': True,
                'model': model_object,
                'model_name': row[1],
                'model_type': row[2],
                'model_metrics': metrics,
                'feature_names': features,
                'target_column': row[5]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Visualization management
    def save_visualization(self, user_id: int, dataset_id: int, viz_type: str,
                          file_path: str, viz_config: Dict) -> Dict:
        """Save visualization metadata"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            config_json = json.dumps(viz_config) if viz_config else None
            
            cursor.execute('''
                INSERT INTO visualizations 
                (user_id, dataset_id, viz_type, file_path, viz_config)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, dataset_id, viz_type, file_path, config_json))
            
            viz_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {'success': True, 'visualization_id': viz_id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_visualizations(self, user_id: int, dataset_id: int = None) -> List[Dict]:
        """Get visualizations for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT id, dataset_id, viz_type, file_path, viz_config, creation_timestamp
                FROM visualizations 
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if dataset_id:
                query += ' AND dataset_id = ?'
                params.append(dataset_id)
            
            query += ' ORDER BY creation_timestamp DESC'
            
            cursor.execute(query, params)
            
            visualizations = []
            for row in cursor.fetchall():
                viz_config = json.loads(row[4]) if row[4] else {}
                visualizations.append({
                    'id': row[0],
                    'dataset_id': row[1],
                    'viz_type': row[2],
                    'file_path': row[3],
                    'viz_config': viz_config,
                    'creation_timestamp': row[5]
                })
            
            conn.close()
            return visualizations
            
        except Exception as e:
            return []
    
    # Session management
    def create_session(self, user_id: int, session_id: str, initial_data: Dict = None):
        """Create a new user session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            session_data = json.dumps(initial_data) if initial_data else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_sessions 
                (user_id, session_id, session_data, last_activity)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, session_id, session_data))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            return False
    
    def update_session(self, session_id: str, session_data: Dict):
        """Update session data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            data_json = json.dumps(session_data)
            
            cursor.execute('''
                UPDATE user_sessions 
                SET session_data = ?, last_activity = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (data_json, session_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            return False
    
    def get_session_data(self, session_id: str) -> Dict:
        """Get session data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, session_data, last_activity
                FROM user_sessions 
                WHERE session_id = ? AND is_active = 1
            ''', (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return {}
            
            session_data = json.loads(row[1]) if row[1] else {}
            conn.close()
            
            return {
                'user_id': row[0],
                'session_data': session_data,
                'last_activity': row[2]
            }
            
        except Exception as e:
            return {}
    
    # Cleanup methods
    def cleanup_old_sessions(self, days_old: int = 7):
        """Remove inactive sessions older than specified days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_sessions 
                SET is_active = 0 
                WHERE datetime(last_activity) < datetime('now', '-{} days')
            '''.format(days_old))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            return False
    
    def cleanup_old_conversations(self, days_old: int = 30):
        """Archive old conversations"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Could move to archive table instead of deleting
            cursor.execute('''
                DELETE FROM conversations 
                WHERE datetime(timestamp) < datetime('now', '-{} days')
            '''.format(days_old))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            return False