from fastapi import APIRouter
from pydantic import BaseModel
from httpx import AsyncClient

from app.core.config import settings
SEARCH_URL = settings.SEARCH_URL

router = APIRouter(prefix="/search",tags=['Search'] )




class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    court: str | None = None
    court_level: str | None = None
    domain: str | None = None
    judgment_id: str | None = None
    bench: str | None = None
    decision_date: str | None = None
    use_llm: bool = False  




@router.post('/')
async def search(request: SearchRequest):
    async with AsyncClient(timeout=180) as client:
        response = await client.post(f"{SEARCH_URL}/search",
                               json=request.model_dump())
        

        if response.status_code != 200:
            return {
                "error": f"Search service returned {response.status_code}",
                "detail": response.text
            }
        return response.json()
    
