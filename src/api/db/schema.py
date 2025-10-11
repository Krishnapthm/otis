from pydantic import BaseModel, UUID4, Field
from typing import List, Literal, Optional, Dict, Any
import datetime


class Options(BaseModel):
    id: Literal["A", "B", "C", "D"] = Field(description="Options")
    text: str = Field(description="options for the answer of MCQ")

class Questions(BaseModel):
    question_id: int = Field(description="The unique id of the MCQ")
    question: str = Field(description="the generated MCQ")
    options: List[Options] = Field(description="the options for the generated MCQ")
    answer: Literal["A", "B", "C", "D"] = Field(description="the correct option for the MCQ") 
    explanation: str = Field(description="explanation for the right answer")

class MCQ(BaseModel):
    questions: List[Questions] = Field(description="Multiple Choice Questions")

class CreateMCQ(BaseModel):
    project: Optional[str]
    mcq: MCQ
    generated_at: datetime.datetime
    
class ReadMCQ(CreateMCQ):
    id: UUID4
    generated_at: datetime.datetime