"""
Job Board API Connectors
Integrations with various job boards for job discovery
"""
import uuid
import logging
import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import re

logger = logging.getLogger(__name__)


class BaseJobConnector(ABC):
    """
    Base class for job board connectors
    """
    
    def __init__(self, source_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.source_name = source_name
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.rate_limit_delay = 1.0  # seconds between requests
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def search_jobs(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for jobs based on criteria
        
        Args:
            criteria: Search criteria dictionary
            
        Returns:
            List of job dictionaries
        """
        pass
    
    @abstractmethod
    async def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific job
        
        Args:
            job_id: Job identifier
            
        Returns:
            Detailed job information
        """
        pass
    
    def _normalize_job_data(self, raw_job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize job data to standard format
        
        Args:
            raw_job_data: Raw job data from API
            
        Returns:
            Normalized job data
        """
        return {
            "title": raw_job_data.get("title", ""),
            "company": raw_job_data.get("company", ""),
            "location": raw_job_data.get("location", ""),
            "remote_type": self._normalize_remote_type(raw_job_data.get("remote_type")),
            "description": raw_job_data.get("description", ""),
            "requirements": self._extract_requirements(raw_job_data.get("description", "")),
            "responsibilities": self._extract_responsibilities(raw_job_data.get("description", "")),
            "qualifications": self._extract_qualifications(raw_job_data.get("description", "")),
            "salary_min": raw_job_data.get("salary_min"),
            "salary_max": raw_job_data.get("salary_max"),
            "salary_currency": raw_job_data.get("salary_currency", "USD"),
            "benefits": raw_job_data.get("benefits", []),
            "employment_type": self._normalize_employment_type(raw_job_data.get("employment_type")),
            "experience_level": self._normalize_experience_level(raw_job_data.get("experience_level")),
            "industry": raw_job_data.get("industry", ""),
            "department": raw_job_data.get("department", ""),
            "source": self.source_name,
            "external_id": raw_job_data.get("id", str(uuid.uuid4())),
            "source_url": raw_job_data.get("url", ""),
            "posted_date": self._parse_date(raw_job_data.get("posted_date")),
            "application_deadline": self._parse_date(raw_job_data.get("application_deadline")),
            "scraped_at": datetime.utcnow()
        }
    
    def _normalize_remote_type(self, remote_type: str) -> str:
        """Normalize remote work type"""
        if not remote_type:
            return "onsite"
        
        remote_type = remote_type.lower()
        if "remote" in remote_type:
            return "remote"
        elif "hybrid" in remote_type:
            return "hybrid"
        else:
            return "onsite"
    
    def _normalize_employment_type(self, employment_type: str) -> str:
        """Normalize employment type"""
        if not employment_type:
            return "full-time"
        
        employment_type = employment_type.lower()
        if "part" in employment_type:
            return "part-time"
        elif "contract" in employment_type or "freelance" in employment_type:
            return "contract"
        elif "intern" in employment_type:
            return "internship"
        else:
            return "full-time"
    
    def _normalize_experience_level(self, experience_level: str) -> str:
        """Normalize experience level"""
        if not experience_level:
            return "mid"
        
        experience_level = experience_level.lower()
        if "entry" in experience_level or "junior" in experience_level or "graduate" in experience_level:
            return "entry"
        elif "senior" in experience_level or "lead" in experience_level:
            return "senior"
        elif "executive" in experience_level or "director" in experience_level or "vp" in experience_level:
            return "executive"
        else:
            return "mid"
    
    def _extract_requirements(self, description: str) -> List[str]:
        """Extract requirements from job description"""
        if not description:
            return []
        
        requirements = []
        
        # Look for requirements sections
        req_patterns = [
            r"requirements?:?\s*(.*?)(?=responsibilities|qualifications|benefits|$)",
            r"what you.ll need:?\s*(.*?)(?=what you.ll do|responsibilities|$)",
            r"must have:?\s*(.*?)(?=nice to have|responsibilities|$)"
        ]
        
        for pattern in req_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Split by bullet points or line breaks
                items = re.split(r'[•\-\*\n]', match)
                for item in items:
                    item = item.strip()
                    if len(item) > 10 and len(item) < 200:  # Filter reasonable requirements
                        requirements.append(item)
        
        return requirements[:10]  # Limit to 10 requirements
    
    def _extract_responsibilities(self, description: str) -> List[str]:
        """Extract responsibilities from job description"""
        if not description:
            return []
        
        responsibilities = []
        
        # Look for responsibilities sections
        resp_patterns = [
            r"responsibilities:?\s*(.*?)(?=requirements|qualifications|benefits|$)",
            r"what you.ll do:?\s*(.*?)(?=what you.ll need|requirements|$)",
            r"duties:?\s*(.*?)(?=requirements|qualifications|$)"
        ]
        
        for pattern in resp_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Split by bullet points or line breaks
                items = re.split(r'[•\-\*\n]', match)
                for item in items:
                    item = item.strip()
                    if len(item) > 10 and len(item) < 200:  # Filter reasonable responsibilities
                        responsibilities.append(item)
        
        return responsibilities[:10]  # Limit to 10 responsibilities
    
    def _extract_qualifications(self, description: str) -> List[str]:
        """Extract qualifications from job description"""
        if not description:
            return []
        
        qualifications = []
        
        # Look for qualifications sections
        qual_patterns = [
            r"qualifications:?\s*(.*?)(?=responsibilities|requirements|benefits|$)",
            r"preferred:?\s*(.*?)(?=responsibilities|requirements|$)",
            r"nice to have:?\s*(.*?)(?=responsibilities|requirements|$)"
        ]
        
        for pattern in qual_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Split by bullet points or line breaks
                items = re.split(r'[•\-\*\n]', match)
                for item in items:
                    item = item.strip()
                    if len(item) > 10 and len(item) < 200:  # Filter reasonable qualifications
                        qualifications.append(item)
        
        return qualifications[:10]  # Limit to 10 qualifications
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        
        try:
            # Try common date formats
            formats = [
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%m/%d/%Y",
                "%d/%m/%Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None


class LinkedInConnector(BaseJobConnector):
    """
    LinkedIn Jobs API connector
    Note: This is a mock implementation as LinkedIn's official API has limited job search access
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("linkedin", api_key, "https://api.linkedin.com/v2")
    
    async def search_jobs(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search LinkedIn jobs (mock implementation)
        """
        try:
            # Mock LinkedIn job data for demonstration
            mock_jobs = [
                {
                    "id": f"linkedin_{uuid.uuid4()}",
                    "title": f"Senior {criteria.get('keywords', ['Software Engineer'])[0] if criteria.get('keywords') else 'Software Engineer'}",
                    "company": "Tech Corp",
                    "location": criteria.get("location", "San Francisco, CA"),
                    "remote_type": criteria.get("remote_type", "hybrid"),
                    "description": f"We are looking for a skilled {criteria.get('keywords', ['developer'])[0] if criteria.get('keywords') else 'developer'} to join our team. Requirements include experience with modern technologies and strong problem-solving skills. Responsibilities include developing software solutions and collaborating with cross-functional teams.",
                    "employment_type": criteria.get("employment_type", "full-time"),
                    "experience_level": criteria.get("experience_level", "mid"),
                    "industry": criteria.get("industry", "Technology"),
                    "salary_min": 80000,
                    "salary_max": 120000,
                    "posted_date": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                    "url": "https://linkedin.com/jobs/view/mock-job-1"
                },
                {
                    "id": f"linkedin_{uuid.uuid4()}",
                    "title": f"{criteria.get('keywords', ['Product Manager'])[0] if criteria.get('keywords') else 'Product Manager'}",
                    "company": "Innovation Inc",
                    "location": criteria.get("location", "New York, NY"),
                    "remote_type": "remote",
                    "description": "Join our product team to drive innovation and growth. Requirements include product management experience and analytical skills. Responsibilities include defining product strategy and working with engineering teams.",
                    "employment_type": "full-time",
                    "experience_level": criteria.get("experience_level", "senior"),
                    "industry": criteria.get("industry", "Technology"),
                    "salary_min": 100000,
                    "salary_max": 150000,
                    "posted_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "url": "https://linkedin.com/jobs/view/mock-job-2"
                }
            ]
            
            # Simulate API delay
            await asyncio.sleep(self.rate_limit_delay)
            
            # Normalize job data
            normalized_jobs = [self._normalize_job_data(job) for job in mock_jobs]
            
            logger.info(f"LinkedIn connector found {len(normalized_jobs)} jobs")
            return normalized_jobs
            
        except Exception as e:
            logger.error(f"Error searching LinkedIn jobs: {str(e)}")
            return []
    
    async def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Get detailed job information from LinkedIn"""
        # Mock implementation
        return {
            "id": job_id,
            "detailed_description": "Detailed job description would be fetched here",
            "company_info": {"name": "Tech Corp", "size": "1000-5000", "industry": "Technology"}
        }


class IndeedConnector(BaseJobConnector):
    """
    Indeed Jobs API connector
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("indeed", api_key, "https://api.indeed.com/ads")
    
    async def search_jobs(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search Indeed jobs (mock implementation)
        """
        try:
            # Mock Indeed job data
            mock_jobs = [
                {
                    "id": f"indeed_{uuid.uuid4()}",
                    "title": f"Junior {criteria.get('keywords', ['Developer'])[0] if criteria.get('keywords') else 'Developer'}",
                    "company": "StartupCo",
                    "location": criteria.get("location", "Austin, TX"),
                    "remote_type": "onsite",
                    "description": f"Entry-level position for {criteria.get('keywords', ['developer'])[0] if criteria.get('keywords') else 'developer'}. Requirements include basic programming knowledge and eagerness to learn. Responsibilities include coding, testing, and documentation.",
                    "employment_type": "full-time",
                    "experience_level": "entry",
                    "industry": criteria.get("industry", "Technology"),
                    "salary_min": 50000,
                    "salary_max": 70000,
                    "posted_date": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                    "url": "https://indeed.com/viewjob?jk=mock-job-3"
                }
            ]
            
            await asyncio.sleep(self.rate_limit_delay)
            
            normalized_jobs = [self._normalize_job_data(job) for job in mock_jobs]
            
            logger.info(f"Indeed connector found {len(normalized_jobs)} jobs")
            return normalized_jobs
            
        except Exception as e:
            logger.error(f"Error searching Indeed jobs: {str(e)}")
            return []
    
    async def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Get detailed job information from Indeed"""
        return {
            "id": job_id,
            "detailed_description": "Detailed job description from Indeed",
            "company_info": {"name": "StartupCo", "size": "10-50", "industry": "Technology"}
        }


class GlassdoorConnector(BaseJobConnector):
    """
    Glassdoor Jobs API connector
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("glassdoor", api_key, "https://api.glassdoor.com/api")
    
    async def search_jobs(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search Glassdoor jobs (mock implementation)
        """
        try:
            # Mock Glassdoor job data
            mock_jobs = [
                {
                    "id": f"glassdoor_{uuid.uuid4()}",
                    "title": f"Lead {criteria.get('keywords', ['Engineer'])[0] if criteria.get('keywords') else 'Engineer'}",
                    "company": "Enterprise Corp",
                    "location": criteria.get("location", "Seattle, WA"),
                    "remote_type": "hybrid",
                    "description": f"Leadership role for experienced {criteria.get('keywords', ['engineer'])[0] if criteria.get('keywords') else 'engineer'}. Requirements include 8+ years experience and team leadership skills. Responsibilities include technical leadership and mentoring.",
                    "employment_type": "full-time",
                    "experience_level": "senior",
                    "industry": criteria.get("industry", "Technology"),
                    "salary_min": 130000,
                    "salary_max": 180000,
                    "posted_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "url": "https://glassdoor.com/job-listing/mock-job-4"
                }
            ]
            
            await asyncio.sleep(self.rate_limit_delay)
            
            normalized_jobs = [self._normalize_job_data(job) for job in mock_jobs]
            
            logger.info(f"Glassdoor connector found {len(normalized_jobs)} jobs")
            return normalized_jobs
            
        except Exception as e:
            logger.error(f"Error searching Glassdoor jobs: {str(e)}")
            return []
    
    async def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Get detailed job information from Glassdoor"""
        return {
            "id": job_id,
            "detailed_description": "Detailed job description from Glassdoor",
            "company_info": {"name": "Enterprise Corp", "size": "5000+", "industry": "Technology"},
            "salary_insights": {"average": 155000, "range": "130k-180k"}
        }


class AngelListConnector(BaseJobConnector):
    """
    AngelList (Wellfound) Jobs API connector
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("angellist", api_key, "https://api.angel.co/1")
    
    async def search_jobs(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search AngelList jobs (mock implementation)
        """
        try:
            # Mock AngelList job data (startup focused)
            mock_jobs = [
                {
                    "id": f"angellist_{uuid.uuid4()}",
                    "title": f"Full Stack {criteria.get('keywords', ['Developer'])[0] if criteria.get('keywords') else 'Developer'}",
                    "company": "AI Startup",
                    "location": criteria.get("location", "San Francisco, CA"),
                    "remote_type": "remote",
                    "description": f"Join our fast-growing AI startup as a {criteria.get('keywords', ['developer'])[0] if criteria.get('keywords') else 'developer'}. Requirements include full-stack development experience and startup mindset. Responsibilities include building scalable applications and rapid prototyping.",
                    "employment_type": "full-time",
                    "experience_level": criteria.get("experience_level", "mid"),
                    "industry": "Artificial Intelligence",
                    "salary_min": 90000,
                    "salary_max": 140000,
                    "benefits": ["Equity", "Health Insurance", "Flexible PTO"],
                    "posted_date": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
                    "url": "https://angel.co/company/ai-startup/jobs/mock-job-5"
                }
            ]
            
            await asyncio.sleep(self.rate_limit_delay)
            
            normalized_jobs = [self._normalize_job_data(job) for job in mock_jobs]
            
            logger.info(f"AngelList connector found {len(normalized_jobs)} jobs")
            return normalized_jobs
            
        except Exception as e:
            logger.error(f"Error searching AngelList jobs: {str(e)}")
            return []
    
    async def get_job_details(self, job_id: str) -> Dict[str, Any]:
        """Get detailed job information from AngelList"""
        return {
            "id": job_id,
            "detailed_description": "Detailed job description from AngelList",
            "company_info": {"name": "AI Startup", "size": "10-50", "industry": "AI", "stage": "Series A"},
            "equity_info": {"equity_min": 0.1, "equity_max": 0.5}
        }


class JobConnectorManager:
    """
    Manager for job board connectors
    """
    
    def __init__(self):
        self.connectors = {}
        self._initialize_connectors()
    
    def _initialize_connectors(self):
        """Initialize all job board connectors"""
        try:
            # Initialize connectors (API keys would come from environment variables)
            self.connectors["linkedin"] = LinkedInConnector()
            self.connectors["indeed"] = IndeedConnector()
            self.connectors["glassdoor"] = GlassdoorConnector()
            self.connectors["angellist"] = AngelListConnector()
            
            logger.info(f"Initialized {len(self.connectors)} job connectors")
            
        except Exception as e:
            logger.error(f"Error initializing job connectors: {str(e)}")
    
    def get_connector(self, source: str) -> Optional[BaseJobConnector]:
        """Get connector for specific job board"""
        return self.connectors.get(source)
    
    def get_all_connectors(self) -> Dict[str, BaseJobConnector]:
        """Get all available connectors"""
        return self.connectors.copy()
    
    async def search_all_sources(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search jobs from all available sources
        
        Args:
            criteria: Search criteria
            
        Returns:
            Combined job results from all sources
        """
        all_jobs = []
        
        for source, connector in self.connectors.items():
            try:
                async with connector:
                    jobs = await connector.search_jobs(criteria)
                    all_jobs.extend(jobs)
                    logger.info(f"Found {len(jobs)} jobs from {source}")
            except Exception as e:
                logger.error(f"Error searching {source}: {str(e)}")
        
        logger.info(f"Total jobs found across all sources: {len(all_jobs)}")
        return all_jobs


# Global connector manager instance
job_connector_manager = JobConnectorManager()