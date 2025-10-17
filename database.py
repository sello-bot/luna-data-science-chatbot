"""
Enhanced Database Manager with full CRUD operations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from models import (
    DatabaseConnection, User, Dataset, Conversation, 
    MLModel, APILog, SystemMetrics
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Enhanced database manager with all operations"""
    
    def __init__(self):
        self.db = DatabaseConnection()
        self.db.create_tables()
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.db.get_session()
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, email: str, password_hash: str, api_key: str, plan: str = 'free') -> Dict[str, Any]:
        """Create new user"""
        session = self.get_session()
        try:
            user = User(
                email=email,
                password_hash=password_hash,
                api_key=api_key,
                plan=plan,
                created_at=datetime.utcnow()
            )
            session.add(user)
            session.commit()
            
            return {
                "success": True,
                "user_id": user.id,
                "email": user.email,
                "api_key": user.api_key,
                "plan": user.plan
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
            return user
        finally:
            session.close()
    
    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.api_key == api_key).first()
            return user
        finally:
            session.close()
    
    def update_user_login(self, user_id: int):
        """Update user's last login time"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating user login: {str(e)}")
        finally:
            session.close()
    
    def increment_user_usage(self, user_id: int):
        """Increment user's request counters"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                now = datetime.utcnow()
                
                # Reset daily counter if new day
                if user.last_request_date and user.last_request_date.date() < now.date():
                    user.requests_today = 0
                
                user.requests_today += 1
                user.requests_this_month += 1
                user.total_requests += 1
                user.last_request_date = now
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error incrementing usage: {str(e)}")
        finally:
            session.close()
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            
            datasets_count = session.query(Dataset).filter(Dataset.user_id == user_id).count()
            conversations_count = session.query(Conversation).filter(Conversation.user_id == user_id).count()
            models_count = session.query(MLModel).filter(MLModel.user_id == user_id).count()
            
            return {
                "user_id": user.id,
                "email": user.email,
                "plan": user.plan,
                "requests_today": user.requests_today,
                "requests_this_month": user.requests_this_month,
                "total_requests": user.total_requests,
                "datasets": datasets_count,
                "conversations": conversations_count,
                "models_trained": models_count,
                "member_since": user.created_at.isoformat() if user.created_at else None
            }
        finally:
            session.close()
    
    # ==================== DATASET OPERATIONS ====================
    
    def save_dataset(self, user_id: int, filename: str, original_filename: str, 
                     filepath: str, file_size: int, file_type: str, 
                     data_info: Dict[str, Any]) -> Dict[str, Any]:
        """Save dataset metadata"""
        session = self.get_session()
        try:
            dataset = Dataset(
                user_id=user_id,
                filename=filename,
                original_filename=original_filename,
                filepath=filepath,
                file_size=file_size,
                file_type=file_type,
                rows=data_info.get('shape', [0, 0])[0],
                columns=data_info.get('shape', [0, 0])[1],
                column_names=data_info.get('columns', []),
                column_types=data_info.get('dtypes', {}),
                memory_usage=data_info.get('memory_usage', 0),
                missing_values=data_info.get('missing_values', 0),
                uploaded_at=datetime.utcnow()
            )
            session.add(dataset)
            session.commit()
            
            return {
                "success": True,
                "dataset_id": dataset.id,
                "message": "Dataset saved successfully"
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving dataset: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()
    
    def get_user_datasets(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's datasets"""
        session = self.get_session()
        try:
            datasets = session.query(Dataset)\
                .filter(Dataset.user_id == user_id)\
                .order_by(Dataset.uploaded_at.desc())\
                .limit(limit)\
                .all()
            
            return [{
                "id": ds.id,
                "filename": ds.original_filename,
                "file_type": ds.file_type,
                "rows": ds.rows,
                "columns": ds.columns,
                "file_size": ds.file_size,
                "uploaded_at": ds.uploaded_at.isoformat() if ds.uploaded_at else None,
                "last_accessed": ds.last_accessed.isoformat() if ds.last_accessed else None
            } for ds in datasets]
        finally:
            session.close()
    
    def get_dataset(self, dataset_id: int) -> Optional[Dataset]:
        """Get dataset by ID"""
        session = self.get_session()
        try:
            dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()
            if dataset:
                dataset.last_accessed = datetime.utcnow()
                session.commit()
            return dataset
        finally:
            session.close()
    
    def delete_dataset(self, dataset_id: int, user_id: int) -> Dict[str, Any]:
        """Delete dataset"""
        session = self.get_session()
        try:
            dataset = session.query(Dataset)\
                .filter(and_(Dataset.id == dataset_id, Dataset.user_id == user_id))\
                .first()
            
            if not dataset:
                return {"success": False, "error": "Dataset not found"}
            
            session.delete(dataset)
            session.commit()
            return {"success": True, "message": "Dataset deleted"}
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting dataset: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()
    
    # ==================== CONVERSATION OPERATIONS ====================
    
    def save_conversation(self, user_id: int, session_id: str, role: str, 
                         message: str, dataset_id: Optional[int] = None,
                         function_called: Optional[str] = None,
                         function_result: Optional[Dict] = None) -> Dict[str, Any]:
        """Save conversation message"""
        session = self.get_session()
        try:
            conversation = Conversation(
                user_id=user_id,
                dataset_id=dataset_id,
                session_id=session_id,
                role=role,
                message=message,
                function_called=function_called,
                function_result=function_result,
                created_at=datetime.utcnow()
            )
            session.add(conversation)
            session.commit()
            
            return {"success": True, "conversation_id": conversation.id}
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving conversation: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()
    
    def get_conversation_history(self, user_id: int, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        session = self.get_session()
        try:
            conversations = session.query(Conversation)\
                .filter(and_(Conversation.user_id == user_id, Conversation.session_id == session_id))\
                .order_by(Conversation.created_at.asc())\
                .limit(limit)\
                .all()
            
            return [{
                "role": conv.role,
                "message": conv.message,
                "function_called": conv.function_called,
                "created_at": conv.created_at.isoformat() if conv.created_at else None
            } for conv in conversations]
        finally:
            session.close()
    
    def get_all_user_conversations(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all conversations for user (grouped by session)"""
        session = self.get_session()
        try:
            # Get unique sessions with their latest message
            sessions = session.query(
                Conversation.session_id,
                func.max(Conversation.created_at).label('last_message'),
                func.count(Conversation.id).label('message_count')
            ).filter(Conversation.user_id == user_id)\
             .group_by(Conversation.session_id)\
             .order_by(func.max(Conversation.created_at).desc())\
             .limit(limit)\
             .all()
            
            return [{
                "session_id": s.session_id,
                "last_message": s.last_message.isoformat() if s.last_message else None,
                "message_count": s.message_count
            } for s in sessions]
        finally:
            session.close()
    
    def cleanup_old_conversations(self, days: int = 30):
        """Delete conversations older than specified days"""
        session = self.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted = session.query(Conversation)\
                .filter(Conversation.created_at < cutoff_date)\
                .delete()
            session.commit()
            logger.info(f"Deleted {deleted} old conversations")
            return {"success": True, "deleted": deleted}
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning conversations: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()
    
    # ==================== ML MODEL OPERATIONS ====================
    
    def save_ml_model(self, user_id: int, model_name: str, model_type: str,
                      model_path: str, target_column: str, feature_columns: List[str],
                      metrics: Dict[str, Any], training_samples: int,
                      test_samples: int, dataset_name: str) -> Dict[str, Any]:
        """Save ML model metadata"""
        session = self.get_session()
        try:
            ml_model = MLModel(
                user_id=user_id,
                model_name=model_name,
                model_type=model_type,
                model_path=model_path,
                target_column=target_column,
                feature_columns=feature_columns,
                metrics=metrics,
                training_samples=training_samples,
                test_samples=test_samples,
                dataset_name=dataset_name,
                created_at=datetime.utcnow()
            )
            session.add(ml_model)
            session.commit()
            
            return {"success": True, "model_id": ml_model.id}
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving ML model: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()
    
    def get_user_models(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's trained models"""
        session = self.get_session()
        try:
            models = session.query(MLModel)\
                .filter(MLModel.user_id == user_id)\
                .order_by(MLModel.created_at.desc())\
                .all()
            
            return [{
                "id": m.id,
                "model_name": m.model_name,
                "model_type": m.model_type,
                "metrics": m.metrics,
                "created_at": m.created_at.isoformat() if m.created_at else None
            } for m in models]
        finally:
            session.close()
    
    # ==================== API LOGGING ====================
    
    def log_api_request(self, user_id: Optional[int], endpoint: str, method: str,
                       status_code: int, response_time: float, ip_address: str,
                       user_agent: str) -> Dict[str, Any]:
        """Log API request"""
        session = self.get_session()
        try:
            log = APILog(
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time=response_time,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.utcnow()
            )
            session.add(log)
            session.commit()
            return {"success": True}
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging API request: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()
    
    # ==================== SYSTEM METRICS ====================
    
    def record_system_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Record system metrics"""
        session = self.get_session()
        try:
            system_metrics = SystemMetrics(**metrics, recorded_at=datetime.utcnow())
            session.add(system_metrics)
            session.commit()
            return {"success": True}
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording metrics: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        session = self.get_session()
        try:
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count()
            total_datasets = session.query(Dataset).count()
            total_conversations = session.query(Conversation).count()
            total_models = session.query(MLModel).count()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_datasets": total_datasets,
                "total_conversations": total_conversations,
                "total_models_trained": total_models
            }
        finally:
            session.close()

