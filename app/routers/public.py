from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.database import db
from app.models import TimelineEvent, Subtopic, Proposal, Judgment
from app.config import settings

router = APIRouter()

# Cache the universe filter to avoid recreating it
UNIVERSE_FILTER = {"universe_id": settings.UNIVERSE_ID}

def get_paginated(collection_name: str, skip: int, limit: int, sort_order: int = -1):
    """Helper to get paginated results from a collection."""
    cursor = db.get_collection(collection_name).find(
        UNIVERSE_FILTER
    ).sort("day_index", sort_order).skip(skip).limit(min(limit, 100))
    return list(cursor)

@router.get("/timeline", response_model=List[TimelineEvent])
async def get_timeline(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    """Get timeline events with pagination."""
    return get_paginated("timeline", skip, limit)

@router.get("/timeline/latest", response_model=TimelineEvent)
async def get_latest_event():
    """Get the most recent timeline event."""
    event = db.get_collection("timeline").find_one(
        UNIVERSE_FILTER,
        sort=[("day_index", -1)]
    )
    if not event:
        raise HTTPException(404, "No events found")
    return event

@router.get("/timeline/{day_index}", response_model=TimelineEvent)
async def get_event_by_day(day_index: int):
    """Get a specific day's event."""
    event = db.get_collection("timeline").find_one(
        {**UNIVERSE_FILTER, "day_index": day_index}
    )
    if not event:
        raise HTTPException(404, f"Event for day {day_index} not found")
    return event

@router.get("/subtopics", response_model=List[Subtopic])
async def get_subtopics(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    """Get subtopics with pagination."""
    return get_paginated("subtopics", skip, limit)

@router.get("/proposals", response_model=List[Proposal])
async def get_proposals(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    """Get proposals with pagination."""
    return get_paginated("proposals", skip, limit)

@router.get("/judgements", response_model=List[Judgment])
async def get_judgements(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    """Get judgements with pagination."""
    return get_paginated("judgements", skip, limit)
