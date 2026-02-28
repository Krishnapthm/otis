from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal, TypedDict, List
import json
import requests

load_dotenv()

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

tools = [Questions]

llm = ChatOpenAI(
    model="gpt-4o-mini",
)
url = "http://localhost:8000/v1/mcq/"

def store_mcq(quiz: MCQ):
    payload = {
        "mcq": quiz.model_dump(),
        
    }
    response = requests.post(url, json=payload)
    print(response.json())


llm_with_format = llm.with_structured_output(MCQ)

if __name__ == "__main__":

    quiz_json = llm_with_format.invoke("generate 2 mcq's on beginner level python")

    store_mcq(quiz_json)