from fastapi import FastAPI
from Backend.routes.search import router as search_router
import uvicorn

app = FastAPI()

# Register routes
app.include_router(search_router)


if __name__ == "__main__":
    uvicorn.run(
        "Backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # ✅ This enables auto-reload
        log_level="info"
        
    )
