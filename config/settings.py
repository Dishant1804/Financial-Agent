from typing import List
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from pydantic_settings import BaseSettings
    from typing import Optional
    
    class Settings(BaseSettings):
        app_name: str = "Financial Analysis Agent API"
        app_version: str = "1.0.0"
        app_description: str = "API for financial analysis using AI agent"
        
        host: str = "0.0.0.0"
        port: int = 8000
        debug: bool = True
        reload: bool = True
        log_level: str = "info"
        
        cors_origins: List[str] = [
            "http://localhost:3000",
            "https://finvest-jbmuljwql-dishant1804s-projects.vercel.app"
        ]
        cors_credentials: bool = True
        cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
        cors_headers: List[str] = ["*"]
        
        database_name: str = "finvest_analysis"
        
        tavily_api_key: Optional[str] = None
        google_api_key: Optional[str] = None
        groq_api_key: Optional[str] = None
        
        model_config = {
            "env_file": ".env", 
            "case_sensitive": False,
            "extra": "allow"
        }

except ImportError:
    class Settings:
        """Application settings with environment variable support"""
        
        def __init__(self):
            self.app_name: str = os.getenv("APP_NAME", "Financial Analysis Agent API")
            self.app_version: str = os.getenv("APP_VERSION", "1.0.0")
            self.app_description: str = os.getenv("APP_DESCRIPTION", "API for financial analysis using AI agent")
            
            self.host: str = os.getenv("HOST", "0.0.0.0")
            self.port: int = int(os.getenv("PORT", "8000"))
            self.debug: bool = os.getenv("DEBUG", "True").lower() == "true"
            self.reload: bool = os.getenv("RELOAD", "True").lower() == "true"
            self.log_level: str = os.getenv("LOG_LEVEL", "info")
            
            cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,*")
            self.cors_origins: List[str] = [origin.strip() for origin in cors_origins_str.split(",")]
            self.cors_credentials: bool = os.getenv("CORS_CREDENTIALS", "True").lower() == "true"
            
            cors_methods_str = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE")
            self.cors_methods: List[str] = [method.strip() for method in cors_methods_str.split(",")]
            
            cors_headers_str = os.getenv("CORS_HEADERS", "*")
            self.cors_headers: List[str] = [header.strip() for header in cors_headers_str.split(",")]
            
            self.mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            self.database_name: str = os.getenv("DATABASE_NAME", "finvest_analysis")
            
            self.tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
            self.google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
            self.groq_api_key: str = os.getenv("GROQ_API_KEY", "")

settings = Settings()
