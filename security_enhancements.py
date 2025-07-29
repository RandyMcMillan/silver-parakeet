"""
Security enhancements for the route optimization application
Implements input validation, rate limiting, and security headers
"""

import re
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import request, abort, g
from typing import Dict, Any

class SecurityValidator:
    """Input validation and sanitization utilities"""
    
    # Validation patterns
    PATTERNS = {
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'phone': re.compile(r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'),
        'zip_code': re.compile(r'^\d{5}(-\d{4})?$'),
        'state': re.compile(r'^[A-Z]{2}$'),
        'address': re.compile(r'^[a-zA-Z0-9\s,.-]+$'),
        'name': re.compile(r'^[a-zA-Z\s\-\']{2,50}$'),
        'service_type': re.compile(r'^(install|pickup|remove|deliver)$'),
        'post_type': re.compile(r'^[a-zA-Z0-9\s-]{2,100}$')
    }
    
    # Dangerous patterns to reject
    DANGEROUS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
        re.compile(r'<iframe[^>]*>.*?</iframe>', re.IGNORECASE | re.DOTALL),
        re.compile(r'<object[^>]*>.*?</object>', re.IGNORECASE | re.DOTALL),
        re.compile(r'<embed[^>]*>.*?</embed>', re.IGNORECASE | re.DOTALL),
        re.compile(r'<link[^>]*>.*?</link>', re.IGNORECASE | re.DOTALL),
        re.compile(r'<meta[^>]*>.*?</meta>', re.IGNORECASE | re.DOTALL),
        re.compile(r'<style[^>]*>.*?</style>', re.IGNORECASE | re.DOTALL),
        re.compile(r'expression\s*\(', re.IGNORECASE),
        re.compile(r'url\s*\(', re.IGNORECASE),
        re.compile(r'@import', re.IGNORECASE),
        re.compile(r'<!--.*?-->', re.DOTALL)
    ]
    
    @classmethod
    def validate_field(cls, value: str, field_type: str) -> tuple[bool, str]:
        """
        Validate a field against patterns and security rules
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not value or not isinstance(value, str):
            return False, f"{field_type} is required"
        
        # Check for dangerous patterns first
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern.search(value):
                logging.warning(f"Dangerous pattern detected in {field_type}: {value[:50]}...")
                return False, f"{field_type} contains invalid characters"
        
        # Check against specific pattern if available
        if field_type in cls.PATTERNS:
            pattern = cls.PATTERNS[field_type]
            if not pattern.match(value.strip()):
                return False, f"{field_type} format is invalid"
        
        # Length checks
        max_lengths = {
            'address': 500,
            'post_type': 100,
            'agent_sign_description': 1000,
            'riders_toppers_description': 500,
            'deliver_notes': 500,
            'post_type_notes': 200
        }
        
        if field_type in max_lengths and len(value) > max_lengths[field_type]:
            return False, f"{field_type} is too long (max {max_lengths[field_type]} characters)"
        
        return True, ""
    
    @classmethod
    def sanitize_input(cls, value: str) -> str:
        """
        Sanitize input by removing dangerous characters
        """
        if not value:
            return value
        
        # Remove dangerous patterns
        sanitized = value
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = pattern.sub('', sanitized)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    @classmethod
    def validate_form_data(cls, form_data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate entire form data
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields validation
        required_fields = {
            'street_address': 'address',
            'city': 'name',
            'state': 'state',
            'zip_code': 'zip_code',
            'service_type': 'service_type'
        }
        
        for field_name, field_type in required_fields.items():
            value = form_data.get(field_name, '').strip()
            is_valid, error = cls.validate_field(value, field_type)
            if not is_valid:
                errors.append(error)
        
        # Service-specific validation
        service_type = form_data.get('service_type', '')
        if service_type == 'install':
            post_type = form_data.get('post_type', '').strip()
            if not post_type:
                errors.append('Post type is required for installations')
            else:
                is_valid, error = cls.validate_field(post_type, 'post_type')
                if not is_valid:
                    errors.append(error)
        
        elif service_type == 'deliver':
            deliver_notes = form_data.get('deliver_notes', '').strip()
            if not deliver_notes:
                errors.append('Delivery notes are required')
        
        # Date validation for scheduled stops
        if not form_data.get('is_asap'):
            required_date = form_data.get('required_date')
            if required_date:
                try:
                    date_obj = datetime.strptime(required_date, '%Y-%m-%d')
                    if date_obj.date() < datetime.now().date():
                        errors.append('Required date must be in the future')
                except ValueError:
                    errors.append('Invalid date format')
        
        return len(errors) == 0, errors

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
        self.limits = {
            'add_stop': {'count': 10, 'window': 300},      # 10 requests per 5 minutes
            'generate_routes': {'count': 5, 'window': 600}, # 5 requests per 10 minutes
            'default': {'count': 60, 'window': 300}         # 60 requests per 5 minutes
        }
    
    def is_allowed(self, client_id: str, endpoint: str = 'default') -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        limit_config = self.limits.get(endpoint, self.limits['default'])
        
        # Clean old entries
        self._cleanup_old_entries(now, limit_config['window'])
        
        # Check current requests for this client
        client_requests = self.requests.get(client_id, [])
        recent_requests = [req_time for req_time in client_requests 
                          if (now - req_time).seconds < limit_config['window']]
        
        if len(recent_requests) >= limit_config['count']:
            return False
        
        # Add current request
        recent_requests.append(now)
        self.requests[client_id] = recent_requests
        
        return True
    
    def _cleanup_old_entries(self, now: datetime, window: int):
        """Remove old entries to prevent memory leaks"""
        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if (now - req_time).seconds < window
            ]
            if not self.requests[client_id]:
                del self.requests[client_id]

# Global rate limiter instance
rate_limiter = RateLimiter()

def require_rate_limit(endpoint: str = 'default'):
    """Decorator to apply rate limiting to routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_id = request.remote_addr or 'unknown'
            
            if not rate_limiter.is_allowed(client_id, endpoint):
                logging.warning(f"Rate limit exceeded for {client_id} on endpoint {endpoint}")
                abort(429)  # Too Many Requests
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://cdn.replit.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://cdn.replit.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
        "connect-src 'self' https:; "
        "frame-ancestors 'none';"
    )
    return response

def validate_csrf_token():
    """Simple CSRF protection"""
    if request.method == 'POST':
        token = request.form.get('csrf_token')
        expected_token = g.get('csrf_token')
        
        if not token or not expected_token or token != expected_token:
            logging.warning(f"CSRF token mismatch from {request.remote_addr}")
            abort(403)  # Forbidden

# Usage example for routes:
"""
from security_enhancements import SecurityValidator, require_rate_limit, add_security_headers

@main.route('/add_stop', methods=['POST'])
@require_rate_limit('add_stop')
def add_stop():
    # Validate form data
    is_valid, errors = SecurityValidator.validate_form_data(request.form)
    if not is_valid:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('main.index'))
    
    # Sanitize inputs
    street_address = SecurityValidator.sanitize_input(request.form.get('street_address', ''))
    # ... rest of the route logic
"""