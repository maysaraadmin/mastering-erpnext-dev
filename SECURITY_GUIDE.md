# 🔒 Comprehensive Security Guide for ERPNext Development

## 📋 Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication & Authorization](#authentication-authorization)
3. [Data Protection](#data-protection)
4. [API Security](#api-security)
5. [Database Security](#database-security)
6. [Application Security](#application-security)
7. [Security Testing](#security-testing)
8. [Security Checklist](#security-checklist)

---

## 🛡️ Security Overview

ERPNext applications handle sensitive business data and require comprehensive security measures. This guide provides best practices for securing your Frappe applications.

### Core Security Principles

1. **Principle of Least Privilege** - Users should only have access to what they need
2. **Defense in Depth** - Multiple layers of security controls
3. **Secure by Default** - Secure configurations out of the box
4. **Zero Trust** - Verify everything, trust nothing

---

## 🔐 Authentication & Authorization

### User Authentication

```python
# Secure authentication implementation
import frappe
import secrets
from frappe.auth import LoginManager

class SecureAuthentication:
    """Enhanced authentication with security best practices"""
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> dict:
        """Secure user authentication with rate limiting"""
        try:
            # Rate limiting check
            client_ip = frappe.local.request_ip
            if SecureAuthentication._is_rate_limited(client_ip):
                frappe.throw("Too many login attempts", frappe.PermissionError)
            
            # Validate credentials
            login_manager = LoginManager()
            result = login_manager.authenticate(username, password)
            
            if result.success:
                # Log successful login
                frappe.logger().info(f"User {username} authenticated successfully")
                return {
                    "success": True,
                    "user": result.user,
                    "sid": result.sid
                }
            else:
                # Log failed attempt
                frappe.log_error(f"Failed login attempt for {username}")
                SecureAuthentication._record_failed_attempt(client_ip)
                return {"success": False}
                
        except Exception as e:
            frappe.log_error(f"Authentication error: {str(e)}")
            return {"success": False}
    
    @staticmethod
    def _is_rate_limited(client_ip: str) -> bool:
        """Check if client is rate limited"""
        cache_key = f"login_attempts:{client_ip}"
        attempts = frappe.cache().get(cache_key) or 0
        return attempts >= 5
    
    @staticmethod
    def _record_failed_attempt(client_ip: str):
        """Record failed authentication attempt"""
        cache_key = f"login_attempts:{client_ip}"
        attempts = frappe.cache().get(cache_key) or 0
        frappe.cache().setex(cache_key, attempts + 1, 300)  # 5 minutes
```

### Role-Based Access Control

```python
# Secure role-based permissions
import frappe
from frappe.permissions import get_role_permissions

class SecurePermissions:
    """Enhanced permission management"""
    
    @staticmethod
    def check_user_permission(user: str, doctype: str, permission: str) -> bool:
        """Check if user has specific permission"""
        try:
            # Get user roles
            user_roles = frappe.get_roles(user)
            
            # Check each role for permission
            for role in user_roles:
                if SecurePermissions._role_has_permission(role, doctype, permission):
                    return True
            
            return False
            
        except Exception as e:
            frappe.log_error(f"Permission check failed: {str(e)}")
            return False
    
    @staticmethod
    def _role_has_permission(role: str, doctype: str, permission: str) -> bool:
        """Check if role has specific permission"""
        role_perms = get_role_permissions(role)
        
        for perm in role_perms:
            if (perm.doctype == doctype and 
                perm.permlevel == permission):
                return True
        
        return False
```

---

## 🛡️ Data Protection

### Input Validation

```python
# Comprehensive input validation
import re
from frappe import _
from typing import Any, Optional

class InputValidator:
    """Comprehensive input validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        # Remove common formatting characters
        clean_phone = re.sub(r'[^\d+]', '', phone)
        return 10 <= len(clean_phone) <= 15
    
    @staticmethod
    def sanitize_input(data: Any, max_length: int = 255) -> str:
        """Sanitize user input"""
        if not data:
            return ""
        
        # Convert to string and limit length
        sanitized = str(data)[:max_length]
        
        # Remove potentially harmful characters
        sanitized = re.sub(r'[<>"\'\&]', '', sanitized)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_sql_injection(input_data: str) -> bool:
        """Check for potential SQL injection patterns"""
        dangerous_patterns = [
            r'\b(union|select|insert|update|delete|drop|create|alter)\b',
            r'[\'"]\s*;\s*\w+',
            r'\b(or|and)\s+\d+\s*=\s*\d+',
            r'--.*$',
            r'/\*.*\*/'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                return False
        
        return True
```

### Data Encryption

```python
# Data encryption utilities
import frappe
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class DataEncryption:
    """Secure data encryption and decryption"""
    
    def __init__(self):
        self._key = self._generate_key()
        self._cipher = Fernet(self._key)
    
    def _generate_key(self) -> bytes:
        """Generate encryption key"""
        password = frappe.conf.get('encryption_key', '').encode()
        if not password:
            # Generate random key if not configured
            password = os.urandom(32)
        
        salt = b'secure_salt_for_encryption'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted_data = self._cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            frappe.log_error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            frappe.log_error(f"Decryption failed: {str(e)}")
            raise
```

---

## 🔌 API Security

### API Authentication

```python
# Secure API authentication with JWT
import jwt
import time
from datetime import datetime, timedelta
from typing import Dict, Any

class APISecurity:
    """Secure API authentication and authorization"""
    
    def __init__(self):
        self.secret_key = frappe.conf.get('jwt_secret', 'your-secret-key')
    
    def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Generate JWT token"""
        try:
            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(seconds=expires_in),
                'iat': datetime.utcnow(),
                'iss': 'erpnext-api'
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')
            return token
            
        except Exception as e:
            frappe.log_error(f"Token generation failed: {str(e)}")
            raise
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
            
        except jwt.ExpiredSignatureError:
            frappe.log_error("Token expired")
            raise frappe.PermissionError("Token expired")
        except jwt.InvalidTokenError:
            frappe.log_error("Invalid token")
            raise frappe.PermissionError("Invalid token")
        except Exception as e:
            frappe.log_error(f"Token verification failed: {str(e)}")
            raise
    
    def rate_limit_api(self, user_id: str, endpoint: str, limit: int = 100) -> bool:
        """API rate limiting"""
        try:
            cache_key = f"api_rate_limit:{user_id}:{endpoint}"
            current_count = frappe.cache().get(cache_key) or 0
            
            if current_count >= limit:
                return False
            
            # Increment counter with 1 hour expiry
            frappe.cache().setex(cache_key, current_count + 1, 3600)
            return True
            
        except Exception as e:
            frappe.log_error(f"Rate limiting failed: {str(e)}")
            return False
```

### API Input Validation

```python
# API input validation middleware
from flask import request, jsonify
from functools import wraps

def validate_api_input(f):
    """Decorator for API input validation"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Validate content type
            if request.content_type != 'application/json':
                return jsonify({
                    'error': 'Content-Type must be application/json'
                }), 400
            
            # Validate request size
            if request.content_length and request.content_length > 1024 * 1024:  # 1MB
                return jsonify({
                    'error': 'Request too large'
                }), 413
            
            # Validate JSON structure
            try:
                data = request.get_json()
                if not isinstance(data, dict):
                    return jsonify({
                        'error': 'Invalid JSON structure'
                    }), 400
            except:
                return jsonify({
                    'error': 'Invalid JSON format'
                }), 400
            
            return f(*args, **kwargs)
            
        except Exception as e:
            frappe.log_error(f"API validation error: {str(e)}")
            return jsonify({
                'error': 'Validation failed'
            }), 500
    
    return decorated_function
```

---

## 🗄️ Database Security

### Secure Database Connections

```python
# Secure database configuration
import frappe
from frappe.database import Database

class SecureDatabase:
    """Secure database connection management"""
    
    @staticmethod
    def get_secure_connection():
        """Get database connection with security settings"""
        try:
            # Use SSL for database connections in production
            if frappe.conf.get('environment') == 'production':
                db_config = {
                    'ssl': {
                        'ca': frappe.conf.get('db_ssl_ca'),
                        'cert': frappe.conf.get('db_ssl_cert'),
                        'key': frappe.conf.get('db_ssl_key')
                    }
                }
            else:
                db_config = {}
            
            return Database(user='frappe', **db_config)
            
        except Exception as e:
            frappe.log_error(f"Database connection failed: {str(e)}")
            raise

# Secure SQL query builder
class SecureQueryBuilder:
    """Secure SQL query builder with parameter binding"""
    
    @staticmethod
    def build_select_query(table: str, fields: list, 
                         filters: dict = None, 
                         order_by: str = None,
                         limit: int = None) -> tuple:
        """Build secure SELECT query with parameter binding"""
        
        # Validate table name
        if not SecureQueryBuilder._validate_table_name(table):
            raise ValueError("Invalid table name")
        
        # Validate field names
        for field in fields:
            if not SecureQueryBuilder._validate_field_name(field):
                raise ValueError(f"Invalid field name: {field}")
        
        # Build query
        query_parts = [f"SELECT {', '.join(fields)} FROM `{table}`"]
        params = []
        
        if filters:
            where_clause, where_params = SecureQueryBuilder._build_where_clause(filters)
            query_parts.append(f"WHERE {where_clause}")
            params.extend(where_params)
        
        if order_by:
            query_parts.append(f"ORDER BY {order_by}")
        
        if limit:
            query_parts.append("LIMIT %s")
            params.append(limit)
        
        query = " ".join(query_parts)
        return query, tuple(params)
    
    @staticmethod
    def _validate_table_name(table: str) -> bool:
        """Validate table name against SQL injection"""
        # Allow only alphanumeric characters and underscores
        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table) is not None
    
    @staticmethod
    def _validate_field_name(field: str) -> bool:
        """Validate field name against SQL injection"""
        # Allow alphanumeric characters, underscores, and dots
        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', field) is not None
    
    @staticmethod
    def _build_where_clause(filters: dict) -> tuple:
        """Build WHERE clause with parameter binding"""
        conditions = []
        params = []
        
        for field, value in filters.items():
            if isinstance(value, list):
                placeholders = ', '.join(['%s'] * len(value))
                conditions.append(f"`{field}` IN ({placeholders})")
                params.extend(value)
            else:
                conditions.append(f"`{field}` = %s")
                params.append(value)
        
        where_clause = " AND ".join(conditions)
        return where_clause, params
```

---

## 🔒 Application Security

### CSRF Protection

```python
# CSRF protection for forms
import frappe
import secrets
from frappe.utils import cstr

class CSRFProtection:
    """CSRF protection for web forms"""
    
    @staticmethod
    def generate_token() -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_token(token: str) -> bool:
        """Validate CSRF token"""
        try:
            # Get token from session
            session_token = frappe.session.get('csrf_token')
            
            if not session_token:
                return False
            
            # Use secrets.compare_digest for secure comparison
            return secrets.compare_digest(
                cstr(token).encode(),
                cstr(session_token).encode()
            )
            
        except Exception as e:
            frappe.log_error(f"CSRF validation failed: {str(e)}")
            return False
    
    @staticmethod
    def set_token():
        """Set CSRF token in session"""
        token = CSRFProtection.generate_token()
        frappe.session['csrf_token'] = token
        return token
```

### Secure File Uploads

```python
# Secure file upload validation
import os
import hashlib
from werkzeug.utils import secure_filename
from frappe import _

class SecureFileUpload:
    """Secure file upload validation"""
    
    ALLOWED_EXTENSIONS = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
        'document': ['.pdf', '.doc', '.docx', '.txt', '.csv'],
        'spreadsheet': ['.xls', '.xlsx', '.csv']
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_file_upload(file_data, file_type: str = 'document') -> dict:
        """Validate uploaded file"""
        try:
            # Check file size
            if len(file_data) > SecureFileUpload.MAX_FILE_SIZE:
                return {
                    'valid': False,
                    'error': 'File too large'
                }
            
            # Check file extension
            filename = secure_filename(file_data.filename)
            file_ext = os.path.splitext(filename)[1].lower()
            
            allowed_exts = SecureFileUpload.ALLOWED_EXTENSIONS.get(file_type, [])
            
            if file_ext not in allowed_exts:
                return {
                    'valid': False,
                    'error': f'File type {file_ext} not allowed'
                }
            
            # Calculate file hash
            file_hash = hashlib.sha256(file_data.read()).hexdigest()
            file_data.seek(0)  # Reset file pointer
            
            return {
                'valid': True,
                'filename': filename,
                'hash': file_hash,
                'size': len(file_data)
            }
            
        except Exception as e:
            frappe.log_error(f"File validation failed: {str(e)}")
            return {
                'valid': False,
                'error': 'File validation failed'
            }
```

---

## 🧪 Security Testing

### Security Test Suite

```python
# Security testing utilities
import unittest
import frappe
from frappe.tests.utils import FrappeTestCase

class SecurityTests(FrappeTestCase):
    """Security test cases"""
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        # Test malicious input
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1 UNION SELECT * FROM users --",
            "'; UPDATE users SET password='hacked' --"
        ]
        
        for malicious_input in malicious_inputs:
            with self.assertRaises(frappe.ValidationError):
                # This should raise validation error
                frappe.db.sql(f"SELECT * FROM tabUser WHERE name = '{malicious_input}'")
    
    def test_xss_protection(self):
        """Test XSS protection"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            # Test input sanitization
            sanitized = InputValidator.sanitize_input(payload)
            self.assertNotIn('<script>', sanitized)
            self.assertNotIn('javascript:', sanitized)
    
    def test_authentication_security(self):
        """Test authentication security"""
        # Test rate limiting
        client_ip = "127.0.0.1"
        
        # Simulate multiple failed attempts
        for i in range(6):
            result = SecureAuthentication.authenticate_user(
                "test_user", "wrong_password"
            )
            if i < 5:
                self.assertFalse(result['success'])
            else:
                # Should be rate limited
                self.assertIn('Too many login attempts', str(result))
    
    def test_api_security(self):
        """Test API security"""
        # Test JWT token validation
        token = APISecurity().generate_token("test_user")
        
        # Valid token should work
        payload = APISecurity().verify_token(token)
        self.assertEqual(payload['user_id'], 'test_user')
        
        # Invalid token should fail
        with self.assertRaises(frappe.PermissionError):
            APISecurity().verify_token("invalid_token")
        
        # Expired token should fail
        expired_token = APISecurity().generate_token("test_user", expires_in=-1)
        with self.assertRaises(frappe.PermissionError):
            APISecurity().verify_token(expired_token)
    
    def test_file_upload_security(self):
        """Test file upload security"""
        # Test malicious file upload
        malicious_file = b"<script>alert('xss')</script>"
        
        result = SecureFileUpload.validate_file_upload(
            type('MockFile', filename='malicious.js', data=malicious_file),
            'document'
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('File type not allowed', result['error'])
```

---

## ✅ Security Checklist

### Development Phase Checklist

- [ ] **Input Validation**
  - [ ] All user inputs are validated and sanitized
  - [ ] SQL injection protection implemented
  - [ ] XSS protection in place
  - [ ] File upload validation implemented

- [ ] **Authentication**
  - [ ] Strong password policies enforced
  - [ ] Rate limiting on login attempts
  - [ ] Session management secure
  - [ ] Multi-factor authentication considered

- [ ] **Authorization**
  - [ ] Principle of least privilege applied
  - [ ] Role-based access control implemented
  - [ ] Permission checks on all sensitive operations
  - [ ] Regular permission audits

### Production Phase Checklist

- [ ] **Network Security**
  - [ ] HTTPS/TLS enforced
  - [ ] Security headers configured
  - [ ] Firewall rules implemented
  - [ ] DDoS protection in place

- [ ] **Database Security**
  - [ ] Database connections encrypted
  - [ ] Regular database backups
  - [ ] Database access limited
  - [ ] SQL injection protection verified

- [ ] **Application Security**
  - [ ] Error handling doesn't leak information
  - [ ] Logging doesn't contain sensitive data
  - [ ] Debug mode disabled in production
  - [ ] Security headers configured

- [ ] **Monitoring**
  - [ ] Security event logging
  - [ ] Intrusion detection
  - [ ] Regular security scans
  - [ ] Vulnerability assessments

---

## 🚨 Common Security Vulnerabilities

### 1. SQL Injection

**Problem:** Malicious SQL code executed through user input
**Solution:** Use parameterized queries and input validation

```python
# BAD - Vulnerable to SQL injection
query = f"SELECT * FROM tabUser WHERE name = '{user_input}'"

# GOOD - Protected with parameterized query
query = "SELECT * FROM tabUser WHERE name = %s"
result = frappe.db.sql(query, (user_input,), as_dict=True)
```

### 2. Cross-Site Scripting (XSS)

**Problem:** Malicious scripts executed in user's browser
**Solution:** Input sanitization and output encoding

```python
# BAD - Vulnerable to XSS
return f"<div>{user_input}</div>"

# GOOD - Protected with sanitization
sanitized = InputValidator.sanitize_input(user_input)
return f"<div>{sanitized}</div>"
```

### 3. Authentication Bypass

**Problem:** Weak authentication mechanisms
**Solution:** Strong passwords, rate limiting, MFA

```python
# BAD - Weak authentication
if password == "password123":
    return True

# GOOD - Strong authentication
return bcrypt.checkpw(password.encode(), hashed_password.encode())
```

---

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Frappe Security Guidelines](https://frappeframework.com/docs/user/en/security)
- [Python Security Best Practices](https://python-security.readthedocs.io/)
- [Database Security Guidelines](https://owasp.org/www-project-database-security-cheatsheet/)

---

## 🎯 Security Best Practices Summary

1. **Never Trust User Input** - Always validate and sanitize
2. **Use Parameterized Queries** - Prevent SQL injection
3. **Implement Rate Limiting** - Prevent brute force attacks
4. **Encrypt Sensitive Data** - Protect data at rest and in transit
5. **Regular Security Audits** - Stay ahead of threats
6. **Keep Software Updated** - Patch vulnerabilities promptly
7. **Monitor Security Events** - Detect and respond to incidents
8. **Educate Users** - Security is everyone's responsibility

---

*This security guide should be reviewed regularly and updated with new threats and best practices.*
