"""
Database models for persistent storage
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    plan = Column(String(50), default='free')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    requests_today = Column(Integer, default=0)
    requests_this_month = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    last_request_date = Column(DateTime)
    
    # Relationships
    datasets = relationship('Dataset', back_populates='user', cascade='all, delete-orphan')
    conversations = relationship('Conversation', back_populates='user', cascade='all, delete-orphan')
    models = relationship('MLModel', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', plan='{self.plan}')>"


class Dataset(Base):
    """Dataset model"""
    __tablename__ = 'datasets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))
    
    # Dataset metadata
    rows = Column(Integer)
    columns = Column(Integer)
    column_names = Column(JSON)
    column_types = Column(JSON)
    memory_usage = Column(Integer)
    
    # Quality metrics
    missing_values = Column(Integer)
    duplicate_rows = Column(Integer)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='datasets')
    conversations = relationship('Conversation', back_populates='dataset')
    
    def __repr__(self):
        return f"<Dataset(id={self.id}, filename='{self.filename}', rows={self.rows})>"


class Conversation(Base):
    """Conversation model"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id'), nullable=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    
    # Message content
    role = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    
    # Context
    function_called = Column(String(100))
    function_result = Column(JSON)
    
    # Metadata
    tokens_used = Column(Integer)
    model_used = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship('User', back_populates='conversations')
    dataset = relationship('Dataset', back_populates='conversations')
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, role='{self.role}', session='{self.session_id}')>"


class MLModel(Base):
    """ML Model model"""
    __tablename__ = 'ml_models'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Model info
    model_name = Column(String(255), nullable=False)
    model_type = Column(String(100), nullable=False)
    model_path = Column(String(500), nullable=False)
    
    # Training info
    target_column = Column(String(255))
    feature_columns = Column(JSON)
    
    # Performance metrics
    metrics = Column(JSON)
    training_time = Column(Float)
    
    # Dataset info
    dataset_name = Column(String(255))
    training_samples = Column(Integer)
    test_samples = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    
    # Relationships
    user = relationship('User', back_populates='models')
    
    def __repr__(self):
        return f"<MLModel(id={self.id}, name='{self.model_name}', type='{self.model_type}')>"


class APILog(Base):
    """API Log model"""
    __tablename__ = 'api_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    
    # Request info
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)
    
    # Performance
    response_time = Column(Float)
    
    # Context
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<APILog(id={self.id}, endpoint='{self.endpoint}', status={self.status_code})>"


class SystemMetrics(Base):
    """System Metrics model"""
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    
    # Metrics
    total_users = Column(Integer, default=0)
    active_users_today = Column(Integer, default=0)
    total_datasets = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)
    total_models_trained = Column(Integer, default=0)
    
    # Resource usage
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    
    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<SystemMetrics(users={self.total_users}, datasets={self.total_datasets})>"


class DatabaseConnection:
    """Manage database connections and sessions"""
    
    def __init__(self, database_url=None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///chatbot.db')
        
        # Fix Heroku Postgres URL
        if self.database_url.startswith('postgres://'):
            self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
        
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(self.engine)
    
    def drop_tables(self):
        """Drop all database tables"""
        Base.metadata.drop_all(self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def test_connection(self):
        """Test database connection"""
        try:
            session = self.get_session()
            session.execute(text("SELECT 1"))
            session.close()
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False


def init_database():
    """Initialize database with tables"""
    db = DatabaseConnection()
    db.create_tables()
    print("Database tables created successfully!")
    return db


def get_db_session():
    """Get database session"""
    db = DatabaseConnection()
    session = db.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def migrate_database():
    """Run database migrations"""
    try:
        db = DatabaseConnection()
        
        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            print("Creating new database...")
            db.create_tables()
            print("Database created!")
        else:
            print(f"Database exists with tables: {existing_tables}")
            Base.metadata.create_all(db.engine)
            print("Database updated!")
        
        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing database setup...")
    db = DatabaseConnection()
    
    if db.test_connection():
        print("Database connection successful!")
        db.create_tables()
        print("All tables created!")
    else:
        print("Database connection failed!")
