"""
Data anonymization utilities for GDPR compliance and privacy protection.
"""
import re
import hashlib
import secrets
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataAnonymizer:
    """Utility class for anonymizing sensitive data"""
    
    @staticmethod
    def anonymize_email(email: str) -> str:
        """Anonymize email address while preserving domain"""
        if not email or '@' not in email:
            return "anonymized@example.com"
        
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            anonymized_local = 'x' * len(local)
        else:
            anonymized_local = local[0] + 'x' * (len(local) - 2) + local[-1]
        
        return f"{anonymized_local}@{domain}"
    
    @staticmethod
    def anonymize_phone(phone: str) -> str:
        """Anonymize phone number"""
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) >= 4:
            # Keep last 4 digits, anonymize the rest
            return 'x' * (len(digits) - 4) + digits[-4:]
        else:
            return 'x' * len(digits)
    
    @staticmethod
    def anonymize_name(name: str) -> str:
        """Anonymize name while preserving first letter"""
        if not name:
            return ""
        
        if len(name) <= 1:
            return 'X'
        
        return name[0] + 'x' * (len(name) - 1)
    
    @staticmethod
    def anonymize_address(address: str) -> str:
        """Anonymize address while preserving city/state"""
        if not address:
            return ""
        
        # Simple anonymization - replace numbers and specific street names
        anonymized = re.sub(r'\d+', 'XXX', address)
        anonymized = re.sub(r'\b\w+\s+(St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court)\b', 
                          'XXX Street', anonymized, flags=re.IGNORECASE)
        
        return anonymized
    
    @staticmethod
    def anonymize_ssn(ssn: str) -> str:
        """Anonymize SSN keeping only last 4 digits"""
        if not ssn:
            return ""
        
        digits = re.sub(r'\D', '', ssn)
        if len(digits) >= 4:
            return 'XXX-XX-' + digits[-4:]
        else:
            return 'XXX-XX-XXXX'
    
    @staticmethod
    def anonymize_date_of_birth(dob: Union[str, datetime]) -> str:
        """Anonymize date of birth to just year"""
        if not dob:
            return ""
        
        if isinstance(dob, str):
            try:
                dob = datetime.fromisoformat(dob.replace('Z', '+00:00'))
            except:
                return "XXXX-XX-XX"
        
        return f"{dob.year}-XX-XX"
    
    @staticmethod
    def generate_pseudonym(original_id: str, salt: str = None) -> str:
        """Generate consistent pseudonym for an ID"""
        if not salt:
            salt = "default_salt_change_in_production"
        
        # Create consistent hash-based pseudonym
        hash_input = f"{original_id}{salt}".encode()
        hash_digest = hashlib.sha256(hash_input).hexdigest()
        
        # Convert to readable pseudonym
        return f"user_{hash_digest[:8]}"
    
    @staticmethod
    def anonymize_json_data(data: Dict[str, Any], fields_to_anonymize: List[str]) -> Dict[str, Any]:
        """Anonymize specific fields in JSON data"""
        if not isinstance(data, dict):
            return data
        
        anonymized_data = data.copy()
        
        for field in fields_to_anonymize:
            if field in anonymized_data:
                value = anonymized_data[field]
                
                if field in ['email', 'email_address']:
                    anonymized_data[field] = DataAnonymizer.anonymize_email(str(value))
                elif field in ['phone', 'phone_number', 'mobile']:
                    anonymized_data[field] = DataAnonymizer.anonymize_phone(str(value))
                elif field in ['first_name', 'last_name', 'name']:
                    anonymized_data[field] = DataAnonymizer.anonymize_name(str(value))
                elif field in ['address', 'street_address', 'home_address']:
                    anonymized_data[field] = DataAnonymizer.anonymize_address(str(value))
                elif field in ['ssn', 'social_security_number']:
                    anonymized_data[field] = DataAnonymizer.anonymize_ssn(str(value))
                elif field in ['date_of_birth', 'dob', 'birth_date']:
                    anonymized_data[field] = DataAnonymizer.anonymize_date_of_birth(value)
                else:
                    # Generic anonymization for unknown fields
                    anonymized_data[field] = 'ANONYMIZED'
        
        return anonymized_data

class DataRetentionManager:
    """Manage data retention policies and automatic cleanup"""
    
    def __init__(self):
        self.retention_policies = {
            'user_sessions': timedelta(days=30),
            'audit_logs': timedelta(days=365),
            'temporary_files': timedelta(days=7),
            'deleted_user_data': timedelta(days=30),  # Grace period for account recovery
            'interview_recordings': timedelta(days=90),
            'resume_versions': timedelta(days=365),
        }
    
    def should_delete_data(self, data_type: str, created_at: datetime) -> bool:
        """Check if data should be deleted based on retention policy"""
        if data_type not in self.retention_policies:
            return False
        
        retention_period = self.retention_policies[data_type]
        expiry_date = created_at + retention_period
        
        return datetime.utcnow() > expiry_date
    
    def get_expired_data_query_filter(self, data_type: str) -> datetime:
        """Get datetime filter for expired data queries"""
        if data_type not in self.retention_policies:
            return None
        
        retention_period = self.retention_policies[data_type]
        return datetime.utcnow() - retention_period

class PIIDetector:
    """Detect Personally Identifiable Information in text"""
    
    def __init__(self):
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        }
    
    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect PII in text and return matches by type"""
        if not text:
            return {}
        
        detected_pii = {}
        
        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected_pii[pii_type] = matches
        
        return detected_pii
    
    def sanitize_text(self, text: str, replacement: str = '[REDACTED]') -> str:
        """Remove PII from text"""
        if not text:
            return text
        
        sanitized_text = text
        
        for pii_type, pattern in self.patterns.items():
            sanitized_text = re.sub(pattern, replacement, sanitized_text, flags=re.IGNORECASE)
        
        return sanitized_text
    
    def has_pii(self, text: str) -> bool:
        """Check if text contains any PII"""
        detected = self.detect_pii(text)
        return len(detected) > 0

# Global instances
data_anonymizer = DataAnonymizer()
retention_manager = DataRetentionManager()
pii_detector = PIIDetector()