from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import verify_admin_key
from app.services.pipeline import pipeline_service
from app.models import SimulationResult
from app.database import db
from app.config import settings
from app.utils.logging import logger

router = APIRouter(dependencies=[Depends(verify_admin_key)])

@router.post("/simulate/day", response_model=SimulationResult)
async def simulate_day():
    """
    Trigger the daily simulation pipeline.
    Requires admin authentication via x-admin-key header.
    """
    try:
        result = pipeline_service.run_daily_simulation()
        logger.info(f"Simulation completed successfully for day {result['day_index']}")
        return {
            "day_index": result["day_index"],
            "message": f"Day {result['day_index']} simulation completed successfully"
        }
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}")
        raise HTTPException(500, f"Simulation failed: {str(e)}")

@router.post("/reset")
async def reset_simulation():
    """
    Reset the entire simulation by clearing all data.
    WARNING: This is a destructive operation!
    Requires admin authentication via x-admin-key header.
    """
    try:
        collections = ["timeline", "subtopics", "proposals", "judgements"]
        for col in collections:
            result = db.get_collection(col).delete_many({"universe_id": settings.UNIVERSE_ID})
            logger.info(f"Deleted {result.deleted_count} documents from {col}")
        
        return {
            "message": "Simulation reset successfully",
            "universe_id": settings.UNIVERSE_ID
        }
    except Exception as e:
        logger.error(f"Reset failed: {str(e)}")
        raise HTTPException(500, f"Reset failed: {str(e)}")
