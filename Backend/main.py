from fastapi import FastAPI
from routes.search import router as search_router
from routes.auth import router as auth_router
from routes.datafetch import router as datafetch_router
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI()

# Allow multiple frontend origins
FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").split(",")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,  # Can handle multiple origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # Changed from specific headers
)

# Register routes
app.include_router(search_router)
app.include_router(auth_router)
app.include_router(datafetch_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    """Preload heavy models on startup to avoid cold start latency."""
    print("🚀 App starting up... preloading models")
    from embedding.embedd import _get_dense_model
    try:
        _get_dense_model()
        print("✅ Embedding model preloaded successfully")
    except Exception as e:
        print(f"❌ Failed to preload embedding model: {e}")

# Only runs when you do: python main.py (NOT used by Railway)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # Changed default to 8080
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Fine for local dev
        log_level="info"
    )
