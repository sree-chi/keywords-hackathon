# Cross-Disciplinary Research Discovery Engine

A hackathon-ready prototype that demonstrates structural analogies between academic papers from different fields using Retrieval-Augmented Generation (RAG) with full observability.

## 🎯 Overview

This system extracts structural schemas from academic papers, strips field-specific jargon, and finds cross-disciplinary analogies based on system structure (optimization goals, constraints, state variables, failure modes) rather than domain-specific content.

## 🏗️ Architecture

The system implements a 5-step RAG pipeline:

1. **Step A - PDF Ingestion**: Extract and chunk text from uploaded PDFs
2. **Step B - Structural Abstraction**: Use LLM to extract structural schema (jargon-stripped)
3. **Step C - Embedding & Storage**: Generate embeddings and store in Supabase with pgvector
4. **Step D - Structural Retrieval**: Find top-K structurally similar papers using vector similarity
5. **Step E - Explanation Generation**: Generate natural language explanations of analogies

All LLM calls are routed through **Keywords AI Gateway** for full observability.

## 📁 Project Structure

```
keywords-hackathon/
├── backend/                 # Flask API server
│   ├── agents/             # Main research agent orchestrator
│   ├── database/           # Database connection & migrations
│   │   └── migrations/     # SQL migration files
│   ├── services/           # Core services (PDF, LLM, embeddings)
│   ├── app.py              # Flask API endpoints
│   ├── config.py           # Configuration management
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.js          # Main React component
│   │   └── index.css       # Styling
│   └── package.json        # Node dependencies
├── .env.example            # Environment variable template
└── README.md               # This file
```

## 🚀 Quick Start (2-Minute Demo)

### Prerequisites

- Python 3.9+
- Node.js 16+
- Supabase project (with pgvector extension)
- Keywords AI Gateway API key
- OpenAI API key (for embeddings)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example .env
# Edit .env with your credentials:
# - SUPABASE_URL
# - SUPABASE_KEY
# - KEYWORDS_API_KEY
# - OPENAI_API_KEY (for embeddings)
```

### 2. Database Setup

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Run the migration file: `backend/database/migrations/001_initial_schema.sql`
4. This creates the `papers` and `paper_chunks` tables with pgvector support

**Note**: You can modify migrations later by creating new migration files (see `backend/database/migrations/README.md`)

### 3. Start Backend Server

```bash
cd backend
python app.py
```

The API will run on `http://localhost:5000`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will run on `http://localhost:3000`

### 5. Demo Workflow

1. **Upload a PDF**: Click "Upload Paper" tab, drag & drop a PDF
2. **View Schema**: See the extracted structural schema (system name, optimization goal, constraints, etc.)
3. **Find Analogies**: System automatically finds structurally similar papers from different domains
4. **Get Explanation**: Click "Explain Analogy" on any match to see why they're structurally similar

## 🔧 Configuration

All configuration is via `.env` file in the `backend/` directory:

```env
# Supabase
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Keywords AI Gateway
KEYWORDS_API_KEY=your_keywords_api_key
KEYWORDS_API_URL=https://api.keywords.ai/v1  # Update if different

# LLM (via Keywords Gateway)
LLM_MODEL=claude-3-sonnet  # or gpt-4, etc.

# OpenAI (for embeddings)
OPENAI_API_KEY=your_openai_api_key

# Application
FLASK_ENV=development
PORT=5000
EMBEDDING_MODEL=text-embedding-3-large
TOP_K_RESULTS=5
```

## 📊 Data Model

All papers are mapped to a fixed structural schema:

```json
{
  "system_name": "string",
  "domain": "string",
  "entities": ["string"],
  "state_variables": ["string"],
  "optimization_goal": "string",
  "constraints": ["string"],
  "failure_modes": ["string"],
  "key_equations_or_principles": ["string"],
  "plain_language_summary": "string"
}
```

**Similarity search** is computed ONLY over:
- `optimization_goal`
- `constraints`
- `state_variables`
- `failure_modes`

## 🔍 API Endpoints

### `POST /api/papers`
Upload and process a PDF paper.

**Request**: `multipart/form-data` with `file` (PDF)

**Response**:
```json
{
  "paper_id": "uuid",
  "title": "string",
  "schema": { ... },
  "trace": { ... }
}
```

### `POST /api/papers/<paper_id>/analogies`
Find structurally analogous papers.

**Request Body**:
```json
{
  "top_k": 5,
  "exclude_domain": "biology"  // Optional
}
```

### `GET /api/papers/<paper_id>/explain/<target_paper_id>`
Generate explanation of structural analogy.

### `GET /api/papers`
List all processed papers (with optional `?domain=X` filter).

### `GET /api/papers/<paper_id>`
Get full paper details including schema.

## 🗄️ Database Migrations

Migrations are in `backend/database/migrations/`. To modify the schema:

1. **Never edit existing migrations** - always create new ones
2. Create `002_description.sql` with your changes
3. Run in Supabase SQL Editor
4. Document changes in the migration file header

See `backend/database/migrations/README.md` for details.

## 🔬 Observability

All LLM calls are logged through Keywords AI Gateway with:
- Step name
- Prompt version ID
- Input summary
- Output schema
- Latency

This produces a multi-step agent trace suitable for live demos.

## 🛠️ Development Notes

### PDF Processing
- Uses `pdfplumber` (primary) and `PyPDF2` (fallback)
- Chunks text by sentences with overlap
- Extracts title from first few lines

### Embeddings
- Uses OpenAI embeddings (can be routed through Keywords Gateway if supported)
- Embedding dimension: 1536 (for `text-embedding-3-large`)
- Stored in Supabase pgvector column

### Vector Search
- Currently uses in-memory cosine similarity (works for demo)
- For production, implement proper pgvector similarity search via Supabase RPC

### Keywords Gateway Integration
- Adjust `KEYWORDS_API_URL` and request format in `services/keywords_gateway.py` based on actual API
- Current implementation assumes OpenAI-compatible chat completions format

## 🐛 Troubleshooting

**"Configuration validation failed"**
- Check that `.env` file exists and has all required variables

**"Failed to extract text from PDF"**
- PDF might be image-based or corrupted
- Try a different PDF

**"No analogous papers found"**
- Upload at least 2 papers from different domains first
- Check that embeddings were generated successfully

**Embedding storage errors**
- Verify pgvector extension is enabled in Supabase
- Check that embedding dimension matches migration (1536)

## 📝 Next Steps (Future Enhancements)

- [ ] Add arXiv/PubMed/DOI paper fetching
- [ ] Implement proper pgvector similarity search via Supabase RPC
- [ ] Add batch processing for multiple PDFs
- [ ] Improve PDF text extraction for complex layouts
- [ ] Add paper metadata extraction (authors, citations, etc.)
- [ ] Implement caching for embeddings
- [ ] Add user authentication and paper collections

## 📄 License

Hackathon prototype - not for production use.
