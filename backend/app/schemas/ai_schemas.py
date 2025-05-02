from pydantic import BaseModel, Field
from typing import Optional

# Request model for generating text
class GenerateTextRequest(BaseModel):
    contest_id: int = Field(..., description="ID of the contest")
    ai_writer_id: int = Field(..., description="ID of the AI Writer")
    model_id: str = Field(..., description="ID of the AI Model to use (e.g., 'gpt-4o', 'claude-3-opus-20240229')")
    title: str = Field(..., description="Title for the generated text", min_length=1, max_length=200)

# Response model for generating text
class GenerateTextResponse(BaseModel):
    success: bool = Field(..., description="Indicates if the operation was successful")
    message: str = Field(..., description="A message describing the outcome")
    submission_id: Optional[int] = Field(None, description="The ID of the created submission if successful")
    text: Optional[str] = Field(None, description="The generated text if successful")

class AIEvaluationResult(BaseModel):
    success: bool
    message: str
    evaluation_id: Optional[int] = None
    judge_id: Optional[int] = None
    contest_id: Optional[int] = None
    rankings: Optional[dict] = None # {submission_id: place}
    comments: Optional[dict] = None # {submission_id: comment} 