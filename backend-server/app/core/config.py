"""
Application Configuration Management
"""
import os
from typing import Dict, Any, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """
    
    # Application settings
    app_name: str = Field(default="JobSwitch.ai", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    
    # Database settings
    database_url: str = Field(default="sqlite:///./jobswitch.db", env="DATABASE_URL")
    sql_debug: bool = Field(default=False, env="SQL_DEBUG")
    
    # Security settings
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # CORS settings
    cors_origins: list = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # WatsonX.ai settings
    watsonx_api_key: str = Field(default="", env="WATSONX_API_KEY")
    watsonx_base_url: str = Field(default="https://us-south.ml.cloud.ibm.com", env="WATSONX_BASE_URL")
    watsonx_project_id: str = Field(default="", env="WATSONX_PROJECT_ID")
    
    # WatsonX Orchestrate settings
    watsonx_orchestrate_api_key: str = Field(default="", env="WATSONX_ORCHESTRATE_API_KEY")
    watsonx_orchestrate_base_url: str = Field(default="https://orchestrate.watson.ai", env="WATSONX_ORCHESTRATE_BASE_URL")
    
    # LangChain settings
    langchain_verbose: bool = Field(default=False, env="LANGCHAIN_VERBOSE")
    langchain_cache_enabled: bool = Field(default=True, env="LANGCHAIN_CACHE_ENABLED")
    
    # External API settings
    linkedin_api_key: str = Field(default="", env="LINKEDIN_API_KEY")
    indeed_api_key: str = Field(default="", env="INDEED_API_KEY")
    glassdoor_api_key: str = Field(default="", env="GLASSDOOR_API_KEY")
    angellist_api_key: str = Field(default="", env="ANGELLIST_API_KEY")
    
    # Redis settings (for caching)
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_enabled: bool = Field(default=False, env="REDIS_ENABLED")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")
    
    # Agent settings
    max_concurrent_agents: int = Field(default=10, env="MAX_CONCURRENT_AGENTS")
    agent_timeout_seconds: int = Field(default=300, env="AGENT_TIMEOUT_SECONDS")
    task_queue_size: int = Field(default=1000, env="TASK_QUEUE_SIZE")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    
    # Email settings
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    default_from_email: str = Field(default="noreply@jobswitch.ai", env="DEFAULT_FROM_EMAIL")
    default_from_name: str = Field(default="JobSwitch.ai", env="DEFAULT_FROM_NAME")
    base_url: str = Field(default="http://localhost:8000", env="BASE_URL")
    domain: str = Field(default="jobswitch.ai", env="DOMAIN")
    
    # Add missing constants for email sender
    SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: str = Field(default="", env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    DEFAULT_FROM_EMAIL: str = Field(default="noreply@jobswitch.ai", env="DEFAULT_FROM_EMAIL")
    DEFAULT_FROM_NAME: str = Field(default="JobSwitch.ai", env="DEFAULT_FROM_NAME")
    BASE_URL: str = Field(default="http://localhost:8000", env="BASE_URL")
    DOMAIN: str = Field(default="jobswitch.ai", env="DOMAIN")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class ConfigManager:
    """
    Configuration manager for the application
    """
    
    def __init__(self):
        self.settings = Settings()
        self._validate_settings()
    
    def _validate_settings(self):
        """
        Validate critical settings
        """
        if self.settings.environment == "production":
            if self.settings.secret_key == "your-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be set in production environment")
            
            if not self.settings.watsonx_api_key:
                logger.warning("WATSONX_API_KEY not set - AI features may not work")
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration
        
        Returns:
            Database configuration dictionary
        """
        return {
            "url": self.settings.database_url,
            "debug": self.settings.sql_debug,
            "echo": self.settings.sql_debug
        }
    
    def get_watsonx_config(self) -> Dict[str, Any]:
        """
        Get WatsonX.ai configuration
        
        Returns:
            WatsonX configuration dictionary
        """
        return {
            "api_key": self.settings.watsonx_api_key,
            "base_url": self.settings.watsonx_base_url,
            "project_id": self.settings.watsonx_project_id
        }
    
    def get_watsonx_orchestrate_config(self) -> Dict[str, Any]:
        """
        Get WatsonX Orchestrate configuration
        
        Returns:
            WatsonX Orchestrate configuration dictionary
        """
        return {
            "api_key": self.settings.watsonx_orchestrate_api_key,
            "base_url": self.settings.watsonx_orchestrate_base_url
        }
    
    def get_langchain_config(self) -> Dict[str, Any]:
        """
        Get LangChain configuration
        
        Returns:
            LangChain configuration dictionary
        """
        return {
            "verbose": self.settings.langchain_verbose,
            "cache_enabled": self.settings.langchain_cache_enabled
        }
    
    def get_external_apis_config(self) -> Dict[str, Any]:
        """
        Get external APIs configuration
        
        Returns:
            External APIs configuration dictionary
        """
        return {
            "linkedin": {"api_key": self.settings.linkedin_api_key},
            "indeed": {"api_key": self.settings.indeed_api_key},
            "glassdoor": {"api_key": self.settings.glassdoor_api_key},
            "angellist": {"api_key": self.settings.angellist_api_key}
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """
        Get Redis configuration
        
        Returns:
            Redis configuration dictionary
        """
        return {
            "url": self.settings.redis_url,
            "enabled": self.settings.redis_enabled
        }
    
    def get_cors_config(self) -> Dict[str, Any]:
        """
        Get CORS configuration
        
        Returns:
            CORS configuration dictionary
        """
        return {
            "origins": self.settings.cors_origins,
            "allow_credentials": self.settings.cors_allow_credentials,
            "allow_methods": ["*"],
            "allow_headers": ["*"]
        }
    
    def get_agent_config(self) -> Dict[str, Any]:
        """
        Get agent configuration
        
        Returns:
            Agent configuration dictionary
        """
        return {
            "max_concurrent": self.settings.max_concurrent_agents,
            "timeout_seconds": self.settings.agent_timeout_seconds,
            "queue_size": self.settings.task_queue_size
        }
    
    def is_production(self) -> bool:
        """
        Check if running in production environment
        
        Returns:
            True if production, False otherwise
        """
        return self.settings.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """
        Check if running in development environment
        
        Returns:
            True if development, False otherwise
        """
        return self.settings.environment.lower() == "development"
    
    def get_email_config(self) -> Dict[str, Any]:
        """
        Get email configuration
        
        Returns:
            Email configuration dictionary
        """
        return {
            "smtp_host": self.settings.smtp_host,
            "smtp_port": self.settings.smtp_port,
            "smtp_username": self.settings.smtp_username,
            "smtp_password": self.settings.smtp_password,
            "smtp_use_tls": self.settings.smtp_use_tls,
            "default_from_email": self.settings.default_from_email,
            "default_from_name": self.settings.default_from_name,
            "base_url": self.settings.base_url,
            "domain": self.settings.domain
        }


# Global configuration manager instance
config = ConfigManager()

# Export settings for easy access
settings = config.settings

def get_settings() -> Settings:
    """
    Get application settings instance
    
    Returns:
        Settings instance
    """
    return settings