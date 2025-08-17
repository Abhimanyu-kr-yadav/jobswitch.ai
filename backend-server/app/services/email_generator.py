"""
Email Template Generation Service using WatsonX.ai
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..integrations.watsonx import WatsonXClient

logger = logging.getLogger(__name__)


class EmailTemplateGenerator:
    """Service for generating personalized email templates using AI"""
    
    def __init__(self, watsonx_client: WatsonXClient = None):
        self.watsonx = watsonx_client
        self.template_cache = {}
    
    async def generate_personalized_template(self, 
                                           user_profile: Dict[str, Any],
                                           contact: Dict[str, Any],
                                           campaign_context: Dict[str, Any],
                                           template_type: str = "cold_outreach") -> Dict[str, Any]:
        """
        Generate a personalized email template for a specific contact
        
        Args:
            user_profile: User's profile information
            contact: Target contact information
            campaign_context: Campaign details and context
            template_type: Type of email template to generate
            
        Returns:
            Generated email template with subject and body
        """
        try:
            # Create context for AI generation
            generation_context = self._build_generation_context(
                user_profile, contact, campaign_context, template_type
            )
            
            # Generate email using WatsonX.ai
            if self.watsonx:
                template = await self._generate_with_ai(generation_context, template_type)
            else:
                template = self._get_fallback_template(generation_context, template_type)
            
            # Post-process and validate template
            processed_template = self._process_template(template, generation_context)
            
            return {
                'success': True,
                'template': processed_template,
                'context': generation_context,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating email template: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'template': self._get_fallback_template(
                    self._build_generation_context(user_profile, contact, campaign_context, template_type),
                    template_type
                )
            }
    
    async def generate_follow_up_template(self,
                                        original_email: Dict[str, Any],
                                        user_profile: Dict[str, Any],
                                        contact: Dict[str, Any],
                                        follow_up_reason: str = "no_response") -> Dict[str, Any]:
        """
        Generate a follow-up email template based on previous interaction
        
        Args:
            original_email: Previous email sent to the contact
            user_profile: User's profile information
            contact: Target contact information
            follow_up_reason: Reason for follow-up
            
        Returns:
            Generated follow-up email template
        """
        try:
            context = {
                'user_profile': user_profile,
                'contact': contact,
                'original_email': original_email,
                'follow_up_reason': follow_up_reason,
                'template_type': 'follow_up'
            }
            
            if self.watsonx:
                template = await self._generate_follow_up_with_ai(context)
            else:
                template = self._get_fallback_follow_up_template(context)
            
            processed_template = self._process_template(template, context)
            
            return {
                'success': True,
                'template': processed_template,
                'context': context,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating follow-up template: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'template': self._get_fallback_follow_up_template(context)
            }
    
    async def generate_bulk_templates(self,
                                    user_profile: Dict[str, Any],
                                    contacts: List[Dict[str, Any]],
                                    campaign_context: Dict[str, Any],
                                    template_type: str = "cold_outreach") -> List[Dict[str, Any]]:
        """
        Generate personalized templates for multiple contacts
        
        Args:
            user_profile: User's profile information
            contacts: List of target contacts
            campaign_context: Campaign details and context
            template_type: Type of email template to generate
            
        Returns:
            List of generated email templates
        """
        try:
            templates = []
            
            # Process contacts in batches to avoid overwhelming the AI service
            batch_size = 5
            for i in range(0, len(contacts), batch_size):
                batch = contacts[i:i + batch_size]
                batch_tasks = []
                
                for contact in batch:
                    task = self.generate_personalized_template(
                        user_profile, contact, campaign_context, template_type
                    )
                    batch_tasks.append(task)
                
                # Process batch concurrently
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for contact, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Error generating template for {contact.get('full_name', 'Unknown')}: {str(result)}")
                        # Add fallback template
                        result = {
                            'success': False,
                            'error': str(result),
                            'template': self._get_fallback_template(
                                self._build_generation_context(user_profile, contact, campaign_context, template_type),
                                template_type
                            )
                        }
                    
                    result['contact_id'] = contact.get('contact_id')
                    result['contact_name'] = contact.get('full_name')
                    templates.append(result)
                
                # Add small delay between batches
                if i + batch_size < len(contacts):
                    await asyncio.sleep(1)
            
            return templates
            
        except Exception as e:
            logger.error(f"Error generating bulk templates: {str(e)}")
            return []
    
    def _build_generation_context(self,
                                user_profile: Dict[str, Any],
                                contact: Dict[str, Any],
                                campaign_context: Dict[str, Any],
                                template_type: str) -> Dict[str, Any]:
        """Build context for AI template generation"""
        return {
            'user': {
                'name': f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip(),
                'title': user_profile.get('current_title', 'Professional'),
                'company': user_profile.get('current_company', ''),
                'industry': user_profile.get('industry', ''),
                'location': user_profile.get('location', ''),
                'skills': user_profile.get('skills', []),
                'experience_years': user_profile.get('experience_years', 0)
            },
            'contact': {
                'name': contact.get('full_name', contact.get('first_name', 'there')),
                'first_name': contact.get('first_name', ''),
                'title': contact.get('current_title', ''),
                'company': contact.get('current_company', ''),
                'department': contact.get('department', ''),
                'seniority_level': contact.get('seniority_level', ''),
                'location': contact.get('location', ''),
                'linkedin_url': contact.get('linkedin_url', '')
            },
            'campaign': {
                'name': campaign_context.get('name', ''),
                'target_company': campaign_context.get('target_company', ''),
                'target_role': campaign_context.get('target_role', ''),
                'campaign_type': campaign_context.get('campaign_type', ''),
                'objective': campaign_context.get('objective', 'networking'),
                'tone': campaign_context.get('tone', 'professional'),
                'call_to_action': campaign_context.get('call_to_action', 'connect')
            },
            'template_type': template_type,
            'personalization_level': campaign_context.get('personalization_level', 'medium')
        }
    
    async def _generate_with_ai(self, context: Dict[str, Any], template_type: str) -> Dict[str, Any]:
        """Generate email template using WatsonX.ai"""
        try:
            prompt = self._create_generation_prompt(context, template_type)
            
            # Generate email using WatsonX
            response = await self.watsonx.generate_text(
                prompt=prompt,
                max_tokens=500,
                temperature=0.7,
                stop_sequences=["---END---"]
            )
            
            generated_text = response.get('generated_text', '')
            
            # Parse the generated email
            parsed_email = self._parse_generated_email(generated_text)
            
            return parsed_email
            
        except Exception as e:
            logger.error(f"Error generating email with AI: {str(e)}")
            raise
    
    async def _generate_follow_up_with_ai(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate follow-up email using WatsonX.ai"""
        try:
            prompt = self._create_follow_up_prompt(context)
            
            response = await self.watsonx.generate_text(
                prompt=prompt,
                max_tokens=400,
                temperature=0.6,
                stop_sequences=["---END---"]
            )
            
            generated_text = response.get('generated_text', '')
            parsed_email = self._parse_generated_email(generated_text)
            
            return parsed_email
            
        except Exception as e:
            logger.error(f"Error generating follow-up email with AI: {str(e)}")
            raise
    
    def _create_generation_prompt(self, context: Dict[str, Any], template_type: str) -> str:
        """Create prompt for AI email generation"""
        user = context['user']
        contact = context['contact']
        campaign = context['campaign']
        
        base_prompt = f"""
        Generate a professional networking email for the following scenario:
        
        SENDER INFORMATION:
        - Name: {user['name']}
        - Title: {user['title']}
        - Company: {user['company']}
        - Industry: {user['industry']}
        - Location: {user['location']}
        
        RECIPIENT INFORMATION:
        - Name: {contact['name']}
        - Title: {contact['title']}
        - Company: {contact['company']}
        - Department: {contact['department']}
        - Seniority: {contact['seniority_level']}
        
        CAMPAIGN CONTEXT:
        - Objective: {campaign['objective']}
        - Target Company: {campaign['target_company']}
        - Target Role: {campaign['target_role']}
        - Tone: {campaign['tone']}
        - Call to Action: {campaign['call_to_action']}
        
        EMAIL TYPE: {template_type}
        PERSONALIZATION LEVEL: {context['personalization_level']}
        """
        
        if template_type == "cold_outreach":
            prompt = base_prompt + """
            
            Generate a cold outreach email that:
            1. Has a compelling, personalized subject line
            2. Opens with a genuine connection or shared interest
            3. Briefly introduces the sender and their background
            4. Explains the reason for reaching out
            5. Offers value or mutual benefit
            6. Includes a clear, low-pressure call to action
            7. Maintains a professional but friendly tone
            8. Is concise (under 150 words)
            
            Format the response as:
            SUBJECT: [subject line]
            
            BODY:
            [email body]
            
            ---END---
            """
        
        elif template_type == "referral_request":
            prompt = base_prompt + """
            
            Generate a referral request email that:
            1. Has a clear subject line about referral request
            2. Opens with appreciation for their time
            3. Briefly explains the sender's background and interest
            4. Specifically asks for a referral or introduction
            5. Explains why they're interested in the company/role
            6. Offers to provide more information if needed
            7. Thanks them in advance
            8. Is respectful and not pushy
            
            Format the response as:
            SUBJECT: [subject line]
            
            BODY:
            [email body]
            
            ---END---
            """
        
        elif template_type == "informational_interview":
            prompt = base_prompt + """
            
            Generate an informational interview request email that:
            1. Has a subject line about informational interview
            2. Opens with genuine interest in their career path
            3. Briefly introduces the sender and their goals
            4. Requests a brief informational interview
            5. Suggests specific topics to discuss
            6. Offers flexibility in timing and format
            7. Emphasizes learning, not job seeking
            8. Shows respect for their time
            
            Format the response as:
            SUBJECT: [subject line]
            
            BODY:
            [email body]
            
            ---END---
            """
        
        return prompt
    
    def _create_follow_up_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for follow-up email generation"""
        user = context['user_profile']
        contact = context['contact']
        original_email = context['original_email']
        reason = context['follow_up_reason']
        
        prompt = f"""
        Generate a professional follow-up email for the following scenario:
        
        ORIGINAL EMAIL CONTEXT:
        - Subject: {original_email.get('subject', '')}
        - Sent: {original_email.get('sent_at', '')}
        - Purpose: {original_email.get('purpose', 'networking')}
        
        FOLLOW-UP REASON: {reason}
        
        SENDER: {user.get('first_name', '')} {user.get('last_name', '')}
        RECIPIENT: {contact.get('full_name', '')}
        
        Generate a follow-up email that:
        1. References the previous email appropriately
        2. Provides additional value or context
        3. Maintains a professional and respectful tone
        4. Doesn't sound pushy or desperate
        5. Includes a clear but gentle call to action
        6. Is brief and to the point
        
        Format the response as:
        SUBJECT: [subject line]
        
        BODY:
        [email body]
        
        ---END---
        """
        
        return prompt
    
    def _parse_generated_email(self, generated_text: str) -> Dict[str, Any]:
        """Parse generated email text into subject and body"""
        try:
            lines = generated_text.strip().split('\n')
            subject = ""
            body_lines = []
            in_body = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('SUBJECT:'):
                    subject = line.replace('SUBJECT:', '').strip()
                elif line == 'BODY:':
                    in_body = True
                elif in_body and line and line != '---END---':
                    body_lines.append(line)
                elif line == '---END---':
                    break
            
            body = '\n'.join(body_lines).strip()
            
            # Fallback parsing if format is not followed
            if not subject or not body:
                # Try to extract subject from first line if it looks like a subject
                if lines and len(lines[0]) < 100 and not lines[0].startswith('Dear') and not lines[0].startswith('Hi'):
                    subject = lines[0].strip()
                    body = '\n'.join(lines[1:]).strip()
                else:
                    subject = "Connection Request"
                    body = generated_text.strip()
            
            return {
                'subject': subject,
                'body': body,
                'word_count': len(body.split()),
                'estimated_read_time': max(1, len(body.split()) // 200)  # Rough estimate
            }
            
        except Exception as e:
            logger.error(f"Error parsing generated email: {str(e)}")
            return {
                'subject': "Connection Request",
                'body': generated_text.strip(),
                'word_count': len(generated_text.split()),
                'estimated_read_time': 1
            }
    
    def _process_template(self, template: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process and validate the generated template"""
        try:
            # Add personalization placeholders if not present
            body = template.get('body', '')
            
            # Ensure key placeholders are present
            placeholders = {
                '{{contact_name}}': context['contact']['name'],
                '{{contact_first_name}}': context['contact']['first_name'],
                '{{contact_title}}': context['contact']['title'],
                '{{contact_company}}': context['contact']['company'],
                '{{user_name}}': context['user']['name'],
                '{{user_title}}': context['user']['title'],
                '{{user_company}}': context['user']['company']
            }
            
            # Replace placeholders with actual values for preview
            preview_body = body
            for placeholder, value in placeholders.items():
                if value:
                    preview_body = preview_body.replace(placeholder, value)
            
            # Validate email length and content
            word_count = len(body.split())
            if word_count > 200:
                logger.warning(f"Generated email is long ({word_count} words)")
            
            return {
                'subject': template.get('subject', ''),
                'body': body,
                'preview_body': preview_body,
                'placeholders': list(placeholders.keys()),
                'word_count': word_count,
                'estimated_read_time': template.get('estimated_read_time', 1),
                'quality_score': self._calculate_quality_score(template, context),
                'suggestions': self._generate_improvement_suggestions(template, context)
            }
            
        except Exception as e:
            logger.error(f"Error processing template: {str(e)}")
            return template
    
    def _calculate_quality_score(self, template: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate a quality score for the generated template"""
        score = 0.0
        
        subject = template.get('subject', '')
        body = template.get('body', '')
        
        # Subject line quality
        if subject:
            score += 0.2
            if len(subject) > 5 and len(subject) < 60:
                score += 0.1
            if context['contact']['name'].split()[0] in subject:
                score += 0.1
        
        # Body quality
        if body:
            score += 0.2
            word_count = len(body.split())
            if 50 <= word_count <= 150:
                score += 0.2
            elif word_count < 200:
                score += 0.1
        
        # Personalization
        contact_name = context['contact']['name']
        if contact_name and contact_name in body:
            score += 0.1
        
        # Professional tone indicators
        professional_words = ['professional', 'experience', 'opportunity', 'connect', 'discuss', 'learn']
        if any(word in body.lower() for word in professional_words):
            score += 0.1
        
        return min(1.0, score)
    
    def _generate_improvement_suggestions(self, template: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Generate suggestions for improving the email template"""
        suggestions = []
        
        subject = template.get('subject', '')
        body = template.get('body', '')
        word_count = len(body.split())
        
        # Subject line suggestions
        if not subject:
            suggestions.append("Add a compelling subject line")
        elif len(subject) > 60:
            suggestions.append("Consider shortening the subject line")
        
        # Body length suggestions
        if word_count > 150:
            suggestions.append("Consider making the email more concise")
        elif word_count < 50:
            suggestions.append("Consider adding more context or value proposition")
        
        # Personalization suggestions
        contact_name = context['contact']['name']
        if contact_name and contact_name not in body:
            suggestions.append("Consider adding the recipient's name for personalization")
        
        # Call to action suggestions
        cta_words = ['call', 'meeting', 'coffee', 'chat', 'discuss', 'connect']
        if not any(word in body.lower() for word in cta_words):
            suggestions.append("Consider adding a clear call to action")
        
        return suggestions
    
    def _get_fallback_template(self, context: Dict[str, Any], template_type: str) -> Dict[str, Any]:
        """Get fallback template when AI generation fails"""
        user = context['user']
        contact = context['contact']
        
        templates = {
            'cold_outreach': {
                'subject': f"Connection request from {user['name']}",
                'body': f"""Hi {{{{contact_name}}}},

I hope this message finds you well. I'm {user['name']}, a {user['title']} with a strong interest in {contact['company']} and the work you're doing as {contact['title']}.

I've been following {contact['company']}'s recent developments and am impressed by your team's innovative approach. I'd love to learn more about your experience and share some insights from my background in {user['industry']}.

Would you be open to a brief 15-minute conversation over coffee or a virtual call? I believe we could have a mutually beneficial discussion about industry trends and opportunities.

Thank you for your time, and I look forward to potentially connecting.

Best regards,
{user['name']}"""
            },
            'referral_request': {
                'subject': f"Referral request for {context['campaign']['target_role']} role",
                'body': f"""Hi {{{{contact_name}}}},

I hope you're doing well. I'm {user['name']}, a {user['title']} currently exploring opportunities in {context['campaign']['target_role']} roles.

I noticed you work at {contact['company']}, and I'm very interested in the company's mission and culture. Would you be willing to provide a referral or introduction for relevant opportunities?

I have {user['experience_years']} years of experience in {user['industry']} and believe I could contribute meaningfully to your team. I'd be happy to share my resume and discuss how my background aligns with your company's needs.

Thank you for considering my request. I understand referrals are valuable, and I appreciate any guidance you can provide.

Best regards,
{user['name']}"""
            },
            'informational_interview': {
                'subject': f"Informational interview request - {user['title']} seeking insights",
                'body': f"""Hi {{{{contact_name}}}},

I hope this message finds you well. I'm {user['name']}, a {user['title']} with a keen interest in {contact['title']} roles and career development.

I've been researching professionals in your field and was impressed by your background at {contact['company']}. Would you be open to a brief 20-minute informational interview to discuss your career journey and insights about the industry?

I'm particularly interested in learning about:
- Your path to {contact['title']}
- Key skills and experiences that have been valuable
- Industry trends and future opportunities
- Any advice for someone looking to grow in this field

I completely understand if your schedule doesn't permit, but I would greatly appreciate any insights you could share. I'm happy to work around your availability.

Thank you for your time and consideration.

Best regards,
{user['name']}"""
            }
        }
        
        template = templates.get(template_type, templates['cold_outreach'])
        
        return {
            'subject': template['subject'],
            'body': template['body'],
            'word_count': len(template['body'].split()),
            'estimated_read_time': 1,
            'is_fallback': True
        }
    
    def _get_fallback_follow_up_template(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback follow-up template"""
        user = context['user_profile']
        contact = context['contact']
        reason = context['follow_up_reason']
        
        if reason == "no_response":
            subject = "Following up on my previous message"
            body = f"""Hi {contact.get('full_name', 'there')},

I wanted to follow up on my previous message from last week. I understand you're likely very busy, so I thought I'd reach out once more.

I'm still very interested in connecting and learning about your experience at {contact.get('current_company', 'your company')}. If now isn't a good time, I completely understand.

If you'd prefer, I'm happy to connect on LinkedIn or schedule a brief call at your convenience.

Thank you for your time.

Best regards,
{user.get('first_name', '')} {user.get('last_name', '')}"""
        
        elif reason == "additional_value":
            subject = "Additional thoughts on our potential connection"
            body = f"""Hi {contact.get('full_name', 'there')},

I hope you're doing well. Following up on my previous message, I wanted to share an additional thought that might be of interest.

[Additional value or insight would go here]

I'd still love to connect and learn more about your work at {contact.get('current_company', 'your company')}. Please let me know if you'd be open to a brief conversation.

Best regards,
{user.get('first_name', '')} {user.get('last_name', '')}"""
        
        else:
            subject = "Following up on our connection"
            body = f"""Hi {contact.get('full_name', 'there')},

I hope this message finds you well. I wanted to follow up on my previous outreach and see if you might be interested in connecting.

I believe we could have a valuable conversation about our shared interests in the industry.

Please let me know if you'd be open to a brief chat.

Best regards,
{user.get('first_name', '')} {user.get('last_name', '')}"""
        
        return {
            'subject': subject,
            'body': body,
            'word_count': len(body.split()),
            'estimated_read_time': 1,
            'is_fallback': True
        }