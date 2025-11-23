from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class TimelineEvent(BaseModel):
    day_index: int
    subtopic: str
    event: Dict[str, Any]
    created_at: datetime

class Subtopic(BaseModel):
    day_index: int
    selected_subtopic: str
    reason: str
    tags: List[str]
    created_at: datetime

class Proposal(BaseModel):
    day_index: int
    model: str
    subtopic: str
    created_at: datetime
    # Allow extra fields since models output variable JSON
    class Config:
        extra = "allow"

class Judgment(BaseModel):
    day_index: int
    decision: str
    reason: str
    created_at: datetime

class SimulationResult(BaseModel):
    day_index: int
    status: str = "success"
    message: str
