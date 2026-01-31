"""
Database connection manager for Supabase.
"""
from supabase import create_client, Client
from config import Config

class Database:
    """Manages Supabase database connections."""
    
    _client: Client = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client."""
        if cls._client is None:
            cls._client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        return cls._client
    
    @classmethod
    def get_service_client(cls) -> Client:
        """Get Supabase client with service key (for admin operations)."""
        return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
