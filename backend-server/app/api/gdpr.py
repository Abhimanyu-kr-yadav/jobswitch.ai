"""
GDPR compliance API endpoints for data protection and user rights.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import logging

from app.core.database import get_database
from app.core.auth import get_current_user
from app.core.gdpr_compliance import get_gdpr_manager, get_consent_manager
from app.schemas.validation import (
    DataExportRequest, DataDeletionRequest, BaseValidatedModel
)
from app.models.user import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdpr", tags=["GDPR Compliance"])

class ConsentRequest(BaseValidatedModel):
    consent_type: str
    purpose: str
    granted: bool

class ConsentWithdrawalRequest(BaseValidatedModel):
    consent_type: str

@router.post("/export-data")
async def export_user_data(
    request: DataExportRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Export user data according to GDPR Article 15 (Right of Access)
    
    Returns user data in requested format (JSON, CSV, or XML)
    """
    try:
        gdpr_manager = get_gdpr_manager(db)
        
        # Export user data
        exported_data = await gdpr_manager.export_user_data(
            user_id=current_user.id,
            data_categories=request.data_types,
            format=request.format,
            include_deleted=request.include_deleted
        )
        
        # Determine content type and filename
        if request.format == 'json':
            content_type = 'application/json'
            filename = f"user_data_export_{current_user.id}.json"
        elif request.format == 'csv':
            content_type = 'application/zip'
            filename = f"user_data_export_{current_user.id}.zip"
        elif request.format == 'xml':
            content_type = 'application/xml'
            filename = f"user_data_export_{current_user.id}.xml"
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported export format"
            )
        
        # Create streaming response
        data_stream = io.BytesIO(exported_data)
        
        return StreamingResponse(
            io.BytesIO(exported_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(exported_data))
            }
        )
        
    except ValueError as e:
        logger.error(f"Data export failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during data export: {e}")
        raise HTTPException(
            status_code=500,
            detail="Data export failed"
        )

@router.delete("/delete-data")
async def delete_user_data(
    request: DataDeletionRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Delete user data according to GDPR Article 17 (Right to Erasure)
    
    Supports both soft delete (marking as deleted) and hard delete (permanent removal)
    """
    try:
        if not request.confirm_deletion:
            raise HTTPException(
                status_code=400,
                detail="Deletion must be explicitly confirmed"
            )
        
        gdpr_manager = get_gdpr_manager(db)
        
        # Delete user data
        deletion_results = await gdpr_manager.delete_user_data(
            user_id=current_user.id,
            data_categories=request.data_types,
            soft_delete=True  # Default to soft delete for safety
        )
        
        return {
            "success": True,
            "message": "Data deletion completed",
            "deletion_results": deletion_results
        }
        
    except ValueError as e:
        logger.error(f"Data deletion failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during data deletion: {e}")
        raise HTTPException(
            status_code=500,
            detail="Data deletion failed"
        )

@router.post("/anonymize-data")
async def anonymize_user_data(
    data_categories: Optional[List[str]] = None,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Anonymize user data while preserving analytical value
    
    This is an alternative to deletion that maintains data utility for analytics
    """
    try:
        gdpr_manager = get_gdpr_manager(db)
        
        # Anonymize user data
        anonymization_results = await gdpr_manager.anonymize_user_data(
            user_id=current_user.id,
            data_categories=data_categories
        )
        
        return {
            "success": True,
            "message": "Data anonymization completed",
            "anonymization_results": anonymization_results
        }
        
    except ValueError as e:
        logger.error(f"Data anonymization failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during data anonymization: {e}")
        raise HTTPException(
            status_code=500,
            detail="Data anonymization failed"
        )

@router.get("/processing-record")
async def get_data_processing_record(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get record of data processing activities for the user
    
    Required for GDPR Article 30 compliance
    """
    try:
        gdpr_manager = get_gdpr_manager(db)
        
        processing_record = await gdpr_manager.get_data_processing_record(
            user_id=current_user.id
        )
        
        return processing_record
        
    except ValueError as e:
        logger.error(f"Processing record generation failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during processing record generation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Processing record generation failed"
        )

@router.post("/consent")
async def record_consent(
    request: ConsentRequest,
    http_request: Request,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Record user consent for data processing
    
    Required for GDPR Article 7 (Conditions for consent)
    """
    try:
        consent_manager = get_consent_manager(db)
        
        # Get client IP for audit trail
        client_ip = http_request.client.host
        
        consent_record = await consent_manager.record_consent(
            user_id=current_user.id,
            consent_type=request.consent_type,
            purpose=request.purpose,
            granted=request.granted,
            ip_address=client_ip
        )
        
        return {
            "success": True,
            "message": "Consent recorded successfully",
            "consent_record": consent_record
        }
        
    except ValueError as e:
        logger.error(f"Consent recording failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during consent recording: {e}")
        raise HTTPException(
            status_code=500,
            detail="Consent recording failed"
        )

@router.post("/withdraw-consent")
async def withdraw_consent(
    request: ConsentWithdrawalRequest,
    http_request: Request,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Withdraw user consent for data processing
    
    Required for GDPR Article 7(3) (Withdrawal of consent)
    """
    try:
        consent_manager = get_consent_manager(db)
        
        # Get client IP for audit trail
        client_ip = http_request.client.host
        
        withdrawal_record = await consent_manager.withdraw_consent(
            user_id=current_user.id,
            consent_type=request.consent_type,
            ip_address=client_ip
        )
        
        return {
            "success": True,
            "message": "Consent withdrawn successfully",
            "withdrawal_record": withdrawal_record
        }
        
    except ValueError as e:
        logger.error(f"Consent withdrawal failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during consent withdrawal: {e}")
        raise HTTPException(
            status_code=500,
            detail="Consent withdrawal failed"
        )

@router.get("/consent-status")
async def get_consent_status(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get current consent status for the user
    
    Shows all consent types and their current status
    """
    try:
        consent_manager = get_consent_manager(db)
        
        consent_status = await consent_manager.get_consent_status(
            user_id=current_user.id
        )
        
        return consent_status
        
    except ValueError as e:
        logger.error(f"Consent status retrieval failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during consent status retrieval: {e}")
        raise HTTPException(
            status_code=500,
            detail="Consent status retrieval failed"
        )

@router.get("/data-categories")
async def get_data_categories(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get available data categories for export/deletion
    
    Returns list of data categories that can be exported or deleted
    """
    try:
        gdpr_manager = get_gdpr_manager(db)
        
        return {
            "data_categories": gdpr_manager.data_categories,
            "supported_formats": gdpr_manager.supported_formats
        }
        
    except Exception as e:
        logger.error(f"Data categories retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Data categories retrieval failed"
        )

@router.get("/privacy-policy")
async def get_privacy_policy():
    """
    Get current privacy policy
    
    Returns the current privacy policy and data processing information
    """
    return {
        "privacy_policy": {
            "version": "1.0",
            "effective_date": "2025-01-01",
            "data_controller": {
                "name": "JobSwitch.ai",
                "contact": "privacy@jobswitch.ai",
                "address": "123 Privacy Street, Data City, DC 12345"
            },
            "data_processing": {
                "purposes": [
                    "Provide job search and career development services",
                    "Personalize user experience",
                    "Improve our services through analytics",
                    "Communicate with users about our services"
                ],
                "legal_basis": [
                    "Consent (GDPR Article 6(1)(a))",
                    "Legitimate Interest (GDPR Article 6(1)(f))",
                    "Contract Performance (GDPR Article 6(1)(b))"
                ],
                "data_categories": [
                    "Personal identification information",
                    "Professional information",
                    "Usage data and analytics",
                    "Communication preferences"
                ],
                "retention_periods": {
                    "active_users": "Duration of account plus 2 years",
                    "deleted_accounts": "30 days grace period",
                    "audit_logs": "7 years",
                    "anonymized_analytics": "Indefinite"
                }
            },
            "user_rights": [
                "Right of access (Article 15)",
                "Right to rectification (Article 16)",
                "Right to erasure (Article 17)",
                "Right to restrict processing (Article 18)",
                "Right to data portability (Article 20)",
                "Right to object (Article 21)",
                "Right to withdraw consent (Article 7(3))"
            ],
            "contact_info": {
                "data_protection_officer": "dpo@jobswitch.ai",
                "privacy_inquiries": "privacy@jobswitch.ai",
                "supervisory_authority": "Your local data protection authority"
            }
        }
    }
