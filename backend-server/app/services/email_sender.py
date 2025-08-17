"""
Email Sending Service with Delivery and Open Rate Tracking
"""
import asyncio
import smtplib
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import aiosmtplib
import base64
import json

from ..models.networking import ContactInteraction
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailTracker:
    """Service for tracking email delivery and open rates"""
    
    def __init__(self):
        self.tracking_pixels = {}
        self.tracking_links = {}
    
    def generate_tracking_pixel(self, interaction_id: str) -> str:
        """Generate a tracking pixel for email open tracking"""
        tracking_id = str(uuid.uuid4())
        self.tracking_pixels[tracking_id] = {
            'interaction_id': interaction_id,
            'created_at': datetime.utcnow()
        }
        
        # Create tracking pixel URL
        pixel_url = f"{settings.BASE_URL}/api/v1/tracking/pixel/{tracking_id}.png"
        
        # HTML for invisible tracking pixel
        pixel_html = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" alt="" />'
        
        return pixel_html
    
    def generate_tracking_link(self, original_url: str, interaction_id: str) -> str:
        """Generate a tracking link for click tracking"""
        tracking_id = str(uuid.uuid4())
        self.tracking_links[tracking_id] = {
            'interaction_id': interaction_id,
            'original_url': original_url,
            'created_at': datetime.utcnow()
        }
        
        return f"{settings.BASE_URL}/api/v1/tracking/link/{tracking_id}"
    
    def wrap_links_with_tracking(self, html_content: str, interaction_id: str) -> str:
        """Wrap all links in the email with tracking"""
        import re
        
        # Find all links in the HTML
        link_pattern = r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"'
        
        def replace_link(match):
            original_url = match.group(1)
            if original_url.startswith('http'):
                tracking_url = self.generate_tracking_link(original_url, interaction_id)
                return match.group(0).replace(original_url, tracking_url)
            return match.group(0)
        
        return re.sub(link_pattern, replace_link, html_content)
    
    async def record_email_opened(self, tracking_id: str) -> bool:
        """Record that an email was opened"""
        try:
            tracking_info = self.tracking_pixels.get(tracking_id)
            if not tracking_info:
                return False
            
            interaction_id = tracking_info['interaction_id']
            
            # Update interaction record (in real implementation, this would update the database)
            logger.info(f"Email opened - Interaction ID: {interaction_id}, Tracking ID: {tracking_id}")
            
            # Store open event
            open_event = {
                'interaction_id': interaction_id,
                'tracking_id': tracking_id,
                'opened_at': datetime.utcnow(),
                'event_type': 'email_opened'
            }
            
            # In real implementation, save to database
            return True
            
        except Exception as e:
            logger.error(f"Error recording email open: {str(e)}")
            return False
    
    async def record_link_clicked(self, tracking_id: str) -> Optional[str]:
        """Record that a link was clicked and return the original URL"""
        try:
            tracking_info = self.tracking_links.get(tracking_id)
            if not tracking_info:
                return None
            
            interaction_id = tracking_info['interaction_id']
            original_url = tracking_info['original_url']
            
            # Record click event
            logger.info(f"Link clicked - Interaction ID: {interaction_id}, URL: {original_url}")
            
            click_event = {
                'interaction_id': interaction_id,
                'tracking_id': tracking_id,
                'original_url': original_url,
                'clicked_at': datetime.utcnow(),
                'event_type': 'link_clicked'
            }
            
            # In real implementation, save to database
            return original_url
            
        except Exception as e:
            logger.error(f"Error recording link click: {str(e)}")
            return None


class EmailSender:
    """Service for sending emails with tracking capabilities"""
    
    def __init__(self):
        self.tracker = EmailTracker()
        self.smtp_config = {
            'hostname': settings.SMTP_HOST,
            'port': settings.SMTP_PORT,
            'username': settings.SMTP_USERNAME,
            'password': settings.SMTP_PASSWORD,
            'use_tls': settings.SMTP_USE_TLS
        }
    
    async def send_email(self,
                        to_email: str,
                        subject: str,
                        body: str,
                        from_email: str = None,
                        from_name: str = None,
                        interaction_id: str = None,
                        enable_tracking: bool = True) -> Dict[str, Any]:
        """
        Send an email with optional tracking
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (can be HTML or plain text)
            from_email: Sender email address
            from_name: Sender name
            interaction_id: ID for tracking this interaction
            enable_tracking: Whether to enable open/click tracking
            
        Returns:
            Result of email sending operation
        """
        try:
            if not interaction_id:
                interaction_id = str(uuid.uuid4())
            
            # Prepare email content
            from_email = from_email or settings.DEFAULT_FROM_EMAIL
            from_name = from_name or settings.DEFAULT_FROM_NAME
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>" if from_name else from_email
            msg['To'] = to_email
            msg['Message-ID'] = f"<{interaction_id}@{settings.DOMAIN}>"
            
            # Prepare HTML and text versions
            html_body = self._ensure_html_format(body)
            text_body = self._html_to_text(html_body)
            
            # Add tracking if enabled
            if enable_tracking:
                # Add tracking pixel
                tracking_pixel = self.tracker.generate_tracking_pixel(interaction_id)
                html_body = html_body.replace('</body>', f'{tracking_pixel}</body>')
                
                # Wrap links with tracking
                html_body = self.tracker.wrap_links_with_tracking(html_body, interaction_id)
            
            # Attach text and HTML versions
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            result = await self._send_smtp_email(msg, to_email)
            
            # Record sending attempt
            await self._record_email_sent(interaction_id, to_email, subject, result)
            
            return {
                'success': result['success'],
                'interaction_id': interaction_id,
                'message_id': result.get('message_id'),
                'error': result.get('error'),
                'sent_at': datetime.utcnow().isoformat(),
                'tracking_enabled': enable_tracking
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'interaction_id': interaction_id
            }
    
    async def send_bulk_emails(self,
                              emails: List[Dict[str, Any]],
                              batch_size: int = 10,
                              delay_between_batches: int = 60) -> List[Dict[str, Any]]:
        """
        Send multiple emails in batches with rate limiting
        
        Args:
            emails: List of email data dictionaries
            batch_size: Number of emails to send per batch
            delay_between_batches: Delay in seconds between batches
            
        Returns:
            List of sending results
        """
        try:
            results = []
            
            for i in range(0, len(emails), batch_size):
                batch = emails[i:i + batch_size]
                batch_tasks = []
                
                logger.info(f"Sending batch {i//batch_size + 1} of {len(batch)} emails")
                
                for email_data in batch:
                    task = self.send_email(
                        to_email=email_data['to_email'],
                        subject=email_data['subject'],
                        body=email_data['body'],
                        from_email=email_data.get('from_email'),
                        from_name=email_data.get('from_name'),
                        interaction_id=email_data.get('interaction_id'),
                        enable_tracking=email_data.get('enable_tracking', True)
                    )
                    batch_tasks.append(task)
                
                # Send batch concurrently
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for email_data, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        result = {
                            'success': False,
                            'error': str(result),
                            'to_email': email_data['to_email']
                        }
                    
                    result['to_email'] = email_data['to_email']
                    results.append(result)
                
                # Delay between batches (except for the last batch)
                if i + batch_size < len(emails):
                    logger.info(f"Waiting {delay_between_batches} seconds before next batch")
                    await asyncio.sleep(delay_between_batches)
            
            return results
            
        except Exception as e:
            logger.error(f"Error sending bulk emails: {str(e)}")
            return []
    
    async def _send_smtp_email(self, msg: MIMEMultipart, to_email: str) -> Dict[str, Any]:
        """Send email via SMTP"""
        try:
            # Use aiosmtplib for async SMTP
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_config['hostname'],
                port=self.smtp_config['port'],
                username=self.smtp_config['username'],
                password=self.smtp_config['password'],
                use_tls=self.smtp_config['use_tls']
            )
            
            return {
                'success': True,
                'message_id': msg['Message-ID'],
                'delivery_status': 'sent'
            }
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'delivery_status': 'failed'
            }
    
    def _ensure_html_format(self, body: str) -> str:
        """Ensure email body is in HTML format"""
        if not body.strip().startswith('<'):
            # Convert plain text to HTML
            body_with_breaks = body.replace('\n', '<br>')
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                {body_with_breaks}
            </body>
            </html>
            """
            return html_body
        return body
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text()
        except ImportError:
            # Fallback: simple HTML tag removal
            import re
            text = re.sub('<[^<]+?>', '', html)
            return text.strip()
    
    async def _record_email_sent(self,
                                interaction_id: str,
                                to_email: str,
                                subject: str,
                                send_result: Dict[str, Any]) -> None:
        """Record email sending attempt"""
        try:
            # In real implementation, this would save to database
            record = {
                'interaction_id': interaction_id,
                'to_email': to_email,
                'subject': subject,
                'sent_at': datetime.utcnow(),
                'success': send_result['success'],
                'message_id': send_result.get('message_id'),
                'error': send_result.get('error'),
                'delivery_status': send_result.get('delivery_status', 'unknown')
            }
            
            logger.info(f"Email sent record: {record}")
            
        except Exception as e:
            logger.error(f"Error recording email sent: {str(e)}")


class EmailCampaignManager:
    """Manager for email campaigns with scheduling and tracking"""
    
    def __init__(self):
        self.email_sender = EmailSender()
        self.active_campaigns = {}
    
    async def start_campaign(self,
                           campaign_id: str,
                           emails: List[Dict[str, Any]],
                           schedule_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start an email campaign with scheduling
        
        Args:
            campaign_id: Unique campaign identifier
            emails: List of emails to send
            schedule_config: Configuration for scheduling (daily_limit, start_time, etc.)
            
        Returns:
            Campaign start result
        """
        try:
            if campaign_id in self.active_campaigns:
                return {
                    'success': False,
                    'error': 'Campaign is already active'
                }
            
            # Validate schedule configuration
            daily_limit = schedule_config.get('daily_limit', 10)
            start_time = schedule_config.get('start_time', '09:00')
            end_time = schedule_config.get('end_time', '17:00')
            timezone = schedule_config.get('timezone', 'UTC')
            
            # Create campaign state
            campaign_state = {
                'campaign_id': campaign_id,
                'emails': emails,
                'schedule_config': schedule_config,
                'status': 'active',
                'emails_sent_today': 0,
                'total_emails_sent': 0,
                'last_sent_date': None,
                'started_at': datetime.utcnow(),
                'results': []
            }
            
            self.active_campaigns[campaign_id] = campaign_state
            
            # Start campaign processing (in background)
            asyncio.create_task(self._process_campaign(campaign_id))
            
            return {
                'success': True,
                'campaign_id': campaign_id,
                'status': 'active',
                'total_emails': len(emails),
                'daily_limit': daily_limit,
                'estimated_completion_days': max(1, len(emails) // daily_limit)
            }
            
        except Exception as e:
            logger.error(f"Error starting campaign: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Pause an active campaign"""
        try:
            if campaign_id not in self.active_campaigns:
                return {
                    'success': False,
                    'error': 'Campaign not found'
                }
            
            self.active_campaigns[campaign_id]['status'] = 'paused'
            
            return {
                'success': True,
                'campaign_id': campaign_id,
                'status': 'paused'
            }
            
        except Exception as e:
            logger.error(f"Error pausing campaign: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def resume_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Resume a paused campaign"""
        try:
            if campaign_id not in self.active_campaigns:
                return {
                    'success': False,
                    'error': 'Campaign not found'
                }
            
            campaign = self.active_campaigns[campaign_id]
            if campaign['status'] != 'paused':
                return {
                    'success': False,
                    'error': 'Campaign is not paused'
                }
            
            campaign['status'] = 'active'
            
            # Resume processing
            asyncio.create_task(self._process_campaign(campaign_id))
            
            return {
                'success': True,
                'campaign_id': campaign_id,
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Error resuming campaign: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_campaign_status(self, campaign_id: str) -> Dict[str, Any]:
        """Get current status of a campaign"""
        try:
            if campaign_id not in self.active_campaigns:
                return {
                    'success': False,
                    'error': 'Campaign not found'
                }
            
            campaign = self.active_campaigns[campaign_id]
            
            # Calculate progress
            total_emails = len(campaign['emails'])
            sent_count = campaign['total_emails_sent']
            progress = (sent_count / total_emails) * 100 if total_emails > 0 else 0
            
            # Calculate success rate
            successful_sends = sum(1 for result in campaign['results'] if result.get('success'))
            success_rate = (successful_sends / sent_count) * 100 if sent_count > 0 else 0
            
            return {
                'success': True,
                'campaign_id': campaign_id,
                'status': campaign['status'],
                'progress': round(progress, 2),
                'total_emails': total_emails,
                'emails_sent': sent_count,
                'emails_remaining': total_emails - sent_count,
                'success_rate': round(success_rate, 2),
                'emails_sent_today': campaign['emails_sent_today'],
                'daily_limit': campaign['schedule_config'].get('daily_limit', 10),
                'started_at': campaign['started_at'].isoformat(),
                'last_sent_date': campaign['last_sent_date'].isoformat() if campaign['last_sent_date'] else None
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _process_campaign(self, campaign_id: str) -> None:
        """Process campaign emails according to schedule"""
        try:
            while campaign_id in self.active_campaigns:
                campaign = self.active_campaigns[campaign_id]
                
                if campaign['status'] != 'active':
                    await asyncio.sleep(60)  # Check every minute
                    continue
                
                # Check if we've sent all emails
                if campaign['total_emails_sent'] >= len(campaign['emails']):
                    campaign['status'] = 'completed'
                    logger.info(f"Campaign {campaign_id} completed")
                    break
                
                # Check daily limit
                today = datetime.utcnow().date()
                if campaign['last_sent_date'] and campaign['last_sent_date'].date() == today:
                    if campaign['emails_sent_today'] >= campaign['schedule_config'].get('daily_limit', 10):
                        # Wait until tomorrow
                        await asyncio.sleep(3600)  # Check every hour
                        continue
                else:
                    # Reset daily counter for new day
                    campaign['emails_sent_today'] = 0
                
                # Check if we're within sending hours
                current_hour = datetime.utcnow().hour
                start_hour = int(campaign['schedule_config'].get('start_time', '09:00').split(':')[0])
                end_hour = int(campaign['schedule_config'].get('end_time', '17:00').split(':')[0])
                
                if not (start_hour <= current_hour < end_hour):
                    await asyncio.sleep(1800)  # Check every 30 minutes
                    continue
                
                # Send next email
                next_email_index = campaign['total_emails_sent']
                if next_email_index < len(campaign['emails']):
                    email_data = campaign['emails'][next_email_index]
                    
                    result = await self.email_sender.send_email(
                        to_email=email_data['to_email'],
                        subject=email_data['subject'],
                        body=email_data['body'],
                        from_email=email_data.get('from_email'),
                        from_name=email_data.get('from_name'),
                        interaction_id=email_data.get('interaction_id'),
                        enable_tracking=email_data.get('enable_tracking', True)
                    )
                    
                    # Update campaign state
                    campaign['results'].append(result)
                    campaign['total_emails_sent'] += 1
                    campaign['emails_sent_today'] += 1
                    campaign['last_sent_date'] = datetime.utcnow()
                    
                    logger.info(f"Campaign {campaign_id}: Sent email {next_email_index + 1}/{len(campaign['emails'])}")
                    
                    # Wait between emails (to avoid being flagged as spam)
                    await asyncio.sleep(300)  # 5 minutes between emails
                
        except Exception as e:
            logger.error(f"Error processing campaign {campaign_id}: {str(e)}")
            if campaign_id in self.active_campaigns:
                self.active_campaigns[campaign_id]['status'] = 'error'
                self.active_campaigns[campaign_id]['error'] = str(e)


# Global instances
email_sender = EmailSender()
email_campaign_manager = EmailCampaignManager()
email_tracker = EmailTracker()