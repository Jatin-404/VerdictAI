from fastapi import FastAPI
from pydantic import BaseModel
import httpx
from httpx import AsyncClient
from sklearn.metrics.pairwise import cosine_similarity
import os
import uvicorn

from app.core.config import settings
STORE_URL    = settings.STORE_URL
EMBED_URL    = settings.EMBED_URL
OLLAMA_URL   = settings.OLLAMA_URL
OLLAMA_MODEL = settings.OLLAMA_MODEL



app = FastAPI()

# What the user sends to search
class SearchRequest(BaseModel):
    query:         str
    top_k:         int = 5
    court:         str | None = None
    court_level:   str | None = None   # "HC" or "SC"
    domain:        str | None = None   # "civil"/"criminal"/"service"
    decision_date: str | None = None
    bench:         str | None = None   # filter by judge
    judgment_id:   str | None = None
    use_llm: bool = False              #  <--------- flag to use llm or not 

async def generate_ans(query: str, chunks: list[dict]) -> str:
    """
    Sends retrieved chunks as context to Ollama
    and gets a grounded answer back.
    """

    # build context from top chunks
    context_parts= []
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i+1}] "
            f"Court: {chunk['court']} | "
            f"Case: {chunk['judgment_id']} | "
            f"Date: {chunk['decision_date']}\n"
            f"{chunk['chunk_text']}"
            )
    context = "\n\n---\n\n".join(context_parts)

    # Prompt engineered for legal RAG
    # Key rules:
    # 1. Answer ONLY from context — no hallucination
    # 2. Cite which source you used
    # 3. If not in context, say so clearly

    prompt = f"""You are a legal research assistant. Answer the question using ONLY the provided court judgment excerpts.

    Rules:
    - Answer based strictly on the provided sources
    - Cite which source (Source 1, Source 2 etc.) supports your answer
    - If the answer is not found in the sources, say "The provided judgments do not contain relevant information to answer this question."
    - Be concise and precise
    - Use legal terminology appropriately

    Question: {query}

    Sources:
    {context}

    Answer:"""
    
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json= {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False     # get full response at once not streamed
            }
        )
        result = response.json()
        return result["response"].strip()



@app.get("/health")
def health():
    return {"status": "ok", "service": "search"}

@app.post("/search")
async def search(data: SearchRequest):
    async with AsyncClient(timeout= 300) as client:

        # Embed the user's query
        embed_response = await client.post(
            f"{EMBED_URL}/embed",
            json={
                "chunks": [{
                    "document_id": "query",
                    "chunk_text": data.query,
                    "chunk_index": 0,
                    "filename": "query",
                    "ingestion_timestamp": "",
                    "judgment_id": "",
                    "court": "",
                    "court_level": "",
                    "decision_date": "",
                    "domain": "",
                    "bench": "",
                    "jurisdiction":""
                }]
            }
        )
        query_vector = embed_response.json()["chunks"][0]["vector"]

        # Fetching all chunks from store
        store_response = await client.get(f"{STORE_URL}/chunks")
        # catch bad responses before they crash
        if store_response.status_code != 200:
            return {
                "error": f"Store service returned {store_response.status_code}",
                "detail": store_response.text
            }
        all_chunks = store_response.json()["chunks"]

    # Step 3: Apply metadata filters BEFORE doing vector math
    # This is the "hybrid" part — filter first, then rank by similarity
    filtered_chunks = []
    for chunk in all_chunks:  # This loop removes chunks that don’t match the metadata filters

        # Filter by court if provided
        if data.court and chunk["court"].lower() != data.court.lower():
            continue

        # Filter by court_level if provided
        if data.court_level and chunk["court_level"].lower() != data.court_level.lower():
            continue

        # Filter by domain if provided
        if data.domain and chunk["domain"].lower() != data.domain.lower():
            continue

        # Filter by judgment_id if provided 
        if data.judgment_id and chunk["judgment_id"] != data.judgment_id:
            continue

        # Filter by bech if provided
        if data.bench and data.bench.lower() not in chunk["bench"].lower():
            continue

        # Filter by decision_date if provided
        if data.decision_date and chunk["decision_date"] != data.decision_date:
            continue

        filtered_chunks.append(chunk)

    #  Score remaining chunks by vector similarity 
    results = []
    for chunk in filtered_chunks:
        score = cosine_similarity(
            [query_vector],
            [chunk["vector"]]
        )[0][0]

        results.append({
            "document_id": chunk["document_id"],
            "chunk_text": chunk["chunk_text"],
            "chunk_index": chunk["chunk_index"],
            "filename": chunk["filename"],
            "judgment_id": chunk["judgment_id"],
            "court": chunk["court"],
            "court_level": chunk["court_level"],
            "decision_date": chunk["decision_date"],
            "domain": chunk["domain"],
            "bench": chunk["bench"],
            "score": round(float(score), 4)
        })

    # Sorting by score and returning top k
    results.sort(key=lambda x: x["score"], reverse=True)
    top_results = results[:data.top_k]

    response = {
        "query": data.query,
        "filters_applied": {
            "court": data.court,
            "court_level": data.court_level,
            "domain": data.domain,
            "judgment_id": data.judgment_id,
            "bench": data.bench
        },
        "total_after_filter": len(filtered_chunks),
        "top_k": data.top_k,
        "results": results[:data.top_k]
    }

    # use llm (only if use_llm = True)
    if data.use_llm:
        if not top_results:
            # No chunks found → no point calling Ollama
            response["answer"] = "The provided judgments do not contain relevant information to answer this question."
            response["sources_used"] = []
        else:
            # Generate answer from top chunks
            answer = await generate_ans(data.query, top_results)
            response["answer"] = answer
            response["sources_used"] = [
                {
                    "judgment_id": r["judgment_id"],
                    "court": r["court"],
                    "decision_date": r["decision_date"],
                    "chunk_index": r["chunk_index"],
                    "score": r["score"]
                }
                for r in top_results
            ]

    return response

if __name__ == "__main__":
    uvicorn.run("search:app", host="0.0.0.0", port=8004, reload=True)