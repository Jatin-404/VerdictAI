import { useMemo, useState } from "react";

const API_BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

function formatJson(value) {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export default function App() {
  const [zipFile, setZipFile] = useState(null);
  const [chunkSize, setChunkSize] = useState(800);
  const [overlap, setOverlap] = useState(200);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [ingestError, setIngestError] = useState("");
  const [ingestResponse, setIngestResponse] = useState(null);

  const [jobId, setJobId] = useState("");
  const [jobStatus, setJobStatus] = useState(null);
  const [jobLoading, setJobLoading] = useState(false);
  const [jobError, setJobError] = useState("");

  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState("");
  const [documentsResponse, setDocumentsResponse] = useState(null);

  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [court, setCourt] = useState("");
  const [courtLevel, setCourtLevel] = useState("");
  const [domain, setDomain] = useState("");
  const [judgmentId, setJudgmentId] = useState("");
  const [bench, setBench] = useState("");
  const [decisionDate, setDecisionDate] = useState("");
  const [useLlm, setUseLlm] = useState(false);

  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [searchResponse, setSearchResponse] = useState(null);

  const apiHint = useMemo(() => {
    if (API_BASE) return API_BASE;
    return "(using dev proxy to http://localhost:8000)";
  }, []);

  async function handleIngestSubmit(event) {
    event.preventDefault();
    setIngestError("");
    setIngestResponse(null);

    if (!zipFile) {
      setIngestError("Please select a .zip file.");
      return;
    }

    setIngestLoading(true);
    try {
      const formData = new FormData();
      formData.append("zip_file", zipFile);
      formData.append("chunk_size", String(chunkSize));
      formData.append("overlap", String(overlap));

      const response = await fetch(`${API_BASE}/ingest/batch`, {
        method: "POST",
        body: formData
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || "Failed to start ingestion");
      }

      setIngestResponse(data);
      if (data?.job_id) {
        setJobId(data.job_id);
      }
    } catch (error) {
      setIngestError(error?.message || "Upload failed");
    } finally {
      setIngestLoading(false);
    }
  }

  async function handleJobCheck(event) {
    event?.preventDefault();
    if (!jobId) {
      setJobError("Enter a job ID to check status.");
      return;
    }

    setJobLoading(true);
    setJobError("");

    try {
      const response = await fetch(`${API_BASE}/ingest/jobs/${jobId}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || "Failed to fetch job status");
      }

      setJobStatus(data);
    } catch (error) {
      setJobError(error?.message || "Failed to fetch job status");
    } finally {
      setJobLoading(false);
    }
  }

  async function handleLoadDocuments(event) {
    event?.preventDefault();
    setDocumentsError("");
    setDocumentsResponse(null);
    setDocumentsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/documents`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || "Failed to load documents");
      }

      setDocumentsResponse(data);
    } catch (error) {
      setDocumentsError(error?.message || "Failed to load documents");
    } finally {
      setDocumentsLoading(false);
    }
  }

  async function handleSearch(event) {
    event.preventDefault();
    setSearchError("");
    setSearchResponse(null);

    if (!query.trim()) {
      setSearchError("Please enter a legal query.");
      return;
    }

    setSearchLoading(true);
    try {
      const payload = {
        query: query.trim(),
        top_k: Number(topK) || 5,
        court: court || null,
        court_level: courtLevel || null,
        domain: domain || null,
        judgment_id: judgmentId || null,
        bench: bench || null,
        decision_date: decisionDate || null,
        use_llm: Boolean(useLlm)
      };

      const response = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.detail || "Search failed");
      }

      setSearchResponse(data);
    } catch (error) {
      setSearchError(error?.message || "Search failed");
    } finally {
      setSearchLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">VerdictAI Legal RAG</p>
          <h1>Case intelligence for legal teams.</h1>
          <p className="subhead">
            Upload a zip of judgments, track ingestion, and search across the
            corpus with metadata filters.
          </p>
        </div>
        <div className="hero-card">
          <h3>Gateway</h3>
          <p className="mono">{apiHint}</p>
          <p className="muted">Use `VITE_API_BASE` to point at a hosted API.</p>
        </div>
      </header>

      <section className="card">
        <div className="card-header">
          <h2>1. Upload Cases (ZIP)</h2>
          <p>Batch ingest judgments using the `/ingest/batch` endpoint.</p>
        </div>
        <form onSubmit={handleIngestSubmit} className="form">
          <label className="field">
            <span>ZIP file</span>
            <input
              type="file"
              accept=".zip"
              onChange={(event) => setZipFile(event.target.files?.[0] || null)}
            />
          </label>

          <label className="field">
            <span>Chunk size</span>
            <input
              type="number"
              min="100"
              max="2000"
              value={chunkSize}
              onChange={(event) => setChunkSize(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Overlap</span>
            <input
              type="number"
              min="0"
              max="500"
              value={overlap}
              onChange={(event) => setOverlap(event.target.value)}
            />
          </label>

          <button className="primary" type="submit" disabled={ingestLoading}>
            {ingestLoading ? "Uploading..." : "Start Ingestion"}
          </button>
        </form>

        {ingestError && <p className="error">{ingestError}</p>}
        {ingestResponse && (
          <pre className="code-block">{formatJson(ingestResponse)}</pre>
        )}
      </section>

      <section className="card">
        <div className="card-header">
          <h2>2. Stored Documents</h2>
          <p>View documents already stored in PostgreSQL via `/documents`.</p>
        </div>
        <form onSubmit={handleLoadDocuments} className="form">
          <button className="secondary" type="submit" disabled={documentsLoading}>
            {documentsLoading ? "Loading..." : "Load Documents"}
          </button>
        </form>
        {documentsError && <p className="error">{documentsError}</p>}
        {documentsResponse && (
          <div className="doc-list">
            <div className="doc-summary">
              Total documents: {documentsResponse.total_documents ?? 0}
            </div>
            {Array.isArray(documentsResponse.documents) &&
            documentsResponse.documents.length > 0 ? (
              <div className="doc-grid">
                {documentsResponse.documents.map((doc) => (
                  <article
                    key={`${doc.document_id}-${doc.filename}`}
                    className="doc-card"
                  >
                    <h3>{doc.judgment_id || doc.document_id}</h3>
                    <p className="muted">{doc.filename}</p>
                    <div className="doc-meta">
                      <span>{doc.court}</span>
                      <span>{doc.court_level}</span>
                      <span>{doc.domain}</span>
                      <span>Chunks: {doc.total_chunks}</span>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="muted">No documents found in the store.</p>
            )}
          </div>
        )}
      </section>

      <section className="card">
        <div className="card-header">
          <h2>3. Check Ingestion Status</h2>
          <p>Poll `/ingest/jobs/{"{job_id}"}` for progress and results.</p>
        </div>
        <form onSubmit={handleJobCheck} className="form">
          <label className="field">
            <span>Job ID</span>
            <input
              type="text"
              placeholder="Paste job_id from upload response"
              value={jobId}
              onChange={(event) => setJobId(event.target.value)}
            />
          </label>
          <button className="secondary" type="submit" disabled={jobLoading}>
            {jobLoading ? "Checking..." : "Check Status"}
          </button>
        </form>
        {jobError && <p className="error">{jobError}</p>}
        {jobStatus && <pre className="code-block">{formatJson(jobStatus)}</pre>}
      </section>

      <section className="card">
        <div className="card-header">
          <h2>4. Legal Search</h2>
          <p>Run semantic search with optional metadata filters.</p>
        </div>
        <form onSubmit={handleSearch} className="form grid">
          <label className="field span-2">
            <span>Query</span>
            <input
              type="text"
              placeholder="e.g. standard for anticipatory bail in service matters"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Top K</span>
            <input
              type="number"
              min="1"
              max="20"
              value={topK}
              onChange={(event) => setTopK(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Court</span>
            <input
              type="text"
              placeholder="Allahabad High Court"
              value={court}
              onChange={(event) => setCourt(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Court Level</span>
            <input
              type="text"
              placeholder="HC / SC"
              value={courtLevel}
              onChange={(event) => setCourtLevel(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Domain</span>
            <input
              type="text"
              placeholder="civil / criminal / service"
              value={domain}
              onChange={(event) => setDomain(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Judgment ID</span>
            <input
              type="text"
              placeholder="IN-HC-ALL-2006-CV-121D60"
              value={judgmentId}
              onChange={(event) => setJudgmentId(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Bench</span>
            <input
              type="text"
              placeholder="Justice Name"
              value={bench}
              onChange={(event) => setBench(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Decision Date</span>
            <input
              type="text"
              placeholder="27 MARCH, 2006"
              value={decisionDate}
              onChange={(event) => setDecisionDate(event.target.value)}
            />
          </label>

          <label className="field checkbox">
            <input
              type="checkbox"
              checked={useLlm}
              onChange={(event) => setUseLlm(event.target.checked)}
            />
            <span>Use LLM answer generation</span>
          </label>

          <button className="primary" type="submit" disabled={searchLoading}>
            {searchLoading ? "Searching..." : "Run Search"}
          </button>
        </form>

        {searchError && <p className="error">{searchError}</p>}

        {searchResponse && (
          <div className="results">
            {searchResponse.answer && (
              <div className="answer">
                <h3>LLM Answer</h3>
                <p>{searchResponse.answer}</p>
              </div>
            )}

            {Array.isArray(searchResponse.results) && (
              <div className="result-list">
                {searchResponse.results.map((item, index) => (
                  <article key={`${item.document_id}-${item.chunk_index}-${index}`}>
                    <div className="result-meta">
                      <span>{item.court}</span>
                      <span>{item.judgment_id}</span>
                      <span>{item.decision_date}</span>
                      <span>Score: {item.score}</span>
                    </div>
                    <p>{item.chunk_text}</p>
                  </article>
                ))}
              </div>
            )}

            <details>
              <summary>Raw response</summary>
              <pre className="code-block">{formatJson(searchResponse)}</pre>
            </details>
          </div>
        )}
      </section>
    </div>
  );
}
