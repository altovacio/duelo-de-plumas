from pydantic import BaseModel, Field
from typing import List, Literal

# Define allowed status values
RoadmapStatus = Literal['backlog', 'in-progress', 'completed']

class RoadmapItemBase(BaseModel):
    text: str
    status: RoadmapStatus = 'backlog'

class RoadmapItemCreate(RoadmapItemBase):
    # Allow status override on creation if needed, otherwise defaults to backlog
    pass 

class RoadmapItem(RoadmapItemBase):
    id: int

class RoadmapItemUpdateStatus(BaseModel):
    status: RoadmapStatus 