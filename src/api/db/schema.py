from pydantic import BaseModel, UUID4, Field
from typing import List, Literal, Optional, Dict, Any
import datetime


class Options(BaseModel):
    id: Literal["A", "B", "C", "D"] = Field(description="Option id")
    text: str = Field(description="Options for the answer of MCQ")

class Questions(BaseModel):
    question_id: int = Field(description="The unique id of the MCQ")
    question: str = Field(description="Generated Question")
    options: List[Options] = Field(description="The list of options for the generated MCQ")
    answer: Literal["A", "B", "C", "D"] = Field(description="The correct option for the MCQ") 
    explanation: str = Field(description="Explanation for the right answer")

class MCQ(BaseModel):
    questions: List[Questions] = Field(description="Multiple Choice Questions")

class CreateMCQ(BaseModel):
    mcq: MCQ
    
class ReadMCQ(CreateMCQ):
    mcq_id: UUID4
    generated_at: datetime.datetime

class DocBase(BaseModel):
    filename: str
    file_type: str
    file_size: int
    file_path: str
    # project_id: UUID4

class DocResponse(DocBase):
    doc_id: UUID4
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None

class ProjectBase(BaseModel):
    project_name: str
    project_desc: Optional[str]

class ProjectResponse(ProjectBase):
    project_id: UUID4
    created_at: datetime.datetime
    