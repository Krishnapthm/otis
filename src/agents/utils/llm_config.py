"""Centralised LLM and embedding model configuration for agent nodes."""

from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI

load_dotenv()

embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://ollama:11434")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    streaming=True,
)

guardrail_llm = ChatOpenAI(
    model="gpt-4.1-nano",
)

# --- Placeholder model aliases for modular MCQ pipeline nodes ---
# Replace any alias below with a different model name when needed.
planner_llm = ChatOpenAI(
    model="gpt-4.1-nano",
)

intent_llm = ChatOpenAI(
    model="gpt-4.1-nano",
)

retrieval_llm = ChatOpenAI(
    model="gpt-4.1-nano",
)

stem_llm = ChatOpenAI(
    model="gpt-4.1-nano",
)

options_llm = ChatOpenAI(
    model="gpt-4.1-nano",
)

validator_llm = ChatOpenAI(
    model="gpt-4.1-nano",
)

chat_no_tools_llm = ChatOpenAI(
    model="gpt-4.1-nano",
    streaming=True,
)
