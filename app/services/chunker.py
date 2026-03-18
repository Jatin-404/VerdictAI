from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

app = FastAPI()

class CaseMetadata(BaseModel):
    judgment_id:   str      # "IN-HC-ALL-2006-CV-121D60"
    court:         str      # "Allahabad High Court"
    court_level:   str      # "HC" or "SC"
    decision_date: str      # "27 MARCH, 2006"
    domain:        str      # "service" / "civil" / "criminal"
    bench:         str      # judge name
    jurisdiction:  str      # "India"

class ChunkRequest(BaseModel):
    content_text: str
    metadata: CaseMetadata
    document_id: str | None = None
    filename: str
    chunk_size: int = 800
    overlap: int = 200      

# response

class Chunk(BaseModel):
    document_id: str
    chunk_text: str
    chunk_index: int
    filename: str
    ingestion_timestamp: str
    judgment_id: str
    court: str
    court_level: str
    decision_date: str
    domain: str
    bench: str
    jurisdiction: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "chunker" 
    }


@app.post("/chunk")
def chunk_document(data: ChunkRequest):
    doc_id = data.document_id or str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    text = data.content_text.strip()
    size = data.chunk_size
    overlap = min(data.overlap, data.chunk_size - 1)  # ← new field, default 200

    raw_chunks = []
    start = 0
    while start < len(text):
        end = start + size
        raw_chunks.append(text[start:end])
        start += size - overlap   # ← move forward by (size - overlap)
        if start >= len(text):
            break

    # Stamp case metadata on every chunk
    chunks = []
    for index, chunk_text in enumerate(raw_chunks):
        chunks.append(Chunk(
        document_id=doc_id,
        chunk_text=chunk_text,
        chunk_index=index,
        filename=data.filename,
        ingestion_timestamp=timestamp,
        judgment_id=data.metadata.judgment_id,
        court=data.metadata.court,
        court_level=data.metadata.court_level,
        decision_date=data.metadata.decision_date,
        domain=data.metadata.domain,
        bench=data.metadata.bench,
        jurisdiction=data.metadata.jurisdiction
        ))

    return {
    "document_id": doc_id,
    "total_chunks": len(chunks),
    "judgment_id": data.metadata.judgment_id,
    "court": data.metadata.court,
    "chunks": [c.model_dump() for c in chunks]
    }



if __name__ == "__main__":
    uvicorn.run("chunker:app", host="0.0.0.0", port=8001, reload=True)