"""explorer/api.py - FastAPI service wrapping the EmbeddingExplorer.

This module exposes health, embed, search, and UMAP visualization endpoints.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .main import EmbeddingExplorer, CORPUS
from .visualise import visualise

# Shared application state container
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager.

    Startup:
        1. Instantiates the EmbeddingExplorer (loads model onto CPU once).
        2. Seeds the store with the 24 CORPUS sentences.
        3. Saves references to state.

    Shutdown:
        Clears the state container to release memory resources.
    """
    explorer = EmbeddingExplorer()
    for text, _topic in CORPUS:
        explorer.add(text)
    
    state["explorer"] = explorer
    state["groups"] = [topic for _text, topic in CORPUS]
    
    print(f"FastAPI startup complete: pre-seeded {len(explorer.store)} sentences.")
    yield
    state.clear()
    print("FastAPI shutdown complete: resources released.")


app = FastAPI(
    title="Embedding Explorer API",
    version="1.0.0",
    lifespan=lifespan,
    description="Study guide web API for semantic vector embedding exploration and visualization.",
)


class EmbedRequest(BaseModel):
    """Request model for text ingestion."""
    text: str = Field(..., min_length=1, description="Raw text segment to embed and store.")


class SearchRequest(BaseModel):
    """Request model for vector search query."""
    query: str = Field(..., min_length=1, description="Semantic search query text.")
    top_k: int = Field(5, ge=1, le=50, description="Number of matches to return.")


@app.get("/health")
def health():
    """Liveness check and database size info."""
    explorer = state.get("explorer")
    if not explorer:
        return {"status": "starting", "store_size": 0}
    return {
        "status": "ok",
        "store_size": len(explorer.store),
    }


@app.post("/embed")
def embed(req: EmbedRequest):
    """Encode a text, insert it into the store, and return its vector representation."""
    explorer = state["explorer"]
    embedding = explorer.add(req.text)
    state["groups"].append("user")
    return {
        "added": req.text,
        "store_size": len(explorer.store),
        "embedding": embedding,
    }


@app.post("/search")
def search(req: SearchRequest):
    """Perform a cosine similarity search over stored vectors using the query text."""
    explorer = state["explorer"]
    results = explorer.search(req.query, req.top_k)
    return {
        "query": req.query,
        "results": results,
    }


@app.get("/visualise")
def visualise_endpoint():
    """Trigger a fresh UMAP layout computation and stream back the PNG plot."""
    explorer = state["explorer"]
    path = visualise(explorer.store, output_path="embedding_space.png", groups=state["groups"])
    return FileResponse(path, media_type="image/png", filename="embedding_space.png")
