"""
Security middleware - Fixed for Heroku (no python-magic dependency)
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
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    def validate_file_upload(self, file):
        """Validate uploaded file without python-magic"""
        errors = []
        
        # Check if file exists
        if not file or not file.filename:
            errors.append("No file provided")
            return {"valid": False, "errors": errors}
        
        # Secure the filename
        original_filename = file.filename
        secure_name = werkzeug_secure_filename(original_filename)
        
        if not secure_name:
            errors.append("Invalid filename")
            return {"valid": False, "errors": errors}
        
        # Check file extension
        file_ext = os.path.splitext(secure_name)[1].lower()
        if file_ext not in self.allowed_extensions:
            errors.append(f"File type {file_ext} not allowed. Allowed: {', '.join(self.allowed_extensions)}")
        
        # Check file size (if possible)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > self.max_file_size:
            errors.append(f"File too large. Maximum size: {self.max_file_size / 1024 / 1024}MB")
        
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
        
        # Check length
        if len(message) > 10000:
            return {
                "valid": False,
                "error": "Message too long (max 10000 characters)",
                "sanitized_message": ""
            }
        
        # Basic sanitization
        sanitized = message.strip()
        
        # Check for potential injection attacks (basic)
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
                    "error": "Message contains potentially dangerous content",
                    "sanitized_message": ""
                }
        
        return {
            "valid": True,
            "sanitized_message": sanitized,
            "error": None
        }
    
    def check_rate_limit(self, identifier, max_requests=100, window_seconds=60):
        """Simple in-memory rate limiting"""
        import time
        
        current_time = time.time()
        
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []
        
        # Remove old requests outside the window
        self.rate_limits[identifier] = [
            req_time for req_time in self.rate_limits[identifier]
            if current_time - req_time < window_seconds
        ]
        
        # Check if limit exceeded
        if len(self.rate_limits[identifier]) >= max_requests:
            return {
                "allowed": False,
                "retry_after": window_seconds
            }
        
        # Add current request
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
            # Get identifier (IP address or user ID)
            identifier = request.remote_addr
            if hasattr(request, 'user_info') and request.user_info:
                identifier = f"user_{request.user_info.get('user_id')}"
            
            # Check rate limit
            result = security_manager.check_rate_limit(
                identifier,
                max_requests=max_requests,
                window_seconds=window_minutes * 60
            )
            
            if not result["allowed"]:
                return jsonify({
                    "error": "Rate limit exceeded. Please try again later.",
                    "retry_after": result["retry_after"]
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_json_input(required_fields=None):
    """Validate JSON input decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid JSON"}), 400
            
            # Check required fields
            if required_fields:
                missing = [field for field in required_fields if field not in data]
                if missing:
                    return jsonify({
                        "error": f"Missing required fields: {', '.join(missing)}"
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def secure_headers(f):
    """Add security headers to response"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # If response is a tuple (response, status_code)
        if isinstance(response, tuple):
            resp, status_code = response[0], response[1]
        else:
            resp = response
            status_code = 200
        
        # Add security headers
        if hasattr(resp, 'headers'):
            resp.headers['X-Content-Type-Options'] = 'nosniff'
            resp.headers['X-Frame-Options'] = 'DENY'
            resp.headers['X-XSS-Protection'] = '1; mode=block'
            resp.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        if isinstance(response, tuple):
            return resp, status_code
        return resp
    
    return decorated_function


def sanitize_filename(filename):
    """Sanitize filename to prevent directory traversal"""
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


def validate_api_key_format(api_key):
    """Validate API key format"""
    if not api_key:
        return False
    
    # Check format: ds_xxxxx (data science prefix)
    if not api_key.startswith('ds_'):
        return False
    
    # Check length (should be reasonable)
    if len(api_key) < 20 or len(api_key) > 100:
        return False
    
    # Check for valid characters (alphanumeric + underscore + hyphen)
    if not re.match(r'^ds_[A-Za-z0-9_\-]+$', api_key):
        return False
    
    return True