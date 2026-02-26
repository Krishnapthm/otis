from typing import Annotated, List, Literal, Optional
import uuid
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
    topic: str
    difficulty: Literal["EASY", "MEDIUM", "HARD"]
    num_questions: int
    blooms_level: Literal[
        "REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"
    ]
    stem_guidance: str
    distractor_strategy: str
    retrieval_queries: List[str]
    concepts: List[Concept]


class MCQDraft(BaseModel):
    question_index: int = Field(default=0)
    stem: Optional[str]
    options: Optional[List[str]]
    distractors: Optional[List[str]]
    answer: Optional[str]
    explanation: str = ""
    validation_score: Optional[float] = None
    validation_feedback: Optional[str] = None


class MCQQuestion(BaseModel):
    question_index: int
    question: str


class MCQOption(BaseModel):
    key: Literal["A", "B", "C", "D"]
    text: str


class FinalMCQ(BaseModel):
    question_index: int
    question: str
    options: List[MCQOption]
    right_answer: Literal["A", "B", "C", "D"]
    explanation: str


class ValidationResult(BaseModel):
    validation_passed: bool
    validation_feedback: str = ""
    validation_score: Optional[float] = None


class RetrievalStatus(BaseModel):
    status: Literal["pending", "done", "failed"] = "pending"
    error: Optional[str] = None


class QuestionSubgraphState(TypedDict, total=False):
    plan: TestGenerationPlan
    question_index: int
    retrieved_chunks: List[RetrievedChunk]
    existing_draft: Optional[MCQDraft]
    stem: Optional[str]
    options: Optional[List[str]]
    correct_answer: Optional[str]
    distractors: Optional[List[str]]
    explanation: Optional[str]
    retry_count: int
    validation_passed: bool
    validation_feedback: str
    draft: Optional[MCQDraft]


class IntentClassification(BaseModel):
    intent: Literal[
        "followup", "mcq_request", "utility_task", "clarification", "BLOCKED"
    ]


class State(TypedDict, total=False):
    """
    State
    """

    # guardrails
    before_agent_guardrail: BeforeAgentGuardrail
    intent: IntentClassification

    # conversation
    messages: Annotated[List[ChatMessage], add] = None
    user_prompt: str
    user_id: str
    doc_ids: List[uuid.UUID]

    search_queries: List[str]
    retrieved_chunks: List[RetrievedChunk]
    retrieval_status: RetrievalStatus
    use_naive_generator: bool
    plan: TestGenerationPlan
    plan_version: int
    retry_count: int
    max_retries: int
    validation_feedback: str

    mcq_question_prompts: List[str]
    mcq_drafts: Annotated[List[MCQDraft], add]
    final_mcqs: List[FinalMCQ]

    edit_mode: bool
    edit_target: Literal["all", "specific"]
    edit_indices: List[int]
    edit_strategy: Literal["regenerate", "patch"]
    existing_drafts: List[MCQDraft]

    artifact_version: int
    retrieval_signature: Optional[str]
    retrieval_signature_valid: bool
    artifact_bump: bool
    tool_result: str
