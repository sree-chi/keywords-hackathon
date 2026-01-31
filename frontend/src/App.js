import React, { useState } from 'react';
import axios from 'axios';
import './index.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [currentPaper, setCurrentPaper] = useState(null);
  const [matches, setMatches] = useState([]);
  const [explanation, setExplanation] = useState(null);
  const [explainingFor, setExplainingFor] = useState(null);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a PDF file');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
  };

  const handleDragLeave = (e) => {
    e.currentTarget.classList.remove('dragover');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile);
      setError(null);
    } else {
      setError('Please drop a PDF file');
    }
  };

  const uploadPaper = async () => {
    if (!file) {
      setError('Please select a PDF file');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    setCurrentPaper(null);
    setMatches([]);
    setExplanation(null);

    try {
      // Upload PDF
      const formData = new FormData();
      formData.append('file', file);
      const response = await axios.post(`${API_BASE}/api/papers`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setCurrentPaper(response.data);
      setSuccess(`Paper processed successfully! System: ${response.data.schema?.system_name || 'Unknown'}`);
      
      // Automatically find analogies
      if (response.data.paper_id) {
        await findAnalogies(response.data.paper_id);
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Upload failed');
      console.error('Upload error:', err);
    } finally {
      setLoading(false);
    }
  };

  const findAnalogies = async (paperId) => {
    if (!paperId) paperId = currentPaper?.paper_id;
    if (!paperId) return;

    setLoading(true);
    setError(null);
    setMatches([]);
    setExplanation(null);

    try {
      const response = await axios.post(`${API_BASE}/api/papers/${paperId}/analogies`, {
        top_k: 5,
        exclude_domain: currentPaper?.schema?.domain
      });

      setMatches(response.data.matches || []);
      if (response.data.matches?.length === 0) {
        setError('No analogous papers found. Try uploading more papers first.');
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Search failed');
      console.error('Analogy search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateExplanation = async (targetPaperId) => {
    if (!currentPaper?.paper_id) return;

    setLoading(true);
    setError(null);
    setExplainingFor(targetPaperId);

    try {
      const response = await axios.get(
        `${API_BASE}/api/papers/${currentPaper.paper_id}/explain/${targetPaperId}`
      );

      setExplanation({
        ...response.data,
        target_paper_id: targetPaperId
      });
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Explanation generation failed');
      console.error('Explanation error:', err);
    } finally {
      setLoading(false);
      setExplainingFor(null);
    }
  };

  return (
    <div className="container">
      <h1>🔬 Research Discovery Engine</h1>
      <p className="subtitle">Find structural analogies between academic papers across disciplines</p>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          Upload Paper
        </button>
        <button
          className={`tab ${activeTab === 'browse' ? 'active' : ''}`}
          onClick={() => setActiveTab('browse')}
        >
          Browse Papers
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      <div className={`tab-content ${activeTab === 'upload' ? 'active' : ''}`}>
        <div className="section">
          <h2>Step 1: Upload a PDF Paper</h2>
          
          <div className="input-group">
            <label>Upload PDF File</label>
            <div
              className="upload-area"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-input').click()}
            >
              {file ? (
                <div>
                  <p>✓ {file.name}</p>
                  <button className="secondary" onClick={(e) => { e.stopPropagation(); setFile(null); }}>
                    Remove
                  </button>
                </div>
              ) : (
                <div>
                  <p>📄 Click to select or drag & drop a PDF file</p>
                </div>
              )}
              <input
                id="file-input"
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
              />
            </div>
          </div>

          <button onClick={uploadPaper} disabled={loading || !file}>
            {loading ? 'Processing...' : 'Process Paper'}
          </button>
        </div>

        {currentPaper && (
          <>
            <div className="section">
              <h2>Extracted Structural Schema</h2>
              <div className="paper-card">
                <h3>{currentPaper.title || 'Untitled'}</h3>
                <span className="domain">{currentPaper.schema?.domain || 'unknown'}</span>
                <div className="schema-display">
                  <strong>System:</strong> {currentPaper.schema?.system_name || 'N/A'}<br/>
                  <strong>Optimization Goal:</strong> {currentPaper.schema?.optimization_goal || 'N/A'}<br/>
                  <strong>Constraints:</strong> {currentPaper.schema?.constraints?.join(', ') || 'N/A'}<br/>
                  <strong>State Variables:</strong> {currentPaper.schema?.state_variables?.join(', ') || 'N/A'}<br/>
                  <strong>Failure Modes:</strong> {currentPaper.schema?.failure_modes?.join(', ') || 'N/A'}<br/>
                  <strong>Summary:</strong> {currentPaper.schema?.plain_language_summary || 'N/A'}
                </div>
              </div>
            </div>

            {matches.length > 0 && (
              <div className="section">
                <h2>Structurally Analogous Papers</h2>
                <button onClick={() => findAnalogies()} disabled={loading}>
                  Refresh Matches
                </button>
                {matches.map((match, idx) => (
                  <div key={match.paper_id || idx} className="paper-card">
                    <h3>{match.title || 'Untitled'}</h3>
                    <span className="domain">{match.domain || 'unknown'}</span>
                    <div className="similarity">
                      Similarity Score: {(match.similarity_score * 100).toFixed(1)}%
                    </div>
                    <div className="schema-display">
                      <strong>System:</strong> {match.schema?.system_name || 'N/A'}<br/>
                      <strong>Optimization Goal:</strong> {match.schema?.optimization_goal || 'N/A'}<br/>
                      <strong>Constraints:</strong> {match.schema?.constraints?.join(', ') || 'N/A'}
                    </div>
                    <button
                      onClick={() => generateExplanation(match.paper_id)}
                      disabled={loading && explainingFor === match.paper_id}
                    >
                      {loading && explainingFor === match.paper_id
                        ? 'Generating...'
                        : 'Explain Analogy'}
                    </button>
                  </div>
                ))}
              </div>
            )}

            {explanation && (
              <div className="section">
                <h2>Explanation of Structural Analogy</h2>
                <div className="explanation">
                  {explanation.explanation}
                </div>
                {explanation.metadata && (
                  <div style={{ marginTop: '10px', fontSize: '0.9em', color: '#666' }}>
                    Generated in {explanation.metadata.latency?.toFixed(2)}s
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      <div className={`tab-content ${activeTab === 'browse' ? 'active' : ''}`}>
        <div className="section">
          <h2>All Processed Papers</h2>
          <BrowsePapers />
        </div>
      </div>

      {loading && <div className="loading">⏳ Processing...</div>}
    </div>
  );
}

function BrowsePapers() {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  React.useEffect(() => {
    const fetchPapers = async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/papers`);
        setPapers(response.data.papers || []);
      } catch (err) {
        setError(err.response?.data?.error || err.message || 'Failed to load papers');
      } finally {
        setLoading(false);
      }
    };
    fetchPapers();
  }, []);

  if (loading) return <div className="loading">Loading papers...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div>
      {papers.length === 0 ? (
        <p>No papers processed yet. Upload a paper to get started!</p>
      ) : (
        papers.map((paper) => (
          <div key={paper.id} className="paper-card">
            <h3>{paper.title || 'Untitled'}</h3>
            <span className="domain">{paper.domain || 'unknown'}</span>
            <p><strong>System:</strong> {paper.system_name || 'N/A'}</p>
            <p><strong>Goal:</strong> {paper.optimization_goal || 'N/A'}</p>
          </div>
        ))
      )}
    </div>
  );
}

export default App;
