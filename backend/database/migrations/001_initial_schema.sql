-- Migration: 001_initial_schema.sql
-- Description: Initial database schema for Research Discovery Engine
-- Created: 2024-01-XX
-- 
-- To apply: Run this in Supabase SQL Editor
-- To modify: Create a new migration file (002_*.sql) with your changes

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Table for storing papers and their structural schemas
CREATE TABLE IF NOT EXISTS papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    domain TEXT,
    source TEXT DEFAULT 'upload', -- 'upload' for now, can add 'arxiv', 'nature', etc. later
    source_id TEXT, -- For future use: arXiv ID, DOI, etc.
    
    -- Raw structural schema JSON (matches the fixed schema structure)
    structural_schema JSONB NOT NULL,
    
    -- Vector embedding of the structural schema
    -- Dimension: 1536 (for text-embedding-3-large) or 3072 (for text-embedding-3-large with large dimension)
    -- Adjust based on your embedding model
    structural_embedding vector(1536),
    
    -- Metadata
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT valid_schema CHECK (structural_schema IS NOT NULL)
);

-- Table for storing raw PDF text chunks
CREATE TABLE IF NOT EXISTS paper_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraint
    CONSTRAINT fk_paper_chunks_paper_id 
        FOREIGN KEY (paper_id) 
        REFERENCES papers(id) 
        ON DELETE CASCADE
);

-- Indexes for performance

-- Vector similarity search index (IVFFlat for approximate nearest neighbor)
-- Note: This index requires at least some data to be effective
-- You may want to create it after inserting initial data
CREATE INDEX IF NOT EXISTS papers_structural_embedding_idx 
ON papers 
USING ivfflat (structural_embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for domain filtering (useful for cross-disciplinary searches)
CREATE INDEX IF NOT EXISTS papers_domain_idx ON papers(domain);

-- Index for source filtering
CREATE INDEX IF NOT EXISTS papers_source_idx ON papers(source);

-- Index for paper chunks lookup
CREATE INDEX IF NOT EXISTS paper_chunks_paper_id_idx ON paper_chunks(paper_id);
CREATE INDEX IF NOT EXISTS paper_chunks_chunk_index_idx ON paper_chunks(paper_id, chunk_index);

-- Comments for documentation
COMMENT ON TABLE papers IS 'Stores papers with their structural schemas and embeddings for similarity search';
COMMENT ON COLUMN papers.structural_schema IS 'JSON matching the fixed schema: system_name, domain, entities, state_variables, optimization_goal, constraints, failure_modes, key_equations_or_principles, plain_language_summary';
COMMENT ON COLUMN papers.structural_embedding IS 'Vector embedding computed from optimization_goal, constraints, state_variables, and failure_modes fields';
COMMENT ON TABLE paper_chunks IS 'Stores chunked text from PDFs for reference and potential future RAG improvements';
