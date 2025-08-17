"""
Networking API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..agents.networking import NetworkingAgent
from ..core.auth import get_current_user
from ..models.user import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents/networking", tags=["networking"])

# Initialize networking agent
networking_agent = NetworkingAgent()


# Request/Response Models
class ContactDiscoveryRequest(BaseModel):
    company_name: str = Field(..., description="Name of the company to research")
    company_domain: Optional[str] = Field(None, description="Company website domain")
    target_role: Optional[str] = Field(None, description="Specific role to target")


class ContactScoringRequest(BaseModel):
    contacts: List[Dict[str, Any]] = Field(..., description="List of contacts to score")
    target_role: Optional[str] = Field(None, description="Target role for relevance scoring")


class CompanyResearchRequest(BaseModel):
    company_name: str = Field(..., description="Company name to research")


class CampaignCreateRequest(BaseModel):
    campaign_name: str = Field(..., description="Name of the networking campaign")
    description: Optional[str] = Field(None, description="Campaign description")
    target_company: Optional[str] = Field(None, description="Target company")
    target_role: Optional[str] = Field(None, description="Target role")
    campaign_type: str = Field("company_research", description="Type of campaign")
    contact_criteria: Optional[Dict[str, Any]] = Field({}, description="Criteria for selecting contacts")
    daily_limit: int = Field(10, description="Daily outreach limit")


class ContactRecommendationsRequest(BaseModel):
    target_role: Optional[str] = Field(None, description="Target role")
    target_companies: Optional[List[str]] = Field([], description="Target companies")


class NetworkingResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    recommendations: Optional[List[Dict[str, Any]]] = []
    timestamp: datetime


@router.post("/discover-contacts", response_model=NetworkingResponse)
async def discover_contacts(
    request: ContactDiscoveryRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Discover contacts at a specific company
    """
    try:
        user_input = {
            'action': 'discover_contacts',
            'user_id': current_user.user_id,
            'company_name': request.company_name,
            'company_domain': request.company_domain,
            'target_role': request.target_role
        }
        
        # Get user profile context
        context = {
            'user_profile': current_user.to_dict()
        }
        
        # Process request through networking agent
        result = await networking_agent.process_request(user_input, context)
        
        return NetworkingResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            recommendations=result.get('recommendations', []),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in discover_contacts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Contact discovery failed: {str(e)}"
        )


@router.post("/score-contacts", response_model=NetworkingResponse)
async def score_contacts(
    request: ContactScoringRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Score contacts for relevance to user's career goals
    """
    try:
        user_input = {
            'action': 'score_contacts',
            'user_id': current_user.user_id,
            'contacts': request.contacts,
            'target_role': request.target_role
        }
        
        context = {
            'user_profile': current_user.to_dict()
        }
        
        result = await networking_agent.process_request(user_input, context)
        
        return NetworkingResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            recommendations=result.get('recommendations', []),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in score_contacts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Contact scoring failed: {str(e)}"
        )


@router.post("/research-company", response_model=NetworkingResponse)
async def research_company(
    request: CompanyResearchRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Research a company for networking opportunities
    """
    try:
        user_input = {
            'action': 'research_company',
            'user_id': current_user.user_id,
            'company_name': request.company_name
        }
        
        context = {
            'user_profile': current_user.to_dict()
        }
        
        result = await networking_agent.process_request(user_input, context)
        
        return NetworkingResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            recommendations=result.get('recommendations', []),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in research_company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Company research failed: {str(e)}"
        )


@router.post("/create-campaign", response_model=NetworkingResponse)
async def create_campaign(
    request: CampaignCreateRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Create a new networking campaign
    """
    try:
        user_input = {
            'action': 'create_campaign',
            'user_id': current_user.user_id,
            'campaign_name': request.campaign_name,
            'description': request.description,
            'target_company': request.target_company,
            'target_role': request.target_role,
            'campaign_type': request.campaign_type,
            'contact_criteria': request.contact_criteria,
            'daily_limit': request.daily_limit
        }
        
        context = {
            'user_profile': current_user.to_dict()
        }
        
        result = await networking_agent.process_request(user_input, context)
        
        return NetworkingResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            recommendations=result.get('recommendations', []),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in create_campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign creation failed: {str(e)}"
        )


@router.get("/recommendations", response_model=NetworkingResponse)
async def get_networking_recommendations(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get personalized networking recommendations
    """
    try:
        # Generate recommendations based on user profile
        recommendations = await networking_agent.get_recommendations(current_user.to_dict())
        
        return NetworkingResponse(
            success=True,
            data={
                'recommendations': recommendations,
                'total_recommendations': len(recommendations)
            },
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting networking recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.post("/contact-recommendations", response_model=NetworkingResponse)
async def get_contact_recommendations(
    request: ContactRecommendationsRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get personalized contact recommendations
    """
    try:
        user_input = {
            'action': 'get_contact_recommendations',
            'user_id': current_user.user_id,
            'target_role': request.target_role,
            'target_companies': request.target_companies
        }
        
        context = {
            'user_profile': current_user.to_dict()
        }
        
        result = await networking_agent.process_request(user_input, context)
        
        return NetworkingResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            recommendations=result.get('recommendations', []),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting contact recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get contact recommendations: {str(e)}"
        )


@router.get("/campaigns", response_model=NetworkingResponse)
async def get_user_campaigns(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get user's networking campaigns
    """
    try:
        # In a real implementation, this would query the database
        # For now, return mock data
        campaigns = [
            {
                'campaign_id': 'campaign_1',
                'name': 'Tech Company Outreach',
                'status': 'active',
                'target_company': 'Google',
                'contacts_targeted': 15,
                'emails_sent': 8,
                'responses_received': 2,
                'response_rate': 0.25,
                'created_at': datetime.utcnow().isoformat()
            }
        ]
        
        return NetworkingResponse(
            success=True,
            data={
                'campaigns': campaigns,
                'total_campaigns': len(campaigns)
            },
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting user campaigns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaigns: {str(e)}"
        )


@router.get("/contacts", response_model=NetworkingResponse)
async def get_user_contacts(
    company: Optional[str] = None,
    limit: int = 50,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get user's discovered contacts
    """
    try:
        # In a real implementation, this would query the database
        # For now, return mock data
        contacts = [
            {
                'contact_id': 'contact_1',
                'full_name': 'John Smith',
                'current_title': 'Senior Software Engineer',
                'current_company': 'Google',
                'email': 'john.smith@example.com',
                'linkedin_url': 'https://linkedin.com/in/johnsmith',
                'relevance_score': 0.85,
                'contact_quality': 'high',
                'contact_status': 'discovered',
                'created_at': datetime.utcnow().isoformat()
            }
        ]
        
        # Filter by company if specified
        if company:
            contacts = [c for c in contacts if c.get('current_company', '').lower() == company.lower()]
        
        return NetworkingResponse(
            success=True,
            data={
                'contacts': contacts[:limit],
                'total_contacts': len(contacts),
                'filtered_by_company': company
            },
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting user contacts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get contacts: {str(e)}"
        )


@router.get("/companies", response_model=NetworkingResponse)
async def get_researched_companies(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get companies that have been researched for networking
    """
    try:
        # In a real implementation, this would query the database
        companies = [
            {
                'company_id': 'company_1',
                'name': 'Google',
                'industry': 'Technology',
                'contact_count': 15,
                'networking_priority': 'high',
                'last_scraped': datetime.utcnow().isoformat(),
                'scraping_status': 'completed'
            }
        ]
        
        return NetworkingResponse(
            success=True,
            data={
                'companies': companies,
                'total_companies': len(companies)
            },
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting researched companies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get companies: {str(e)}"
        )


@router.get("/analytics", response_model=NetworkingResponse)
async def get_networking_analytics(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get networking analytics and metrics
    """
    try:
        analytics = {
            'total_contacts': 45,
            'total_companies_researched': 8,
            'active_campaigns': 2,
            'total_outreach_sent': 23,
            'total_responses': 6,
            'overall_response_rate': 0.26,
            'connections_made': 4,
            'meetings_scheduled': 2,
            'top_companies': [
                {'name': 'Google', 'contact_count': 15},
                {'name': 'Microsoft', 'contact_count': 12},
                {'name': 'Apple', 'contact_count': 8}
            ],
            'monthly_activity': {
                'contacts_discovered': 15,
                'emails_sent': 12,
                'responses_received': 3,
                'connections_made': 2
            }
        }
        
        return NetworkingResponse(
            success=True,
            data=analytics,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting networking analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


# Email Generation and Outreach Endpoints

class EmailTemplateRequest(BaseModel):
    contact: Dict[str, Any] = Field(..., description="Contact information")
    campaign_context: Optional[Dict[str, Any]] = Field({}, description="Campaign context")
    template_type: str = Field("cold_outreach", description="Type of email template")


class OutreachEmailRequest(BaseModel):
    to_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    contact_id: Optional[str] = Field(None, description="Contact ID")
    campaign_id: Optional[str] = Field(None, description="Campaign ID")


class EmailCampaignRequest(BaseModel):
    campaign_id: str = Field(..., description="Campaign ID")
    contacts: List[Dict[str, Any]] = Field(..., description="List of contacts")
    template: Dict[str, Any] = Field(..., description="Email template")
    schedule_config: Optional[Dict[str, Any]] = Field({}, description="Campaign schedule configuration")


class CampaignManagementRequest(BaseModel):
    campaign_id: str = Field(..., description="Campaign ID")
    campaign_action: str = Field(..., description="Action to perform (pause, resume, status)")


@router.post("/generate-email-template", response_model=NetworkingResponse)
async def generate_email_template(
    request: EmailTemplateRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Generate personalized email template for a contact
    """
    try:
        user_input = {
            'action': 'generate_email_template',
            'user_id': current_user.user_id,
            'contact': request.contact,
            'campaign_context': request.campaign_context,
            'template_type': request.template_type
        }
        
        context = {
            'user_profile': current_user.to_dict()
        }
        
        result = await networking_agent.process_request(user_input, context)
        
        return NetworkingResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            recommendations=result.get('recommendations', []),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error generating email template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email template generation failed: {str(e)}"
        )


@router.post("/send-outreach-email", response_model=NetworkingResponse)
async def send_outreach_email(
    request: OutreachEmailRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Send outreach email to a contact
    """
    try:
        user_input = {
            'action': 'send_outreach_email',
            'user_id': current_user.user_id,
            'to_email': request.to_email,
            'subject': request.subject,
            'body': request.body,
            'contact_id': request.contact_id,
            'campaign_id': request.campaign_id
        }
        
        context = {
            'user_profile': current_user.to_dict()
        }
        
        result = await networking_agent.process_request(user_input, context)
        
        return NetworkingResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            recommendations=result.get('recommendations', []),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error sending outreach email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Outreach email sending failed: {str(e)}"
        )


@router.post("/start-email-campaign", response_model=NetworkingResponse)
async def start_email_campaign(
    request: EmailCampaignRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Start an automated email campaign
    """
    try:
        user_input = {
            'action': 'start_email_campaign',
            'user_id': current_user.user_id,
            'campaign_id': request.campaign_id,
            'contacts': request.contacts,
            'template': request.template,
            'schedule_config': request.schedule_config
        }
        
        context = {
            'user_profile': current_user.to_dict()
        }
        
        result = await networking_agent.process_request(user_input, context)
        
        return NetworkingResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            recommendations=result.get('recommendations', []),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error starting email campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email campaign start failed: {str(e)}"
        )


@router.post("/manage-campaign", response_model=NetworkingResponse)
async def manage_campaign(
    request: CampaignManagementRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Manage campaign (pause, resume, get status)
    """
    try:
        user_input = {
            'action': 'manage_campaign',
            'user_id': current_user.user_id,
            'campaign_id': request.campaign_id,
            'campaign_action': request.campaign_action
        }
        
        context = {
            'user_profile': current_user.to_dict()
        }
        
        result = await networking_agent.process_request(user_input, context)
        
        return NetworkingResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            recommendations=result.get('recommendations', []),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error managing campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign management failed: {str(e)}"
        )


@router.get("/campaign-analytics", response_model=NetworkingResponse)
async def get_campaign_analytics(
    campaign_id: Optional[str] = None,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get campaign analytics and performance metrics
    """
    try:
        user_input = {
            'action': 'get_campaign_analytics',
            'user_id': current_user.user_id,
            'campaign_id': campaign_id
        }
        
        context = {
            'user_profile': current_user.to_dict()
        }
        
        result = await networking_agent.process_request(user_input, context)
        
        return NetworkingResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            recommendations=result.get('recommendations', []),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting campaign analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign analytics retrieval failed: {str(e)}"
        )


# Email Tracking Endpoints

@router.get("/tracking/pixel/{tracking_id}.png")
async def track_email_open(tracking_id: str):
    """
    Track email open via tracking pixel
    """
    try:
        from ..services.email_sender import email_tracker
        await email_tracker.record_email_opened(tracking_id)
        
        # Return a 1x1 transparent PNG
        import base64
        pixel_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
        )
        
        from fastapi.responses import Response
        return Response(content=pixel_data, media_type="image/png")
        
    except Exception as e:
        logger.error(f"Error tracking email open: {str(e)}")
        # Still return pixel even if tracking fails
        import base64
        pixel_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
        )
        from fastapi.responses import Response
        return Response(content=pixel_data, media_type="image/png")


@router.get("/tracking/link/{tracking_id}")
async def track_link_click(tracking_id: str):
    """
    Track link click and redirect to original URL
    """
    try:
        from ..services.email_sender import email_tracker
        original_url = await email_tracker.record_link_clicked(tracking_id)
        
        if original_url:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=original_url)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracking link not found"
            )
        
    except Exception as e:
        logger.error(f"Error tracking link click: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Link tracking failed"
        )