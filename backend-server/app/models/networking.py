"""
Networking and Contact Database Models
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base import Base



class Contact(Base):
    """Contact information for networking purposes"""
    __tablename__ = "contacts"
    
    contact_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)  # User who discovered this contact
    
    # Basic contact information
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(20))
    
    # Professional information
    current_title = Column(String(255))
    current_company = Column(String(255))
    department = Column(String(100))
    seniority_level = Column(String(50))  # 'entry', 'mid', 'senior', 'executive', 'c-level'
    
    # Location
    location = Column(String(255))
    timezone = Column(String(50))
    
    # Social profiles
    linkedin_url = Column(String(500))
    twitter_url = Column(String(500))
    github_url = Column(String(500))
    personal_website = Column(String(500))
    
    # Contact scoring and relevance
    relevance_score = Column(Float, default=0.0)  # 0.0 to 1.0
    contact_quality = Column(String(20), default="unknown")  # 'high', 'medium', 'low', 'unknown'
    
    # Contact source and discovery
    discovery_source = Column(String(50))  # 'linkedin', 'company_website', 'github', etc.
    discovery_method = Column(String(100))  # How the contact was found
    source_url = Column(String(500))  # Original source URL
    
    # Contact status
    contact_status = Column(String(50), default="discovered")  # 'discovered', 'contacted', 'responded', 'connected'
    last_contact_date = Column(DateTime)
    response_rate = Column(Float, default=0.0)  # Historical response rate
    
    # Metadata
    notes = Column(Text)  # User notes about the contact
    tags = Column(JSON)  # List of tags for categorization
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contact to dictionary"""
        return {
            "contact_id": self.contact_id,
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "current_title": self.current_title,
            "current_company": self.current_company,
            "department": self.department,
            "seniority_level": self.seniority_level,
            "location": self.location,
            "timezone": self.timezone,
            "linkedin_url": self.linkedin_url,
            "twitter_url": self.twitter_url,
            "github_url": self.github_url,
            "personal_website": self.personal_website,
            "relevance_score": self.relevance_score,
            "contact_quality": self.contact_quality,
            "discovery_source": self.discovery_source,
            "discovery_method": self.discovery_method,
            "source_url": self.source_url,
            "contact_status": self.contact_status,
            "last_contact_date": self.last_contact_date.isoformat() if self.last_contact_date else None,
            "response_rate": self.response_rate,
            "notes": self.notes,
            "tags": self.tags,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Company(Base):
    """Company information for networking research"""
    __tablename__ = "companies"
    
    company_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255))  # Company website domain
    
    # Company details
    industry = Column(String(100))
    size = Column(String(50))  # 'startup', 'small', 'medium', 'large', 'enterprise'
    employee_count = Column(Integer)
    founded_year = Column(Integer)
    
    # Location
    headquarters = Column(String(255))
    locations = Column(JSON)  # List of office locations
    
    # Company information
    description = Column(Text)
    mission = Column(Text)
    values = Column(JSON)  # List of company values
    
    # Social presence
    website = Column(String(500))
    linkedin_url = Column(String(500))
    twitter_url = Column(String(500))
    careers_page = Column(String(500))
    
    # Networking metadata
    contact_count = Column(Integer, default=0)  # Number of contacts at this company
    last_scraped = Column(DateTime)
    scraping_status = Column(String(50), default="pending")  # 'pending', 'in_progress', 'completed', 'failed'
    
    # Company scoring
    networking_priority = Column(String(20), default="medium")  # 'low', 'medium', 'high'
    hiring_activity = Column(String(20), default="unknown")  # 'low', 'medium', 'high', 'unknown'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert company to dictionary"""
        return {
            "company_id": self.company_id,
            "name": self.name,
            "domain": self.domain,
            "industry": self.industry,
            "size": self.size,
            "employee_count": self.employee_count,
            "founded_year": self.founded_year,
            "headquarters": self.headquarters,
            "locations": self.locations,
            "description": self.description,
            "mission": self.mission,
            "values": self.values,
            "website": self.website,
            "linkedin_url": self.linkedin_url,
            "twitter_url": self.twitter_url,
            "careers_page": self.careers_page,
            "contact_count": self.contact_count,
            "last_scraped": self.last_scraped.isoformat() if self.last_scraped else None,
            "scraping_status": self.scraping_status,
            "networking_priority": self.networking_priority,
            "hiring_activity": self.hiring_activity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class NetworkingCampaign(Base):
    """Networking campaign tracking"""
    __tablename__ = "networking_campaigns"
    
    campaign_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    
    # Campaign details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_company = Column(String(255))
    target_role = Column(String(255))
    
    # Campaign configuration
    campaign_type = Column(String(50))  # 'company_research', 'role_specific', 'industry_wide'
    contact_criteria = Column(JSON)  # Criteria for selecting contacts
    message_template = Column(Text)  # Email template for outreach
    
    # Campaign status
    status = Column(String(50), default="draft")  # 'draft', 'active', 'paused', 'completed'
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Campaign metrics
    contacts_targeted = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    responses_received = Column(Integer, default=0)
    connections_made = Column(Integer, default=0)
    response_rate = Column(Float, default=0.0)
    
    # Campaign settings
    daily_limit = Column(Integer, default=10)  # Max emails per day
    follow_up_enabled = Column(Boolean, default=True)
    follow_up_delay_days = Column(Integer, default=7)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert campaign to dictionary"""
        return {
            "campaign_id": self.campaign_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "target_company": self.target_company,
            "target_role": self.target_role,
            "campaign_type": self.campaign_type,
            "contact_criteria": self.contact_criteria,
            "message_template": self.message_template,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "contacts_targeted": self.contacts_targeted,
            "emails_sent": self.emails_sent,
            "responses_received": self.responses_received,
            "connections_made": self.connections_made,
            "response_rate": self.response_rate,
            "daily_limit": self.daily_limit,
            "follow_up_enabled": self.follow_up_enabled,
            "follow_up_delay_days": self.follow_up_delay_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ContactInteraction(Base):
    """Track interactions with contacts"""
    __tablename__ = "contact_interactions"
    
    interaction_id = Column(String(50), primary_key=True)
    contact_id = Column(String(50), nullable=False)
    campaign_id = Column(String(50))  # Optional: if part of a campaign
    user_id = Column(String(50), nullable=False)
    
    # Interaction details
    interaction_type = Column(String(50))  # 'email', 'linkedin_message', 'phone_call', 'meeting'
    subject = Column(String(500))
    message_content = Column(Text)
    
    # Interaction status
    status = Column(String(50))  # 'sent', 'delivered', 'opened', 'responded', 'bounced'
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    responded_at = Column(DateTime)
    
    # Response tracking
    response_content = Column(Text)
    response_sentiment = Column(String(20))  # 'positive', 'neutral', 'negative'
    follow_up_needed = Column(Boolean, default=False)
    follow_up_date = Column(DateTime)
    
    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert interaction to dictionary"""
        return {
            "interaction_id": self.interaction_id,
            "contact_id": self.contact_id,
            "campaign_id": self.campaign_id,
            "user_id": self.user_id,
            "interaction_type": self.interaction_type,
            "subject": self.subject,
            "message_content": self.message_content,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "response_content": self.response_content,
            "response_sentiment": self.response_sentiment,
            "follow_up_needed": self.follow_up_needed,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }