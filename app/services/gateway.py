from fastapi import FastAPI
import uvicorn
from app.routes import ingest, search
from app.middleware import add_cors


app = FastAPI()
add_cors(app)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "gateway" 
    }


app.include_router(ingest.router)
app.include_router(search.router)


if __name__ == "__main__":
    uvicorn.run("gateway:app", host="0.0.0.0", port=8000, reload=True)
