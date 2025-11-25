from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import public, admin
from app.database import db
from app.utils.logging import setup_logging
from app.services.scheduler import scheduler_service

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
    scheduler_service.start()

@app.on_event("shutdown")
def shutdown_db_client():
    scheduler_service.shutdown()
    db.close()

# Routers
app.include_router(public.router, tags=["Public"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/health/scheduler")
async def scheduler_health_check():
    if scheduler_service.scheduler and scheduler_service.scheduler.running:
        job = scheduler_service.scheduler.get_job(scheduler_service.job_id)
        next_run = job.next_run_time if job else None
        return {
            "status": "running",
            "next_run_time": next_run,
            "timezone": str(scheduler_service.scheduler.timezone)
        }
    return {"status": "stopped"}
