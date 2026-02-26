from typing import Annotated, List, Literal, Optional, Type
import uuid
from langchain_postgres import chat_message_histories
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from operator import add


class Concept(BaseModel):
    name: str = Field(description="Concept Name")
    summary: str = Field(description="Concept Summary")
    # search_queries: List[str] = Field(description="search queries")


class SearchQueries(BaseModel):
    queries: List[str] = Field(default_factory=list)


class Overview(BaseModel):
    """
    Overview of the document
    """

    doc_name: str = Field(description="Document Name")
    concepts: List[Concept]


class DocumentContent(BaseModel):
    doc_id: uuid.UUID
    content_md: str


class ChatMessage(BaseModel):
    role: str = Field(description="Role of the message, e.g. user, assistant, system")
    content: str = Field(description="Content of the message")
    doc_ids: Optional[List[uuid.UUID]] = Field(
        default_factory=list, description="Documents associated with the message"
    )


class AgentState(TypedDict, total=False):
    """
    Agent State
    """

    chat_message: Annotated[List[ChatMessage], add] = None
    doc_ids: List[uuid.UUID]
    collection_name: Optional[List[str]] = None
    documents: Optional[List[DocumentContent]] = None
    overview: Optional[List[Overview]] = None
    user_prompt: Optional[List[str]] = None
    retrived_context: List
    selected_concepts: List[Concept]
    search_queries: List[SearchQueries]


class BeforeAgentGuardrail(BaseModel):
    intent: Literal["ALLOW", "BLOCK"]


class RetrievedChunk(TypedDict):
    chunk_id: str
    doc_id: str
    content: str
    score: float
    metadata: dict


# ---Plan state---#


class TestGenerationPlan(BaseModel):
    difficulty: Literal["EASY", "MEDIUM", "HARD"]
    num_questions: int
    blooms_level: Literal[
        "REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"
    ]
    stem_guidance: str
    distractor_strategy: str
    retrieval_queries: List[str]
    concepts: List[Concept]


class State(TypedDict, total=False):
    """
    State
    """

    intent: BeforeAgentGuardrail
    chat_messages: Annotated[List[ChatMessage], add] = None
    user_prompt: str
    doc_ids: List[uuid.UUID]
    user_id: str
    search_queries: List[str]
    retrieved_chunks: List[RetrievedChunk]
    use_naive_generator: bool
