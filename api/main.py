from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .schemas import SearchRequest, SearchResponse
from .adapter import run_supervisor_workflow

app = FastAPI(title="Supervisor Finder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    result = run_supervisor_workflow(request.query, request.from_date, request.to_date)
    return SearchResponse(
        candidates=result["candidates"],
        metadata=result["metadata"]
    )
