from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal, TypedDict, List
import json

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

llm = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini",
    api_version="2024-12-01-preview"
)

def store_mcq(quiz: MCQ):
    with open('quiz.json', 'w') as file:
        file.write(quiz.model_dump_json(indent=2))
    print("saved in quiz.json")


llm_with_format = llm.with_structured_output(MCQ)

if __name__ == "__main__":

    quiz_json = llm_with_format.invoke("generate 2 mcq's on beginner level python")

    store_mcq(quiz_json)