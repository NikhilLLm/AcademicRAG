from fastapi import FastAPI
from Backend.routes.search import router as search_router
from Backend.routes.auth import router as auth_router
from Backend.routes.datafetch import router as datafetch_router
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

# Register routes
app.include_router(search_router)
app.include_router(auth_router)
app.include_router(datafetch_router)




# Debug: Print all registered routes

if __name__ == "__main__":
    uvicorn.run(
        "Backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # ✅ This enables auto-reload
        log_level="info"
        
    )
