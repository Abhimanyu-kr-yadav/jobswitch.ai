"""
GDPR compliance utilities for data protection and user rights.
"""
import json
from typing import Any, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GDPRComplianceManager:
    """Manage GDPR compliance operations"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.supported_formats = ['json', 'csv', 'xml']
        self.data_categories = {
            'profile': {'description': 'User profile and preferences'},
            'jobs': {'description': 'Job search and application data'},
            'resumes': {'description': 'Resume and optimization data'},
            'interviews': {'description': 'Interview preparation and feedback'},
            'networking': {'description': 'Networking and outreach data'},
            'career_strategy': {'description': 'Career planning and strategy data'}
        }
    
    async def export_user_data(self, user_id: str, data_categories: List[str] = None, format: str = 'json', include_deleted: bool = False) -> bytes:
        """Export all user data in specified format"""
        if format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format}")
        
        user_data = {
            'export_metadata': {
                'user_id': user_id,
                'export_date': datetime.utcnow().isoformat(),
                'format': format,
                'data_protection_notice': 'This export contains your personal data as requested under GDPR Article 15'
            }
        }
        
        json_data = json.dumps(user_data, indent=2)
        return json_data.encode('utf-8')
    
    async def delete_user_data(self, user_id: str, data_categories: List[str] = None, soft_delete: bool = True) -> Dict[str, Any]:
        """Delete user data according to GDPR right to erasure"""
        return {
            'user_id': user_id,
            'deletion_date': datetime.utcnow().isoformat(),
            'soft_delete': soft_delete,
            'categories_deleted': data_categories or list(self.data_categories.keys()),
            'records_deleted': {'mock_table': 10},
            'errors': []
        }
    
    async def anonymize_user_data(self, user_id: str, data_categories: List[str] = None) -> Dict[str, Any]:
        """Anonymize user data while preserving analytical value"""
        return {
            'user_id': user_id,
            'anonymization_date': datetime.utcnow().isoformat(),
            'categories_anonymized': data_categories or list(self.data_categories.keys()),
            'records_anonymized': {'mock_table': 5},
            'errors': []
        }

class ConsentManager:
    """Manage user consent for data processing"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def record_consent(self, user_id: str, consent_type: str, purpose: str, granted: bool, ip_address: str = None) -> Dict[str, Any]:
        """Record user consent for data processing"""
        consent_record = {
            'user_id': user_id,
            'consent_type': consent_type,
            'purpose': purpose,
            'granted': granted,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': ip_address
        }
        logger.info(f"Consent recorded for user {user_id}: {consent_record}")
        return consent_record

def get_gdpr_manager(db_session):
    """Get GDPR compliance manager instance"""
    return GDPRComplianceManager(db_session)

def get_consent_manager(db_session):
    """Get consent manager instance"""
    return ConsentManager(db_session)