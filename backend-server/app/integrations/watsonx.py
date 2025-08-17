"""
WatsonX.ai Integration Utilities
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
import aiohttp
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class WatsonXClient:
    """
    Client for interacting with WatsonX.ai services
    Handles authentication, model inference, and error handling
    """
    
    def __init__(self, api_key: str, base_url: str = "https://us-south.ml.cloud.ibm.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.auth_token = None
        self.token_expires_at = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        await self._authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _authenticate(self) -> None:
        """Authenticate with WatsonX.ai and get access token"""
        try:
            auth_url = f"{self.base_url}/v1/authorize"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            auth_data = {
                "apikey": self.api_key,
                "response_type": "cloud_iam"
            }
            
            async with self.session.post(auth_url, json=auth_data, headers=headers) as response:
                if response.status == 200:
                    auth_result = await response.json()
                    self.auth_token = auth_result.get("access_token")
                    # Token typically expires in 1 hour
                    self.token_expires_at = datetime.utcnow().timestamp() + 3600
                    logger.info("Successfully authenticated with WatsonX.ai")
                else:
                    error_text = await response.text()
                    logger.error(f"WatsonX.ai authentication failed: {error_text}")
                    raise Exception(f"Authentication failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error authenticating with WatsonX.ai: {str(e)}")
            raise
    
    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token"""
        if not self.auth_token or (self.token_expires_at and 
                                  datetime.utcnow().timestamp() > self.token_expires_at - 300):
            await self._authenticate()
    
    async def generate_text(self, prompt: str, model_id: str = "ibm/granite-13b-chat-v2", 
                           parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate text using WatsonX.ai language models
        
        Args:
            prompt: Input prompt for text generation
            model_id: Model identifier to use
            parameters: Model parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response
        """
        await self._ensure_authenticated()
        
        if parameters is None:
            parameters = {
                "temperature": 0.7,
                "max_new_tokens": 512,
                "top_p": 0.9,
                "repetition_penalty": 1.1
            }
        
        try:
            url = f"{self.base_url}/ml/v1/text/generation"
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            payload = {
                "model_id": model_id,
                "input": prompt,
                "parameters": parameters,
                "project_id": "your-project-id"  # This should be configurable
            }
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "generated_text": result.get("results", [{}])[0].get("generated_text", ""),
                        "model_id": model_id,
                        "token_count": result.get("results", [{}])[0].get("generated_token_count", 0)
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Text generation failed: {error_text}")
                    return {
                        "success": False,
                        "error": f"Generation failed: {response.status}",
                        "details": error_text
                    }
                    
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_text(self, text: str, analysis_type: str = "sentiment") -> Dict[str, Any]:
        """
        Analyze text using WatsonX.ai NLP capabilities
        
        Args:
            text: Text to analyze
            analysis_type: Type of analysis ('sentiment', 'entities', 'keywords')
            
        Returns:
            Analysis results
        """
        await self._ensure_authenticated()
        
        try:
            # This would use Watson Natural Language Understanding
            url = f"{self.base_url}/v1/analyze"
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            features = {}
            if analysis_type == "sentiment":
                features["sentiment"] = {}
            elif analysis_type == "entities":
                features["entities"] = {"limit": 10}
            elif analysis_type == "keywords":
                features["keywords"] = {"limit": 10}
            
            payload = {
                "text": text,
                "features": features
            }
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "analysis": result,
                        "analysis_type": analysis_type
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Analysis failed: {response.status}",
                        "details": error_text
                    }
                    
        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from text (resume, job description, etc.)
        
        Args:
            text: Text to extract skills from
            
        Returns:
            List of extracted skills
        """
        prompt = f"""
        Extract technical and professional skills from the following text.
        Return only the skills as a comma-separated list.
        
        Text: {text}
        
        Skills:
        """
        
        result = await self.generate_text(prompt)
        
        if result["success"]:
            skills_text = result["generated_text"].strip()
            skills = [skill.strip() for skill in skills_text.split(",") if skill.strip()]
            return skills
        else:
            logger.error(f"Skill extraction failed: {result.get('error')}")
            return []
    
    async def score_job_compatibility(self, user_profile: Dict[str, Any], 
                                    job_description: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score compatibility between user profile and job description
        
        Args:
            user_profile: User's profile data
            job_description: Job posting data
            
        Returns:
            Compatibility score and analysis
        """
        prompt = f"""
        Analyze the compatibility between this user profile and job description.
        Provide a compatibility score from 0.0 to 1.0 and explain the reasoning.
        
        User Profile:
        Skills: {user_profile.get('skills', [])}
        Experience: {user_profile.get('years_experience', 0)} years
        Current Title: {user_profile.get('current_title', 'N/A')}
        
        Job Description:
        Title: {job_description.get('title', 'N/A')}
        Requirements: {job_description.get('requirements', [])}
        Experience Level: {job_description.get('experience_level', 'N/A')}
        
        Provide response in JSON format:
        {{
            "compatibility_score": 0.0-1.0,
            "reasoning": "explanation",
            "skill_match": 0.0-1.0,
            "experience_match": 0.0-1.0,
            "missing_skills": ["skill1", "skill2"]
        }}
        """
        
        result = await self.generate_text(prompt)
        
        if result["success"]:
            try:
                # Parse JSON response
                response_text = result["generated_text"].strip()
                compatibility_data = json.loads(response_text)
                return {
                    "success": True,
                    "compatibility": compatibility_data
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse compatibility analysis"
                }
        else:
            return result


class WatsonXOrchestrate:
    """
    Client for WatsonX Orchestrate workflow management
    Handles complex multi-agent workflows and coordination
    """
    
    def __init__(self, api_key: str, base_url: str = "https://orchestrate.watson.ai"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def create_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new workflow in WatsonX Orchestrate
        
        Args:
            workflow_definition: Workflow configuration
            
        Returns:
            Workflow creation result
        """
        try:
            url = f"{self.base_url}/v1/workflows"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(url, json=workflow_definition, headers=headers) as response:
                if response.status == 201:
                    result = await response.json()
                    return {
                        "success": True,
                        "workflow_id": result.get("workflow_id"),
                        "status": result.get("status")
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Workflow creation failed: {response.status}",
                        "details": error_text
                    }
                    
        except Exception as e:
            logger.error(f"Error creating workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow with input data
        
        Args:
            workflow_id: ID of workflow to execute
            input_data: Input data for workflow
            
        Returns:
            Workflow execution result
        """
        try:
            url = f"{self.base_url}/v1/workflows/{workflow_id}/execute"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(url, json=input_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "execution_id": result.get("execution_id"),
                        "status": result.get("status"),
                        "results": result.get("results")
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Workflow execution failed: {response.status}",
                        "details": error_text
                    }
                    
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }