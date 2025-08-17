"""
Contact Discovery and Web Scraping Service
"""
import asyncio
import aiohttp
import re
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ContactScraper:
    """Service for discovering contacts through web scraping"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def discover_company_contacts(self, company_name: str, company_domain: str = None) -> List[Dict[str, Any]]:
        """
        Discover contacts at a specific company
        
        Args:
            company_name: Name of the company
            company_domain: Company website domain
            
        Returns:
            List of discovered contacts
        """
        contacts = []
        
        try:
            # Try multiple discovery methods
            if company_domain:
                # Method 1: Company website team/about pages
                website_contacts = await self._scrape_company_website(company_domain)
                contacts.extend(website_contacts)
                
            # Method 2: LinkedIn company page (simulated - would need LinkedIn API)
            linkedin_contacts = await self._discover_linkedin_contacts(company_name)
            contacts.extend(linkedin_contacts)
            
            # Method 3: GitHub organization members (if tech company)
            github_contacts = await self._discover_github_contacts(company_name)
            contacts.extend(github_contacts)
            
            # Deduplicate contacts
            contacts = self._deduplicate_contacts(contacts)
            
            logger.info(f"Discovered {len(contacts)} contacts for {company_name}")
            return contacts
            
        except Exception as e:
            logger.error(f"Error discovering contacts for {company_name}: {str(e)}")
            return []
    
    async def _scrape_company_website(self, domain: str) -> List[Dict[str, Any]]:
        """Scrape company website for team/contact information"""
        contacts = []
        
        try:
            # Common team/about page URLs
            team_urls = [
                f"https://{domain}/team",
                f"https://{domain}/about",
                f"https://{domain}/about-us",
                f"https://{domain}/leadership",
                f"https://{domain}/management",
                f"https://{domain}/people",
                f"https://{domain}/our-team"
            ]
            
            for url in team_urls:
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            page_contacts = self._extract_contacts_from_html(html, url)
                            contacts.extend(page_contacts)
                            
                            # Small delay to be respectful
                            await asyncio.sleep(1)
                            
                except Exception as e:
                    logger.debug(f"Failed to scrape {url}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping company website {domain}: {str(e)}")
            
        return contacts
    
    def _extract_contacts_from_html(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """Extract contact information from HTML content"""
        contacts = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for common patterns in team pages
            # Pattern 1: Team member cards/sections
            team_sections = soup.find_all(['div', 'section'], class_=re.compile(r'team|member|person|staff|employee', re.I))
            
            for section in team_sections:
                contact = self._extract_contact_from_section(section, source_url)
                if contact:
                    contacts.append(contact)
            
            # Pattern 2: Email addresses in text
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, html)
            
            for email in emails:
                # Skip common non-personal emails
                if not any(skip in email.lower() for skip in ['info@', 'contact@', 'support@', 'hello@', 'admin@']):
                    contact = {
                        'contact_id': str(uuid.uuid4()),
                        'email': email,
                        'discovery_source': 'company_website',
                        'discovery_method': 'email_extraction',
                        'source_url': source_url,
                        'full_name': self._extract_name_from_email(email)
                    }
                    contacts.append(contact)
                    
        except Exception as e:
            logger.error(f"Error extracting contacts from HTML: {str(e)}")
            
        return contacts
    
    def _extract_contact_from_section(self, section, source_url: str) -> Optional[Dict[str, Any]]:
        """Extract contact information from a team member section"""
        try:
            contact = {
                'contact_id': str(uuid.uuid4()),
                'discovery_source': 'company_website',
                'discovery_method': 'team_page_scraping',
                'source_url': source_url
            }
            
            # Extract name
            name_elem = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or section.find(class_=re.compile(r'name', re.I))
            if name_elem:
                contact['full_name'] = name_elem.get_text().strip()
                name_parts = contact['full_name'].split()
                if len(name_parts) >= 2:
                    contact['first_name'] = name_parts[0]
                    contact['last_name'] = ' '.join(name_parts[1:])
            
            # Extract title/role
            title_elem = section.find(class_=re.compile(r'title|role|position|job', re.I))
            if title_elem:
                contact['current_title'] = title_elem.get_text().strip()
            
            # Extract email
            email_elem = section.find('a', href=re.compile(r'mailto:', re.I))
            if email_elem:
                contact['email'] = email_elem.get('href').replace('mailto:', '')
            
            # Extract LinkedIn
            linkedin_elem = section.find('a', href=re.compile(r'linkedin\.com', re.I))
            if linkedin_elem:
                contact['linkedin_url'] = linkedin_elem.get('href')
            
            # Only return if we have at least a name or email
            if contact.get('full_name') or contact.get('email'):
                return contact
                
        except Exception as e:
            logger.debug(f"Error extracting contact from section: {str(e)}")
            
        return None
    
    def _extract_name_from_email(self, email: str) -> str:
        """Extract likely name from email address"""
        try:
            local_part = email.split('@')[0]
            # Remove numbers and common separators
            name_part = re.sub(r'[0-9._-]', ' ', local_part)
            # Capitalize words
            return ' '.join(word.capitalize() for word in name_part.split() if len(word) > 1)
        except:
            return ""
    
    async def _discover_linkedin_contacts(self, company_name: str) -> List[Dict[str, Any]]:
        """
        Discover LinkedIn contacts (simulated - would need LinkedIn API)
        This is a placeholder for LinkedIn integration
        """
        # In a real implementation, this would use LinkedIn's API
        # For now, return simulated data structure
        return []
    
    async def _discover_github_contacts(self, company_name: str) -> List[Dict[str, Any]]:
        """Discover contacts through GitHub organization members"""
        contacts = []
        
        try:
            # Try to find GitHub organization
            github_org = await self._find_github_organization(company_name)
            if not github_org:
                return contacts
            
            # Get organization members (public API)
            members_url = f"https://api.github.com/orgs/{github_org}/members"
            
            async with self.session.get(members_url) as response:
                if response.status == 200:
                    members = await response.json()
                    
                    for member in members[:20]:  # Limit to first 20 members
                        # Get detailed user info
                        user_url = member.get('url')
                        if user_url:
                            contact = await self._get_github_user_details(user_url, company_name)
                            if contact:
                                contacts.append(contact)
                                
                            # Rate limiting
                            await asyncio.sleep(0.5)
                            
        except Exception as e:
            logger.error(f"Error discovering GitHub contacts: {str(e)}")
            
        return contacts
    
    async def _find_github_organization(self, company_name: str) -> Optional[str]:
        """Find GitHub organization name for a company"""
        try:
            # Search for organization
            search_url = f"https://api.github.com/search/users?q={company_name}+type:org"
            
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get('items', [])
                    
                    if items:
                        # Return the first match
                        return items[0].get('login')
                        
        except Exception as e:
            logger.debug(f"Error finding GitHub organization: {str(e)}")
            
        return None
    
    async def _get_github_user_details(self, user_url: str, company_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a GitHub user"""
        try:
            async with self.session.get(user_url) as response:
                if response.status == 200:
                    user_data = await response.json()
                    
                    contact = {
                        'contact_id': str(uuid.uuid4()),
                        'full_name': user_data.get('name', ''),
                        'github_url': user_data.get('html_url'),
                        'location': user_data.get('location', ''),
                        'current_company': company_name,
                        'discovery_source': 'github',
                        'discovery_method': 'organization_members',
                        'source_url': user_data.get('html_url')
                    }
                    
                    # Extract email if public
                    if user_data.get('email'):
                        contact['email'] = user_data['email']
                    
                    # Extract personal website
                    if user_data.get('blog'):
                        contact['personal_website'] = user_data['blog']
                    
                    return contact
                    
        except Exception as e:
            logger.debug(f"Error getting GitHub user details: {str(e)}")
            
        return None
    
    def _deduplicate_contacts(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate contacts based on email or name"""
        seen = set()
        unique_contacts = []
        
        for contact in contacts:
            # Create a key for deduplication
            key_parts = []
            if contact.get('email'):
                key_parts.append(contact['email'].lower())
            if contact.get('full_name'):
                key_parts.append(contact['full_name'].lower())
            
            if key_parts:
                key = '|'.join(key_parts)
                if key not in seen:
                    seen.add(key)
                    unique_contacts.append(contact)
        
        return unique_contacts


class ContactScorer:
    """Service for scoring contact relevance"""
    
    def __init__(self, watsonx_client=None):
        self.watsonx = watsonx_client
    
    async def score_contact_relevance(self, contact: Dict[str, Any], user_profile: Dict[str, Any], 
                                    target_role: str = None) -> float:
        """
        Score how relevant a contact is for the user's career goals
        
        Args:
            contact: Contact information
            user_profile: User's profile and career goals
            target_role: Specific role the user is targeting
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        try:
            score = 0.0
            
            # Base scoring factors
            factors = {
                'title_relevance': 0.0,
                'company_relevance': 0.0,
                'seniority_match': 0.0,
                'industry_match': 0.0,
                'location_proximity': 0.0
            }
            
            # Score title relevance
            if contact.get('current_title') and target_role:
                factors['title_relevance'] = self._score_title_similarity(
                    contact['current_title'], target_role
                )
            
            # Score company relevance
            user_target_companies = user_profile.get('job_preferences', {}).get('target_companies', [])
            if contact.get('current_company') and user_target_companies:
                if contact['current_company'] in user_target_companies:
                    factors['company_relevance'] = 1.0
                else:
                    factors['company_relevance'] = 0.3  # Still valuable for networking
            
            # Score seniority match
            if contact.get('seniority_level'):
                factors['seniority_match'] = self._score_seniority_relevance(
                    contact['seniority_level'], user_profile
                )
            
            # Score industry match
            user_industry = user_profile.get('industry')
            if user_industry and contact.get('current_company'):
                # This would ideally use a company-to-industry mapping
                factors['industry_match'] = 0.5  # Placeholder
            
            # Score location proximity
            user_location = user_profile.get('location')
            if user_location and contact.get('location'):
                factors['location_proximity'] = self._score_location_proximity(
                    user_location, contact['location']
                )
            
            # Calculate weighted score
            weights = {
                'title_relevance': 0.3,
                'company_relevance': 0.25,
                'seniority_match': 0.2,
                'industry_match': 0.15,
                'location_proximity': 0.1
            }
            
            score = sum(factors[factor] * weights[factor] for factor in factors)
            
            # Bonus for having contact information
            if contact.get('email'):
                score += 0.1
            if contact.get('linkedin_url'):
                score += 0.05
            
            return min(score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error scoring contact relevance: {str(e)}")
            return 0.0
    
    def _score_title_similarity(self, contact_title: str, target_role: str) -> float:
        """Score similarity between contact title and target role"""
        try:
            # Simple keyword-based similarity
            contact_words = set(contact_title.lower().split())
            target_words = set(target_role.lower().split())
            
            if not contact_words or not target_words:
                return 0.0
            
            intersection = contact_words.intersection(target_words)
            union = contact_words.union(target_words)
            
            return len(intersection) / len(union) if union else 0.0
            
        except:
            return 0.0
    
    def _score_seniority_relevance(self, contact_seniority: str, user_profile: Dict[str, Any]) -> float:
        """Score how relevant the contact's seniority is for networking"""
        try:
            user_experience = user_profile.get('years_experience', 0)
            
            # Map seniority levels to experience ranges
            seniority_map = {
                'entry': (0, 2),
                'mid': (2, 5),
                'senior': (5, 10),
                'executive': (10, 20),
                'c-level': (15, 50)
            }
            
            contact_range = seniority_map.get(contact_seniority.lower(), (0, 0))
            
            # Higher seniority contacts are generally more valuable for networking
            if contact_seniority.lower() in ['senior', 'executive', 'c-level']:
                return 0.8
            elif contact_seniority.lower() == 'mid':
                return 0.6
            else:
                return 0.4
                
        except:
            return 0.5
    
    def _score_location_proximity(self, user_location: str, contact_location: str) -> float:
        """Score location proximity (simplified)"""
        try:
            if user_location.lower() == contact_location.lower():
                return 1.0
            
            # Check if same city/state/country (simplified)
            user_parts = user_location.lower().split(',')
            contact_parts = contact_location.lower().split(',')
            
            common_parts = set(part.strip() for part in user_parts).intersection(
                set(part.strip() for part in contact_parts)
            )
            
            if common_parts:
                return 0.7
            
            return 0.3  # Different locations but still valuable
            
        except:
            return 0.5