"""
Embedding service for generating vector embeddings of structural schemas.
Uses OpenAI embeddings (can be routed through Keywords Gateway if needed).
"""
import json
from typing import List, Dict, Any
from openai import OpenAI
from config import Config

class EmbeddingService:
    """Service for generating embeddings from structural schemas."""
    
    def __init__(self):
        # Initialize OpenAI client for embeddings
        # Route through Keywords Gateway using its API key and base URL
        self.client = OpenAI(
            api_key=Config.KEYWORDS_API_KEY,
            base_url=Config.KEYWORDS_API_URL
        )
        self.model = Config.EMBEDDING_MODEL
    
    def embed_schema(self, schema: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for a structural schema.
        
        The embedding is computed from these key fields only:
        - optimization_goal
        - constraints
        - state_variables
        - failure_modes
        
        Args:
            schema: Structural schema dictionary
            
        Returns:
            List of floats representing the embedding vector
        """
        # Extract key fields for similarity search
        key_fields = {
            "optimization_goal": schema.get("optimization_goal", ""),
            "constraints": ", ".join(schema.get("constraints", [])),
            "state_variables": ", ".join(schema.get("state_variables", [])),
            "failure_modes": ", ".join(schema.get("failure_modes", []))
        }
        
        # Create text representation for embedding
        embedding_text = f"""Optimization Goal: {key_fields['optimization_goal']}
Constraints: {key_fields['constraints']}
State Variables: {key_fields['state_variables']}
Failure Modes: {key_fields['failure_modes']}"""
        
        # Generate embedding
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=embedding_text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[ERROR] Embedding generation failed: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for arbitrary text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[ERROR] Embedding generation failed: {e}")
            raise
