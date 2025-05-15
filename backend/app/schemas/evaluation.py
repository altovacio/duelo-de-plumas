from typing import Optional
from pydantic import BaseModel

class EvaluationCommentResponse(BaseModel):
    comment: Optional[str] = None
    # Placeholder for judge identifier, to be refined later
    judge_identifier: Optional[str] = None 
    # Could also include place given by this judge if needed
    # text_place: Optional[int] = None 

    class Config:
        from_attributes = True 