"""
Security middleware - No external dependencies
"""

import os
import re
from functools import wraps
from flask import request, jsonify
from werkzeug.utils import secure_filename as werkzeug_secure_filename
import logging

logger = logging.getLogger(__name__)


class SecurityManager:
    """Manage security operations"""
    
    def __init__(self):
        self.rate_limits = {}
        self.allowed_extensions = {'.csv', '.json', '.xlsx', '.xls', '.parquet'}
        self.max_file_size = 50 * 1024 * 1024
    
    def validate_file_upload(self, file):
        """Validate uploaded file"""
        errors = []
        
        if not file or not file.filename:
            errors.append("No file provided")
            return {"valid": False, "errors": errors}
        
        original_filename = file.filename
        secure_name = werkzeug_secure_filename(original_filename)
        
        if not secure_name:
            errors.append("Invalid filename")
            return {"valid": False, "errors": errors}
        
        file_ext = os.path.splitext(secure_name)[1].lower()
        if file_ext not in self.allowed_extensions:
            errors.append(f"File type {file_ext} not allowed")
        
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > self.max_file_size:
            errors.append(f"File too large")
        
        if file_size == 0:
            errors.append("File is empty")
        
        if errors:
            return {"valid": False, "errors": errors}
        
        return {
            "valid": True,
            "secure_filename": secure_name,
            "original_filename": original_filename,
            "file_size": file_size,
            "errors": []
        }
    
    def validate_chat_input(self, message):
        """Validate chat input"""
        if not message or not message.strip():
            return {
                "valid": False,
                "error": "Message cannot be empty",
                "sanitized_message": ""
            }
        
        if len(message) > 10000:
            return {
                "valid": False,
                "error": "Message too long",
                "sanitized_message": ""
            }
        
        sanitized = message.strip()
        
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'onerror\s*=',
            r'onclick\s*='
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                return {
                    "valid": False,
                    "error": "Message contains dangerous content",
                    "sanitized_message": ""
                }
        
        return {
            "valid": True,
            "sanitized_message": sanitized,
            "error": None
        }
    
    def check_rate_limit(self, identifier, max_requests=100, window_seconds=60):
        """Rate limiting"""
        import time
        
        current_time = time.time()
        
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []
        
        self.rate_limits[identifier] = [
            req_time for req_time in self.rate_limits[identifier]
            if current_time - req_time < window_seconds
        ]
        
        if len(self.rate_limits[identifier]) >= max_requests:
            return {"allowed": False, "retry_after": window_seconds}
        
        self.rate_limits[identifier].append(current_time)
        
        return {
            "allowed": True,
            "remaining": max_requests - len(self.rate_limits[identifier])
        }


def require_rate_limit(security_manager, max_requests=100, window_minutes=1):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = request.remote_addr
            if hasattr(request, 'user_info') and request.user_info:
                identifier = f"user_{request.user_info.get('user_id')}"
            
            result = security_manager.check_rate_limit(
                identifier,
                max_requests=max_requests,
                window_seconds=window_minutes * 60
            )
            
            if not result["allowed"]:
                return jsonify({
                    "error": "Rate limit exceeded",
                    "retry_after": result["retry_after"]
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_json_input(required_fields=None):
    """Validate JSON input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Must be JSON"}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid JSON"}), 400
            
            if required_fields:
                missing = [field for field in required_fields if field not in data]
                if missing:
                    return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def secure_headers(f):
    """Add security headers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        if isinstance(response, tuple):
            resp, status_code = response[0], response[1]
        else:
            resp = response
            status_code = 200
        
        if hasattr(resp, 'headers'):
            resp.headers['X-Content-Type-Options'] = 'nosniff'
            resp.headers['X-Frame-Options'] = 'DENY'
            resp.headers['X-XSS-Protection'] = '1; mode=block'
        
        if isinstance(response, tuple):
            return resp, status_code
        return resp
    
    return decorated_function