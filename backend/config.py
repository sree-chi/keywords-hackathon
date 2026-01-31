"""
Configuration management for the Research Discovery Engine.
Loads environment variables and provides centralized config access.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    # Keywords AI Gateway
    KEYWORDS_API_KEY = os.getenv('KEYWORDS_API_KEY')
    KEYWORDS_API_URL = os.getenv('KEYWORDS_API_URL', 'https://api.keywordsai.co/api')
    
    # LLM Configuration
    LLM_MODEL = os.getenv('LLM_MODEL', 'claude-3-sonnet')
    
    # Application
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    
    # Vector Search
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-large')
    TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', 5))
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        required = [
            'SUPABASE_URL', 'SUPABASE_KEY', 'KEYWORDS_API_KEY'
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
