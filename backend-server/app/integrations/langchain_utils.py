"""
LangChain Integration Utilities
"""
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

try:
    from langchain.llms.base import LLM
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain.memory import ConversationBufferMemory
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.tools import Tool
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain not installed. Some features may not be available.")
    LANGCHAIN_AVAILABLE = False
    # Create dummy classes when LangChain is not available
    class LLM:
        pass
    class LLMChain:
        pass
    class PromptTemplate:
        pass
    class ConversationBufferMemory:
        pass
    class Tool:
        pass
    class BaseMessage:
        pass
    class HumanMessage:
        pass
    class AIMessage:
        pass


if LANGCHAIN_AVAILABLE:
    class WatsonXLLM(LLM):
        """
        Custom LangChain LLM wrapper for WatsonX.ai
        """
        
        def __init__(self, watsonx_client, model_id: str = "ibm/granite-13b-chat-v2"):
            super().__init__()
            self.watsonx_client = watsonx_client
            self.model_id = model_id
        
        @property
        def _llm_type(self) -> str:
            return "watsonx"
        
        def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
            """
            Call the WatsonX.ai model with the given prompt
            
            Args:
                prompt: Input prompt
                stop: Stop sequences
                
            Returns:
                Generated text
            """
            try:
                # This would need to be adapted for sync/async compatibility
                result = asyncio.run(self.watsonx_client.generate_text(prompt, self.model_id))
                
                if result["success"]:
                    return result["generated_text"]
                else:
                    logger.error(f"WatsonX generation failed: {result.get('error')}")
                    return ""
                    
            except Exception as e:
                logger.error(f"Error calling WatsonX LLM: {str(e)}")
                return ""
else:
    class WatsonXLLM:
        """Dummy class when LangChain is not available"""
        def __init__(self, *args, **kwargs):
            pass


class LangChainAgentManager:
    """
    Manager for LangChain-based AI agents and workflows
    """
    
    def __init__(self, watsonx_client):
        self.watsonx_client = watsonx_client
        self.llm = WatsonXLLM(watsonx_client) if LANGCHAIN_AVAILABLE else None
        self.agents = {}
        self.tools = {}
        self.memories = {}
        self.available = LANGCHAIN_AVAILABLE
    
    def create_prompt_template(self, template: str, input_variables: List[str]) -> PromptTemplate:
        """
        Create a LangChain prompt template
        
        Args:
            template: Prompt template string
            input_variables: List of input variable names
            
        Returns:
            PromptTemplate instance
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is not available")
        
        return PromptTemplate(
            template=template,
            input_variables=input_variables
        )
    
    def create_chain(self, prompt_template: PromptTemplate, 
                    memory_key: str = None) -> LLMChain:
        """
        Create a LangChain LLM chain
        
        Args:
            prompt_template: Prompt template to use
            memory_key: Key for conversation memory
            
        Returns:
            LLMChain instance
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is not available")
        
        memory = None
        if memory_key:
            if memory_key not in self.memories:
                self.memories[memory_key] = ConversationBufferMemory()
            memory = self.memories[memory_key]
        
        return LLMChain(
            llm=self.llm,
            prompt=prompt_template,
            memory=memory
        )
    
    def register_tool(self, name: str, func: Callable, description: str) -> None:
        """
        Register a tool for use in LangChain agents
        
        Args:
            name: Tool name
            func: Tool function
            description: Tool description
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is not available")
        
        tool = Tool(
            name=name,
            func=func,
            description=description
        )
        self.tools[name] = tool
    
    def create_job_search_chain(self) -> LLMChain:
        """
        Create a specialized chain for job search queries
        
        Returns:
            Configured LLMChain for job search
        """
        template = """
        You are a career advisor AI helping with job search. 
        Based on the user's profile and preferences, provide personalized job search advice.
        
        User Profile: {user_profile}
        Query: {query}
        
        Provide specific, actionable advice including:
        1. Job search strategies
        2. Relevant job boards and platforms
        3. Networking recommendations
        4. Skills to highlight
        
        Response:
        """
        
        prompt = self.create_prompt_template(
            template=template,
            input_variables=["user_profile", "query"]
        )
        
        return self.create_chain(prompt, memory_key="job_search")
    
    def create_resume_optimization_chain(self) -> LLMChain:
        """
        Create a specialized chain for resume optimization
        
        Returns:
            Configured LLMChain for resume optimization
        """
        template = """
        You are a resume optimization expert. Analyze the resume and job description 
        to provide specific optimization recommendations.
        
        Current Resume: {resume_content}
        Target Job Description: {job_description}
        
        Provide detailed recommendations for:
        1. Keywords to add for ATS optimization
        2. Skills to emphasize
        3. Experience to highlight
        4. Formatting improvements
        5. Content gaps to address
        
        Optimization Recommendations:
        """
        
        prompt = self.create_prompt_template(
            template=template,
            input_variables=["resume_content", "job_description"]
        )
        
        return self.create_chain(prompt, memory_key="resume_optimization")
    
    def create_interview_prep_chain(self) -> LLMChain:
        """
        Create a specialized chain for interview preparation
        
        Returns:
            Configured LLMChain for interview preparation
        """
        template = """
        You are an interview preparation coach. Generate relevant interview questions 
        and provide guidance based on the job role and company.
        
        Job Title: {job_title}
        Company: {company}
        Job Description: {job_description}
        User Background: {user_background}
        
        Provide:
        1. 5 common interview questions for this role
        2. 3 behavioral questions
        3. 2 technical questions (if applicable)
        4. Questions the candidate should ask
        5. Key points to emphasize from their background
        
        Interview Preparation Guide:
        """
        
        prompt = self.create_prompt_template(
            template=template,
            input_variables=["job_title", "company", "job_description", "user_background"]
        )
        
        return self.create_chain(prompt, memory_key="interview_prep")
    
    def create_skills_analysis_chain(self) -> LLMChain:
        """
        Create a specialized chain for skills gap analysis
        
        Returns:
            Configured LLMChain for skills analysis
        """
        template = """
        You are a career development advisor specializing in skills analysis.
        Compare the user's current skills with job market requirements.
        
        Current Skills: {current_skills}
        Target Role: {target_role}
        Market Requirements: {market_requirements}
        
        Provide:
        1. Skills gap analysis
        2. Priority skills to develop
        3. Learning resources and courses
        4. Timeline for skill development
        5. Alternative career paths to consider
        
        Skills Development Plan:
        """
        
        prompt = self.create_prompt_template(
            template=template,
            input_variables=["current_skills", "target_role", "market_requirements"]
        )
        
        return self.create_chain(prompt, memory_key="skills_analysis")
    
    def create_networking_chain(self) -> LLMChain:
        """
        Create a specialized chain for networking advice
        
        Returns:
            Configured LLMChain for networking
        """
        template = """
        You are a networking and career strategy expert. Help the user build 
        professional connections and expand their network.
        
        User Profile: {user_profile}
        Target Companies: {target_companies}
        Career Goals: {career_goals}
        
        Provide:
        1. Networking strategy for target companies
        2. LinkedIn outreach templates
        3. Industry events and conferences to attend
        4. Professional associations to join
        5. Informational interview approaches
        
        Networking Action Plan:
        """
        
        prompt = self.create_prompt_template(
            template=template,
            input_variables=["user_profile", "target_companies", "career_goals"]
        )
        
        return self.create_chain(prompt, memory_key="networking")
    
    async def process_with_chain(self, chain: LLMChain, 
                               input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data with a LangChain chain
        
        Args:
            chain: LangChain to use
            input_data: Input data for the chain
            
        Returns:
            Chain output
        """
        try:
            start_time = datetime.utcnow()
            
            # Run the chain
            result = chain.run(**input_data)
            
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "result": result,
                "processing_time_ms": processing_time,
                "timestamp": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing with LangChain: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_conversation_history(self, memory_key: str) -> List[Dict[str, Any]]:
        """
        Get conversation history from memory
        
        Args:
            memory_key: Memory key to retrieve
            
        Returns:
            List of conversation messages
        """
        if memory_key not in self.memories:
            return []
        
        memory = self.memories[memory_key]
        messages = []
        
        # Extract messages from memory buffer
        if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
            for message in memory.chat_memory.messages:
                if isinstance(message, HumanMessage):
                    messages.append({
                        "type": "human",
                        "content": message.content,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                elif isinstance(message, AIMessage):
                    messages.append({
                        "type": "ai",
                        "content": message.content,
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        return messages
    
    def clear_memory(self, memory_key: str) -> None:
        """
        Clear conversation memory
        
        Args:
            memory_key: Memory key to clear
        """
        if memory_key in self.memories:
            self.memories[memory_key].clear()
            logger.info(f"Cleared memory for key: {memory_key}")


# Global LangChain manager instance
langchain_manager = None

def initialize_langchain_manager(watsonx_client):
    """
    Initialize the global LangChain manager
    
    Args:
        watsonx_client: WatsonX client instance
    """
    global langchain_manager
    langchain_manager = LangChainAgentManager(watsonx_client)
    return langchain_manager