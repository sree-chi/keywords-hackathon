"""
Keywords AI Gateway integration for observability and LLM routing.
This service handles all LLM calls through the Keywords AI Gateway,
logging each step with full observability.
"""
import requests
import json
import time
from typing import Dict, Any, Optional
from config import Config

class KeywordsGateway:
    """
    Client for Keywords AI Gateway.
    Routes all LLM calls through the gateway for observability.
    """
    
    def __init__(self):
        self.api_key = Config.KEYWORDS_API_KEY
        self.base_url = Config.KEYWORDS_API_URL
        self.model = Config.LLM_MODEL
    
    def _make_request(
        self,
        step_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Make an LLM request through Keywords AI Gateway.
        
        Args:
            step_name: Name of the agent step (for observability)
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with 'content' (response text) and 'metadata' (latency, etc.)
        """
        start_time = time.time()
        
        # Construct request payload
        # Adjust this structure based on actual Keywords Gateway API format
        payload = {
            "model": self.model,
            "messages": []
        }
        
        if system_prompt:
            payload["messages"].append({
                "role": "system",
                "content": system_prompt
            })
        
        payload["messages"].append({
            "role": "user",
            "content": prompt
        })
        
        payload["temperature"] = temperature
        payload["max_tokens"] = max_tokens
        
        # Metadata for observability
        metadata = {
            "step_name": step_name,
            "model": self.model,
            "prompt_length": len(prompt),
            "system_prompt_length": len(system_prompt) if system_prompt else 0
        }
        
        try:
            # Make request to Keywords Gateway
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Try different possible endpoint formats
            endpoint = f"{self.base_url}/chat/completions"
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            latency = time.time() - start_time
            
            if response.status_code != 200:
                # Log error but don't fail silently
                error_msg = f"Keywords Gateway error: {response.status_code} - {response.text}"
                print(f"[ERROR] {error_msg}")
                raise Exception(error_msg)
            
            result = response.json()
            
            # Extract content from response
            # Adjust based on actual Keywords Gateway response format
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
            elif "content" in result:
                content = result["content"]
            else:
                content = str(result)
            
            metadata.update({
                "latency": latency,
                "status": "success",
                "response_length": len(content),
                "prompt_version_id": result.get("prompt_version_id", "unknown")
            })
            
            return {
                "content": content,
                "metadata": metadata,
                "raw_response": result
            }
            
        except requests.exceptions.RequestException as e:
            latency = time.time() - start_time
            metadata.update({
                "latency": latency,
                "status": "error",
                "error": str(e)
            })
            print(f"[ERROR] Keywords Gateway request failed: {e}")
            raise
    
    def structural_abstraction(
        self,
        paper_text: str,
        paper_title: str = ""
    ) -> Dict[str, Any]:
        """
        Step B: Structural Abstraction
        Strip jargon and extract structural schema from paper text.
        
        Args:
            paper_text: Raw text from PDF
            paper_title: Optional paper title for context
            
        Returns:
            Dictionary with 'schema' (JSON) and 'metadata'
        """
        system_prompt = """You are an expert at analyzing academic papers and extracting their structural components while stripping away field-specific jargon.

Your task is to analyze a paper and extract its core structural elements into a fixed schema. Focus on the SYSTEM STRUCTURE, not the domain-specific details.

Output ONLY valid JSON matching this exact schema:
{
  "system_name": "string - a brief name for the system",
  "domain": "string - the academic field (e.g., 'biology', 'physics', 'economics')",
  "entities": ["string"] - key components or actors in the system,
  "state_variables": ["string"] - variables that describe the system state,
  "optimization_goal": "string - what the system optimizes for",
  "constraints": ["string"] - limitations or constraints on the system,
  "failure_modes": ["string"] - ways the system can fail or break down,
  "key_equations_or_principles": ["string"] - core mathematical or conceptual principles,
  "plain_language_summary": "string - 2-3 sentence summary in plain language"
}

CRITICAL: 
- Strip all field-specific jargon
- Focus on structural patterns, not domain details
- Output ONLY the JSON object, no markdown, no explanations
- Ensure all fields are populated (use empty arrays/strings if needed)
- The schema must be valid JSON that can be parsed directly"""

        user_prompt = f"""Analyze the following academic paper and extract its structural schema.

Title: {paper_title}

Paper Text:
{paper_text[:8000]}  # Limit to avoid token limits

Extract the structural schema following the format specified. Focus on the SYSTEM STRUCTURE, not domain-specific terminology."""

        result = self._make_request(
            step_name="structural_abstraction",
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2,  # Lower temperature for more consistent schema extraction
            max_tokens=1500
        )
        
        # Parse JSON from response
        content = result["content"].strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        try:
            schema = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse schema JSON: {e}")
            print(f"[DEBUG] Response content: {content[:500]}")
            raise ValueError(f"Invalid JSON schema returned: {e}")
        
        # Validate schema has required fields
        required_fields = [
            "system_name", "domain", "entities", "state_variables",
            "optimization_goal", "constraints", "failure_modes",
            "key_equations_or_principles", "plain_language_summary"
        ]
        for field in required_fields:
            if field not in schema:
                schema[field] = "" if isinstance(schema.get(field, ""), str) else []
        
        return {
            "schema": schema,
            "metadata": result["metadata"]
        }
    
    def generate_explanation(
        self,
        source_schema: Dict[str, Any],
        target_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step E: Explanation Generation
        Generate natural language explanation of structural analogy.
        
        Args:
            source_schema: Schema of the query paper
            target_schema: Schema of the matched paper
            
        Returns:
            Dictionary with 'explanation' and 'metadata'
        """
        system_prompt = """You are an expert at identifying structural analogies between systems from different academic domains.

Your task is to explain why two systems might be structurally analogous despite being from different fields. Focus on:
- Similar optimization goals
- Similar constraints
- Similar state variables
- Similar failure modes
- Structural patterns, not domain-specific details

Write a clear, concise explanation (2-3 paragraphs) that a researcher could use to understand the cross-disciplinary connection."""

        user_prompt = f"""Explain why these two systems might be structurally analogous:

SOURCE SYSTEM ({source_schema.get('domain', 'unknown')}):
- System: {source_schema.get('system_name', 'unknown')}
- Optimization Goal: {source_schema.get('optimization_goal', 'N/A')}
- Constraints: {', '.join(source_schema.get('constraints', []))}
- State Variables: {', '.join(source_schema.get('state_variables', []))}
- Failure Modes: {', '.join(source_schema.get('failure_modes', []))}

TARGET SYSTEM ({target_schema.get('domain', 'unknown')}):
- System: {target_schema.get('system_name', 'unknown')}
- Optimization Goal: {target_schema.get('optimization_goal', 'N/A')}
- Constraints: {', '.join(target_schema.get('constraints', []))}
- State Variables: {', '.join(target_schema.get('state_variables', []))}
- Failure Modes: {', '.join(target_schema.get('failure_modes', []))}

Generate an explanation of the structural analogy."""

        result = self._make_request(
            step_name="explanation_generation",
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,  # Higher temperature for more natural explanations
            max_tokens=800
        )
        
        return {
            "explanation": result["content"],
            "metadata": result["metadata"]
        }
