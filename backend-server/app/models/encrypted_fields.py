"""
Encrypted database fields for sensitive user information.
"""
from typing import Any, Optional, Dict
from sqlalchemy import TypeDecorator, String, Text
from sqlalchemy.ext.declarative import declarative_base
from app.core.security import encryption
import logging

logger = logging.getLogger(__name__)

class EncryptedString(TypeDecorator):
    """SQLAlchemy type for encrypted string fields"""
    
    impl = String
    cache_ok = True
    
    def __init__(self, length=None, **kwargs):
        # Encrypted data is base64 encoded, so we need more space
        if length:
            length = int(length * 1.5)  # Account for base64 encoding overhead
        super().__init__(length, **kwargs)
    
    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Encrypt value before storing in database"""
        if value is None:
            return None
        
        try:
            return encryption.encrypt_string(value)
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError("Failed to encrypt sensitive data")
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Decrypt value when retrieving from database"""
        if value is None:
            return None
        
        try:
            return encryption.decrypt_string(value)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            # Return None instead of raising exception to handle corrupted data gracefully
            return None

class EncryptedText(TypeDecorator):
    """SQLAlchemy type for encrypted text fields"""
    
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Encrypt value before storing in database"""
        if value is None:
            return None
        
        try:
            return encryption.encrypt_string(value)
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError("Failed to encrypt sensitive data")
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Decrypt value when retrieving from database"""
        if value is None:
            return None
        
        try:
            return encryption.decrypt_string(value)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

class HashedField(TypeDecorator):
    """SQLAlchemy type for hashed fields (one-way encryption)"""
    
    impl = String
    cache_ok = True
    
    def __init__(self, length=None, **kwargs):
        # Hash output is fixed length (base64 encoded)
        super().__init__(length or 64, **kwargs)
    
    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Hash value before storing in database"""
        if value is None:
            return None
        
        try:
            hashed_value, salt = encryption.hash_sensitive_data(value)
            # Store hash and salt together (separated by $)
            return f"{hashed_value}${salt}"
        except Exception as e:
            logger.error(f"Hashing failed: {e}")
            raise ValueError("Failed to hash sensitive data")
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Return the stored hash (cannot be decrypted)"""
        return value
    
    def verify_value(self, stored_hash: str, input_value: str) -> bool:
        """Verify input value against stored hash"""
        if not stored_hash or not input_value:
            return False
        
        try:
            # Split hash and salt
            if '$' not in stored_hash:
                return False
            
            stored_hash_part, salt_b64 = stored_hash.split('$', 1)
            
            # Hash input value with same salt
            import base64
            salt = base64.b64decode(salt_b64.encode())
            input_hash, _ = encryption.hash_sensitive_data(input_value, salt)
            
            return input_hash == stored_hash_part
        except Exception as e:
            logger.error(f"Hash verification failed: {e}")
            return False

class EncryptedJSON(TypeDecorator):
    """SQLAlchemy type for encrypted JSON fields"""
    
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value: Optional[Dict], dialect) -> Optional[str]:
        """Encrypt JSON value before storing in database"""
        if value is None:
            return None
        
        try:
            # Convert to JSON string first
            json_str = json.dumps(value)
            return encryption.encrypt_string(json_str)
        except Exception as e:
            logger.error(f"JSON encryption failed: {e}")
            raise ValueError("Failed to encrypt JSON data")
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[Dict]:
        """Decrypt and parse JSON value when retrieving from database"""
        if value is None:
            return None
        
        try:
            # Decrypt first
            decrypted_str = encryption.decrypt_string(value)
            if decrypted_str is None:
                return None
            
            # Parse JSON
            import json
            return json.loads(decrypted_str)
        except Exception as e:
            logger.error(f"JSON decryption failed: {e}")
            return None

class TokenizedField(TypeDecorator):
    """SQLAlchemy type for tokenized fields (replace sensitive data with tokens)"""
    
    impl = String
    cache_ok = True
    
    def __init__(self, length=None, **kwargs):
        super().__init__(length or 64, **kwargs)
        self.token_store = {}  # In production, use Redis or database
    
    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Replace sensitive value with token"""
        if value is None:
            return None
        
        try:
            # Generate token
            token = f"tok_{secrets.token_urlsafe(32)}"
            
            # Store mapping (in production, use secure storage)
            self.token_store[token] = encryption.encrypt_string(value)
            
            return token
        except Exception as e:
            logger.error(f"Tokenization failed: {e}")
            raise ValueError("Failed to tokenize sensitive data")
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Retrieve original value using token"""
        if value is None or not value.startswith('tok_'):
            return value
        
        try:
            # Get encrypted value from token store
            encrypted_value = self.token_store.get(value)
            if encrypted_value is None:
                logger.warning(f"Token not found: {value}")
                return None
            
            # Decrypt and return
            return encryption.decrypt_string(encrypted_value)
        except Exception as e:
            logger.error(f"Detokenization failed: {e}")
            return None
    
    def detokenize(self, token: str) -> Optional[str]:
        """Manually detokenize a token"""
        return self.process_result_value(token, None)

class MaskedField(TypeDecorator):
    """SQLAlchemy type for masked fields (show only partial data)"""
    
    impl = String
    cache_ok = True
    
    def __init__(self, mask_pattern: str = "****", show_last: int = 4, **kwargs):
        super().__init__(**kwargs)
        self.mask_pattern = mask_pattern
        self.show_last = show_last
    
    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Store value encrypted"""
        if value is None:
            return None
        
        try:
            return encryption.encrypt_string(value)
        except Exception as e:
            logger.error(f"Masking encryption failed: {e}")
            raise ValueError("Failed to encrypt masked data")
    
    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Return masked version of the value"""
        if value is None:
            return None
        
        try:
            # Decrypt the value
            decrypted = encryption.decrypt_string(value)
            if decrypted is None:
                return None
            
            # Apply masking
            if len(decrypted) <= self.show_last:
                return self.mask_pattern
            
            visible_part = decrypted[-self.show_last:]
            masked_part = self.mask_pattern
            
            return f"{masked_part}{visible_part}"
        except Exception as e:
            logger.error(f"Masking decryption failed: {e}")
            return self.mask_pattern
    
    def get_full_value(self, encrypted_value: str) -> Optional[str]:
        """Get the full unmasked value (for authorized access)"""
        try:
            return encryption.decrypt_string(encrypted_value)
        except Exception as e:
            logger.error(f"Full value decryption failed: {e}")
            return None

# Utility functions for field encryption
def encrypt_field_value(value: str) -> str:
    """Encrypt a field value"""
    return encryption.encrypt_string(value)

def decrypt_field_value(encrypted_value: str) -> str:
    """Decrypt a field value"""
    return encryption.decrypt_string(encrypted_value)

def hash_field_value(value: str, salt: bytes = None) -> tuple[str, str]:
    """Hash a field value with salt"""
    return encryption.hash_sensitive_data(value, salt)

# Field validation decorators
def validate_encrypted_field(field_name: str):
    """Decorator to validate encrypted field access"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Encrypted field access failed for {field_name}: {e}")
                raise ValueError(f"Cannot access encrypted field {field_name}")
        return wrapper
    return decorator

# Database model mixins for encrypted fields
class EncryptedFieldsMixin:
    """Mixin to add encrypted field support to models"""
    
    def encrypt_field(self, field_name: str, value: str) -> str:
        """Encrypt a field value"""
        try:
            return encryption.encrypt_string(value)
        except Exception as e:
            logger.error(f"Field encryption failed for {field_name}: {e}")
            raise ValueError(f"Cannot encrypt field {field_name}")
    
    def decrypt_field(self, field_name: str, encrypted_value: str) -> str:
        """Decrypt a field value"""
        try:
            return encryption.decrypt_string(encrypted_value)
        except Exception as e:
            logger.error(f"Field decryption failed for {field_name}: {e}")
            return None
    
    def hash_field(self, field_name: str, value: str) -> str:
        """Hash a field value"""
        try:
            hashed_value, salt = encryption.hash_sensitive_data(value)
            return f"{hashed_value}${salt}"
        except Exception as e:
            logger.error(f"Field hashing failed for {field_name}: {e}")
            raise ValueError(f"Cannot hash field {field_name}")

# Import json for EncryptedJSON
import json
import secrets