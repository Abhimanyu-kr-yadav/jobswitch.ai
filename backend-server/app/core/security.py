"""
Security utilities for input validation, sanitization, and data protection.
"""
import re
import html
import hashlib
import secrets

# Optional import for HTML sanitization
try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator
from fastapi import HTTPException, Request
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import logging

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration constants"""
    MAX_STRING_LENGTH = 10000
    MAX_EMAIL_LENGTH = 254
    MAX_PASSWORD_LENGTH = 128
    MIN_PASSWORD_LENGTH = 8
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES = {'.pdf', '.doc', '.docx', '.txt'}
    
    # Allowed HTML tags for rich text content
    ALLOWED_HTML_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3']
    ALLOWED_HTML_ATTRIBUTES = {}

class InputValidator:
    """Input validation and sanitization utilities"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = SecurityConfig.MAX_STRING_LENGTH) -> str:
        """Sanitize string input by removing dangerous characters and limiting length"""
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # Remove null bytes and control characters
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        # HTML escape to prevent XSS
        value = html.escape(value)
        
        # Limit length
        if len(value) > max_length:
            raise ValueError(f"String length exceeds maximum of {max_length} characters")
        
        return value.strip()
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """Sanitize HTML content using bleach (if available) or basic escaping"""
        if BLEACH_AVAILABLE:
            return bleach.clean(
                value,
                tags=SecurityConfig.ALLOWED_HTML_TAGS,
                attributes=SecurityConfig.ALLOWED_HTML_ATTRIBUTES,
                strip=True
            )
        else:
            # Fallback to basic HTML escaping
            return html.escape(value)
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email address"""
        email = InputValidator.sanitize_string(email, SecurityConfig.MAX_EMAIL_LENGTH)
        
        # Basic email regex validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return email.lower()
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password strength"""
        if not isinstance(password, str):
            raise ValueError("Password must be a string")
        
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters")
        
        if len(password) > SecurityConfig.MAX_PASSWORD_LENGTH:
            raise ValueError(f"Password must not exceed {SecurityConfig.MAX_PASSWORD_LENGTH} characters")
        
        # Check for at least one uppercase, lowercase, digit, and special character
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            raise ValueError("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain at least one special character")
        
        return password
    
    @staticmethod
    def validate_file_upload(filename: str, file_size: int) -> str:
        """Validate file upload parameters"""
        filename = InputValidator.sanitize_string(filename, 255)
        
        # Check file size
        if file_size > SecurityConfig.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum of {SecurityConfig.MAX_FILE_SIZE} bytes")
        
        # Check file extension
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in SecurityConfig.ALLOWED_FILE_TYPES:
            raise ValueError(f"File type {file_ext} not allowed")
        
        # Remove path traversal attempts
        filename = os.path.basename(filename)
        
        return filename
    
    @staticmethod
    def validate_json_input(data: Dict[str, Any], max_depth: int = 10) -> Dict[str, Any]:
        """Validate JSON input for depth and content"""
        def check_depth(obj, current_depth=0):
            if current_depth > max_depth:
                raise ValueError(f"JSON depth exceeds maximum of {max_depth}")
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if not isinstance(key, str):
                        raise ValueError("JSON keys must be strings")
                    check_depth(value, current_depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, current_depth + 1)
        
        check_depth(data)
        return data

class DataEncryption:
    """Data encryption utilities for sensitive information"""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        if encryption_key:
            self.fernet = Fernet(encryption_key)
        else:
            # Generate key from environment variable or create new one
            key = os.environ.get('ENCRYPTION_KEY')
            if key:
                self.fernet = Fernet(key.encode())
            else:
                # Generate new key (should be stored securely in production)
                key = Fernet.generate_key()
                self.fernet = Fernet(key)
                logger.warning("Generated new encryption key. Store securely!")
    
    def encrypt_string(self, plaintext: str) -> str:
        """Encrypt a string and return base64 encoded result"""
        if not plaintext:
            return ""
        
        encrypted = self.fernet.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_string(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded encrypted string"""
        if not encrypted_data:
            return ""
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data")
    
    def hash_sensitive_data(self, data: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """Hash sensitive data with salt for storage"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(data.encode()))
        salt_b64 = base64.b64encode(salt).decode()
        
        return key.decode(), salt_b64

class SecurityHeaders:
    """Security headers for HTTP responses"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }

# Global encryption instance
encryption = DataEncryption()