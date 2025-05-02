from pydantic import BaseModel
from typing import List, Optional

# Import ContestPublic schema (adjust path if necessary)
from ... import schemas 

class DashboardData(BaseModel):
    active_contests: List[schemas.ContestPublic] = []
    closed_contests: List[schemas.ContestPublic] = []
    judge_assigned_evaluations: Optional[List[schemas.ContestPublic]] = None # Null if user not judge
    pending_ai_evaluations: Optional[List[schemas.ContestPublic]] = None # Null if user not admin
    expired_open_contests: Optional[List[schemas.ContestPublic]] = None # Null if user not admin

    class Config:
        from_attributes = True # Allow creating from ORM objects 