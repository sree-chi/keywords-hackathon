"""
PDF processing service for extracting text from uploaded PDFs.
Supports multiple PDF libraries (pdfplumber and PyPDF2).
"""
import PyPDF2
import pdfplumber
from typing import Dict, List
import io

class PDFProcessor:
    """Service for processing PDF files and extracting text."""
    
    def extract_text_from_pdf(self, pdf_file: bytes, title: str = "") -> Dict[str, any]:
        """
        Step A: PDF Ingestion
        Extract text from PDF file and chunk it.
        
        Args:
            pdf_file: PDF file bytes
            title: Optional paper title
            
        Returns:
            Dictionary with 'text' (full text), 'chunks' (list of chunks), and 'title'
        """
        # Try pdfplumber first (better for complex layouts)
        try:
            pdf = pdfplumber.open(io.BytesIO(pdf_file))
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            full_text = "\n\n".join(text_parts)
            pdf.close()
        except Exception as e:
            print(f"[WARNING] pdfplumber failed, trying PyPDF2: {e}")
            # Fallback to PyPDF2
            try:
                pdf = PyPDF2.PdfReader(io.BytesIO(pdf_file))
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                full_text = "\n\n".join(text_parts)
            except Exception as e2:
                raise ValueError(f"Failed to extract text from PDF: {e2}")
        
        if not full_text or len(full_text.strip()) < 100:
            raise ValueError("PDF appears to be empty or unreadable")
        
        # Chunk the text (simple chunking by paragraphs/sentences)
        chunks = self._chunk_text(full_text)
        
        return {
            "text": full_text,
            "chunks": chunks,
            "title": title or self._extract_title_from_text(full_text)
        }
    
    def _chunk_text(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """
        Chunk text into smaller pieces for processing.
        
        Args:
            text: Full text
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for punct in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct != -1:
                        end = last_punct + 2
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks
    
    def _extract_title_from_text(self, text: str) -> str:
        """Extract title from text (first line or first sentence)."""
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and len(line) > 10 and len(line) < 200:
                return line
        return "Untitled Paper"
