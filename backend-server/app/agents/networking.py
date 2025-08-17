"""
Networking Agent for Contact Discovery and Management
"""
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from ..agents.base import BaseAgent, AgentResponse, AgentError
from ..services.contact_scraper import ContactScraper, ContactScorer
from ..services.email_generator import EmailTemplateGenerator
from ..services.email_sender import EmailSender, EmailCampaignManager
from ..models.networking import Contact, Company, NetworkingCampaign, ContactInteraction
from ..integrations.watsonx import WatsonXClient

logger = logging.getLogger(__name__)


class NetworkingAgent(BaseAgent):
    """AI agent for networking and contact discovery"""
    
    def __init__(self, agent_id: str = "networking_agent", watsonx_client=None, langchain_config=None):
        super().__init__(agent_id, watsonx_client, langchain_config)
        self.contact_scraper = ContactScraper()
        self.contact_scorer = ContactScorer(watsonx_client)
        self.email_generator = EmailTemplateGenerator(watsonx_client)
        self.email_sender = EmailSender()
        self.campaign_manager = EmailCampaignManager()
        self.status = "ready"
    
    async def process_request(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process networking-related requests
        
        Args:
            user_input: User request containing action and parameters
            context: Current session context
            
        Returns:
            Structured response with networking data
        """
        try:
            if not self._validate_input(user_input):
                return AgentResponse(
                    success=False,
                    error="Invalid input format"
                ).to_dict()
            
            action = user_input.get('action')
            user_id = user_input.get('user_id')
            
            if not user_id:
                return AgentResponse(
                    success=False,
                    error="User ID is required"
                ).to_dict()
            
            # Route to appropriate handler
            if action == 'discover_contacts':
                return await self._discover_contacts(user_input, context)
            elif action == 'score_contacts':
                return await self._score_contacts(user_input, context)
            elif action == 'research_company':
                return await self._research_company(user_input, context)
            elif action == 'create_campaign':
                return await self._create_campaign(user_input, context)
            elif action == 'get_contact_recommendations':
                return await self._get_contact_recommendations(user_input, context)
            elif action == 'generate_email_template':
                return await self._generate_email_template(user_input, context)
            elif action == 'send_outreach_email':
                return await self._send_outreach_email(user_input, context)
            elif action == 'start_email_campaign':
                return await self._start_email_campaign(user_input, context)
            elif action == 'manage_campaign':
                return await self._manage_campaign(user_input, context)
            elif action == 'get_campaign_analytics':
                return await self._get_campaign_analytics(user_input, context)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Unknown action: {action}"
                ).to_dict()
                
        except Exception as e:
            logger.error(f"Error processing networking request: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Processing error: {str(e)}"
            ).to_dict()
    
    async def get_recommendations(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate networking recommendations based on user profile
        
        Args:
            user_profile: User profile data
            
        Returns:
            List of networking recommendations
        """
        try:
            recommendations = []
            
            # Get career goals and target companies
            career_goals = user_profile.get('career_goals', {})
            target_role = career_goals.get('target_role')
            target_companies = career_goals.get('target_companies', [])
            
            # Recommend companies to research
            if target_companies:
                for company in target_companies[:5]:  # Top 5 companies
                    recommendations.append({
                        'type': 'company_research',
                        'title': f'Research contacts at {company}',
                        'description': f'Discover key employees and decision makers at {company}',
                        'priority': 'high',
                        'action': 'research_company',
                        'parameters': {'company_name': company}
                    })
            
            # Recommend role-specific networking
            if target_role:
                recommendations.append({
                    'type': 'role_networking',
                    'title': f'Connect with {target_role} professionals',
                    'description': f'Find and connect with professionals in {target_role} roles',
                    'priority': 'medium',
                    'action': 'discover_contacts',
                    'parameters': {'target_role': target_role}
                })
            
            # Recommend industry networking
            user_industry = user_profile.get('industry')
            if user_industry:
                recommendations.append({
                    'type': 'industry_networking',
                    'title': f'Expand {user_industry} network',
                    'description': f'Connect with professionals in the {user_industry} industry',
                    'priority': 'medium',
                    'action': 'discover_contacts',
                    'parameters': {'industry': user_industry}
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating networking recommendations: {str(e)}")
            return []
    
    async def _discover_contacts(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Discover contacts for networking"""
        try:
            company_name = user_input.get('company_name')
            company_domain = user_input.get('company_domain')
            target_role = user_input.get('target_role')
            user_id = user_input.get('user_id')
            
            if not company_name:
                return AgentResponse(
                    success=False,
                    error="Company name is required for contact discovery"
                ).to_dict()
            
            # Use contact scraper to discover contacts
            async with ContactScraper() as scraper:
                discovered_contacts = await scraper.discover_company_contacts(
                    company_name, company_domain
                )
            
            # Score contacts for relevance
            user_profile = context.get('user_profile', {})
            scored_contacts = []
            
            for contact_data in discovered_contacts:
                # Score the contact
                relevance_score = await self.contact_scorer.score_contact_relevance(
                    contact_data, user_profile, target_role
                )
                
                contact_data['relevance_score'] = relevance_score
                contact_data['user_id'] = user_id
                contact_data['current_company'] = company_name
                
                # Determine contact quality based on available information
                quality_score = self._assess_contact_quality(contact_data)
                contact_data['contact_quality'] = quality_score
                
                scored_contacts.append(contact_data)
            
            # Sort by relevance score
            scored_contacts.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Store contacts in database (simulated)
            stored_contacts = await self._store_contacts(scored_contacts)
            
            return AgentResponse(
                success=True,
                data={
                    'contacts_discovered': len(scored_contacts),
                    'contacts': scored_contacts[:20],  # Return top 20
                    'company_name': company_name
                },
                recommendations=self._generate_contact_recommendations(scored_contacts[:10])
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error discovering contacts: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Contact discovery failed: {str(e)}"
            ).to_dict()
    
    async def _score_contacts(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Score existing contacts for relevance"""
        try:
            contacts = user_input.get('contacts', [])
            target_role = user_input.get('target_role')
            user_profile = context.get('user_profile', {})
            
            scored_contacts = []
            
            for contact in contacts:
                relevance_score = await self.contact_scorer.score_contact_relevance(
                    contact, user_profile, target_role
                )
                contact['relevance_score'] = relevance_score
                scored_contacts.append(contact)
            
            # Sort by relevance
            scored_contacts.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            return AgentResponse(
                success=True,
                data={
                    'scored_contacts': scored_contacts,
                    'total_contacts': len(scored_contacts)
                }
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error scoring contacts: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Contact scoring failed: {str(e)}"
            ).to_dict()
    
    async def _research_company(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Research a company for networking opportunities"""
        try:
            company_name = user_input.get('company_name')
            user_id = user_input.get('user_id')
            
            if not company_name:
                return AgentResponse(
                    success=False,
                    error="Company name is required"
                ).to_dict()
            
            # Gather company information
            company_info = await self._gather_company_info(company_name)
            
            # Discover contacts at the company
            async with ContactScraper() as scraper:
                contacts = await scraper.discover_company_contacts(
                    company_name, company_info.get('domain')
                )
            
            # Score contacts
            user_profile = context.get('user_profile', {})
            for contact in contacts:
                contact['relevance_score'] = await self.contact_scorer.score_contact_relevance(
                    contact, user_profile
                )
                contact['user_id'] = user_id
                contact['current_company'] = company_name
            
            # Sort by relevance
            contacts.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Generate networking strategy
            strategy = await self._generate_networking_strategy(company_info, contacts, user_profile)
            
            return AgentResponse(
                success=True,
                data={
                    'company_info': company_info,
                    'contacts': contacts[:15],  # Top 15 contacts
                    'networking_strategy': strategy,
                    'total_contacts_found': len(contacts)
                },
                recommendations=self._generate_company_networking_recommendations(
                    company_name, contacts[:5]
                )
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error researching company: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Company research failed: {str(e)}"
            ).to_dict()
    
    async def _create_campaign(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a networking campaign"""
        try:
            campaign_data = {
                'campaign_id': str(uuid.uuid4()),
                'user_id': user_input.get('user_id'),
                'name': user_input.get('campaign_name', 'New Networking Campaign'),
                'description': user_input.get('description', ''),
                'target_company': user_input.get('target_company'),
                'target_role': user_input.get('target_role'),
                'campaign_type': user_input.get('campaign_type', 'company_research'),
                'contact_criteria': user_input.get('contact_criteria', {}),
                'daily_limit': user_input.get('daily_limit', 10),
                'status': 'draft'
            }
            
            # Generate message template using AI
            if self.watsonx:
                template = await self._generate_message_template(
                    campaign_data, context.get('user_profile', {})
                )
                campaign_data['message_template'] = template
            
            # Store campaign (simulated)
            stored_campaign = await self._store_campaign(campaign_data)
            
            return AgentResponse(
                success=True,
                data={
                    'campaign': stored_campaign,
                    'next_steps': [
                        'Review and customize the message template',
                        'Select target contacts',
                        'Set campaign schedule',
                        'Launch campaign'
                    ]
                }
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Campaign creation failed: {str(e)}"
            ).to_dict()
    
    async def _get_contact_recommendations(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get personalized contact recommendations"""
        try:
            user_profile = context.get('user_profile', {})
            target_role = user_input.get('target_role')
            target_companies = user_input.get('target_companies', [])
            
            recommendations = []
            
            # Generate recommendations based on career goals
            career_goals = user_profile.get('career_goals', {})
            
            if not target_companies:
                target_companies = career_goals.get('target_companies', [])
            
            if not target_role:
                target_role = career_goals.get('target_role')
            
            # Recommend high-value contacts to connect with
            for company in target_companies[:3]:
                recommendations.append({
                    'type': 'high_value_contact',
                    'title': f'Connect with hiring managers at {company}',
                    'description': f'Reach out to hiring managers and team leads at {company}',
                    'priority': 'high',
                    'company': company,
                    'suggested_roles': ['Hiring Manager', 'Team Lead', 'Director']
                })
            
            # Recommend industry connections
            user_industry = user_profile.get('industry')
            if user_industry:
                recommendations.append({
                    'type': 'industry_connection',
                    'title': f'Expand your {user_industry} network',
                    'description': f'Connect with senior professionals in {user_industry}',
                    'priority': 'medium',
                    'industry': user_industry
                })
            
            return AgentResponse(
                success=True,
                data={
                    'recommendations': recommendations,
                    'total_recommendations': len(recommendations)
                }
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error getting contact recommendations: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Failed to get recommendations: {str(e)}"
            ).to_dict()
    
    def _assess_contact_quality(self, contact: Dict[str, Any]) -> str:
        """Assess the quality of contact information"""
        score = 0
        
        # Check for key information
        if contact.get('email'):
            score += 3
        if contact.get('linkedin_url'):
            score += 2
        if contact.get('current_title'):
            score += 2
        if contact.get('full_name'):
            score += 1
        if contact.get('phone'):
            score += 1
        
        # Determine quality level
        if score >= 6:
            return 'high'
        elif score >= 4:
            return 'medium'
        else:
            return 'low'
    
    async def _store_contacts(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Store contacts in database (simulated)"""
        # In a real implementation, this would store contacts in the database
        stored_contacts = []
        
        for contact in contacts:
            # Add storage metadata
            contact['created_at'] = datetime.utcnow().isoformat()
            contact['updated_at'] = datetime.utcnow().isoformat()
            contact['is_active'] = True
            contact['contact_status'] = 'discovered'
            
            stored_contacts.append(contact)
        
        logger.info(f"Stored {len(stored_contacts)} contacts")
        return stored_contacts
    
    async def _store_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store campaign in database (simulated)"""
        # Add storage metadata
        campaign_data['created_at'] = datetime.utcnow().isoformat()
        campaign_data['updated_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Stored campaign: {campaign_data['name']}")
        return campaign_data
    
    async def _gather_company_info(self, company_name: str) -> Dict[str, Any]:
        """Gather basic company information"""
        # This would typically integrate with company data APIs
        # For now, return basic structure
        return {
            'name': company_name,
            'domain': f"{company_name.lower().replace(' ', '')}.com",
            'industry': 'Technology',  # Would be determined from data
            'size': 'medium',
            'description': f'Information about {company_name}',
            'headquarters': 'Unknown',
            'website': f"https://{company_name.lower().replace(' ', '')}.com"
        }
    
    async def _generate_networking_strategy(self, company_info: Dict[str, Any], 
                                          contacts: List[Dict[str, Any]], 
                                          user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a networking strategy for the company"""
        strategy = {
            'approach': 'multi_touch',
            'priority_contacts': contacts[:5],
            'recommended_sequence': [
                'Research company and recent news',
                'Connect with mid-level employees first',
                'Engage with content before reaching out',
                'Send personalized connection requests',
                'Follow up with value-added messages'
            ],
            'timeline': '2-4 weeks',
            'success_metrics': [
                'Connection acceptance rate > 30%',
                'Response rate > 15%',
                'At least 2 meaningful conversations'
            ]
        }
        
        return strategy
    
    async def _generate_message_template(self, campaign_data: Dict[str, Any], 
                                       user_profile: Dict[str, Any]) -> str:
        """Generate personalized message template using AI"""
        if not self.watsonx:
            return self._get_default_message_template()
        
        try:
            # Create prompt for message generation
            prompt = f"""
            Create a professional networking message template for:
            
            User Profile:
            - Name: {user_profile.get('first_name', 'User')} {user_profile.get('last_name', '')}
            - Current Role: {user_profile.get('current_title', 'Professional')}
            - Industry: {user_profile.get('industry', 'Technology')}
            
            Campaign Details:
            - Target Company: {campaign_data.get('target_company', 'Company')}
            - Target Role: {campaign_data.get('target_role', 'Professional')}
            - Campaign Type: {campaign_data.get('campaign_type', 'networking')}
            
            Create a personalized, professional message that:
            1. Introduces the sender briefly
            2. Mentions a specific reason for connecting
            3. Offers value or mutual benefit
            4. Includes a clear call to action
            5. Is concise (under 150 words)
            
            Use placeholders like {{contact_name}}, {{contact_company}}, {{contact_title}} for personalization.
            """
            
            # Generate message using WatsonX
            response = await self.watsonx.generate_text(prompt)
            return response.get('generated_text', self._get_default_message_template())
            
        except Exception as e:
            logger.error(f"Error generating message template: {str(e)}")
            return self._get_default_message_template()
    
    def _get_default_message_template(self) -> str:
        """Get default message template"""
        return """Hi {{contact_name}},

I hope this message finds you well. I'm {{user_name}}, a {{user_title}} with a strong interest in {{target_company}} and the work you're doing in {{contact_title}}.

I've been following {{target_company}}'s recent developments and am impressed by your team's innovative approach. I'd love to learn more about your experience at {{target_company}} and share some insights from my background in {{user_industry}}.

Would you be open to a brief 15-minute conversation over coffee or a virtual call? I believe we could have a mutually beneficial discussion about industry trends and opportunities.

Thank you for your time, and I look forward to potentially connecting.

Best regards,
{{user_name}}"""
    
    def _generate_contact_recommendations(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on discovered contacts"""
        recommendations = []
        
        high_value_contacts = [c for c in contacts if c.get('relevance_score', 0) > 0.7]
        
        if high_value_contacts:
            recommendations.append({
                'type': 'priority_outreach',
                'title': f'Prioritize outreach to {len(high_value_contacts)} high-value contacts',
                'description': 'These contacts have high relevance scores and should be contacted first',
                'action': 'create_outreach_campaign',
                'contacts': high_value_contacts[:3]
            })
        
        return recommendations
    
    def _generate_company_networking_recommendations(self, company_name: str, 
                                                   top_contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate company-specific networking recommendations"""
        recommendations = []
        
        if top_contacts:
            recommendations.append({
                'type': 'company_outreach',
                'title': f'Start networking campaign for {company_name}',
                'description': f'Begin outreach to {len(top_contacts)} key contacts at {company_name}',
                'priority': 'high',
                'company': company_name,
                'contact_count': len(top_contacts)
            })
        
        recommendations.append({
            'type': 'company_research',
            'title': f'Research {company_name} company culture',
            'description': f'Learn about {company_name}\'s values, recent news, and team structure',
            'priority': 'medium',
            'company': company_name
        })
        
        return recommendations
    
    async def _generate_email_template(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized email template"""
        try:
            contact = user_input.get('contact')
            campaign_context = user_input.get('campaign_context', {})
            template_type = user_input.get('template_type', 'cold_outreach')
            user_profile = context.get('user_profile', {})
            
            if not contact:
                return AgentResponse(
                    success=False,
                    error="Contact information is required"
                ).to_dict()
            
            # Generate template using email generator
            result = await self.email_generator.generate_personalized_template(
                user_profile, contact, campaign_context, template_type
            )
            
            return AgentResponse(
                success=result['success'],
                data={
                    'template': result.get('template'),
                    'context': result.get('context'),
                    'generated_at': result.get('generated_at'),
                    'error': result.get('error')
                }
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error generating email template: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Template generation failed: {str(e)}"
            ).to_dict()
    
    async def _send_outreach_email(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send outreach email to a contact"""
        try:
            to_email = user_input.get('to_email')
            subject = user_input.get('subject')
            body = user_input.get('body')
            contact_id = user_input.get('contact_id')
            campaign_id = user_input.get('campaign_id')
            user_profile = context.get('user_profile', {})
            
            if not all([to_email, subject, body]):
                return AgentResponse(
                    success=False,
                    error="Email address, subject, and body are required"
                ).to_dict()
            
            # Send email
            result = await self.email_sender.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                from_email=user_profile.get('email'),
                from_name=f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip(),
                enable_tracking=True
            )
            
            # Record interaction (in real implementation, save to database)
            interaction_data = {
                'interaction_id': result.get('interaction_id'),
                'contact_id': contact_id,
                'campaign_id': campaign_id,
                'user_id': user_input.get('user_id'),
                'interaction_type': 'email',
                'subject': subject,
                'message_content': body,
                'status': 'sent' if result['success'] else 'failed',
                'sent_at': result.get('sent_at')
            }
            
            return AgentResponse(
                success=result['success'],
                data={
                    'interaction_id': result.get('interaction_id'),
                    'message_id': result.get('message_id'),
                    'sent_at': result.get('sent_at'),
                    'tracking_enabled': result.get('tracking_enabled'),
                    'error': result.get('error')
                }
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error sending outreach email: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Email sending failed: {str(e)}"
            ).to_dict()
    
    async def _start_email_campaign(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Start an automated email campaign"""
        try:
            campaign_id = user_input.get('campaign_id')
            contacts = user_input.get('contacts', [])
            template = user_input.get('template', {})
            schedule_config = user_input.get('schedule_config', {})
            user_profile = context.get('user_profile', {})
            
            if not all([campaign_id, contacts, template]):
                return AgentResponse(
                    success=False,
                    error="Campaign ID, contacts, and template are required"
                ).to_dict()
            
            # Prepare emails for campaign
            emails = []
            for contact in contacts:
                # Personalize template for each contact
                personalized_subject = self._personalize_text(template.get('subject', ''), contact, user_profile)
                personalized_body = self._personalize_text(template.get('body', ''), contact, user_profile)
                
                emails.append({
                    'to_email': contact.get('email'),
                    'subject': personalized_subject,
                    'body': personalized_body,
                    'from_email': user_profile.get('email'),
                    'from_name': f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip(),
                    'interaction_id': str(uuid.uuid4()),
                    'contact_id': contact.get('contact_id'),
                    'enable_tracking': True
                })
            
            # Start campaign
            result = await self.campaign_manager.start_campaign(
                campaign_id=campaign_id,
                emails=emails,
                schedule_config=schedule_config
            )
            
            return AgentResponse(
                success=result['success'],
                data=result,
                recommendations=[
                    {
                        'type': 'campaign_monitoring',
                        'title': 'Monitor campaign progress',
                        'description': f'Track the progress of your {len(emails)}-email campaign',
                        'action': 'get_campaign_status',
                        'campaign_id': campaign_id
                    }
                ]
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error starting email campaign: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Campaign start failed: {str(e)}"
            ).to_dict()
    
    async def _manage_campaign(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage campaign (pause, resume, get status)"""
        try:
            campaign_id = user_input.get('campaign_id')
            action = user_input.get('campaign_action')  # 'pause', 'resume', 'status'
            
            if not campaign_id:
                return AgentResponse(
                    success=False,
                    error="Campaign ID is required"
                ).to_dict()
            
            if action == 'pause':
                result = await self.campaign_manager.pause_campaign(campaign_id)
            elif action == 'resume':
                result = await self.campaign_manager.resume_campaign(campaign_id)
            elif action == 'status':
                result = await self.campaign_manager.get_campaign_status(campaign_id)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Unknown campaign action: {action}"
                ).to_dict()
            
            return AgentResponse(
                success=result['success'],
                data=result
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error managing campaign: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Campaign management failed: {str(e)}"
            ).to_dict()
    
    async def _get_campaign_analytics(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get campaign analytics and performance metrics"""
        try:
            campaign_id = user_input.get('campaign_id')
            user_id = user_input.get('user_id')
            
            # Get campaign status
            if campaign_id:
                status_result = await self.campaign_manager.get_campaign_status(campaign_id)
                if not status_result['success']:
                    return AgentResponse(
                        success=False,
                        error=status_result.get('error', 'Campaign not found')
                    ).to_dict()
                
                analytics = status_result
            else:
                # Get overall analytics for user
                analytics = await self._get_user_campaign_analytics(user_id)
            
            # Generate insights and recommendations
            insights = self._generate_campaign_insights(analytics)
            
            return AgentResponse(
                success=True,
                data={
                    'analytics': analytics,
                    'insights': insights,
                    'generated_at': datetime.utcnow().isoformat()
                }
            ).to_dict()
            
        except Exception as e:
            logger.error(f"Error getting campaign analytics: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Analytics retrieval failed: {str(e)}"
            ).to_dict()
    
    def _personalize_text(self, text: str, contact: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        """Personalize text with contact and user information"""
        try:
            # Replace contact placeholders
            text = text.replace('{{contact_name}}', contact.get('full_name', contact.get('first_name', 'there')))
            text = text.replace('{{contact_first_name}}', contact.get('first_name', ''))
            text = text.replace('{{contact_title}}', contact.get('current_title', ''))
            text = text.replace('{{contact_company}}', contact.get('current_company', ''))
            
            # Replace user placeholders
            user_name = f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip()
            text = text.replace('{{user_name}}', user_name)
            text = text.replace('{{user_title}}', user_profile.get('current_title', ''))
            text = text.replace('{{user_company}}', user_profile.get('current_company', ''))
            
            return text
            
        except Exception as e:
            logger.error(f"Error personalizing text: {str(e)}")
            return text
    
    async def _get_user_campaign_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get overall campaign analytics for a user"""
        # In real implementation, this would query the database
        # For now, return mock analytics
        return {
            'total_campaigns': 3,
            'active_campaigns': 1,
            'completed_campaigns': 2,
            'total_emails_sent': 45,
            'total_responses': 12,
            'overall_response_rate': 26.7,
            'total_connections_made': 8,
            'connection_rate': 17.8,
            'average_campaign_duration_days': 14,
            'best_performing_template': 'cold_outreach',
            'monthly_stats': {
                'emails_sent': 15,
                'responses': 4,
                'connections': 2
            }
        }
    
    def _generate_campaign_insights(self, analytics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights and recommendations based on campaign analytics"""
        insights = []
        
        # Response rate insights
        response_rate = analytics.get('response_rate', analytics.get('overall_response_rate', 0))
        if response_rate > 25:
            insights.append({
                'type': 'positive',
                'title': 'Excellent Response Rate',
                'description': f'Your {response_rate:.1f}% response rate is above industry average (15-20%)',
                'recommendation': 'Continue using similar messaging and targeting strategies'
            })
        elif response_rate < 15:
            insights.append({
                'type': 'improvement',
                'title': 'Low Response Rate',
                'description': f'Your {response_rate:.1f}% response rate could be improved',
                'recommendation': 'Consider personalizing messages more or adjusting your target audience'
            })
        
        # Campaign progress insights
        progress = analytics.get('progress', 0)
        if progress > 0 and progress < 100:
            emails_remaining = analytics.get('emails_remaining', 0)
            insights.append({
                'type': 'status',
                'title': 'Campaign in Progress',
                'description': f'Campaign is {progress:.1f}% complete with {emails_remaining} emails remaining',
                'recommendation': 'Monitor response patterns to optimize remaining outreach'
            })
        
        # Success rate insights
        success_rate = analytics.get('success_rate', 0)
        if success_rate < 90:
            insights.append({
                'type': 'technical',
                'title': 'Email Delivery Issues',
                'description': f'Only {success_rate:.1f}% of emails were successfully delivered',
                'recommendation': 'Check email configuration and consider using a different sending method'
            })
        
        return insights  
  
    # Abstract method implementations required by BaseAgent
    
    async def _process_request_impl(self, user_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of request processing for networking
        """
        try:
            task_type = user_input.get("task_type", "generate_outreach")
            user_id = user_input.get("user_id") or context.get("user_id")
            
            if task_type == "generate_outreach":
                contact_info = user_input.get("contact_info", {})
                message_type = user_input.get("message_type", "introduction")
                
                outreach_result = await self.generate_outreach_message(
                    contact_info=contact_info,
                    message_type=message_type,
                    user_context=context
                )
                
                return {
                    "success": True,
                    "data": outreach_result,
                    "recommendations": [
                        {
                            "type": "outreach_message",
                            "description": "Personalized outreach message generated",
                            "action": "review_and_send",
                            "priority": "high"
                        }
                    ],
                    "metadata": {
                        "message_type": message_type,
                        "generation_timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            elif task_type == "discover_contacts":
                company = user_input.get("company", "")
                role = user_input.get("role", "")
                
                contacts = await self.discover_contacts(company=company, role=role)
                
                return {
                    "success": True,
                    "data": {"contacts": contacts},
                    "recommendations": [
                        {
                            "type": "contact_discovery",
                            "description": f"Found {len(contacts)} potential contacts",
                            "action": "review_contacts",
                            "priority": "medium"
                        }
                    ],
                    "metadata": {
                        "company": company,
                        "role": role,
                        "discovery_timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            elif task_type == "create_campaign":
                campaign_data = user_input.get("campaign_data", {})
                
                campaign = await self.create_networking_campaign(campaign_data)
                
                return {
                    "success": True,
                    "data": campaign,
                    "recommendations": [
                        {
                            "type": "networking_campaign",
                            "description": "Networking campaign created successfully",
                            "action": "start_campaign",
                            "priority": "high"
                        }
                    ],
                    "metadata": {
                        "campaign_id": campaign.get("id"),
                        "creation_timestamp": datetime.utcnow().isoformat()
                    }
                }
            
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            logger.error(f"Error in _process_request_impl: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "recommendations": [],
                "metadata": {"error_timestamp": datetime.utcnow().isoformat()}
            }
    
    async def _get_recommendations_impl(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Implementation of recommendations generation for networking
        """
        try:
            recommendations = []
            
            # Generate networking recommendations based on user profile
            target_companies = user_profile.get("target_companies", [])
            target_role = user_profile.get("target_role", "")
            current_network_size = user_profile.get("network_size", 0)
            
            if target_companies:
                for company in target_companies[:3]:  # Top 3 companies
                    recommendations.append({
                        "type": "company_networking",
                        "description": f"Connect with professionals at {company}",
                        "action": "discover_contacts",
                        "priority": "high",
                        "metadata": {
                            "company": company,
                            "target_role": target_role
                        }
                    })
            
            if current_network_size < 50:
                recommendations.append({
                    "type": "network_expansion",
                    "description": "Expand your professional network to increase opportunities",
                    "action": "start_networking_campaign",
                    "priority": "medium",
                    "metadata": {
                        "current_size": current_network_size,
                        "target_size": 100
                    }
                })
            
            if target_role:
                recommendations.append({
                    "type": "role_specific_networking",
                    "description": f"Connect with other {target_role} professionals for insights",
                    "action": "find_role_contacts",
                    "priority": "medium",
                    "metadata": {
                        "target_role": target_role
                    }
                })
            
            return recommendations
                
        except Exception as e:
            logger.error(f"Error in _get_recommendations_impl: {str(e)}")
            return []