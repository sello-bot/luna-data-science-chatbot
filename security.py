# security.py - Security and Input Validation Module
import re
import os
import hashlib
from flask import request, jsonify
from werkzeug.utils import secure_filename
from functools import wraps
import magic as magic

from datetime import datetime, timedelta

class SecurityManager:
    def __init__(self):
        self.allowed_extensions = {'csv', 'json', 'xlsx', 'xls', 'parquet'}
        self.max_file_size = 16 * 1024 * 1024  # 16MB
        self.allowed_mime_types = {
            'text/csv',
            'application/json',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/octet-stream'  # for parquet files
        }
        
        # Rate limiting storage (use Redis in production)
        self.rate_limit_storage = {}
    
    def validate_file_upload(self, file):
        """Comprehensive file upload validation"""
        errors = []
        
        # Check if file exists
        if not file or file.filename == '':
            errors.append("No file provided")
            return {'valid': False, 'errors': errors}
        
        # Secure filename
        filename = secure_filename(file.filename)
        if not filename:
            errors.append("Invalid filename")
            return {'valid': False, 'errors': errors}
        
        # Check file extension
        if not self._allowed_file_extension(filename):
            errors.append(f"File type not allowed. Supported: {', '.join(self.allowed_extensions)}")
        
        # Check file size
        if hasattr(file, 'content_length') and file.content_length > self.max_file_size:
            errors.append(f"File too large. Maximum size: {self.max_file_size / (1024*1024)}MB")
        
        # Validate MIME type
        if hasattr(file, 'content_type'):
            if not self._allowed_mime_type(file.content_type):
                errors.append("File type validation failed")
        
        # Generate secure filename with hash
        secure_name = self._generate_secure_filename(filename)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'secure_filename': secure_name,
            'original_filename': filename
        }
    
    def _allowed_file_extension(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _allowed_mime_type(self, mime_type):
        """Check if MIME type is allowed"""
        return mime_type in self.allowed_mime_types
    
    def _generate_secure_filename(self, filename):
        """Generate secure filename with timestamp and hash"""
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        hash_suffix = hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:8]
        return f"{secure_filename(name)}_{timestamp}_{hash_suffix}{ext}"
    
    def validate_chat_input(self, message):
        """Validate chat message input"""
        if not message or not isinstance(message, str):
            return {'valid': False, 'error': 'Invalid message format'}
        
        # Length check
        if len(message) > 2000:
            return {'valid': False, 'error': 'Message too long (max 2000 characters)'}
        
        # Basic XSS protection
        dangerous_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return {'valid': False, 'error': 'Invalid message content'}
        
        # Sanitize message
        sanitized = self._sanitize_input(message)
        
        return {'valid': True, 'sanitized_message': sanitized}
    
    def _sanitize_input(self, text):
        """Basic input sanitization"""
        # Remove potential HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove potential script injections
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def check_rate_limit(self, client_id, endpoint, max_requests=60, window_minutes=1):
        """Simple rate limiting (use Redis in production)"""
        current_time = datetime.now()
        window_start = current_time - timedelta(minutes=window_minutes)
        
        # Clean old entries
        if client_id in self.rate_limit_storage:
            self.rate_limit_storage[client_id] = [
                req_time for req_time in self.rate_limit_storage[client_id]
                if req_time > window_start
            ]
        else:
            self.rate_limit_storage[client_id] = []
        
        # Check current count
        current_requests = len(self.rate_limit_storage[client_id])
        
        if current_requests >= max_requests:
            return {
                'allowed': False,
                'error': f'Rate limit exceeded. Max {max_requests} requests per {window_minutes} minute(s)'
            }
        
        # Add current request
        self.rate_limit_storage[client_id].append(current_time)
        
        return {
            'allowed': True,
            'remaining': max_requests - current_requests - 1
        }
    
    def validate_api_parameters(self, params, required_fields, allowed_fields):
        """Validate API parameters"""
        errors = []
        
        # Check required fields
        for field in required_fields:
            if field not in params:
                errors.append(f"Missing required field: {field}")
        
        # Check for unexpected fields
        for field in params:
            if field not in allowed_fields:
                errors.append(f"Unexpected field: {field}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

# Security decorators
def require_rate_limit(security_manager, max_requests=60, window_minutes=1):
    """Decorator for rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_id = request.remote_addr
            endpoint = request.endpoint
            
            rate_check = security_manager.check_rate_limit(
                client_id, endpoint, max_requests, window_minutes
            )
            
            if not rate_check['allowed']:
                return jsonify({'error': rate_check['error']}), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_json_input(required_fields=None, allowed_fields=None):
    """Decorator to validate JSON input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid JSON data'}), 400
            
            if required_fields or allowed_fields:
                security_manager = SecurityManager()
                validation = security_manager.validate_api_parameters(
                    data, required_fields or [], allowed_fields or list(data.keys())
                )
                
                if not validation['valid']:
                    return jsonify({'error': 'Validation failed', 'details': validation['errors']}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def secure_headers(f):
    """Add security headers to response"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Add security headers
        if hasattr(response, 'headers'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
        
        return response
    return decorated_function