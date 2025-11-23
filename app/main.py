from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import public, admin
from app.database import db
from app.utils.logging import setup_logging

# Setup logging
setup_logging()

app = FastAPI(
    title="Alternate History Engine API",
    description="AI-powered alternate history generation engine.",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Connection
@app.on_event("startup")
def startup_db_client():
    db.connect()

@app.on_event("shutdown")
def shutdown_db_client():
    db.close()

# Routers
app.include_router(public.router, prefix="/api", tags=["Public"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
