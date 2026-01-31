"""
Flask API server for the Research Discovery Engine.
Provides REST endpoints for the React frontend.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

from config import Config
from agents.research_agent import ResearchAgent

# Validate configuration on startup
try:
    Config.validate()
except ValueError as e:
    print(f"[WARNING] Configuration validation failed: {e}")
    print("[INFO] Make sure to set up your .env file")

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize agent
agent = ResearchAgent()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "research-discovery-engine"})

@app.route('/api/papers', methods=['POST'])
def upload_paper():
    """
    Upload and process a paper.
    
    Accepts:
    - PDF file upload (multipart/form-data)
    
    Returns:
    - paper_id, title, schema, trace
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file provided"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "File must be a PDF"}), 400
        
        pdf_bytes = file.read()
        title = request.form.get('title', '')
        
        result = agent.process_paper(pdf_file=pdf_bytes, title=title)
        return jsonify(result), 201
            
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/papers/<paper_id>/analogies', methods=['POST'])
def find_analogies(paper_id):
    """
    Find structurally analogous papers for a given paper.
    
    Args:
        paper_id: ID of the paper to find analogies for
        
    Optional JSON body:
        top_k: Number of results (default: 5)
        exclude_domain: Domain to exclude (to find cross-disciplinary matches)
    
    Returns:
        List of matched papers with similarity scores
    """
    try:
        # Get paper schema
        from database.db import Database
        db = Database.get_client()
        response = db.table("papers").select("structural_schema, domain").eq("id", paper_id).execute()
        
        if not response.data:
            return jsonify({"error": f"Paper {paper_id} not found"}), 404
        
        schema = response.data[0]["structural_schema"]
        domain = response.data[0].get("domain")
        
        # Get parameters
        data = request.json or {}
        top_k = data.get("top_k", 5)
        exclude_domain = data.get("exclude_domain", domain)  # Exclude same domain by default
        
        # Find analogies
        matches = agent.find_analogous_papers(
            query_schema=schema,
            top_k=top_k,
            exclude_domain=exclude_domain
        )
        
        return jsonify({
            "query_paper_id": paper_id,
            "matches": matches
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Analogy search failed: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/papers/<paper_id>/explain/<target_paper_id>', methods=['GET'])
def explain_analogy(paper_id, target_paper_id):
    """
    Generate explanation for why two papers are structurally analogous.
    
    Args:
        paper_id: Source paper ID
        target_paper_id: Target paper ID
        
    Returns:
        Explanation text and metadata
    """
    try:
        # Get source paper schema
        from database.db import Database
        db = Database.get_client()
        response = db.table("papers").select("structural_schema").eq("id", paper_id).execute()
        
        if not response.data:
            return jsonify({"error": f"Paper {paper_id} not found"}), 404
        
        source_schema = response.data[0]["structural_schema"]
        
        # Generate explanation
        result = agent.generate_explanation_for_match(
            source_schema=source_schema,
            target_paper_id=target_paper_id
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"[ERROR] Explanation generation failed: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/papers', methods=['GET'])
def list_papers():
    """
    List all processed papers.
    
    Query params:
        domain: Filter by domain
        limit: Limit results (default: 50)
        
    Returns:
        List of papers with basic info
    """
    try:
        from database.db import Database
        db = Database.get_client()
        
        query = db.table("papers").select("id, title, domain, source, uploaded_at, structural_schema")
        
        # Apply filters
        domain = request.args.get('domain')
        if domain:
            query = query.eq("domain", domain)
        
        limit = int(request.args.get('limit', 50))
        query = query.limit(limit)
        
        response = query.execute()
        
        # Format response
        papers = []
        for paper in response.data:
            schema = paper.get("structural_schema", {})
            papers.append({
                "id": paper["id"],
                "title": paper.get("title"),
                "domain": paper.get("domain"),
                "source": paper.get("source"),
                "system_name": schema.get("system_name"),
                "optimization_goal": schema.get("optimization_goal", "")[:100],
                "uploaded_at": paper.get("uploaded_at")
            })
        
        return jsonify({"papers": papers}), 200
        
    except Exception as e:
        print(f"[ERROR] List papers failed: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/papers/<paper_id>', methods=['GET'])
def get_paper(paper_id):
    """
    Get full details of a paper including schema.
    
    Returns:
        Complete paper data with schema
    """
    try:
        from database.db import Database
        db = Database.get_client()
        
        response = db.table("papers").select("*").eq("id", paper_id).execute()
        
        if not response.data:
            return jsonify({"error": f"Paper {paper_id} not found"}), 404
        
        paper = response.data[0]
        return jsonify(paper), 200
        
    except Exception as e:
        print(f"[ERROR] Get paper failed: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("[INFO] Starting Research Discovery Engine API...")
    print(f"[INFO] Environment: {Config.FLASK_ENV}")
    print(f"[INFO] Debug: {Config.FLASK_DEBUG}")
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.FLASK_DEBUG)
