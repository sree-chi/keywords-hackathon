"""
Main Research Discovery Agent
Orchestrates the complete workflow: PDF ingestion -> Structural abstraction -> 
Embedding & Storage -> Retrieval -> Explanation
"""
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from database.db import Database
from services.pdf_processor import PDFProcessor
from services.keywords_gateway import KeywordsGateway
from services.embedding_service import EmbeddingService

class ResearchAgent:
    """
    Main agent that orchestrates the research discovery pipeline.
    Each step is explicit and traceable for observability.
    """
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.keywords_gateway = KeywordsGateway()
        self.embedding_service = EmbeddingService()
        self.db = Database.get_client()
    
    def process_paper(
        self,
        pdf_file: bytes,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete pipeline: Process a paper through all agent steps.
        
        Args:
            pdf_file: PDF file bytes
            title: Optional paper title
            
        Returns:
            Dictionary with paper_id and processing metadata
        """
        if not pdf_file:
            raise ValueError("pdf_file is required")
        
        paper_id = str(uuid.uuid4())
        trace = {
            "paper_id": paper_id,
            "steps": [],
            "errors": []
        }
        
        try:
            # Step A: PDF Ingestion
            print(f"[STEP A] PDF Ingestion for paper {paper_id}")
            pdf_data = self.pdf_processor.extract_text_from_pdf(pdf_file, title)
            source = "upload"
            source_id = None
            
            title = pdf_data.get("title", title or "Untitled")
            full_text = pdf_data["text"]
            chunks = pdf_data["chunks"]
            
            trace["steps"].append({
                "step": "pdf_ingestion",
                "status": "success",
                "chunks_count": len(chunks),
                "text_length": len(full_text)
            })
            
            # Step B: Structural Abstraction
            print(f"[STEP B] Structural Abstraction for paper {paper_id}")
            abstraction_result = self.keywords_gateway.structural_abstraction(
                paper_text=full_text[:10000],  # Limit for token efficiency
                paper_title=title
            )
            
            schema = abstraction_result["schema"]
            schema["domain"] = schema.get("domain", "unknown")
            
            trace["steps"].append({
                "step": "structural_abstraction",
                "status": "success",
                "metadata": abstraction_result["metadata"],
                "schema_preview": {
                    "system_name": schema.get("system_name"),
                    "domain": schema.get("domain"),
                    "optimization_goal": schema.get("optimization_goal", "")[:100]
                }
            })
            
            # Step C: Embedding & Storage
            print(f"[STEP C] Embedding & Storage for paper {paper_id}")
            embedding = self.embedding_service.embed_schema(schema)
            
            # Store in database
            self._store_paper(
                paper_id=paper_id,
                title=title,
                domain=schema.get("domain", "unknown"),
                source=source,
                source_id=source_id,
                schema=schema,
                embedding=embedding
            )
            
            # Store raw chunks in database (must be after paper creation due to FK)
            self._store_chunks(paper_id, chunks)
            
            trace["steps"].append({
                "step": "embedding_storage",
                "status": "success",
                "embedding_dimension": len(embedding)
            })
            
            return {
                "paper_id": paper_id,
                "title": title,
                "schema": schema,
                "trace": trace
            }
            
        except Exception as e:
            trace["errors"].append({
                "step": "processing",
                "error": str(e)
            })
            print(f"[ERROR] Processing failed: {e}")
            raise
    
    def find_analogous_papers(
        self,
        query_schema: Dict[str, Any],
        top_k: int = 5,
        exclude_domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Step D: Structural Retrieval
        Find papers with structurally similar schemas.
        
        Args:
            query_schema: Structural schema to search for
            top_k: Number of results to return
            exclude_domain: Optional domain to exclude (to find cross-disciplinary matches)
            
        Returns:
            List of matched papers with similarity scores
        """
        print(f"[STEP D] Structural Retrieval (top_k={top_k})")
        
        # Generate embedding for query schema
        query_embedding = self.embedding_service.embed_schema(query_schema)
        
        # Build query
        # Use Supabase RPC or direct SQL for vector similarity search
        # Note: Supabase Python client may need custom SQL for pgvector
        
        # For now, we'll use a workaround with the Supabase client
        # In production, you'd use a Postgres function or direct SQL
        
        # Get all papers (this is inefficient but works for demo)
        # In production, use proper vector similarity search
        response = self.db.table("papers").select("*").execute()
        all_papers = response.data
        
        # Filter by domain if needed
        if exclude_domain:
            all_papers = [p for p in all_papers if p.get("domain") != exclude_domain]
        
        # Compute cosine similarity (simplified - in production use pgvector operators)
        import numpy as np
        query_vec = np.array(query_embedding)
        
        similarities = []
        for paper in all_papers:
            if not paper.get("structural_embedding"):
                continue
            
            paper_embedding = paper["structural_embedding"]
            if isinstance(paper_embedding, str):
                paper_embedding = json.loads(paper_embedding)
            
            paper_vec = np.array(paper_embedding)
            
            # Cosine similarity
            dot_product = np.dot(query_vec, paper_vec)
            norm_query = np.linalg.norm(query_vec)
            norm_paper = np.linalg.norm(paper_vec)
            
            if norm_query > 0 and norm_paper > 0:
                similarity = dot_product / (norm_query * norm_paper)
                similarities.append({
                    "paper": paper,
                    "similarity": float(similarity)
                })
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        top_matches = similarities[:top_k]
        
        return [
            {
                "paper_id": match["paper"]["id"],
                "title": match["paper"].get("title"),
                "domain": match["paper"].get("domain"),
                "schema": match["paper"].get("structural_schema"),
                "similarity_score": match["similarity"]
            }
            for match in top_matches
        ]
    
    def generate_explanation_for_match(
        self,
        source_schema: Dict[str, Any],
        target_paper_id: str
    ) -> Dict[str, Any]:
        """
        Step E: Explanation Generation
        Generate explanation for why two papers are structurally analogous.
        
        Args:
            source_schema: Schema of the query paper
            target_paper_id: ID of the matched paper
            
        Returns:
            Dictionary with explanation and metadata
        """
        print(f"[STEP E] Explanation Generation for paper {target_paper_id}")
        
        # Fetch target paper schema
        response = self.db.table("papers").select("structural_schema").eq("id", target_paper_id).execute()
        if not response.data:
            raise ValueError(f"Paper {target_paper_id} not found")
        
        target_schema = response.data[0]["structural_schema"]
        
        # Generate explanation
        explanation_result = self.keywords_gateway.generate_explanation(
            source_schema=source_schema,
            target_schema=target_schema
        )
        
        return {
            "explanation": explanation_result["explanation"],
            "metadata": explanation_result["metadata"],
            "target_paper_id": target_paper_id
        }
    
    def _store_chunks(self, paper_id: str, chunks: List[str]):
        """Store text chunks in database."""
        chunks_data = [
            {
                "paper_id": paper_id,
                "chunk_index": i,
                "text_content": chunk
            }
            for i, chunk in enumerate(chunks)
        ]
        
        if chunks_data:
            self.db.table("paper_chunks").insert(chunks_data).execute()
    
    def _store_paper(
        self,
        paper_id: str,
        title: str,
        domain: str,
        source: str,
        source_id: Optional[str],
        schema: Dict[str, Any],
        embedding: List[float]
    ):
        """Store paper with schema and embedding in database."""
        # Supabase pgvector expects the embedding as a list/array
        # The Python client should handle the conversion automatically
        # If issues occur, we may need to use raw SQL or format as PostgreSQL array string
        
        paper_data = {
            "id": paper_id,
            "title": title,
            "domain": domain,
            "source": source,
            "source_id": source_id,
            "structural_schema": schema,
            "structural_embedding": embedding,  # Pass as list, Supabase should handle conversion
            "processed_at": datetime.utcnow().isoformat()
        }
        
        try:
            self.db.table("papers").insert(paper_data).execute()
        except Exception as e:
            # If direct insertion fails, try with formatted string
            # Some Supabase setups require explicit array formatting
            print(f"[WARNING] Direct embedding insert failed, trying formatted string: {e}")
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            paper_data["structural_embedding"] = embedding_str
            self.db.table("papers").insert(paper_data).execute()
